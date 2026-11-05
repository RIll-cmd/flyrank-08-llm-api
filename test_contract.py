from fastapi.testclient import TestClient
import app

def test_explicit_stub_overrides_enabled_provider(monkeypatch):
    monkeypatch.setenv('LLM_ENABLED','true'); monkeypatch.setenv('LLM_STUB','1')
    monkeypatch.setattr(app,'call_model',lambda *a,**k: (_ for _ in ()).throw(AssertionError('called')))
    assert TestClient(app.app).post('/triage',json={'text':'test'}).status_code==200

def test_failed_repair_is_quarantined(tmp_path,monkeypatch):
    monkeypatch.setenv('LLM_ENABLED','true'); monkeypatch.setenv('LLM_STUB','0'); monkeypatch.setenv('QUARANTINE_PATH',str(tmp_path/'quarantine.jsonl'))
    monkeypatch.setattr(app,'call_model',lambda *a,**k:'invalid')
    assert TestClient(app.app).post('/triage',json={'text':'test'}).status_code==422
    assert 'prompt_version' in (tmp_path/'quarantine.jsonl').read_text()
