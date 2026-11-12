import io,copy
from datetime import datetime,timedelta
from pypdf import PdfReader
from test_app import isolated,admin,create,headers,add_user
from test_dashboard import finish
from test_rollout_base import form,put
from rollout_executive_report import report_payload,create_rollout_executive_pdf
import app as module

def payload():
    with module.app.test_request_context('/'):
        return report_payload(vars(module))

def test_pdf_all_saved_rollout_and_cutover_current_data(isolated):
    c=admin(isolated);id=create(c);b=c.get('/api/cutovers/'+id).json['branch_id']
    body=form(c,b);body.update(gr='GR Executivo',regional='SP Centro')
    body['machines'][0].update(status='Implantado',installed_version='Orion 2.0',notes='Não imprimir observações completas')
    assert put(c,b,body).status_code==200
    d=payload()
    assert d['base']['pdvs_expected']==5 and d['base']['pdvs_deployed']==1 and d['base']['pdvs_pending']==4
    assert d['totals']['ok']==0 and d['totals']['pending']==5
    assert any(r['source']=='Base de Rollout' and r['code']=='VD266' for r in d['updates'])
    finish(c,id)
    d=payload();assert d['totals']['ok']==1 and d['base']['pdvs_deployed']==1
    response=c.get('/api/reports/rollout-executive.pdf')
    assert response.status_code==200 and response.mimetype=='application/pdf'
    assert 'attachment;' in response.headers['Content-Disposition']
    assert 'no-store' in response.headers['Cache-Control']
    reader=PdfReader(io.BytesIO(response.data));assert len(reader.pages)==3
    first_page=reader.pages[0].extract_text()
    for label in ('Filiais ativas','PDVs previstos','PDVs implantados','PDVs pendentes',
                  'Lojas atualizadas','Pendências abertas','Avanço do rollout','Prioridade executiva'):
        assert label in first_page
    text='\n'.join(p.extract_text() for p in reader.pages)
    for value in ['Relatório executivo','GR EXECUTIVO','SP CENTRO','Orion 2.0','VD266 / 01','Registros atualizados','PDVs atualmente Orion OK']:
        assert value in text
    assert 'Não imprimir observações completas' not in text
    assert len(response.data)<100000

def test_pdf_read_permissions_empty_and_no_business_writes(isolated):
    c=admin(isolated)
    assert module.app.test_client().get('/api/reports/rollout-executive.pdf').status_code==401
    for role in ['viewer','operator','manager']:
        user,_=add_user(c,'exec-'+role+'@qa.test',role,isolated)
        response=user.get('/api/reports/rollout-executive.pdf')
        assert response.status_code==200
        pdf=PdfReader(io.BytesIO(response.data));assert len(pdf.pages)==3
        text=' '.join(' '.join(p.extract_text() for p in pdf.pages).split())
        assert 'Nenhuma versão registrada' in text and 'Sem registros salvos' in text
    id=create(c);before=c.get('/api/cutovers/'+id).json
    assert c.get('/api/reports/rollout-executive.pdf').status_code==200
    assert c.get('/api/cutovers/'+id).json==before

def test_macro_bounds_large_group_and_version_counts(isolated):
    c=admin(isolated);create(c);d=payload()
    d['base'].update(pdvs_expected=7200,pdvs_deployed=3600,pdvs_pending=3600,pdvs_percent=50,stores_expected=1800,stores_updated=900,stores_percent=50)
    groups=[dict(name='GERENTE REGIONAL COM NOME EXTENSO '+str(i),stores_expected=18,stores_updated=9,percent=50,pdvs_expected=72,pdvs_deployed=36) for i in range(100)]
    d['base']['by_gr']=groups;d['base']['by_regional']=copy.deepcopy(groups)
    d['base']['versions']=[dict(name='Orion-build-'+str(i),count=36,percent=1) for i in range(100)]
    d['executive']['attention_total']=1800
    d['executive']['attention']=[dict(code='L2000',name='FILIAL COM NOME MUITO EXTENSO PARA CONFERENCIA EXECUTIVA',pdvs=[str(n).zfill(2) for n in range(1,51)],critical=3,overdue=4,open_issues=8) for _ in range(10)]
    d['updates']=[dict(code='L2000',pdv='9999',source='Base de Rollout',status='Cadastro atualizado',at=module.now()) for _ in range(5)]
    data=create_rollout_executive_pdf(d).getvalue();pdf=PdfReader(io.BytesIO(data))
    assert len(pdf.pages)==3 and len(data)<100000
    text=' '.join(' '.join(p.extract_text() for p in pdf.pages).split())
    assert text.count('Demais grupos (94)')==2 and 'Demais versões (94)' in text
    assert '7.200' in text and '3.600' in text

def test_trend_counts_only_identified_approvals_in_window(isolated,monkeypatch):
    c=admin(isolated);id=create(c);finish(c,id)
    d=payload();assert sum(r['count'] for r in d['trend'])==1
    from rollout_executive_report import dashboard_data as calculate
    original=calculate(vars(module))
    future=copy.deepcopy(original);future['machines'][0]['date_reference']=True
    monkeypatch.setattr('rollout_executive_report.dashboard_data',lambda core:future)
    assert sum(r['count'] for r in payload()['trend'])==0
