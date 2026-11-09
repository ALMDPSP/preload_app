import json
from test_app import isolated,admin,create,headers,add_user,save
from test_rollout_base import form,put
from test_dashboard import finish
from test_operations import plan,issue
import app as module

def renumber(c,b,**values):
    d=form(c,b);m=next(m for m in d['machines'] if m['pdv']=='01')
    return c.put('/api/rollout-base/branches/'+b+'/pdv-number',headers=headers(c),json=dict(from_pdv='01',to_pdv='05',plan_version=d['plan_version'],inventory_version=m['version'],**values))

def test_rename_preserves_saved_checklist_inventory_operations_and_other_branch(isolated):
    c=admin(isolated);id=create(c);finish(c,id);before=c.get('/api/cutovers/'+id).json;b=before['branch_id']
    data=form(c,b);data['machines'][0].update(status='Implantado',installed_version='Orion 2',notes='Preservar');assert put(c,b,data).status_code==200
    assert c.put('/api/operations/schedule',headers=headers(c),json=plan(b)).status_code==200
    assert c.post('/api/operations/issues',headers=headers(c),json=issue(b)).status_code==201
    other=c.post('/api/branches',headers=headers(c),json={'code':'L9999','name':'Outra loja'}).json['id']
    other_id=c.post('/api/cutovers',headers=headers(c),json={'branch_id':other,'pdv':'01'}).json['id']
    response=renumber(c,b);assert response.status_code==200 and response.json['cutovers_updated']==1
    after=c.get('/api/cutovers/'+id).json
    assert after['state']['meta']['pdv']=='05' and after['state']['meta']['branch']=='VD266 / PDV 05'
    assert after['state']['tasks']==before['state']['tasks'] and after['state']['decisions']==before['state']['decisions']
    assert after['version']==before['version']+1 and after['updated_at']==before['updated_at'] and after['updated_by']==before['updated_by']
    assert save(c,id,before['state'],before['version']).status_code in (400,409)
    assert save(c,id,after['state'],before['version']).status_code==409
    fresh=form(c,b);assert [m['pdv'] for m in fresh['machines']]==['02','03','04','05']
    assert fresh['machines'][-1]['notes']=='Preservar' and fresh['machines'][-1]['installed_version']=='Orion 2' and fresh['machines'][-1]['version']==2
    ops=c.get('/api/operations/overview').json
    assert ops['schedule'][0]['pdv']=='05' and ops['schedule'][0]['version']==2
    assert ops['issues'][0]['pdv']=='05' and ops['issues'][0]['version']==2
    assert c.get('/api/cutovers/'+other_id).json['state']['meta']['pdv']=='01'
    assert c.get('/api/dashboard?compact=1').json['totals']['ok']==1
    assert c.get('/api/branches/'+b+'/cutover-progress').json['machines'][-1]['execution']['id']==id

def test_rename_all_historical_runs_keeps_order(isolated):
    c=admin(isolated);id=create(c);r=c.get('/api/cutovers/'+id).json;b=r['branch_id']
    # Simulate an earlier saved run retained in the audit history.
    with module.db() as db:
        row=dict(db.execute('SELECT * FROM ct_cutovers WHERE id=%s',(id,)).fetchone())
        row.update(id='historic',updated_at='2020-01-01T00:00:00Z')
        columns=list(row)
        db.execute('INSERT INTO ct_cutovers ('+','.join(columns)+') VALUES ('+','.join(['%s']*len(columns))+')',tuple(row[k] for k in columns))
        db.execute('INSERT INTO ct_cutover_branch (cutover_id,branch_id) VALUES (%s,%s)',('historic',b))
    assert renumber(c,b).json['cutovers_updated']==2
    older=c.get('/api/cutovers/historic').json
    assert older['state']['meta']['pdv']=='05' and older['updated_at']=='2020-01-01T00:00:00Z'
    progress=c.get('/api/branches/'+b+'/cutover-progress').json
    assert next(m for m in progress['machines'] if m['pdv']=='05')['execution']['id']==id

def test_duplicates_and_stale_versions_leave_everything_unchanged(isolated):
    c=admin(isolated);id=create(c);before=c.get('/api/cutovers/'+id).json;b=before['branch_id']
    def call(**changes):
        return c.put('/api/rollout-base/branches/'+b+'/pdv-number',headers=headers(c),json={'from_pdv':'01','to_pdv':'05','plan_version':0,'inventory_version':0,**changes})
    for changes in [{'to_pdv':'02'},{'plan_version':9},{'inventory_version':9}]:
        assert call(**changes).status_code==409
    target=c.post('/api/cutovers',headers=headers(c),json={'branch_id':b,'pdv':'05'}).json['id']
    assert call().status_code==409
    assert c.get('/api/cutovers/'+id).json==before
    assert form(c,b)['plan_version']==0
    assert c.delete('/api/cutovers/'+target,headers=headers(c),json={'version':1}).status_code==200
    with module.db() as db:
        db.execute("INSERT INTO ct_rollout_inventory (branch_id,pdv,status,installed_version,deployed_at,notes,version,updated_at,updated_by) VALUES (%s,'05','Pendente','','','',1,%s,'qa')",(b,module.now()))
    assert call().status_code==409
    assert form(c,b)['plan_version']==0

def test_permissions_validation_and_default_plan_rename(isolated):
    c=admin(isolated);id=create(c);b=c.get('/api/cutovers/'+id).json['branch_id'];url='/api/rollout-base/branches/'+b+'/pdv-number'
    body={'from_pdv':'01','to_pdv':'05','plan_version':0,'inventory_version':0}
    for role in ['viewer','operator']:
        user,_=add_user(c,role+'-renumber@qa.test',role,isolated)
        assert user.put(url,headers=headers(user),json=body).status_code==403
    assert module.app.test_client().put(url,json=body).status_code in (401,403)
    assert c.put(url,json=body).status_code==403
    for changes in [{'to_pdv':'0'},{'to_pdv':'10000'},{'to_pdv':'abc'},{'to_pdv':'01'},{'from_pdv':[]},{'plan_version':True},{'inventory_version':-1}]:
        assert c.put(url,headers=headers(c),json={**body,**changes}).status_code==400
    manager,_=add_user(c,'manager-rename@qa.test','manager',isolated)
    assert manager.put(url,headers=headers(manager),json=body).status_code==200
    d=form(c,b);assert d['plan_version']==1 and d['machines'][-1]['pdv']=='05' and d['machines'][-1]['version']==0
