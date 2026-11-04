"""Emergency recovery through the server shell; never prints passwords or MFA secrets."""
import sys
from app import db, audit, init_db
if len(sys.argv)!=3 or sys.argv[1]!='reset-mfa':
    raise SystemExit('Uso: python manage.py reset-mfa email-do-administrador')
init_db()
email=sys.argv[2].strip().lower()
with db() as c:
    user=c.execute('SELECT id,role FROM ct_users WHERE email=%s',(email,)).fetchone()
    if not user or user['role']!='admin':raise SystemExit('Administrador não encontrado.')
    c.execute('UPDATE ct_auth SET secret=NULL,temp_secret=NULL,last_step=-1,recovery=%s,auth_version=auth_version+1 WHERE user_id=%s',('[]',user['id']))
    audit(c,'server-shell','recuperação administrativa de MFA',detail={'email':email})
print('MFA redefinido. Entre com sua senha para cadastrar o Authenticator novamente.')
