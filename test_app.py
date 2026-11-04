import os, tempfile, copy
os.environ['APP_ENV']='development'
os.environ['ADMIN_EMAIL']='admin@example.test'
os.environ['ADMIN_PASSWORD']='Test-password-2026!'
os.environ['SQLITE_PATH']=tempfile.mktemp(suffix='.sqlite')
import app as module

def client_login(email='admin@example.test',password='Test-password-2026!'):
    client=module.app.test_client()
    client.get('/login')
    with client.session_transaction() as s:csrf=s['csrf']
    response=client.post('/login',data={'email':email,'password':password,'csrf':csrf})
    assert response.status_code==302
    with client.session_transaction() as s:csrf=s['csrf']
    return client,{'X-CSRF-Token':csrf}

def test_shared_cutover_security_conflicts_and_gates():
    module.init_db()
    a,h=client_login()
    assert module.app.test_client().get('/api/cutovers').status_code==401
    assert a.post('/api/cutovers',json={'title':'VD266'}).status_code==403
    assert a.get('/').status_code==200
    assert a.post('/api/users',headers=h,json={'name':'Operador','email':'operator@example.test','password':'Operator-password-2026!','role':'operator'}).status_code==201
    b,hb=client_login('operator@example.test','Operator-password-2026!')
    assert b.get('/api/users').status_code==403
    id=a.post('/api/cutovers',headers=h,json={'title':'VD266 / PDV01'}).json['id']
    original=a.get('/api/cutovers/'+id).json
    state=copy.deepcopy(original['state'])
    state['tasks']['orion4']={'status':'Em andamento'}
    assert a.put('/api/cutovers/'+id,headers=h,json={'state':state,'version':1}).status_code==400
    state=copy.deepcopy(original['state'])
    for key in ['orion1','orion2','orion3','linx1','linx2','linx3','linx4','linx5']:
        state['tasks'][key]={'status':'Concluído','owner':'Técnico','evidence':'Teste validado'}
    state['decisions']['linx']={'value':'GO','owner':'Coordenador','at':'2026-11-04T21:00','reason':'Pré-requisitos aprovados'}
    state['tasks']['orion4']={'status':'Em andamento'}
    assert a.put('/api/cutovers/'+id,headers=h,json={'state':state,'version':1}).json['version']==2
    assert b.get('/api/cutovers/'+id).json['state']['tasks']['orion4']['status']=='Em andamento'
    assert b.put('/api/cutovers/'+id,headers=hb,json={'state':state,'version':1}).status_code==409
    assert a.get('/api/cutovers/'+id+'/audit').json[0]['actor']=='admin@example.test'
    operator=next(u for u in a.get('/api/users').json if u['email']=='operator@example.test')
    assert operator['last_login']
    assert a.put('/api/users/'+operator['id']+'/active',headers=h,json={'active':False}).status_code==200
    assert b.get('/api/cutovers').status_code==401
    assert a.post('/api/password',headers=h,json={'current':'Test-password-2026!','new':'New-password-2026!'}).status_code==200
    assert a.get('/api/cutovers').status_code==401
    client_login(password='New-password-2026!')

def test_login_throttling_and_invalid_status():
    module.init_db()
    c=module.app.test_client();c.get('/login')
    with c.session_transaction() as s:token=s['csrf']
    for _ in range(16):r=c.post('/login',data={'email':'missing@example.test','password':'wrong','csrf':token},environ_base={'REMOTE_ADDR':'192.0.2.55'})
    assert 'Muitas tentativas' in r.text
    try:module.valid_state({'meta':{'branch':'X'},'tasks':{'linx1':{'status':'Qualquer'}},'decisions':{'linx':{},'orion':{}}})
    except ValueError:pass
    else:raise AssertionError('Status inválido aceito')
