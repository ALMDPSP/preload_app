"""Shared vector identity for Cutover online reports."""
import io
from pathlib import Path

import reportlab
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, SimpleDocTemplate, Spacer, Table, TableStyle

INK=HexColor('#2e3345')
MUTED=HexColor('#545d70')
BLUE=HexColor('#3c83f5')
PALE=HexColor('#99e0ff')
LINE=HexColor('#d9deea')
BG=HexColor('#f2f5fa')
PAGE=(960,540)
WIDTH=856


def register_fonts():
    fonts=Path(reportlab.__file__).parent/'fonts'
    if 'RolloutSans' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('RolloutSans',str(fonts/'Vera.ttf')))
        pdfmetrics.registerFont(TTFont('RolloutSans-Bold',str(fonts/'VeraBd.ttf')))


def columns(left,right,widths,gap=16):
    grid=Table([[left,'',right]],colWidths=[widths[0],gap,widths[1]],hAlign='LEFT')
    grid.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
    ]))
    return grid


def build_report(flow,title,subtitle,position):
    out=io.BytesIO()
    doc=SimpleDocTemplate(out,pagesize=PAGE,leftMargin=46,rightMargin=46,topMargin=35,bottomMargin=35,
                          title=title,author='Expansão de TI')

    def cover(canvas,doc):
        canvas.saveState()
        canvas.setFillColor(HexColor('#ffffff'))
        canvas.rect(0,0,*PAGE,stroke=0,fill=1)
        canvas.setFillColor(INK)
        shape=canvas.beginPath()
        shape.moveTo(650,0);shape.lineTo(960,0);shape.lineTo(960,540);shape.lineTo(760,540)
        shape.curveTo(535,390,800,180,650,0)
        canvas.drawPath(shape,stroke=0,fill=1)
        canvas.setFillColor(BLUE)
        canvas.circle(900,450,110,stroke=0,fill=1)
        canvas.setFillColor(PALE)
        canvas.circle(925,80,95,stroke=0,fill=1)
        canvas.setStrokeColor(HexColor('#ffffff'))
        canvas.setLineWidth(1.5)
        canvas.circle(850,255,120,stroke=1,fill=0)
        canvas.setFillColor(INK)
        canvas.setFont('RolloutSans-Bold',23)
        canvas.drawString(49,474,'Cutover')
        canvas.setFillColor(BLUE)
        canvas.setFont('RolloutSans',16)
        canvas.drawString(49,451,'online')
        canvas.restoreState()
        canvas.setFillColor(INK)
        for value,y,font,size in [
            (title,333,'RolloutSans-Bold',39), (subtitle,286,'RolloutSans-Bold',27),
            ('Cutover Online',243,'RolloutSans',17), (position,184,'RolloutSans',13),
        ]:
            width=pdfmetrics.stringWidth(value,font,size)
            canvas.setFont(font,size*min(1,490/max(1,width)))
            canvas.drawString(49,y,value)

    def body(canvas,doc):
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(.6)
        canvas.line(46,526,914,526)
        canvas.line(46,14,914,14)
        canvas.setStrokeColor(BLUE)
        canvas.setLineWidth(3)
        canvas.line(46,526,126,526)
        canvas.setFont('RolloutSans',8)
        canvas.setFillColor(MUTED)
        canvas.drawString(52,24,'Cutover Online · Expansão de TI')
        canvas.drawRightString(875,24,f'Página {doc.page}')

    doc.build([Spacer(1,1),PageBreak(),*flow],onFirstPage=cover,onLaterPages=body)
    out.seek(0)
    return out
