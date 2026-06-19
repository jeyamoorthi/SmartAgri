import json
import os
import re

transcript_path = r"C:\Users\Jayamoorthi\.gemini\antigravity\brain\4bdae4fd-959b-412c-a85b-1d81f1181628\.system_generated\logs\transcript.jsonl"

with open(transcript_path, 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        try:
            obj = json.loads(line)
            content = obj.get("content", "")
            step_idx = obj.get("step_index")
            step_type = obj.get("type")
            
            if "File Path:" in content:
                # Extract path
                path_match = re.search(r'File Path:\s*`file:///([^`]+)`', content)
                if path_match:
                    path = path_match.group(1).split('/')[-1]
                    is_truncated = "truncated" in content.lower() or "Showing lines" in content and len(content) < 3000
                    print(f"Step {step_idx} | File: {path} | Content Len: {len(content)} | Is Truncated: {is_truncated}")
        except Exception:
            pass
