"""Executive report containing the cover and rollout overview."""
from datetime import datetime
from zoneinfo import ZoneInfo
from xml.sax.saxutils import escape
from flask import send_file,request
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Spacer,Table,TableStyle
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
      'klabel':ParagraphStyle('rkl',fontName='RolloutSans-Bold',fontSize=9,leading=12,textColor=INK),
      'kvalue':ParagraphStyle('rkv',fontName='RolloutSans-Bold',fontSize=25,leading=33,textColor=INK),
    }
    def p(value,style='body'):
        return Paragraph(escape(str(value)).replace('\n','<br/>'),styles[style])
    def n(value):return f'{value:,}'.replace(',','.')
    def pct(value):return str(value).replace('.',',')+'%'
    def stamp(value):return datetime.fromisoformat(value).astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
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
