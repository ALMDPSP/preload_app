"""Executive report with the rollout dashboard first and bounded detail pages."""
from datetime import datetime
from zoneinfo import ZoneInfo
from xml.sax.saxutils import escape
from flask import send_file,request
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Spacer,Table,TableStyle,PageBreak
from reportlab.graphics.shapes import Drawing,Rect,String,Line,PolyLine,Circle
from dashboard import dashboard_data
from rollout_base import rollout_base_summary
from operations import operation_overview,today
from executive_dashboard import approval_trend,executive_metrics

from pdf_brand import INK, MUTED, BLUE, PALE, LINE, BG, WIDTH, build_report, columns, register_fonts

def report_payload(core):
    data=dashboard_data(core)
    operations=operation_overview(core,data)
    base=rollout_base_summary(core,data)
    executive=executive_metrics(data,operations,core)
    trend=approval_trend(data['machines'],today(core),length=14)
    branches={s['id']:s for s in data['stores']}
    updates=[{'code':m['code'],'pdv':m['pdv'],'source':'Cutover','status':m['status'],'at':m['updated_at']} for m in data['machines'] if m['updated_at']]
    with core['db']() as c:
        for row in c.execute('SELECT branch_id,pdv,status,updated_at FROM ct_rollout_inventory').fetchall():
            if row['branch_id'] in branches and row['pdv'] in branches[row['branch_id']]['pdvs']:
                updates.append({'code':branches[row['branch_id']]['code'],'pdv':row['pdv'],'source':'Base de Rollout','status':row['status'],'at':row['updated_at']})
        for row in c.execute('SELECT branch_id,updated_at FROM ct_rollout_organization').fetchall():
            if row['branch_id'] in branches:
                updates.append({'code':branches[row['branch_id']]['code'],'pdv':'','source':'GR / Regional','status':'Cadastro atualizado','at':row['updated_at']})
    updates.sort(key=lambda r:(r['at'],r['code'],r['pdv'],r['source']),reverse=True)
    return {'generated_at':data['generated_at'],'base':base,'totals':data['totals'],'excluded':data['excluded'],
            'executive':executive,'network':{'active_branches':data['active_branches_total'],
            'open_issues':operations['metrics']['open_issues'],'overdue_issues':operations['metrics']['overdue_issues']},'trend':trend,'updates':updates[:5],'updates_total':len(updates),'date_references':data['date_references']}

def create_rollout_executive_pdf(data):
    register_fonts()
    styles={
      'title':ParagraphStyle('rt',fontName='RolloutSans-Bold',fontSize=25,leading=31,textColor=INK,spaceAfter=7),
      'h':ParagraphStyle('rh',fontName='RolloutSans-Bold',fontSize=14,leading=19,textColor=INK,spaceBefore=12,spaceAfter=8,keepWithNext=True),
      'body':ParagraphStyle('rb',fontName='RolloutSans',fontSize=11,leading=15,textColor=INK,spaceAfter=8),
      'muted':ParagraphStyle('rm',fontName='RolloutSans',fontSize=9,leading=13,textColor=MUTED,spaceAfter=6),
      'cell':ParagraphStyle('rc',fontName='RolloutSans',fontSize=10,leading=13,textColor=INK),
      'th':ParagraphStyle('rth',fontName='RolloutSans-Bold',fontSize=9,leading=12,textColor=INK),
      'klabel':ParagraphStyle('rkl',fontName='RolloutSans-Bold',fontSize=9,leading=12,textColor=INK),
      'kvalue':ParagraphStyle('rkv',fontName='RolloutSans-Bold',fontSize=25,leading=33,textColor=INK),
    }
    def p(value,style='body'):
        return Paragraph(escape(str(value)).replace('\n','<br/>'),styles[style])
    def n(value):return f'{value:,}'.replace(',','.')
    def pct(value):return str(value).replace('.',',')+'%'
    def stamp(value):return datetime.fromisoformat(value).astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
    def short(value,maximum=85,tail=0):
        text=str(value)
        if len(text)<=maximum:return text
        return text[:maximum-3-tail]+'...'+(text[-tail:] if tail else '')
    def table(rows,widths,padding=7):
        t=Table([[p(v,'th' if i==0 else 'cell') for v in row] for i,row in enumerate(rows)],colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),BG),
          ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#fafbfd')]),
          ('LINEBELOW',(0,0),(-1,-1),.35,LINE),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
          ('TOPPADDING',(0,0),(-1,-1),padding),('BOTTOMPADDING',(0,0),(-1,-1),padding)]))
        return t
    def kpis(items):
        cells=[[p(label,'klabel'),p(n(value),'kvalue'),p(note,'muted')] for label,value,note in items]
        t=Table([cells],colWidths=[WIDTH/len(cells)]*len(cells))
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,-1),BG),
          ('BOX',(0,0),(-1,-1),.5,LINE),('LINEAFTER',(0,0),(-2,-1),.5,colors.white),
          ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),9)]))
        return t
    def rate(count, total):
        value = f'{count / total * 100:.2f}'.rstrip('0').rstrip('.') if total else '0'
        return pct(value)

    def headline_cards(items):
        grid=kpis([(label,value,note) for label,value,note,_ in items])
        grid.setStyle(TableStyle([('BACKGROUND',(i,0),(i,0),background) for i,(_,_,_,background) in enumerate(items)]))
        return grid

    def rollout_progress(expected, installed, ok, delayed, critical):
        width=400
        graphic = Drawing(width, 134)
        dark = INK
        light = colors.HexColor('#dce7f6')
        track = colors.HexColor('#52647f')
        graphic.add(Rect(0,0,width,134,fillColor=dark,strokeColor=None))

        def label(x, y, value, size=8, bold=False, color=light, align='start'):
            graphic.add(String(x,y,str(value),fontName='RolloutSans-Bold' if bold else 'RolloutSans',
                               fontSize=size,fillColor=color,textAnchor=align))

        label(15,111,'Avanço do rollout',13,True,colors.white)
        label(208,111,'Atenção no rollout',13,True,colors.white)
        graphic.add(Line(192,19,192,117,strokeColor=track))
        for y, name, value, color in [(82,'Implantação',installed,PALE),(43,'Orion OK',ok,PALE)]:
            label(14,y,name)
            unit = ' PDV' if value == 1 else ' PDVs'
            label(177,y,n(value)+unit+' | '+rate(value,expected),8,True,colors.white,'end')
            graphic.add(Rect(14,y-12,162,5,fillColor=track,strokeColor=None))
            ratio = min(1,value/expected) if expected else 0
            if ratio:
                graphic.add(Rect(14,y-12,162*ratio,5,fillColor=color,strokeColor=None))
        risks = [(max(0,installed-ok),'Implantados','sem Orion OK'),
                 (delayed,'PDVs','atrasados'),(critical,'Pendências','críticas')]
        for i,(value, first, second) in enumerate(risks):
            x = 209+i*64
            label(x,70,n(value),17,True,colors.white)
            label(x,48,first)
            label(x,34,second)
        return graphic

    def approval_chart(trend):
        width=440
        chart = Drawing(width,162)
        left, right, bottom, top = 38, width-16, 26, 135
        maximum = max([row['cumulative_ok'] for row in trend]+[1])
        for value in sorted({0, maximum//2, maximum}):
            y = bottom+(top-bottom)*value/maximum
            chart.add(Line(left,y,right,y,strokeColor=LINE))
            chart.add(String(left-5,y-2,n(value),fontName='RolloutSans',fontSize=7,
                             textAnchor='end',fillColor=MUTED))
        points = []
        for i,row in enumerate(trend):
            x = left+(right-left)*i/max(1,len(trend)-1)
            y = bottom+(top-bottom)*row['cumulative_ok']/maximum
            points.extend([x,y])
            if i%3==0 or i==len(trend)-1:
                day = row['day'][8:10]+'/'+row['day'][5:7]
                chart.add(String(x,8,day,fontName='RolloutSans',fontSize=7,textAnchor='middle',fillColor=MUTED))
        if trend and trend[-1]['cumulative_ok']:
            chart.add(PolyLine(points,strokeColor=BLUE,strokeWidth=2))
            for i,row in enumerate(trend):
                if row['count'] or i==len(trend)-1:
                    chart.add(Circle(points[2*i],points[2*i+1],2.8,fillColor=BLUE,strokeColor=colors.white,strokeWidth=.7))
            total = trend[-1]['cumulative_ok']
            unit = ' PDV' if total == 1 else ' PDVs'
            chart.add(String(right,top+9,n(total)+unit,fontName='RolloutSans-Bold',
                             fontSize=8,textAnchor='end',fillColor=BLUE))
        else:
            chart.add(String(width/2,78,'Sem aprovações com data identificada.',fontName='RolloutSans',
                             fontSize=9,textAnchor='middle',fillColor=MUTED))
        return chart

    b, t, e = data['base'], data['totals'], data['executive']
    network = data['network']
    gap = max(0,b['pdvs_deployed']-t['ok'])
    if e['critical_issues']:
        focus = 'Tratar '+n(e['critical_issues'])+' pendência(s) crítica(s).'
    elif e['overdue_pdvs']:
        focus = 'Priorizar '+n(e['overdue_pdvs'])+' PDV(s) com prazo vencido.'
    elif gap:
        focus = 'Validar '+n(gap)+' PDV(s) implantado(s) que aguardam Orion OK.'
    elif b['pdvs_pending']:
        focus = 'Avançar a implantação dos PDVs pendentes.'
    elif b['pdvs_expected']:
        focus = 'Parque implantado. Acompanhar a operação das lojas.'
    else:
        focus = 'Nenhum PDV previsto no escopo.'
    cards = [
        ('Filiais ativas',network['active_branches'],'Total da rede no escopo',BG),
        ('PDVs previstos',b['pdvs_expected'],'Parque previsto',BG),
        ('PDVs implantados',b['pdvs_deployed'],rate(b['pdvs_deployed'],b['pdvs_expected'])+' do parque',colors.HexColor('#e9f6f0')),
        ('PDVs pendentes',b['pdvs_pending'],'Aguardam implantação',colors.HexColor('#fff6e4')),
        ('Lojas atualizadas',b['stores_updated'],n(b['stores_updated'])+' de '+n(b['stores_expected'])+' lojas',BG),
        ('Pendências abertas',network['open_issues'],'',colors.HexColor('#fcf0f2')),
    ]
    flow = [
        p('Visão geral do rollout','title'),
        p('Posição em '+stamp(data['generated_at'])+' (Brasília)','muted'),
        headline_cards(cards),Spacer(1,16),
        columns(
            [p('Evolução acumulada do Orion OK','h'),approval_chart(data['trend']),
             p('Últimos 14 dias, com saldo anterior.','muted')],
            [Spacer(1,12),rollout_progress(b['pdvs_expected'],b['pdvs_deployed'],t['ok'],e['overdue_pdvs'],e['critical_issues']),
             p('Prioridade executiva','h'),p(focus)],
            (440,400),
        ),
        p('Escopo: filiais ativas e abertas com cadastro confirmado.','muted'),
        PageBreak(),
    ]
    period=data.get('period_summary')
    if period:
        def fmt_day(day):return day.split('-')[2]+'/'+day.split('-')[1]+'/'+day.split('-')[0]
        cur=period['current'];prior=period['previous']
        waves=sorted([w for w in period['waves'] if w['start_date']<=period['to_date'] and w['due_date']>=period['from_date']],key=lambda w:(-w['overdue'],w['due_date'],w['name']))[:3]
        wave_rows=[['Onda','Previstos','Validados','Atrasados','Justificativa']]
        wave_rows += [[short(w['name'],32),n(w['planned']),n(w['validated']),n(w['overdue']),short(w['delay_reason'] or 'Não informada',90)] for w in waves]
        if not waves:wave_rows.append(['Sem ondas no período','0','0','0','Não informada'])
        comparison=[['Indicador','Período anterior','Período selecionado'],
                    ['Previstos por prazo',n(prior['planned']),n(cur['planned'])],
                    ['Previstos já validados',n(prior['validated_planned']),n(cur['validated_planned'])],
                    ['Aprovações vigentes por data',n(prior['validated']),n(cur['validated'])],
                    ['Implantações declaradas por data',n(prior['declared_deployed']),n(cur['declared_deployed'])]]
        flow.extend([
            p('Resultado do período','title'),
            p(fmt_day(period['from_date'])+' a '+fmt_day(period['to_date'])+' · Comparação com '+fmt_day(period['previous_from'])+' a '+fmt_day(period['previous_to']),'muted'),
            kpis([('PDVs previstos',cur['planned'],'Com prazo no período'),('Previstos validados',cur['validated_planned'],'Orion OK vigente'),('Previstos pendentes',cur['deviation'],'Ainda sem Orion OK')]),
            Spacer(1,10),columns(
                [p('Comparação executiva','h'),table(comparison,[190,87,106],padding=6),
                 Spacer(1,7),p('Variação das aprovações vigentes: '+('+' if period['validated_delta']>0 else '')+str(period['validated_delta'])+' PDV(s).'),
                 p(str(period['declared_without_date'])+' PDV(s) implantado(s) sem data declarada.','muted')],
                [p('Ondas e justificativas','h'),table(wave_rows,[102,64,66,68,157],padding=6),
                 Spacer(1,7),p('Até 3 ondas do período, priorizadas por atraso.','muted'),
                 p(str(period['overdue'])+' PDV(s) atrasado(s) hoje, '+str(period['awaiting_acceptance'])+' aguardando aceite e '+str(period['critical'])+' ocorrência(s) crítica(s).','muted')],
                (383,457)),
            p(period['note'].replace('; não','. Não'),'muted'),PageBreak(),
        ])

    flow += [p('Cobertura e versões','title'),p('Implantação por liderança e distribuição do parque instalado.','muted')]
    versions=[dict(v) for v in b['versions']]
    versions.sort(key=lambda v:(-v['count'],v['name']))
    selected=versions[:6]
    known=sum(v['count'] for v in versions)
    if len(versions)>6:
        count=sum(v['count'] for v in versions[6:]);selected.append({'name':'Demais versões ('+str(len(versions)-6)+')','count':count,'percent':round(count/known*100,1)})
    rows=[['Versão instalada','PDVs','% com versão']]+[[short(v['name'],42),n(v['count']),pct(v['percent'])] for v in selected]
    if not selected:rows.append(['Nenhuma versão registrada','0','0%'])
    version_content=[p('Versões instaladas','h'),table(rows,[159,49,76],padding=5),
                     Spacer(1,7),p('As versões de menor volume são agrupadas. Percentuais entre PDVs com versão registrada.','muted')]
    def grouping(title,groups):
        ranked=sorted(groups,key=lambda r:(-(r['pdvs_expected']-r['pdvs_deployed']),r['name']))
        chosen=ranked[:6]
        if len(ranked)>6:
            rest=ranked[6:];expected=sum(r['stores_expected'] for r in rest);updated=sum(r['stores_updated'] for r in rest)
            chosen.append({'name':'Demais grupos ('+str(len(rest))+')','stores_expected':expected,'stores_updated':updated,'percent':round(updated/expected*100,1) if expected else 0})
        return [p(title,'h'),table([['Grupo','Lojas','Atual.','Avanço']]+[[short(r['name'],28,tail=7),n(r['stores_expected']),n(r['stores_updated']),pct(r['percent'])] for r in chosen or [{'name':'Sem lojas no escopo','stores_expected':0,'stores_updated':0,'percent':0}]],[111,45,53,61],padding=4)]
    group_content=columns(grouping('Avanço por GR',b['by_gr']),grouping('Avanço por regional',b['by_regional']),(270,270))
    flow += [columns(version_content,[group_content],(284,556)),
             p('Até 6 grupos por visão, priorizados por PDVs ainda sem implantação. O avanço mede a proporção de lojas com ao menos um PDV implantado.','muted'),
             p('Orion OK exige todos os processos e os dois aceites GO com responsável e data.','muted'),
             PageBreak(),p('Atenção e atualizações','title'),p('Pendências operacionais e registros salvos recentemente.','muted'),
             kpis([('Ocorrências abertas no escopo',e['open_issues'],str(e['critical_issues'])+(' crítica' if e['critical_issues']==1 else ' críticas')),('PDVs atrasados',e['overdue_pdvs'],'Conforme cronograma'),('Lojas com atenção',e['attention_total'],'Riscos e pendências')]),Spacer(1,10)]
    attention=e['attention'][:4]
    priorities=[['Filial / loja','PDVs','Pontos de atenção']]
    for r in attention:
        pdvs=', '.join(r['pdvs'][:6])+(' +'+str(len(r['pdvs'])-6) if len(r['pdvs'])>6 else '')
        priorities.append([short(r['code']+' - '+r['name'],45),pdvs,str(r['critical'])+' crítica(s), '+str(r['overdue'])+' atraso(s), '+str(r['open_issues'])+' ocorrência(s)'])
    if not attention:priorities.append(['Nenhuma prioridade identificada','-','Não há alertas neste recorte.'])
    recent=[['Filial / PDV','Origem','Situação','Salvo em (Brasília)']]
    for r in data['updates']:
        recent.append([r['code']+(' / '+r['pdv'] if r['pdv'] else ''),r['source'],r['status'],stamp(r['at'])])
    if not data['updates']:recent.append(['Sem registros salvos','-','-','-'])
    flow += [
        columns(
            [p('Prioridades por filial e PDV','h'),table(priorities,[145,105,160],padding=5),
             Spacer(1,7),p('Até 4 lojas priorizadas por criticidade, atraso e ocorrências.','muted')],
            [p('Registros atualizados recentemente','h'),table(recent,[83,99,131,117],padding=5),
             Spacer(1,7),p('Até 5 gravações recentes de cutover, implantação e GR/regional.','muted')],
            (410,430)),
        p('Qualidade da informação','h'),
        p(n(b['stores_missing_organization'])+' loja(s) sem GR ou regional. '+n(b['deployed_without_version'])+' PDV(s) implantado(s) sem versão. '+n(t['exceptions'])+' registro(s) com numeração fora do plano.','muted'),
        p('Fora do escopo: '+n(data['excluded']['inactive'])+' filial(is) inativa(s), '+n(data['excluded']['opening_soon'])+' a inaugurar e '+n(data['excluded']['needs_review'])+' a revisar.','muted'),
    ]
    return build_report(flow,'Relatório executivo','Rollout PDV Orion',
                        'Posição em '+stamp(data['generated_at'])+' (Brasília)')

def download_rollout_executive(core):
    if request.args.get('from') or request.args.get('to'):
        from rollout_management import period_summary
        try:period=period_summary(core,request.args)
        except ValueError as exc:return core['error'](str(exc))
    else:period=None
    data=report_payload(core)
    if period:data['period_summary']=period
    stamp=datetime.fromisoformat(data['generated_at']).astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%Y-%m-%d_%H-%M')
    return send_file(create_rollout_executive_pdf(data),mimetype='application/pdf',as_attachment=True,
                     download_name='Executivo_Rollout_PDV_Orion_'+stamp+'.pdf',max_age=0)
