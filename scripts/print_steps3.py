import json

transcript_path = r'C:\Users\Salomanov\.gemini\antigravity\brain\698fed0a-63fa-48c9-9dbc-8a9b76a7b939\.system_generated\logs\transcript.jsonl'
with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        idx = obj.get('step_index')
        if idx in [370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380]:
            print("=== STEP %s (%s) ===" % (idx, obj.get('source')))
            content = obj.get('content')
            if content:
                print(content[:500].encode('ascii', 'replace').decode('ascii'))
