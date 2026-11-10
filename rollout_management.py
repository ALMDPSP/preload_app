"""Atomic central saves, accountable PDVs, rollout waves and period comparisons."""
import csv,io,json,secrets
from collections import Counter
from datetime import date,timedelta,datetime
from zoneinfo import ZoneInfo
from flask import request,g,jsonify,Response
from dashboard import dashboard_data,pdv_number
from rollout_base import branch_base,rollout_base_summary
from operations import today,valid_date,planned_branch,operation_overview
from reports import summarize

WAVE_STATUSES=['Planejada','Em execução','Concluída','Cancelada']
SCHEMA=[
 'CREATE TABLE IF NOT EXISTS ct_rollout_waves (id TEXT PRIMARY KEY,name TEXT NOT NULL,start_date TEXT NOT NULL,due_date TEXT NOT NULL,status TEXT NOT NULL,delay_reason TEXT NOT NULL,notes TEXT NOT NULL,version INTEGER NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL)',
 'CREATE TABLE IF NOT EXISTS ct_pdv_assignments (branch_id TEXT NOT NULL REFERENCES ct_branches(id) ON DELETE CASCADE,pdv TEXT NOT NULL,executor_id TEXT REFERENCES ct_users(id) ON DELETE SET NULL,validator_id TEXT REFERENCES ct_users(id) ON DELETE SET NULL,wave_id TEXT REFERENCES ct_rollout_waves(id) ON DELETE SET NULL,planned_date TEXT NOT NULL DEFAULT \'\',version INTEGER NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL,PRIMARY KEY(branch_id,pdv))'
]
def migrate_management(c,postgres=False):
    for sql in SCHEMA:c.execute(sql)
    columns=[r['name'] for r in c.execute('PRAGMA table_info(ct_rollout_issues)').fetchall()] if not postgres else [r['column_name'] for r in c.execute("SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='ct_rollout_issues'").fetchall()]
    if 'impact' not in columns:c.execute("ALTER TABLE ct_rollout_issues ADD COLUMN impact TEXT NOT NULL DEFAULT ''")

def clean(body,key,maximum=160):
    value=body.get(key,'')
    if not isinstance(value,str) or len(value)>maximum:raise ValueError('Confira o campo '+key+'.')
    return value.strip()

def validator_guard(c,user,branch,pdv,previous,state):
    # Reopening tasks may invalidate approvals, but approval decisions remain accountable.
    changed=any(state.get('decisions',{}).get(k,{})!=previous.get('decisions',{}).get(k,{}) and state.get('decisions',{}).get(k,{}).get('value') in ['GO','NO-GO'] for k in ['linx','orion'])
    if not changed or user['role']=='admin':return None
    row=c.execute('SELECT validator_id FROM ct_pdv_assignments WHERE branch_id=%s AND pdv=%s',(branch,pdv_number(pdv))).fetchone()
    if row and row['validator_id'] and row['validator_id']!=user['id']:
        return 'O aceite deste PDV está atribuído a outro analista validador. Solicite a validação ou o ajuste da atribuição ao Administrador/Gestor.'
    return None

def assignment_write(core,c,branch,pdv,body):
    if g.user['role'] not in ['admin','manager']:raise PermissionError('Somente Administrador ou Gestor atribui responsáveis e ondas.')
    if not isinstance(body,dict) or type(body.get('version')) is not int or body['version']<0:raise ValueError('Atualize as atribuições antes de salvar.')
    planned_branch(c,branch,pdv)
    old=c.execute('SELECT * FROM ct_pdv_assignments WHERE branch_id=%s AND pdv=%s',(branch,pdv)).fetchone()
    if (old['version'] if old else 0)!=body['version']:raise Conflict('As atribuições mudaram. Recarregue o cadastro.')
    ids={}
    for key in ['executor_id','validator_id']:
        value=body.get(key) or None
        if value is not None and not isinstance(value,str):raise ValueError('Escolha um usuário cadastrado.')
        if value:
            user=c.execute('SELECT id,role,active FROM ct_users WHERE id=%s',(value,)).fetchone()
            roles=['admin','manager'] if key=='validator_id' else ['admin','manager','operator']
            if not user or not user['active'] or user['role'] not in roles:raise ValueError('Escolha responsáveis ativos e com perfil adequado.')
        ids[key]=value
    wave=body.get('wave_id') or None
    if wave:
        if not isinstance(wave,str):raise ValueError('Onda inválida.')
        row=c.execute('SELECT status FROM ct_rollout_waves WHERE id=%s',(wave,)).fetchone()
        if not row or row['status']=='Cancelada' and (not old or old['wave_id']!=wave):raise ValueError('Selecione uma onda disponível.')
    planned=valid_date(body.get('planned_date',''))
    values=(ids['executor_id'],ids['validator_id'],wave,planned,core['now'](),g.user['email'])
    if old:
        row=c.execute('UPDATE ct_pdv_assignments SET executor_id=%s,validator_id=%s,wave_id=%s,planned_date=%s,version=version+1,updated_at=%s,updated_by=%s WHERE branch_id=%s AND pdv=%s AND version=%s',(*values,branch,pdv,body['version']))
    else:
        row=c.execute('INSERT INTO ct_pdv_assignments (branch_id,pdv,executor_id,validator_id,wave_id,planned_date,version,updated_at,updated_by) VALUES (%s,%s,%s,%s,%s,%s,1,%s,%s) ON CONFLICT(branch_id,pdv) DO NOTHING',(branch,pdv,*values[:4],*values[4:]))
    if row.rowcount!=1:raise Conflict('As atribuições mudaram. Recarregue o cadastro.')
    core['audit'](c,g.user['email'],'atribuição do rollout',detail={'branch_id':branch,'pdv':pdv,'executor_id':ids['executor_id'],'validator_id':ids['validator_id'],'wave_id':wave,'planned_date':planned})

class Conflict(Exception):pass
class AtomicRejected(Exception):
    def __init__(self,response):self.response=response

def branch_context(core,id):
    base=branch_base(core,id)
    if not base:return None
    with core['db']() as c:
        base['assignments']=[dict(r) for r in c.execute('SELECT * FROM ct_pdv_assignments WHERE branch_id=%s',(id,)).fetchall()]
        base['people']=[dict(r) for r in c.execute('SELECT id,name,email,role,active FROM ct_users WHERE active=1 ORDER BY name,email').fetchall()]
        base['waves']=[dict(r) for r in c.execute("SELECT * FROM ct_rollout_waves ORDER BY due_date,name").fetchall()]
        base['issues']=[dict(r) for r in c.execute("SELECT * FROM ct_rollout_issues WHERE branch_id=%s AND status!='Resolvida' ORDER BY due_date,created_at",(id,)).fetchall()]
    return base

def model(core,data=None,operations=None):
    data=data if data is not None else dashboard_data(core)
    operations=operations if operations is not None else operation_overview(core,data)
    with core['db']() as c:
        assignments={(r['branch_id'],r['pdv']):dict(r) for r in c.execute('SELECT * FROM ct_pdv_assignments').fetchall()}
        waves={r['id']:dict(r) for r in c.execute('SELECT * FROM ct_rollout_waves ORDER BY due_date,name').fetchall()}
        users={r['id']:dict(r) for r in c.execute('SELECT id,name,email,role,active FROM ct_users').fetchall()}
        inventory={(r['branch_id'],r['pdv']):dict(r) for r in c.execute('SELECT branch_id,pdv,status,deployed_at FROM ct_rollout_inventory').fetchall()}
    schedules={(r['branch_id'],r['pdv']):r for r in operations['schedule']}
    issues={}
    for issue in operations['issues']:
        if issue['status']!='Resolvida':issues.setdefault((issue['branch_id'],issue['pdv']),[]).append(issue)
    rows=[];current=today(core).isoformat()
    for m in data['machines']:
        key=(m['branch_id'],m['pdv']);a=assignments.get(key,{});wave=waves.get(a.get('wave_id'),{});schedule=schedules.get(key,{})
        due=a.get('planned_date') or schedule.get('due_date') or wave.get('due_date','')
        start=schedule.get('start_date') or wave.get('start_date','')
        executor=users.get(a.get('executor_id'),{});validator=users.get(a.get('validator_id'),{});items=issues.get(key,[])
        row={**m,'executor_id':a.get('executor_id'),'executor':executor.get('name') or schedule.get('owner') or 'Não atribuído',
             'validator_id':a.get('validator_id'),'validator':validator.get('name') or 'Não atribuído',
             'wave_id':a.get('wave_id'),'wave':wave.get('name','Sem onda'),'wave_status':wave.get('status',''),
             'planned_date':due,'start_date':start,'overdue':bool(due and due<current and not m['ok'] and wave.get('status')!='Cancelada'),
             'scheduled':bool(a or schedule),'open_issues':len(items),'critical':sum(i['priority']=='Crítica' for i in items),
             'impact':'; '.join(dict.fromkeys(i.get('impact','') for i in items if i.get('impact'))),
             'delay_reason':wave.get('delay_reason') or schedule.get('notes') or '',
             'deployed':bool(m['ok'] or inventory.get(key,{}).get('status')=='Implantado'),
             'declared_date':inventory.get(key,{}).get('deployed_at','') if inventory.get(key,{}).get('status')=='Implantado' else ''}
        rows.append(row)
    return {'data':data,'operations':operations,'rows':rows,'waves':waves,'users':users}

def period_dates(core,args):
    end=valid_date(args.get('to',(today(core)+timedelta(days=6-today(core).weekday())).isoformat()),True)
    start=valid_date(args.get('from',(today(core)-timedelta(days=today(core).weekday())).isoformat()),True)
    if start>end or (date.fromisoformat(end)-date.fromisoformat(start)).days>365:raise ValueError('Escolha um período de até 366 dias, com início anterior ao fim.')
    span=(date.fromisoformat(end)-date.fromisoformat(start)).days+1
    previous_end=date.fromisoformat(start)-timedelta(days=1)
    return start,end,(previous_end-timedelta(days=span-1)).isoformat(),previous_end.isoformat()

def period_summary(core,args=None,loaded=None):
    start,end,prev_start,prev_end=period_dates(core,args or {})
    loaded=loaded or model(core)
    rows=loaded['rows']
    def counts(a,b):
        planned=[r for r in rows if a<=r['planned_date']<=b and r['wave_status']!='Cancelada']
        approved=[r for r in rows if r['ok'] and r['approved_at'] and not r['date_reference'] and a<=datetime.fromisoformat(r['approved_at']).astimezone(ZoneInfo('America/Sao_Paulo')).date().isoformat()<=b]
        deployed=sum(bool(r['deployed'] and r['declared_date'] and a<=r['declared_date']<=b) for r in rows)
        return {'planned':len(planned),'validated_planned':sum(r['ok'] for r in planned),'validated':len(approved),
                'declared_deployed':deployed,'deviation':sum(not r['ok'] for r in planned)}
    cur=counts(start,end);previous=counts(prev_start,prev_end)
    waves=[];by_wave={}
    for row in rows:by_wave.setdefault(row['wave_id'],[]).append(row)
    for wave in loaded['waves'].values():
        assigned=by_wave.get(wave['id'],[])
        count=len(assigned);ok=sum(r['ok'] for r in assigned)
        waves.append({**wave,'planned':count,'deployed':sum(r['deployed'] for r in assigned),'validated':ok,'pending':count-ok,
                      'overdue':sum(r['overdue'] for r in assigned),'percent':round(ok/count*100,1) if count else 0})
    return {'from_date':start,'to_date':end,'previous_from':prev_start,'previous_to':prev_end,'current':cur,'previous':previous,
            'validated_delta':cur['validated']-previous['validated'],'overdue':sum(r['overdue'] for r in rows),
            'awaiting_acceptance':sum(r['status']=='Aguardando aceite' for r in rows),'critical':sum(r['critical'] for r in rows),
            'unassigned':sum(not r['executor_id'] for r in rows if r['scheduled'] or r['cutover_id']),
            'without_validation_owner':sum(not r['validator_id'] for r in rows if r['cutover_id']),
            'declared_without_date':sum(r['deployed'] and not r['declared_date'] for r in rows),
            'waves':waves,'note':'Comparação por datas registradas dos PDVs que permanecem validados hoje; não é fotografia histórica. Implantação declarada usa a data preenchida na Base, sem estimar a data pela última edição.'}

def register_management(app,core):
    @app.get('/api/rollout/branches/<id>/context')
    def rollout_context(id):
        data=branch_context(core,id)
        return jsonify(data) if data else core['error']('Filial não encontrada.',404)

    @app.post('/api/rollout/branches/<id>/save-all')
    def save_all(id):
        body=request.get_json(silent=True)
        if not isinstance(body,dict) or not isinstance(body.get('base'),dict):return core['error']('Confira o cadastro antes de salvar.')
        pdv=pdv_number(body.get('pdv'));check=body.get('checklist');assignment=body.get('assignment')
        if not pdv:return core['error']('Selecione o PDV.')
        base=body['base'];machines=base.get('machines')
        if not isinstance(machines,list) or len(machines)!=1 or not isinstance(machines[0],dict) or pdv_number(machines[0].get('pdv'))!=pdv:return core['error']('O salvamento deve conter somente o PDV selecionado.')
        g.atomic_write=True
        try:
            with core['db']() as c:
                lock=' FOR UPDATE' if core['DATABASE'] else ''
                if not c.execute('SELECT id FROM ct_branches WHERE id=%s'+lock,(id,)).fetchone():return core['error']('Filial não encontrada.',404)
                g.atomic_db=c
                try:
                    if check is not None:
                        if not isinstance(check,dict) or not isinstance(check.get('id'),str):raise ValueError('Checklist inválido.')
                        row=c.execute('SELECT x.state,l.branch_id FROM ct_cutovers x JOIN ct_cutover_branch l ON l.cutover_id=x.id WHERE x.id=%s'+(' FOR UPDATE OF x' if core['DATABASE'] else ''),(check['id'],)).fetchone()
                        if not isinstance(check.get('state'),dict) or pdv_number(check['state'].get('meta',{}).get('pdv'))!=pdv:raise ValueError('A numeração do checklist não corresponde ao PDV selecionado.')
                        if not row or row['branch_id']!=id or pdv_number(json.loads(row['state']).get('meta',{}).get('pdv'))!=pdv:raise ValueError('O checklist não corresponde à filial e ao PDV selecionados.')
                    if assignment is not None:assignment_write(core,c,id,pdv,assignment)
                    response=app.make_response(app.view_functions['save_rollout_base'](id,body=base))
                    if response.status_code>=400:raise AtomicRejected(response)
                    saved=None
                    if check is not None:
                        response=app.make_response(core['update_cutover'](check['id'],body={'state':check.get('state'),'version':check.get('version')}))
                        if response.status_code>=400:raise AtomicRejected(response)
                        saved=response.get_json()
                    core['audit'](c,g.user['email'],'salvamento único da central',check['id'] if check else None,{'branch_id':id,'pdv':pdv})
                    result={'ok':True,'checklist':saved,'base':branch_context(core,id)}
                finally:g.pop('atomic_db',None)
        except AtomicRejected as exc:return exc.response
        except PermissionError as exc:return core['error'](str(exc),403)
        except Conflict as exc:return core['error'](str(exc),409)
        except (ValueError,TypeError,AttributeError) as exc:return core['error'](str(exc))
        finally:g.pop('atomic_write',None)
        return jsonify(result)

    @app.get('/api/rollout/summary')
    def rollout_summary():
        try:return jsonify(period_summary(core,request.args))
        except ValueError as exc:return core['error'](str(exc))

    @app.get('/api/rollout/queue')
    def rollout_queue():
        loaded=model(core);rows=loaded['rows'];mode=request.args.get('mode','today');owner=request.args.get('owner','');wave=request.args.get('wave','');query=request.args.get('q','').casefold().strip();current=today(core).isoformat()
        def eligible(r):
            if wave and r['wave_id']!=wave:return False
            if owner=='my' and g.user['id'] not in [r['executor_id'],r['validator_id']]:return False
            if owner not in ['','my'] and owner not in [r['executor_id'],r['validator_id']]:return False
            if query and query not in ' '.join(str(r.get(k,'')) for k in ['code','name','pdv','executor','validator','wave']).casefold():return False
            if mode=='today':return not r['ok'] and (r['overdue'] or r['critical'] or r['status'] in ['Em andamento','Aguardando aceite','Bloqueado','Rejeitado'] or r['planned_date'] and (r['start_date'] or r['planned_date'])<=current<=r['planned_date'])
            if mode=='overdue':return r['overdue']
            if mode=='approval':return r['status']=='Aguardando aceite'
            if mode=='done':return r['ok']
            return bool(r['scheduled'] or r['cutover_id'] or r['open_issues'])
        rows=[r for r in rows if eligible(r)]
        rows.sort(key=lambda r:(-r['critical'],-int(r['overdue']),r['planned_date'] or '9999',r['code'],int(r['pdv'])))
        try:page=max(1,int(request.args.get('page',1)))
        except ValueError:page=1
        pages=max(1,(len(rows)+39)//40);page=min(page,pages)
        return jsonify(rows=rows[(page-1)*40:page*40],page=page,pages=pages,total=len(rows),
                       metrics={'overdue':sum(r['overdue'] for r in rows),'approval':sum(r['status']=='Aguardando aceite' for r in rows),'critical':sum(r['critical'] for r in rows)},
                       people=[u for u in loaded['users'].values() if u['active']],waves=list(loaded['waves'].values()),today=current)

    @app.get('/api/rollout/waves')
    def rollout_waves():return jsonify(rows=period_summary(core)['waves'])

    @app.route('/api/rollout/waves',methods=['POST'])
    @app.route('/api/rollout/waves/<id>',methods=['PUT'])
    def save_wave(id=None):
        if g.user['role'] not in ['admin','manager']:return core['error']('Somente Administrador ou Gestor gerencia ondas.',403)
        body=request.get_json() or {}
        try:
            name=clean(body,'name',120);start=valid_date(body.get('start_date'),True);due=valid_date(body.get('due_date'),True);status=body.get('status','Planejada')
            reason=clean(body,'delay_reason',2000);notes=clean(body,'notes',2000)
            if not name or start>due or status not in WAVE_STATUSES:raise ValueError('Confira nome, período e situação da onda.')
            if id and type(body.get('version')) is not int:raise ValueError('Atualize a onda antes de salvar.')
            with core['db']() as c:
                if id:
                    row=c.execute('UPDATE ct_rollout_waves SET name=%s,start_date=%s,due_date=%s,status=%s,delay_reason=%s,notes=%s,version=version+1,updated_at=%s,updated_by=%s WHERE id=%s AND version=%s',(name,start,due,status,reason,notes,core['now'](),g.user['email'],id,body['version']))
                    if row.rowcount!=1:raise Conflict('A onda mudou. Recarregue antes de salvar.')
                else:
                    id=secrets.token_hex(16)
                    c.execute('INSERT INTO ct_rollout_waves VALUES (%s,%s,%s,%s,%s,%s,%s,1,%s,%s)',(id,name,start,due,status,reason,notes,core['now'](),g.user['email']))
                core['audit'](c,g.user['email'],'planejamento de onda',detail={'id':id,'name':name,'status':status})
        except ValueError as exc:return core['error'](str(exc))
        except Conflict as exc:return core['error'](str(exc),409)
        return jsonify(ok=True,id=id)

    @app.post('/api/rollout/waves/<id>/assign-branch')
    def assign_wave_branch(id):
        if g.user['role'] not in ['admin','manager']:return core['error']('Somente Administrador ou Gestor vincula filiais.',403)
        body=request.get_json() or {};branch=body.get('branch_id');expected=body.get('versions');plan_version=body.get('plan_version')
        if not isinstance(branch,str) or not isinstance(expected,dict) or type(plan_version) is not int:return core['error']('Selecione uma filial e atualize os PDVs.')
        g.atomic_write=True
        try:
            with core['db']() as c:
                lock=' FOR UPDATE' if core['DATABASE'] else ''
                if not c.execute('SELECT id FROM ct_branches WHERE id=%s'+lock,(branch,)).fetchone():raise ValueError('Filial não encontrada.')
                wave=c.execute('SELECT status FROM ct_rollout_waves WHERE id=%s',(id,)).fetchone()
                if not wave or wave['status']=='Cancelada':raise ValueError('Escolha uma onda disponível.')
                plan=c.execute('SELECT pdvs,version FROM ct_branch_pdv_plan WHERE branch_id=%s',(branch,)).fetchone()
                from dashboard import DEFAULT_PDVS
                numbers=json.loads(plan['pdvs']) if plan else DEFAULT_PDVS
                if (plan['version'] if plan else 0)!=plan_version:raise Conflict('O plano mudou. Confira a filial novamente.')
                old={r['pdv']:dict(r) for r in c.execute('SELECT * FROM ct_pdv_assignments WHERE branch_id=%s',(branch,)).fetchall()}
                if any(type(expected.get(n)) is not int or expected[n]!=(old[n]['version'] if n in old else 0) for n in numbers):raise Conflict('As atribuições mudaram. Confira a filial novamente.')
                stamp=core['now']();actor=g.user['email']
                values=[(branch,n,old.get(n,{}).get('executor_id'),old.get(n,{}).get('validator_id'),id,old.get(n,{}).get('planned_date',''),stamp,actor) for n in numbers]
                c.executemany('INSERT INTO ct_pdv_assignments (branch_id,pdv,executor_id,validator_id,wave_id,planned_date,version,updated_at,updated_by) VALUES (%s,%s,%s,%s,%s,%s,1,%s,%s) ON CONFLICT(branch_id,pdv) DO UPDATE SET wave_id=excluded.wave_id,version=ct_pdv_assignments.version+1,updated_at=excluded.updated_at,updated_by=excluded.updated_by',values)
                core['audit'](c,actor,'vínculo da filial à onda',detail={'branch_id':branch,'wave_id':id,'pdvs':numbers})
        except ValueError as exc:return core['error'](str(exc))
        except Conflict as exc:return core['error'](str(exc),409)
        finally:g.pop('atomic_write',None)
        return jsonify(ok=True,pdvs=len(numbers))

    @app.get('/api/rollout/operations.csv')
    def operational_csv():
        try:start,end,_,_=period_dates(core,request.args)
        except ValueError as exc:return core['error'](str(exc))
        rows=model(core)['rows'];wave=request.args.get('wave','')
        def update_day(r):
            if not r['updated_at']:return ''
            dt=datetime.fromisoformat(r['updated_at'])
            return (dt.astimezone(ZoneInfo('America/Sao_Paulo')) if dt.tzinfo else dt).date().isoformat()
        rows=[r for r in rows if (not wave or r['wave_id']==wave) and (start<=r['planned_date']<=end or start<=update_day(r)<=end)]
        out=io.StringIO();writer=csv.writer(out,delimiter=';')
        def cell(value):
            text=str('' if value is None else value)
            return "'"+text if text.lstrip().startswith(('=','+','-','@')) else text
        writer.writerow(['Filial','Loja','PDV','Situação','Executor','Validador','Onda','Planejado para','Atrasado','Ocorrências','Impacto','Justificativa'])
        for r in rows:writer.writerow([cell(v) for v in [r['code'],r['name'],r['pdv'],r['status'],r['executor'],r['validator'],r['wave'],r['planned_date'],'Sim' if r['overdue'] else 'Não',r['open_issues'],r['impact'],r['delay_reason']]])
        return Response('\ufeff'+out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=Rollout_Operacional_por_PDV.csv'})
