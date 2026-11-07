import gzip,json
from datetime import date
from test_app import isolated,admin,headers,create
from test_dashboard import finish
import app as module
from dashboard import dashboard_data
from executive_dashboard import executive_metrics,selected_data

def test_compact_pagination_and_machine_drilldown_match_saved_totals(isolated):
    c=admin(isolated);id=create(c);finish(c,id)
    with module.db() as db:
        for i in range(55):db.execute('INSERT INTO ct_branches (id,code,name,created_at,uf) VALUES (%s,%s,%s,%s,%s)',('extra'+str(i),'X'+str(i).zfill(3),'QA '+str(i),module.now(),'SP'))
    full=c.get('/api/dashboard').json;compact=c.get('/api/dashboard?compact=1').json
    assert compact['totals']==full['totals'] and compact['compact'] and len(compact['stores'])==25
    assert 'machines' not in compact and compact['pagination']['total']==56
    assert sum(p['count'] for p in compact['executive']['pipeline'])==full['totals']['expected']
    assert sum(r['expected'] for r in compact['executive']['regions'])==full['totals']['expected']
    page2=c.get('/api/dashboard?compact=1&page=2').json;assert len(page2['stores'])==25
    assert not {s['id'] for s in compact['stores']} & {s['id'] for s in page2['stores']}
    assert c.get('/api/dashboard?compact=1&page=999').json['pagination']['page']==3
    pending=c.get('/api/dashboard/machines?status=pending&page=1').json
    assert len(pending['rows'])==40 and pending['total']==full['totals']['pending'] and all(not m['ok'] for m in pending['rows'])
    ok=c.get('/api/dashboard/machines?status=ok').json;assert ok['total']==1 and ok['rows'][0]['pdv']=='01'
    rejected=c.get('/api/dashboard/machines?status=Rejeitado').json;assert rejected['total']==0
    store=c.get('/api/dashboard/store/'+full['stores'][0]['id']).json;assert len(store['machines'])==4
    scoped=c.get('/api/dashboard?compact=1&uf=SP&q=X00').json;assert scoped['totals']['stores']==10 and scoped['totals']['expected']==40
    assert c.get('/api/dashboard/store/absent').status_code==404
    assert module.app.test_client().get('/api/dashboard/machines').status_code==401

def test_approval_cache_avoids_replay_and_invalidates_on_new_version(isolated,monkeypatch):
    import dashboard
    c=admin(isolated);id=create(c);finish(c,id);calls=[];original=dashboard.approval_time
    def replay(*args):calls.append(1);return original(*args)
    monkeypatch.setattr(dashboard,'approval_time',replay)
    dashboard_data(vars(module));assert len(calls)==1
    dashboard_data(vars(module));assert len(calls)==1
    r=c.get('/api/cutovers/'+id).json;r['state']['meta']['coordinator']='Updated contact'
    assert c.put('/api/cutovers/'+id,headers=headers(c),json={'state':r['state'],'version':r['version']}).status_code==200
    dashboard_data(vars(module));assert len(calls)==2
    with module.db() as db:assert db.execute('SELECT version FROM ct_cutover_approval_cache WHERE cutover_id=%s',(id,)).fetchone()['version']==r['version']+1
    assert c.delete('/api/cutovers/'+id,headers=headers(c),json={'version':r['version']+1}).status_code==200
    with module.db() as db:assert db.execute('SELECT * FROM ct_cutover_approval_cache WHERE cutover_id=%s',(id,)).fetchone() is None

def test_one_dashboard_calculation_no_duplicate_snapshot_scan(isolated,monkeypatch):
    import executive_dashboard,operations,dashboard
    c=admin(isolated);create(c);calls=[];original=executive_dashboard.dashboard_data
    def compute(*args,**kwargs):calls.append(1);return original(*args,**kwargs)
    monkeypatch.setattr(executive_dashboard,'dashboard_data',compute)
    monkeypatch.setattr(operations,'dashboard_data',lambda *a,**k:(_ for _ in ()).throw(AssertionError('Snapshot must reuse revision-checked summary')))
    response=c.get('/api/dashboard?compact=1');assert response.status_code==200 and len(calls)==1
    with module.db() as db:assert db.execute('SELECT COUNT(*) AS n FROM ct_rollout_snapshots').fetchone()['n']>=1

def test_transfer_compression_and_asset_cache_do_not_cache_private_data(isolated):
    c=admin(isolated);create(c)
    response=c.get('/api/dashboard?compact=1',headers={'Accept-Encoding':'gzip'})
    assert response.headers['Content-Encoding']=='gzip'
    assert json.loads(gzip.decompress(response.data))['compact']
    assert response.headers['Cache-Control']=='no-store' and 'Accept-Encoding' in response.headers['Vary']
    assert c.get('/api/dashboard?compact=1',headers={'Accept-Encoding':'gzip;q=0'}).headers.get('Content-Encoding') is None
    static=c.get('/static/dashboard.js?v=4.2');assert static.headers['Cache-Control']=='public, max-age=3600'
    assert c.get('/').headers['Cache-Control']=='no-store'

def test_executive_priorities_and_scoped_counts(isolated):
    c=admin(isolated);id=create(c);b=c.get('/api/cutovers/'+id).json['branch_id']
    body={'branch_id':b,'pdv':'01','owner':'QA','due_date':'2020-01-01','start_date':'','notes':'','version':0}
    assert c.put('/api/operations/schedule',headers=headers(c),json=body).status_code==200
    issue={**body,'title':'TEF','priority':'Crítica','status':'Aberta','description':'Rede indisponível','resolution':''}
    assert c.post('/api/operations/issues',headers=headers(c),json=issue).status_code==201
    d=c.get('/api/dashboard?compact=1').json;e=d['executive']
    assert e['overdue_pdvs']==1 and e['critical_issues']==1 and e['attention_total']==1
    assert e['attention'][0]['pdvs']==['01'] and e['attention'][0]['code']=='VD266'
    empty=c.get('/api/dashboard?compact=1&uf=RJ').json
    assert empty['executive']['critical_issues']==0 and empty['executive']['attention']==[] and empty['totals']['expected']==0

def test_request_connection_reused_with_separate_commits_and_closed_on_teardown(isolated,monkeypatch):
    import psycopg
    class Fake:
        closed=False
        def __init__(self):self.commits=0;self.rollbacks=0
        def execute(self,*args):return None
        def commit(self):self.commits+=1
        def rollback(self):self.rollbacks+=1
        def close(self):self.closed=True
    connections=[]
    def connect(*a,**k):c=Fake();connections.append(c);return c
    monkeypatch.setattr(module,'DATABASE','postgresql://qa.invalid/db');monkeypatch.setattr(psycopg,'connect',connect)
    with module.app.test_request_context('/'):
        with module.db():pass
        with module.db():pass
        assert len(connections)==1 and connections[0].commits==2 and not connections[0].closed
    assert connections[0].closed

def test_public_assets_never_open_an_authenticated_database_session(isolated,monkeypatch):
    c=admin(isolated)
    monkeypatch.setattr(module,'db',lambda **kw:(_ for _ in ()).throw(AssertionError('Public assets must not access the database')))
    assert c.get('/static/dashboard.js?v=4.2').status_code==200
    assert c.get('/manifest.webmanifest').status_code==200
    assert c.get('/sw.js').status_code==200
