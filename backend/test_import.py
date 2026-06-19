import traceback
import sys
import os

try:
    print(f"Current dir: {os.getcwd()}")
    import main
    print("SUCCESS")
    print(main.app.routes)
except Exception:
    traceback.print_exc()
