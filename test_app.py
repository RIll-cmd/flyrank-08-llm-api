from fastapi.testclient import TestClient
from app import app
import app as module
import requests

def test_kill_switch_and_validation(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "false")
    c=TestClient(app)
    assert c.post("/triage",json={"text":""}).status_code==400
    result=c.post("/triage",json={"text":"My bill is wrong"})
    assert result.status_code==200 and result.json()["category"]=="other"

def test_repair_and_invalid_output(monkeypatch):
    monkeypatch.setenv('LLM_ENABLED','true')
    calls=[]
    def model(prompt,text,repair=0):
        calls.append(repair)
        return 'not valid json'
    monkeypatch.setattr(module,'call_model',model)
    response=TestClient(app).post('/triage',json={'text':'test'})
    assert response.status_code==422 and calls==[0,1]
    assert 'not valid json' not in response.text

def test_model_timeout(monkeypatch):
    monkeypatch.setenv('LLM_ENABLED','true')
    def model(*args,**kwargs): raise requests.Timeout()
    monkeypatch.setattr(module,'call_model',model)
    assert TestClient(app).post('/triage',json={'text':'test'}).status_code==504
