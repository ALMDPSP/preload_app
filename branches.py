"""Branch registration and permanent one-store linkage for each cutover."""
import json, re, secrets
from flask import g, request, jsonify

BRANCH_SCHEMA=[
 'CREATE TABLE IF NOT EXISTS ct_branches (id TEXT PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, city TEXT NOT NULL DEFAULT \'\', uf TEXT NOT NULL DEFAULT \'\', active INTEGER NOT NULL DEFAULT 1, needs_review INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL)',
 'CREATE TABLE IF NOT EXISTS ct_cutover_branch (cutover_id TEXT PRIMARY KEY REFERENCES ct_cutovers(id), branch_id TEXT NOT NULL REFERENCES ct_branches(id))',
 'CREATE INDEX IF NOT EXISTS ct_cutover_branch_store_idx ON ct_cutover_branch(branch_id)'
]

def migrate_branches(c,now):
    for sql in BRANCH_SCHEMA:c.execute(sql)
    rows=c.execute('SELECT x.id,x.title,x.state FROM ct_cutovers x LEFT JOIN ct_cutover_branch b ON b.cutover_id=x.id WHERE b.cutover_id IS NULL').fetchall()
    for row in rows:
        state=json.loads(row['state']);label=state.get('meta',{}).get('branch') or row['title']
        match=re.match(r'^\s*((?:VD|L)?\d{2,8})(?=\s*[/\s-]|$)',label,re.IGNORECASE)
        code=match.group(1).upper() if match else 'LEGADO-'+row['id'][:16].upper()
        review=0 if match else 1
        name='Filial '+code+' (nome a completar)' if match else 'Execução anterior - confirmar filial'
        c.execute('INSERT INTO ct_branches (id,code,name,needs_review,created_at) VALUES (%s,%s,%s,%s,%s) ON CONFLICT(code) DO NOTHING',(secrets.token_hex(16),code,name,review,now()))
        branch=c.execute('SELECT id FROM ct_branches WHERE code=%s',(code,)).fetchone()
        c.execute('INSERT INTO ct_cutover_branch (cutover_id,branch_id) VALUES (%s,%s) ON CONFLICT(cutover_id) DO NOTHING',(row['id'],branch['id']))

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
        name=str(body.get('name','')).strip();city=str(body.get('city','')).strip();uf=str(body.get('uf','')).strip().upper()
        if not name or len(name)>160 or len(city)>100 or (uf and uf not in ['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']):raise ValueError('Informe o nome da filial e confira cidade e UF.')
        return name,city,uf

    @app.route('/api/branches',methods=['GET','POST'])
    def branches():
        if request.method=='GET':
            with db() as c:rows=c.execute('SELECT b.*,COUNT(l.cutover_id) AS cutover_count FROM ct_branches b LEFT JOIN ct_cutover_branch l ON l.branch_id=b.id WHERE b.needs_review=0 OR l.cutover_id IS NOT NULL GROUP BY b.id,b.code,b.name,b.city,b.uf,b.active,b.needs_review,b.created_at ORDER BY b.needs_review DESC,b.code').fetchall()
            return jsonify([dict(r) for r in rows])
        if g.user['role'] not in ['admin','manager']:return error('Somente Administrador ou Gestor pode cadastrar filiais.',403)
        body=request.get_json() or {};code=str(body.get('code','')).strip().upper()
        if not re.fullmatch(r'[A-Z0-9][A-Z0-9_-]{1,29}',code):return error('Informe um código de filial de 2 a 30 caracteres, como VD266 ou L2621.')
        try:name,city,uf=valid_fields(body)
        except ValueError as exc:return error(str(exc))
        with db() as c:
            uid=secrets.token_hex(16)
            row=c.execute('INSERT INTO ct_branches (id,code,name,city,uf,created_at) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(code) DO NOTHING',(uid,code,name,city,uf,now()))
            if row.rowcount!=1:return error('Essa filial já está cadastrada. Selecione-a na lista.',409)
            audit(c,g.user['email'],'cadastro de filial',detail={'id':uid,'code':code,'name':name})
        return jsonify(id=uid,code=code),201

    @app.put('/api/branches/<id>')
    def edit_branch(id):
        if g.user['role'] not in ['admin','manager']:return error('Acesso exclusivo de Administrador ou Gestor.',403)
        body=request.get_json() or {}
        try:name,city,uf=valid_fields(body)
        except ValueError as exc:return error(str(exc))
        if not isinstance(body.get('active',True),bool):return error('Situação da filial inválida.')
        with db() as c:
            previous=c.execute('SELECT * FROM ct_branches WHERE id=%s',(id,)).fetchone()
            if not previous:return error('Filial não encontrada.',404)
            if body.get('code',previous['code'])!=previous['code']:return error('O código da filial não pode ser alterado após o cadastro.')
            c.execute('UPDATE ct_branches SET name=%s,city=%s,uf=%s,active=%s WHERE id=%s',(name,city,uf,int(body.get('active',True)),id))
            audit(c,g.user['email'],'alteração de filial',detail={'id':id,'name':name,'active':body.get('active',True)})
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
