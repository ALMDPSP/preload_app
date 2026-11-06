import io
from datetime import datetime,timezone
from pypdf import PdfReader
from test_app import isolated,admin,create
from dashboard import dashboard_data
from executive_report import create_executive_pdf
import app as module

def test_executive_summary_omits_store_and_machine_payload(isolated):
    a=admin(isolated);create(a)
    full=dashboard_data(vars(module));macro=dashboard_data(vars(module),summary_only=True)
    assert macro['totals']==full['totals'] and macro['evolution']==full['evolution']
    assert all(key not in macro for key in ['stores','machines','exceptions'])
    result=a.get('/api/dashboard/executive.pdf')
    assert result.status_code==200 and len(PdfReader(io.BytesIO(result.data)).pages)==1

def test_macro_remains_one_page_without_iterating_1800_stores():
    class DetailMustNotBeRead:
        def __iter__(self):raise AssertionError('Executive report must not read store details')
    d={'generated_at':datetime.now(timezone.utc).isoformat(),'filters':{'q':'','uf':''},'totals':{'expected':7200,'ok':2400,'pending':4800,'percent':33.3,'stores':1800,'stores_ok':600,'stores_pending':1200,'exceptions':0},'evolution':[{'day':'2026-11-05','cumulative_ok':1200,'daily_ok':1200},{'day':'2026-11-06','cumulative_ok':2400,'daily_ok':1200}],'date_references':0,'stores':DetailMustNotBeRead(),'machines':DetailMustNotBeRead(),'exceptions':DetailMustNotBeRead()}
    data=create_executive_pdf(d).getvalue();pdf=PdfReader(io.BytesIO(data))
    assert len(pdf.pages)==1 and len(data)<100000
    text=pdf.pages[0].extract_text()
    assert '7200' in text and '2400' in text and '4800' in text and 'Execução do parque' in text
    assert 'Lojas e números dos PDVs' not in text
