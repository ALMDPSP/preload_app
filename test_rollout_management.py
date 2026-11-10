import copy,io,json,gzip
from pypdf import PdfReader
from test_app import isolated,admin,create,headers,add_user
from test_rollout_base import form,put
from test_dashboard import finish
import app as module

def central(c,id,**change):
    cut=c.get('/api/cutovers/'+id).json;b=cut['branch_id'];base=form(c,b)
    base['machines']=[base['machines'][0]]
    return b,{'pdv':'01','base':base,'checklist':{'id':id,'state':cut['state'],'version':cut['version']},**change}
def save(c,b,body):return c.post('/api/rollout/branches/'+b+'/save-all',headers=headers(c),json=body)
def preview(c,data):return c.post('/api/admin/operational-restore/preview',headers=headers(c),data={'file':(io.BytesIO(data),'backup.json.gz')})
def restore(c,data,token):return c.post('/api/admin/operational-restore/apply',headers=headers(c),data={'file':(io.BytesIO(data),'backup.json.gz'),'token':token,'confirmation':'RESTAURAR'})

def test_atomic_save_commits_every_part_and_rolls_back_base_on_checklist_conflict(isolated):
    c=admin(isolated);id=create(c);b,body=central(c,id);body['base']['machines'][0].update(status='Implantado',installed_version='Orion v5')
    body['checklist']['state']['tasks']['linx1']={'status':'Concluído'}
    r=save(c,b,body);assert r.status_code==200 and r.json['checklist']['version']==2
    assert r.json['base']['machines'][0]['installed_version']=='Orion v5'
    fresh_b,fresh=central(c,id);fresh['base']['gr']='Não gravar';fresh['checklist']['version']=1
    assert save(c,b,fresh).status_code==409
    assert form(c,b)['gr']=='' and c.get('/api/cutovers/'+id).json['version']==2
    # An assignment written before another failure must also roll back.
    fresh_b,fresh=central(c,id);fresh['assignment']={'version':0,'planned_date':'2026-11-10'}
    fresh['base']['version']=999
    assert save(c,b,fresh).status_code==409
    assert c.get('/api/rollout/branches/'+b+'/context').json['assignments']==[]

def test_assignment_roles_named_validator_and_operator_cannot_reassign(isolated):
    c=admin(isolated);id=create(c);b,body=central(c,id)
    manager,_=add_user(c,'validator-v5@qa.test','manager',isolated);other,_=add_user(c,'other-v5@qa.test','manager',isolated);operator,_=add_user(c,'exec-v5@qa.test','operator',isolated)
    with module.db() as db:people={r['email']:r['id'] for r in db.execute('SELECT id,email FROM ct_users').fetchall()}
    body['assignment']={'version':0,'executor_id':people['exec-v5@qa.test'],'validator_id':people['validator-v5@qa.test']}
    assert save(c,b,body).status_code==200
    b,body=central(c,id);body['assignment']={'version':1,'executor_id':people['exec-v5@qa.test']}
    assert save(operator,b,body).status_code==403
    b,body=central(c,id)
    for t in module.SOURCE['orion'][:3]+module.SOURCE['linx']:body['checklist']['state']['tasks'][t['id']]={'status':'Concluído'}
    body['checklist']['state']['decisions']['linx']={'value':'GO','owner':'Validador','at':'2026-11-10T10:00'}
    assert save(other,b,body).status_code==403
    assert save(manager,b,body).status_code==200
    assert module.app.test_client().get('/api/rollout/queue').status_code==401
    assert c.post('/api/rollout/branches/'+b+'/save-all',json=body).status_code==403

def test_waves_queue_period_and_csv_with_actual_pdvs(isolated):
    c=admin(isolated);id=create(c);b,body=central(c,id)
    wave=c.post('/api/rollout/waves',headers=headers(c),json={'name':'Onda SP','start_date':'2026-11-01','due_date':'2026-11-05','delay_reason':'Aguardando janela'}).json['id']
    body['assignment']={'version':0,'wave_id':wave}
    assert save(c,b,body).status_code==200
    queue=c.get('/api/rollout/queue?mode=overdue').json;assert queue['total']==1 and queue['rows'][0]['pdv']=='01' and queue['rows'][0]['delay_reason']=='Aguardando janela'
    summary=c.get('/api/rollout/summary?from=2026-11-01&to=2026-11-10').json
    assert summary['current']['planned']==1 and summary['current']['deviation']==1 and summary['waves'][0]['planned']==1
    finish(c,id)
    summary=c.get('/api/rollout/summary?from=2026-11-01&to=2026-11-10').json
    assert summary['current']['validated_planned']==1 and summary['waves'][0]['validated']==1
    csv=c.get('/api/rollout/operations.csv?from=2026-11-01&to=2026-11-10')
    assert csv.status_code==200 and 'VD266' in csv.text and 'Onda SP' in csv.text
    assert c.get('/api/rollout/summary?from=2026-12-01&to=2026-01-01').status_code==400
    assert c.put('/api/rollout/waves/'+wave,headers=headers(c),json={'name':'Onda SP','start_date':'2026-11-01','due_date':'2026-11-05','version':99}).status_code==409

def test_signed_backup_preview_and_atomic_restore_preserve_accounts(isolated):
    c=admin(isolated);id=create(c);b,body=central(c,id)
    body['base']['machines'][0]['installed_version']='Versão original';assert save(c,b,body).status_code==200
    backup=c.get('/api/admin/operational-backup');assert backup.status_code==200
    raw=json.loads(gzip.decompress(backup.data));assert not any(k in raw['payload']['tables'] for k in ['ct_users','ct_auth','ct_attempts'])
    with module.db() as db:users=[dict(r) for r in db.execute('SELECT * FROM ct_users').fetchall()]
    b,body=central(c,id);body['base']['machines'][0]['installed_version']='Mudança posterior';assert save(c,b,body).status_code==200
    pv=preview(c,backup.data);assert pv.status_code==200
    applied=restore(c,backup.data,pv.json['token']);assert applied.status_code==200
    assert form(c,b)['machines'][0]['installed_version']=='Versão original'
    with module.db() as db:assert users==[dict(r) for r in db.execute('SELECT * FROM ct_users').fetchall()]
    assert c.get('/api/cutovers/'+id).status_code==200

def test_backup_rejects_tampering_stale_preview_and_non_admin(isolated):
    c=admin(isolated);id=create(c);b,body=central(c,id);data=c.get('/api/admin/operational-backup').data
    modified=json.loads(gzip.decompress(data));modified['payload']['tables']['ct_branches']['rows'][0]['name']='Forjado'
    assert preview(c,gzip.compress(json.dumps(modified).encode())).status_code==400
    pv=preview(c,data);assert pv.status_code==200
    assert save(c,b,body).status_code==200
    assert restore(c,data,pv.json['token']).status_code==409
    viewer,_=add_user(c,'backup-view@qa.test','viewer',isolated)
    assert viewer.get('/api/admin/operational-backup').status_code==403
    assert module.app.test_client().get('/api/admin/operational-backup').status_code==401

def test_issue_impact_is_saved_and_preserved_in_queue(isolated):
    c=admin(isolated);id=create(c);b,body=central(c,id)
    issue={'branch_id':b,'pdv':'01','title':'Impressora sem comunicação','owner':'Infra','due_date':'2026-11-01','impact':'Venda parada','priority':'Crítica'}
    r=c.post('/api/operations/issues',headers=headers(c),json=issue);assert r.status_code==201
    row=c.get('/api/rollout/queue').json['rows'][0];assert row['impact']=='Venda parada' and row['critical']==1
    issue.update(version=1,status='Resolvida',resolution='Driver corrigido')
    assert c.put('/api/operations/issues/'+r.json['id'],headers=headers(c),json=issue).status_code==200

def test_concurrent_sqlite_saves_have_one_winner(isolated):
    from concurrent.futures import ThreadPoolExecutor
    c=admin(isolated);id=create(c);b,body=central(c,id)
    with c.session_transaction() as session:auth=dict(session)
    clients=[]
    for _ in range(2):
        client=module.app.test_client()
        with client.session_transaction() as session:session.update(auth)
        clients.append(client)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda client:save(client,b,copy.deepcopy(body)).status_code,clients))
    assert sorted(results)==[200,409]
    assert c.get('/api/cutovers/'+id).json['version']==2

def test_wave_branch_bulk_preserves_named_responsibilities_and_checks_versions(isolated):
    c=admin(isolated);id=create(c);b,body=central(c,id)
    wave=c.post('/api/rollout/waves',headers=headers(c),json={'name':'Onda em lote','start_date':'2026-11-01','due_date':'2026-11-30'}).json['id']
    with module.db() as db:uid=db.execute('SELECT id FROM ct_users LIMIT 1').fetchone()['id']
    body['assignment']={'version':0,'executor_id':uid,'validator_id':uid}
    assert save(c,b,body).status_code==200
    ctx=c.get('/api/rollout/branches/'+b+'/context').json
    versions={m['pdv']:next((a['version'] for a in ctx['assignments'] if a['pdv']==m['pdv']),0) for m in ctx['machines']}
    payload={'branch_id':b,'plan_version':ctx['plan_version'],'versions':versions}
    url='/api/rollout/waves/'+wave+'/assign-branch'
    assert c.post(url,headers=headers(c),json=payload).status_code==200
    rows=c.get('/api/rollout/branches/'+b+'/context').json['assignments']
    assert len(rows)==4 and all(a['wave_id']==wave for a in rows)
    first=next(a for a in rows if a['pdv']=='01');assert first['executor_id']==uid and first['validator_id']==uid
    assert c.post(url,headers=headers(c),json=payload).status_code==409

def test_period_pdf_and_invalid_period(isolated):
    c=admin(isolated);create(c)
    r=c.get('/api/reports/rollout-executive.pdf?from=2026-11-01&to=2026-11-10')
    assert r.status_code==200
    pdf=PdfReader(io.BytesIO(r.data));assert len(pdf.pages)==4
    text=' '.join(' '.join(p.extract_text() for p in pdf.pages).split())
    assert 'Resultado do período' in text and 'Período anterior' in text and 'Não informada' in text
    assert c.get('/api/reports/rollout-executive.pdf?from=2026-12-01&to=2026-11-10').status_code==400

def test_restore_constraint_failure_rolls_back_all_operational_tables(isolated):
    from operational_backup import sign,snapshot,digest
    c=admin(isolated);id=create(c);backup=c.get('/api/admin/operational-backup').data
    payload=json.loads(gzip.decompress(backup))['payload']
    payload['tables']['ct_cutover_branch']['rows'][0]['branch_id']='nonexistent'
    broken=gzip.compress(json.dumps({'payload':payload,'signature':sign(vars(module),payload)}).encode())
    pv=preview(c,broken);assert pv.status_code==200
    with module.db() as db:before=digest(snapshot(db))
    assert restore(c,broken,pv.json['token']).status_code==409
    with module.db() as db:assert digest(snapshot(db))==before
    assert c.get('/api/cutovers/'+id).status_code==200

def test_administrator_integrity_check(isolated):
    c=admin(isolated);create(c)
    result=c.get('/api/admin/operational-integrity')
    assert result.status_code==200 and result.json['ok'] is True and result.json['totals']['planned']==4
    with module.db() as db:
        branch=db.execute('SELECT id FROM ct_branches LIMIT 1').fetchone()['id']
        db.execute('INSERT INTO ct_branch_pdv_plan (branch_id,pdvs,version) VALUES (%s,%s,1)',(branch,'["01","01"]'))
    result=c.get('/api/admin/operational-integrity')
    assert result.json['ok'] is False and any(i['level']=='error' for i in result.json['issues'])
