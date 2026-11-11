"""Organization and declared deployment inventory, kept separate from checklist approval."""
import json
from collections import Counter,defaultdict
from datetime import date
from flask import request,g,jsonify
from dashboard import dashboard_data,pdv_number,DEFAULT_PDVS,normalize

SCHEMA=[
 'CREATE TABLE IF NOT EXISTS ct_rollout_organization (branch_id TEXT PRIMARY KEY REFERENCES ct_branches(id) ON DELETE CASCADE,regional TEXT NOT NULL,gr TEXT NOT NULL,version INTEGER NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL)',
 'CREATE TABLE IF NOT EXISTS ct_rollout_inventory (branch_id TEXT NOT NULL REFERENCES ct_branches(id) ON DELETE CASCADE,pdv TEXT NOT NULL,status TEXT NOT NULL,installed_version TEXT NOT NULL,deployed_at TEXT NOT NULL,notes TEXT NOT NULL,version INTEGER NOT NULL,updated_at TEXT NOT NULL,updated_by TEXT NOT NULL,PRIMARY KEY(branch_id,pdv))'
]

def migrate_rollout_base(c):
    for sql in SCHEMA:c.execute(sql)

def base_records(core):
    with core['db']() as c:
        org={r['branch_id']:dict(r) for r in c.execute('SELECT branch_id,regional,gr FROM ct_rollout_organization').fetchall()}
        inventory={(r['branch_id'],r['pdv']):dict(r) for r in c.execute('SELECT branch_id,pdv,status,installed_version,deployed_at FROM ct_rollout_inventory').fetchall()}
    return org,inventory

def deployed(machine,record):return bool(machine.get('ok') or record and record['status']=='Implantado')

def reported_version(record):
    value=(record or {}).get('installed_version','').strip()
    return '' if normalize(value) in {'nao informada','nao informado'} else value

def rollout_base_summary(core,data,records=None):
    org,inventory=records if records is not None else base_records(core)
    groups={key:{} for key in ['gr','regional']};versions=Counter();updated_stores=0;updated_pdvs=0;no_version=0;missing_org=0
    for store in data['stores']:
        organization=org.get(store['id'],{});count=0
        for machine in store['machines']:
            row=inventory.get((store['id'],machine['pdv']))
            if deployed(machine,row):
                count+=1;updated_pdvs+=1
                version=reported_version(row)
                if version:versions[version]+=1
                else:no_version+=1
        updated_stores+=int(count>0)
        missing_org+=int(not organization.get('gr') or not organization.get('regional'))
        for key in groups:
            label=organization.get(key) or 'Não informado';identity=normalize(label)
            item=groups[key].setdefault(identity,{'name':label,'stores_expected':0,'stores_updated':0,'pdvs_expected':0,'pdvs_deployed':0})
            item['stores_expected']+=1;item['stores_updated']+=int(count>0);item['pdvs_expected']+=store['expected'];item['pdvs_deployed']+=count
    for group in groups.values():
        for row in group.values():row['percent']=round(row['stores_updated']/row['stores_expected']*100,1) if row['stores_expected'] else 0
    expected=data['totals']['expected'];stores=data['totals']['stores']
    return {'pdvs_expected':expected,'pdvs_deployed':updated_pdvs,'pdvs_pending':expected-updated_pdvs,'pdvs_percent':round(updated_pdvs/expected*100,1) if expected else 0,'stores_expected':stores,'stores_updated':updated_stores,'stores_percent':round(updated_stores/stores*100,1) if stores else 0,'stores_missing_organization':missing_org,'deployed_without_version':no_version,
      'versions':[{'name':name,'count':count,'percent':round(count/(updated_pdvs-no_version)*100,1)} for name,count in sorted(versions.items(),key=lambda r:(-r[1],r[0]))],
      'by_gr':sorted(groups['gr'].values(),key=lambda r:(-r['stores_expected'],r['name'])),'by_regional':sorted(groups['regional'].values(),key=lambda r:(-r['stores_expected'],r['name']))}

def branch_base(core,id):
    with core['db']() as c:
        branch=c.execute('SELECT id,code,name,uf,active,opening_soon,needs_review FROM ct_branches WHERE id=%s',(id,)).fetchone()
        if not branch:return None
        org=c.execute('SELECT * FROM ct_rollout_organization WHERE branch_id=%s',(id,)).fetchone()
        plan=c.execute('SELECT * FROM ct_branch_pdv_plan WHERE branch_id=%s',(id,)).fetchone()
        records={r['pdv']:dict(r) for r in c.execute('SELECT * FROM ct_rollout_inventory WHERE branch_id=%s',(id,)).fetchall()}
    pdvs=json.loads(plan['pdvs']) if plan else list(DEFAULT_PDVS)
    return {'branch':dict(branch),'regional':org['regional'] if org else '','gr':org['gr'] if org else '','version':org['version'] if org else 0,'plan_version':plan['version'] if plan else 0,'machines':[records.get(pdv,{'pdv':pdv,'status':'Pendente','installed_version':'','deployed_at':'','notes':'','version':0}) for pdv in pdvs]}

def clean(body,key,maximum,uppercase=False):
    value=body.get(key,'')
    if not isinstance(value,str) or len(value)>maximum:raise ValueError('Confira o campo '+key+'.')
    value=' '.join(value.split()) if key in ['regional','gr','installed_version'] else value.strip()
    return value.upper() if uppercase else value

def register_rollout_base(app,core):
    @app.get('/api/rollout-base')
    def list_rollout_base():
        data=dashboard_data(core,include_evolution=False);organizations,inventory=base_records(core);active={s['id']:s for s in data['stores']}
        with core['db']() as c:branches=[dict(r) for r in c.execute('SELECT b.id,b.code,b.name,b.uf,b.active,b.opening_soon,b.needs_review,p.pdvs FROM ct_branches b LEFT JOIN ct_branch_pdv_plan p ON p.branch_id=b.id ORDER BY b.code').fetchall()]
        q=normalize(request.args.get('q','')[:200].strip());gr=normalize(request.args.get('gr','')[:120].strip());regional=normalize(request.args.get('regional','')[:120].strip());uf=request.args.get('uf','').upper()[:2];rows=[]
        for branch in branches:
            org=organizations.get(branch['id'],{});store=active.get(branch['id']);plan=json.loads(branch['pdvs']) if branch['pdvs'] else list(DEFAULT_PDVS)
            if uf and branch['uf']!=uf or gr and normalize(org.get('gr',''))!=gr or regional and normalize(org.get('regional',''))!=regional:continue
            if q not in normalize(' '.join([branch['code'],branch['name'],org.get('gr',''),org.get('regional','')])):continue
            count=sum(deployed(m,inventory.get((branch['id'],m['pdv']))) for m in store['machines']) if store else sum(inventory.get((branch['id'],pdv),{}).get('status')=='Implantado' for pdv in plan)
            rows.append({k:branch[k] for k in ['id','code','name','uf','active','opening_soon','needs_review']}|{'regional':org.get('regional',''),'gr':org.get('gr',''),'expected':len(plan),'deployed':count,'percent':round(count/len(plan)*100,1) if plan else 0,'in_scope':bool(store)})
        try:page=max(1,int(request.args.get('page',1)))
        except ValueError:page=1
        pages=max(1,(len(rows)+24)//25);page=min(page,pages)
        return jsonify(rows=rows[(page-1)*25:page*25],page=page,pages=pages,total=len(rows),grs=sorted({o['gr'] for o in organizations.values() if o['gr']}),regionals=sorted({o['regional'] for o in organizations.values() if o['regional']}),ufs=sorted({b['uf'] for b in branches if b['uf']}))
    @app.get('/api/rollout-base/branches/<id>')
    def read_rollout_base(id):
        result=branch_base(core,id)
        return jsonify(result) if result else core['error']('Filial não encontrada.',404)
    @app.put('/api/rollout-base/branches/<id>')
    def save_rollout_base(id,body=None):
        if g.user['role']=='viewer':return core['error']('Consulta permite somente leitura.',403)
        body=body if body is not None else request.get_json(silent=True)
        try:
            if not isinstance(body,dict):raise ValueError('Preencha os dados do cadastro.')
            regional=clean(body,'regional',120,True);gr=clean(body,'gr',120,True)
            if type(body.get('version')) is not int or type(body.get('plan_version')) is not int:raise ValueError('Atualize o cadastro antes de salvar.')
            machines=body.get('machines')
            if not isinstance(machines,list) or not 1<=len(machines)<=50:raise ValueError('Informe de 1 a 50 PDVs previstos.')
            prepared=[];seen=set()
            for row in machines:
                if not isinstance(row,dict):raise ValueError('PDV inválido.')
                pdv=pdv_number(row.get('pdv'));status=row.get('status');version=row.get('version');installed=clean(row,'installed_version',80);at=clean(row,'deployed_at',10);notes=clean(row,'notes',2000)
                if not pdv or pdv in seen or status not in ['Pendente','Implantado'] or type(version) is not int:raise ValueError('Confira os PDVs, a situação e a versão do registro.')
                seen.add(pdv)
                if at:
                    try:date.fromisoformat(at)
                    except ValueError:raise ValueError('Data de implantação inválida.')
                    if len(at)!=10:raise ValueError('Data de implantação inválida.')
                prepared.append((pdv,status,installed,at,notes,version))
        except ValueError as exc:return core['error'](str(exc))
        with core['db']() as c:
            lock=' FOR UPDATE' if core['DATABASE'] else ''
            if not c.execute('SELECT id FROM ct_branches WHERE id=%s'+lock,(id,)).fetchone():return core['error']('Filial não encontrada.',404)
            plan=c.execute('SELECT * FROM ct_branch_pdv_plan WHERE branch_id=%s',(id,)).fetchone();expected=json.loads(plan['pdvs']) if plan else DEFAULT_PDVS
            if (plan['version'] if plan else 0)!=body['plan_version']:return core['error']('A lista de PDVs mudou. Reabra o cadastro.',409)
            if any(pdv not in expected for pdv,*rest in prepared):return core['error']('Inclua o PDV na lista prevista da filial antes de cadastrar.')
            org=c.execute('SELECT * FROM ct_rollout_organization WHERE branch_id=%s',(id,)).fetchone()
            if (org['version'] if org else 0)!=body['version']:return core['error']('Outra pessoa atualizou este cadastro. Reabra antes de salvar.',409)
            if g.user['role'] not in ['admin','manager'] and (regional,gr)!=(org['regional'] if org else '',org['gr'] if org else ''):return core['error']('Somente Administrador ou Gestor altera GR e regional.',403)
            old={r['pdv']:dict(r) for r in c.execute('SELECT * FROM ct_rollout_inventory WHERE branch_id=%s',(id,)).fetchall()}
            # Validate all versions before any write, so a conflict never saves a partial form.
            if any((old.get(pdv,{}).get('version',0))!=version for pdv,status,installed,at,notes,version in prepared):return core['error']('Um PDV foi atualizado por outra pessoa. Reabra o cadastro.',409)
            stamp=core['now']();actor=g.user['email']
            c.execute('INSERT INTO ct_rollout_organization (branch_id,regional,gr,version,updated_at,updated_by) VALUES (%s,%s,%s,1,%s,%s) ON CONFLICT(branch_id) DO UPDATE SET regional=excluded.regional,gr=excluded.gr,version=ct_rollout_organization.version+1,updated_at=excluded.updated_at,updated_by=excluded.updated_by',(id,regional,gr,stamp,actor))
            for pdv,status,installed,at,notes,version in prepared:
                c.execute('INSERT INTO ct_rollout_inventory (branch_id,pdv,status,installed_version,deployed_at,notes,version,updated_at,updated_by) VALUES (%s,%s,%s,%s,%s,%s,1,%s,%s) ON CONFLICT(branch_id,pdv) DO UPDATE SET status=excluded.status,installed_version=excluded.installed_version,deployed_at=excluded.deployed_at,notes=excluded.notes,version=ct_rollout_inventory.version+1,updated_at=excluded.updated_at,updated_by=excluded.updated_by',(id,pdv,status,installed,at,notes,stamp,actor))
            core['audit'](c,actor,'cadastro da base de rollout',detail={'branch_id':id,'before_organization':{'regional':org['regional'],'gr':org['gr']} if org else None,'regional':regional,'gr':gr,'before_pdvs':{pdv:old.get(pdv) for pdv,*rest in prepared},'after_pdvs':[{'pdv':pdv,'status':status,'installed_version':installed,'deployed_at':at,'notes':notes} for pdv,status,installed,at,notes,version in prepared]})
        return jsonify(ok=True)
