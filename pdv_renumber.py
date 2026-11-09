"""Atomic PDV identity correction without creating or reordering cutovers."""
import json
from flask import request,g,jsonify
from dashboard import pdv_number,DEFAULT_PDVS

class RenumberConflict(Exception):pass

def register_pdv_renumber(app,core):
    @app.put('/api/rollout-base/branches/<id>/pdv-number')
    def renumber_rollout_pdv(id):
        error=core['error']
        if g.user['role'] not in ['admin','manager']:return error('Somente Administrador ou Gestor pode alterar a numeração do PDV.',403)
        body=request.get_json(silent=True)
        if not isinstance(body,dict):return error('Informe o número atual e o novo número do PDV.')
        old=pdv_number(body.get('from_pdv'));new=pdv_number(body.get('to_pdv'))
        if not old or not new or old==new:return error('Informe um novo número de PDV entre 1 e 9999, diferente do atual.')
        if any(type(body.get(k)) is not int or body[k]<0 for k in ['plan_version','inventory_version']):return error('Reabra o cadastro antes de alterar a numeração.')
        try:
            with core['db']() as c:
                lock=' FOR UPDATE' if core['DATABASE'] else ''
                branch=c.execute('SELECT id,code FROM ct_branches WHERE id=%s'+lock,(id,)).fetchone()
                if not branch:return error('Filial não encontrada.',404)
                plan=c.execute('SELECT * FROM ct_branch_pdv_plan WHERE branch_id=%s',(id,)).fetchone();numbers=json.loads(plan['pdvs']) if plan else list(DEFAULT_PDVS)
                if (plan['version'] if plan else 0)!=body['plan_version']:return error('A lista de PDVs mudou. Reabra o cadastro.',409)
                if old not in numbers:return error('O PDV atual não está na lista prevista desta filial.')
                if new in numbers:return error('O novo número já existe nesta filial. Escolha outro número.',409)
                inventory=c.execute('SELECT * FROM ct_rollout_inventory WHERE branch_id=%s AND pdv=%s',(id,old)).fetchone()
                if (inventory['version'] if inventory else 0)!=body['inventory_version']:return error('O cadastro do PDV mudou. Reabra antes de alterar.',409)
                for table in ['ct_rollout_inventory','ct_rollout_schedule','ct_rollout_issues']:
                    if c.execute('SELECT pdv FROM '+table+' WHERE branch_id=%s AND pdv=%s',(id,new)).fetchone():return error('O novo número já possui registros nesta filial. Escolha outro número.',409)
                suffix=' FOR UPDATE OF x' if core['DATABASE'] else ''
                records=c.execute('SELECT x.* FROM ct_cutovers x JOIN ct_cutover_branch l ON l.cutover_id=x.id WHERE l.branch_id=%s ORDER BY x.id'+suffix,(id,)).fetchall()
                affected=[]
                for row in records:
                    state=json.loads(row['state']);number=pdv_number(state.get('meta',{}).get('pdv'))
                    if number==new:return error('Já existe cutover para o novo número nesta filial. Escolha outro número.',409)
                    if number==old:affected.append((row,state))
                numbers=sorted([new if n==old else n for n in numbers],key=int);stamp=core['now']();actor=g.user['email']
                if plan:
                    changed=c.execute('UPDATE ct_branch_pdv_plan SET pdvs=%s,version=version+1 WHERE branch_id=%s AND version=%s',(json.dumps(numbers),id,body['plan_version']))
                else:changed=c.execute('INSERT INTO ct_branch_pdv_plan (branch_id,pdvs,version) VALUES (%s,%s,1) ON CONFLICT(branch_id) DO NOTHING',(id,json.dumps(numbers)))
                if changed.rowcount!=1:raise RenumberConflict()
                if inventory:
                    changed=c.execute('UPDATE ct_rollout_inventory SET pdv=%s,version=version+1,updated_at=%s,updated_by=%s WHERE branch_id=%s AND pdv=%s AND version=%s',(new,stamp,actor,id,old,body['inventory_version']))
                    if changed.rowcount!=1:raise RenumberConflict()
                c.execute('UPDATE ct_rollout_schedule SET pdv=%s,version=version+1,updated_at=%s,updated_by=%s WHERE branch_id=%s AND pdv=%s',(new,stamp,actor,id,old))
                c.execute('UPDATE ct_rollout_issues SET pdv=%s,version=version+1,updated_at=%s,updated_by=%s WHERE branch_id=%s AND pdv=%s',(new,stamp,actor,id,old))
                for row,state in affected:
                    state['meta']['pdv']=new;state['meta']['branch']=branch['code']+' / PDV '+new
                    # Identity-only correction: preserve last checklist save time/actor and the ordering of historical runs.
                    changed=c.execute('UPDATE ct_cutovers SET state=%s,title=%s,version=version+1 WHERE id=%s AND version=%s',(json.dumps(state,ensure_ascii=False),state['meta']['branch'],row['id'],row['version']))
                    if changed.rowcount!=1:raise RenumberConflict()
                    core['audit'](c,actor,'renumeração de PDV',row['id'],{'branch_id':id,'from_pdv':old,'to_pdv':new,'previous_version':row['version']})
                core['audit'](c,actor,'alteração da numeração na base de rollout',detail={'branch_id':id,'from_pdv':old,'to_pdv':new,'cutovers_updated':len(affected)})
        except RenumberConflict:return error('Outro usuário atualizou os registros. Nenhuma alteração foi aplicada. Reabra o cadastro.',409)
        return jsonify(ok=True,pdv=new,cutovers_updated=len(affected))
