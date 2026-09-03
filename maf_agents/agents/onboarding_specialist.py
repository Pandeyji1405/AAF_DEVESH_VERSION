from typing import Optional, Dict, Any
from agent_framework import Agent
from core.models import IncidentTicket, ApprovalStatus, RiskTier
from core.context_graph import ContextGraph
from core.base_agent import BaseAgent

from maf_agents.tools.ops_tools import create_ops_tools
from maf_agents.tools.servicenow_tools import create_servicenow_tools
from maf_agents.client_factory import get_maf_chat_client

class MAFOnboardingAgent(BaseAgent):
    """
    Microsoft Agent Framework (MAF): Employee Onboarding Specialist Agent.
    Orchestrates new-hire package deployments, local security baseline policies, and welcome kit dispatch.
    """

    def __init__(self, ae_client, policy_engine, hitl_manager):
        super().__init__("MAF_Onboarding_Agent", ae_client, policy_engine, hitl_manager)
        self.ops_tools = {t.name: t for t in create_ops_tools(ae_client)}
        self.snow_tools = {t.name: t for t in create_servicenow_tools(ae_client)}

        self.maf_agent = Agent(
            client=get_maf_chat_client(),
            name="MAF_Onboarding_Specialist",
            description="Microsoft Agent Framework specialist for automated new hire provisioning and workstation staging",
            tools=list(self.ops_tools.values())
        )

    def execute_request(self, ticket: IncidentTicket, context_graph: ContextGraph, approval_decision: Optional[ApprovalStatus] = None) -> IncidentTicket:
        user_email = context_graph.get_fact("requester_email") or ticket.requester_email
        agent_id = context_graph.get_fact("agent_id") or "agent-trmm-001"
        manager_email = context_graph.get_fact("manager_email") or "sarah.connor@enterprise.com"
        bundle_name = "STANDARD_DEV_WORKSTATION_BUNDLE"

        workflow_name = "AE_Package_Deployer_Workflow"
        params = {
            "agent_id": agent_id,
            "package_bundle": bundle_name,
            "ticket_id": ticket.ticket_id
        }

        approval_record = self.hitl_manager.create_approval_request(
            ticket_id=ticket.ticket_id,
            approver_email=manager_email,
            action_name=workflow_name,
            parameters=params,
            risk_tier="R2",
            target_resource=f"Workstation {agent_id} for {user_email}",
            business_justification=f"Provision workstation with {bundle_name} for new employee {user_email}",
            requester_email=user_email
        )

        if approval_decision:
            self.hitl_manager.sign_decision(approval_record.approval_id, approval_decision, "Authorized by Line Manager via Enterprise Mobile Authenticator")
            approval_record = self.hitl_manager.get_approval(approval_record.approval_id)

        if approval_record.status == ApprovalStatus.APPROVED:
            context_graph.validate_action_parameters(workflow_name, params)
            app_dict = approval_record.dict() if hasattr(approval_record, "dict") else approval_record.model_dump()
            decision = self.policy_engine.evaluate(workflow_name, params, app_dict)
            if decision["decision"] == "DENY":
                raise PermissionError(f"PDP denied {workflow_name}: {decision.get('reason')}")

            # 1. Deploy package bundle
            deploy_res = self.ops_tools["deploy_package"](agent_id=agent_id, package_bundle=bundle_name, ticket_id=ticket.ticket_id)
            
            # 2. Configure baseline policies
            pol_params = {"agent_id": agent_id, "policy_set": "CORP_ONBOARDING_V1", "ticket_id": ticket.ticket_id}
            context_graph.validate_action_parameters("AE_Configure_Local_Policies_Workflow", pol_params)
            pol_dec = self.policy_engine.evaluate("AE_Configure_Local_Policies_Workflow", pol_params, app_dict)
            if pol_dec["decision"] == "DENY":
                raise PermissionError(f"PDP denied AE_Configure_Local_Policies_Workflow: {pol_dec.get('reason')}")
            self.ops_tools["configure_local_policies"](agent_id=agent_id, policy_set="CORP_ONBOARDING_V1", ticket_id=ticket.ticket_id)

            # 3. Send welcome kit
            self.ops_tools["send_welcome_kit"](user_email=user_email, recipient_name=user_email.split('@')[0].replace('.', ' ').title(), ticket_id=ticket.ticket_id)

            # Strict Verification Read-back
            verification = self.verify_state(
                check_name=f"Workstation Onboarding Provisioning on {agent_id}",
                actual_state=deploy_res,
                expected_state={"deployment_status": "COMPLETED"},
                keys_to_compare=["deployment_status"]
            )
            ticket.verification = verification
            ticket.status = "RESOLVED"
            ticket.customer_summary = f"Onboarding complete! Standard software bundle and security policies deployed to workstation {agent_id}. Welcome kit dispatched to {user_email}."
            self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Complete", resolution_code="ONBOARDING_PROVISIONED", work_notes="Workstation configured and kit sent.", customer_summary=ticket.customer_summary)
        elif approval_record.status == ApprovalStatus.REJECTED:
            ticket.status = "CLOSED_REJECTED"
            rej_reason = approval_record.rejection_reason or approval_record.comments or f"Rejected by {manager_email}"
            ticket.work_notes.append(f"Onboarding request was REJECTED by {manager_email}. Notes: \"{rej_reason}\".")
            ticket.customer_summary = f"Onboarding provisioning request was rejected by your manager ({manager_email}). Reason: \"{rej_reason}\"."
            self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Rejected", resolution_code="REJECTED_BY_APPROVER", work_notes="\n".join(ticket.work_notes), customer_summary=ticket.customer_summary)
        else:
            ticket.status = "PENDING_APPROVAL"
            ticket.customer_summary = f"Workstation provisioning requires manager approval from {manager_email}."

        return ticket
