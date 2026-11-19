from test_app import isolated, admin, add_user, headers, auth_row, create
from test_app import module
import json
import pytest


def test_delete_user_preserves_operations_and_revokes_access(isolated):
    actor=admin(isolated)
    target,_=add_user(actor,'deleted@example.test','operator',isolated)
    uid=auth_row('deleted@example.test')['user_id']
    cutover=create(target)
    before=actor.get('/api/cutovers/'+cutover).json
    with module.db() as c:
        branch=c.execute('SELECT branch_id FROM ct_cutover_branch WHERE cutover_id=%s',(cutover,)).fetchone()
        c.execute('INSERT INTO ct_pdv_assignments (branch_id,pdv,executor_id,validator_id,version,updated_at,updated_by) VALUES (%s,%s,%s,%s,1,%s,%s)',(branch['branch_id'],'01',uid,uid,module.now(),'deleted@example.test'))
    response=actor.delete('/api/users/'+uid,headers=headers(actor))
    assert response.status_code==200
    assert all(u['id']!=uid for u in actor.get('/api/users').json)
    assert target.get('/api/cutovers').status_code==401
    assert actor.get('/api/cutovers/'+cutover).json==before
    with module.db() as c:
        assert c.execute('SELECT user_id FROM ct_auth WHERE user_id=%s',(uid,)).fetchone() is None
        assignment=c.execute('SELECT executor_id,validator_id FROM ct_pdv_assignments WHERE branch_id=%s',(branch['branch_id'],)).fetchone()
        assert assignment['executor_id'] is None and assignment['validator_id'] is None
        log=c.execute('SELECT actor,detail FROM ct_audit WHERE action=%s',('exclusão de usuário',)).fetchone()
        assert log['actor']=='admin@example.test'
        assert json.loads(log['detail'])['email']=='deleted@example.test'
    assert actor.delete('/api/users/'+uid,headers=headers(actor)).status_code==404
    # Deleted email can be registered again without inheriting old credentials.
    response=actor.post('/api/users',headers=headers(actor),json={'name':'Nova conta','email':'deleted@example.test','role':'operator','password':'Temporary-user-2026!'})
    assert response.status_code==201
    assert auth_row('deleted@example.test')['user_id']!=uid


@pytest.mark.parametrize('role',['operator','manager','viewer'])
def test_delete_user_requires_administrator(isolated,role):
    actor=admin(isolated)
    other,_=add_user(actor,role+'@example.test',role,isolated)
    uid=auth_row('admin@example.test')['user_id']
    assert other.delete('/api/users/'+uid,headers=headers(other)).status_code==403
    assert len(actor.get('/api/users').json)==2


def test_delete_user_self_and_csrf_protection(isolated):
    actor=admin(isolated)
    uid=auth_row('admin@example.test')['user_id']
    assert actor.delete('/api/users/'+uid,headers=headers(actor)).status_code==400
    other,_=add_user(actor,'target@example.test','operator',isolated)
    target=auth_row('target@example.test')['user_id']
    assert actor.delete('/api/users/'+target).status_code==403
    assert len(actor.get('/api/users').json)==2
