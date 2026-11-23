from test_app import isolated,admin,create,headers
from test_dashboard import finish,new_run
from test_rollout_base import form,put


def test_completed_stores_requires_all_planned_orion_ok_and_updates(isolated):
    client=admin(isolated);first=create(client)
    branch=client.get('/api/cutovers/'+first).json['branch_id']
    plan='/api/branches/'+branch+'/pdv-plan'
    assert client.put(plan,headers=headers(client),json={'version':0,'pdvs':['01','02']}).status_code==200
    # Declaring every PDV implanted must not mark a store as fully Orion OK.
    body=form(client,branch)
    for machine in body['machines']:machine['status']='Implantado'
    assert put(client,branch,body).status_code==200
    assert client.get('/api/dashboard?compact=1').json['totals']['stores_ok']==0
    assert client.get('/api/dashboard/completed-stores').json['total']==0
    finish(client,first)
    assert client.get('/api/dashboard/completed-stores').json['total']==0
    second=new_run(client,branch,'02');finish(client,second)
    data=client.get('/api/dashboard/completed-stores').json
    assert data['total']==1 and len(data['rows'])==1
    assert data['rows'][0]['id']==branch and data['rows'][0]['ok']==data['rows'][0]['expected']==2
    assert client.get('/api/dashboard?compact=1').json['totals']['stores_ok']==1
    assert client.get('/api/dashboard/completed-stores?store_q=VD266').json['total']==1
    assert client.get('/api/dashboard/completed-stores?store_q=absent').json['total']==0
    assert client.get('/api/dashboard/completed-stores?uf=RJ').json['total']==0
    # Expanding the planned park immediately removes the store until the new PDV is OK.
    assert client.put(plan,headers=headers(client),json={'version':1,'pdvs':['01','02','03']}).status_code==200
    assert client.get('/api/dashboard?compact=1').json['totals']['stores_ok']==0
    assert client.get('/api/dashboard/completed-stores').json['total']==0
    assert client.get('/api/cutovers/'+first).status_code==200
    assert client.get('/api/cutovers/'+second).status_code==200
    assert client.application.test_client().get('/api/dashboard/completed-stores').status_code==401


def test_completed_stores_reopens_when_pdv_loses_approval(isolated):
    client=admin(isolated);cutover=create(client)
    row=client.get('/api/cutovers/'+cutover).json
    branch=row['branch_id']
    assert client.put('/api/branches/'+branch+'/pdv-plan',headers=headers(client),json={'version':0,'pdvs':['01']}).status_code==200
    finish(client,cutover)
    assert client.get('/api/dashboard/completed-stores').json['total']==1
    saved=client.get('/api/cutovers/'+cutover).json
    saved['state']['tasks']['orion6']['status']='Bloqueado'
    saved['state']['decisions']['orion']={}
    assert client.put('/api/cutovers/'+cutover,headers=headers(client),json={'version':saved['version'],'state':saved['state']}).status_code==200
    assert client.get('/api/dashboard/completed-stores').json['total']==0
    assert client.get('/api/dashboard?compact=1').json['totals']['stores_ok']==0
