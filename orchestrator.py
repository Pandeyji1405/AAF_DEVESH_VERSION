import json
from typing import Dict, Any, Optional
from core.models import UserQuery, IncidentTicket, IntentCategory, ApprovalStatus, ApprovalDecisionChannel
from core.policy_engine import PolicyDecisionPoint
from core.hitl import HumanInTheLoopManager
from core.case_store import CaseStore
from automationedge.client import AutomationEdgeClient
from maf_agents import (
    MAFCaseManagerAgent,
    MAFDeviceOpsAgent,
    MAFAccessGovAgent,
    MAFHardwareAgent,
    MAFOnboardingAgent,
    MAFSecOpsAgent,
    MAFRMMCopilotAgent,
    MAFInfraOpsAgent
)

class AutonomousITOrchestrator:
    def __init__(self, use_mock_ae: bool = False, base_url: Optional[str] = None,
                 username: Optional[str] = None, password: Optional[str] = None,
                 org_code: Optional[str] = None):
        self.ae_client = AutomationEdgeClient(
            base_url=base_url,
            username=username,
            password=password,
            org_code=org_code,
            use_mock=use_mock_ae
        )
        self.policy_engine = PolicyDecisionPoint()
        self.hitl_manager = HumanInTheLoopManager()
        self.case_store = CaseStore()

        # Specialist Agents
        self.case_manager = MAFCaseManagerAgent(self.ae_client, self.policy_engine, self.hitl_manager)
        self.access_agent = MAFAccessGovAgent(self.ae_client, self.policy_engine, self.hitl_manager)
        self.device_agent = MAFDeviceOpsAgent(self.ae_client, self.policy_engine, self.hitl_manager)
        self.hardware_agent = MAFHardwareAgent(self.ae_client, self.policy_engine, self.hitl_manager)
        self.onboarding_agent = MAFOnboardingAgent(self.ae_client, self.policy_engine, self.hitl_manager)
        self.secops_agent = MAFSecOpsAgent(self.ae_client, self.policy_engine, self.hitl_manager)
        self.rmm_copilot_agent = MAFRMMCopilotAgent(self.ae_client, self.policy_engine, self.hitl_manager)
        self.infra_ops_agent = MAFInfraOpsAgent(self.ae_client, self.policy_engine, self.hitl_manager)

    def _get_specialist(self, intent: IntentCategory):
        mapping = {
            IntentCategory.ACCESS: self.access_agent,
            IntentCategory.DEVICE: self.device_agent,
            IntentCategory.HARDWARE: self.hardware_agent,
            IntentCategory.ONBOARDING: self.onboarding_agent,
            IntentCategory.SECOPS: self.secops_agent,
            IntentCategory.RMM_COPILOT: self.rmm_copilot_agent,
            IntentCategory.INFRA_OPS: self.infra_ops_agent
        }
        return mapping.get(intent, self.device_agent)

    def process_request(self, query_text: str, requester_email: str, 
                        approval_decision: Optional[ApprovalStatus] = None) -> Dict[str, Any]:
        """
        Executes the full end-to-end MAF reasoning, governance, execution, and verification flow.
        """
        user_query = UserQuery(query_text=query_text, requester_email=requester_email)
        
        # 1. MAF Intake, Intent Classification & Ticket Creation
        ticket, context_graph = self.case_manager.process_incoming_query(user_query)

        # 2. Dispatch to Specialist Agent based on Intent
        specialist = self._get_specialist(ticket.intent)
        resolved_ticket = specialist.execute_request(ticket, context_graph, approval_decision)

        # 3. If Pending Approval, persist state into SQLite Case Store
        for app in self.hitl_manager.approval_store.values():
            if app.ticket_id == resolved_ticket.ticket_id and app.status == ApprovalStatus.PENDING:
                self.case_store.save_case(
                    ticket=resolved_ticket,
                    context_graph=context_graph,
                    approval_id=app.approval_id,
                    workflow_name=app.action_name,
                    parameters=app.parameters,
                    specialist_name=specialist.agent_name,
                    reference_token=app.reference_token
                )

        # Collect all approval records generated for this ticket
        approvals = [
            {
                "approval_id": app.approval_id,
                "status": app.status.value,
                "approver_email": app.approver_email,
                "action_name": app.action_name,
                "risk_tier": app.risk_tier,
                "target_resource": app.target_resource,
                "business_justification": app.business_justification,
                "card": self.hitl_manager.render_approval_card(app.approval_id),
                "teams_card": self.hitl_manager.render_teams_adaptive_card(app),
                "record": app.model_dump() if hasattr(app, "model_dump") else app.dict()
            }
            for app in self.hitl_manager.approval_store.values()
            if app.ticket_id == resolved_ticket.ticket_id
        ]

        ticket_dump = resolved_ticket.model_dump() if hasattr(resolved_ticket, "model_dump") else resolved_ticket.dict()
        ver_dump = resolved_ticket.verification.model_dump() if (resolved_ticket.verification and hasattr(resolved_ticket.verification, "model_dump")) else (resolved_ticket.verification.dict() if resolved_ticket.verification else None)

        return {
            "ticket": ticket_dump,
            "context_graph": context_graph.snapshot(),
            "verification": ver_dump,
            "user_response": resolved_ticket.customer_summary,
            "approvals": approvals
        }

    def resume_case(self, approval_id: str, decision: ApprovalStatus, notes: str = "",
                    channel: Optional[ApprovalDecisionChannel] = None) -> Dict[str, Any]:
        """
        Resumes a paused case after human authorization has been signed (via Webhook or Email Reply).
        Re-validates zero-hallucination parameters and PDP policies before execution.
        """
        case_data = self.case_store.get_case_by_approval_id(approval_id)
        if not case_data:
            raise ValueError(f"Case with approval {approval_id} not found in persistent store.")

        # Reconstruct models
        ticket = IncidentTicket(**case_data["ticket"])
        specialist = self._get_specialist(ticket.intent)

        # Sign in HITL Manager
        self.hitl_manager.sign_decision(approval_id, decision, comments=notes, channel=channel)
        
        # Resume specialist execution with the explicit approval decision
        # Load ContextGraph from snapshot
        from core.context_graph import ContextGraph
        cg = ContextGraph(ticket_id=ticket.ticket_id, requester_email=ticket.requester_email)
        cg.facts = case_data["context_graph"].get("facts", {})
        cg.entities = case_data["context_graph"].get("entities", {})

        resolved_ticket = specialist.execute_request(ticket, cg, approval_decision=decision)
        
        ticket_dump = resolved_ticket.model_dump() if hasattr(resolved_ticket, "model_dump") else resolved_ticket.dict()
        self.case_store.update_case_status(case_data["case_id"], resolved_ticket.status, ticket_dump)

        return {
            "ticket": ticket_dump,
            "status": resolved_ticket.status,
            "customer_summary": resolved_ticket.customer_summary
        }
