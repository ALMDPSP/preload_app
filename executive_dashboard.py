"""Executive aggregates and bounded payloads. All figures use saved, latest planned PDVs."""
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from dashboard import dashboard_data,normalize
from operations import operation_overview,today

def selected_data(data,q='',uf=''):
    q=normalize(q.strip());uf=uf.upper()
    stores=[s for s in data['stores'] if (not uf or s['uf']==uf) and q in normalize(' '.join(str(s[k]) for k in ['code','name','city','uf']))]
    ids={s['id'] for s in stores};machines=[m for m in data['machines'] if m['branch_id'] in ids];exceptions=[e for e in data['exceptions'] if e['branch_id'] in ids]
    days=Counter();references=0
    for m in machines:
        if m['ok'] and m['approved_at']:
            try:day=datetime.fromisoformat(m['approved_at']).astimezone(ZoneInfo('America/Sao_Paulo')).date().isoformat()
            except ValueError:continue
            days[day]+=1;references+=int(m['date_reference'])
    cumulative=0;series=[]
    for day,count in sorted(days.items()):cumulative+=count;series.append({'day':day,'daily_ok':count,'cumulative_ok':cumulative})
    expected=len(machines);ok=sum(m['ok'] for m in machines)
    return {**data,'stores':stores,'machines':machines,'exceptions':exceptions,'filters':{'q':q,'uf':uf},'date_references':references,'evolution':series,'totals':{'expected':expected,'ok':ok,'pending':expected-ok,'percent':round(ok/expected*100,1) if expected else 0,'stores':len(stores),'stores_ok':sum(s['pending']==0 for s in stores),'stores_pending':sum(s['pending']>0 for s in stores),'exceptions':len(exceptions)}}

def approval_trend(machines, current, length=30):
    """Date the current Orion OK fleet using only recorded approvals."""
    start = current - timedelta(days=length-1)
    daily = Counter()
    baseline = 0
    for machine in machines:
        if not machine['ok'] or not machine['approved_at'] or machine['date_reference']:
            continue
        try:
            day = datetime.fromisoformat(machine['approved_at']).astimezone(ZoneInfo('America/Sao_Paulo')).date()
        except ValueError:
            continue
        if day < start:
            baseline += 1
        elif day <= current:
            daily[day] += 1
    rows = []
    cumulative = baseline
    for offset in range(length):
        day = start + timedelta(days=offset)
        cumulative += daily[day]
        rows.append({'day':day.isoformat(), 'count':daily[day], 'cumulative_ok':cumulative})
    return rows

def executive_metrics(data,operations,core):
    machines=data['machines'];stores=data['stores'];ids={s['id'] for s in stores};counts=Counter(m['status'] for m in machines)
    current=today(core);week=current-timedelta(days=current.weekday());recent=0
    for m in machines:
        if m['ok'] and m['approved_at'] and not m['date_reference']:
            day=datetime.fromisoformat(m['approved_at']).astimezone(ZoneInfo('America/Sao_Paulo')).date()
            recent+=int(current-timedelta(days=6)<=day<=current)
    regional=defaultdict(lambda:{'stores':0,'expected':0,'ok':0,'pending':0})
    for s in stores:
        r=regional[s['uf'] or 'Não informada'];r['stores']+=1
        for k in ['expected','ok','pending']:r[k]+=s[k]
    regions=[{'uf':uf,**r,'percent':round(r['ok']/r['expected']*100,1) if r['expected'] else 0} for uf,r in regional.items()]
    schedule=[s for s in operations['schedule'] if s['branch_id'] in ids];issues=[i for i in operations['issues'] if i['branch_id'] in ids and i['status']!='Resolvida']
    overdue=[s for s in schedule if s['status']=='Atrasado'];risk=defaultdict(lambda:{'overdue_pdvs':set(),'issues':0,'critical':0,'pdvs':set()})
    for r in overdue:risk[r['branch_id']]['overdue_pdvs'].add(r['pdv']);risk[r['branch_id']]['pdvs'].add(r['pdv'])
    for i in issues:
        r=risk[i['branch_id']];r['issues']+=1;r['critical']+=int(i['priority']=='Crítica');r['pdvs'].add(i['pdv'])
    for m in machines:
        if m['status'] in ['Bloqueado','Rejeitado']:risk[m['branch_id']]['pdvs'].add(m['pdv'])
    attention=[]
    for s in stores:
        if s['id'] in risk:
            r=risk[s['id']];attention.append({'branch_id':s['id'],'code':s['code'],'name':s['name'],'uf':s['uf'],'pdvs':sorted(r['pdvs'],key=int),'overdue':len(r['overdue_pdvs']),'open_issues':r['issues'],'critical':r['critical'],'pending':s['pending'],'percent':s['percent']})
    attention.sort(key=lambda r:(-r['critical'],-r['overdue'],-r['open_issues'],-len(r['pdvs']),r['code']))
    return {'pipeline':[{'status':status,'count':counts[status]} for status in ['Sem cutover','Pendente','Em andamento','Bloqueado','Aguardando aceite','Rejeitado','Orion OK']],
      'stores_not_started':sum(all(not m['cutover_id'] for m in s['machines']) for s in stores),'stores_in_progress':sum(s['pending']>0 and any(m['cutover_id'] for m in s['machines']) for s in stores),
      'recent_ok':recent,'recent_from':(current-timedelta(days=6)).isoformat(),'recent_to':current.isoformat(),'recent_daily_average':round(recent/7,1),
      'regions':sorted(regions,key=lambda r:(-r['pending'],r['uf'])),'attention':attention[:10],'attention_total':len(attention),'open_issues':len(issues),'critical_issues':sum(i['priority']=='Crítica' for i in issues),'overdue_pdvs':len(overdue),'planned_pdvs':sum(s['status']!='Fora do escopo' for s in schedule),'overdue_issues':sum(i['overdue'] for i in issues)}

def integer(value,default,maximum):
    try:return max(1,min(int(value),maximum))
    except (TypeError,ValueError):return default

def dashboard_bundle(core,args):
    data=dashboard_data(core);operations=operation_overview(core,data);scoped=selected_data(data,args.get('q','')[:200],args.get('uf','')[:2]);page=integer(args.get('page'),1,100000);size=25
    pages=max(1,(len(scoped['stores'])+size-1)//size);page=min(page,pages)
    result={k:v for k,v in scoped.items() if k not in ['machines','stores','_revision']}
    result['exceptions']=result['exceptions'][:100]
    result['approval_trend']=approval_trend(scoped['machines'],today(core))
    from rollout_base import rollout_base_summary
    result['rollout_base']=rollout_base_summary(core,scoped)
    from rollout_management import period_summary,model
    result['management']=period_summary(core,args,model(core,scoped,operations))
    result.update(compact=True,stores=scoped['stores'][(page-1)*size:page*size],pagination={'page':page,'pages':pages,'total':len(scoped['stores']),'size':size},executive=executive_metrics(scoped,operations,core),operations={'generated_at':operations['generated_at'],'goal':operations['goal'],'metrics':operations['metrics']},_snapshot=data)
    return result

def machine_page(core,args):
    status=args.get('status','')
    rollout_status=status in {'deployed','undeployed'}
    data=dashboard_data(core,args.get('q','')[:200],args.get('uf','').upper()[:2],include_evolution=not rollout_status)
    if rollout_status:
        from rollout_base import base_records,deployed,reported_version
        _,inventory=base_records(core)
        rows=[]
        for machine in data['machines']:
            record=inventory.get((machine['branch_id'],machine['pdv']))
            if deployed(machine,record)!=(status=='deployed'):
                continue
            label=machine['status']
            if status=='deployed' and not machine['ok']:
                label='Implantação declarada'
            rows.append({**machine,'status':label,
                         'installed_version':reported_version(record),
                         'deployed_at':(record or {}).get('deployed_at','')})
    else:
        complete={s['id'] for s in data['stores'] if not s['pending']}
        rows=[m for m in data['machines'] if (status not in ['ok','pending','stores_ok'] or (m['ok'] if status=='ok' else not m['ok'] if status=='pending' else m['branch_id'] in complete)) and (status in ['','all','ok','pending','stores_ok'] or m['status']==status)]
    size=40;pages=max(1,(len(rows)+size-1)//size);page=min(integer(args.get('page'),1,100000),pages)
    return {'rows':rows[(page-1)*size:page*size],'page':page,'pages':pages,'total':len(rows)}
