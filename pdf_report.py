"""Downloadable report, built only from the version actually saved in the database."""
import re
from reports import summarize
from datetime import datetime
from zoneinfo import ZoneInfo
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak

from pdf_brand import INK, MUTED, BLUE, LINE, BG, WIDTH, build_report, columns, register_fonts

def report_filename(state, version):
    branch=re.sub(r'[^a-zA-Z0-9_-]+','-',state.get('meta',{}).get('branch','execucao')).strip('-')[:80] or 'execucao'
    return f'Checklist_{branch}_v{version}.pdf'

def create_report(source, state, saved):
    register_fonts()
    navy,muted,line,surface=INK,MUTED,LINE,BG
    blue=BLUE
    red=colors.HexColor('#ac263a')
    amber=colors.HexColor('#905f12')
    styles=getSampleStyleSheet()
    styles['Heading4'].fontName='RolloutSans-Bold';styles['Heading4'].fontSize=10;styles['Heading4'].leading=14
    styles['Title'].fontName='RolloutSans-Bold';styles['Title'].fontSize=21;styles['Title'].leading=26;styles['Title'].textColor=navy;styles['Title'].alignment=0
    styles.add(ParagraphStyle(name='BodySmall',fontName='RolloutSans',fontSize=9,leading=13,textColor=navy,spaceAfter=5,splitLongWords=True))
    styles.add(ParagraphStyle(name='SectionHeading',fontName='RolloutSans-Bold',fontSize=12,leading=16,textColor=navy,spaceBefore=11,spaceAfter=6,keepWithNext=True))
    styles.add(ParagraphStyle(name='MutedLine',fontName='RolloutSans',fontSize=8,leading=11,textColor=muted,spaceAfter=5))
    styles.add(ParagraphStyle(name='Kpi',fontName='RolloutSans-Bold',fontSize=21,leading=25,textColor=navy))
    styles.add(ParagraphStyle(name='Badge',fontName='RolloutSans-Bold',fontSize=9,leading=12,textColor=navy))
    def p(value,style='BodySmall'):return Paragraph(escape(str(value if value is not None else '')).replace('\n','<br/>'),styles[style])
    def local(value):
        try:return datetime.fromisoformat(value).astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')
        except (ValueError,TypeError):return str(value or 'Não informado')
    def decision_time(value):
        try:
            dt=datetime.fromisoformat(value)
            if dt.tzinfo:dt=dt.astimezone(ZoneInfo('America/Sao_Paulo'))
            return dt.strftime('%d/%m/%Y %H:%M')
        except (ValueError,TypeError):return str(value or 'Data não informada')
    tasks=state.get('tasks',{});meta=state.get('meta',{});all_tasks=source['orion']+source['linx']
    review=saved.get('rejection');inventory=saved.get('rollout_inventory') or {}
    status,count,blocked=summarize(state,bool(review),[t['id'] for t in all_tasks])
    pending_count=len(all_tasks)-count
    percent=round(count/len(all_tasks)*100) if all_tasks else 0
    status_label='Orion OK' if status=='Concluído' else status.upper() if review else status
    reference=meta.get('branch') or 'Filial não informada'
    phase_groups=[('Preparação do Orion',source['orion'][:3]),('Retirada do Linx',source['linx']),('Instalação e testes do Orion',source['orion'][3:])]

    def table(rows, widths, *rules):
        result=Table(rows,colWidths=widths,hAlign='LEFT')
        result.setStyle(TableStyle([
            ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),
            ('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),6),
            ('BOTTOMPADDING',(0,0),(-1,-1),6),*rules,
        ]))
        return result

    def metric(label,value,caption):
        return [p(label,'MutedLine'),p(value,'Kpi'),p(caption,'MutedLine')]

    def bar(complete,total):
        bar_width=42*mm
        drawing=Drawing(bar_width,9)
        drawing.add(Rect(0,1,bar_width,6,rx=3,ry=3,fillColor=line,strokeColor=None))
        if complete and total:
            drawing.add(Rect(0,1,bar_width*complete/total,6,rx=3,ry=3,fillColor=blue,strokeColor=None))
        return drawing

    elements=[
        p('Resumo do cutover por PDV','Title'),
        p(reference+(('  ·  '+meta['branch_name']) if meta.get('branch_name') else ''),'Badge'),
        Spacer(1,3*mm),
        table([[metric('PDV NOVO · ORION',meta.get('pdv') or '—','Numeração da implantação'),
                metric('PDV ANTIGO · LINX',inventory.get('legacy_pdv') or '—','Numeração de origem'),
                metric('AVANÇO DO CHECKLIST',f'{percent}%',f'{count} de {len(all_tasks)} processos concluídos')]],
              [WIDTH/3]*3,('BACKGROUND',(0,0),(-1,-1),surface),('LINEAFTER',(0,0),(1,0),.6,line)),
        Spacer(1,2*mm),
        table([[p('SITUAÇÃO DO PDV','MutedLine'),p(status_label,'Badge'),p(f'{pending_count} a concluir · {blocked} em bloqueio','Badge')]],
              [185,290,381],('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#fcecf0') if review or blocked else colors.HexColor('#e9f5f1') if status=='Concluído' else surface)),
    ]
    try:date_label=datetime.fromisoformat(meta.get('date','')).strftime('%d/%m/%Y')
    except ValueError:date_label=meta.get('date') or 'Data não informada'
    info=[
        [p('DATA / JANELA','MutedLine'),p(date_label+' · '+(meta.get('window') or 'Janela não informada'))],
        [p('COORDENADOR','MutedLine'),p(meta.get('coordinator') or 'Não informado')],
        [p('IMPLANTAÇÃO','MutedLine'),p((inventory['status']+' · Versão: '+(inventory['installed_version'] or 'Não informada')) if inventory else 'Cadastro não preenchido')],
        [p('REGISTRO SALVO','MutedLine'),p(f"Revisão {saved['version']} · {local(saved['updated_at'])} (Brasília) · {saved['updated_by']}")],
    ]
    compact_rows=(('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
                  ('LINEBELOW',(0,0),(-1,-1),.4,line))
    identity=[p('Identificação da execução','SectionHeading'),table(info,[120,290],*compact_rows)]
    phases=[[p(label,'MutedLine') for label in ['FASE','PROGRESSO','CONCLUÍDOS','PENDENTES']]]
    for title,group in phase_groups:
        complete=sum(tasks.get(t['id'],{}).get('status')=='Concluído' for t in group)
        phases.append([p(title),bar(complete,len(group)),p(f'{complete} / {len(group)}'),p(len(group)-complete)])
    progress=table(phases,[150,139,73,68],*compact_rows,
                   ('BACKGROUND',(0,0),(-1,0),surface),('VALIGN',(0,0),(-1,-1),'MIDDLE'))
    elements.append(columns(identity,[p('Avanço por fase','SectionHeading'),progress],(410,430)))
    elements.append(p('Aceites e próximos passos','SectionHeading'))
    approvals=[]
    for key,label in [('linx','GO da retirada'),('orion','Aceite Orion')]:
        decision=state.get('decisions',{}).get(key,{})
        value=decision.get('value') or 'Pendente'
        owner=decision.get('owner') or 'Responsável não informado'
        approved_color=blue if value=='GO' and decision.get('owner') and decision.get('at') else red if value=='NO-GO' else amber
        caption=Paragraph(escape(value),ParagraphStyle(name='Approval',parent=styles['Badge'],textColor=approved_color))
        approvals.append([p(label,'Badge'),caption,p(owner+' · '+decision_time(decision.get('at')))])
    elements.append(table(approvals,[185,135,536],*compact_rows))
    elements.append(Spacer(1,2*mm))
    retirada=state.get('decisions',{}).get('linx',{})
    retirada_ok=retirada.get('value')=='GO' and all(retirada.get(k) for k in ['owner','at'])
    pending=[t['title'] for t in source['orion'][:3]+source['linx']+source['orion'][3:] if tasks.get(t['id'],{}).get('status')!='Concluído']
    if review:elements.append(p('Próxima ação: solicitar a revisão ou a exclusão a um Administrador ou Operador.','BodySmall'))
    elif all(tasks.get(t['id'],{}).get('status')=='Concluído' for t in source['orion'][:3]+source['linx']) and not retirada_ok:elements.append(p('Próxima ação: conferir e registrar o GO da retirada antes da instalação do Orion.','BodySmall'))
    elif pending:elements.append(p('Próxima ação: '+pending[0]+'.','BodySmall'))
    elif status!='Concluído':elements.append(p('Próxima ação: conferir os aceites e registrar as liberações pendentes.','BodySmall'))
    elements.extend([PageBreak(),p('Checklist detalhado','Title')])
    if review:
        elements.extend([p('Registro da rejeição','SectionHeading'),p(review['actor']+' · '+local(review['created_at']),'MutedLine'),p(review['reason'])])
    for position,(title,group) in enumerate(phase_groups,1):
        elements.append(p(f'{position:02}  {title}','SectionHeading'))
        for t in group:
            record=tasks.get(t['id'],{});status=record.get('status','Pendente');marked='CONCLUÍDO' if status=='Concluído' else status.upper()
            heading=Table([[p(f"{t['number']:02}  {t['title']}",'Heading4'),p(marked)]],colWidths=[666,190])
            heading.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#e9f5f1') if status=='Concluído' else colors.HexColor('#fcecf0') if status=='Bloqueado' else surface),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),4),('LEFTPADDING',(0,0),(-1,-1),8)]))
            block=[heading,p(t['description']),p('Condição de avanço: '+t['gate'],'MutedLine')]
            if record.get('owner'):block.append(p('Responsável: '+record['owner']))
            if record.get('checkedByEmail'):block.append(p('Marcado por: '+record['checkedByEmail']+' | '+local(record.get('checkedAt')),'MutedLine'))
            elements.append(KeepTogether(block))
            if record.get('notes'):elements.append(p('Observações: '+record['notes']))
            if record.get('evidence'):elements.append(p('Evidência registrada: '+record['evidence']))
            if record.get('start') or record.get('duration'):elements.append(p('Início previsto: '+record.get('start','Não informado')+' | Duração: '+record.get('duration','Não informada')+' min','MutedLine'))
            elements.append(Spacer(1,2*mm))
    elements.append(p('Decisões e liberação','SectionHeading'))
    for key,label in [('linx','Entrega do Linx'),('orion','Aceite do Orion')]:
        decision=state.get('decisions',{}).get(key,{})
        block=[p(label+': '+decision.get('value','Pendente'),'Heading4')]
        for k,caption in [('owner','Responsável'),('at','Data / hora informada')]:
            if decision.get(k):block.append(p(caption+': '+(decision_time(decision[k]) if k=='at' else decision[k])))
        elements.append(KeepTogether(block))
        if decision.get('reason'):elements.append(p('Observações: '+decision['reason']))
    for key,caption in [('contacts','Contatos para escalonamento'),('handoff','Passagem para suporte')]:
        if meta.get(key):elements.extend([p(caption,'Heading4'),p(meta[key])])
    elements.append(p('Requisitos de rede - referência','SectionHeading'))
    network=source['network']
    for index in range(0,len(network),2):
        cells=[[p(item['label'],'Heading4'),p(item['value'])] for item in network[index:index+2]]
        elements.append(columns(cells[0],cells[1] if len(cells)==2 else '',(420,420)))
    return build_report(elements,'Checklist de cutover',reference[:72],
                        'Salvo em '+local(saved['updated_at'])+' (Brasília)')
