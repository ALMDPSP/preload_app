import io, json
from test_app import isolated, admin, add_user, headers, create
import app as module

def preview(c,content,filename='filiais.csv',mode='create_only'):
    return c.post('/api/branches/import/preview',headers=headers(c),data={'mode':mode,'file':(io.BytesIO(content),filename)},content_type='multipart/form-data')

def confirm(c,id):return c.post('/api/branches/import/confirm',headers=headers(c),json={'import_id':id})

def xlsx_bytes(rows):
    # In-memory test input; no spreadsheet deliverable is produced.
    from openpyxl import Workbook
    book=Workbook();sheet=book.active;sheet.title='Filiais'
    for row in rows:sheet.append(row)
    output=io.BytesIO();book.save(output);book.close();return output.getvalue()

def test_excel_1800_rows_preview_then_atomic_confirm_and_idempotency(isolated):
    a=admin(isolated)
    rows=[['Código da filial','Nome da loja','Cidade','UF','Ativo']]+[[f'L{i:05d}',f'Loja {i}','São Paulo','SP','Ativa'] for i in range(1,1801)]
    response=preview(a,xlsx_bytes(rows),'filiais.xlsx');assert response.status_code==200,response.json
    data=response.json;assert data['counts']['new']==1800 and data['total']==1800 and data['error_count']==0
    assert len(data['rows'])==100 and a.get('/api/branches').json==[]
    applied=confirm(a,data['import_id']);assert applied.status_code==200 and applied.json['created']==1800
    all_branches=a.get('/api/branches').json;assert len(all_branches)==1800 and all_branches[0]['code']=='L00001'
    assert confirm(a,data['import_id']).json['already_applied'] is True
    assert len(a.get('/api/branches').json)==1800
    with module.db() as c:
        staged=c.execute('SELECT payload FROM ct_branch_imports WHERE id=%s',(data['import_id'],)).fetchone()
        assert staged['payload']=='[]'

def test_update_preserves_branch_ids_bindings_and_blank_optional_fields(isolated):
    a=admin(isolated);cutover=create(a)
    before=a.get('/api/cutovers/'+cutover).json;branch_id=before['branch_id']
    assert a.put('/api/branches/'+branch_id,headers=headers(a),json={'name':'Nome anterior','city':'São Paulo','uf':'SP','active':False}).status_code==200
    content='codigo;nome;cidade;uf;ativo\nVD266;Nome atualizado;;;\n'.encode('utf-8')
    only_new=preview(a,content).json;assert only_new['counts']['ignored']==1 and only_new['import_id'] is None
    upsert=preview(a,content,mode='upsert').json;assert upsert['counts']['update']==1
    assert confirm(a,upsert['import_id']).json['updated']==1
    after=a.get('/api/cutovers/'+cutover).json
    assert after['branch_id']==branch_id and after['state']==before['state']
    store=next(b for b in a.get('/api/branches').json if b['id']==branch_id)
    assert store['name']=='Nome atualizado' and store['city']=='São Paulo' and store['uf']=='SP' and not store['active']

def test_errors_and_duplicates_block_the_entire_file(isolated):
    a=admin(isolated)
    result=preview(a,'filial;nome;uf\nVD20;Nome;SP\nvd20;Repetida;SP\nVD21;;XX\n'.encode()).json
    assert result['total']==3 and result['error_count']==2 and result['import_id'] is None
    assert a.get('/api/branches').json==[]
    assert preview(a,b'coluna;outra\nABC;Teste').status_code==400
    assert preview(a,b'codigo;nome\n','empty.csv').status_code==400
    assert preview(a,b'not an excel','file.xls').status_code==400
    assert preview(a,xlsx_bytes([['codigo','nome'],['=1+1','Loja']]),'formulas.xlsx').status_code==400
    assert preview(a,b'codigo;nome;ativo\nVD22;Loja;-1').json['error_count']==1

def test_changed_records_abort_without_partial_import(isolated):
    a=admin(isolated)
    staged=preview(a,b'codigo;nome\nVD20;Primeira\nVD21;Segunda\n').json
    assert a.post('/api/branches',headers=headers(a),json={'code':'VD21','name':'Concorrente'}).status_code==201
    assert confirm(a,staged['import_id']).status_code==409
    branches=a.get('/api/branches').json
    assert len(branches)==1 and branches[0]['name']=='Concorrente'

def test_permissions_owner_expiry_encoding_and_template(isolated):
    a=admin(isolated)
    manager,_=add_user(a,'manager-import@example.test','manager',isolated)
    viewer,_=add_user(a,'viewer-import@example.test','viewer',isolated)
    assert preview(viewer,b'codigo;nome\nVD20;Teste').status_code==403
    assert confirm(viewer,'missing').status_code==403
    assert a.post('/api/branches/import/preview',data={'file':(io.BytesIO(b'codigo;nome\nVD20;Teste'),'file.csv')}).status_code==403
    result=preview(manager,'Código;Nome;Cidade;UF\n0012;Farmácia São José;São Paulo;SP\n'.encode('cp1252')).json
    assert result['rows'][0]['code']=='0012'
    assert confirm(a,result['import_id']).status_code==404
    isolated[0]+=1201
    assert confirm(manager,result['import_id']).status_code==409
    assert a.get('/api/branches').json==[]
    template=a.get('/api/branches/import-template')
    assert template.status_code==200 and 'attachment' in template.headers['Content-Disposition'] and 'codigo;nome' in template.text

def test_excel_numeric_zero_format_and_row_limit(isolated):
    from openpyxl import Workbook
    a=admin(isolated);book=Workbook();sheet=book.active;sheet.append(['codigo','nome']);sheet.append([12,'Loja com zeros']);sheet['A2'].number_format='0000'
    output=io.BytesIO();book.save(output);book.close()
    result=preview(a,output.getvalue(),'zero.xlsx').json
    assert result['rows'][0]['code']=='0012'
    too_many=('codigo;nome\n'+''.join(f'VD{i:05d};Loja\n' for i in range(10001))).encode()
    assert preview(a,too_many).status_code==400
