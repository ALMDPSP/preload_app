"""Downloadable report, built only from the version actually saved in the database."""
import io, re
from pathlib import Path
import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reports import summarize
from release import APP_VERSION
from datetime import datetime
from zoneinfo import ZoneInfo
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak

def report_filename(state, version):
    branch=re.sub(r'[^a-zA-Z0-9_-]+','-',state.get('meta',{}).get('branch','execucao')).strip('-')[:80] or 'execucao'
    return f'Checklist_{branch}_v{version}.pdf'

def create_report(source, state, saved):
    fonts=Path(reportlab.__file__).parent/'fonts'
    if 'RolloutSans' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('RolloutSans',str(fonts/'Vera.ttf')))
        pdfmetrics.registerFont(TTFont('RolloutSans-Bold',str(fonts/'VeraBd.ttf')))
    output=io.BytesIO();doc=SimpleDocTemplate(output,pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=20*mm,bottomMargin=19*mm,title='Checklist de Cutover - Linx para Orion',author='Expansão de TI')
    styles=getSampleStyleSheet()
    styles['Heading4'].fontName='RolloutSans-Bold';styles['Heading4'].fontSize=10;styles['Heading4'].leading=14
    styles['Title'].fontName='RolloutSans-Bold';styles['Title'].fontSize=20;styles['Title'].leading=25;styles['Title'].textColor=colors.HexColor('#28354d')
    styles.add(ParagraphStyle(name='BodySmall',fontName='RolloutSans',fontSize=9,leading=13,textColor=colors.HexColor('#354c6b'),spaceAfter=5,splitLongWords=True))
    styles.add(ParagraphStyle(name='SectionGreen',fontName='RolloutSans-Bold',fontSize=12,leading=16,textColor=colors.HexColor('#31527b'),spaceBefore=16,spaceAfter=10,keepWithNext=True))
    styles.add(ParagraphStyle(name='MutedLine',fontName='RolloutSans',fontSize=8,leading=11,textColor=colors.HexColor('#718198'),spaceAfter=5))
    def p(value,style='BodySmall'):return Paragraph(escape(str(value or '')).replace('\n','<br/>'),styles[style])
    def local(value):
        try:return datetime.fromisoformat(value).astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
        except (ValueError,TypeError):return str(value or 'Não informado')
    def decision_time(value):
        try:
            dt=datetime.fromisoformat(value)
            if dt.tzinfo:dt=dt.astimezone(ZoneInfo('America/Sao_Paulo'))
            return dt.strftime('%d/%m/%Y %H:%M')
        except (ValueError,TypeError):return str(value or 'Data não informada')
    tasks=state.get('tasks',{});meta=state.get('meta',{});all_tasks=source['orion']+source['linx'];count=sum(tasks.get(t['id'],{}).get('status')=='Concluído' for t in all_tasks)
    elements=[p('ALM / EXPANSÃO DE TI','SectionGreen'),p('Resumo do cutover por PDV','Title'),p('Retirada Linx Agiliza e implantação Orion','MutedLine'),Spacer(1,3*mm)]
    info=[['FILIAL / PDV',meta.get('branch','Não informado')],['DATA / JANELA',(meta.get('date') or 'Não informada')+' | '+(meta.get('window') or 'Janela não informada')],['COORDENADOR',meta.get('coordinator') or 'Não informado'],['PROGRESSO',f'{count} de {len(all_tasks)} processos concluídos ({round(count/len(all_tasks)*100)}%)'],['REGISTRO SALVO',f"Versão {saved['version']} | {local(saved['updated_at'])} (Brasília)"],['SALVO POR',saved['updated_by']]]
    inventory=saved.get('rollout_inventory')
    if inventory:info.insert(4,['CADASTRO DE IMPLANTAÇÃO',inventory['status']+' | Versão: '+(inventory['installed_version'] or 'Não informada')])
    if saved.get('rejection'):
        review=saved['rejection']
        info.extend([['SITUAÇÃO','REJEITADO'],['MOTIVO DA REJEIÇÃO',review['reason'] if len(review['reason'])<=250 else review['reason'][:247]+'... (motivo completo no detalhamento)'],['REJEITADO POR',review['actor']+' | '+local(review['created_at'])]])
    if meta.get('branch_name'):info.insert(1,['LOJA',meta['branch_name']])
    status,_,blocked=summarize(state,bool(saved.get('rejection')),[t['id'] for t in all_tasks])
    info.insert(3,['SITUAÇÃO DO PDV','Orion OK' if status=='Concluído' else status])
    table=Table([[p(k,'MutedLine'),p(v)] for k,v in info],colWidths=[37*mm,137*mm],hAlign='LEFT')
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f4f7fb')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),5)]));elements.append(table)
    elements.append(p('Avanço por fase','SectionGreen'))
    phase_rows=[['FASE','CONCLUÍDOS','PENDENTES']]
    for title,group in [('Preparação Orion',source['orion'][:3]),('Retirada Linx',source['linx']),('Implantação e testes Orion',source['orion'][3:])]:
        complete=sum(tasks.get(t['id'],{}).get('status')=='Concluído' for t in group)
        phase_rows.append([title,str(complete)+' / '+str(len(group)),str(len(group)-complete)])
    summary=Table([[p(v,'MutedLine' if i==0 else 'BodySmall') for v in row] for i,row in enumerate(phase_rows)],colWidths=[100*mm,37*mm,37*mm])
    summary.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#edf2f8')),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#dfe6f0')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    elements.append(summary)
    elements.append(p('Aceites e próximos passos','SectionGreen'))
    for key,label in [('linx','GO da retirada'),('orion','Aceite Orion')]:
        decision=state.get('decisions',{}).get(key,{})
        elements.append(p(label+': '+(decision.get('value') or 'Pendente')+' | '+(decision.get('owner') or 'Responsável não informado')+' | '+decision_time(decision.get('at'))))
    elements.append(p(str(len(all_tasks)-count)+' processo(s) não concluído(s); '+str(blocked)+' bloqueado(s). Orion OK exige todos os processos concluídos e os dois aceites GO com responsável e data.','MutedLine'))
    retirada=state.get('decisions',{}).get('linx',{})
    retirada_ok=retirada.get('value')=='GO' and all(retirada.get(k) for k in ['owner','at'])
    pending=[t['title'] for t in source['orion'][:3]+source['linx']+source['orion'][3:] if tasks.get(t['id'],{}).get('status')!='Concluído']
    if saved.get('rejection'):elements.append(p('Próxima ação: solicitar ao Administrador a revisão e a reabertura da execução rejeitada.','BodySmall'))
    elif all(tasks.get(t['id'],{}).get('status')=='Concluído' for t in source['orion'][:3]+source['linx']) and not retirada_ok:elements.append(p('Próxima ação: conferir e registrar o GO da retirada antes da instalação do Orion.','BodySmall'))
    elif pending:elements.append(p('Próxima ação: '+pending[0]+'.','BodySmall'))
    elif status!='Concluído' and not saved.get('rejection'):elements.append(p('Próxima ação: conferir os aceites e registrar as liberações pendentes.','BodySmall'))
    elements.extend([p('As páginas seguintes detalham os processos, observações, decisões e referências do registro salvo.','MutedLine'),PageBreak(),p('Checklist detalhado','Title')])
    if saved.get('rejection'):elements.extend([p('Motivo completo da rejeição','SectionGreen'),p(saved['rejection']['reason'])])
    for title,group in [('01 | Preparação do Orion',source['orion'][:3]),('02 | Retirada do Linx Agiliza',source['linx']),('03 | Instalação, testes e aceite',source['orion'][3:])]:
        elements.append(p(title,'SectionGreen'))
        for t in group:
            record=tasks.get(t['id'],{});status=record.get('status','Pendente');marked='CONCLUÍDO' if status=='Concluído' else status.upper()
            heading=Table([[p(f"{t['number']:02}  {t['title']}",'Heading4'),p(marked)]],colWidths=[128*mm,46*mm])
            heading.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#e4f2e9') if status=='Concluído' else colors.HexColor('#f2f4f3')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),6),('LEFTPADDING',(0,0),(-1,-1),8)]))
            block=[heading,p(t['description']),p('Condição de avanço: '+t['gate'],'MutedLine')]
            if record.get('owner'):block.append(p('Responsável: '+record['owner']))
            if record.get('checkedByEmail'):block.append(p('Marcado por: '+record['checkedByEmail']+' | '+local(record.get('checkedAt')),'MutedLine'))
            elements.append(KeepTogether(block))
            if record.get('notes'):elements.append(p('Observações: '+record['notes']))
            if record.get('evidence'):elements.append(p('Evidência registrada: '+record['evidence']))
            if record.get('start') or record.get('duration'):elements.append(p('Início previsto: '+record.get('start','Não informado')+' | Duração: '+record.get('duration','Não informada')+' min','MutedLine'))
            elements.append(Spacer(1,4*mm))
    elements.append(p('Decisões e liberação','SectionGreen'))
    for key,label in [('linx','Entrega do Linx'),('orion','Aceite do Orion')]:
        decision=state.get('decisions',{}).get(key,{})
        block=[p(label+': '+decision.get('value','Pendente'),'Heading4')]
        for k,caption in [('owner','Responsável'),('at','Data / hora informada')]:
            if decision.get(k):block.append(p(caption+': '+(decision_time(decision[k]) if k=='at' else decision[k])))
        elements.append(KeepTogether(block))
        if decision.get('reason'):elements.append(p('Observações: '+decision['reason']))
    for key,caption in [('contacts','Contatos para escalonamento'),('handoff','Passagem para suporte')]:
        if meta.get(key):elements.extend([p(caption,'Heading4'),p(meta[key])])
    elements.append(p('Requisitos de rede - referência','SectionGreen'))
    for item in source['network']:elements.extend([p(item['label'],'Heading4'),p(item['value'])])
    def footer(canvas,doc):
        canvas.saveState();canvas.setStrokeColor(colors.HexColor('#d6e4da'));canvas.line(18*mm,15*mm,192*mm,15*mm);canvas.setFont('RolloutSans',8);canvas.setFillColor(colors.HexColor('#718198'));canvas.drawString(18*mm,11*mm,'Developed by ALM - Expansão de TI | v'+APP_VERSION);canvas.drawRightString(192*mm,11*mm,f'Página {doc.page}');canvas.restoreState()
    doc.build(elements,onFirstPage=footer,onLaterPages=footer);output.seek(0);return output
