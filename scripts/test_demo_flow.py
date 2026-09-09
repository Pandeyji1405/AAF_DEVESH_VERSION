import os
import sys
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from demo import run_conversational_flow

if __name__ == "__main__":
    print("Testing conversational flow for 'i want to check my machine summary':")
    run_conversational_flow("i want to check my machine summary", user_email="apoorva.giri@enterprise.com", skip_prompt=True)
