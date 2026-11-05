from test_app import isolated,admin,add_user,headers,create
from test_branch_import import preview,confirm
import app as module
from branch_values import NAMES,UFS,normalize_uf

def test_upcoming_import_and_registry(isolated):
    a=admin(isolated)
    result=preview(a,'codigo;nome;estado;situacao\nL9999;Nova loja;São Paulo;A inaugurar\nL9998;Loja dois;Rio de Janeiro;Ativa\n'.encode()).json
    assert result['error_count']==0,result
    assert confirm(a,result['import_id']).json['created']==2
    branches=a.get('/api/branches').json
    upcoming=next(x for x in branches if x['code']=='L9999')
    assert upcoming['opening_soon']==1 and upcoming['active']==1 and upcoming['uf']=='SP'
    module.init_db()
    assert next(x for x in a.get('/api/branches').json if x['code']=='L9999')['opening_soon']==1
    updated=preview(a,'codigo;nome;situacao\nL9999;Nova loja;Ativa\n'.encode(),mode='upsert').json
    assert confirm(a,updated['import_id']).json['updated']==1
    assert next(x for x in a.get('/api/branches').json if x['code']=='L9999')['opening_soon']==0
    response=a.post('/api/branches',headers=headers(a),json={'code':'NEW01','name':'Loja futura','status':'A inaugurar'})
    assert response.status_code==201
    id=response.json['id']
    assert a.put('/api/branches/'+id,headers=headers(a),json={'name':'Loja futura','status':'Inativa'}).status_code==200
    assert next(x for x in a.get('/api/branches').json if x['id']==id)['active']==0

def test_delete_admin_only_and_preserve_cutover_history(isolated):
    a=admin(isolated);create(a)
    bound=a.get('/api/branches').json[0]['id']
    assert a.delete('/api/branches/'+bound,headers=headers(a)).status_code==409
    new=a.post('/api/branches',headers=headers(a),json={'code':'NEW02','name':'Loja a excluir','status':'A inaugurar'}).json['id']
    manager,_=add_user(a,'manager@example.test','manager',isolated)
    assert manager.delete('/api/branches/'+new,headers=headers(manager)).status_code==403
    assert a.delete('/api/branches/'+new).status_code==403
    assert a.delete('/api/branches/'+new,headers=headers(a)).status_code==200
    assert a.delete('/api/branches/'+new,headers=headers(a)).status_code==404
    assert len(a.get('/api/branches').json)==1
    with module.db() as c:assert c.execute("SELECT id FROM ct_audit WHERE action=%s",('exclusão de filial',)).fetchone()

def test_all_brazilian_state_names():
    for name,uf in zip(NAMES,UFS):
        assert normalize_uf(name)==uf
        assert normalize_uf(' '+uf.lower()+' ')==uf
