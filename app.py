import os, json, secrets, sqlite3, time
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from functools import wraps
from pathlib import Path
from flask import Flask, request, session, jsonify, render_template, redirect, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

ROOT = Path(__file__).parent
app = Flask(__name__)
DEV = os.getenv('APP_ENV') == 'development'
if not os.getenv('SECRET_KEY') and not DEV:
    raise RuntimeError('Configure SECRET_KEY antes de iniciar.')
app.secret_key = os.getenv('SECRET_KEY') or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_SECURE=not DEV, SESSION_COOKIE_HTTPONLY=True,
                  SESSION_COOKIE_SAMESITE='Lax', PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
                  MAX_CONTENT_LENGTH=2 * 1024 * 1024)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
DATABASE = os.getenv('DATABASE_URL', '')
if not DATABASE and not DEV:
    raise RuntimeError('Configure DATABASE_URL do Neon. Não há banco local em produção.')
SCHEMA = [
    'CREATE TABLE IF NOT EXISTS ct_users (id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1, last_login TEXT)',
    'CREATE TABLE IF NOT EXISTS ct_cutovers (id TEXT PRIMARY KEY, title TEXT NOT NULL, state TEXT NOT NULL, version INTEGER NOT NULL, updated_at TEXT NOT NULL, updated_by TEXT NOT NULL)',
    'CREATE TABLE IF NOT EXISTS ct_audit (id TEXT PRIMARY KEY, cutover_id TEXT, actor TEXT NOT NULL, action TEXT NOT NULL, created_at TEXT NOT NULL, detail TEXT NOT NULL)',
    'CREATE TABLE IF NOT EXISTS ct_attempts (key TEXT PRIMARY KEY, count INTEGER NOT NULL, window_start REAL NOT NULL)'
]
SOURCE = json.loads((ROOT / 'data.json').read_text())
IDS = [t['id'] for t in SOURCE['orion'] + SOURCE['linx']]
STATUSES = ['Pendente', 'Em andamento', 'Concluído', 'Bloqueado']

def now(): return datetime.now(timezone.utc).isoformat()

@contextmanager
def db():
    if DATABASE:
        import psycopg
        from psycopg.rows import dict_row
        conn = psycopg.connect(DATABASE, connect_timeout=15, row_factory=dict_row)
    else:
        conn = sqlite3.connect(os.getenv('SQLITE_PATH', str(ROOT / 'dev.sqlite')), timeout=15)
        conn.row_factory = sqlite3.Row
    class Connection:
        def execute(self, sql, params=()):
            return conn.execute(sql if DATABASE else sql.replace('%s', '?'), params)
    try:
        yield Connection()
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally: conn.close()

def init_db():
    with db() as c:
        for sql in SCHEMA: c.execute(sql)
        email = os.getenv('ADMIN_EMAIL', '').strip().lower()
        password = os.getenv('ADMIN_PASSWORD', '')
        if not c.execute('SELECT id FROM ct_users LIMIT 1').fetchone():
            if not email or len(password) < 12:
                raise RuntimeError('Primeiro acesso: defina ADMIN_EMAIL e ADMIN_PASSWORD com pelo menos 12 caracteres.')
            c.execute('INSERT INTO ct_users (id,email,name,password,role) VALUES (%s,%s,%s,%s,%s)',
                      (secrets.token_hex(16), email, os.getenv('ADMIN_NAME','Administrador'), generate_password_hash(password), 'admin'))

def token():
    if 'csrf' not in session: session['csrf'] = secrets.token_hex(32)
    return session['csrf']

def audit(c, actor, action, cutover=None, detail=None):
    c.execute('INSERT INTO ct_audit VALUES (%s,%s,%s,%s,%s,%s)',
              (secrets.token_hex(16), cutover, actor, action, now(), json.dumps(detail or {}, ensure_ascii=False)))

def error(message, code=400): return jsonify(error=message), code

@app.before_request
def protect():
    g.user = None
    if session.get('uid'):
        with db() as c: row = c.execute('SELECT id,email,name,role,active,last_login FROM ct_users WHERE id=%s', (session['uid'],)).fetchone()
        if row and row['active']: g.user = dict(row)
        else: session.clear()
    if request.method in ('POST','PUT','DELETE','PATCH'):
        supplied = request.headers.get('X-CSRF-Token') or request.form.get('csrf','')
        if not secrets.compare_digest(str(session.get('csrf','!')), supplied):
            return error('Sessão expirada. Atualize a página e tente novamente.',403)
    if request.path.startswith('/api/') and not g.user: return error('Faça login novamente.',401)

@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='same-origin'
    response.headers['Cache-Control']='no-store'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    if not DEV: response.headers['Strict-Transport-Security']='max-age=31536000'
    return response

@app.get('/healthz')
def health():
    try:
        with db() as c: c.execute('SELECT 1').fetchone()
        return jsonify(status='ok')
    except Exception: return error('Banco indisponível',503)

@app.route('/login', methods=['GET','POST'])
def login():
    if g.user: return redirect('/')
    message = ''
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        key = 'login:' + (request.remote_addr or 'unknown')
        with db() as c:
            # Atomic counter works across workers; counts attempts for a 15-minute window.
            row = c.execute('INSERT INTO ct_attempts (key,count,window_start) VALUES (%s,1,%s) ON CONFLICT(key) DO UPDATE SET count=CASE WHEN ct_attempts.window_start < %s THEN 1 ELSE ct_attempts.count+1 END, window_start=CASE WHEN ct_attempts.window_start < %s THEN %s ELSE ct_attempts.window_start END RETURNING count', (key,time.time(),time.time()-900,time.time()-900,time.time())).fetchone()
            user = c.execute('SELECT * FROM ct_users WHERE email=%s',(email,)).fetchone()
            if row['count'] > 15: message='Muitas tentativas. Aguarde 15 minutos.'
            elif user and user['active'] and check_password_hash(user['password'],request.form.get('password','')):
                session.clear();session['uid']=user['id'];session.permanent=True;token()
                c.execute('UPDATE ct_users SET last_login=%s WHERE id=%s',(now(),user['id']))
                c.execute('DELETE FROM ct_attempts WHERE key=%s',(key,))
                audit(c,email,'login')
                return redirect('/')
            else: message='E-mail ou senha inválidos.'
    return render_template('login.html',csrf=token(),message=message)

@app.post('/logout')
def logout(): session.clear();return redirect('/login')

@app.get('/')
def index():
    if not g.user:return redirect('/login')
    return render_template('index.html',csrf=token(),user=g.user)

def valid_state(s):
    if not isinstance(s,dict) or not all(isinstance(s.get(k),dict) for k in ('meta','tasks','decisions')):raise ValueError('Estrutura de dados inválida.')
    if len(json.dumps(s))>500000:raise ValueError('Registros muito extensos.')
    for v in s['meta'].values():
        if not isinstance(v,str):raise ValueError('Campo inválido.')
    if not s['meta'].get('branch','').strip():raise ValueError('Informe filial e PDV.')
    for id,t in s['tasks'].items():
        if id not in IDS or not isinstance(t,dict):raise ValueError('Etapa inválida.')
        if any(not isinstance(v,str) for v in t.values()):raise ValueError('Campo de etapa inválido.')
        if t.get('status','Pendente') not in STATUSES:raise ValueError('Status inválido.')
        if t.get('duration') and (not t['duration'].isdigit() or not 0<int(t['duration'])<=10080):raise ValueError('Duração deve ser de 1 a 10080 minutos.')
        if t.get('status')=='Concluído' and not (t.get('owner','').strip() and t.get('evidence','').strip()):raise ValueError('Etapa concluída exige responsável e evidência.')
    done=lambda id:s['tasks'].get(id,{}).get('status')=='Concluído'
    pre=all(done(id) for id in ['orion1','orion2','orion3','linx1','linx2','linx3','linx4','linx5'])
    for k in ['linx','orion']:
        d=s['decisions'].get(k)
        if not isinstance(d,dict) or any(not isinstance(v,str) for v in d.values()) or d.get('value','Pendente') not in ['Pendente','GO','NO-GO']:raise ValueError('Decisão inválida.')
        if d.get('value')=='GO' and not (pre if k=='linx' else all(done(id) for id in IDS)):raise ValueError('GO sem os pré-requisitos concluídos.')
    # A decision can be drafted while the owner fills the remaining fields.
    d=s['decisions']['linx'];authorized=pre and d.get('value')=='GO' and all(d.get(k,'').strip() for k in ['owner','at','reason'])
    if s['tasks'].get('orion4',{}).get('status') in ['Em andamento','Concluído'] and not authorized:raise ValueError('Instalação exige GO da retirada registrado e completo.')
    if done('orion5') and not done('orion4') or done('orion6') and not done('orion5'):raise ValueError('Conclua a etapa anterior do Orion.')
    return s

@app.get('/api/cutovers')
def cutovers():
    with db() as c: rows=c.execute('SELECT id,title,version,updated_at,updated_by FROM ct_cutovers ORDER BY updated_at DESC').fetchall()
    return jsonify([dict(r) for r in rows])

@app.post('/api/cutovers')
def create_cutover():
    title=str((request.get_json() or {}).get('title','')).strip()[:160]
    if not title:return error('Informe filial / PDV.')
    id=secrets.token_hex(16);s={'meta':{'branch':title},'tasks':{},'decisions':{'linx':{},'orion':{}}}
    with db() as c:
        c.execute('INSERT INTO ct_cutovers VALUES (%s,%s,%s,1,%s,%s)',(id,title,json.dumps(s),now(),g.user['email']))
        audit(c,g.user['email'],'criação',id)
    return jsonify(id=id),201

@app.get('/api/cutovers/<id>')
def get_cutover(id):
    with db() as c: row=c.execute('SELECT * FROM ct_cutovers WHERE id=%s',(id,)).fetchone()
    if not row:return error('Cutover não encontrado.',404)
    return jsonify(id=id,state=json.loads(row['state']),version=row['version'],updated_at=row['updated_at'],updated_by=row['updated_by'])

@app.put('/api/cutovers/<id>')
def update_cutover(id):
    body=request.get_json() or {}
    try:s=valid_state(body.get('state'))
    except (ValueError,TypeError,AttributeError) as e:return error(str(e))
    if not isinstance(body.get('version'),int):return error('Versão inválida.')
    with db() as c:
        old=c.execute('SELECT state FROM ct_cutovers WHERE id=%s',(id,)).fetchone()
        if not old:return error('Cutover não encontrado.',404)
        changed=c.execute('UPDATE ct_cutovers SET state=%s,title=%s,version=version+1,updated_at=%s,updated_by=%s WHERE id=%s AND version=%s', (json.dumps(s,ensure_ascii=False),s['meta']['branch'][:160],now(),g.user['email'],id,body['version']))
        if changed.rowcount!=1:return error('Outra pessoa atualizou este cutover. Exporte sua cópia e recarregue antes de continuar.',409)
        previous=json.loads(old['state']);diff={k:{'antes':previous.get(k),'depois':s.get(k)} for k in ['meta','tasks','decisions'] if previous.get(k)!=s.get(k)}
        audit(c,g.user['email'],'atualização',id,diff)
    return jsonify(version=body['version']+1,updated_at=now(),updated_by=g.user['email'])

@app.get('/api/cutovers/<id>/audit')
def history(id):
    with db() as c:rows=c.execute('SELECT actor,action,created_at,detail FROM ct_audit WHERE cutover_id=%s ORDER BY created_at DESC LIMIT 200',(id,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/users',methods=['GET','POST'])
def users():
    if g.user['role']!='admin':return error('Acesso exclusivo do administrador.',403)
    if request.method=='GET':
        with db() as c:rows=c.execute('SELECT id,email,name,role,active,last_login FROM ct_users ORDER BY name').fetchall()
        return jsonify([dict(r) for r in rows])
    b=request.get_json() or {};email=str(b.get('email','')).strip().lower();pw=str(b.get('password',''));name=str(b.get('name','')).strip();role=b.get('role','operator')
    if '@' not in email or len(email)>254 or not name or len(name)>160 or len(pw)<12 or role not in ['admin','operator']:return error('Informe nome, e-mail, perfil e senha com pelo menos 12 caracteres.')
    with db() as c:
        result=c.execute('INSERT INTO ct_users (id,email,name,password,role) VALUES (%s,%s,%s,%s,%s) ON CONFLICT(email) DO NOTHING',(secrets.token_hex(16),email,name,generate_password_hash(pw),role))
        if result.rowcount!=1:return error('E-mail já cadastrado.',409)
        audit(c,g.user['email'],'criação de usuário',detail={'email':email,'role':role})
    return jsonify(ok=True),201

@app.put('/api/users/<id>/active')
def toggle_user(id):
    if g.user['role']!='admin':return error('Acesso exclusivo do administrador.',403)
    if id==g.user['id']:return error('Não é possível bloquear seu próprio usuário.')
    value=(request.get_json() or {}).get('active')
    if not isinstance(value,bool):return error('Valor inválido.')
    with db() as c:
        c.execute('UPDATE ct_users SET active=%s WHERE id=%s',(int(value),id))
        audit(c,g.user['email'],'alteração de acesso',detail={'id':id,'active':value})
    return jsonify(ok=True)

@app.post('/api/password')
def password():
    b=request.get_json() or {};pw=str(b.get('new',''))
    with db() as c:
        row=c.execute('SELECT password FROM ct_users WHERE id=%s',(g.user['id'],)).fetchone()
        if len(pw)<12 or not check_password_hash(row['password'],str(b.get('current',''))):return error('Confira a senha atual e use uma nova senha com pelo menos 12 caracteres.')
        c.execute('UPDATE ct_users SET password=%s WHERE id=%s',(generate_password_hash(pw),g.user['id']))
        audit(c,g.user['email'],'troca de senha')
    session.clear();return jsonify(ok=True)

@app.errorhandler(500)
def internal_error(e):return error('Erro interno. Tente novamente; se persistir, consulte os logs do serviço.',500)

if __name__=='__main__':
    init_db();app.run(host='127.0.0.1',port=5000)
