import json
import ast

transcript_path = r"C:\Users\Jayamoorthi\.gemini\antigravity\brain\4bdae4fd-959b-412c-a85b-1d81f1181628\.system_generated\logs\transcript.jsonl"

with open(transcript_path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        obj = json.loads(line)
        if obj.get("step_index") == 152:
            tc = obj.get("tool_calls", [])
            for call in tc:
                code = call.get('args', {}).get('CodeContent')
                print("Raw type:", type(code))
                print("Raw starts with double quote:", code.startswith('"'))
                print("Raw ends with double quote:", code.endswith('"'))
                print("Raw length:", len(code))
                
                # Let's test different decoding methods
                try:
                    res_eval = ast.literal_eval(code)
                    print("ast.literal_eval success, len:", len(res_eval))
                except Exception as e:
                    print("ast.literal_eval failed:", e)
                
                # Manual parsing
                if code.startswith('"') and code.endswith('"'):
                    cleaned = code[1:-1].replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                    print("Manual clean length:", len(cleaned))
                    print("Manual clean starts with:", repr(cleaned[:50]))
