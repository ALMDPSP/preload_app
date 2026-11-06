import copy,io,json
from test_app import isolated,admin,add_user,headers,create
import app as module
from dashboard import pdv_number,approval_time

def finish(c,id):
    record=c.get('/api/cutovers/'+id).json
    state=record['state'];state['tasks']={id:{'status':'Concluído'} for id in module.IDS}
    state['decisions']={k:{'value':'GO','owner':'QA','at':'2026-11-06T10:00'} for k in ['linx','orion']}
    response=c.put('/api/cutovers/'+id,headers=headers(c),json={'version':record['version'],'state':state})
    assert response.status_code==200,response.json

def new_run(c,branch,pdv):
    r=c.post('/api/cutovers',headers=headers(c),json={'branch_id':branch,'pdv':pdv});assert r.status_code==201,r.json
    return r.json['id']

def test_unique_pdvs_default_four_and_latest_rejection(isolated):
    a=admin(isolated);first=create(a);branch=a.get('/api/cutovers/'+first).json['branch_id'];finish(a,first)
    d=a.get('/api/dashboard').json
    assert d['totals']['expected']==4 and d['totals']['ok']==1 and d['totals']['pending']==3
    assert [m['pdv'] for m in d['machines']]==['01','02','03','04'] and d['date_references']==0
    assert d['evolution'][-1]['cumulative_ok']==1
    second=new_run(a,branch,'PDV 1')
    assert a.get('/api/dashboard').json['totals']['ok']==0
    finish(a,second)
    assert a.get('/api/dashboard').json['totals']['ok']==1
    v=a.get('/api/cutovers/'+second).json['version']
    assert a.post('/api/cutovers/'+second+'/reject',headers=headers(a),json={'version':v,'reason':'Falha na operação'}).status_code==200
    d=a.get('/api/dashboard').json
    assert d['totals']['ok']==0 and d['totals']['pending']==4 and d['machines'][0]['status']=='Rejeitado'

def test_scope_plan_numbers_exceptions_permissions_and_pdf(isolated):
    a=admin(isolated);id=create(a);branch=a.get('/api/cutovers/'+id).json['branch_id'];finish(a,id)
    for code,status in [('NEW01','A inaugurar'),('NEW02','Inativa')]:
        assert a.post('/api/branches',headers=headers(a),json={'code':code,'name':code,'status':status}).status_code==201
    operator,_=add_user(a,'dash-op@example.test','operator',isolated)
    viewer,_=add_user(a,'dash-view@example.test','viewer',isolated)
    for c in [operator,viewer]:
        assert c.get('/api/dashboard').status_code==200
        assert c.put('/api/branches/'+branch+'/pdv-plan',headers=headers(c),json={'version':0,'pdvs':['01']}).status_code==403
    assert module.app.test_client().get('/api/dashboard').status_code==401
    assert module.app.test_client().get('/api/dashboard/executive.pdf').status_code==401
    assert a.put('/api/branches/'+branch+'/pdv-plan',json={'version':0,'pdvs':['01']}).status_code==403
    planurl='/api/branches/'+branch+'/pdv-plan'
    for values in [[],['0'],['1','01'],['word'],['10000']]:assert a.put(planurl,headers=headers(a),json={'version':0,'pdvs':values}).status_code==400
    assert a.put(planurl,headers=headers(a),json={'version':0,'pdvs':['01','05']}).status_code==200
    assert a.put(planurl,headers=headers(a),json={'version':0,'pdvs':['01']}).status_code==409
    five=new_run(a,branch,'5');finish(a,five)
    extra=new_run(a,branch,'99');finish(a,extra)
    unknown=new_run(a,branch,'Balcão')
    d=a.get('/api/dashboard').json
    assert d['totals']['expected']==2 and d['totals']['ok']==2 and d['totals']['stores_ok']==1 and d['totals']['exceptions']==2
    assert d['excluded']['inactive']==1 and d['excluded']['opening_soon']==1
    assert d['stores'][0]['pdvs']==['01','05']
    assert a.get('/api/dashboard?q=not-found').json['totals']['expected']==0
    assert a.get('/api/dashboard?uf=RJ').json['totals']['expected']==0
    from pypdf import PdfReader
    response=a.get('/api/dashboard/executive.pdf');assert response.status_code==200
    text=' '.join(p.extract_text() for p in PdfReader(io.BytesIO(response.data)).pages)
    assert 'VD266' not in text and '01, 05' not in text and 'Evolução' in text
    assert len(PdfReader(io.BytesIO(response.data)).pages)==1
    module.init_db();assert a.get('/api/dashboard').json['stores'][0]['pdvs']==['01','05']

def test_approval_dates_survive_note_edits_and_reference_fallback():
    completed={'meta':{},'tasks':{id:{'status':'Concluído'} for id in module.IDS},'decisions':{k:{'value':'GO','owner':'QA','at':'2026-11-06T10:00'} for k in ['linx','orion']}}
    previous=copy.deepcopy(completed);previous['decisions']['orion']={}
    events=[{'created_at':'2026-11-06T15:00:00+00:00','detail':json.dumps({'meta':{'antes':{},'depois':{'notes':'Test'}}})},{'created_at':'2026-11-05T15:00:00+00:00','detail':json.dumps({'decisions':{'antes':previous['decisions'],'depois':completed['decisions']}})}]
    assert approval_time(completed,events,'fallback',module.IDS)==('2026-11-05T15:00:00+00:00',False)
    assert approval_time(completed,[],'legacy-date',module.IDS)==('legacy-date',True)
    assert pdv_number('PDV-0001')=='01' and pdv_number('1')=='01' and pdv_number('01')=='01'
    assert pdv_number('0') is None and pdv_number('Orion') is None

def test_1800_active_stores_include_7200_unstarted_pdvs(isolated):
    a=admin(isolated)
    with module.db() as c:
        c.executemany('INSERT INTO ct_branches (id,code,name,created_at) VALUES (%s,%s,%s,%s)',[(f'bulk{i}',f'L{i:04d}',f'Loja {i}',module.now()) for i in range(1800)])
    data=a.get('/api/dashboard').json
    assert data['totals']['stores']==1800 and data['totals']['expected']==7200
    assert data['totals']['ok']==0 and data['totals']['pending']==7200
    assert len(data['machines'])==7200 and data['evolution']==[]

def test_read_and_expand_pdv_plan_preserves_cutovers(isolated):
    a=admin(isolated);id=create(a);branch=a.get('/api/cutovers/'+id).json['branch_id'];url='/api/branches/'+branch+'/pdv-plan'
    assert module.app.test_client().get(url).status_code==401
    viewer,_=add_user(a,'plan-read@example.test','viewer',isolated)
    initial=viewer.get(url);assert initial.status_code==200
    assert initial.json['pdvs']==['01','02','03','04'] and initial.json['plan_version']==0
    assert a.get('/api/branches/missing/pdv-plan').status_code==404
    six=['01','02','03','04','05','06']
    assert a.put(url,headers=headers(a),json={'pdvs':six,'version':0}).status_code==200
    assert a.get(url).json['pdvs']==six and a.get(url).json['plan_version']==1
    assert a.get('/api/dashboard').json['totals']['expected']==6
    assert a.get('/api/cutovers/'+id).status_code==200
    assert a.put(url,headers=headers(a),json={'pdvs':['01'],'version':0}).status_code==409
