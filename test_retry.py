import requests
import pytest
import app

def test_server_errors_retry_but_unauthorized_errors_do_not(monkeypatch):
    class Response:
        def __init__(self,status): self.status_code=status
        def raise_for_status(self):
            if self.status_code >= 400: raise requests.HTTPError(response=self)
        def json(self): return {'message':{'content':'{}'}}
    calls=[]
    def transient(*args,**kwargs):
        calls.append(1); return Response(503 if len(calls)==1 else 200)
    monkeypatch.setattr(app.time,'sleep',lambda seconds:None)
    monkeypatch.setattr(app.requests,'post',transient)
    assert app.call_model('prompt','text')=='{}' and len(calls)==2
    calls.clear()
    def unauthorized(*args,**kwargs): calls.append(1); return Response(401)
    monkeypatch.setattr(app.requests,'post',unauthorized)
    with pytest.raises(requests.HTTPError): app.call_model('prompt','text')
    assert len(calls)==1
