import json
import os

transcript_path = r"C:\Users\Jayamoorthi\.gemini\antigravity\brain\4bdae4fd-959b-412c-a85b-1d81f1181628\.system_generated\logs\transcript.jsonl"
base_dir = r"C:\Users\Jayamoorthi\OneDrive\Desktop\azuo\SMARTAGRI\SmartAgri-main\backend"

mapping = {
    144: os.path.join(base_dir, "services", "bhashini_service.py"),
    150: os.path.join(base_dir, "services", "groq_service.py"),
    152: os.path.join(base_dir, "core", "ai_gateway.py"),
    154: os.path.join(base_dir, "services", "bleu_service.py"),
    156: os.path.join(base_dir, "routers", "voice_consultant.py"),
    158: os.path.join(base_dir, "routers", "subsidies.py"),
    170: os.path.join(base_dir, "routers", "voice_consultant.py"),
    176: os.path.join(base_dir, "services", "groq_service.py"),
    177: os.path.join(base_dir, "routers", "natural_farming.py")
}

with open(transcript_path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        try:
            obj = json.loads(line)
            step_idx = obj.get("step_index")
            if step_idx in mapping:
                target_path = mapping[step_idx]
                tc = obj.get("tool_calls", [])
                for call in tc:
                    code = call.get('args', {}).get('CodeContent') or call.get('args', {}).get('ReplacementContent')
                    if code:
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with open(target_path, 'w', encoding='utf-8') as out:
                            out.write(code)
                        print(f"Restored step {step_idx} to {target_path} (len: {len(code)})")
        except Exception as e:
            print(f"Error in step processing: {e}")

