import json

transcript_path = r'C:\Users\Salomanov\.gemini\antigravity\brain\698fed0a-63fa-48c9-9dbc-8a9b76a7b939\.system_generated\logs\transcript.jsonl'
with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        content = obj.get('content', '')
        if isinstance(content, str):
            low = content.lower()
            if any(w in low for w in ['status.php', 'capabilities', 'адаптир', '2.14', '2.15']):
                print("Step %s: %s\n" % (obj.get('step_index'), content[:250].encode('ascii', 'replace').decode('ascii')))
