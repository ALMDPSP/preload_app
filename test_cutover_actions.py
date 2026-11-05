import io
from test_app import isolated,admin,add_user,headers,create
import app as module

def test_rejection_permissions_version_freeze_pdf(isolated):
    a=admin(isolated);id=create(a);before=a.get('/api/cutovers/'+id).json
    op,_=add_user(a,'op-review@example.test','operator',isolated)
    manager,_=add_user(a,'manager-review@example.test','manager',isolated)
    viewer,_=add_user(a,'viewer-review@example.test','viewer',isolated)
    data={'version':before['version'],'reason':'Falha nos testes da loja'};url='/api/cutovers/'+id
    for c in [op,viewer]:assert c.post(url+'/reject',headers=headers(c),json=data).status_code==403
    assert a.post(url+'/reject',json=data).status_code==403
    assert a.post(url+'/reject',headers=headers(a),json={**data,'reason':' '}).status_code==400
    assert manager.post(url+'/reject',headers=headers(manager),json={**data,'version':99}).status_code==409
    assert manager.post(url+'/reject',headers=headers(manager),json=data).status_code==200
    after=a.get(url).json
    assert after['rejection']['reason']==data['reason'] and after['rejection']['actor']=='manager-review@example.test'
    assert after['version']==before['version']+1 and after['state']==before['state']
    assert a.get('/api/cutovers').json[0]['rejection_reason']==data['reason']
    assert a.put(url,headers=headers(a),json={'version':after['version'],'state':after['state']}).status_code==409
    assert a.post(url+'/reject',headers=headers(a),json={**data,'version':after['version']}).status_code==409
    from pypdf import PdfReader
    pdf=a.get(url+'/pdf?version='+str(after['version']));assert pdf.status_code==200
    text=' '.join(p.extract_text() for p in PdfReader(io.BytesIO(pdf.data)).pages)
    assert 'REJEITADO' in text and data['reason'] in text
    assert any(r['action']=='rejeição do cutover' for r in a.get(url+'/audit').json)

def test_admin_delete_preserves_branch_audit_and_restart(isolated):
    a=admin(isolated);id=create(a);url='/api/cutovers/'+id;before=a.get(url).json
    manager,_=add_user(a,'del-manager@example.test','manager',isolated)
    assert manager.delete(url,headers=headers(manager),json={'version':before['version']}).status_code==403
    assert a.delete(url,json={'version':before['version']}).status_code==403
    assert a.delete(url,headers=headers(a),json={'version':99}).status_code==409
    assert a.get(url).status_code==200
    assert a.post(url+'/reject',headers=headers(a),json={'version':before['version'],'reason':'Refazer implantação'}).status_code==200
    v=a.get(url).json['version']
    assert a.delete(url,headers=headers(a),json={'version':v}).status_code==200
    assert a.get(url).status_code==404 and a.get(url+'/pdf').status_code==404
    assert len(a.get('/api/branches').json)==1 and a.get('/api/cutovers').json==[]
    with module.db() as c:
        assert c.execute('SELECT cutover_id FROM ct_cutover_reviews WHERE cutover_id=%s',(id,)).fetchone() is None
        assert c.execute('SELECT cutover_id FROM ct_cutover_branch WHERE cutover_id=%s',(id,)).fetchone() is None
        assert c.execute('SELECT id FROM ct_audit WHERE cutover_id=%s AND action=%s',(id,'exclusão do cutover')).fetchone()
    new_id=create(a);assert new_id!=id
    new=a.get('/api/cutovers/'+new_id).json
    assert new['state']['tasks']=={} and new['rejection'] is None and new['branch_id']==before['branch_id']
