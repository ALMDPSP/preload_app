"""Saved, resumable PDV checklists scoped to one branch."""
import json
from flask import jsonify
from dashboard import pdv_number,DEFAULT_PDVS
from reports import summarize

def register_branch_progress(app,core):
    @app.get('/api/branches/<id>/cutover-progress')
    def branch_cutover_progress(id):
        with core['db']() as c:
            branch=c.execute('SELECT id,code,name,active,needs_review FROM ct_branches WHERE id=%s',(id,)).fetchone()
            if not branch:return core['error']('Filial não encontrada.',404)
            plan=c.execute('SELECT pdvs FROM ct_branch_pdv_plan WHERE branch_id=%s',(id,)).fetchone()
            rows=c.execute('SELECT x.id,x.title,x.state,x.version,x.updated_at,x.updated_by,rv.reason AS rejection_reason FROM ct_cutovers x JOIN ct_cutover_branch l ON l.cutover_id=x.id LEFT JOIN ct_cutover_reviews rv ON rv.cutover_id=x.id WHERE l.branch_id=%s ORDER BY x.updated_at DESC,x.id DESC',(id,)).fetchall()
        expected=json.loads(plan['pdvs']) if plan else list(DEFAULT_PDVS)
        latest={};executions=[]
        for row in rows:
            state=json.loads(row['state']);raw=state.get('meta',{}).get('pdv','');pdv=pdv_number(raw);status,complete,blocked=summarize(state,bool(row['rejection_reason']),core['IDS'])
            item={k:row[k] for k in ['id','title','version','updated_at','updated_by','rejection_reason']}
            item.update(pdv=pdv or raw or 'Não informado',status=status,completed=complete,pending=len(core['IDS'])-complete,blocked=blocked,total=len(core['IDS']))
            executions.append(item);latest.setdefault(pdv or 'legacy-'+row['id'],item)
        machines=[]
        for pdv in expected:
            saved=latest.pop(pdv,None);machines.append({'pdv':pdv,'planned':True,'execution':saved,'status':saved['status'] if saved else 'Não iniciado'})
        machines.extend({'pdv':item['pdv'],'planned':False,'execution':item,'status':item['status']} for item in latest.values())
        return jsonify(branch=dict(branch),machines=machines,executions=executions,totals={'expected':len(expected),'saved':sum(m['execution'] is not None for m in machines if m['planned']),'ok':sum(m['status']=='Concluído' for m in machines if m['planned']),'pending':sum(m['status']!='Concluído' for m in machines if m['planned'])})
