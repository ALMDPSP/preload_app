"""Read-only operational reports, calculated from saved cutovers."""
import json
from flask import jsonify

def summarize(state,rejected,ids):
    tasks=state.get('tasks',{})
    complete=sum(tasks.get(id,{}).get('status')=='Concluído' for id in ids)
    blocked=sum(tasks.get(id,{}).get('status')=='Bloqueado' for id in ids)
    decisions=state.get('decisions',{})
    accepted=all(decisions.get(k,{}).get('value')=='GO' and all(decisions[k].get(v,'').strip() for v in ['owner','at']) for k in ['linx','orion'])
    if rejected:status='Rejeitado'
    elif complete==len(ids):status='Concluído' if accepted else 'Aguardando aceite'
    elif blocked:status='Bloqueado'
    elif complete or any(t.get('status')=='Em andamento' for t in tasks.values()):status='Em andamento'
    else:status='Pendente'
    return status,complete,blocked

def register_reports(app,core):
    db,ids=core['db'],core['IDS']
    @app.get('/api/reports/rollout-executive.pdf')
    def report_executive_rollout():
        from rollout_executive_report import download_rollout_executive
        return download_rollout_executive(core)

    @app.get('/api/reports/cutovers')
    def report_cutovers():
        with db() as c:
            rows=c.execute('SELECT b.id AS branch_id,b.code,b.name,b.city,b.uf,b.active,b.opening_soon,x.id AS cutover_id,x.title,x.state,x.version,x.updated_at,x.updated_by,r.reason AS rejection_reason FROM ct_branches b LEFT JOIN ct_cutover_branch l ON l.branch_id=b.id LEFT JOIN ct_cutovers x ON x.id=l.cutover_id LEFT JOIN ct_cutover_reviews r ON r.cutover_id=x.id ORDER BY b.code,x.updated_at DESC').fetchall()
        result=[]
        for item in rows:
            row=dict(item);state=json.loads(row.pop('state')) if row['cutover_id'] else {}
            status,complete,blocked=summarize(state,bool(row['rejection_reason']),ids) if row['cutover_id'] else ('Sem cutover',0,0)
            result.append({**row,'status':status,'completed':complete,'pending':len(ids)-complete if row['cutover_id'] else 0,'blocked':blocked,'total':len(ids) if row['cutover_id'] else 0,'pdv':state.get('meta',{}).get('pdv',''),'date':state.get('meta',{}).get('date','')})
        return jsonify(rows=result,generated_at=core['now'](),task_count=len(ids))
