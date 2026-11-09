import os, json, secrets, sqlite3, time
from release import APP_VERSION
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from functools import wraps
from pathlib import Path
from flask import Flask, request, session, jsonify, render_template, redirect, g, has_request_context
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from branches import migrate_branches, branch_for, bound_meta, register_branches

ROOT = Path(__file__).parent
app = Flask(__name__)
DEV = os.getenv('APP_ENV') == 'development'
if not os.getenv('SECRET_KEY') and not DEV:
    raise RuntimeError('Configure SECRET_KEY antes de iniciar.')
app.secret_key = os.getenv('SECRET_KEY') or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_SECURE=not DEV, SESSION_COOKIE_HTTPONLY=True,
                  SESSION_COOKIE_SAMESITE='Lax', PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
                  MAX_CONTENT_LENGTH=10 * 1024 * 1024)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
DATABASE = os.getenv('DATABASE_URL', '')
if not DATABASE and not DEV:
    raise RuntimeError('Configure DATABASE_URL do Neon. Não há banco local em produção.')
SCHEMA = [
    'CREATE TABLE IF NOT EXISTS ct_users (id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1, last_login TEXT)',
    'CREATE TABLE IF NOT EXISTS ct_cutovers (id TEXT PRIMARY KEY, title TEXT NOT NULL, state TEXT NOT NULL, version INTEGER NOT NULL, updated_at TEXT NOT NULL, updated_by TEXT NOT NULL)',
    'CREATE TABLE IF NOT EXISTS ct_audit (id TEXT PRIMARY KEY, cutover_id TEXT, actor TEXT NOT NULL, action TEXT NOT NULL, created_at TEXT NOT NULL, detail TEXT NOT NULL)',
    'CREATE TABLE IF NOT EXISTS ct_attempts (key TEXT PRIMARY KEY, count INTEGER NOT NULL, window_start REAL NOT NULL)',
    'CREATE TABLE IF NOT EXISTS ct_cutover_reviews (cutover_id TEXT PRIMARY KEY REFERENCES ct_cutovers(id), reason TEXT NOT NULL, actor TEXT NOT NULL, created_at TEXT NOT NULL)',
    'CREATE TABLE IF NOT EXISTS ct_auth (user_id TEXT PRIMARY KEY, secret TEXT, temp_secret TEXT, last_step BIGINT NOT NULL DEFAULT -1, recovery TEXT NOT NULL DEFAULT \'[]\', must_change INTEGER NOT NULL DEFAULT 0, auth_version INTEGER NOT NULL DEFAULT 1)'
]
SOURCE = json.loads((ROOT / 'data.json').read_text())
IDS = [t['id'] for t in SOURCE['orion'] + SOURCE['linx']]
STATUSES = ['Pendente', 'Em andamento', 'Concluído', 'Bloqueado']

def now(): return datetime.now(timezone.utc).isoformat()

@contextmanager
def db(*, healthcheck=False):
    if DATABASE:
        import psycopg
        from psycopg.rows import dict_row
        conn = getattr(g,'postgres_connection',None) if has_request_context() else None
        if conn is None or conn.closed:
            conn = psycopg.connect(DATABASE, connect_timeout=2 if healthcheck else 15,row_factory=dict_row,
                                   keepalives=1,keepalives_idle=15,keepalives_interval=5,keepalives_count=3,tcp_user_timeout=20000)
            if has_request_context():g.postgres_connection=conn
    else:
        conn = sqlite3.connect(os.getenv('SQLITE_PATH', str(ROOT / 'dev.sqlite')), timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
    class Connection:
        def execute(self, sql, params=()):
            return conn.execute(sql if DATABASE else sql.replace('%s', '?'), params)
        def executemany(self, sql, params):
            cursor=conn.cursor()
            try:
                cursor.executemany(sql if DATABASE else sql.replace('%s','?'),params)
            finally:cursor.close()
    try:
        if DATABASE:
            # SET LOCAL is scoped to this transaction and compatible with pooled connections.
            conn.execute("SELECT set_config('statement_timeout',%s,true),set_config('lock_timeout',%s,true),set_config('idle_in_transaction_session_timeout','30000',true)",('1500ms' if healthcheck else '45000ms','1000ms' if healthcheck else '8000ms'))
        yield Connection()
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if not DATABASE or not has_request_context():conn.close()

@app.teardown_request
def close_request_database(exception=None):
    conn=g.pop('postgres_connection',None)
    if conn is not None:conn.close()

def init_db(log=None):
    report=log or (lambda message:None)
    started=time.monotonic()
    report('Conectando ao banco de dados...')
    with db() as c:
        report('Conexão estabelecida. Conferindo estrutura principal...')
        for sql in SCHEMA: c.execute(sql)
        report('Conferindo filiais e migrando vínculos anteriores...')
        migrated=migrate_branches(c,now,postgres=bool(DATABASE))
        from dashboard import PLAN_SCHEMA
        c.execute(PLAN_SCHEMA)
        from dashboard import PERFORMANCE_SCHEMA
        for sql in PERFORMANCE_SCHEMA:c.execute(sql)
        from operations import migrate_operations
        migrate_operations(c)
        from rollout_base import migrate_rollout_base
        migrate_rollout_base(c)
        report(f'Filiais conferidas. Vínculos migrados: {migrated}. Conferindo usuários...')
        email = os.getenv('ADMIN_EMAIL', '').strip().lower()
        password = os.getenv('ADMIN_PASSWORD', '')
        if not c.execute('SELECT id FROM ct_users LIMIT 1').fetchone():
            if not email or len(password) < 12:
                raise RuntimeError('Primeiro acesso: defina ADMIN_EMAIL e ADMIN_PASSWORD com pelo menos 12 caracteres.')
            uid=secrets.token_hex(16)
            c.execute('INSERT INTO ct_users (id,email,name,password,role) VALUES (%s,%s,%s,%s,%s)',
                      (uid, email, os.getenv('ADMIN_NAME','Administrador'), generate_password_hash(password), 'admin'))
            c.execute('INSERT INTO ct_auth (user_id,must_change) VALUES (%s,1)',(uid,))
        # Additive migration: existing users and cutovers remain intact.
        c.execute('INSERT INTO ct_auth (user_id) SELECT id FROM ct_users WHERE 1=1 ON CONFLICT(user_id) DO NOTHING')
    report(f'Banco pronto em {time.monotonic()-started:.2f}s.')

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
    # Public assets do not need to authenticate the session or open a Neon connection.
    if request.method in ('GET','HEAD') and (request.path=='/healthz' or request.path.startswith('/static/') or request.path in ('/manifest.webmanifest','/sw.js')):return
    if session.get('uid'):
        with db() as c: row = c.execute('SELECT u.id,u.email,u.name,u.role,u.active,u.last_login,a.auth_version,a.secret,a.must_change FROM ct_users u JOIN ct_auth a ON a.user_id=u.id WHERE u.id=%s', (session['uid'],)).fetchone()
        if row and row['active'] and row['secret'] and not row['must_change'] and session.get('mfa_verified') and session.get('auth_version')==row['auth_version']:
            g.user = {k:row[k] for k in ['id','email','name','role','active','last_login']}
        else: session.clear()
    if request.method in ('POST','PUT','DELETE','PATCH'):
        supplied = request.headers.get('X-CSRF-Token') or request.form.get('csrf','')
        if not secrets.compare_digest(str(session.get('csrf','!')), supplied):
            return error('Sessão expirada. Atualize a página e tente novamente.',403)
    if request.path.startswith('/api/') and not g.user: return error('Faça login novamente.',401)
    if request.path.startswith('/api/') and request.method in ('POST','PUT','PATCH','DELETE') and g.user and g.user['role']=='viewer' and request.path!='/api/password':
        return error('Perfil Consulta permite somente leitura.',403)

@app.after_request
def optimize_transfers(response):
    if request.path.startswith('/static/') and response.status_code in (200,304):
        response.headers['Cache-Control']='public, max-age=3600' if request.args.get('v') else 'public, max-age=300'
    if response.is_json and response.status_code==200 and not response.direct_passthrough:
        response.vary.add('Accept-Encoding')
        if request.accept_encodings['gzip']>0 and not response.headers.get('Content-Encoding'):
            import gzip
            raw=response.get_data()
            if len(raw)>1400:
                compressed=gzip.compress(raw,compresslevel=5,mtime=0)
                if len(compressed)<len(raw):response.set_data(compressed);response.headers['Content-Encoding']='gzip'
    return response

@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='same-origin'
    response.headers['Cache-Control']='no-store'
    response.headers['X-App-Version']=APP_VERSION
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    if not DEV: response.headers['Strict-Transport-Security']='max-age=31536000'
    return response

@app.get('/healthz')
def health():
    try:
        with db(healthcheck=True) as c: c.execute('SELECT 1').fetchone()
        return jsonify(status='ok',version=APP_VERSION)
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
                auth=c.execute('SELECT auth_version FROM ct_auth WHERE user_id=%s',(user['id'],)).fetchone()
                session.clear();session['pending_uid']=user['id'];session['pending_until']=time.time()+600;session['pending_version']=auth['auth_version'];token()
                c.execute('DELETE FROM ct_attempts WHERE key=%s',(key,))
                return redirect('/mfa')
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
    done=lambda id:s['tasks'].get(id,{}).get('status')=='Concluído'
    pre=all(done(id) for id in ['orion1','orion2','orion3','linx1','linx2','linx3','linx4','linx5'])
    for k in ['linx','orion']:
        d=s['decisions'].get(k)
        if not isinstance(d,dict) or any(not isinstance(v,str) for v in d.values()) or d.get('value','Pendente') not in ['Pendente','GO','NO-GO']:raise ValueError('Decisão inválida.')
        if d.get('value')=='GO' and not (pre if k=='linx' else all(done(id) for id in IDS)):raise ValueError('GO sem os pré-requisitos concluídos.')
    # A decision can be drafted while the owner fills the remaining fields.
    d=s['decisions']['linx'];authorized=pre and d.get('value')=='GO' and all(d.get(k,'').strip() for k in ['owner','at'])
    if s['tasks'].get('orion4',{}).get('status') in ['Em andamento','Concluído'] and not authorized:raise ValueError('Instalação exige GO da retirada registrado e completo.')
    if done('orion5') and not done('orion4') or done('orion6') and not done('orion5'):raise ValueError('Conclua a etapa anterior do Orion.')
    return s

@app.get('/api/cutovers')
def cutovers():
    branch_id=request.args.get('branch_id')
    with db() as c:
        sql='SELECT x.id,x.title,x.version,x.updated_at,x.updated_by,l.branch_id,b.code AS branch_code,b.name AS branch_name,b.needs_review,rv.reason AS rejection_reason FROM ct_cutovers x JOIN ct_cutover_branch l ON l.cutover_id=x.id JOIN ct_branches b ON b.id=l.branch_id LEFT JOIN ct_cutover_reviews rv ON rv.cutover_id=x.id'
        rows=c.execute(sql+(' WHERE l.branch_id=%s' if branch_id else '')+' ORDER BY x.updated_at DESC',(branch_id,) if branch_id else ()).fetchall()
    return jsonify([dict(r) for r in rows])

@app.post('/api/cutovers')
def create_cutover():
    if g.user['role'] not in ['admin','manager']:return error('Somente Administrador ou Gestor pode criar cutovers.',403)
    body=request.get_json() or {};branch_id=body.get('branch_id')
    if not isinstance(branch_id,str) or not branch_id:return error('Selecione uma filial cadastrada para iniciar o cutover.')
    pdv=body.get('pdv','')
    if not isinstance(pdv,str):return error('Informe o PDV desta execução.')
    pdv=pdv.strip()
    if not pdv or len(pdv)>40:return error('Informe o PDV desta execução (até 40 caracteres).')
    id=secrets.token_hex(16)
    with db() as c:
        branch=c.execute('SELECT * FROM ct_branches WHERE id=%s',(branch_id,)).fetchone()
        if not branch or not branch['active'] or branch['needs_review']:return error('Selecione uma filial ativa e com cadastro confirmado.')
        title=branch['code']+' / PDV '+pdv
        s=bound_meta({'meta':{'branch':title,'pdv':pdv},'tasks':{},'decisions':{'linx':{},'orion':{}}},branch)
        c.execute('INSERT INTO ct_cutovers VALUES (%s,%s,%s,1,%s,%s)',(id,title,json.dumps(s),now(),g.user['email']))
        c.execute('INSERT INTO ct_cutover_branch (cutover_id,branch_id) VALUES (%s,%s)',(id,branch_id))
        audit(c,g.user['email'],'criação',id)
    return jsonify(id=id),201

@app.get('/api/cutovers/<id>')
def get_cutover(id):
    with db() as c:
        row=c.execute('SELECT * FROM ct_cutovers WHERE id=%s',(id,)).fetchone()
        branch=branch_for(c,id) if row else None
        review=c.execute('SELECT reason,actor,created_at FROM ct_cutover_reviews WHERE cutover_id=%s',(id,)).fetchone() if row else None
    if not row:return error('Cutover não encontrado.',404)
    return jsonify(rejection=dict(review) if review else None,id=id,branch_id=branch['id'] if branch else None,state=bound_meta(json.loads(row['state']),branch) if branch else json.loads(row['state']),version=row['version'],updated_at=row['updated_at'],updated_by=row['updated_by'])

@app.put('/api/cutovers/<id>')
def update_cutover(id):
    body=request.get_json() or {}
    try:s=valid_state(body.get('state'))
    except (ValueError,TypeError,AttributeError) as e:return error(str(e))
    if not isinstance(body.get('version'),int):return error('Versão inválida.')
    with db() as c:
        old=c.execute('SELECT state FROM ct_cutovers WHERE id=%s',(id,)).fetchone()
        if not old:return error('Cutover não encontrado.',404)
        if c.execute('SELECT cutover_id FROM ct_cutover_reviews WHERE cutover_id=%s',(id,)).fetchone():return error('Cutover rejeitado. Consulte o motivo ou solicite ao Administrador a exclusão para refazer.',409)
        previous=json.loads(old['state'])
        branch=branch_for(c,id)
        if not branch:return error('Vincule esta execução a uma filial antes de salvar.')
        canonical=bound_meta(previous,branch)['meta']
        for key in ['branch_id','branch_code','branch_name','branch']:
            if key in s['meta'] and s['meta'][key]!=canonical[key]:return error('A filial deste cutover não pode ser alterada. Inicie outra execução para outra loja.')
            s['meta'][key]=canonical[key]
        for task_id, record in s['tasks'].items():
            prior=previous.get('tasks',{}).get(task_id,{})
            if record.get('status')=='Concluído' and prior.get('status')!='Concluído':
                record['owner']=record.get('owner','').strip() or g.user['name']
                record['checkedByEmail']=g.user['email']
                record['checkedAt']=now()
            else:
                for key in ['checkedByEmail','checkedAt']:
                    if key in prior:record[key]=prior[key]
                    else:record.pop(key,None)
        if g.user['role']=='operator':
            for k in ['linx','orion']:
                before=previous['decisions'].get(k,{})
                after=s['decisions'].get(k,{})
                # Operators can invalidate an approval by reopening a task, but cannot approve or edit a decision.
                invalidated=dict(before);invalidated['value']='Pendente'
                if after!=before and after!=invalidated:return error('Decisões GO / NO-GO são exclusivas de Administrador ou Gestor.',403)
        changed=c.execute('UPDATE ct_cutovers SET state=%s,title=%s,version=version+1,updated_at=%s,updated_by=%s WHERE id=%s AND version=%s', (json.dumps(s,ensure_ascii=False),s['meta']['branch'][:160],now(),g.user['email'],id,body['version']))
        if changed.rowcount!=1:return error('Outra pessoa atualizou este cutover. Exporte sua cópia e recarregue antes de continuar.',409)
        previous=json.loads(old['state']);diff={k:{'antes':previous.get(k),'depois':s.get(k)} for k in ['meta','tasks','decisions'] if previous.get(k)!=s.get(k)}
        audit(c,g.user['email'],'atualização',id,diff)
    return jsonify(version=body['version']+1,updated_at=now(),updated_by=g.user['email'])

@app.post('/api/cutovers/<id>/reject')
def reject_cutover(id):
    if g.user['role'] not in ['admin','manager']:return error('Somente Administrador ou Gestor pode rejeitar cutovers.',403)
    body=request.get_json() or {};reason=body.get('reason');expected=body.get('version')
    if not isinstance(reason,str) or not 3<=len(reason.strip())<=2000:return error('Informe o motivo da rejeição, de 3 a 2.000 caracteres.')
    if type(expected) is not int:return error('Versão inválida.')
    with db() as c:
        lock=' FOR UPDATE' if DATABASE else ''
        row=c.execute('SELECT * FROM ct_cutovers WHERE id=%s'+lock,(id,)).fetchone()
        if not row:return error('Cutover não encontrado.',404)
        if row['version']!=expected:return error('O cutover foi alterado. Atualize os dados antes de rejeitar.',409)
        if c.execute('SELECT cutover_id FROM ct_cutover_reviews WHERE cutover_id=%s',(id,)).fetchone():return error('Este cutover já está rejeitado.',409)
        stamp=now()
        changed=c.execute('UPDATE ct_cutovers SET version=version+1,updated_at=%s,updated_by=%s WHERE id=%s AND version=%s',(stamp,g.user['email'],id,expected))
        if changed.rowcount!=1:return error('O cutover foi alterado. Atualize os dados antes de rejeitar.',409)
        c.execute('INSERT INTO ct_cutover_reviews (cutover_id,reason,actor,created_at) VALUES (%s,%s,%s,%s)',(id,reason.strip(),g.user['email'],stamp))
        audit(c,g.user['email'],'rejeição do cutover',id,{'reason':reason.strip()})
    return jsonify(ok=True,version=expected+1)

@app.delete('/api/cutovers/<id>')
def delete_cutover(id):
    if g.user['role']!='admin':return error('Somente Administrador pode excluir cutovers.',403)
    body=request.get_json() or {};expected=body.get('version')
    if type(expected) is not int:return error('Versão inválida.')
    with db() as c:
        lock=' FOR UPDATE' if DATABASE else ''
        row=c.execute('SELECT * FROM ct_cutovers WHERE id=%s'+lock,(id,)).fetchone()
        if not row:return error('Cutover não encontrado.',404)
        if row['version']!=expected:return error('O cutover foi alterado. Atualize os dados antes de excluir.',409)
        branch=branch_for(c,id)
        audit(c,g.user['email'],'exclusão do cutover',id,{'title':row['title'],'branch_id':branch['id'] if branch else None,'version':expected})
        c.execute('DELETE FROM ct_cutover_reviews WHERE cutover_id=%s',(id,))
        c.execute('DELETE FROM ct_cutover_branch WHERE cutover_id=%s',(id,))
        c.execute('DELETE FROM ct_cutovers WHERE id=%s',(id,))
    return jsonify(ok=True,branch_id=branch['id'] if branch else None)

@app.get('/api/cutovers/<id>/audit')
def history(id):
    with db() as c:rows=c.execute('SELECT actor,action,created_at,detail FROM ct_audit WHERE cutover_id=%s ORDER BY created_at DESC LIMIT 200',(id,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.get('/api/cutovers/<id>/pdf')
def download_pdf(id):
    from flask import send_file
    from pdf_report import create_report, report_filename
    from dashboard import pdv_number
    with db() as c:
        row=c.execute('SELECT * FROM ct_cutovers WHERE id=%s',(id,)).fetchone()
        branch=branch_for(c,id) if row else None
        inventory=None
        if row and branch:
            number=pdv_number(json.loads(row['state']).get('meta',{}).get('pdv'))
            inventory=c.execute('SELECT status,installed_version,deployed_at,updated_at FROM ct_rollout_inventory WHERE branch_id=%s AND pdv=%s',(branch['id'],number)).fetchone()
        review=c.execute('SELECT reason,actor,created_at FROM ct_cutover_reviews WHERE cutover_id=%s',(id,)).fetchone() if row else None
    if not row:return error('Cutover não encontrado.',404)
    expected=request.args.get('version')
    if expected is not None and str(row['version'])!=expected:
        return error('O checklist foi atualizado por outra pessoa. Atualize os dados e gere o PDF novamente.',409)
    state=json.loads(row['state'])
    if branch:bound_meta(state,branch)
    report_saved={**dict(row),'rejection':dict(review) if review else None,'rollout_inventory':dict(inventory) if inventory else None}
    return send_file(create_report(SOURCE,state,report_saved),mimetype='application/pdf',as_attachment=True,download_name=report_filename(state,row['version']),max_age=0)

@app.route('/api/users',methods=['GET','POST'])
def users():
    if g.user['role']!='admin':return error('Acesso exclusivo do administrador.',403)
    if request.method=='GET':
        with db() as c:rows=c.execute('SELECT u.id,u.email,u.name,u.role,u.active,u.last_login,CASE WHEN a.secret IS NULL THEN 0 ELSE 1 END AS mfa_enabled,a.must_change FROM ct_users u JOIN ct_auth a ON a.user_id=u.id ORDER BY u.name').fetchall()
        return jsonify([dict(r) for r in rows])
    b=request.get_json() or {};email=str(b.get('email','')).strip().lower();pw=str(b.get('password',''));name=str(b.get('name','')).strip();role=b.get('role','operator')
    if '@' not in email or len(email)>254 or not name or len(name)>160 or len(pw)<12 or role not in ['admin','manager','operator','viewer']:return error('Informe nome, e-mail, perfil e senha com pelo menos 12 caracteres.')
    with db() as c:
        uid=secrets.token_hex(16)
        result=c.execute('INSERT INTO ct_users (id,email,name,password,role) VALUES (%s,%s,%s,%s,%s) ON CONFLICT(email) DO NOTHING',(uid,email,name,generate_password_hash(pw),role))
        if result.rowcount!=1:return error('E-mail já cadastrado.',409)
        c.execute('INSERT INTO ct_auth (user_id,must_change) VALUES (%s,1)',(uid,))
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
        c.execute('UPDATE ct_auth SET auth_version=auth_version+1 WHERE user_id=%s',(id,))
        audit(c,g.user['email'],'alteração de acesso',detail={'id':id,'active':value})
    return jsonify(ok=True)

@app.post('/api/password')
def password():
    b=request.get_json() or {};pw=str(b.get('new',''))
    with db() as c:
        row=c.execute('SELECT password FROM ct_users WHERE id=%s',(g.user['id'],)).fetchone()
        if len(pw)<12 or not check_password_hash(row['password'],str(b.get('current',''))):return error('Confira a senha atual e use uma nova senha com pelo menos 12 caracteres.')
        c.execute('UPDATE ct_users SET password=%s WHERE id=%s',(generate_password_hash(pw),g.user['id']))
        c.execute('UPDATE ct_auth SET auth_version=auth_version+1 WHERE user_id=%s',(g.user['id'],))
        audit(c,g.user['email'],'troca de senha')
    session.clear();return jsonify(ok=True)

@app.errorhandler(500)
def internal_error(e):return error('Erro interno. Tente novamente; se persistir, consulte os logs do serviço.',500)

@app.errorhandler(413)
def upload_too_large(e):return error('O arquivo ultrapassa o limite de 10 MB.',413)

from auth_mfa import register_auth
from branch_import import register_branch_import
register_auth(app, globals())
register_branches(app, globals())
register_branch_import(app, globals())
from reports import register_reports
from pwa import register_pwa
register_reports(app,globals())
register_pwa(app,ROOT)
from dashboard import register_dashboard
register_dashboard(app,globals())
from operations import register_operations
register_operations(app,globals())

from branch_progress import register_branch_progress
register_branch_progress(app,globals())

from rollout_base import register_rollout_base
register_rollout_base(app,globals())

from pdv_renumber import register_pdv_renumber
register_pdv_renumber(app,globals())

if __name__=='__main__':
    init_db();app.run(host='127.0.0.1',port=5000)
