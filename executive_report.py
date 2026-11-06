"""Executive PDF: unique planned machines, current acceptance and approval dates."""
import io
from datetime import datetime
from zoneinfo import ZoneInfo
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.graphics.shapes import Drawing,Line,PolyLine,String,Circle,Rect

GREEN=colors.HexColor('#087e67');INK=colors.HexColor('#18363b');MUTED=colors.HexColor('#61776c')

def create_executive_pdf(data):
    out=io.BytesIO();doc=SimpleDocTemplate(out,pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=17*mm,bottomMargin=19*mm,title='Evolução do PDV Orion',author='Expansão de TI')
    styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='ExecutiveTitle',fontName='Helvetica-Bold',fontSize=23,leading=28,textColor=INK,spaceAfter=10));styles.add(ParagraphStyle(name='ExecutiveBody',fontName='Helvetica',fontSize=9,leading=13,textColor=INK,spaceAfter=6));styles.add(ParagraphStyle(name='ExecutiveMuted',fontSize=8,leading=11,textColor=MUTED,spaceAfter=6));styles.add(ParagraphStyle(name='ExecutiveHeading',fontName='Helvetica-Bold',fontSize=13,leading=18,textColor=GREEN,spaceBefore=10,spaceAfter=9,keepWithNext=True))
    def p(value,style='ExecutiveBody'):return Paragraph(escape(str(value or '')).replace('\n','<br/>'),styles[style])
    def table(rows,widths,header=True):
        t=Table([[p(v,'ExecutiveMuted' if i==0 and header else 'ExecutiveBody') for v in row] for i,row in enumerate(rows)],colWidths=widths,repeatRows=1 if header else 0,hAlign='LEFT')
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf4ee')),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#dce7e0')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));return t
    totals=data['totals'];stamp=datetime.fromisoformat(data['generated_at']).astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
    flow=[p('DPSP / EXPANSÃO DE TI','ExecutiveHeading'),p('Evolução do PDV Orion','ExecutiveTitle'),p('Relatório executivo | '+stamp+' (Brasília)','ExecutiveMuted')]
    filters=data.get('filters',{});flow.append(p('Escopo: filiais ativas e abertas'+(' | UF: '+filters['uf'] if filters.get('uf') else '')+(' | Busca: '+filters['q'] if filters.get('q') else ''),'ExecutiveMuted'))
    flow.append(table([['PDVs previstos','Virados e Orion OK','PDVs pendentes'],[str(totals['expected']),str(totals['ok']),str(totals['pending'])]],[58*mm]*3))
    flow.append(Spacer(1,5*mm));flow.append(p(f"Avanço: {totals['percent']}% | {totals['stores_ok']} de {totals['stores']} lojas completas | {totals['stores_pending']} lojas com pendências."))
    flow.append(p('Uma máquina por filial + número de PDV. Padrão de 4 por loja ou plano ajustado. Vale a execução mais recente.','ExecutiveMuted'))
    flow.append(p('Execução do parque previsto','ExecutiveHeading'))
    bar=Drawing(174*mm,25*mm);width=170*mm;ratio=totals['ok']/totals['expected'] if totals['expected'] else 0
    bar.add(Rect(0,34,width,16,fillColor=colors.HexColor('#fae5bb'),strokeColor=None))
    if ratio:bar.add(Rect(0,34,width*ratio,16,fillColor=GREEN,strokeColor=None))
    bar.add(String(0,14,f"Orion OK: {totals['ok']} ({totals['percent']}%)",fontSize=9,fillColor=GREEN))
    bar.add(String(width,14,f"Pendentes: {totals['pending']}",fontSize=9,textAnchor='end',fillColor=colors.HexColor('#916013')))
    flow.append(bar)
    flow.append(p('Evolução das aprovações vigentes','ExecutiveHeading'))
    series=data['evolution'];drawing=Drawing(174*mm,53*mm)
    if series:
        left,right,bottom,top=28,174*mm-15,25,53*mm-12;maximum=max(1,totals['ok']);points=[]
        drawing.add(Line(left,bottom,right,bottom,strokeColor=colors.HexColor('#c9d9cf')));drawing.add(Line(left,bottom,left,top,strokeColor=colors.HexColor('#c9d9cf')))
        for i,item in enumerate(series):
            x=left+(right-left)*i/max(1,len(series)-1);y=bottom+(top-bottom)*item['cumulative_ok']/maximum;points.extend([x,y])
            if len(series)<=20:drawing.add(Circle(x,y,2.2,fillColor=GREEN,strokeColor=GREEN))
        if len(points)>2:drawing.add(PolyLine(points,strokeColor=GREEN,strokeWidth=2))
        drawing.add(String(2,bottom,'0',fontSize=8,fillColor=MUTED));drawing.add(String(2,top-2,str(totals['ok']),fontSize=8,fillColor=MUTED));drawing.add(String(left,6,series[0]['day'],fontSize=8,fillColor=MUTED));drawing.add(String(right,6,series[-1]['day'],textAnchor='end',fontSize=8,fillColor=MUTED))
    else:drawing.add(String(15,60,'Nenhum PDV Orion OK neste recorte.',fontSize=10,fillColor=MUTED))
    flow.append(drawing)
    flow.append(p('Curva por data da aprovação dos PDVs que estão OK hoje. Não é uma fotografia histórica do parque: rejeições, exclusões, troca da última execução ou mudanças de escopo podem alterar o recorte.','ExecutiveMuted'))
    if data['date_references']:flow.append(p(f"{data['date_references']} PDV(s) sem transição de aprovação identificada no histórico usam a data da última gravação como referência, sem afirmar a data real da virada.",'ExecutiveMuted'))
    flow.append(p('Critério de OK e pontos de atenção','ExecutiveHeading'))
    flow.append(p('Orion OK exige os 11 processos concluídos e GO da retirada e da operação, ambos com responsável e data. Sem cutover, em andamento, bloqueado, rejeitado ou aguardando aceite continua pendente.'))
    flow.append(p(f"Registros com numeração a revisar: {totals['exceptions']} (fora da meta). Filiais inativas, a inaugurar ou com vínculo legado pendente ficam fora do recorte. Detalhes por loja/PDV estão na tela e no CSV.",'ExecutiveMuted'))
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor('#d6e4da'));canvas.line(18*mm,14*mm,192*mm,14*mm);canvas.setFont('Helvetica',8);canvas.setFillColor(MUTED);canvas.drawString(18*mm,10*mm,'Developed by ALM - Expansão de TI');canvas.drawRightString(192*mm,10*mm,f'Página {doc.page}')
    doc.build(flow,onFirstPage=footer,onLaterPages=footer);out.seek(0);return out
