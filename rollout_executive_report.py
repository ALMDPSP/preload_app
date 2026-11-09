"""Bounded, three-page executive report; all totals come from saved planned PDVs."""
import io
from pathlib import Path
import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from collections import Counter
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from xml.sax.saxutils import escape
from flask import send_file
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
            'executive':executive,'trend':trend,'updates':updates[:5],'updates_total':len(updates),'date_references':data['date_references']}

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
    def table(rows,widths):
        t=Table([[p(v,'th' if i==0 else 'cell') for v in row] for i,row in enumerate(rows)],colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),BG),
          ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#fafbfd')]),
          ('LINEBELOW',(0,0),(-1,-1),.35,LINE),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
          ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
        return t
    def kpis(items):
        cells=[[p(label,'klabel'),p(n(value),'kvalue'),p(note,'muted')] for label,value,note in items]
        t=Table([cells],colWidths=[WIDTH/len(cells)]*len(cells))
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,-1),BG),
          ('BOX',(0,0),(-1,-1),.5,LINE),('LINEAFTER',(0,0),(-2,-1),.5,colors.white),
          ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),9)]))
        return t
    def progress(expected,done):
        d=Drawing(WIDTH,47)
        ratio=done/expected if expected else 0
        d.add(Rect(0,23,WIDTH,13,fillColor=LINE,strokeColor=None))
        if ratio:d.add(Rect(0,23,WIDTH*ratio,13,fillColor=BLUE,strokeColor=None))
        d.add(String(0,6,'Implantados: '+n(done),fontName='RolloutSans-Bold',fontSize=8,fillColor=BLUE))
        d.add(String(WIDTH,6,'Pendentes: '+n(expected-done),textAnchor='end',fontName='RolloutSans',fontSize=8,fillColor=MUTED))
        return d
    b=data['base'];t=data['totals'];e=data['executive'];flow=[]
    gap=max(0,b['pdvs_deployed']-t['ok'])
    focus=('Resolver '+str(e['critical_issues'])+' ocorrência(s) crítica(s).' if e['critical_issues'] else 'Priorizar '+str(e['overdue_pdvs'])+' PDV(s) atrasado(s).' if e['overdue_pdvs'] else 'Validar os PDVs implantados sem Orion OK.' if gap else 'Avançar a implantação e acompanhar os aceites.')
    flow += [p('Relatório executivo','title'),p('ROLLOUT PDV ORION | Posição consolidada em '+stamp(data['generated_at'])+' (Brasília)','muted'),
             p('Prioridade executiva: '+focus,'body'),p('Visão geral da implantação','h'),p('Todas as filiais ativas e abertas no escopo. Consolidação por filial + número de PDV, usando a última execução salva e o cadastro da Base de Rollout.','muted'),
             kpis([('PDVs previstos',b['pdvs_expected'],'Parque planejado'),('PDVs implantados',b['pdvs_deployed'],pct(b['pdvs_percent'])+' do parque'),('PDVs pendentes',b['pdvs_pending'],'Sem implantação'),('Lojas atualizadas',b['stores_updated'],pct(b['stores_percent'])+' das lojas')]),
             Spacer(1,10),progress(b['pdvs_expected'],b['pdvs_deployed']),
             p(n(b['stores_expected'])+' lojas previstas | '+n(b['stores_updated'])+' com ao menos um PDV implantado.','muted'),
             p('Versões instaladas','h')]
    versions=[dict(v) for v in b['versions']]
    if b['deployed_without_version']:versions.append({'name':'Não informada','count':b['deployed_without_version'],'percent':round(b['deployed_without_version']/b['pdvs_deployed']*100,1) if b['pdvs_deployed'] else 0})
    versions.sort(key=lambda v:(-v['count'],v['name']))
    selected=versions[:6]
    if len(versions)>6:
        count=sum(v['count'] for v in versions[6:]);selected.append({'name':'Demais versões ('+str(len(versions)-6)+')','count':count,'percent':round(count/b['pdvs_deployed']*100,1)})
    rows=[['Versão instalada','PDVs','% implantados']]+[[short(v['name'],65),n(v['count']),pct(v['percent'])] for v in selected]
    if not selected:rows.append(['Nenhuma implantação registrada','0','0%'])
    flow += [table(rows,[110*mm,28*mm,36*mm]),p('Os totais incluem todas as versões; as de menor volume são agrupadas. '+n(b['deployed_without_version'])+' PDV(s) sem versão informada.','muted'),
             p('Validação do cutover','h'),p(n(gap)+' PDV(s) implantado(s) ainda sem Orion OK. Implantação e validação são medidas separadas.','muted'),
             kpis([('Virados e Orion OK',t['ok'],pct(t['percent'])+' do parque'),('Pendentes de validação',t['pending'],'Inclui não iniciados'),('Lojas completas',t['stores_ok'],'Todos os PDVs Orion OK')]),
             Spacer(1,8),p('Implantado = declaração na Base ou Orion OK. Orion OK exige todos os processos e os dois aceites GO com responsável e data. Uma implantação declarada não conclui o cutover.','muted'),
             PageBreak(),p('Cobertura e evolução','title'),p('Acompanhamento por liderança e avanço da validação.','muted')]
    def grouping(title,groups):
        ranked=sorted(groups,key=lambda r:(-(r['pdvs_expected']-r['pdvs_deployed']),r['name']))
        chosen=ranked[:6]
        if len(ranked)>6:
            rest=ranked[6:];expected=sum(r['stores_expected'] for r in rest);updated=sum(r['stores_updated'] for r in rest)
            chosen.append({'name':'Demais grupos ('+str(len(rest))+')','stores_expected':expected,'stores_updated':updated,'percent':round(updated/expected*100,1) if expected else 0})
        return [p(title,'h'),table([['Grupo','Lojas','Atual.','Avanço']]+[[short(r['name'],38),n(r['stores_expected']),n(r['stores_updated']),pct(r['percent'])] for r in chosen or [{'name':'Sem lojas no escopo','stores_expected':0,'stores_updated':0,'percent':0}]],[36*mm,16*mm,16*mm,16*mm])]
    groups=Table([[grouping('Avanço por GR',b['by_gr']),Spacer(6*mm,1),grouping('Avanço por regional',b['by_regional'])]],colWidths=[84*mm,6*mm,84*mm])
    groups.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    flow.append(groups)
    flow += [p('Até 6 grupos por visão, priorizados por PDVs ainda sem implantação; os demais são consolidados. Avanço = lojas com ao menos um PDV implantado / lojas previstas do grupo.','muted'),
             p('PDVs atualmente Orion OK por data de aprovação','h')]
    d=Drawing(WIDTH,112);left=22;right=WIDTH-4;bottom=27;top=95;maximum=max([r['count'] for r in data['trend']]+[1])
    d.add(Line(left,bottom,right,bottom,strokeColor=LINE))
    for i,r in enumerate(data['trend']):
        x=left+(right-left)*i/14;width=(right-left)/14-8;height=(top-bottom)*r['count']/maximum
        if height:d.add(Rect(x+4,bottom,width,height,fillColor=BLUE,strokeColor=None))
        if r['count']:d.add(String(x+4+width/2,bottom+height+4,str(r['count']),fontName='RolloutSans',fontSize=7,textAnchor='middle',fillColor=BLUE))
        if i%2==0 or i==13:d.add(String(x+4+width/2,12,r['day'][8:10]+'/'+r['day'][5:7],fontName='RolloutSans',fontSize=6.5,textAnchor='middle',fillColor=MUTED))
    if not any(r['count'] for r in data['trend']):d.add(String((left+right)/2,62,'Sem aprovações identificadas nos últimos 14 dias.',fontName='RolloutSans',fontSize=9,textAnchor='middle',fillColor=MUTED))
    flow += [d,p('Últimos 14 dias. A curva considera apenas PDVs que continuam Orion OK e possuem aprovação identificada no histórico. Não representa fotografias diárias; datas estimadas não entram.','muted'),
             p('Orion OK nos últimos 7 dias: '+n(e['recent_ok'])+' | Média diária: '+str(e['recent_daily_average']).replace('.',',')+' PDV(s).','body'),
             PageBreak(),p('Atenção e atualizações','title'),p('Pendências operacionais e registros salvos recentemente.','muted'),
             kpis([('Ocorrências abertas',e['open_issues'],str(e['critical_issues'])+' críticas'),('PDVs atrasados',e['overdue_pdvs'],'Conforme cronograma'),('Lojas com atenção',e['attention_total'],'Riscos e pendências')]),
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
    data=report_payload(core)
    stamp=datetime.fromisoformat(data['generated_at']).astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%Y-%m-%d_%H-%M')
    return send_file(create_rollout_executive_pdf(data),mimetype='application/pdf',as_attachment=True,
                     download_name='Executivo_Rollout_PDV_Orion_'+stamp+'.pdf',max_age=0)
