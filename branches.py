"""Branch registration and permanent one-store linkage for each cutover."""
import json, re, secrets
from branch_values import normalize_uf, branch_status
from flask import g, request, jsonify

BRANCH_SCHEMA=[
 'CREATE TABLE IF NOT EXISTS ct_branches (id TEXT PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, city TEXT NOT NULL DEFAULT \'\', uf TEXT NOT NULL DEFAULT \'\', active INTEGER NOT NULL DEFAULT 1, needs_review INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL)',
 'CREATE TABLE IF NOT EXISTS ct_cutover_branch (cutover_id TEXT PRIMARY KEY REFERENCES ct_cutovers(id), branch_id TEXT NOT NULL REFERENCES ct_branches(id))',
 'CREATE INDEX IF NOT EXISTS ct_cutover_branch_store_idx ON ct_cutover_branch(branch_id)',
 'CREATE TABLE IF NOT EXISTS ct_branch_imports (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, payload TEXT NOT NULL, mode TEXT NOT NULL, expires_at DOUBLE PRECISION NOT NULL, created_at TEXT NOT NULL, applied_at TEXT, result TEXT)'
]

def migrate_branches(c,now,postgres=False):
    for sql in BRANCH_SCHEMA:c.execute(sql)
    columns=([r['column_name'] for r in c.execute("SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='ct_branches'").fetchall()] if postgres else [r['name'] for r in c.execute('PRAGMA table_info(ct_branches)').fetchall()])
    if 'opening_soon' not in columns:c.execute('ALTER TABLE ct_branches ADD COLUMN opening_soon INTEGER NOT NULL DEFAULT 0')
    rows=c.execute('SELECT x.id,x.title,x.state FROM ct_cutovers x LEFT JOIN ct_cutover_branch b ON b.cutover_id=x.id WHERE b.cutover_id IS NULL').fetchall()
    if not rows:return 0
    candidates={};links=[]
    for row in rows:
        state=json.loads(row['state']);label=state.get('meta',{}).get('branch') or row['title']
        match=re.match(r'^\s*((?:VD|L)?\d{2,8})(?=\s*[/\s-]|$)',label,re.IGNORECASE)
        code=match.group(1).upper() if match else 'LEGADO-'+row['id'][:16].upper()
        review=0 if match else 1
        name='Filial '+code+' (nome a completar)' if match else 'Execução anterior - confirmar filial'
        if code not in candidates:candidates[code]=(secrets.token_hex(16),code,name,review,now())
        links.append((row['id'],code))
    c.executemany('INSERT INTO ct_branches (id,code,name,needs_review,created_at) VALUES (%s,%s,%s,%s,%s) ON CONFLICT(code) DO NOTHING',list(candidates.values()))
    identities={r['code']:r['id'] for r in c.execute('SELECT id,code FROM ct_branches').fetchall()}
    c.executemany('INSERT INTO ct_cutover_branch (cutover_id,branch_id) VALUES (%s,%s) ON CONFLICT(cutover_id) DO NOTHING',[(id,identities[code]) for id,code in links])
    return len(links)

def branch_for(c,cutover_id):
    return c.execute('SELECT b.* FROM ct_branches b JOIN ct_cutover_branch l ON l.branch_id=b.id WHERE l.cutover_id=%s',(cutover_id,)).fetchone()

def bound_meta(state,branch):
    meta=state['meta']
    for key,value in [('branch_id',branch['id']),('branch_code',branch['code']),('branch_name',branch['name'])]:
        meta.setdefault(key,value)
    return state

def register_branches(app,core):
    db,error,audit,now=(core[k] for k in ['db','error','audit','now'])
    def valid_fields(body,update=False):
        name=str(body.get('name','')).strip();city=str(body.get('city','')).strip();uf=normalize_uf(body.get('uf',''))
        if not name or len(name)>160 or len(city)>100 or (uf and uf not in ['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']):raise ValueError('Informe o nome da filial e confira cidade e UF.')
        return name,city,uf

    @app.route('/api/branches',methods=['GET','POST'])
    def branches():
        if request.method=='GET':
            with db() as c:rows=c.execute('SELECT b.*,COUNT(l.cutover_id) AS cutover_count FROM ct_branches b LEFT JOIN ct_cutover_branch l ON l.branch_id=b.id WHERE b.needs_review=0 OR l.cutover_id IS NOT NULL GROUP BY b.id,b.code,b.name,b.city,b.uf,b.active,b.needs_review,b.created_at,b.opening_soon ORDER BY b.needs_review DESC,b.code').fetchall()
            return jsonify([dict(r) for r in rows])
        if g.user['role'] not in ['admin','manager']:return error('Somente Administrador ou Gestor pode cadastrar filiais.',403)
        body=request.get_json() or {};code=str(body.get('code','')).strip().upper()
        if not re.fullmatch(r'[A-Z0-9][A-Z0-9_-]{1,29}',code):return error('Informe um código de filial de 2 a 30 caracteres, como VD266 ou L2621.')
        try:
            name,city,uf=valid_fields(body)
            active,opening=branch_status(body)
        except ValueError as exc:return error(str(exc))
        with db() as c:
            uid=secrets.token_hex(16)
            row=c.execute('INSERT INTO ct_branches (id,code,name,city,uf,active,opening_soon,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(code) DO NOTHING',(uid,code,name,city,uf,active,opening,now()))
            if row.rowcount!=1:return error('Essa filial já está cadastrada. Selecione-a na lista.',409)
            audit(c,g.user['email'],'cadastro de filial',detail={'id':uid,'code':code,'name':name})
        return jsonify(id=uid,code=code),201

    @app.put('/api/branches/<id>')
    def edit_branch(id):
        if g.user['role'] not in ['admin','manager']:return error('Acesso exclusivo de Administrador ou Gestor.',403)
        body=request.get_json() or {}
        try:
            name,city,uf=valid_fields(body)
            active,opening=branch_status(body)
        except ValueError as exc:return error(str(exc))
        with db() as c:
            previous=c.execute('SELECT * FROM ct_branches WHERE id=%s',(id,)).fetchone()
            if not previous:return error('Filial não encontrada.',404)
            if body.get('code',previous['code'])!=previous['code']:return error('O código da filial não pode ser alterado após o cadastro.')
            c.execute('UPDATE ct_branches SET name=%s,city=%s,uf=%s,active=%s,opening_soon=%s WHERE id=%s',(name,city,uf,active,opening,id))
            audit(c,g.user['email'],'alteração de filial',detail={'id':id,'name':name,'active':bool(active),'opening_soon':bool(opening)})
        return jsonify(ok=True)

    @app.delete('/api/branches/<id>')
    def delete_branch(id):
        if g.user['role']!='admin':return error('Somente Administrador pode excluir filiais.',403)
        try:
            with db() as c:
                row=c.execute('SELECT * FROM ct_branches WHERE id=%s',(id,)).fetchone()
                if not row:return error('Filial não encontrada.',404)
                if c.execute('SELECT cutover_id FROM ct_cutover_branch WHERE branch_id=%s LIMIT 1',(id,)).fetchone():
                    return error('Esta filial possui cutovers vinculados. Inative o cadastro para preservar o histórico.',409)
                audit(c,g.user['email'],'exclusão de filial',detail={'id':id,'code':row['code'],'name':row['name']})
                c.execute('DELETE FROM ct_branches WHERE id=%s',(id,))
        except Exception as exc:
            if getattr(exc,'sqlstate',None)=='23503' or type(exc).__name__=='IntegrityError':
                return error('A filial possui vínculos. Atualize a página e inative o cadastro.',409)
            raise
        return jsonify(ok=True)

    @app.put('/api/cutovers/<id>/branch')
    def resolve_legacy_branch(id):
        if g.user['role'] not in ['admin','manager']:return error('Acesso exclusivo de Administrador ou Gestor.',403)
        body=request.get_json() or {}
        with db() as c:
            row=c.execute('SELECT * FROM ct_cutovers WHERE id=%s',(id,)).fetchone()
            if not row:return error('Cutover não encontrado.',404)
            previous=branch_for(c,id)
            if not previous or not previous['needs_review']:return error('Este cutover já está vinculado a uma filial. O vínculo não pode ser alterado.')
            target=c.execute('SELECT * FROM ct_branches WHERE id=%s',(body.get('branch_id',''),)).fetchone()
            if not target or not target['active'] or target['needs_review']:return error('Selecione uma filial cadastrada e ativa.')
            if body.get('version')!=row['version']:return error('O registro foi alterado. Atualize antes de vincular a filial.',409)
            state=json.loads(row['state']);state['meta'].update(branch_id=target['id'],branch_code=target['code'],branch_name=target['name'])
            pdv=str(body.get('pdv','')).strip()[:40]
            state['meta']['pdv']=pdv;state['meta']['branch']=target['code']+(' / PDV '+pdv if pdv else ' / execução anterior')
            changed=c.execute('UPDATE ct_cutovers SET state=%s,title=%s,version=version+1,updated_by=%s,updated_at=%s WHERE id=%s AND version=%s',(json.dumps(state,ensure_ascii=False),state['meta']['branch'],g.user['email'],now(),id,row['version']))
            if changed.rowcount!=1:return error('O registro foi alterado. Atualize antes de vincular a filial.',409)
            c.execute('UPDATE ct_cutover_branch SET branch_id=%s WHERE cutover_id=%s',(target['id'],id))
            audit(c,g.user['email'],'vínculo de execução anterior à filial',id,{'from':previous['id'],'to':target['id']})
        return jsonify(ok=True,branch_id=target['id'])
