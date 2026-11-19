import copy,json
from test_app import isolated,admin,create,headers
from test_rollout_base import form,put
from test_dashboard import finish
from organization_reference import organization_for,reference
import app as module

def legacy_organization(branch):
    with module.db() as db:
        db.execute("INSERT INTO ct_rollout_organization (branch_id,regional,gr,version,updated_at,updated_by) VALUES (%s,'REGIONAL ANTERIOR','GR ANTERIOR',7,'2026-01-01','historico') ON CONFLICT(branch_id) DO UPDATE SET regional='REGIONAL ANTERIOR',gr='GR ANTERIOR',version=7,updated_at='2026-01-01',updated_by='historico'",(branch,))

def saved_tables():
    with module.db() as db:
        return {table:[dict(row) for row in db.execute('SELECT * FROM '+table+' ORDER BY 1').fetchall()] for table in
                ['ct_branches','ct_cutovers','ct_cutover_branch','ct_rollout_inventory','ct_rollout_organization','ct_branch_pdv_plan','ct_rollout_issues','ct_pdv_assignments']}

def test_reference_and_canonical_store_identity():
    assert len(reference())==2085
    for code in ['VD266','vd0266','266','L2015']:
        org=organization_for(code)
        assert org['ggr']=='CESAR MENDONCA' and org['gr']=='OLIVEIRA JUNIOR'
        assert org['division']=='BRUNA COSTA' and org['organization_matched']
    assert not organization_for('LOJA AUSENTE')['organization_matched']

def test_automatic_reads_preserve_all_saved_business_data(isolated):
    c=admin(isolated);identifier=create(c);finish(c,identifier)
    branch=c.get('/api/cutovers/'+identifier).json['branch_id']
    legacy_organization(branch)
    before=saved_tables()
    base=c.get('/api/rollout-base/branches/'+branch).json
    central=c.get('/api/rollout/branches/'+branch+'/context').json
    assert base['gr']==central['gr']=='OLIVEIRA JUNIOR'
    assert base['ggr']==central['ggr']=='CESAR MENDONCA'
    assert base['division']==central['division']=='BRUNA COSTA'
    assert base['version']==7
    assert c.get('/api/rollout-base?gr=OLIVEIRA%20JUNIOR').json['total']==1
    assert c.get('/api/dashboard?compact=1').json['rollout_base']['by_gr'][0]['name']=='OLIVEIRA JUNIOR'
    assert before==saved_tables()

def test_old_and_modified_forms_cannot_overwrite_store_hierarchy(isolated):
    c=admin(isolated);identifier=create(c);finish(c,identifier)
    branch=c.get('/api/cutovers/'+identifier).json['branch_id'];legacy_organization(branch)
    before=c.get('/api/cutovers/'+identifier).json
    body=form(c,branch)
    body.update(gr='VALOR MANUAL',regional='REGIONAL MANUAL',ggr='MANUAL',division='MANUAL')
    body['machines'][0]['notes']='Observação do PDV preservada'
    assert put(c,branch,body).status_code==200
    current=c.get('/api/rollout-base/branches/'+branch).json
    assert current['gr']=='OLIVEIRA JUNIOR' and current['division']=='BRUNA COSTA'
    assert current['machines'][0]['notes']=='Observação do PDV preservada'
    assert c.get('/api/cutovers/'+identifier).json==before
    with module.db() as db:
        raw=dict(db.execute('SELECT * FROM ct_rollout_organization WHERE branch_id=%s',(branch,)).fetchone())
    assert raw['gr']=='GR ANTERIOR' and raw['regional']=='REGIONAL ANTERIOR'

def test_blank_and_unmatched_reference_preserve_legacy_values(isolated):
    c=admin(isolated)
    for code in ['VD002','L99999']:
        branch=c.post('/api/branches',headers=headers(c),json={'code':code,'name':'Loja anterior'}).json['id']
        legacy_organization(branch)
        result=c.get('/api/rollout-base/branches/'+branch).json
        assert result['gr']=='GR ANTERIOR' and result['regional']=='REGIONAL ANTERIOR'
        assert result['ggr']==result['division']==''
        assert result['organization_matched']==(code=='VD002')

def test_delivery_gr_override_covers_reference_and_legacy():
    for code in ['L1620','L1755','L2180','L2296','L2888']:
        assert organization_for(code)['gr']=='MARCELO POLO'
    assert all(row['gr'].strip().upper()!='DELIVERY' for row in reference().values())
    assert organization_for('LOJA AUSENTE',{'gr':'DELIVERY','regional':'SP'})['gr']=='MARCELO POLO'

def test_deployed_dashboard_rows_include_store_leadership_and_keep_search(isolated):
    c=admin(isolated)
    branch=c.post('/api/branches',headers=headers(c),json={'code':'L1620','name':'Loja Delivery'}).json['id']
    body=form(c,branch);body['machines'][0]['status']='Implantado'
    assert put(c,branch,body).status_code==200
    before=saved_tables()
    result=c.get('/api/dashboard/machines?status=deployed&store_q=L1620').json
    assert result['total']==1
    row=result['rows'][0];expected=organization_for('L1620')
    assert row['gr']=='MARCELO POLO'
    assert row['ggr']==expected['ggr'] and row['division']==expected['division']
    assert row['branch_id']==branch and row['pdv']=='01'
    assert c.get('/api/dashboard/machines?status=deployed&store_q=ausente').json['total']==0
    assert c.get('/api/dashboard/machines?status=undeployed&store_q=L1620').json['total']==4
    assert before==saved_tables()
