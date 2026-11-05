"""Recuperação administrativa pelo servidor, preservando senhas e registros."""
import sys
from app import db, audit, init_db


def set_admin(email):
    email=email.strip().lower()
    with db() as c:
        user=c.execute('SELECT id,role,active FROM ct_users WHERE email=%s',(email,)).fetchone()
        if not user:raise ValueError('Usuário não encontrado. Use o e-mail de uma conta já cadastrada no Cutover.')
        c.execute('UPDATE ct_users SET role=%s,active=1 WHERE id=%s',('admin',user['id']))
        c.execute('UPDATE ct_auth SET auth_version=auth_version+1 WHERE user_id=%s',(user['id'],))
        audit(c,'server-shell','recuperação de acesso administrativo',detail={'email':email,'perfil_anterior':user['role'],'ativo_anterior':user['active'],'novo_perfil':'admin'})


def reset_mfa(email):
    email=email.strip().lower()
    with db() as c:
        user=c.execute('SELECT id,role FROM ct_users WHERE email=%s',(email,)).fetchone()
        if not user or user['role']!='admin':raise ValueError('Administrador não encontrado.')
        c.execute('UPDATE ct_auth SET secret=NULL,temp_secret=NULL,last_step=-1,recovery=%s,auth_version=auth_version+1 WHERE user_id=%s',('[]',user['id']))
        audit(c,'server-shell','recuperação administrativa de MFA',detail={'email':email})


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv
    if len(argv)!=2 or argv[0] not in ('reset-mfa','set-admin'):
        raise SystemExit('Uso: python manage.py set-admin email-do-usuario | python manage.py reset-mfa email-do-administrador')
    init_db()
    try:
        if argv[0]=='set-admin':
            set_admin(argv[1]);print('Acesso de Administrador aplicado. Entre novamente com sua senha e seu Authenticator atuais.')
        else:
            reset_mfa(argv[1]);print('MFA redefinido. Entre com sua senha para cadastrar o Authenticator novamente.')
    except ValueError as exc:raise SystemExit(str(exc))


if __name__=='__main__':main()
