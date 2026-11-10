import json
from test_app import isolated,admin,add_user,headers,create
import app as module
import operations
from test_dashboard import finish

def setup(c):
    id=create(c);r=c.get('/api/cutovers/'+id).json
    return id,r['state']['meta']['branch_id']

def plan(branch,**values):
    return dict(branch_id=branch,pdv='PDV 1',owner='Técnico QA',start_date='2026-01-01',due_date='2026-01-02',notes='Janela aprovada',version=0,**values)

def issue(branch):return dict(branch_id=branch,pdv='01',title='Pinpad sem comunicação',description='Conferir rede',owner='Redes',due_date='2026-01-02',priority='Alta',status='Aberta',resolution='')

def test_schedule_validation_conflicts_and_preserved_cutover(isolated):
    c=admin(isolated);id,b=setup(c);body=plan(b)
    assert c.put('/api/operations/schedule',headers=headers(c),json={**body,'pdv':'05'}).status_code==400
    assert c.put('/api/operations/schedule',headers=headers(c),json={**body,'start_date':'2027-01-01'}).status_code==400
    assert c.put('/api/operations/schedule',headers=headers(c),json=body).status_code==200
    assert c.put('/api/operations/schedule',headers=headers(c),json=body).status_code==409
    data=c.get('/api/operations/overview').json;s=data['schedule'][0]
    assert s['pdv']=='01' and s['status']=='Atrasado' and s['cutover_id']==id
    assert c.put('/api/operations/schedule',headers=headers(c),json={**body,'version':1,'owner':'Outra equipe'}).status_code==200
    finish(c,id);s=c.get('/api/operations/overview').json['schedule'][0]
    assert s['status']=='Concluído' and s['completed_at'] and not s['completion_reference']
    assert c.delete('/api/operations/schedule',headers=headers(c),json={**body,'version':1}).status_code==409
    assert c.delete('/api/operations/schedule',headers=headers(c),json={**body,'version':2}).status_code==200
    assert c.get('/api/cutovers/'+id).status_code==200

def test_issue_resolution_conflicts_and_immutable_binding(isolated):
    c=admin(isolated);id,b=setup(c);body=issue(b)
    assert c.post('/api/operations/issues',headers=headers(c),json={**body,'status':'Resolvida'}).status_code==400
    r=c.post('/api/operations/issues',headers=headers(c),json=body);assert r.status_code==201;r_id=r.json['id']
    data=c.get('/api/operations/overview').json;assert data['metrics']['open_issues']==1 and data['issues'][0]['overdue']
    assert c.put('/api/operations/issues/'+r_id,headers=headers(c),json={**body,'version':1,'pdv':'02'}).status_code==400
    resolved={**body,'status':'Resolvida','resolution':'Rede corrigida e teste aprovado','version':1}
    assert c.put('/api/operations/issues/'+r_id,headers=headers(c),json=resolved).status_code==200
    assert c.put('/api/operations/issues/'+r_id,headers=headers(c),json=resolved).status_code==409
    assert c.get('/api/operations/overview').json['metrics']['open_issues']==0
    assert c.get('/api/cutovers/'+id).json['state']['tasks']=={}

def test_permissions_csrf_and_goal_cas(isolated):
    c=admin(isolated);id,b=setup(c);v,_=add_user(c,'view@qa.test','viewer',isolated);o,_=add_user(c,'op@qa.test','operator',isolated);m,_=add_user(c,'manager@qa.test','manager',isolated)
    assert module.app.test_client().get('/api/operations/overview').status_code==401
    assert v.get('/api/operations/history').status_code==200
    assert v.post('/api/operations/issues',headers=headers(v),json=issue(b)).status_code==403
    assert o.put('/api/operations/schedule',headers=headers(o),json=plan(b)).status_code==403
    assert o.post('/api/operations/issues',headers=headers(o),json=issue(b)).status_code==201
    assert m.put('/api/operations/schedule',headers=headers(m),json=plan(b)).status_code==200
    week=c.get('/api/operations/overview').json['goal']['week_start'];path='/api/operations/goals/'+week
    assert c.put(path,json={'target':10,'version':0}).status_code==403
    assert o.put(path,headers=headers(o),json={'target':10,'version':0}).status_code==403
    for target in [-1,True,1.2,100001]:assert c.put(path,headers=headers(c),json={'target':target,'version':0}).status_code==400
    assert c.put('/api/operations/goals/2026-11-03',headers=headers(c),json={'target':10,'version':0}).status_code==400
    assert c.put(path,headers=headers(c),json={'target':10,'version':0}).status_code==200
    assert c.put(path,headers=headers(c),json={'target':20,'version':0}).status_code==409
    assert c.put(path,headers=headers(c),json={'target':20,'version':1}).status_code==200
    assert c.get('/api/operations/overview').json['goal']['target']==20

def test_snapshots_preserve_previous_days_and_no_invented_gaps(isolated,monkeypatch):
    c=admin(isolated);monkeypatch.setattr(module,'now',lambda:'2026-11-01T15:00:00+00:00');id,b=setup(c)
    assert c.get('/api/dashboard').status_code==200
    with module.db() as db:first=dict(db.execute('SELECT * FROM ct_rollout_snapshots WHERE day=%s',('2026-11-01',)).fetchone())
    monkeypatch.setattr(module,'now',lambda:'2026-11-03T15:00:00+00:00');finish(c,id)
    rows=c.get('/api/operations/history?from=2026-11-01&to=2026-11-03').json['rows']
    assert [r['day'] for r in rows]==['2026-11-01','2026-11-03']
    assert rows[0]['ok']==0 and rows[1]['ok']==1 and not rows[0]['provisional'] and rows[1]['provisional']
    with module.db() as db:assert dict(db.execute('SELECT * FROM ct_rollout_snapshots WHERE day=%s',('2026-11-01',)).fetchone())==first
    # A stale supplied dashboard is ignored and recomputed after reading the revision.
    operations.capture_snapshot(vars(module),{'generated_at':'2026-11-01T15:00:00+00:00','totals':{'ok':999}})
    assert c.get('/api/operations/history?from=2026-11-03&to=2026-11-03').json['rows'][0]['ok']==1
    assert c.get('/api/operations/history?from=invalid').status_code==400
    assert c.get('/api/operations/history?from=2020-01-01&to=2026-11-03').status_code==400

def test_snapshot_failure_does_not_turn_saved_checklist_into_error(isolated,monkeypatch):
    c=admin(isolated);id,b=setup(c)
    monkeypatch.setattr(operations,'capture_snapshot',lambda *a,**kw:(_ for _ in ()).throw(RuntimeError('test')))
    r=c.get('/api/cutovers/'+id).json;r['state']['tasks']['orion1']={'status':'Concluído'}
    result=c.put('/api/cutovers/'+id,headers=headers(c),json={'state':r['state'],'version':r['version']})
    assert result.status_code==200 and c.get('/api/cutovers/'+id).json['state']['tasks']['orion1']['status']=='Concluído'

def test_history_comparisons_use_recorded_baselines_and_show_gaps():
    from datetime import date
    rows=[{'day':day,'payload':json.dumps({'ok':ok})} for day,ok in [('2026-09-30',1),('2026-10-29',3),('2026-11-01',4),('2026-11-03',6),('2026-11-06',5)]]
    result=operations.history_comparisons(rows,date(2026,11,6))
    assert result[0]['label']=='Semana atual' and result[0]['ok_delta']==1 and result[0]['baseline_day']=='2026-11-01'
    assert result[1]['days_recorded']==2 and result[1]['ok_delta']==3
    assert result[2]['ok_delta']==2 and result[2]['last_day']=='2026-11-06'
    assert result[3]['ok_delta']==2
    assert operations.history_comparisons(rows[-1:],date(2026,11,6))[0]['ok_delta'] is None

def test_daily_boundary_cli_and_decreasing_counts(isolated,monkeypatch,capsys):
    import manage
    c=admin(isolated);monkeypatch.setattr(module,'now',lambda:'2026-11-07T01:00:00+00:00');id,b=setup(c);finish(c,id)
    manage.main(['snapshot-rollout']);assert '2026-11-06' in capsys.readouterr().out
    response=c.post('/api/cutovers/'+id+'/reject',headers=headers(c),json={'reason':'Falha fiscal confirmada','version':c.get('/api/cutovers/'+id).json['version']})
    assert response.status_code==200
    rows=c.get('/api/operations/history?from=2026-11-06&to=2026-11-06').json['rows'];assert rows[0]['ok']==0 and rows[0]['provisional']
    import pytest
    with pytest.raises(SystemExit):manage.main(['snapshot-rollout','wrong-extra-argument'])

def test_delete_issue_admin_only_conflicts_audit_and_preserves_checklist(isolated):
    c=admin(isolated);cutover,b=setup(c);body=issue(b)
    r=c.post('/api/operations/issues',headers=headers(c),json=body);id=r.json['id'];path='/api/operations/issues/'+id
    original=c.get('/api/cutovers/'+cutover).json
    assert module.app.test_client().delete(path,json={'version':1}).status_code==403
    assert c.delete(path,json={'version':1}).status_code==403
    for role in ['manager','operator','viewer']:
        user,_=add_user(c,'delete-'+role+'@qa.test',role,isolated)
        assert user.delete(path,headers=headers(user),json={'version':1}).status_code==403
    for version in [None,True,0,-1,'1']:
        assert c.delete(path,headers=headers(c),json={'version':version}).status_code==400
    assert c.put(path,headers=headers(c),json={**body,'version':1,'title':'Pendência atualizada'}).status_code==200
    assert c.delete(path,headers=headers(c),json={'version':1}).status_code==409
    assert c.get('/api/operations/overview').json['metrics']['open_issues']==1
    assert c.delete(path,headers=headers(c),json={'version':2}).status_code==200
    data=c.get('/api/operations/overview').json
    assert data['issues']==[] and data['metrics']['open_issues']==0
    assert c.get('/api/cutovers/'+cutover).json==original
    with module.db() as db:
        row=db.execute('SELECT * FROM ct_audit WHERE action=%s',('exclusão de pendência',)).fetchone()
        assert row and json.loads(row['detail'])['id']==id
    assert c.delete(path,headers=headers(c),json={'version':2}).status_code==404
