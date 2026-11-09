from test_app import isolated,admin,create,headers,add_user
from test_dashboard import finish
import app as module

def form(c,b):
    d=c.get('/api/rollout-base/branches/'+b).json
    return {'version':d['version'],'plan_version':d['plan_version'],'regional':d['regional'],'gr':d['gr'],'machines':d['machines']}

def put(c,b,body):return c.put('/api/rollout-base/branches/'+b,headers=headers(c),json=body)

def test_declared_implantation_is_separate_from_acceptance_and_deduplicated(isolated):
    c=admin(isolated);id=create(c);b=c.get('/api/cutovers/'+id).json['branch_id'];body=form(c,b);body.update(gr='Oliveira Junior',regional='SP Centro');body['machines'][0].update(status='Implantado',installed_version='Orion 1.0',deployed_at='2026-11-09')
    assert put(c,b,body).status_code==200
    d=c.get('/api/dashboard?compact=1').json
    assert d['totals']['ok']==0 and d['rollout_base']['pdvs_deployed']==1
    assert d['rollout_base']['pdvs_expected']==4 and d['rollout_base']['pdvs_percent']==25
    assert d['rollout_base']['stores_updated']==1 and d['rollout_base']['stores_percent']==100
    assert c.get('/api/cutovers/'+id).json['state']['tasks']=={}
    finish(c,id);d=c.get('/api/dashboard?compact=1').json
    assert d['totals']['ok']==1 and d['rollout_base']['pdvs_deployed']==1
    assert d['rollout_base']['versions']==[{'name':'Orion 1.0','count':1,'percent':100.0}]

def test_gr_regional_denominators_and_uninformed_versions_are_consistent(isolated):
    c=admin(isolated);id=create(c);b=c.get('/api/cutovers/'+id).json['branch_id']
    others=[c.post('/api/branches',headers=headers(c),json={'code':code,'name':code,'uf':uf}).json['id'] for code,uf in [('L0002','SP'),('L0003','RJ')]]
    for i,branch in enumerate([b,*others]):
        body=form(c,branch);body.update(gr='Mesmo GR' if i<2 else 'Outro GR',regional='SP Centro' if i<2 else 'RJ Centro')
        if i==0:
            for m in body['machines'][:2]:m.update(status='Implantado',installed_version='v1')
        assert put(c,branch,body).status_code==200
    r=c.post('/api/cutovers',headers=headers(c),json={'branch_id':others[1],'pdv':'01'});finish(c,r.json['id'])
    d=c.get('/api/dashboard?compact=1').json['rollout_base']
    assert d['pdvs_expected']==12 and d['pdvs_deployed']==3 and d['stores_updated']==2 and d['stores_percent']==66.7
    assert d['deployed_without_version']==1 and sum(v['count'] for v in d['versions'])+d['deployed_without_version']==d['pdvs_deployed']
    gr=next(g for g in d['by_gr'] if g['name']=='MESMO GR');assert gr['stores_expected']==2 and gr['stores_updated']==1 and gr['percent']==50
    assert sum(g['stores_expected'] for g in d['by_regional'])==3
    scoped=c.get('/api/dashboard?compact=1&uf=RJ').json['rollout_base'];assert scoped['stores_expected']==1 and scoped['pdvs_deployed']==1
    empty=c.get('/api/dashboard?compact=1&uf=AC').json['rollout_base'];assert empty['stores_percent']==0 and empty['pdvs_percent']==0 and empty['by_gr']==[]

def test_role_permissions_and_conflicts_never_partially_save(isolated):
    c=admin(isolated);id=create(c);b=c.get('/api/cutovers/'+id).json['branch_id'];body=form(c,b)
    operator,_=add_user(c,'base-operator@qa.test','operator',isolated);viewer,_=add_user(c,'base-viewer@qa.test','viewer',isolated)
    assert viewer.get('/api/rollout-base').status_code==200
    assert put(viewer,b,body).status_code==403
    assert put(operator,b,{**body,'gr':'Alteração proibida'}).status_code==403
    body['machines'][0].update(status='Implantado',installed_version='build-1');assert put(operator,b,body).status_code==200
    assert put(c,b,body).status_code==409
    fresh=form(c,b);fresh['gr']='Não deve salvar';fresh['machines'][0]['version']=0
    assert put(c,b,fresh).status_code==409
    assert form(c,b)['gr']=='' and form(c,b)['machines'][0]['installed_version']=='build-1'
    assert module.app.test_client().get('/api/rollout-base').status_code==401
    assert c.put('/api/rollout-base/branches/'+b,json=form(c,b)).status_code==403

def test_validation_plan_change_and_missing_registration(isolated):
    c=admin(isolated);id=create(c);b=c.get('/api/cutovers/'+id).json['branch_id'];body=form(c,b)
    bad={**body,'machines':[{**body['machines'][0],'pdv':'05'}]};assert put(c,b,bad).status_code==400
    assert put(c,b,{**body,'machines':[body['machines'][0],body['machines'][0]]}).status_code==400
    assert put(c,b,{**body,'machines':[{**body['machines'][0],'deployed_at':'2026-99-99'}]}).status_code==400
    assert put(c,b,{**body,'machines':[{**body['machines'][0],'status':'Qualquer'}]}).status_code==400
    assert put(c,b,{**body,'regional':[]}).status_code==400
    assert c.get('/api/rollout-base/branches/absent').status_code==404
    assert c.put('/api/branches/'+b+'/pdv-plan',headers=headers(c),json={'pdvs':['01','02','03','04','05'],'version':0}).status_code==200
    assert put(c,b,body).status_code==409
    d=c.get('/api/dashboard?compact=1').json['rollout_base'];assert d['stores_missing_organization']==1 and d['by_gr'][0]['name']=='Não informado' and d['pdvs_expected']==5

def test_base_filters_pagination_inactive_scope_and_edits(isolated):
    c=admin(isolated);id=create(c);b=c.get('/api/cutovers/'+id).json['branch_id'];body=form(c,b);body.update(gr='Ana',regional='SP Centro');body['machines'][0].update(status='Implantado',installed_version='1.0');assert put(c,b,body).status_code==200
    assert c.get('/api/rollout-base?gr=ana&regional=sp%20centro&q=VD266').json['total']==1
    assert c.get('/api/rollout-base?regional=RJ').json['total']==0
    with module.db() as db:
        for i in range(30):db.execute('INSERT INTO ct_branches (id,code,name,created_at) VALUES (%s,%s,%s,%s)',('qa'+str(i),'Q'+str(i).zfill(3),'QA',module.now()))
    page=c.get('/api/rollout-base').json;assert len(page['rows'])==25 and page['pages']==2
    assert len(c.get('/api/rollout-base?page=2').json['rows'])==6
    body=form(c,b);body['machines'][0].update(status='Pendente',installed_version='');assert put(c,b,body).status_code==200
    assert c.get('/api/dashboard?compact=1&q=VD266').json['rollout_base']['pdvs_deployed']==0
    assert c.put('/api/branches/'+b,headers=headers(c),json={'name':'Loja','city':'','uf':'SP','status':'Inativa'}).status_code==200
    assert c.get('/api/dashboard?compact=1&q=VD266').json['rollout_base']['stores_expected']==0
    assert c.get('/api/rollout-base?q=VD266').json['rows'][0]['in_scope'] is False
