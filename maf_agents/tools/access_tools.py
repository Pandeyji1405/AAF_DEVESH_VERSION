from typing import Dict, Any
from agent_framework import tool

def create_access_tools(ae_client):
    """
    Creates Microsoft Agent Framework (@tool) tools for Microsoft Entra ID & Access Governance.
    """

    @tool(
        name="resolve_user",
        description="Resolves user identity, department, manager, and assigned hardware from Microsoft Entra ID."
    )
    def resolve_user(user_email: str) -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_ACC_001_ResolveUser", {
            "user_email": user_email
        })
        return res.get("workflowResponse", {})

    @tool(
        name="get_entitlements",
        description="Queries currently assigned security groups, licenses, and roles from Microsoft Entra ID."
    )
    def get_entitlements(user_id: str) -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_ACC_002_GetEntitlements", {
            "user_id": user_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="resolve_catalog",
        description="Matches a natural language request against the enterprise access and SaaS catalog."
    )
    def resolve_catalog(app_or_group_name: str) -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_ACC_003_ResolveCatalog", {
            "app_or_group_name": app_or_group_name
        })
        return res.get("workflowResponse", {})

    @tool(
        name="add_group_member",
        description="Adds a user to a Microsoft Entra ID Security Group (e.g. GitHub Enterprise, DevOps)."
    )
    def add_group_member(user_id: str, group_id: str, ticket_id: str, reason: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_ACC_011_AddGroupMember", {
            "user_id": user_id,
            "group_id": group_id,
            "ticket_id": ticket_id,
            "reason": reason
        })
        return res.get("workflowResponse", {})

    @tool(
        name="assign_license",
        description="Assigns an enterprise software license (e.g. M365 E5, Figma, Power BI) in Microsoft Entra ID."
    )
    def assign_license(user_id: str, sku_id: str, ticket_id: str) -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_ACC_013_AssignLicense", {
            "user_id": user_id,
            "sku_id": sku_id,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="revoke_sessions",
        description="Revokes all active refresh tokens and browser sessions in Microsoft Entra ID."
    )
    def revoke_sessions(user_id: str) -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_ACC_021_RevokeSessions", {
            "user_id": user_id
        })
        return res.get("workflowResponse", {})

    return [
        resolve_user,
        get_entitlements,
        resolve_catalog,
        add_group_member,
        assign_license,
        revoke_sessions
    ]
