import ast
import os

backend_dir = r"C:\Users\Jayamoorthi\OneDrive\Desktop\azuo\SMARTAGRI\SmartAgri-main\backend"

print("VERIFYING RECOVERED PYTHON FILES:")
for root, dirs, files in os.walk(backend_dir):
    for file in files:
        if file.endswith('.py') and not file in ['recover_from_history.py', 'restore_files.py', 'parse_transcript.py', 'inspect_pyc.py', 'inspect_all_auth.py', 'check_all_recovered.py']:
            path = os.path.join(root, file)
            try:
                content = open(path, 'r', encoding='utf-8').read()
                ast.parse(content)
                print(f"  [OK] {os.path.relpath(path, backend_dir)}: Syntactically Valid (len: {len(content)})")
            except SyntaxError as e:
                msg = str(e).encode('ascii', 'replace').decode('ascii')
                print(f"  [CRITICAL] {os.path.relpath(path, backend_dir)}: Syntax Error: {msg}")
            except Exception as e:
                print(f"  [ERROR] {os.path.relpath(path, backend_dir)}: {e}")
