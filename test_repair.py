from fastapi.testclient import TestClient
import app as module

def test_one_schema_repair_can_recover_a_bad_model_response(monkeypatch):
    monkeypatch.setenv('LLM_ENABLED','true')
    calls=[]
    def answer(prompt,text,repair=0):
        calls.append(repair)
        return 'bad json' if not repair else '{"category":"billing","urgency":"low","suggested_team":"billing","summary":"Invoice question"}'
    monkeypatch.setattr(module,'call_model',answer)
    response=TestClient(module.app).post('/triage',json={'text':'Question about my invoice'})
    assert response.status_code==200 and response.json()['category']=='billing'
    assert calls==[0,1]
