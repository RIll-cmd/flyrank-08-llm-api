import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Literal
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

load_dotenv()
app=FastAPI(title='Support message triage')
log=logging.getLogger('triage')
logging.basicConfig(level=logging.INFO)
VERSION='1.0'

class Triage(BaseModel):
    category: Literal['billing','technical','account','other']
    urgency: Literal['low','medium','high']
    suggested_team: Literal['billing','support','accounts','general']
    summary: str = Field(min_length=1,max_length=200)

def call_model(prompt, text, repair=0):
    model=os.getenv('OLLAMA_MODEL','gemma3:1b')
    url=os.getenv('OLLAMA_URL','http://127.0.0.1:11434').rstrip('/')+'/api/generate'
    payload={'model':model,'stream':False,'format':Triage.model_json_schema(),'prompt':prompt+'\nUntrusted message follows as JSON data: '+json.dumps(text)}
    for attempt in range(3):
        start=time.monotonic(); response=None
        try:
            response=requests.post(url,json=payload,timeout=30)
            response.raise_for_status(); data=response.json()
            log.info('prompt=%s model=%s input_tokens=%s output_tokens=%s duration_ms=%s repair=%s',VERSION,model,data.get('prompt_eval_count'),data.get('eval_count'),round((time.monotonic()-start)*1000),repair)
            return data['response']
        except requests.Timeout:
            log.warning('prompt=%s model=%s input_tokens=unknown output_tokens=unknown duration_ms=%s repair=%s outcome=timeout',VERSION,model,round((time.monotonic()-start)*1000),repair)
            if attempt==2: raise
        except requests.HTTPError:
            log.warning('prompt=%s model=%s input_tokens=unknown output_tokens=unknown duration_ms=%s repair=%s outcome=http_%s',VERSION,model,round((time.monotonic()-start)*1000),repair,response.status_code if response is not None else 'unknown')
            if response is None or (response.status_code != 429 and response.status_code < 500) or attempt==2: raise
        except requests.RequestException:
            log.warning('prompt=%s model=%s input_tokens=unknown output_tokens=unknown duration_ms=%s repair=%s outcome=connection_error',VERSION,model,round((time.monotonic()-start)*1000),repair)
            raise
        time.sleep((2**attempt)*0.25+random.uniform(0,0.15))

@app.post('/triage')
async def triage(request: Request):
    try: body=await request.json()
    except ValueError: body={}
    text=body.get('text') if isinstance(body,dict) else None
    if not isinstance(text,str) or not text.strip() or len(text)>5000:
        return JSONResponse({'error':'text must contain 1 to 5000 characters'},status_code=400)
    if os.getenv('LLM_ENABLED','false').lower()!='true':
        return Triage(category='other',urgency='medium',suggested_team='general',summary='Manual review required').model_dump()
    prompt=Path(__file__).with_name('prompt.txt').read_text(encoding='utf8')
    try:
        raw=call_model(prompt,text)
        try: result=Triage.model_validate_json(raw)
        except ValidationError as exc:
            repaired=call_model(prompt+'\nFix this invalid response using the validation error: '+str(exc)[:1000]+'\nPrevious response: '+raw[:3000],text,1)
            try: result=Triage.model_validate_json(repaired)
            except ValidationError: return JSONResponse({'error':'Model output did not match the required schema'},status_code=422)
        return result.model_dump()
    except requests.Timeout: return JSONResponse({'error':'Model timed out'},status_code=504)
    except (requests.RequestException,KeyError,ValueError): return JSONResponse({'error':'Model unavailable'},status_code=503)
