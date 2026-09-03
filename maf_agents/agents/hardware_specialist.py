from typing import Optional
from agent_framework import Agent
from core.models import IncidentTicket, ApprovalStatus, RiskTier
from core.context_graph import ContextGraph
from core.base_agent import BaseAgent

from maf_agents.tools.hardware_tools import create_hardware_tools
from maf_agents.tools.servicenow_tools import create_servicenow_tools
from maf_agents.client_factory import get_maf_chat_client

class MAFHardwareAgent(BaseAgent):
    """
    Microsoft Agent Framework (MAF): Hardware Asset Lifecycle Specialist Agent.
    Binds directly with agent_framework.Agent and @tool functions for CMDB operations.
    """

    def __init__(self, ae_client, policy_engine, hitl_manager):
        super().__init__("MAF_Hardware_Agent", ae_client, policy_engine, hitl_manager)
        self.hardware_tools = {t.name: t for t in create_hardware_tools(ae_client)}
        self.snow_tools = {t.name: t for t in create_servicenow_tools(ae_client)}

        # Instantiate Microsoft Agent Framework Agent
        self.maf_agent = Agent(
            client=get_maf_chat_client(),
            name="MAF_Hardware_Specialist",
            description="Microsoft Agent Framework specialist for CMDB hardware lifecycle and replacement logistics",
            tools=list(self.hardware_tools.values())
        )

    def execute_request(self, ticket: IncidentTicket, context_graph: ContextGraph, approval_decision: Optional[ApprovalStatus] = None) -> IncidentTicket:
        user_email = context_graph.get_fact("requester_email") or ticket.requester_email
        assigned_device = context_graph.get_fact("assigned_device_id") or "DEV-WIN-102"

        # Step 1: Query CMDB via MAF hardware tool
        hw_asset = self.hardware_tools["get_asset_details"](asset_tag_or_serial=assigned_device)
        ci_id = hw_asset.get("ci_id", "CI-HW-5002")
        serial_number = hw_asset.get("serial_number", "PF4B7719")
        model_name = hw_asset.get("model_name", "ThinkPad X1 Carbon Gen 11")
        asset_tag = hw_asset.get("asset_tag", "ASSET-L-102")

        context_graph.add_entity("hardware_assets", ci_id, hw_asset)
        context_graph.add_fact("ci_id", ci_id, source="SERVICENOW_CMDB")
        context_graph.add_fact("serial_number", serial_number, source="SERVICENOW_CMDB")

        manager_email = context_graph.get_fact("manager_email") or "sarah.connor@enterprise.com"

        # Step 2: HITL Approval Request
        params = {
            "ci_id": ci_id,
            "serial_number": serial_number,
            "shipping_address": "Enterprise Office - IT Hub / Employee Remote Desk",
            "ticket_id": ticket.ticket_id
        }

        approval_record = self.hitl_manager.create_approval_request(
            ticket_id=ticket.ticket_id,
            approver_email=manager_email,
            action_name="AE_HW_020_OrderReplacement",
            parameters=params,
            risk_tier="R2",
            target_resource=f"{model_name} (Serial: {serial_number}, Tag: {asset_tag})",
            business_justification=f"Order hardware replacement for defective asset {ci_id} ({model_name})",
            requester_email=user_email
        )

        if approval_decision:
            self.hitl_manager.sign_decision(approval_record.approval_id, approval_decision, "Authorized by Line Manager via Enterprise Mobile Authenticator")
            approval_record = self.hitl_manager.get_approval(approval_record.approval_id)

        if approval_record.status == ApprovalStatus.APPROVED:
            context_graph.validate_action_parameters("AE_HW_020_OrderReplacement", params)
            app_dict = approval_record.dict() if hasattr(approval_record, "dict") else approval_record.model_dump()
            decision = self.policy_engine.evaluate("AE_HW_020_OrderReplacement", params, app_dict)
            if decision["decision"] == "DENY":
                raise PermissionError(f"PDP denied AE_HW_020_OrderReplacement: {decision.get('reason')}")

            order_res = self.hardware_tools["order_replacement"](ci_id=ci_id, serial_number=serial_number, ticket_id=ticket.ticket_id)
            tracking_num = order_res.get("tracking_number", "1Z99999999AA4826")
            carrier = order_res.get("carrier", "FedEx Enterprise Express")

            # Update CMDB CI State
            ci_params = {"ci_id": ci_id, "new_install_status": "Pending Replacement / In Repair", "condition_notes": f"Replaced via ticket {ticket.ticket_id}", "ticket_id": ticket.ticket_id}
            context_graph.validate_action_parameters("AE_HW_010_UpdateCIState", ci_params)
            ci_decision = self.policy_engine.evaluate("AE_HW_010_UpdateCIState", ci_params, app_dict)
            if ci_decision["decision"] == "DENY":
                raise PermissionError(f"PDP denied AE_HW_010_UpdateCIState: {ci_decision.get('reason')}")

            self.hardware_tools["update_ci_state"](ci_id=ci_id, new_install_status="Pending Replacement / In Repair", ticket_id=ticket.ticket_id, condition_notes=f"Replaced via ticket {ticket.ticket_id}")

            # Verification Read-back
            post_cmdb = self.hardware_tools["get_asset_details"](asset_tag_or_serial=ci_id)
            verification = self.verify_state(
                check_name=f"CMDB Asset Status Verification on {ci_id}",
                actual_state=post_cmdb,
                expected_state={"install_status": "Pending Replacement / In Repair"},
                keys_to_compare=["install_status"]
            )
            ticket.verification = verification
            ticket.status = "RESOLVED"
            ticket.customer_summary = f"Your hardware replacement for {model_name} has been ordered. Tracking Number: {tracking_num} ({carrier}). Estimated delivery: 2 Business Days."
            self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Complete", resolution_code="AUTOMATED_RESOLVED_WITH_HITL", work_notes=f"Replacement dispatched. Tracking: {tracking_num}", customer_summary=ticket.customer_summary)

        elif approval_record.status == ApprovalStatus.REJECTED:
            ticket.status = "CLOSED_REJECTED"
            rej_reason = approval_record.rejection_reason or approval_record.comments or "Rejected by Line Manager"
            ticket.work_notes.append(f"Hardware replacement request for {model_name} was REJECTED by {manager_email}. Manager Notes: \"{rej_reason}\".")
            ticket.customer_summary = f"Your hardware replacement request for {model_name} was rejected by your manager ({manager_email}). Reason: \"{rej_reason}\"."
            self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Rejected", resolution_code="REJECTED_BY_APPROVER", work_notes="\n".join(ticket.work_notes), customer_summary=ticket.customer_summary)

        else:
            ticket.status = "PENDING_APPROVAL"
            ticket.customer_summary = f"Hardware replacement for {model_name} requires signed approval from {manager_email}."

        return ticket
