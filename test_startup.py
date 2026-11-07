"""Startup regression checks, using isolated disposable databases."""
import json
import pytest
from test_app import isolated
import app as module


def test_batch_migration_1800_preserves_links_and_existing_branch(isolated):
    with module.db() as c:
        c.execute('INSERT INTO ct_branches (id,code,name,created_at) VALUES (%s,%s,%s,%s)',('existing','L0001','Nome cadastrado',module.now()))
        c.executemany('INSERT INTO ct_cutovers VALUES (%s,%s,%s,%s,%s,%s)',[(f'old-{i}',f'L{i:04d}',json.dumps({'meta':{'branch':f'L{i:04d}'}}),1,module.now(),'qa') for i in range(1800)])
    messages=[];module.init_db(log=messages.append)
    assert any('Vínculos migrados: 1800' in text for text in messages)
    with module.db() as c:
        before=[dict(r) for r in c.execute('SELECT * FROM ct_cutover_branch ORDER BY cutover_id').fetchall()]
        assert len(before)==1800
        assert c.execute('SELECT branch_id FROM ct_cutover_branch WHERE cutover_id=%s',('old-1',)).fetchone()['branch_id']=='existing'
        assert c.execute('SELECT name FROM ct_branches WHERE id=%s',('existing',)).fetchone()['name']=='Nome cadastrado'
    messages=[];module.init_db(log=messages.append)
    assert any('Vínculos migrados: 0' in text for text in messages)
    with module.db() as c:assert before==[dict(r) for r in c.execute('SELECT * FROM ct_cutover_branch ORDER BY cutover_id').fetchall()]


def test_transaction_rollback_keeps_failed_migration_atomic(isolated):
    with pytest.raises(RuntimeError):
        with module.db() as c:
            c.execute('INSERT INTO ct_branches (id,code,name,created_at) VALUES (%s,%s,%s,%s)',('rollback','ZZ01','Teste',module.now()))
            raise RuntimeError('Simulated interruption')
    with module.db() as c:assert c.execute('SELECT id FROM ct_branches WHERE id=%s',('rollback',)).fetchone() is None


def test_postgres_connection_timeouts_and_cleanup(monkeypatch,isolated):
    import psycopg
    class Fake:
        def __init__(self):self.sql=[];self.committed=False;self.closed=False;self.rolled_back=False
        def execute(self,sql,params=()):self.sql.append((sql,params))
        def commit(self):self.committed=True
        def rollback(self):self.rolled_back=True
        def close(self):self.closed=True
    calls=[]
    def connect(uri,**kwargs):
        connection=Fake();calls.append((kwargs,connection));return connection
    monkeypatch.setattr(module,'DATABASE','postgresql://qa.invalid/test')
    monkeypatch.setattr(psycopg,'connect',connect)
    with module.db():pass
    kwargs,normal=calls[-1]
    assert kwargs['connect_timeout']==15 and kwargs['tcp_user_timeout']==20000
    assert normal.sql[0][1]==('45000ms','8000ms')
    assert all(key in normal.sql[0][0] for key in ['statement_timeout','lock_timeout','idle_in_transaction_session_timeout'])
    assert normal.committed and normal.closed
    with pytest.raises(RuntimeError):
        with module.db(healthcheck=True):raise RuntimeError('test')
    kwargs,health=calls[-1]
    assert kwargs['connect_timeout']==2
    assert health.sql[0][1]==('1500ms','1000ms')
    assert health.rolled_back and health.closed
