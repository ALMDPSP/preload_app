from test_app import isolated,admin,create,headers,add_user
from test_dashboard import finish
import app as module

def test_partial_save_list_and_resume_edit_with_pending_processes(isolated):
    c=admin(isolated);id=create(c);record=c.get('/api/cutovers/'+id).json;b=record['branch_id']
    record['state']['tasks']['orion1']={'status':'Concluído','notes':'Fiscal confirmado; rede ainda pendente.'}
    saved=c.put('/api/cutovers/'+id,headers=headers(c),json={'state':record['state'],'version':record['version']})
    assert saved.status_code==200
    progress=c.get('/api/branches/'+b+'/cutover-progress').json
    assert progress['totals']=={'expected':5,'saved':1,'ok':0,'pending':5}
    assert progress['machines'][0]['execution']['completed']==1 and progress['machines'][0]['status']=='Em andamento'
    assert progress['machines'][1]['execution'] is None and progress['machines'][1]['status']=='Não iniciado'
    reopened=c.get('/api/cutovers/'+progress['machines'][0]['execution']['id']).json
    assert reopened['state']['tasks']['orion1']['notes']=='Fiscal confirmado; rede ainda pendente.'
    reopened['state']['tasks']['orion1']['notes']='Atualizado após retomar a loja.'
    assert c.put('/api/cutovers/'+id,headers=headers(c),json={'state':reopened['state'],'version':reopened['version']}).status_code==200
    assert c.get('/api/cutovers/'+id).json['state']['tasks']['orion1']['notes']=='Atualizado após retomar a loja.'

def test_completed_checklist_remains_editable_and_can_reopen_process(isolated):
    c=admin(isolated);id=create(c);finish(c,id);record=c.get('/api/cutovers/'+id).json;b=record['branch_id']
    assert c.get('/api/branches/'+b+'/cutover-progress').json['totals']['ok']==1
    record['state']['meta']['handoff']='Acompanhamento após conclusão.'
    assert c.put('/api/cutovers/'+id,headers=headers(c),json={'state':record['state'],'version':record['version']}).status_code==200
    record=c.get('/api/cutovers/'+id).json;record['state']['tasks']['orion6']['status']='Pendente';record['state']['decisions']['orion']['value']='Pendente'
    assert c.put('/api/cutovers/'+id,headers=headers(c),json={'state':record['state'],'version':record['version']}).status_code==200
    progress=c.get('/api/branches/'+b+'/cutover-progress').json
    assert progress['totals']['ok']==0 and progress['machines'][0]['execution']['completed']==10

def test_branch_progress_is_scoped_and_includes_nonstandard_and_history(isolated):
    c=admin(isolated);first=create(c);b=c.get('/api/cutovers/'+first).json['branch_id']
    second=c.post('/api/cutovers',headers=headers(c),json={'branch_id':b,'pdv':'PDV 0001'}).json['id']
    extra=c.post('/api/cutovers',headers=headers(c),json={'branch_id':b,'pdv':'06'}).json['id']
    other=c.post('/api/branches',headers=headers(c),json={'code':'L9999','name':'Outra loja'}).json['id']
    c.post('/api/cutovers',headers=headers(c),json={'branch_id':other,'pdv':'02'})
    viewer,_=add_user(c,'progress-view@qa.test','viewer',isolated)
    data=viewer.get('/api/branches/'+b+'/cutover-progress').json
    assert len(data['executions'])==3 and {r['id'] for r in data['executions']}=={first,second,extra}
    assert len(data['machines'])==6 and data['machines'][-1]['pdv']=='06' and not data['machines'][-1]['planned']
    assert data['totals']['saved']==1 and len([m for m in data['machines'] if m['pdv']=='01'])==1
    assert c.get('/api/branches/missing/cutover-progress').status_code==404
    assert module.app.test_client().get('/api/branches/'+b+'/cutover-progress').status_code==401
