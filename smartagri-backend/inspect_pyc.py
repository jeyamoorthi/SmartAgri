import marshal
import sys
import types
import os
import re

backend_dir = r"c:\Users\Jayamoorthi\OneDrive\Desktop\azuo\SMARTAGRI\SmartAgri-main\backend"

def safe_print(msg):
    # Encode as ascii and decode to avoid CP1252 crashes
    print(msg.encode('ascii', 'replace').decode('ascii'))

def inspect_pyc(pyc_path):
    if not os.path.exists(pyc_path):
        safe_print(f"File not found: {pyc_path}")
        return
    safe_print(f"\n========================================\nINSPECTING {os.path.basename(pyc_path)}\n========================================")
    with open(pyc_path, 'rb') as f:
        f.read(16)
        try:
            code_obj = marshal.load(f)
            safe_print(f"Names: {code_obj.co_names}")
            safe_print("Code Objects:")
            for i, c in enumerate(code_obj.co_consts):
                if isinstance(c, types.CodeType):
                    safe_print(f"  - <CodeObject {c.co_name}>")
                    safe_print(f"    Names: {c.co_names}")
                    safe_print(f"    Varnames: {c.co_varnames}")
                    safe_print(f"    Constants:")
                    for j, ic in enumerate(c.co_consts):
                        if isinstance(ic, str) and len(ic) > 5:
                            safe_print(f"      [{j}]: {repr(ic[:150])}")
        except Exception as e:
            safe_print(f"Error loading: {e}")

# Find all pyc files in __pycache__
for root, dirs, files in os.walk(backend_dir):
    if "__pycache__" in root:
        for file in files:
            if file.endswith(".pyc"):
                inspect_pyc(os.path.join(root, file))
