"""Shared 16:9 Grupo DPSP artwork for downloadable reports."""
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
ARTWORK=Path(__file__).parent/'static'/'report'


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
        canvas.drawImage(str(ARTWORK/'dpsp-cover.png'),0,0,*PAGE)
        canvas.setFillColor(INK)
        for value,y,font,size in [
            (title,333,'RolloutSans-Bold',39), (subtitle,286,'RolloutSans-Bold',27),
            ('Cutover Online',243,'RolloutSans',17), (position,184,'RolloutSans',13),
        ]:
            width=pdfmetrics.stringWidth(value,font,size)
            canvas.setFont(font,size*min(1,490/max(1,width)))
            canvas.drawString(49,y,value)

    def body(canvas,doc):
        canvas.drawImage(str(ARTWORK/'dpsp-content.png'),0,0,*PAGE)
        canvas.setFont('RolloutSans',8)
        canvas.setFillColor(MUTED)
        canvas.drawString(52,24,'Cutover Online · Expansão de TI')
        canvas.drawRightString(875,24,f'Página {doc.page}')

    doc.build([Spacer(1,1),PageBreak(),*flow],onFirstPage=cover,onLaterPages=body)
    out.seek(0)
    return out
