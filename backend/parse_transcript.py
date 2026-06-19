import json
import os

transcript_path = r"C:\Users\Jayamoorthi\.gemini\antigravity\brain\4bdae4fd-959b-412c-a85b-1d81f1181628\.system_generated\logs\transcript.jsonl"

views = []
writes = []

with open(transcript_path, 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        try:
            obj = json.loads(line)
            step_idx = obj.get("step_index")
            step_type = obj.get("type")
            content = obj.get("content", "")
            
            # If model made a tool call
            if "tool_calls" in obj:
                for tc in obj["tool_calls"]:
                    name = tc.get("name")
                    args = tc.get("args", {})
                    if name == "view_file":
                        path = args.get("AbsolutePath") or args.get("TargetFile")
                        views.append((step_idx, path))
                    elif name == "write_to_file":
                        path = args.get("TargetFile")
                        code = args.get("CodeContent", "")
                        writes.append((step_idx, path, code))
            
            # If it's a view_file output step
            if step_type == "VIEW_FILE" or (step_type == "DONE" and "Showing lines" in content):
                # This step has the content of the viewed file in the 'content' field!
                # Let's map it to the last view tool call
                print(f"Step {step_idx} contains VIEW_FILE content, size {len(content)} chars. Starts with: {content[:100].strip()}")
                
        except Exception as e:
            pass

print(f"Found {len(views)} view calls and {len(writes)} write calls.")
for v in views:
    print(f"  View at Step {v[0]}: {v[1]}")
for w in writes:
    print(f"  Write at Step {w[0]}: {w[1]} (code len {len(w[2])})")
