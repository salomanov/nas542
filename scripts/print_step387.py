import json

transcript_path = r'C:\Users\Salomanov\.gemini\antigravity\brain\698fed0a-63fa-48c9-9dbc-8a9b76a7b939\.system_generated\logs\transcript.jsonl'
with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        if obj.get('step_index') == 387:
            print(obj.get('content')[:1500].encode('ascii', 'replace').decode('ascii'))
