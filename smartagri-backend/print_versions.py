import json
import os
import re

brain_dir = r"C:\Users\Jayamoorthi\.gemini\antigravity\brain"
target = "voice_consultant.py"

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
                tool_calls = obj.get("tool_calls", [])
                step_idx = obj.get("step_index", i)
                
                for tc in tool_calls:
                    name = tc.get("name")
                    args = tc.get("args", {})
                    path = args.get("TargetFile") or args.get("AbsolutePath")
                    if path and target in path:
                        code = args.get("CodeContent") or ""
                        print(f"Conv {d} | Step {step_idx} | Tool: {name} | Code Len: {len(code)}")
                
                if target in content and "File Path:" in content:
                    is_trunc = "truncated" in content.lower() or (len(content) > 3900 and len(content) < 4200)
                    print(f"Conv {d} | Step {step_idx} | View Content Len: {len(content)} | Is Truncated: {is_trunc}")
            except Exception:
                pass
