import json
import os
import re

brain_dir = r"C:\Users\Jayamoorthi\.gemini\antigravity\brain"
target_file = "auth.py"

for d in os.listdir(brain_dir):
    d_path = os.path.join(brain_dir, d)
    if not os.path.isdir(d_path):
        continue
    transcript_path = os.path.join(d_path, ".system_generated", "logs", "transcript.jsonl")
    if not os.path.exists(transcript_path):
        continue
    
    with open(transcript_path, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f):
            try:
                obj = json.loads(line)
                content = obj.get("content", "")
                if target_file in content and "The following code has been modified" in content:
                    print(f"Conversation {d} | Step {obj.get('step_index')} | Length {len(content)}")
                    # Print last 100 chars to see if it is truncated
                    print(f"  ENDS WITH: {repr(content[-200:])}")
            except Exception:
                pass
