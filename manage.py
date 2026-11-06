"""Recuperação administrativa pelo servidor, preservando registros e permitindo recuperar senha ou MFA separadamente."""
import sys,os
from getpass import getpass
from werkzeug.security import generate_password_hash
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


def reset_password(email,password):
    email=email.strip().lower()
    if not isinstance(password,str) or len(password)<12:raise ValueError('A senha temporária deve ter pelo menos 12 caracteres.')
    with db() as c:
        user=c.execute('SELECT id,role FROM ct_users WHERE email=%s',(email,)).fetchone()
        if not user or user['role']!='admin':raise ValueError('Administrador não encontrado. Confira o e-mail da conta já cadastrada.')
        c.execute('UPDATE ct_users SET password=%s,active=1 WHERE id=%s',(generate_password_hash(password),user['id']))
        c.execute('UPDATE ct_auth SET must_change=1,auth_version=auth_version+1 WHERE user_id=%s',(user['id'],))
        audit(c,'server-shell','recuperação de senha administrativa',detail={'email':email,'mfa_preservado':True})


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv
    if len(argv)!=2 or argv[0] not in ('reset-mfa','set-admin','reset-password'):
        raise SystemExit('Uso: python manage.py set-admin email-do-usuario | python manage.py reset-mfa email-do-administrador | python manage.py reset-password email-do-administrador')
    init_db()
    try:
        if argv[0]=='set-admin':
            set_admin(argv[1]);print('Acesso de Administrador aplicado. Entre novamente com sua senha e seu Authenticator atuais.')
        elif argv[0]=='reset-password':
            password=os.getenv('ADMIN_RESET_PASSWORD')
            if password is None:
                if not sys.stdin.isatty():raise ValueError('Defina ADMIN_RESET_PASSWORD ou execute em um terminal interativo.')
                password=getpass('Nova senha temporária (mínimo 12 caracteres): ')
                if password!=getpass('Confirme a senha temporária: '):raise ValueError('As senhas não conferem.')
            reset_password(argv[1],password)
            print('Senha temporária aplicada. Entre, crie sua senha definitiva e confirme o Authenticator atual. Remova ADMIN_RESET_PASSWORD e o comando temporário do deploy, se usados.')
        else:
            reset_mfa(argv[1]);print('MFA redefinido. Entre com sua senha para cadastrar o Authenticator novamente.')
    except ValueError as exc:raise SystemExit(str(exc))


if __name__=='__main__':main()
