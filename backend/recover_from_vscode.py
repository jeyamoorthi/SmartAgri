import json
import os
import shutil
import urllib.parse

history_dir = os.path.expandvars(r"%APPDATA%\Code\User\History")
workspace_dir = r"c:\users\jayamoorthi\onedrive\desktop\azuo\smartagri"

recovered_count = 0

print("DEBUGGING VS CODE HISTORY SCAN:")
for root, dirs, files in os.walk(history_dir):
    if "entries.json" in files:
        entries_path = os.path.join(root, "entries.json")
        try:
            with open(entries_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                resource = data.get("resource", "")
                if "smartagri" in resource.lower() or "azuo" in resource.lower():
                    print(f"Resource in entries: {resource}")
                    # Decode
                    decoded_path = urllib.parse.unquote(resource[7:])
                    if decoded_path.startswith("/") and decoded_path[2] == ":":
                        decoded_path = decoded_path[1:]
                    decoded_path = decoded_path.replace('/', '\\')
                    print(f"  Decoded: {decoded_path}")
                    
                    entries = data.get("entries", [])
                    if entries:
                        entries.sort(key=lambda x: x.get("timestamp", 0))
                        best_entry = None
                        for entry in reversed(entries):
                            entry_id = entry.get("id")
                            if entry_id:
                                entry_file_path = os.path.join(root, entry_id)
                                if os.path.exists(entry_file_path):
                                    size = os.path.getsize(entry_file_path)
                                    if size > 0:
                                        best_entry = entry
                                        break
                        if best_entry:
                            entry_id = best_entry.get("id")
                            entry_file_path = os.path.join(root, entry_id)
                            target_path = os.path.abspath(decoded_path)
                            os.makedirs(os.path.dirname(target_path), exist_ok=True)
                            shutil.copy2(entry_file_path, target_path)
                            print(f"  --> RESTORED {target_path} ({size} bytes)")
                            recovered_count += 1
        except Exception as e:
            print(f"Error: {e}")

print(f"\nSuccessfully recovered {recovered_count} files!")
