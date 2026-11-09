import io,copy
from pypdf import PdfReader
from test_app import isolated,admin,create,headers,add_user
from test_rollout_base import form,put
import app as module

def test_single_pdv_base_edit_preserves_other_pdvs_and_saved_checklist(isolated):
    c=admin(isolated);id=create(c);cutover=c.get('/api/cutovers/'+id).json;b=cutover['branch_id']
    body=form(c,b);body.update(gr='GR Central',regional='SP Centro')
    body['machines'][1].update(status='Implantado',installed_version='Orion antigo',notes='Manter os dados do PDV 02')
    assert put(c,b,body).status_code==200
    fresh=form(c,b);second=copy.deepcopy(fresh['machines'][1]);first={**fresh['machines'][0],'installed_version':'Orion Central','status':'Implantado'}
    assert put(c,b,{**fresh,'machines':[first]}).status_code==200
    saved=form(c,b)
    assert saved['machines'][1]==second and saved['machines'][0]['installed_version']=='Orion Central'
    assert c.get('/api/cutovers/'+id).json==cutover
    stale={**fresh,'gr':'Não deve salvar','machines':[first]}
    assert put(c,b,stale).status_code==409
    assert form(c,b)['gr']=='GR CENTRAL'
    assert c.get('/api/dashboard?compact=1').json['rollout_base']['pdvs_deployed']==2
    assert c.get('/api/dashboard?compact=1').json['totals']['ok']==0

def test_central_operator_cannot_grant_acceptance_and_pdf_has_pdv_summary(isolated):
    c=admin(isolated);id=create(c);before=c.get('/api/cutovers/'+id).json;b=before['branch_id']
    operator,_=add_user(c,'operator-central@qa.test','operator',isolated)
    body=form(c,b);body['machines'][0]['installed_version']='Orion Central'
    assert put(operator,b,{**body,'machines':[body['machines'][0]]}).status_code==200
    state=copy.deepcopy(before['state']);state['decisions']['linx'].update(value='GO',owner='Operador',at='2026-11-09T10:00')
    for task in module.SOURCE['orion'][:3]+module.SOURCE['linx']:state['tasks'][task['id']]={'status':'Concluído','owner':'Operador'}
    assert operator.put('/api/cutovers/'+id,headers=headers(operator),json={'version':before['version'],'state':state}).status_code==403
    response=c.get('/api/cutovers/'+id+'/pdf');assert response.status_code==200
    pdf=PdfReader(io.BytesIO(response.data));first=' '.join(pdf.pages[0].extract_text().split())
    assert 'Resumo do cutover por PDV' in first and 'VD266 / PDV 01' in first
    assert 'Orion Central' in first
    assert 'Avanço por fase' in first and 'GO da retirada' in first and 'Aceite Orion' in first
    assert 'Próxima ação' in first
    assert any('Checklist detalhado' in page.extract_text() for page in pdf.pages[1:])
