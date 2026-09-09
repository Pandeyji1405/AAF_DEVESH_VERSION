import sys
import os
import re
import glob
from typing import Set, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from automationedge.workflow_registry import AE_WORKFLOW_REGISTRY

IGNORED_TOKENS = {
    "AE_BASE_URL", "AE_USERNAME", "AE_PASSWORD", "AE_ORG_CODE",
    "AE_EXECUTION_USER", "AE_PROJECT", "AE_TELEMETRY", "AE_WORKFLOW_REGISTRY",
    "AE_UNREGISTERED_WORKFLOW_DELETE_ALL", "AE_REQ", "AE_T4",
    "AE_WORKFLOW_CREATE_INCIDENT", "AE_WORKFLOW_TRMM_CMD", "AE_WORKFLOW_UPDATE_INCIDENT",
    "AE_WORKFLOW_TRMM_MACHINE_SUMMARY", "AE_WORKFLOW_TRMM_AGENTS_LIST",
    "AE_WORKFLOW_TRMM_SOFTWARE_LIST", "AE_WORKFLOW_TRMM_WINDOWS_PATCHES",
    "AE_WORKFLOW_TRMM_SOFTWARE_INSTALL"
}

def find_referenced_workflows(root_dir: str) -> Set[str]:
    pattern = re.compile(r'AE_[A-Za-z0-9_]+')
    referenced = set()
    
    for ext in ["*.py", "*.json", "*.md"]:
        for filepath in glob.glob(os.path.join(root_dir, "**", ext), recursive=True):
            if any(skip in filepath for skip in [".git", "__pycache__", ".pytest_cache", "venv", ".venv"]):
                continue
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    matches = pattern.findall(content)
                    for m in matches:
                        if not m.endswith("_") and m not in IGNORED_TOKENS:
                            referenced.add(m)
            except Exception:
                pass
    return referenced

def verify_workflows(root_dir: Optional[str] = None) -> bool:
    if not root_dir:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    referenced = find_referenced_workflows(root_dir)
    registered = set(AE_WORKFLOW_REGISTRY.keys())
    
    missing_in_registry = referenced - registered
    
    print("="*75)
    print("🔍 AUTOMATIONEDGE WORKFLOW RECONCILIATION PRE-FLIGHT CHECK")
    print("="*75)
    print(f"Total Unique AE Workflows Referenced in Code: {len(referenced)}")
    print(f"Total Workflows Registered in Registry     : {len(registered)}")
    
    if missing_in_registry:
        print(f"\n❌ ERROR: {len(missing_in_registry)} workflows referenced in code are missing from registry:")
        for wf in sorted(missing_in_registry):
            print(f"  • {wf}")
        return False
    
    print("\n✅ All referenced AE workflows are fully cataloged in AE_WORKFLOW_REGISTRY.")
    print("="*75)
    return True

if __name__ == "__main__":
    success = verify_workflows()
    sys.exit(0 if success else 1)
