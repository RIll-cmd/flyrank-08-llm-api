from fastapi.testclient import TestClient
from app import app

def test_triage_is_added_to_existing_task_api(tmp_path,monkeypatch):
    monkeypatch.setenv('TASK_DB',str(tmp_path/'tasks.db'));monkeypatch.setenv('LLM_STUB','1')
    with TestClient(app) as c:
        assert c.get('/health').status_code==200
        assert len(c.get('/tasks').json())==3
        assert c.post('/triage',json={'text':'Question'}).status_code==200
