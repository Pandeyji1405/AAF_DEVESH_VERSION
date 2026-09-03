import os
from typing import Dict, Any, Optional
from agent_framework import tool

def create_servicenow_tools(ae_client):
    """
    Creates Microsoft Agent Framework (@tool) tools for ServiceNow Incident Management
    by directly calling published ServiceNow workflows on the AutomationEdge T4 server
    ('Servicenow_Incident_Creation' and 'ServiceNow_Update_Incident').
    All workflow executions appear in the AutomationEdge T4 'Requests' tab.
    """
    create_workflow_name = os.environ.get("AE_WORKFLOW_CREATE_INCIDENT", "Servicenow_Incident_Creation")
    update_workflow_name = os.environ.get("AE_WORKFLOW_UPDATE_INCIDENT", "ServiceNow_Update_Incident")

    snow_url = os.environ.get("SERVICENOW_INSTANCE_URL", "https://dev00000.service-now.com")
    snow_user = os.environ.get("SERVICENOW_USERNAME", "admin")
    snow_pass = os.environ.get("SERVICENOW_PASSWORD", "")

    @tool(
        name="create_incident",
        description="Calls the published 'Servicenow_Incident_Creation' workflow on AutomationEdge T4 and returns mapped ticket parameters."
    )
    def create_incident(requester_email: str, short_description: str, description: str, category: str, urgency: str = "Medium") -> Dict[str, Any]:
        # Required parameters for published AutomationEdge T4 Servicenow_Incident_Creation workflow
        params = {
            "ServiceNowDeveloperURL": snow_url,
            "Username_Servicenow": snow_user,
            "Password_Servicenow": snow_pass,
            "Caller": requester_email,
            "Short_Description": short_description,
            "Description": description,
            "Impact": "2",
            "Urgency": "1" if urgency.lower() in ["high", "critical", "1"] else "2",
            "work_note": f"Incident created via Autonomous IT Service Desk for {requester_email}"
        }
        
        # Execute published workflow on AutomationEdge T4 server
        res = ae_client.execute_workflow(create_workflow_name, params)
        resp = res.get("workflowResponse", {})
        if isinstance(resp, str):
            import json
            try:
                resp = json.loads(resp)
            except Exception:
                resp = {"output": resp}

        # Extract ticket fields from AutomationEdge T4 output
        ticket_id = (
            resp.get("Incident_Number") or
            resp.get("incident_number") or
            resp.get("ticket_id") or
            resp.get("number") or
            resp.get("ticket_number")
        )
        sys_id = (
            resp.get("SysId") or
            resp.get("sys_id") or
            resp.get("Sys_Id") or
            f"sys_{ticket_id or 'unknown'}"
        )
        
        if not ticket_id:
            import uuid
            ticket_id = f"INC-{uuid.uuid4().hex[:8].upper()}"

        request_id = res.get("automationRequestId", "")

        return {
            "ticket_id": str(ticket_id),
            "number": str(ticket_id),
            "sys_id": str(sys_id),
            "SysId": str(sys_id),
            "state": resp.get("state", "New"),
            "short_description": short_description,
            "category": category,
            "requester_email": requester_email,
            "ae_request_id": request_id,
            "source": "AUTOMATIONEDGE_T4_WORKFLOW",
            "raw_result": resp
        }

    @tool(
        name="update_incident",
        description="Calls the published 'ServiceNow_Update_Incident' workflow on AutomationEdge T4 to update state and work notes."
    )
    def update_incident(ticket_id: str, state: str, resolution_code: str = "", work_notes: str = "", customer_summary: str = "", sys_id: str = "") -> Dict[str, Any]:
        target_sys_id = sys_id or ticket_id

        # Map state string to ServiceNow close state
        close_code_val = resolution_code or ("Solved (Work Around)" if "approved" in state.lower() or "complete" in state.lower() else "Closed/Rejected by Approver")
        close_note_val = customer_summary or work_notes or f"Updated state to {state}"

        # Required parameters for published AutomationEdge T4 ServiceNow_Update_Incident workflow
        params = {
            "ServiceNowDeveloperURL": snow_url,
            "Username_Servicenow": snow_user,
            "Password_Servicenow": snow_pass,
            "SysId": target_sys_id,
            "state": state,
            "close_code": close_code_val,
            "close_note": close_note_val
        }
        
        # Execute update workflow on AutomationEdge T4 server
        res = ae_client.execute_workflow(update_workflow_name, params)
        resp = res.get("workflowResponse", {})
        if isinstance(resp, str):
            import json
            try:
                resp = json.loads(resp)
            except Exception:
                resp = {"output": resp}

        return {
            "ticket_id": ticket_id,
            "sys_id": target_sys_id,
            "state": state,
            "ae_request_id": res.get("automationRequestId", ""),
            "status": res.get("status", "Complete"),
            "raw_result": resp
        }

    return [
        create_incident,
        update_incident
    ]
