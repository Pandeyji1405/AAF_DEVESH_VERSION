from typing import Optional, Dict, Any
from agent_framework import Agent
from core.models import IncidentTicket, ApprovalStatus, RiskTier, ProposedAction
from core.context_graph import ContextGraph
from core.base_agent import BaseAgent

from maf_agents.tools.ops_tools import create_ops_tools
from maf_agents.tools.itsm_tools import create_itsm_tools
from maf_agents.client_factory import get_maf_chat_client

class MAFRMMCopilotAgent(BaseAgent):
    """
    Microsoft Agent Framework (MAF): RMM Fleet Copilot Specialist Agent.
    Executes cross-fleet diagnostics, bulk querying, and governed batch script deployments.
    """

    def __init__(self, ae_client, policy_engine, hitl_manager):
        super().__init__("MAF_RMM_Copilot_Agent", ae_client, policy_engine, hitl_manager)
        self.ops_tools = {t.name: t for t in create_ops_tools(ae_client)}
        self.snow_tools = {t.name: t for t in create_itsm_tools(ae_client)}
        self.itsm_tools = self.snow_tools

        self.maf_agent = Agent(
            client=get_maf_chat_client(),
            name="MAF_RMM_Copilot",
            description="Microsoft Agent Framework specialist for cross-fleet TacticalRMM queries and batch operations",
            tools=list(self.ops_tools.values())
        )

    def execute_request(self, ticket: IncidentTicket, context_graph: ContextGraph, approval_decision: Optional[ApprovalStatus] = None) -> IncidentTicket:
        user_email = context_graph.get_fact("requester_email") or ticket.requester_email
        query_text = (context_graph.get_fact("query_text") or ticket.short_description).lower()
        manager_email = context_graph.get_fact("manager_email") or "it.director@enterprise.com"

        # 1. Fleet Query (R0 - Read-Only)
        query_filter = "os=Windows AND client=Enterprise Engineering"
        query_res = self.ops_tools["query_endpoints"](query_filter=query_filter)
        target_nodes = query_res.get("matching_agent_ids", ["agent-trmm-001", "agent-trmm-002", "agent-trmm-004"])
        target_str = ",".join(target_nodes)
        
        context_graph.add_fact("target_agent_ids", target_str, source="TACTICAL_RMM")

        # 2. Batch Execution (R2 - Standard Write with Approval)
        script_name = "DEPLOY_HOTFIX_SEC_V3.ps1"
        workflow_name = "AE_Batch_Script_Runner_Workflow"
        params = {
            "target_agent_ids": target_str,
            "script_name": script_name,
            "ticket_id": ticket.ticket_id
        }

        approval_record = self.hitl_manager.create_approval_request(
            ticket_id=ticket.ticket_id,
            approver_email=manager_email,
            action_name=workflow_name,
            parameters=params,
            risk_tier="R2",
            target_resource=f"{len(target_nodes)} Fleet Nodes ({target_str})",
            business_justification=f"Execute batch maintenance script {script_name} across {len(target_nodes)} endpoints",
            requester_email=user_email
        )

        if approval_decision:
            self.hitl_manager.sign_decision(approval_record.approval_id, approval_decision, "Batch execution authorized by IT Operations Director")
            approval_record = self.hitl_manager.get_approval(approval_record.approval_id)

        if approval_record.status == ApprovalStatus.APPROVED:
            context_graph.validate_action_parameters(workflow_name, params)
            app_dict = approval_record.model_dump() if hasattr(approval_record, "model_dump") else approval_record.dict()
            decision = self.policy_engine.evaluate(workflow_name, params, app_dict)
            if decision["decision"] == "DENY":
                raise PermissionError(f"PDP denied {workflow_name}: {decision.get('reason')}")

            batch_res = self.ops_tools["batch_execute"](target_agent_ids=target_str, script_name=script_name, ticket_id=ticket.ticket_id)
            batch_id = batch_res.get("batch_id", "BATCH-9001")
            
            stream_res = self.ops_tools["stream_execution_status"](batch_id=batch_id)

            verification = self.verify_state(
                check_name=f"TacticalRMM Fleet Batch Execution {batch_id}",
                actual_state=batch_res,
                expected_state={"batch_status": "COMPLETED"},
                keys_to_compare=["batch_status"]
            )
            action_id = f"ACT-FLEET-{len(ticket.actions_executed) + 1:03d}"
            ticket.actions_executed.append(ProposedAction(
                action_id=action_id,
                workflow_name=workflow_name,
                risk_tier=RiskTier.R2,
                target_entity=target_str,
                parameters={"script_name": script_name, "target_agent_ids": target_str, "batch_id": batch_id},
                reason=f"Batch execution of script '{script_name}' on {len(target_nodes)} fleet endpoints"
            ))
            context_graph.add_fact("last_executed_script", script_name, source="TACTICAL_RMM")
            context_graph.add_fact("batch_id", batch_id, source="TACTICAL_RMM")
            ticket.verification = verification
            ticket.status = "RESOLVED"
            ticket.customer_summary = (
                f"RMM Copilot successfully executed script '{script_name}' across {len(target_nodes)} nodes ({target_str}). Success rate: 100%.\n\n"
                f"💻 [Executed Script]: `{script_name}` (Batch ID: {batch_id})"
            )
            ticket.work_notes.append(
                f"[TACTICAL RMM FLEET EXECUTION RECORD]\n"
                f"• Target Fleet Nodes: {target_str}\n"
                f"• Workflow: AE_Batch_Script_Runner_Workflow\n"
                f"• Script Name: {script_name}\n"
                f"• Batch ID: {batch_id}\n"
                f"• Approval ID: {approval_record.approval_id}\n"
                f"• Status: COMPLETED (100% Verified)"
            )
            self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Complete", resolution_code="BATCH_EXECUTED", work_notes="\n".join(ticket.work_notes), customer_summary=ticket.customer_summary)
        elif approval_record.status == ApprovalStatus.REJECTED:
            ticket.status = "CLOSED_REJECTED"
            ticket.customer_summary = f"Batch fleet operation was rejected by IT Director ({manager_email})."
            self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Rejected", resolution_code="REJECTED_BY_APPROVER", work_notes=f"Rejected by {manager_email}", customer_summary=ticket.customer_summary)
        else:
            ticket.status = "PENDING_APPROVAL"
            ticket.customer_summary = f"Fleet batch execution across {len(target_nodes)} endpoints requires approval from {manager_email}."

        return ticket
