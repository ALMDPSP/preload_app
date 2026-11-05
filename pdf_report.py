"""Downloadable report, built only from the version actually saved in the database."""
import io, re
from datetime import datetime
from zoneinfo import ZoneInfo
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether

def report_filename(state, version):
    branch=re.sub(r'[^a-zA-Z0-9_-]+','-',state.get('meta',{}).get('branch','execucao')).strip('-')[:80] or 'execucao'
    return f'Checklist_{branch}_v{version}.pdf'

def create_report(source, state, saved):
    output=io.BytesIO();doc=SimpleDocTemplate(output,pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=20*mm,bottomMargin=19*mm,title='Checklist de Cutover - Linx para Orion',author='Expansão de TI')
    styles=getSampleStyleSheet()
    styles['Heading4'].fontName='Helvetica-Bold';styles['Heading4'].fontSize=10;styles['Heading4'].leading=14
    styles['Title'].fontName='Helvetica-Bold';styles['Title'].fontSize=20;styles['Title'].leading=25;styles['Title'].textColor=colors.HexColor('#173e34')
    styles.add(ParagraphStyle(name='BodySmall',fontName='Helvetica',fontSize=9,leading=13,textColor=colors.HexColor('#24423e'),spaceAfter=5,splitLongWords=True))
    styles.add(ParagraphStyle(name='SectionGreen',fontName='Helvetica-Bold',fontSize=12,leading=16,textColor=colors.HexColor('#007f70'),spaceBefore=16,spaceAfter=10,keepWithNext=True))
    styles.add(ParagraphStyle(name='MutedLine',fontSize=8,leading=11,textColor=colors.HexColor('#62766e'),spaceAfter=5))
    def p(value,style='BodySmall'):return Paragraph(escape(str(value or '')).replace('\n','<br/>'),styles[style])
    def local(value):
        try:return datetime.fromisoformat(value).astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
        except (ValueError,TypeError):return str(value or 'Não informado')
    tasks=state.get('tasks',{});meta=state.get('meta',{});all_tasks=source['orion']+source['linx'];count=sum(tasks.get(t['id'],{}).get('status')=='Concluído' for t in all_tasks)
    elements=[p('DPSP / EXPANSÃO DE TI','SectionGreen'),p('Checklist de Cutover','Title'),p('Retirada Linx Agiliza e implantação Orion','MutedLine'),Spacer(1,8*mm)]
    info=[['FILIAL / PDV',meta.get('branch','Não informado')],['DATA / JANELA',(meta.get('date') or 'Não informada')+' | '+(meta.get('window') or 'Janela não informada')],['COORDENADOR',meta.get('coordinator') or 'Não informado'],['PROGRESSO',f'{count} de {len(all_tasks)} processos concluídos ({round(count/len(all_tasks)*100)}%)'],['REGISTRO SALVO',f"Versão {saved['version']} | {local(saved['updated_at'])} (Brasília)"],['SALVO POR',saved['updated_by']]]
    if saved.get('rejection'):
        review=saved['rejection']
        info.extend([['SITUAÇÃO','REJEITADO'],['MOTIVO DA REJEIÇÃO',review['reason']],['REJEITADO POR',review['actor']+' | '+local(review['created_at'])]])
    if meta.get('branch_name'):info.insert(1,['LOJA',meta['branch_name']])
    table=Table([[p(k,'MutedLine'),p(v)] for k,v in info],colWidths=[37*mm,137*mm],hAlign='LEFT')
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f0f6f2')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),5)]));elements.append(table)
    for title,group in [('01 | Preparação do Orion',source['orion'][:3]),('02 | Retirada do Linx Agiliza',source['linx']),('03 | Instalação, testes e aceite',source['orion'][3:])]:
        elements.append(p(title,'SectionGreen'))
        for t in group:
            record=tasks.get(t['id'],{});status=record.get('status','Pendente');marked='CONCLUÍDO' if status=='Concluído' else status.upper()
            heading=Table([[p(f"{t['number']:02}  {t['title']}",'Heading4'),p(marked)]],colWidths=[128*mm,46*mm])
            heading.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#e4f2e9') if status=='Concluído' else colors.HexColor('#f2f4f3')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),6),('LEFTPADDING',(0,0),(-1,-1),8)]))
            elements.append(KeepTogether([heading,p(t['description'])]))
            elements.append(p('Condição de avanço: '+t['gate'],'MutedLine'))
            if record.get('owner'):elements.append(p('Responsável: '+record['owner']))
            if record.get('checkedByEmail'):elements.append(p('Marcado por: '+record['checkedByEmail']+' | '+local(record.get('checkedAt')),'MutedLine'))
            if record.get('notes'):elements.append(p('Observações: '+record['notes']))
            if record.get('evidence'):elements.append(p('Evidência registrada: '+record['evidence']))
            if record.get('start') or record.get('duration'):elements.append(p('Início previsto: '+record.get('start','Não informado')+' | Duração: '+record.get('duration','Não informada')+' min','MutedLine'))
            elements.append(Spacer(1,4*mm))
    elements.append(p('Decisões e liberação','SectionGreen'))
    for key,label in [('linx','Entrega do Linx'),('orion','Aceite do Orion')]:
        decision=state.get('decisions',{}).get(key,{})
        elements.append(p(label+': '+decision.get('value','Pendente'),'Heading4'))
        for k,caption in [('owner','Responsável'),('at','Data / hora informada'),('reason','Observações')]:
            if decision.get(k):elements.append(p(caption+': '+decision[k]))
    for key,caption in [('contacts','Contatos para escalonamento'),('handoff','Passagem para suporte')]:
        if meta.get(key):elements.extend([p(caption,'Heading4'),p(meta[key])])
    elements.append(p('Requisitos de rede - referência','SectionGreen'))
    for item in source['network']:elements.extend([p(item['label'],'Heading4'),p(item['value'])])
    def footer(canvas,doc):
        canvas.saveState();canvas.setStrokeColor(colors.HexColor('#d6e4da'));canvas.line(18*mm,15*mm,192*mm,15*mm);canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#62766e'));canvas.drawString(18*mm,11*mm,'Developed by ALM - Expansão de TI');canvas.drawRightString(192*mm,11*mm,f'Página {doc.page}');canvas.restoreState()
    doc.build(elements,onFirstPage=footer,onLaterPages=footer);output.seek(0);return output
