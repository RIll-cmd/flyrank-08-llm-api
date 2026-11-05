import json
import os
from pathlib import Path
import requests

cases=json.loads(Path(__file__).with_name('cases.json').read_text(encoding='utf8'))
correct=0
for case in cases:
    response=requests.post(os.getenv('BASE_URL','http://127.0.0.1:8000').rstrip('/')+'/triage',json={'text':case['text']},timeout=120)
    response.raise_for_status()
    actual=response.json()['category']
    correct+=actual==case['category']
    print(f"expected={case['category']} actual={actual}")
print(f'Category accuracy: {correct}/{len(cases)} = {correct/len(cases):.3f}')
print('Only report this as a model score when LLM_ENABLED=true and a real model was used.')
