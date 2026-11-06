import pytest
from test_app import isolated,admin,headers,auth_row,begin,post,complete,add_user
import app as module
from manage import reset_password
from werkzeug.security import check_password_hash

def test_admin_password_reset_preserves_mfa_data_revokes_session(isolated):
    a=admin(isolated)
    before=auth_row('admin@example.test')
    secret=before['secret']
    reset_password('ADMIN@example.test','Temporary-reset-2026!')
    after=auth_row('admin@example.test')
    assert after['secret']==secret and after['must_change']==1 and after['auth_version']==before['auth_version']+1
    assert a.get('/api/cutovers').status_code==401
    c=begin('admin@example.test','Temporary-reset-2026!')
    complete(c,'admin@example.test','Permanent-reset-2026!',isolated)
    assert c.get('/api/cutovers').status_code==200
    with module.db() as db:
        row=db.execute('SELECT password FROM ct_users WHERE email=%s',('admin@example.test',)).fetchone()
        assert check_password_hash(row['password'],'Permanent-reset-2026!')
        logs=db.execute('SELECT detail FROM ct_audit WHERE action=%s',('recuperação de senha administrativa',)).fetchall()
        assert logs and all('Temporary-reset-2026!' not in r['detail'] for r in logs)

def test_recovery_rejects_short_password_missing_and_non_admin(isolated):
    a=admin(isolated);add_user(a,'operator-reset@example.test','operator',isolated)
    for email,password in [('admin@example.test','short'),('missing@example.test','Temporary-reset-2026!'),('operator-reset@example.test','Temporary-reset-2026!')]:
        with pytest.raises(ValueError):reset_password(email,password)
