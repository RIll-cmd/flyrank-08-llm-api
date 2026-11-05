import json
import os
from pathlib import Path
import requests

cases=json.loads(Path(__file__).with_name('cases.json').read_text(encoding='utf8'))
correct=0;full_correct=0
for case in cases:
    response=requests.post(os.getenv('BASE_URL','http://127.0.0.1:8000').rstrip('/')+'/triage',json={'text':case['text']},timeout=120)
    response.raise_for_status()
    result=response.json();actual=result['category']
    correct+=actual==case['category']
    full=all(result[field]==case[field] for field in ('category','urgency','suggested_team')) and isinstance(result.get('summary'),str) and 1<=len(result['summary'])<=200
    full_correct+=full
    print(f"expected={case['category']} actual={actual} closed_fields={'PASS' if full else 'MISS'}")
print(f'Category accuracy: {correct}/{len(cases)} = {correct/len(cases):.3f}')
print(f'Category/urgency/team plus summary-shape accuracy: {full_correct}/{len(cases)} = {full_correct/len(cases):.3f}')
print('Only report this as a model score when LLM_ENABLED=true and a real model was used.')
