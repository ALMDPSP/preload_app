import io
from pypdf import PdfReader
from report_organization import organization_rollout
from rollout_executive_report import create_rollout_executive_pdf
from test_rollout_executive_pdf import payload
from test_app import isolated,admin,create


def sample():
    data={'stores':[
        {'id':'a','code':'VD001','name':'Loja A','expected':2,'machines':[{'pdv':'101','ok':True},{'pdv':'102','ok':False}]},
        {'id':'b','code':'VD002','name':'Loja B','expected':1,'machines':[{'pdv':'101','ok':False}]},
        {'id':'c','code':'VD003','name':'Loja C','expected':1,'machines':[{'pdv':'105','ok':False}]},
        {'id':'d','code':'VD004','name':'Loja D','expected':1,'machines':[{'pdv':'101','ok':False}]},
    ]}
    org={'a':{'division':'DIV A','ggr':'GGR A','gr':'GR X'},'b':{'division':'DIV A','ggr':'GGR A','gr':'GR X'},
         'c':{'division':'DIV B','ggr':'GGR B','gr':'GR X'}}
    inventory={('a','101'):{'status':'Implantado'},('a','102'):{'status':'Implantado'},('c','105'):{'status':'Implantado'}}
    return data,(org,inventory)


def test_organization_rollout_unique_stores_pdvs_and_hierarchy():
    data,records=sample()
    result=organization_rollout(data,records)
    assert len(result['groups'])==3
    a=next(row for row in result['groups'] if row['division']=='DIV A')
    assert (a['stores_expected'],a['stores_updated'],a['stores_complete'])==(2,1,0)
    assert (a['pdvs_expected'],a['pdvs_deployed'],a['pdvs_ok'])==(3,2,1)
    assert a['percent']==33.33
    assert len(result['stores'])==2
    assert next(row for row in result['stores'] if row['code']=='VD001')['installed']==['101','102']
    assert any(row['division']=='Sem vínculo' for row in result['groups'])
    assert sum(row['pdvs_deployed'] for row in result['groups'])==3


def test_organization_pdf_names_and_continuation_without_truncation(isolated):
    client=admin(isolated);create(client)
    d=payload()
    data,records=sample();d['organization']=organization_rollout(data,records)
    pdf=PdfReader(create_rollout_executive_pdf(d))
    text=' '.join(page.extract_text() for page in pdf.pages)
    for term in ('Resumo por DIV, GGR e GR','Lojas totalmente viradas','DIV A','GGR A','GR X'):
        assert term in text
    assert len(pdf.pages)==3
    assert all(code not in text for code in ('VD001','VD002','VD003','VD004'))
    rows=[]
    for i in range(100):
        row=dict(d['organization']['groups'][0]);row['gr']='GR RESPONSÁVEL COM NOME EXTENSO '+str(i);rows.append(row)
    d['organization']['groups']=rows
    pdf=PdfReader(create_rollout_executive_pdf(d))
    text=' '.join(page.extract_text() for page in pdf.pages)
    assert len(pdf.pages)>4
    assert all('GR RESPONSÁVEL COM NOME EXTENSO '+str(i) in ' '.join(text.split()) for i in range(100))
    assert 'Lojas com virada registrada' not in text
