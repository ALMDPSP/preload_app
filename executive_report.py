"""Summary of planned machines, current acceptance and approval dates."""
from datetime import datetime
from zoneinfo import ZoneInfo
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Circle, Drawing, Line, PolyLine, Rect, String
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from pdf_brand import BG, BLUE, INK, LINE, MUTED, WIDTH, build_report, columns, register_fonts


def create_executive_pdf(data):
    register_fonts()
    styles={
        'title':ParagraphStyle('title',fontName='RolloutSans-Bold',fontSize=25,leading=31,textColor=INK,spaceAfter=7),
        'heading':ParagraphStyle('heading',fontName='RolloutSans-Bold',fontSize=14,leading=19,textColor=INK,spaceAfter=8,keepWithNext=True),
        'body':ParagraphStyle('body',fontName='RolloutSans',fontSize=11,leading=15,textColor=INK,spaceAfter=7),
        'muted':ParagraphStyle('muted',fontName='RolloutSans',fontSize=9,leading=13,textColor=MUTED,spaceAfter=6),
        'number':ParagraphStyle('number',fontName='RolloutSans-Bold',fontSize=25,leading=33,textColor=INK),
    }

    def p(value,style='body'):
        return Paragraph(escape(str(value)),styles[style])

    totals=data['totals']
    stamp=datetime.fromisoformat(data['generated_at']).astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
    filters=data.get('filters',{})
    scope='Escopo: filiais ativas e abertas'
    if filters.get('uf'):scope+=' · UF '+filters['uf']
    if filters.get('q'):scope+=' · Busca: '+filters['q']
    items=[('PDVs previstos',totals['expected']),('Virados e Orion OK',totals['ok']),('PDVs pendentes',totals['pending'])]
    metrics=Table([[[p(label,'muted'),p(value,'number')] for label,value in items]],colWidths=[WIDTH/3]*3)
    metrics.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),BG), ('GRID',(0,0),(-1,-1),.5,LINE),
        ('LEFTPADDING',(0,0),(-1,-1),12), ('TOPPADDING',(0,0),(-1,-1),8), ('BOTTOMPADDING',(0,0),(-1,-1),8),
    ]))

    bar=Drawing(290,55)
    ratio=totals['ok']/totals['expected'] if totals['expected'] else 0
    bar.add(Rect(0,34,282,10,fillColor=LINE,strokeColor=None))
    if ratio:bar.add(Rect(0,34,282*ratio,10,fillColor=BLUE,strokeColor=None))
    bar.add(String(0,15,f"Orion OK: {totals['ok']} ({totals['percent']}%)",fontName='RolloutSans-Bold',fontSize=9,fillColor=INK))
    bar.add(String(282,15,f"Pendentes: {totals['pending']}",fontName='RolloutSans',fontSize=9,textAnchor='end',fillColor=MUTED))

    series=data['evolution'];chart=Drawing(550,133)
    left,right,bottom,top=33,535,22,116
    if series:
        maximum=max(1,totals['ok'])
        chart.add(Line(left,bottom,right,bottom,strokeColor=LINE))
        chart.add(Line(left,top,right,top,strokeColor=LINE))
        points=[]
        for i,item in enumerate(series):
            x=left+(right-left)*i/max(1,len(series)-1)
            y=bottom+(top-bottom)*item['cumulative_ok']/maximum
            points.extend([x,y])
        if len(points)>2:chart.add(PolyLine(points,strokeColor=BLUE,strokeWidth=2))
        if len(series)<=20:
            for x,y in zip(points[::2],points[1::2]):
                chart.add(Circle(x,y,2.4,fillColor=BLUE,strokeColor=BLUE))
        for y,value in [(bottom,0),(top,totals['ok'])]:
            chart.add(String(left-5,y-2,str(value),fontName='RolloutSans',fontSize=8,textAnchor='end',fillColor=MUTED))
        chart.add(String(left,6,series[0]['day'],fontName='RolloutSans',fontSize=8,fillColor=MUTED))
        if len(series)>1:
            chart.add(String(right,6,series[-1]['day'],fontName='RolloutSans',fontSize=8,textAnchor='end',fillColor=MUTED))
    else:
        chart.add(String(15,67,'Nenhum PDV Orion OK neste recorte.',fontName='RolloutSans',fontSize=11,fillColor=MUTED))

    flow=[
        p('Evolução do PDV Orion','title'),p(scope,'muted'),metrics,Spacer(1,14),
        columns(
            [p('Execução do parque previsto','heading'),bar,
             p(f"{totals['stores_ok']} de {totals['stores']} lojas completas. {totals['stores_pending']} lojas com PDVs pendentes."),
             p('Uma máquina por filial e número de PDV. Vale a execução mais recente.','muted')],
            [p('Evolução das aprovações vigentes','heading'),chart,
             p('Curva pelas datas de aprovação dos PDVs que estão Orion OK hoje. Mudanças nas execuções ou no escopo podem alterar a curva.','muted')],
            (290,550)),
        Spacer(1,9),p('Critério de OK e pontos de atenção','heading'),
        p('Orion OK exige todos os processos concluídos e ambos os aceites GO com responsável e data.'),
        p(f"Registros fora da meta por numeração a revisar: {totals['exceptions']}. Filiais inativas, a inaugurar ou com vínculo legado pendente ficam fora do recorte.",'muted'),
    ]
    if data['date_references']:
        flow.append(p(f"{data['date_references']} PDV(s) sem data de aprovação identificada usam a última gravação como referência.",'muted'))
    return build_report(flow,'Evolução do PDV Orion','Validação do cutover','Posição em '+stamp+' (Brasília)')
