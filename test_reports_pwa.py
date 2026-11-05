from PIL import Image
from test_app import isolated,admin,add_user,headers,create
import app as module
from reports import summarize

def test_report_classification():
    ids=['one','two'];base={'tasks':{},'decisions':{'linx':{},'orion':{}}}
    assert summarize(base,False,ids)==('Pendente',0,0)
    base['tasks']['one']={'status':'Concluído'}
    assert summarize(base,False,ids)[0]=='Em andamento'
    base['tasks']['two']={'status':'Bloqueado'}
    assert summarize(base,False,ids)==('Bloqueado',1,1)
    base['tasks']['two']['status']='Concluído'
    assert summarize(base,False,ids)[0]=='Aguardando aceite'
    base['decisions']={k:{'value':'GO','owner':'QA','at':'2026-11-05T10:00'} for k in ['linx','orion']}
    assert summarize(base,False,ids)[0]=='Concluído'
    assert summarize(base,True,ids)[0]=='Rejeitado'

def test_reports_saved_data_permissions_unstarted(isolated):
    a=admin(isolated);id=create(a)
    a.post('/api/branches',headers=headers(a),json={'code':'NEW99','name':'Nova loja','status':'A inaugurar'})
    assert module.app.test_client().get('/api/reports/cutovers').status_code==401
    for role in ['manager','operator','viewer']:
        c,_=add_user(a,role+'-reports@example.test',role,isolated)
        response=c.get('/api/reports/cutovers');assert response.status_code==200 and len(response.json['rows'])==2
    response=a.get('/api/reports/cutovers').json
    assert {r['status'] for r in response['rows']}=={'Pendente','Sem cutover'}
    assert next(r for r in response['rows'] if r['cutover_id'])['pending']==11
    state=a.get('/api/cutovers/'+id).json['state'];state['tasks']['orion1']={'status':'Concluído'}
    a.put('/api/cutovers/'+id,headers=headers(a),json={'version':1,'state':state})
    row=next(r for r in a.get('/api/reports/cutovers').json['rows'] if r['cutover_id'])
    assert row['completed']==1 and row['pending']==10 and row['status']=='Em andamento'
    a.post('/api/cutovers/'+id+'/reject',headers=headers(a),json={'version':2,'reason':'Falha no teste fiscal'})
    assert next(r for r in a.get('/api/reports/cutovers').json['rows'] if r['cutover_id'])['status']=='Rejeitado'
    a.delete('/api/cutovers/'+id,headers=headers(a),json={'version':3})
    assert all(r['status']=='Sem cutover' for r in a.get('/api/reports/cutovers').json['rows'])

def test_public_install_assets_no_sensitive_offline_cache(isolated):
    c=module.app.test_client();response=c.get('/manifest.webmanifest')
    assert response.status_code==200 and response.mimetype=='application/manifest+json'
    data=response.json;assert data['display']=='standalone' and data['start_url']=='/' and data['scope']=='/'
    for icon in data['icons']:
        assert c.get(icon['src']).status_code==200
        with Image.open(module.ROOT/icon['src'].lstrip('/')) as image:assert f'{image.width}x{image.height}'==icon['sizes']
    worker=c.get('/sw.js');assert worker.status_code==200 and worker.headers['Service-Worker-Allowed']=='/'
    assert 'no-store' in worker.headers['Cache-Control']
    assert 'caches.open' not in worker.text and "event.request.mode!=='navigate'" in worker.text
    login=c.get('/login');assert 'id="installApp"' in login.text and 'rel="manifest"' in login.text
