"""Rollout planning, accountable issues, weekly goals and daily consolidation."""
import json,secrets
from datetime import datetime,date,timedelta
from zoneinfo import ZoneInfo
from flask import request,g,jsonify
from dashboard import dashboard_data,pdv_number,DEFAULT_PDVS

SCHEMA=[
 'CREATE TABLE IF NOT EXISTS ct_rollout_schedule (branch_id TEXT NOT NULL REFERENCES ct_branches(id),pdv TEXT NOT NULL,owner TEXT NOT NULL,start_date TEXT NOT NULL,due_date TEXT NOT NULL,notes TEXT NOT NULL,version INTEGER NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL,PRIMARY KEY(branch_id,pdv))',
 'CREATE TABLE IF NOT EXISTS ct_rollout_issues (id TEXT PRIMARY KEY,branch_id TEXT NOT NULL REFERENCES ct_branches(id),pdv TEXT NOT NULL,title TEXT NOT NULL,description TEXT NOT NULL,owner TEXT NOT NULL,due_date TEXT NOT NULL,priority TEXT NOT NULL,status TEXT NOT NULL,resolution TEXT NOT NULL,version INTEGER NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL)',
 'CREATE TABLE IF NOT EXISTS ct_rollout_goals (week_start TEXT PRIMARY KEY,target INTEGER NOT NULL,version INTEGER NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL)',
 'CREATE TABLE IF NOT EXISTS ct_rollout_clock (id INTEGER PRIMARY KEY,revision BIGINT NOT NULL)',
 'CREATE TABLE IF NOT EXISTS ct_rollout_snapshots (day TEXT PRIMARY KEY,payload TEXT NOT NULL,captured_at TEXT NOT NULL,revision BIGINT NOT NULL)'
]
PRIORITIES=['Baixa','Normal','Alta','Crítica'];ISSUE_STATUSES=['Aberta','Em tratamento','Resolvida']

def migrate_operations(c):
    for sql in SCHEMA:c.execute(sql)
    c.execute('INSERT INTO ct_rollout_clock (id,revision) VALUES (1,0) ON CONFLICT(id) DO NOTHING')

def today(core):return datetime.fromisoformat(core['now']()).astimezone(ZoneInfo('America/Sao_Paulo')).date()

def text(body,key,maximum,required=False):
    value=body.get(key,'')
    if not isinstance(value,str):raise ValueError('Campo inválido: '+key)
    value=value.strip()
    if len(value)>maximum or required and not value:raise ValueError('Preencha '+key+' e respeite o limite de '+str(maximum)+' caracteres.')
    return value

def valid_date(value,required=False):
    if not value and not required:return ''
    if not isinstance(value,str) or len(value)!=10:raise ValueError('Informe uma data válida.')
    try:return date.fromisoformat(value).isoformat()
    except ValueError:raise ValueError('Informe uma data válida.')

def planned_branch(c,branch_id,pdv):
    branch=c.execute('SELECT id FROM ct_branches WHERE id=%s',(branch_id,)).fetchone()
    if not branch:raise ValueError('Selecione uma filial cadastrada.')
    plan=c.execute('SELECT pdvs FROM ct_branch_pdv_plan WHERE branch_id=%s',(branch_id,)).fetchone()
    if pdv not in (json.loads(plan['pdvs']) if plan else DEFAULT_PDVS):raise ValueError('Inclua o número nos PDVs previstos da filial antes de planejar ou registrar a pendência.')

def capture_snapshot(core,summary=None,advance=False):
    with core['db']() as c:
        if advance:revision=c.execute('UPDATE ct_rollout_clock SET revision=revision+1 WHERE id=1 RETURNING revision').fetchone()['revision']
        else:revision=c.execute('SELECT revision FROM ct_rollout_clock WHERE id=1').fetchone()['revision']
    # Read the revision before recomputing; a supplied older dashboard must not overwrite a newer save.
    data=summary if summary and summary.get('_revision')==revision and not any(summary.get('filters',{}).values()) else dashboard_data(core,summary_only=True,include_evolution=False)
    stamp=data['generated_at'];day=datetime.fromisoformat(stamp).astimezone(ZoneInfo('America/Sao_Paulo')).date().isoformat()
    if day!=today(core).isoformat():raise ValueError('Não é permitido gravar um consolidado retroativo.')
    # Only today's record can change. Earlier days are never recalculated or backfilled.
    with core['db']() as c:
        c.execute('INSERT INTO ct_rollout_snapshots (day,payload,captured_at,revision) VALUES (%s,%s,%s,%s) ON CONFLICT(day) DO UPDATE SET payload=excluded.payload,captured_at=excluded.captured_at,revision=excluded.revision WHERE ct_rollout_snapshots.revision<=excluded.revision AND ct_rollout_snapshots.captured_at<=excluded.captured_at',(day,json.dumps(data['totals']),stamp,revision))
    return day

def operation_overview(core,data=None):
    data=data if data is not None else dashboard_data(core,include_evolution=True);current=today(core);week=(current-timedelta(days=current.weekday())).isoformat()
    machines={(m['branch_id'],m['pdv']):m for m in data['machines']}
    with core['db']() as c:
        schedules=[dict(r) for r in c.execute('SELECT s.*,b.code,b.name,b.uf FROM ct_rollout_schedule s JOIN ct_branches b ON b.id=s.branch_id ORDER BY s.due_date,b.code,s.pdv').fetchall()]
        issues=[dict(r) for r in c.execute('SELECT i.*,b.code,b.name,b.uf FROM ct_rollout_issues i JOIN ct_branches b ON b.id=i.branch_id ORDER BY i.created_at DESC,i.id').fetchall()]
        goal=c.execute('SELECT * FROM ct_rollout_goals WHERE week_start=%s',(week,)).fetchone()
    for row in schedules:
        m=machines.get((row['branch_id'],row['pdv']));row['machine_status']=m['status'] if m else 'Fora do escopo';row['cutover_id']=m['cutover_id'] if m else None;row['completed_at']=m['approved_at'] if m and m['ok'] else None;row['completion_reference']=bool(m and m['date_reference'])
        if m is None:row['status']='Fora do escopo'
        elif m['ok']:row['status']='Concluído'
        elif row['due_date']<current.isoformat():row['status']='Atrasado'
        elif row['start_date'] and row['start_date']>current.isoformat():row['status']='Programado'
        else:row['status']='Em execução' if m['cutover_id'] else 'Não iniciado'
    for issue in issues:issue['overdue']=bool(issue['status']!='Resolvida' and issue['due_date']<current.isoformat())
    approved_week=0
    for m in data['machines']:
        if m['ok'] and m['approved_at'] and not m['date_reference']:
            day=datetime.fromisoformat(m['approved_at']).astimezone(ZoneInfo('America/Sao_Paulo')).date().isoformat()
            approved_week+=int(week<=day<=current.isoformat())
    target=goal['target'] if goal else 0
    return {'generated_at':core['now'](),'today':current.isoformat(),'schedule':schedules,'issues':issues,'goal':{'week_start':week,'target':target,'version':goal['version'] if goal else 0,'achieved':approved_week,'percent':round(approved_week/target*100,1) if target else None},'metrics':{'overdue_schedule':sum(r['status']=='Atrasado' for r in schedules),'scheduled':len(schedules),'open_issues':sum(r['status']!='Resolvida' for r in issues),'overdue_issues':sum(r['overdue'] for r in issues)},'_dashboard':data}

def history_comparisons(rows,current):
    week=current-timedelta(days=current.weekday());month=current.replace(day=1);previous_month=(month-timedelta(days=1)).replace(day=1)
    periods=[('Semana atual',week,current),('Semana anterior',week-timedelta(days=7),week-timedelta(days=1)),('Mês atual',month,current),('Mês anterior',previous_month,month-timedelta(days=1))]
    result=[]
    for label,start,end in periods:
        before=[r for r in rows if r['day']<start.isoformat()];inside=[r for r in rows if start.isoformat()<=r['day']<=end.isoformat()]
        baseline=before[-1] if before else None;last=inside[-1] if inside else None
        result.append({'label':label,'from_date':start.isoformat(),'to_date':end.isoformat(),'baseline_day':baseline['day'] if baseline else None,'last_day':last['day'] if last else None,'days_recorded':len(inside),'ok_delta':json.loads(last['payload'])['ok']-json.loads(baseline['payload'])['ok'] if last and baseline else None})
    return result

def register_operations(app,core):
    db,error,audit=(core[k] for k in ['db','error','audit'])
    def stamp():return core['now']()
    @app.get('/api/operations/overview')
    def ops_overview():
        result=operation_overview(core);data=result.pop('_dashboard')
        try:capture_snapshot(core,data)
        except Exception as exc:app.logger.warning('Daily consolidation unavailable: %s',type(exc).__name__)
        return jsonify(result)
    @app.get('/api/operations/history')
    def ops_history():
        current=today(core)
        try:
            start=valid_date(request.args.get('from',(current-timedelta(days=30)).isoformat()),True);end=valid_date(request.args.get('to',current.isoformat()),True)
            if start>end or (date.fromisoformat(end)-date.fromisoformat(start)).days>366:raise ValueError('Escolha um período de até 366 dias, com início anterior ao fim.')
        except ValueError as exc:return error(str(exc))
        with db() as c:
            rows=c.execute('SELECT * FROM ct_rollout_snapshots WHERE day>=%s AND day<=%s ORDER BY day',(start,end)).fetchall()
            comparisons=c.execute('SELECT day,payload FROM ct_rollout_snapshots WHERE day<=%s ORDER BY day',(current.isoformat(),)).fetchall()
        return jsonify(today=current.isoformat(),from_date=start,to_date=end,comparisons=history_comparisons(comparisons,current),rows=[{'day':r['day'],'captured_at':r['captured_at'],'provisional':r['day']==current.isoformat(),**json.loads(r['payload'])} for r in rows])
    @app.put('/api/operations/goals/<week>')
    def ops_goal(week):
        if g.user['role'] not in ['admin','manager']:return error('Somente Administrador ou Gestor define metas.',403)
        body=request.get_json() or {}
        try:
            valid_date(week,True)
            if date.fromisoformat(week).weekday()!=0:raise ValueError('A semana deve começar em uma segunda-feira.')
            if type(body.get('target')) is not int or not 0<=body['target']<=100000 or type(body.get('version')) is not int:raise ValueError('Informe a meta entre 0 e 100.000 e a versão atual.')
        except ValueError as exc:return error(str(exc))
        with db() as c:
            if body['version']==0:
                result=c.execute('INSERT INTO ct_rollout_goals (week_start,target,version,updated_at,updated_by) VALUES (%s,%s,1,%s,%s) ON CONFLICT(week_start) DO NOTHING',(week,body['target'],stamp(),g.user['email']))
            else:result=c.execute('UPDATE ct_rollout_goals SET target=%s,version=version+1,updated_at=%s,updated_by=%s WHERE week_start=%s AND version=%s',(body['target'],stamp(),g.user['email'],week,body['version']))
            if result.rowcount!=1:return error('A meta mudou. Atualize a página.',409)
            audit(c,g.user['email'],'meta semanal do rollout',detail={'week_start':week,'target':body['target']})
        return jsonify(ok=True)
    @app.put('/api/operations/schedule')
    def ops_save_schedule():
        if g.user['role'] not in ['admin','manager']:return error('Somente Administrador ou Gestor pode planejar o rollout.',403)
        body=request.get_json() or {}
        try:
            branch=text(body,'branch_id',80,True);pdv=pdv_number(body.get('pdv'));owner=text(body,'owner',120,True);start=valid_date(body.get('start_date',''));due=valid_date(body.get('due_date',''),True);notes=text(body,'notes',2000)
            if not pdv or type(body.get('version')) is not int:raise ValueError('Informe o PDV e a versão atual.')
            if start and start>due:raise ValueError('O início deve ser anterior ou igual ao prazo.')
            with db() as c:
                planned_branch(c,branch,pdv)
                params=(owner,start,due,notes,stamp(),g.user['email'])
                if body['version']==0:result=c.execute('INSERT INTO ct_rollout_schedule (branch_id,pdv,owner,start_date,due_date,notes,version,updated_at,updated_by) VALUES (%s,%s,%s,%s,%s,%s,1,%s,%s) ON CONFLICT(branch_id,pdv) DO NOTHING',(branch,pdv,*params[:4],*params[4:]))
                else:result=c.execute('UPDATE ct_rollout_schedule SET owner=%s,start_date=%s,due_date=%s,notes=%s,version=version+1,updated_at=%s,updated_by=%s WHERE branch_id=%s AND pdv=%s AND version=%s',(*params,branch,pdv,body['version']))
                if result.rowcount!=1:return error('O cronograma mudou. Atualize a página.',409)
                audit(c,g.user['email'],'planejamento de PDV',detail={'branch_id':branch,'pdv':pdv,'owner':owner,'due_date':due})
        except ValueError as exc:return error(str(exc))
        return jsonify(ok=True)
    @app.delete('/api/operations/schedule')
    def ops_remove_schedule():
        if g.user['role'] not in ['admin','manager']:return error('Somente Administrador ou Gestor pode remover um planejamento.',403)
        body=request.get_json() or {}
        if type(body.get('version')) is not int:return error('Versão inválida.')
        with db() as c:
            row=c.execute('DELETE FROM ct_rollout_schedule WHERE branch_id=%s AND pdv=%s AND version=%s',(body.get('branch_id'),pdv_number(body.get('pdv')),body['version']))
            if row.rowcount!=1:return error('O cronograma mudou. Atualize a página.',409)
            audit(c,g.user['email'],'remoção de planejamento',detail={'branch_id':body.get('branch_id'),'pdv':body.get('pdv')})
        return jsonify(ok=True)
    def issue_fields(body):
        branch=text(body,'branch_id',80,True);pdv=pdv_number(body.get('pdv'));title=text(body,'title',160,True);description=text(body,'description',2000);owner=text(body,'owner',120,True);due=valid_date(body.get('due_date'),True);priority=body.get('priority','Normal');status=body.get('status','Aberta');resolution=text(body,'resolution',2000)
        if not pdv or priority not in PRIORITIES or status not in ISSUE_STATUSES:raise ValueError('Confira o PDV, prioridade e situação.')
        if status=='Resolvida' and len(resolution)<3:raise ValueError('Descreva como a pendência foi resolvida.')
        return branch,pdv,title,description,owner,due,priority,status,resolution
    @app.post('/api/operations/issues')
    def ops_create_issue():
        if g.user['role']=='viewer':return error('Consulta permite somente leitura.',403)
        body=request.get_json() or {};id=secrets.token_hex(16)
        try:
            values=issue_fields(body)
            with db() as c:
                planned_branch(c,values[0],values[1])
                c.execute('INSERT INTO ct_rollout_issues (id,branch_id,pdv,title,description,owner,due_date,priority,status,resolution,version,created_at,updated_at,updated_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s,%s,%s)',(id,*values,stamp(),stamp(),g.user['email']))
                audit(c,g.user['email'],'abertura de pendência',detail={'id':id,'branch_id':values[0],'pdv':values[1],'title':values[2]})
        except ValueError as exc:return error(str(exc))
        return jsonify(id=id),201
    @app.put('/api/operations/issues/<id>')
    def ops_update_issue(id):
        if g.user['role']=='viewer':return error('Consulta permite somente leitura.',403)
        body=request.get_json() or {}
        if type(body.get('version')) is not int:return error('Versão inválida.')
        try:
            values=issue_fields(body)
            with db() as c:
                before=c.execute('SELECT * FROM ct_rollout_issues WHERE id=%s',(id,)).fetchone()
                if not before:return error('Pendência não encontrada.',404)
                if (values[0],values[1])!=(before['branch_id'],before['pdv']):return error('Não altere a filial/PDV de uma pendência existente.')
                result=c.execute('UPDATE ct_rollout_issues SET title=%s,description=%s,owner=%s,due_date=%s,priority=%s,status=%s,resolution=%s,version=version+1,updated_at=%s,updated_by=%s WHERE id=%s AND version=%s',(*values[2:],stamp(),g.user['email'],id,body['version']))
                if result.rowcount!=1:return error('A pendência mudou. Atualize a página.',409)
                audit(c,g.user['email'],'atualização de pendência',detail={'id':id,'before_status':before['status'],'status':values[7],'owner':values[4],'resolution':values[8]})
        except ValueError as exc:return error(str(exc))
        return jsonify(ok=True)
    @app.after_request
    def snapshot_saved_rollout(response):
        if 200<=response.status_code<300:
            path=request.path
            mutation=request.method in ['POST','PUT','DELETE'] and (path.startswith('/api/cutovers') or path.startswith('/api/branches') or path.startswith('/api/rollout-base/branches/') and path.endswith('/pdv-number')) and not path.endswith('/import/preview')
            dashboard=path=='/api/dashboard' and not request.args.get('q') and not request.args.get('uf')
            if mutation or dashboard:
                try:capture_snapshot(core,getattr(g,'dashboard_snapshot',None) if dashboard else None,advance=mutation)
                except Exception as exc:app.logger.warning('Daily consolidation pending: %s',type(exc).__name__)
        return response
