"""Executive report with the rollout dashboard first and bounded detail pages."""
import io
from pathlib import Path
import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from collections import Counter
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from xml.sax.saxutils import escape
from flask import send_file,request
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from reportlab.graphics.shapes import Drawing,Rect,String,Line
from dashboard import dashboard_data
from rollout_base import rollout_base_summary
from operations import operation_overview,today
from executive_dashboard import executive_metrics
from release import APP_VERSION

INK=colors.HexColor('#28354d');MUTED=colors.HexColor('#718198');RED=colors.HexColor('#d51f35')
BLUE=colors.HexColor('#31527b');PALE=colors.HexColor('#a7dce9');GREEN=colors.HexColor('#137961')
LINE=colors.HexColor('#dfe6f0');BG=colors.HexColor('#f4f7fb')
WIDTH=174*mm

def report_payload(core):
    data=dashboard_data(core)
    operations=operation_overview(core,data)
    base=rollout_base_summary(core,data)
    executive=executive_metrics(data,operations,core)
    current=today(core)
    days=Counter()
    for m in data['machines']:
        if m['ok'] and m['approved_at'] and not m['date_reference']:
            day=datetime.fromisoformat(m['approved_at']).astimezone(ZoneInfo('America/Sao_Paulo')).date()
            if current-timedelta(days=13)<=day<=current:days[day.isoformat()]+=1
    trend=[{'day':(current-timedelta(days=13-i)).isoformat(),'count':days[(current-timedelta(days=13-i)).isoformat()]} for i in range(14)]
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
    fonts=Path(reportlab.__file__).parent/'fonts'
    if 'RolloutSans' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('RolloutSans',str(fonts/'Vera.ttf')))
        pdfmetrics.registerFont(TTFont('RolloutSans-Bold',str(fonts/'VeraBd.ttf')))
    out=io.BytesIO()
    doc=SimpleDocTemplate(out,pagesize=A4,leftMargin=18*mm,rightMargin=18*mm,topMargin=27*mm,bottomMargin=19*mm,
                          title='Relatório executivo - Rollout PDV Orion',author='ALM - Expansão de TI')
    styles={
      'title':ParagraphStyle('rt',fontName='RolloutSans-Bold',fontSize=22,leading=27,textColor=INK,spaceAfter=7),
      'h':ParagraphStyle('rh',fontName='RolloutSans-Bold',fontSize=13,leading=18,textColor=INK,spaceBefore=13,spaceAfter=9,keepWithNext=True),
      'body':ParagraphStyle('rb',fontName='RolloutSans',fontSize=9,leading=13,textColor=INK,spaceAfter=6),
      'muted':ParagraphStyle('rm',fontName='RolloutSans',fontSize=8,leading=11.5,textColor=MUTED,spaceAfter=6),
      'cell':ParagraphStyle('rc',fontName='RolloutSans',fontSize=8,leading=11,textColor=INK),
      'th':ParagraphStyle('rth',fontName='RolloutSans-Bold',fontSize=7.5,leading=10,textColor=BLUE),
      'klabel':ParagraphStyle('rkl',fontName='RolloutSans',fontSize=8,leading=11,textColor=MUTED),
      'kvalue':ParagraphStyle('rkv',fontName='RolloutSans-Bold',fontSize=23,leading=30,textColor=INK),
    }
    def p(value,style='body'):
        return Paragraph(escape(str(value)).replace('\n','<br/>'),styles[style])
    def n(value):return f'{value:,}'.replace(',','.')
    def pct(value):return str(value).replace('.',',')+'%'
    def stamp(value):return datetime.fromisoformat(value).astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
    def short(value,maximum=85):
        text=str(value);return text if len(text)<=maximum else text[:maximum-3]+'...'
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
        cells = [[p(label, 'klabel'), p(n(value), 'kvalue'), p(note, 'muted')]
                 for label, value, note, _ in items]
        grid = Table([cells[:3], cells[3:]], colWidths=[WIDTH/3]*3, hAlign='LEFT')
        rules = [
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 3, colors.white),
            ('LEFTPADDING', (0,0), (-1,-1), 13),
            ('TOPPADDING', (0,0), (-1,-1), 11),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]
        for i, (_, _, _, background) in enumerate(items):
            cell = (i % 3, i // 3)
            rules.append(('BACKGROUND', cell, cell, background))
        grid.setStyle(TableStyle(rules))
        return grid

    def rollout_progress(expected, installed, ok, delayed, critical):
        graphic = Drawing(WIDTH, 112)
        dark = colors.HexColor('#24354e')
        light = colors.HexColor('#dce7f6')
        track = colors.HexColor('#52647f')
        graphic.add(Rect(0,0,WIDTH,112,fillColor=dark,strokeColor=None))

        def label(x, y, value, size=8, bold=False, color=light, align='start'):
            graphic.add(String(x,y,str(value),fontName='RolloutSans-Bold' if bold else 'RolloutSans',
                               fontSize=size,fillColor=color,textAnchor=align))

        label(14,91,'Avanço do rollout',11,True,colors.white)
        label(257,91,'Atenção no rollout',11,True,colors.white)
        graphic.add(Line(242,15,242,95,strokeColor=track))
        for y, name, value, color in [(66,'Implantação',installed,PALE),(34,'Orion OK',ok,colors.HexColor('#a3c6fa'))]:
            label(14,y,name)
            unit = ' PDV' if value == 1 else ' PDVs'
            label(228,y,n(value)+unit+' | '+rate(value,expected),8,True,colors.white,'end')
            graphic.add(Rect(14,y-12,214,5,fillColor=track,strokeColor=None))
            ratio = min(1,value/expected) if expected else 0
            if ratio:
                graphic.add(Rect(14,y-12,214*ratio,5,fillColor=color,strokeColor=None))
        risks = [(max(0,installed-ok),'Implantados','sem Orion OK'),
                 (delayed,'PDVs','atrasados'),(critical,'Pendências','críticas')]
        for i,(value, first, second) in enumerate(risks):
            x = 257+i*78
            label(x,56,n(value),17,True,colors.white)
            label(x,37,first)
            label(x,25,second)
        return graphic

    def approval_chart(trend):
        chart = Drawing(WIDTH,106)
        left, right, bottom, top = 32, WIDTH-7, 22, 85
        maximum = max([row['count'] for row in trend]+[1])
        ticks = sorted({0, maximum//2, maximum})
        for value in ticks:
            y = bottom+(top-bottom)*value/maximum
            chart.add(Line(left,y,right,y,strokeColor=LINE))
            chart.add(String(left-5,y-2,n(value),fontName='RolloutSans',fontSize=7,
                             textAnchor='end',fillColor=MUTED))
        for i,row in enumerate(trend):
            width = (right-left)/len(trend)
            x = left+width*i
            height = (top-bottom)*row['count']/maximum
            if height:
                chart.add(Rect(x+5,bottom,width-10,height,fillColor=BLUE,strokeColor=None))
                chart.add(String(x+width/2,bottom+height+4,n(row['count']),fontName='RolloutSans',
                                 fontSize=7,textAnchor='middle',fillColor=BLUE))
            if i%2==0 or i==len(trend)-1:
                day = row['day'][8:10]+'/'+row['day'][5:7]
                chart.add(String(x+width/2,8,day,fontName='RolloutSans',fontSize=7,textAnchor='middle',fillColor=MUTED))
        if not any(row['count'] for row in trend):
            chart.add(String(WIDTH/2,54,'Sem aprovações identificadas no período.',fontName='RolloutSans',
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
        ('Pendências abertas',network['open_issues'],n(network['overdue_issues'])+' com prazo vencido na rede',colors.HexColor('#fcf0f2')),
    ]
    flow = [
        p('Relatório executivo','title'),
        p('Posição em '+stamp(data['generated_at'])+' (Brasília)','muted'),
        headline_cards(cards), Spacer(1,12),
        rollout_progress(b['pdvs_expected'],b['pdvs_deployed'],t['ok'],e['overdue_pdvs'],e['critical_issues']),
        Spacer(1,9),p('Prioridade executiva','h'),p(focus),
        p('PDVs atualmente Orion OK por data de aprovação','h'),
        approval_chart(data['trend']),
        p('Últimos 14 dias. Aprovações vigentes com data identificada no histórico.','muted'),
        p('Lojas com todos os PDVs Orion OK  '+n(t['stores_ok'])+' | Aprovações nos últimos 7 dias  '+n(e['recent_ok']),'body'),
        p('Escopo geral: filiais ativas e abertas com cadastro sem revisão pendente. Implantação inclui declaração na Base ou Orion OK. Pendências abertas incluem ocorrências em tratamento na rede.','muted'),
        PageBreak(),
    ]
    period=data.get('period_summary')
    if period:
        def fmt_day(day):return day.split('-')[2]+'/'+day.split('-')[1]+'/'+day.split('-')[0]
        cur=period['current'];prior=period['previous']
        flow.extend([p('Resultado do período','title'),p(fmt_day(period['from_date'])+' a '+fmt_day(period['to_date'])+' | Comparação com '+fmt_day(period['previous_from'])+' a '+fmt_day(period['previous_to']),'muted'),
                     kpis([('PDVs previstos',cur['planned'],'Com prazo no período'),('Previstos validados',cur['validated_planned'],'Orion OK vigente'),('Previstos pendentes',cur['deviation'],'Ainda sem Orion OK')]),
                     p('Comparação executiva','h'),
                     table([['Indicador','Período anterior','Período selecionado'],['Previstos por prazo',n(prior['planned']),n(cur['planned'])],['Previstos já validados',n(prior['validated_planned']),n(cur['validated_planned'])],['Aprovações vigentes por data',n(prior['validated']),n(cur['validated'])],['Implantações declaradas por data',n(prior['declared_deployed']),n(cur['declared_deployed'])]],[90*mm,42*mm,42*mm]),
                     Spacer(1,10),p('Variação das aprovações vigentes: '+('+' if period['validated_delta']>0 else '')+str(period['validated_delta'])+' PDV(s).','body'),
                     p(str(period['overdue'])+' PDV(s) atrasado(s) hoje; '+str(period['awaiting_acceptance'])+' aguardando aceite; '+str(period['critical'])+' ocorrência(s) crítica(s).','muted'),
                     p('Ondas e justificativas','h')])
        waves=sorted([w for w in period['waves'] if w['start_date']<=period['to_date'] and w['due_date']>=period['from_date']],key=lambda w:(-w['overdue'],w['due_date'],w['name']))[:3]
        flow.append(table([['Onda','Previstos','Validados','Atrasados','Justificativa']]+[[short(w['name'],32),n(w['planned']),n(w['validated']),n(w['overdue']),short(w['delay_reason'] or 'Não informada',90)] for w in waves or [{'name':'Sem ondas cadastradas','planned':0,'validated':0,'overdue':0,'delay_reason':''}]],[49*mm,23*mm,23*mm,23*mm,56*mm]))
        flow.extend([p('Até 3 ondas que cruzam o período selecionado, priorizadas por atraso. Os números das ondas mostram sua posição atual; os indicadores do período incluem todos os planejamentos. '+period['note'],'muted'),p(str(period['declared_without_date'])+' PDV(s) implantado(s) sem data declarada de implantação. Esses registros permanecem no total atual, sem estimar uma data para o comparativo.','muted'),p('O painel da primeira página e os detalhamentos seguintes mostram a posição atual do parque.','muted'),PageBreak()])

    flow += [p('Cobertura e versões','title'),p('Implantação por liderança e distribuição do parque instalado.','muted'),
             p('Versões instaladas','h')]
    versions=[dict(v) for v in b['versions']]
    versions.sort(key=lambda v:(-v['count'],v['name']))
    selected=versions[:6]
    known=sum(v['count'] for v in versions)
    if len(versions)>6:
        count=sum(v['count'] for v in versions[6:]);selected.append({'name':'Demais versões ('+str(len(versions)-6)+')','count':count,'percent':round(count/known*100,1)})
    rows=[['Versão instalada','PDVs','% com versão']]+[[short(v['name'],65),n(v['count']),pct(v['percent'])] for v in selected]
    if not selected:rows.append(['Nenhuma versão registrada','0','0%'])
    flow += [table(rows,[110*mm,28*mm,36*mm]),
             p('A distribuição considera os PDVs com versão registrada. As versões de menor volume são agrupadas.','muted')]
    def grouping(title,groups):
        ranked=sorted(groups,key=lambda r:(-(r['pdvs_expected']-r['pdvs_deployed']),r['name']))
        chosen=ranked[:6]
        if len(ranked)>6:
            rest=ranked[6:];expected=sum(r['stores_expected'] for r in rest);updated=sum(r['stores_updated'] for r in rest)
            chosen.append({'name':'Demais grupos ('+str(len(rest))+')','stores_expected':expected,'stores_updated':updated,'percent':round(updated/expected*100,1) if expected else 0})
        return [p(title,'h'),table([['Grupo','Lojas','Atual.','Avanço']]+[[short(r['name'],38),n(r['stores_expected']),n(r['stores_updated']),pct(r['percent'])] for r in chosen or [{'name':'Sem lojas no escopo','stores_expected':0,'stores_updated':0,'percent':0}]],[36*mm,16*mm,16*mm,16*mm],padding=5)]
    groups=Table([[grouping('Avanço por GR',b['by_gr']),Spacer(6*mm,1),grouping('Avanço por regional',b['by_regional'])]],colWidths=[84*mm,6*mm,84*mm])
    groups.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    flow.append(groups)
    flow += [p('Até 6 grupos por visão, priorizados por PDVs ainda sem implantação. Avanço = lojas com ao menos um PDV implantado / lojas previstas do grupo.','muted'),
             p('Orion OK exige todos os processos e os dois aceites GO com responsável e data.','muted'),
             PageBreak(),p('Atenção e atualizações','title'),p('Pendências operacionais e registros salvos recentemente.','muted'),
             kpis([('Ocorrências abertas no escopo',e['open_issues'],str(e['critical_issues'])+' críticas'),('PDVs atrasados',e['overdue_pdvs'],'Conforme cronograma'),('Lojas com atenção',e['attention_total'],'Riscos e pendências')]),
             p('Prioridades por filial e PDV','h')]
    attention=e['attention'][:4]
    rows=[['Filial / loja','PDVs','Pontos de atenção']]
    for r in attention:
        pdvs=', '.join(r['pdvs'][:6])+(' +'+str(len(r['pdvs'])-6) if len(r['pdvs'])>6 else '')
        rows.append([short(r['code']+' - '+r['name'],45),pdvs,str(r['critical'])+' crítica(s); '+str(r['overdue'])+' atraso(s); '+str(r['open_issues'])+' ocorrência(s)'])
    if not attention:rows.append(['Nenhuma prioridade identificada','-','Não há alertas neste recorte.'])
    flow += [table(rows,[78*mm,30*mm,66*mm]),p('Até 4 lojas priorizadas por criticidade, atraso e ocorrências. Os indicadores acima incluem todas as lojas do escopo.','muted'),
             p('Registros atualizados recentemente','h')]
    rows=[['Filial / PDV','Origem','Situação','Salvo em (Brasília)']]
    for r in data['updates']:
        rows.append([r['code']+(' / '+r['pdv'] if r['pdv'] else ''),r['source'],r['status'],stamp(r['at'])])
    if not data['updates']:rows.append(['Sem registros salvos','-','-','-'])
    flow += [table(rows,[33*mm,38*mm,56*mm,47*mm]),p('Até 5 registros mais recentes entre cutover, implantação e GR/regional. Mostra a última gravação por registro, sem reproduzir o histórico completo de alterações.','muted'),
             p('Critérios e qualidade da informação','h'),
             p(n(b['stores_missing_organization'])+' loja(s) sem GR e/ou regional; '+n(b['deployed_without_version'])+' PDV(s) implantado(s) sem versão. '+n(t['exceptions'])+' registro(s) com numeração fora do plano.','muted'),
             p('Fora do escopo geral: '+n(data['excluded']['inactive'])+' filial(is) inativa(s), '+n(data['excluded']['opening_soon'])+' a inaugurar e '+n(data['excluded']['needs_review'])+' a revisar. Alterações ainda não salvas não entram neste relatório.','muted')]
    def footer(canvas,doc):
        canvas.saveState();canvas.setFillColor(RED);canvas.rect(18*mm,278*mm,9*mm,2*mm,fill=1,stroke=0)
        canvas.setFillColor(INK);canvas.setFont('RolloutSans-Bold',8.5);canvas.drawString(30*mm,278*mm,'ALM / EXPANSÃO DE TI')
        canvas.setFont('RolloutSans',7.5);canvas.setFillColor(MUTED);canvas.drawRightString(192*mm,278*mm,'ROLLOUT PDV ORION')
        canvas.setStrokeColor(LINE);canvas.line(18*mm,14*mm,192*mm,14*mm);canvas.setFont('RolloutSans',7)
        canvas.drawString(18*mm,10*mm,'Developed by ALM - Expansão de TI | v'+APP_VERSION)
        canvas.drawRightString(192*mm,10*mm,'Página '+str(doc.page));canvas.restoreState()
    doc.build(flow,onFirstPage=footer,onLaterPages=footer);out.seek(0);return out

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
