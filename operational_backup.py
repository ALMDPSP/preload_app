"""Administrator-only, signed operational backups with preview and atomic restore."""
import gzip,io,json,hmac,hashlib,time,secrets
from flask import request,g,session,jsonify,send_file
from release import APP_VERSION

TABLES=['ct_branches','ct_branch_pdv_plan','ct_cutovers','ct_cutover_branch','ct_cutover_reviews','ct_audit',
        'ct_rollout_organization','ct_rollout_inventory','ct_rollout_waves','ct_pdv_assignments',
        'ct_rollout_schedule','ct_rollout_issues','ct_rollout_goals','ct_rollout_snapshots']
MAX_BYTES=32*1024*1024
def encoded(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def digest(value):return hashlib.sha256(encoded(value)).hexdigest()
def columns(c,table):
    cursor=c.execute('SELECT * FROM '+table+' LIMIT 0')
    return [item.name if hasattr(item,'name') else item[0] for item in cursor.description]
def snapshot(c):
    layout={table:columns(c,table) for table in TABLES}
    estimated=0;total=0
    for table in TABLES:
        fields='+'.join('COALESCE(length(CAST('+name+' AS TEXT)),0)' for name in layout[table])
        size=c.execute('SELECT COUNT(*) AS n,COALESCE(SUM('+fields+'),0) AS chars FROM '+table).fetchone()
        total+=size['n'];estimated+=size['chars']*4+size['n']*256
        if total>200000 or estimated>MAX_BYTES:raise ValueError('O volume excede o limite seguro da aplicação. Utilize o backup e restauração nativos do PostgreSQL.')
    result={}
    for table in TABLES:
        rows=[dict(r) for r in c.execute('SELECT * FROM '+table).fetchall()]
        result[table]={'columns':layout[table],'rows':sorted(rows,key=lambda r:encoded(r))}
    return result
def current_fingerprint(c,tables=None):
    users=[dict(r) for r in c.execute('SELECT id,email,role,active FROM ct_users ORDER BY id').fetchall()]
    return digest({'tables':tables if tables is not None else snapshot(c),'users':users})
def sign(core,payload):return hmac.new(core['app'].secret_key.encode(),encoded(payload),hashlib.sha256).hexdigest()
def read_upload(core,c):
    file=request.files.get('file')
    if not file:raise ValueError('Selecione o backup operacional .json.gz.')
    compressed=file.read(10*1024*1024+1)
    if len(compressed)>10*1024*1024:raise ValueError('O arquivo ultrapassa 10 MB.')
    try:
        if compressed[:2]==b'\x1f\x8b':
            with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:raw=stream.read(MAX_BYTES+1)
        else:raw=compressed
        if len(raw)>MAX_BYTES:raise ValueError('O conteúdo descompactado ultrapassa 32 MB.')
        container=json.loads(raw)
        payload=container['payload'];signature=container['signature']
        if not isinstance(signature,str) or not hmac.compare_digest(signature,sign(core,payload)):raise ValueError('A assinatura não confere. Use um backup deste sistema com a mesma SECRET_KEY.')
        if payload.get('format')!='ALM_ROLLOUT_OPERATIONAL_1' or set(payload.get('tables',{}))!=set(TABLES):raise ValueError('Formato de backup incompatível.')
        total=0
        for table in TABLES:
            saved=payload['tables'][table];expected=columns(c,table)
            if not isinstance(saved,dict) or saved.get('columns')!=expected or not isinstance(saved.get('rows'),list):raise ValueError('Estrutura incompatível: '+table)
            total+=len(saved['rows'])
            if total>200000:raise ValueError('O backup ultrapassa 200 mil registros.')
            for row in saved['rows']:
                if not isinstance(row,dict) or set(row)!=set(expected) or any(type(v) not in [str,int,float,bool,type(None)] for v in row.values()):raise ValueError('Registro inválido em '+table)
        refs=payload.get('user_references')
        if not isinstance(refs,list) or any(not isinstance(u,dict) or set(u)!=set(['id','email']) for u in refs):raise ValueError('Referências de usuários inválidas.')
        users={r['email'].lower():dict(r) for r in c.execute('SELECT id,email,role,active FROM ct_users').fetchall()}
        mapping={u['id']:users.get(str(u['email']).lower()) for u in refs};unlinked=0
        for row in payload['tables']['ct_pdv_assignments']['rows']:
            for key in ['executor_id','validator_id']:
                before=row[key];user=mapping.get(before)
                roles=['admin','manager'] if key=='validator_id' else ['admin','manager','operator']
                after=user['id'] if user and user['active'] and user['role'] in roles else None
                unlinked+=int(bool(before) and not after);row[key]=after
        return payload,unlinked,hashlib.sha256(raw).hexdigest()
    except (KeyError,TypeError,json.JSONDecodeError,UnicodeDecodeError,OSError,EOFError,RecursionError) as exc:raise ValueError('Arquivo de backup inválido ou corrompido.') from exc

def register_backup(app,core):
    def admin_error():return core['error']('Somente Administrador gerencia backups e restaurações.',403)
    @app.get('/api/admin/operational-integrity')
    def integrity_check():
        if g.user['role']!='admin':return admin_error()
        from dashboard import pdv_number,dashboard_data
        from rollout_base import rollout_base_summary
        issues=[];g.operational_exclusive=True
        try:
            with core['db']() as c:
                counts={table:c.execute('SELECT COUNT(*) AS n FROM '+table).fetchone()['n'] for table in TABLES}
                invalid_plans=0
                for row in c.execute('SELECT pdvs FROM ct_branch_pdv_plan').fetchall():
                    try:
                        values=json.loads(row['pdvs'])
                        if not isinstance(values,list) or not 1<=len(values)<=50 or any(not pdv_number(n) for n in values) or len({pdv_number(n) for n in values})!=len(values):invalid_plans+=1
                    except (TypeError,ValueError):invalid_plans+=1
                invalid_states=0
                for row in c.execute('SELECT state FROM ct_cutovers').fetchall():
                    try:
                        value=json.loads(row['state'])
                        if not isinstance(value,dict) or not isinstance(value.get('meta',{}),dict) or not isinstance(value.get('tasks',{}),dict) or not isinstance(value.get('decisions',{}),dict) or any(not isinstance(v,dict) for v in value.get('tasks',{}).values()) or any(not isinstance(v,dict) for v in value.get('decisions',{}).values()):invalid_states+=1
                    except (TypeError,ValueError):invalid_states+=1
                unbound=c.execute('SELECT COUNT(*) AS n FROM ct_cutovers x LEFT JOIN ct_cutover_branch l ON l.cutover_id=x.id WHERE l.cutover_id IS NULL').fetchone()['n']
                if invalid_plans:issues.append({'level':'error','count':invalid_plans,'description':'Planos de PDV com estrutura ou numeração inválida.'})
                if invalid_states:issues.append({'level':'error','count':invalid_states,'description':'Checklists com estrutura de dados inválida.'})
                if unbound:issues.append({'level':'warning','count':unbound,'description':'Cutovers sem vínculo de filial.'})
                totals=None
                if not invalid_plans and not invalid_states:
                    g.atomic_db=c
                    try:
                        data=dashboard_data(core);base=rollout_base_summary(core,data)
                        totals={'stores':data['totals']['stores'],'planned':data['totals']['expected'],'deployed':base['pdvs_deployed'],'validated':data['totals']['ok'],'pending':base['pdvs_pending']}
                        if totals['deployed']<totals['validated'] or totals['deployed']+totals['pending']!=totals['planned']:issues.append({'level':'error','count':1,'description':'Os totais de implantação e validação não fecham.'})
                        if data['totals']['exceptions']:issues.append({'level':'warning','count':data['totals']['exceptions'],'description':'Registros fora da numeração prevista, excluídos dos indicadores.'})
                        if base['stores_missing_organization']:issues.append({'level':'warning','count':base['stores_missing_organization'],'description':'Filiais sem GR e/ou regional.'})
                    finally:g.pop('atomic_db',None)
        finally:g.pop('operational_exclusive',None)
        return jsonify(ok=not any(i['level']=='error' for i in issues),counts=counts,totals=totals,issues=issues,checked_at=core['now'](),
                       note='Conferência automática dos dados salvos. Confirme também uma amostra de filiais e PDVs com a equipe operacional.')

    @app.get('/api/admin/operational-backup')
    def export_backup():
        if g.user['role']!='admin':return admin_error()
        g.operational_exclusive=True
        try:
            with core['db']() as c:
                tables=snapshot(c)
                refs=[dict(r) for r in c.execute('SELECT id,email FROM ct_users').fetchall()]
                payload={'format':'ALM_ROLLOUT_OPERATIONAL_1','version':APP_VERSION,'created_at':core['now'](),'tables':tables,'user_references':refs}
                body=encoded({'payload':payload,'signature':sign(core,payload)})
                if len(body)>MAX_BYTES or sum(len(t['rows']) for t in tables.values())>200000:return core['error']('O volume excede o limite de restauração pela aplicação. Utilize o backup nativo do PostgreSQL.')
                core['audit'](c,g.user['email'],'exportação de backup operacional',detail={'tables':{k:len(v['rows']) for k,v in tables.items()}})
            data=gzip.compress(body)
        except ValueError as exc:return core['error'](str(exc))
        finally:g.pop('operational_exclusive',None)
        return send_file(io.BytesIO(data),mimetype='application/gzip',as_attachment=True,download_name='Backup_Operacional_Rollout_'+core['now']()[:10]+'.json.gz',max_age=0)

    @app.post('/api/admin/operational-restore/preview')
    def preview_restore():
        if g.user['role']!='admin':return admin_error()
        g.operational_exclusive=True
        try:
            with core['db']() as c:
                payload,unlinked,file_hash=read_upload(core,c)
                current=snapshot(c)
                counts={table:{'current':len(current[table]['rows']),'backup':len(payload['tables'][table]['rows'])} for table in TABLES}
                token=secrets.token_hex(24)
                session['restore_preview']={'token':token,'file_hash':file_hash,'current_hash':current_fingerprint(c,current),'expires':time.time()+600}
        except ValueError as exc:return core['error'](str(exc))
        finally:g.pop('operational_exclusive',None)
        return jsonify(token=token,counts=counts,created_at=payload['created_at'],unlinked_assignments=unlinked,
                       note='Substitui os dados operacionais. Contas, senhas, MFA e chaves permanecem. Atribuições sem usuário ativo compatível ficam sem responsável.')

    @app.post('/api/admin/operational-restore/apply')
    def apply_restore():
        if g.user['role']!='admin':return admin_error()
        preview=session.get('restore_preview',{})
        if request.form.get('confirmation')!='RESTAURAR' or not preview or not hmac.compare_digest(str(request.form.get('token','')),str(preview.get('token','!'))) or preview.get('expires',0)<time.time():return core['error']('Confira a prévia e digite RESTAURAR para confirmar.',409)
        g.operational_exclusive=True
        try:
            with core['db']() as c:
                payload,unlinked,file_hash=read_upload(core,c)
                if file_hash!=preview['file_hash'] or current_fingerprint(c)!=preview['current_hash']:raise ValueError('O arquivo ou os dados do sistema mudaram. Gere uma nova prévia antes de restaurar.')
                # Foreign-key order is fixed; any failure rolls the whole transaction back.
                c.execute('DELETE FROM ct_cutover_approval_cache')
                c.execute('DELETE FROM ct_branch_imports')
                for table in reversed(TABLES):c.execute('DELETE FROM '+table)
                for table in TABLES:
                    value=payload['tables'][table];names=value['columns']
                    sql='INSERT INTO '+table+' ('+','.join(names)+') VALUES ('+','.join(['%s']*len(names))+')'
                    if value['rows']:c.executemany(sql,[tuple(row[k] for k in names) for row in value['rows']])
                c.execute('UPDATE ct_rollout_clock SET revision=revision+1 WHERE id=1')
                core['audit'](c,g.user['email'],'restauração operacional',detail={'backup_at':payload['created_at'],'unlinked_assignments':unlinked})
        except ValueError as exc:return core['error'](str(exc),409)
        except Exception as exc:
            app.logger.warning('Operational restore rolled back: %s',type(exc).__name__)
            return core['error']('Não foi possível restaurar. A operação foi revertida integralmente. Confira as referências do arquivo e os logs.',409)
        finally:g.pop('operational_exclusive',None)
        session.pop('restore_preview',None)
        return jsonify(ok=True,note='Dados operacionais restaurados. Contas e acessos preservados.')
