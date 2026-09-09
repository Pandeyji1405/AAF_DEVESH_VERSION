from typing import Optional, Dict, Any
from agent_framework import Agent
from core.models import IncidentTicket, ApprovalStatus, RiskTier
from core.context_graph import ContextGraph
from core.base_agent import BaseAgent

from maf_agents.tools.ops_tools import create_ops_tools
from maf_agents.tools.itsm_tools import create_itsm_tools
from maf_agents.client_factory import get_maf_chat_client

class MAFSecOpsAgent(BaseAgent):
    """
    Microsoft Agent Framework (MAF): Security Operations (SecOps) Specialist Agent.
    Handles high-priority security containment, endpoint isolation, forensic triage, and SIEM logging.
    """

    def __init__(self, ae_client, policy_engine, hitl_manager):
        super().__init__("MAF_SecOps_Agent", ae_client, policy_engine, hitl_manager)
        self.ops_tools = {t.name: t for t in create_ops_tools(ae_client)}
        self.snow_tools = {t.name: t for t in create_itsm_tools(ae_client)}
        self.itsm_tools = self.snow_tools

        self.maf_agent = Agent(
            client=get_maf_chat_client(),
            name="MAF_SecOps_Specialist",
            description="Microsoft Agent Framework specialist for endpoint isolation, EDR incident triage, and memory forensics",
            tools=list(self.ops_tools.values())
        )

    def execute_request(self, ticket: IncidentTicket, context_graph: ContextGraph, approval_decision: Optional[ApprovalStatus] = None) -> IncidentTicket:
        user_email = context_graph.get_fact("requester_email") or ticket.requester_email
        agent_id = context_graph.get_fact("agent_id") or "agent-trmm-002"
        approver_email = "soc.lead@enterprise.com"
        case_id = f"SEC-{ticket.ticket_id}"

        workflow_name = "AE_Isolate_Endpoint_Workflow"
        params = {
            "agent_id": agent_id,
            "reason": "Suspected malware / EDR high-severity threat detection",
            "ticket_id": ticket.ticket_id
        }

        approval_record = self.hitl_manager.create_approval_request(
            ticket_id=ticket.ticket_id,
            approver_email=approver_email,
            action_name=workflow_name,
            parameters=params,
            risk_tier="R2",
            target_resource=f"Compromised Endpoint {agent_id}",
            business_justification=f"Immediate network containment and forensic snapshot for {agent_id}",
            requester_email=user_email
        )

        if approval_decision:
            self.hitl_manager.sign_decision(approval_record.approval_id, approval_decision, "Authorized by SOC Lead")
            approval_record = self.hitl_manager.get_approval(approval_record.approval_id)

        if approval_record.status == ApprovalStatus.APPROVED:
            context_graph.validate_action_parameters(workflow_name, params)
            app_dict = approval_record.model_dump() if hasattr(approval_record, "model_dump") else approval_record.dict()
            decision = self.policy_engine.evaluate(workflow_name, params, app_dict)
            if decision["decision"] == "DENY":
                raise PermissionError(f"PDP denied {workflow_name}: {decision.get('reason')}")

            # 1. Isolate endpoint
            iso_res = self.ops_tools["isolate_endpoint"](agent_id=agent_id, reason="EDR Threat Alert", ticket_id=ticket.ticket_id)
            
            # 2. Extract memory forensics
            for_params = {"agent_id": agent_id, "case_id": case_id, "ticket_id": ticket.ticket_id}
            context_graph.validate_action_parameters("AE_Extract_Memory_Forensics_Workflow", for_params)
            for_dec = self.policy_engine.evaluate("AE_Extract_Memory_Forensics_Workflow", for_params, app_dict)
            if for_dec["decision"] == "DENY":
                raise PermissionError(f"PDP denied AE_Extract_Memory_Forensics_Workflow: {for_dec.get('reason')}")
            
            forensics_res = self.ops_tools["extract_memory_forensics"](agent_id=agent_id, case_id=case_id, ticket_id=ticket.ticket_id)

            # 3. Update SIEM ticket
            self.ops_tools["update_siem_ticket"](alert_id=case_id, status="CONTAINED", notes=f"Isolated endpoint {agent_id}. Forensic dump: {forensics_res.get('dump_path', 's3://soc-evidence/dump.raw')}", ticket_id=ticket.ticket_id)

            verification = self.verify_state(
                check_name=f"SecOps Isolation Verification on {agent_id}",
                actual_state=iso_res,
                expected_state={"isolation_state": "ISOLATED"},
                keys_to_compare=["isolation_state"]
            )
            ticket.verification = verification
            ticket.status = "RESOLVED"
            ticket.customer_summary = f"Security action completed on {agent_id}. Device network isolated (RMM active), live memory triage extracted, and SIEM updated."
            self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Complete", resolution_code="SECURITY_CONTAINED", work_notes=f"Isolated and memory captured: {case_id}", customer_summary=ticket.customer_summary)
        elif approval_record.status == ApprovalStatus.REJECTED:
            ticket.status = "CLOSED_REJECTED"
            ticket.customer_summary = f"Security isolation was rejected by SOC Approver ({approver_email})."
            self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Rejected", resolution_code="REJECTED_BY_APPROVER", work_notes=f"Rejected by {approver_email}", customer_summary=ticket.customer_summary)
        else:
            ticket.status = "PENDING_APPROVAL"
            ticket.customer_summary = f"Endpoint isolation and forensic triage requires approval from SOC Lead ({approver_email})."

        return ticket
