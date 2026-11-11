"""Unique-PDV rollout dashboard and configurable branch plans."""
import copy,json,re,unicodedata
from collections import Counter,defaultdict
from itertools import groupby
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import request,g,jsonify,send_file,has_request_context
from reports import summarize

DEFAULT_PDVS=['01','02','03','04','05']
PLAN_SCHEMA='CREATE TABLE IF NOT EXISTS ct_branch_pdv_plan (branch_id TEXT PRIMARY KEY REFERENCES ct_branches(id), pdvs TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1)'

PERFORMANCE_SCHEMA=[
 'CREATE INDEX IF NOT EXISTS ct_audit_dashboard_idx ON ct_audit(action,cutover_id,created_at DESC,id DESC)',
 'CREATE TABLE IF NOT EXISTS ct_cutover_approval_cache (cutover_id TEXT PRIMARY KEY REFERENCES ct_cutovers(id) ON DELETE CASCADE,version INTEGER NOT NULL,approved_at TEXT NOT NULL,estimated INTEGER NOT NULL)'
]

def pdv_number(value):
    match=re.fullmatch(r'(?:PDV[\s_-]*)?0*([1-9][0-9]{0,3})',str(value or '').strip(),re.I)
    return str(int(match.group(1))).zfill(2) if match else None

def normalize(value):
    return unicodedata.normalize('NFKD',str(value or '')).encode('ascii','ignore').decode().lower()

def approval_time(state,events,fallback,ids):
    # Replay backwards to find the transition to the current completed state.
    current=copy.deepcopy(state)
    for event in events:
        try:diff=json.loads(event['detail'])
        except (ValueError,TypeError):continue
        before=copy.deepcopy(current)
        for key in ['meta','tasks','decisions']:
            if key in diff and isinstance(diff[key],dict) and 'antes' in diff[key]:before[key]=diff[key]['antes'] or {}
        if summarize(current,False,ids)[0]=='Concluído' and summarize(before,False,ids)[0]!='Concluído':return event['created_at'],False
        current=before
    return fallback,True

def dashboard_data(core,q='',uf='',summary_only=False,include_evolution=True):
    key=(q,uf,summary_only,include_evolution)
    memo=getattr(g,'rollout_calculations',None) if has_request_context() else None
    if memo is not None and key in memo:return memo[key]
    db,ids=core['db'],core['IDS']
    with db() as c:
        revision=c.execute('SELECT revision FROM ct_rollout_clock WHERE id=1').fetchone()['revision']
        branches=[dict(r) for r in c.execute('SELECT * FROM ct_branches ORDER BY code').fetchall()]
        plans={r['branch_id']:dict(r) for r in c.execute('SELECT * FROM ct_branch_pdv_plan').fetchall()}
        runs=c.execute('SELECT x.*,l.branch_id,r.reason AS rejection_reason FROM ct_cutovers x JOIN ct_cutover_branch l ON l.cutover_id=x.id LEFT JOIN ct_cutover_reviews r ON r.cutover_id=x.id ORDER BY x.updated_at DESC,x.id DESC').fetchall()
        eligible=[b for b in branches if b['active'] and not b['opening_soon'] and not b['needs_review']]
        ufs=sorted({b['uf'] for b in eligible if b['uf']})
        selected=[b for b in eligible if (not uf or b['uf']==uf) and normalize(q.strip()) in normalize(' '.join(str(b[k]) for k in ['code','name','city','uf']))]
        selected_ids={b['id'] for b in selected}
        latest={};exceptions=[]
        for raw in runs:
            run=dict(raw)
            if run['branch_id'] not in selected_ids:continue
            state=json.loads(run['state']);pdv=pdv_number(state.get('meta',{}).get('pdv'))
            if not pdv:
                exceptions.append({'branch_id':run['branch_id'],'cutover_id':run['id'],'pdv':state.get('meta',{}).get('pdv',''),'reason':'Numeração não identificada. Revise o cadastro do cutover.'});continue
            key=(run['branch_id'],pdv)
            if key not in latest:latest[key]=(run,state)
        approved_ids=[];approved_states={}
        for b in selected:
            plan=json.loads(plans[b['id']]['pdvs']) if b['id'] in plans else list(DEFAULT_PDVS)
            for pdv in plan:
                entry=latest.get((b['id'],pdv))
                if include_evolution and entry and summarize(entry[1],bool(entry[0]['rejection_reason']),ids)[0]=='Concluído':
                    approved_ids.append(entry[0]['id']);approved_states[entry[0]['id']]=entry
        approved_dates={}
        cache={r['cutover_id']:r for r in c.execute('SELECT * FROM ct_cutover_approval_cache').fetchall()} if approved_ids else {}
        missing=[]
        for id in approved_ids:
            saved=cache.get(id);run,state=approved_states[id]
            if saved and saved['version']==run['version']:approved_dates[id]=(saved['approved_at'],bool(saved['estimated']))
            else:missing.append(id)
        # Batches stay below SQLite's conservative parameter limit and avoid loading unrelated history.
        for start in range(0,len(missing),400):
            batch=missing[start:start+400]
            sql='SELECT cutover_id,created_at,detail FROM ct_audit WHERE action=%s AND cutover_id IN ('+','.join(['%s']*len(batch))+') ORDER BY cutover_id,created_at DESC,id DESC'
            cursor=c.execute(sql,('atualização',*batch))
            for cutover_id,events in groupby(cursor,lambda e:e['cutover_id']):
                run,state=approved_states[cutover_id]
                approved_dates[cutover_id]=approval_time(state,events,run['updated_at'],ids)
        for id in missing:
            run,state=approved_states[id];stamp,estimated=approved_dates.setdefault(id,(run['updated_at'],True))
            c.execute('INSERT INTO ct_cutover_approval_cache (cutover_id,version,approved_at,estimated) VALUES (%s,%s,%s,%s) ON CONFLICT(cutover_id) DO UPDATE SET version=excluded.version,approved_at=excluded.approved_at,estimated=excluded.estimated WHERE ct_cutover_approval_cache.version<=excluded.version',(id,run['version'],stamp,int(estimated)))
    stores=[];all_machines=[];days=Counter();baseline=0
    by_branch=defaultdict(list)
    for (branch_id,pdv),(run,state) in latest.items():by_branch[branch_id].append((pdv,run))
    branch_index={b['id']:b for b in selected}
    for b in selected:
        plan=json.loads(plans[b['id']]['pdvs']) if b['id'] in plans else list(DEFAULT_PDVS)
        machines=[]
        for pdv in plan:
            entry=latest.get((b['id'],pdv));run,state=entry if entry else ({},{})
            status,complete,blocked=summarize(state,bool(run.get('rejection_reason')),ids) if entry else ('Sem cutover',0,0)
            ok=status=='Concluído';approved_at=None;estimated=False
            if ok and include_evolution:
                approved_at,estimated=approved_dates.get(run['id'],(run['updated_at'],True))
                baseline+=int(estimated)
                try:day=datetime.fromisoformat(approved_at).astimezone(ZoneInfo('America/Sao_Paulo')).date().isoformat()
                except (TypeError,ValueError):day=core['now']()[:10]
                days[day]+=1
            machine={'branch_id':b['id'],'code':b['code'],'name':b['name'],'pdv':pdv,'status':'Orion OK' if ok else status,'ok':ok,'completed':complete,'cutover_id':run.get('id'),'updated_at':run.get('updated_at'),'approved_at':approved_at,'date_reference':estimated,'rejection_reason':run.get('rejection_reason')}
            machines.append(machine);all_machines.append(machine)
        for pdv,run in by_branch[b['id']]:
            if pdv not in plan:exceptions.append({'branch_id':b['id'],'cutover_id':run['id'],'pdv':pdv,'reason':'PDV fora da lista prevista desta filial. Ajuste a numeração para incluí-lo na meta.'})
        ok=sum(m['ok'] for m in machines)
        stores.append({**{k:b[k] for k in ['id','code','name','city','uf']},'pdvs':plan,'plan_version':plans[b['id']]['version'] if b['id'] in plans else 0,'expected':len(plan),'ok':ok,'pending':len(plan)-ok,'percent':round(ok/len(plan)*100,1),'machines':machines})
    cumulative=0;series=[]
    for day,count in sorted(days.items()):cumulative+=count;series.append({'day':day,'daily_ok':count,'cumulative_ok':cumulative})
    total=len(all_machines);ok=sum(m['ok'] for m in all_machines)
    for e in exceptions:
        b=branch_index[e['branch_id']];e.update(code=b['code'],name=b['name'])
    result={'_revision':revision,'generated_at':core['now'](),'filters':{'q':q,'uf':uf},'ufs':ufs,'active_branches_total':len(eligible),'stores':stores,'machines':all_machines,'exceptions':exceptions,'evolution':series,'date_references':baseline,'totals':{'stores':len(stores),'expected':total,'ok':ok,'pending':total-ok,'percent':round(ok/total*100,1) if total else 0,'stores_ok':sum(s['pending']==0 for s in stores),'stores_pending':sum(s['pending']>0 for s in stores),'exceptions':len(exceptions)},'excluded':{'inactive':sum(not b['active'] for b in branches),'opening_soon':sum(bool(b['active'] and b['opening_soon']) for b in branches),'needs_review':sum(bool(b['active'] and not b['opening_soon'] and b['needs_review']) for b in branches)}}

    if summary_only:
        for key in ['stores','machines','exceptions']:result.pop(key,None)
    if has_request_context():
        if memo is None:g.rollout_calculations={}
        g.rollout_calculations[key]=result
    return result

def register_dashboard(app,core):
    db,error,audit,now=(core[k] for k in ['db','error','audit','now'])
    def read_data():return dashboard_data(core,request.args.get('q','')[:200],request.args.get('uf','').upper()[:2])
    @app.get('/api/dashboard')
    def dashboard():
        if request.args.get('compact')=='1':
            from executive_dashboard import dashboard_bundle
            try:result=dashboard_bundle(core,request.args)
            except ValueError as exc:return error(str(exc))
            g.dashboard_snapshot=result.pop('_snapshot',None)
            return jsonify(result)
        data=read_data();g.dashboard_snapshot=data
        return jsonify(data)
    @app.get('/api/dashboard/machines')
    def dashboard_machine_page():
        from executive_dashboard import machine_page
        return jsonify(machine_page(core,request.args))
    @app.get('/api/dashboard/store/<id>')
    def dashboard_store_detail(id):
        data=dashboard_data(core)
        store=next((s for s in data['stores'] if s['id']==id),None)
        return jsonify(store) if store else error('Filial fora do escopo ativo.',404)
    @app.get('/api/dashboard/executive.pdf')
    def executive():
        from executive_report import create_executive_pdf
        return send_file(create_executive_pdf(dashboard_data(core,request.args.get('q','')[:200],request.args.get('uf','').upper()[:2],summary_only=True)),mimetype='application/pdf',as_attachment=True,download_name='Relatorio_Executivo_PDV_Orion.pdf',max_age=0)
    @app.get('/api/branches/<id>/pdv-plan')
    def get_plan(id):
        with db() as c:
            branch=c.execute('SELECT id,code,name FROM ct_branches WHERE id=%s',(id,)).fetchone()
            if not branch:return error('Filial não encontrada.',404)
            plan=c.execute('SELECT * FROM ct_branch_pdv_plan WHERE branch_id=%s',(id,)).fetchone()
        return jsonify(id=branch['id'],code=branch['code'],name=branch['name'],pdvs=json.loads(plan['pdvs']) if plan else DEFAULT_PDVS,plan_version=plan['version'] if plan else 0)
    @app.put('/api/branches/<id>/pdv-plan')
    def save_plan(id):
        if g.user['role'] not in ['admin','manager']:return error('Somente Administrador ou Gestor pode ajustar os PDVs previstos.',403)
        body=request.get_json() or {};values=body.get('pdvs');version=body.get('version')
        if not isinstance(values,list) or not 1<=len(values)<=50 or type(version) is not int:return error('Informe de 1 a 50 números de PDV e a versão do cadastro.')
        numbers=[pdv_number(v) if isinstance(v,str) else None for v in values]
        if any(v is None for v in numbers) or len(set(numbers))!=len(numbers):return error('Use números de PDV únicos entre 1 e 9999, por exemplo 01, 02, 03 e 04.')
        numbers.sort(key=int)
        with db() as c:
            lock=' FOR UPDATE' if core['DATABASE'] else ''
            branch=c.execute('SELECT id FROM ct_branches WHERE id=%s'+lock,(id,)).fetchone()
            if not branch:return error('Filial não encontrada.',404)
            old=c.execute('SELECT * FROM ct_branch_pdv_plan WHERE branch_id=%s',(id,)).fetchone()
            if (old['version'] if old else 0)!=version:return error('O plano mudou. Atualize o dashboard antes de editar.',409)
            if old:c.execute('UPDATE ct_branch_pdv_plan SET pdvs=%s,version=version+1 WHERE branch_id=%s',(json.dumps(numbers),id))
            else:c.execute('INSERT INTO ct_branch_pdv_plan (branch_id,pdvs,version) VALUES (%s,%s,1)',(id,json.dumps(numbers)))
            audit(c,g.user['email'],'ajuste dos PDVs previstos',detail={'branch_id':id,'before':json.loads(old['pdvs']) if old else DEFAULT_PDVS,'after':numbers})
        return jsonify(ok=True)
