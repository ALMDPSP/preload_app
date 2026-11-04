import os, copy, json, re, time
os.environ['APP_ENV']='development'
os.environ['DATABASE_URL']=''
os.environ['SECRET_KEY']='unit-tests-only-secret-key'
os.environ['MFA_ENCRYPTION_KEY']='MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA='
os.environ['ADMIN_EMAIL']='admin@example.test'
os.environ['ADMIN_PASSWORD']='Temporary-admin-2026!'
import pytest, pyotp
from cryptography.fernet import Fernet
import app as module
CIPHER=Fernet(os.environ['MFA_ENCRYPTION_KEY'].encode())
ADMIN_PASSWORD='Permanent-admin-2026!'

@pytest.fixture(autouse=True)
def isolated(tmp_path,monkeypatch):
    monkeypatch.setenv('SQLITE_PATH',str(tmp_path/'test.sqlite'))
    clock=[1800000000.0]
    monkeypatch.setattr(time,'time',lambda:clock[0])
    module.init_db()
    return clock

def headers(c):
    with c.session_transaction() as s:return {'X-CSRF-Token':s['csrf']}

def post(c,path,data):return c.post(path,data={**data,'csrf':headers(c)['X-CSRF-Token']})

def auth_row(email):
    with module.db() as db:return dict(db.execute('SELECT a.* FROM ct_auth a JOIN ct_users u ON u.id=a.user_id WHERE u.email=%s',(email,)).fetchone())

def begin(email='admin@example.test',password='Temporary-admin-2026!'):
    c=module.app.test_client();c.get('/login')
    r=post(c,'/login',{'email':email,'password':password})
    assert r.status_code==302
    assert c.get('/api/cutovers').status_code==401
    return c

def complete(c,email,new_password=None,clock=None):
    r=c.get('/mfa')
    if r.location and r.location.endswith('/activate-password'):
        assert new_password
        assert post(c,'/activate-password',{'password':new_password,'confirmation':new_password}).status_code==302
    row=auth_row(email)
    if not row['secret']:
        r=c.get('/mfa/setup');assert r.status_code==200
        assert 'data:image/png;base64,' in r.text
        row=auth_row(email);secret=CIPHER.decrypt(row['temp_secret'].encode()).decode()
        r=post(c,'/mfa/setup',{'code':pyotp.TOTP(secret).at(time.time())})
        assert r.status_code==200 and 'Guarde seus' in r.text
        codes=re.findall(r'<code>([A-F0-9]{20})</code>',r.text)
        assert len(codes)==8
    else:
        secret=CIPHER.decrypt(row['secret'].encode()).decode()
        if int(time.time()//30)<=row['last_step']:
            assert clock is not None;clock[0]=(row['last_step']+1)*30
        r=post(c,'/mfa',{'code':pyotp.TOTP(secret).at(time.time())})
        assert r.status_code==302
        codes=[]
    assert c.get('/api/cutovers').status_code==200
    return codes

def admin(clock):
    c=begin();complete(c,'admin@example.test',ADMIN_PASSWORD,clock);return c

def add_user(c,email,role,clock):
    r=c.post('/api/users',headers=headers(c),json={'name':role,'email':email,'role':role,'password':'Temporary-user-2026!'})
    assert r.status_code==201
    user=begin(email,'Temporary-user-2026!');codes=complete(user,email,'Permanent-user-2026!',clock)
    return user,codes

def create(c):
    r=c.post('/api/cutovers',headers=headers(c),json={'title':'VD266 / PDV 01'})
    assert r.status_code==201
    return r.json['id']

def save(c,id,s,v):return c.put('/api/cutovers/'+id,headers=headers(c),json={'state':s,'version':v})

def test_password_activation_mfa_encryption_and_old_session(isolated):
    c=begin()
    assert c.get('/').status_code==302
    assert c.get('/mfa').location.endswith('/activate-password')
    codes=complete(c,'admin@example.test',ADMIN_PASSWORD,isolated)
    row=auth_row('admin@example.test')
    assert row['secret'].startswith('gAAAA') and row['temp_secret'] is None
    assert all(code not in row['recovery'] for code in codes)
    assert 'data-role="admin"' in c.get('/').text
    old=module.app.test_client()
    with old.session_transaction() as s:s['uid']=row['user_id']
    assert old.get('/api/cutovers').status_code==401
    assert module.app.test_client().get('/api/cutovers').status_code==401
    assert c.post('/api/cutovers',json={'title':'X'}).status_code==403
    assert c.get('/healthz').json['status']=='ok'

def test_roles_decisions_shared_data_conflicts_and_revocation(isolated):
    a=admin(isolated)
    manager,_=add_user(a,'manager@example.test','manager',isolated)
    operator,_=add_user(a,'operator@example.test','operator',isolated)
    viewer,_=add_user(a,'viewer@example.test','viewer',isolated)
    assert manager.get('/api/users').status_code==403
    assert operator.post('/api/cutovers',headers=headers(operator),json={'title':'X'}).status_code==403
    assert viewer.post('/api/cutovers',headers=headers(viewer),json={'title':'X'}).status_code==403
    id=create(manager);initial=manager.get('/api/cutovers/'+id).json
    s=copy.deepcopy(initial['state'])
    assert save(viewer,id,s,1).status_code==403
    s['tasks']['linx1']={'status':'Em andamento'}
    assert save(operator,id,s,1).json['version']==2
    assert save(manager,id,s,1).status_code==409
    assert viewer.get('/api/cutovers/'+id).json['state']['tasks']['linx1']['status']=='Em andamento'
    for key in ['orion1','orion2','orion3','linx1','linx2','linx3','linx4','linx5']:
        s['tasks'][key]={'status':'Concluído','owner':'Técnico','evidence':'Evidência validada'}
    s['decisions']['linx']={'value':'GO','owner':'Gestor','at':'2026-11-04T21:00','reason':'Pré-requisitos aprovados'}
    assert save(operator,id,s,2).status_code==403
    assert save(manager,id,s,2).json['version']==3
    s['tasks']['orion4']={'status':'Em andamento'}
    assert save(operator,id,s,3).json['version']==4
    s['decisions']['linx']['owner']='Operador tentou aprovar'
    assert save(operator,id,s,4).status_code==403
    assert viewer.get('/api/cutovers/'+id+'/audit').status_code==200
    uid=auth_row('operator@example.test')['user_id']
    assert a.put('/api/users/'+uid+'/role',headers=headers(a),json={'role':'viewer'}).status_code==200
    assert operator.get('/api/cutovers').status_code==401
    operator=begin('operator@example.test','Permanent-user-2026!');complete(operator,'operator@example.test',clock=isolated)
    assert operator.post('/api/cutovers',headers=headers(operator),json={'title':'X'}).status_code==403
    own=auth_row('admin@example.test')['user_id']
    assert a.put('/api/users/'+own+'/role',headers=headers(a),json={'role':'viewer'}).status_code==400


def test_otp_replay_recovery_and_admin_reset(isolated):
    a=admin(isolated);user,codes=add_user(a,'operator@example.test','operator',isolated)
    row=auth_row('operator@example.test');secret=CIPHER.decrypt(row['secret'].encode()).decode()
    second=begin('operator@example.test','Permanent-user-2026!')
    r=post(second,'/mfa',{'code':pyotp.TOTP(secret).at(time.time())})
    assert r.status_code==200 and 'inválido ou já utilizado' in r.text
    assert second.get('/api/cutovers').status_code==401
    assert post(second,'/mfa',{'code':codes[0],'recovery':'1'}).status_code==302
    third=begin('operator@example.test','Permanent-user-2026!')
    assert 'inválido ou já utilizado' in post(third,'/mfa',{'code':codes[0],'recovery':'1'}).text
    uid=row['user_id']
    assert a.post('/api/users/'+uid+'/reset',headers=headers(a),json={'kind':'mfa','admin_password':'wrong'}).status_code==403
    assert a.post('/api/users/'+uid+'/reset',headers=headers(a),json={'kind':'mfa','admin_password':ADMIN_PASSWORD}).status_code==200
    assert user.get('/api/cutovers').status_code==401
    assert third.get('/mfa').location.endswith('/login')
    second=begin('operator@example.test','Permanent-user-2026!');newcodes=complete(second,'operator@example.test',clock=isolated)
    assert auth_row('operator@example.test')['secret']!=row['secret']
    assert a.post('/api/users/'+uid+'/reset',headers=headers(a),json={'kind':'password','admin_password':ADMIN_PASSWORD,'password':'New-temporary-2026!'}).status_code==200
    assert second.get('/api/cutovers').status_code==401
    reset=begin('operator@example.test','New-temporary-2026!')
    assert reset.get('/mfa').location.endswith('/activate-password')
    complete(reset,'operator@example.test','New-permanent-2026!',isolated)


def test_migration_preserves_v1_users_and_cutovers(isolated):
    a=admin(isolated);id=create(a)
    with module.db() as c:
        original=dict(c.execute('SELECT * FROM ct_users WHERE email=%s',('admin@example.test',)).fetchone())
        cutover=dict(c.execute('SELECT * FROM ct_cutovers WHERE id=%s',(id,)).fetchone())
        c.execute('DROP TABLE ct_auth')
    module.init_db();module.init_db()
    with module.db() as c:
        assert dict(c.execute('SELECT * FROM ct_users WHERE id=%s',(original['id'],)).fetchone())==original
        assert dict(c.execute('SELECT * FROM ct_cutovers WHERE id=%s',(id,)).fetchone())==cutover
        assert c.execute('SELECT secret FROM ct_auth WHERE user_id=%s',(original['id'],)).fetchone()['secret'] is None
    assert a.get('/api/cutovers').status_code==401
    a=begin(password=ADMIN_PASSWORD);complete(a,'admin@example.test',clock=isolated)
    assert a.get('/api/cutovers/'+id).status_code==200


def test_throttle_block_password_and_session_expiration(isolated):
    a=admin(isolated);user,_=add_user(a,'operator@example.test','operator',isolated)
    c=begin('operator@example.test','Permanent-user-2026!')
    for _ in range(11):r=post(c,'/mfa',{'code':'XXXXXX'})
    assert 'Muitas tentativas' in r.text
    assert c.get('/api/cutovers').status_code==401
    uid=auth_row('operator@example.test')['user_id']
    assert a.put('/api/users/'+uid+'/active',headers=headers(a),json={'active':False}).status_code==200
    assert user.get('/api/cutovers').status_code==401
    assert a.put('/api/users/'+uid+'/active',headers=headers(a),json={'active':True}).status_code==200
    assert user.get('/api/cutovers').status_code==401
    pending=begin(password=ADMIN_PASSWORD)
    isolated[0]+=601
    assert pending.get('/mfa').location.endswith('/login')
    assert a.post('/api/password',headers=headers(a),json={'current':ADMIN_PASSWORD,'new':'New-admin-password-2026!'}).status_code==200
    assert a.get('/api/cutovers').status_code==401


def test_gates_and_invalid_data(isolated):
    a=admin(isolated);id=create(a);s=a.get('/api/cutovers/'+id).json['state']
    s['tasks']['orion4']={'status':'Em andamento'}
    assert save(a,id,s,1).status_code==400
    s['tasks']={'linx1':{'status':'Concluído'}}
    assert save(a,id,s,1).status_code==400
    s['tasks']={'linx1':{'status':'Qualquer'}}
    assert save(a,id,s,1).status_code==400
