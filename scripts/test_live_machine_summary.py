import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from orchestrator import AutonomousITOrchestrator
from core.models import ApprovalStatus

def main():
    print("================================================================================")
    print("LIVE TEST: 'get my machine summary' against AutomationEdge T4 Server")
    print("================================================================================")
    
    orch = AutonomousITOrchestrator(use_mock_ae=False)
    res = orch.process_request(
        query_text="get my machine summary",
        requester_email="apoorva.giri@enterprise.com",
        approval_decision=ApprovalStatus.APPROVED
    )
    
    ticket = res["ticket"]
    context_graph = res["context_graph"]
    user_resp = res["user_response"]
    
    print("\n--- EXECUTION RESULT ---")
    print(f"ServiceNow Ticket ID : {ticket['ticket_id']}")
    print(f"Assigned Specialist  : {ticket['assigned_agent']}")
    print(f"Intent Category      : {ticket['intent']}")
    dev_fact = context_graph.get('facts', {}).get('device_name')
    dev_name = dev_fact.get('value') if isinstance(dev_fact, dict) else (dev_fact or 'Apoorva')
    print(f"Target Device        : {dev_name}")
    print(f"Status               : {ticket['status']}")
    print(f"\nUser Output Summary  :\n{user_resp}")
    print("================================================================================")

if __name__ == "__main__":
    main()
