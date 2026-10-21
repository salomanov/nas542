import json

transcript_path = r'C:\Users\Salomanov\.gemini\antigravity\brain\698fed0a-63fa-48c9-9dbc-8a9b76a7b939\.system_generated\logs\transcript.jsonl'
with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        idx = obj.get('step_index')
        if idx in range(390, 410) and obj.get('type') == 'PLANNER_RESPONSE':
            text = obj.get('content')
            if text and len(text) > 100:
                print("=== STEP %s ===" % idx)
                print(text[:800].encode('ascii', 'replace').decode('ascii'))
