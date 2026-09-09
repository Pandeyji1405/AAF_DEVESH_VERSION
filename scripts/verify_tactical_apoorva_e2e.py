import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import json
from dotenv import load_dotenv

load_dotenv()

from orchestrator import AutonomousITOrchestrator
from core.models import ApprovalStatus

def test_apoorva_ip_config():
    print("=" * 80)
    print("TEST 1: Tactical RMM IP Configuration Query (Apoorva Giri)")
    print("=" * 80)
    
    orch = AutonomousITOrchestrator(use_mock_ae=True)
    res = orch.process_request(
        query_text="Can you fetch my full IP configuration and network adapter details for my device?",
        requester_email="apoorva.giri@enterprise.com",
        approval_decision=ApprovalStatus.APPROVED
    )
    
    ticket = res["ticket"]
    context_graph = res["context_graph"]
    user_resp = res["user_response"]
    
    print(f"ServiceNow Ticket ID : {ticket['ticket_id']}")
    print(f"Assigned Specialist  : {ticket['assigned_agent']}")
    print(f"Intent Category      : {ticket['intent']}")
    print(f"Target Device        : {context_graph.get('facts', {}).get('device_name')}")
    print(f"Tactical Agent ID    : {context_graph.get('facts', {}).get('agent_id')}")
    print(f"Status               : {ticket['status']}")
    print(f"\nUser Output Summary  :\n{user_resp}")
    print("-" * 80)
    
    assert ticket["status"] == "RESOLVED"
    assert "Apoorva" in str(context_graph.get("facts", {}).get("device_name"))
    assert "IP Configuration" in user_resp
    print(">>> TEST 1 PASSED SUCCESSFULLY!\n")

def test_apoorva_high_cpu():
    print("=" * 80)
    print("TEST 2: Tactical RMM High CPU & Process Diagnostics (Apoorva Giri)")
    print("=" * 80)
    
    orch = AutonomousITOrchestrator(use_mock_ae=True)
    res = orch.process_request(
        query_text="Check high CPU usage and top consuming processes on my laptop",
        requester_email="apoorva.giri@enterprise.com",
        approval_decision=ApprovalStatus.APPROVED
    )
    
    ticket = res["ticket"]
    user_resp = res["user_response"]
    
    print(f"ServiceNow Ticket ID : {ticket['ticket_id']}")
    print(f"Status               : {ticket['status']}")
    print(f"\nUser Output Summary  :\n{user_resp}")
    print("-" * 80)
    
    assert ticket["status"] == "RESOLVED"
    assert "CPU" in user_resp
    print(">>> TEST 2 PASSED SUCCESSFULLY!\n")

def test_apoorva_whoami():
    print("=" * 80)
    print("TEST 3: Tactical RMM WhoAmI Execution (RunAsUser verification)")
    print("=" * 80)
    
    orch = AutonomousITOrchestrator(use_mock_ae=True)
    res = orch.process_request(
        query_text="Run whoami on my device to check logged in user context",
        requester_email="apoorva.giri@enterprise.com",
        approval_decision=ApprovalStatus.APPROVED
    )
    
    ticket = res["ticket"]
    user_resp = res["user_response"]
    
    print(f"ServiceNow Ticket ID : {ticket['ticket_id']}")
    print(f"Status               : {ticket['status']}")
    print(f"\nUser Output Summary  :\n{user_resp}")
    print("-" * 80)
    
    assert ticket["status"] == "RESOLVED"
    assert "whoami" in user_resp.lower() or "apoorva" in user_resp.lower()
    print(">>> TEST 3 PASSED SUCCESSFULLY!\n")

def test_apoorva_get_my_pc_configuration():
    print("=" * 80)
    print("TEST 4: 'get my pc configuration' query classification & Tactical RMM execution")
    print("=" * 80)
    
    orch = AutonomousITOrchestrator(use_mock_ae=True)
    res = orch.process_request(
        query_text="get my pc configuration",
        requester_email="apoorva.giri@enterprise.com",
        approval_decision=ApprovalStatus.APPROVED
    )
    
    ticket = res["ticket"]
    context_graph = res["context_graph"]
    user_resp = res["user_response"]
    
    print(f"ServiceNow Ticket ID : {ticket['ticket_id']}")
    print(f"Assigned Specialist  : {ticket['assigned_agent']}")
    print(f"Intent Category      : {ticket['intent']}")
    print(f"Target Device        : {context_graph.get('facts', {}).get('device_name')}")
    print(f"Tactical Agent ID    : {context_graph.get('facts', {}).get('agent_id')}")
    print(f"Status               : {ticket['status']}")
    print(f"\nUser Output Summary  :\n{user_resp}")
    print("-" * 80)
    
    assert ticket["status"] == "RESOLVED"
    assert "MAF_Device_Specialist_Agent" in ticket["assigned_agent"]
    assert "IP Configuration" in user_resp or "Windows IP Configuration" in user_resp
    print(">>> TEST 4 PASSED SUCCESSFULLY!\n")

def test_apoorva_machine_summary():
    print("=" * 80)
    print("TEST 5: 'i want to check my machine summary' (Get_Machine_Summary workflow)")
    print("=" * 80)
    
    orch = AutonomousITOrchestrator(use_mock_ae=True)
    res = orch.process_request(
        query_text="i want to check my machine summary",
        requester_email="apoorva.giri@enterprise.com",
        approval_decision=ApprovalStatus.APPROVED
    )
    
    ticket = res["ticket"]
    context_graph = res["context_graph"]
    user_resp = res["user_response"]
    
    print(f"ServiceNow Ticket ID : {ticket['ticket_id']}")
    print(f"Assigned Specialist  : {ticket['assigned_agent']}")
    print(f"Intent Category      : {ticket['intent']}")
    print(f"Target Device        : {context_graph.get('facts', {}).get('device_name')}")
    print(f"Status               : {ticket['status']}")
    print(f"\nUser Output Summary  :\n{user_resp}")
    print("-" * 80)
    
    assert ticket["status"] == "RESOLVED"
    assert "MAF_Device_Specialist_Agent" in ticket["assigned_agent"]
    assert "Get_Machine_Summary" in user_resp
    assert "Apoorva" in user_resp
    print(">>> TEST 5 PASSED SUCCESSFULLY!\n")

if __name__ == "__main__":
    test_apoorva_ip_config()
    test_apoorva_high_cpu()
    test_apoorva_whoami()
    test_apoorva_get_my_pc_configuration()
    test_apoorva_machine_summary()
    print("ALL TACTICAL RMM END-TO-END TESTS COMPLETED 100% ACCURATELY!")

