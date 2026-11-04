"""Password activation, encrypted TOTP, one-use recovery and access administration."""
import os, base64, hashlib, io, json, secrets, time
import pyotp
import qrcode
from cryptography.fernet import Fernet
from flask import request, session, redirect, render_template, g, jsonify
from werkzeug.security import check_password_hash, generate_password_hash


def build_mfa_cipher(secret_key, configured=None):
    # Preserve the explicit Fernet key accepted by v2.0. Without it, derive a
    # stable encryption key from SECRET_KEY, as in Controle de Ativos.
    key = configured.encode() if configured else base64.urlsafe_b64encode(hashlib.sha256(secret_key.encode()).digest())
    return Fernet(key)


def register_auth(app, core):
    db, audit, error, token, now = (core[k] for k in ['db','audit','error','token','now'])
    configured=os.getenv('MFA_ENCRYPTION_KEY')
    cipher=build_mfa_cipher(app.secret_key, configured)
    def encrypt(value):return cipher.encrypt(value.encode()).decode()
    def decrypt(value):return cipher.decrypt(value.encode()).decode()
    def digest(value):return hashlib.sha256(value.strip().replace('-','').upper().encode()).hexdigest()
    lock=' FOR UPDATE' if core['DATABASE'] else ''

    def pending():
        if not session.get('pending_uid') or session.get('pending_until',0)<time.time():
            session.clear();return None
        with db() as c:
            row=c.execute('SELECT u.id,u.email,u.active,u.password,a.* FROM ct_users u JOIN ct_auth a ON a.user_id=u.id WHERE u.id=%s',(session['pending_uid'],)).fetchone()
        if not row or not row['active'] or row['auth_version']!=session.get('pending_version'):
            session.clear();return None
        return dict(row)

    def throttle(c, uid):
        key='mfa:'+uid
        at=time.time()
        row=c.execute('INSERT INTO ct_attempts (key,count,window_start) VALUES (%s,1,%s) ON CONFLICT(key) DO UPDATE SET count=CASE WHEN ct_attempts.window_start < %s THEN 1 ELSE ct_attempts.count+1 END,window_start=CASE WHEN ct_attempts.window_start < %s THEN %s ELSE ct_attempts.window_start END RETURNING count',(key,at,at-900,at-900,at)).fetchone()
        return row['count']<=10

    def verify_step(secret,code,last):
        if len(code)!=6 or not code.isascii() or not code.isdigit():return None
        current=int(time.time()//30);totp=pyotp.TOTP(secret)
        for step in [current,current-1,current+1]:
            if step>last and secrets.compare_digest(totp.at(step*30),code):return step
        return None

    def finish(c, uid, email, auth_version):
        session.clear();session['uid']=uid;session['mfa_verified']=True;session['auth_version']=auth_version;session.permanent=True;token()
        c.execute('UPDATE ct_users SET last_login=%s WHERE id=%s',(now(),uid))
        c.execute('DELETE FROM ct_attempts WHERE key=%s',('mfa:'+uid,))
        audit(c,email,'login com MFA')

    @app.route('/activate-password',methods=['GET','POST'])
    def activate_password():
        user=pending()
        if not user:return redirect('/login')
        if not user['must_change']:return redirect('/mfa')
        message=''
        if request.method=='POST':
            pw=request.form.get('password','');confirmation=request.form.get('confirmation','')
            if len(pw)<12 or pw!=confirmation or check_password_hash(user['password'],pw):message='Use uma nova senha com pelo menos 12 caracteres, diferente da temporária, e confirme corretamente.'
            else:
                with db() as c:
                    auth=c.execute('SELECT auth_version FROM ct_auth WHERE user_id=%s'+lock,(user['id'],)).fetchone()
                    if auth['auth_version']!=session.get('pending_version'):session.clear();return redirect('/login')
                    c.execute('UPDATE ct_users SET password=%s WHERE id=%s',(generate_password_hash(pw),user['id']))
                    c.execute('UPDATE ct_auth SET must_change=0,auth_version=auth_version+1 WHERE user_id=%s',(user['id'],))
                    session['pending_version']=auth['auth_version']+1
                    audit(c,user['email'],'ativação de senha')
                return redirect('/mfa')
        return render_template('mfa.html',mode='password',csrf=token(),message=message,email=user['email'])

    @app.route('/mfa',methods=['GET','POST'])
    def mfa():
        if g.user:return redirect('/')
        user=pending()
        if not user:return redirect('/login')
        if user['must_change']:return redirect('/activate-password')
        if not user['secret']:return redirect('/mfa/setup')
        message=''
        if request.method=='POST':
            code=request.form.get('code','').strip();recovery=request.form.get('recovery')=='1'
            with db() as c:
                allowed=throttle(c,user['id'])
                auth=c.execute('SELECT * FROM ct_auth WHERE user_id=%s'+lock,(user['id'],)).fetchone()
                active=c.execute('SELECT active FROM ct_users WHERE id=%s',(user['id'],)).fetchone()
                if not active['active'] or auth['auth_version']!=session.get('pending_version') or not auth['secret']:session.clear();return redirect('/login')
                if not allowed:message='Muitas tentativas. Aguarde 15 minutos.'
                elif recovery:
                    hashes=json.loads(auth['recovery']);hashed=digest(code)
                    if hashed in hashes:
                        hashes.remove(hashed);c.execute('UPDATE ct_auth SET recovery=%s WHERE user_id=%s',(json.dumps(hashes),user['id']))
                        audit(c,user['email'],'uso de código de recuperação')
                        finish(c,user['id'],user['email'],auth['auth_version']);return redirect('/')
                    message='Código inválido ou já utilizado.'
                else:
                    step=verify_step(decrypt(auth['secret']),code,auth['last_step'])
                    if step is not None:
                        c.execute('UPDATE ct_auth SET last_step=%s WHERE user_id=%s',(step,user['id']))
                        finish(c,user['id'],user['email'],auth['auth_version']);return redirect('/')
                    message='Código inválido ou já utilizado. Aguarde o próximo código do aplicativo.'
        return render_template('mfa.html',mode='verify',csrf=token(),message=message,email=user['email'])

    @app.route('/mfa/setup',methods=['GET','POST'])
    def setup_mfa():
        if g.user:return redirect('/')
        user=pending()
        if not user:return redirect('/login')
        if user['must_change']:return redirect('/activate-password')
        if user['secret']:return redirect('/mfa')
        message='';codes=None
        with db() as c:
            auth=c.execute('SELECT * FROM ct_auth WHERE user_id=%s'+lock,(user['id'],)).fetchone()
            active=c.execute('SELECT active FROM ct_users WHERE id=%s',(user['id'],)).fetchone()
            if not active['active'] or auth['auth_version']!=session.get('pending_version'):session.clear();return redirect('/login')
            if auth['secret']:return redirect('/mfa')
            secret=decrypt(auth['temp_secret']) if auth['temp_secret'] else pyotp.random_base32()
            if not auth['temp_secret']:c.execute('UPDATE ct_auth SET temp_secret=%s WHERE user_id=%s',(encrypt(secret),user['id']))
            if request.method=='POST':
                allowed=throttle(c,user['id'])
                step=verify_step(secret,request.form.get('code','').strip(),-1) if allowed else None
                if not allowed:message='Muitas tentativas. Aguarde 15 minutos.'
                elif step is None:message='Código inválido. Confira o aplicativo e tente novamente.'
                else:
                    codes=[secrets.token_hex(10).upper() for _ in range(8)]
                    c.execute('UPDATE ct_auth SET secret=%s,temp_secret=NULL,last_step=%s,recovery=%s WHERE user_id=%s',(encrypt(secret),step,json.dumps([digest(code) for code in codes]),user['id']))
                    audit(c,user['email'],'ativação de MFA')
                    finish(c,user['id'],user['email'],auth['auth_version'])
        if codes:return render_template('mfa.html',mode='recovery',codes=codes,csrf=token(),email=user['email'])
        uri=pyotp.TOTP(secret).provisioning_uri(name=user['email'],issuer_name='DPSP Cutover')
        output=io.BytesIO();qrcode.make(uri).save(output,format='PNG')
        return render_template('mfa.html',mode='setup',qr=base64.b64encode(output.getvalue()).decode(),secret=secret,csrf=token(),message=message,email=user['email'])

    @app.put('/api/users/<uid>/role')
    def change_role(uid):
        if g.user['role']!='admin':return error('Acesso exclusivo do administrador.',403)
        if uid==g.user['id']:return error('Não é possível alterar seu próprio perfil.')
        role=(request.get_json() or {}).get('role')
        if role not in ['admin','manager','operator','viewer']:return error('Perfil inválido.')
        with db() as c:
            row=c.execute('SELECT id FROM ct_users WHERE id=%s',(uid,)).fetchone()
            if not row:return error('Usuário não encontrado.',404)
            c.execute('UPDATE ct_users SET role=%s WHERE id=%s',(role,uid))
            c.execute('UPDATE ct_auth SET auth_version=auth_version+1 WHERE user_id=%s',(uid,))
            audit(c,g.user['email'],'alteração de perfil',detail={'id':uid,'role':role})
        return jsonify(ok=True)

    @app.post('/api/users/<uid>/reset')
    def reset_access(uid):
        if g.user['role']!='admin':return error('Acesso exclusivo do administrador.',403)
        if uid==g.user['id']:return error('Use Minha senha ou a recuperação administrativa pelo servidor para seu próprio acesso.')
        body=request.get_json() or {};kind=body.get('kind')
        if kind not in ['mfa','password']:return error('Ação inválida.')
        pw=str(body.get('password',''))
        if kind=='password' and len(pw)<12:return error('Use uma senha temporária com pelo menos 12 caracteres.')
        with db() as c:
            actor=c.execute('SELECT password FROM ct_users WHERE id=%s',(g.user['id'],)).fetchone()
            if not check_password_hash(actor['password'],str(body.get('admin_password',''))):return error('Senha do administrador incorreta.',403)
            if not c.execute('SELECT id FROM ct_users WHERE id=%s',(uid,)).fetchone():return error('Usuário não encontrado.',404)
            if kind=='mfa':
                c.execute('UPDATE ct_auth SET secret=NULL,temp_secret=NULL,last_step=-1,recovery=%s,auth_version=auth_version+1 WHERE user_id=%s',('[]',uid))
            else:
                c.execute('UPDATE ct_users SET password=%s WHERE id=%s',(generate_password_hash(pw),uid))
                c.execute('UPDATE ct_auth SET must_change=1,auth_version=auth_version+1 WHERE user_id=%s',(uid,))
            audit(c,g.user['email'],'redefinição de '+kind,detail={'id':uid})
        return jsonify(ok=True)
