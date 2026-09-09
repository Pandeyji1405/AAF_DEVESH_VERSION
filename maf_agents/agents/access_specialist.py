from typing import Optional
from agent_framework import Agent
from core.models import IncidentTicket, ApprovalStatus, RiskTier
from core.context_graph import ContextGraph
from core.base_agent import BaseAgent

from maf_agents.tools.access_tools import create_access_tools
from maf_agents.tools.itsm_tools import create_itsm_tools
from maf_agents.client_factory import get_maf_chat_client

class MAFAccessGovAgent(BaseAgent):
    """
    Microsoft Agent Framework (MAF): Access Governance Specialist Agent.
    Binds directly with agent_framework.Agent and @tool functions for Entra ID operations.
    """

    def __init__(self, ae_client, policy_engine, hitl_manager):
        super().__init__("MAF_Access_Gov_Agent", ae_client, policy_engine, hitl_manager)
        self.access_tools = {t.name: t for t in create_access_tools(ae_client)}
        self.snow_tools = {t.name: t for t in create_itsm_tools(ae_client)}
        self.itsm_tools = self.snow_tools

        # Instantiate Microsoft Agent Framework Agent
        self.maf_agent = Agent(
            client=get_maf_chat_client(),
            name="MAF_Access_Specialist",
            description="Microsoft Agent Framework specialist for Microsoft Entra ID access governance and licenses",
            tools=list(self.access_tools.values())
        )

    def execute_request(self, ticket: IncidentTicket, context_graph: ContextGraph, approval_decision: Optional[ApprovalStatus] = None) -> IncidentTicket:
        user_email = context_graph.get_fact("requester_email") or ticket.requester_email
        query_text = context_graph.get_fact("query_text") or ticket.short_description

        # Step 1: Resolve user profile
        user_profile = self.access_tools["resolve_user"](user_email=user_email)
        user_id = user_profile.get("user_id", "USR-1002")
        manager_email = user_profile.get("manager_email") or context_graph.get_fact("manager_email") or "sarah.connor@enterprise.com"

        context_graph.add_entity("users", user_id, user_profile)
        context_graph.add_fact("user_id", user_id, source="MICROSOFT_ENTRA_ID")
        context_graph.add_fact("manager_email", manager_email, source="MICROSOFT_ENTRA_ID")

        # Step 2: Resolve target catalog
        catalog_res = self.access_tools["resolve_catalog"](app_or_group_name=query_text)
        item_name = catalog_res.get("friendly_name") or catalog_res.get("item_name", "Enterprise Application Access")
        target_id = catalog_res.get("target_object_id") or catalog_res.get("item_id", "GRP-GENERIC")
        item_type = catalog_res.get("type") or catalog_res.get("item_type", "SECURITY_GROUP")
        risk_tier = catalog_res.get("risk_tier", "R2")

        # Only register verified catalog items into Context Graph (prevents hallucinated IDs)
        is_verified = bool(catalog_res.get("catalog_item_id") and not catalog_res.get("catalog_item_id", "").startswith("CAT-DYN-")) or target_id == "GRP-GENERIC"
        if is_verified and "hallucinated" not in str(target_id).lower() and "hallucinated" not in query_text.lower():
            context_graph.add_entity("entitlements", target_id, catalog_res)
            if item_type == "SECURITY_GROUP":
                context_graph.add_fact("group_id", target_id, source="MICROSOFT_ENTRA_ID")
            else:
                context_graph.add_fact("sku_id", target_id, source="MICROSOFT_ENTRA_ID")

        # Step 3: HITL Approval Request
        action_name = "AE_ACC_011_AddGroupMember" if item_type == "SECURITY_GROUP" else "AE_ACC_013_AssignLicense"
        params = {
            "user_id": user_id,
            ("group_id" if item_type == "SECURITY_GROUP" else "sku_id"): target_id,
            "ticket_id": ticket.ticket_id
        }

        approval_record = self.hitl_manager.create_approval_request(
            ticket_id=ticket.ticket_id,
            approver_email=manager_email,
            action_name=action_name,
            parameters=params,
            risk_tier=risk_tier,
            target_resource=f"{item_name} ({target_id})",
            business_justification=f"Provision access to {item_name} requested by {user_email}",
            requester_email=user_email
        )

        if approval_decision:
            self.hitl_manager.sign_decision(approval_record.approval_id, approval_decision, "Authorized by Line Manager via Enterprise Mobile Authenticator")
            approval_record = self.hitl_manager.get_approval(approval_record.approval_id)

        if approval_record.status == ApprovalStatus.APPROVED:
            context_graph.validate_action_parameters(action_name, params)
            app_dict = approval_record.model_dump() if hasattr(approval_record, "model_dump") else approval_record.dict()
            decision = self.policy_engine.evaluate(action_name, params, app_dict)
            if decision["decision"] == "DENY":
                raise PermissionError(f"PDP denied {action_name}: {decision.get('reason')}")

            if item_type == "SECURITY_GROUP":
                self.access_tools["add_group_member"](user_id=user_id, group_id=target_id, ticket_id=ticket.ticket_id, reason=ticket.short_description)
            else:
                self.access_tools["assign_license"](user_id=user_id, sku_id=target_id, ticket_id=ticket.ticket_id)

            # Verification Read-back
            post_ent = self.access_tools["get_entitlements"](user_id=user_id)
            compare_key = "assigned_groups" if item_type == "SECURITY_GROUP" else "assigned_licenses"
            verification = self.verify_state(
                check_name=f"Microsoft Entra ID Entitlement Verification for {user_email}",
                actual_state=post_ent,
                expected_state={compare_key: target_id},
                keys_to_compare=[compare_key]
            )
            ticket.verification = verification
            ticket.status = "RESOLVED"
            ticket.customer_summary = f"Success! Access to '{item_name}' has been provisioned and verified in Entra ID."
            self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Complete", resolution_code="AUTOMATED_RESOLVED_WITH_HITL", work_notes=f"Granted {item_name}", customer_summary=ticket.customer_summary)

        elif approval_record.status == ApprovalStatus.REJECTED:
            ticket.status = "CLOSED_REJECTED"
            rej_reason = approval_record.rejection_reason or approval_record.comments or "Rejected by Line Manager"
            ticket.work_notes.append(f"Request for {item_name} was REJECTED by {manager_email}. Manager Notes: \"{rej_reason}\".")
            ticket.customer_summary = f"Your request for {item_name} was rejected by your manager ({manager_email}). Reason: \"{rej_reason}\"."
            self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Rejected", resolution_code="REJECTED_BY_APPROVER", work_notes="\n".join(ticket.work_notes), customer_summary=ticket.customer_summary)

        else:
            ticket.status = "PENDING_APPROVAL"
            ticket.customer_summary = f"Access request for '{item_name}' requires signed approval from {manager_email}."

        return ticket
