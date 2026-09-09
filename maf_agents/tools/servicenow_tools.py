import os
import json
import base64
import urllib.request
from typing import Dict, Any, Optional
from agent_framework import tool

def create_servicenow_tools(ae_client):
    """
    Creates Microsoft Agent Framework (@tool) tools for ServiceNow Incident Management
    with dual-sync: executes published AutomationEdge T4 workflows and synchronizes
    with ServiceNow Table API REST endpoint (https://dev347280.service-now.com).
    """
    create_workflow_name = os.environ.get("AE_WORKFLOW_CREATE_INCIDENT", "Servicenow_Incident_Creation")
    update_workflow_name = os.environ.get("AE_WORKFLOW_UPDATE_INCIDENT", "ServiceNow_Update_Incident")

    snow_url = os.environ.get("SERVICENOW_INSTANCE_URL", "https://dev347280.service-now.com").strip().rstrip("/")
    snow_user = os.environ.get("SERVICENOW_USERNAME", "admin").strip()
    snow_pass = os.environ.get("SERVICENOW_PASSWORD", "").strip()

    def _direct_snow_create(requester_email: str, short_desc: str, desc: str, cat: str) -> Optional[Dict[str, Any]]:
        if getattr(ae_client, "use_mock", False):
            return None
        if not (snow_url and snow_user and snow_pass and "dev0000" not in snow_url):
            return None
        try:
            api_url = f"{snow_url}/api/now/table/incident"
            payload = {
                "caller_id": requester_email,
                "short_description": short_desc,
                "description": desc or short_desc,
                "category": cat,
                "impact": "2",
                "urgency": "2",
                "contact_type": "virtual_agent",
                "work_notes": f"Incident created via Autonomous IT Service Desk for {requester_email}.\n\nUser Query: {desc or short_desc}"
            }
            req = urllib.request.Request(api_url, data=json.dumps(payload).encode("utf-8"), method="POST")
            auth_str = base64.b64encode(f"{snow_user}:{snow_pass}".encode("utf-8")).decode("utf-8")
            req.add_header("Authorization", f"Basic {auth_str}")
            req.add_header("Content-Type", "application/json")
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                result = data.get("result", {})
                if result.get("number"):
                    return {
                        "number": result.get("number"),
                        "sys_id": result.get("sys_id"),
                        "state": result.get("incident_state") or result.get("state")
                    }
        except Exception:
            pass
        return None

    def _direct_snow_update(target_identifier: str, state_val: str, close_notes: str, work_notes: str, resolution_code: str = "") -> bool:
        if getattr(ae_client, "use_mock", False):
            return True
        if not (snow_url and snow_user and snow_pass and target_identifier and "dev0000" not in snow_url):
            return False
        try:
            auth_str = base64.b64encode(f"{snow_user}:{snow_pass}".encode("utf-8")).decode("utf-8")
            actual_sys_id = target_identifier

            # If target is not a 32-char hex sys_id, lookup sys_id by incident number
            clean_ident = target_identifier.replace("sys_", "").strip()
            if len(clean_ident) != 32 or not all(c in "0123456789abcdefABCDEF" for c in clean_ident):
                try:
                    q_num = clean_ident if clean_ident.startswith("INC") else target_identifier
                    q_url = f"{snow_url}/api/now/table/incident?sysparm_query=number={q_num}&sysparm_limit=1"
                    q_req = urllib.request.Request(q_url, method="GET")
                    q_req.add_header("Authorization", f"Basic {auth_str}")
                    q_req.add_header("Accept", "application/json")
                    with urllib.request.urlopen(q_req, timeout=10) as q_resp:
                        q_data = json.loads(q_resp.read().decode("utf-8"))
                        results = q_data.get("result", [])
                        if results and results[0].get("sys_id"):
                            actual_sys_id = results[0]["sys_id"]
                except Exception:
                    pass
            else:
                actual_sys_id = clean_ident

            api_url = f"{snow_url}/api/now/table/incident/{actual_sys_id}"
            state_code = "7" if "complete" in state_val.lower() or "close" in state_val.lower() else ("6" if "resolve" in state_val.lower() else "2")
            
            # Map close code to valid ServiceNow Data Policy choices
            valid_close_code = "Solution provided"
            if "reject" in state_val.lower() or "reject" in resolution_code.lower():
                valid_close_code = "Resolved by caller"
            elif "workaround" in resolution_code.lower():
                valid_close_code = "Workaround provided"

            formatted_close_notes = close_notes or work_notes or f"Incident state updated to {state_val} by Autonomous IT Service Desk."
            formatted_work_notes = work_notes or formatted_close_notes

            payload = {
                "state": state_code,
                "incident_state": state_code,
                "close_code": valid_close_code,
                "close_notes": formatted_close_notes,
                "work_notes": formatted_work_notes,
                "comments": f"Autonomous IT Service Desk Resolution:\n\n{formatted_close_notes}"
            }
            req = urllib.request.Request(api_url, data=json.dumps(payload).encode("utf-8"), method="PATCH")
            req.add_header("Authorization", f"Basic {auth_str}")
            req.add_header("Content-Type", "application/json")
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status in [200, 204]
        except Exception as ex:
            return False

    @tool(
        name="create_incident",
        description="Calls the published 'Servicenow_Incident_Creation' workflow on AutomationEdge T4 and synchronizes with ServiceNow Table API."
    )
    def create_incident(requester_email: str, short_description: str, description: str, category: str, urgency: str = "Medium") -> Dict[str, Any]:
        # Required parameters for published AutomationEdge T4 Servicenow_Incident_Creation workflow
        params = {
            "ServiceNowDeveloperURL": snow_url,
            "Username_Servicenow": snow_user,
            "Password_Servicenow": snow_pass,
            "Caller": requester_email,
            "Caller_ID": requester_email,
            "Short_Description": short_description,
            "Description": description,
            "Category": category,
            "Impact": "2",
            "Urgency": "1" if urgency.lower() in ["high", "critical", "1"] else "2",
            "work_note": f"Incident created via Autonomous IT Service Desk for {requester_email}: {short_description}",
            "work_notes": f"Incident created via Autonomous IT Service Desk for {requester_email}: {short_description}"
        }
        
        # Execute published workflow on AutomationEdge T4 server
        res = ae_client.execute_workflow(create_workflow_name, params)
        resp = res.get("workflowResponse", {})
        if isinstance(resp, str):
            try:
                resp = json.loads(resp)
            except Exception:
                resp = {"output": resp}

        # Also sync directly to ensure ticket is visible in ServiceNow UI
        direct_info = _direct_snow_create(requester_email, short_description, description, category)

        # Extract ticket fields from AutomationEdge T4 workflow response and fallback to direct Table API
        ticket_id = (
            resp.get("RecordNumber") or
            resp.get("recordnumber") or
            resp.get("number") or
            resp.get("Incident_Number") or
            resp.get("incident_number") or
            resp.get("ticket_id") or
            resp.get("ticket_number") or
            (direct_info.get("number") if direct_info else None)
        )
        sys_id = (
            resp.get("SysID") or
            resp.get("sysid") or
            resp.get("SysId") or
            resp.get("sys_id") or
            resp.get("Sys_Id") or
            (direct_info.get("sys_id") if direct_info else None) or
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
            "source": "SERVICENOW_TABLE_API_AND_AE_T4",
            "raw_result": resp
        }

    @tool(
        name="update_incident",
        description="Calls the published 'ServiceNow_Update_Incident' workflow on AutomationEdge T4 and updates ServiceNow incident state."
    )
    def update_incident(ticket_id: str, state: str, resolution_code: str = "", work_notes: str = "", customer_summary: str = "", sys_id: str = "") -> Dict[str, Any]:
        target_sys_id = sys_id or ticket_id

        # Map state string to ServiceNow close state
        close_code_val = "Solution provided"
        if "reject" in state.lower() or "reject" in resolution_code.lower():
            close_code_val = "Resolved by caller"
        elif "workaround" in resolution_code.lower():
            close_code_val = "Workaround provided"

        # Determine clean state for AutomationEdge ServiceNow_Update_Incident workflow
        if any(c in state.lower() for c in ["close", "resolved", "complete", "7", "6"]):
            ae_state_val = "Closed"
        else:
            ae_state_val = "In Progress"

        close_note_val = customer_summary or work_notes or f"Updated state to {state}"

        # Parameters for published AutomationEdge T4 ServiceNow_Update_Incident workflow
        params = {
            "ServiceNowDeveloperURL": snow_url,
            "Username_Servicenow": snow_user,
            "Password_Servicenow": snow_pass,
            "SysId": target_sys_id,
            "state": ae_state_val,
            "close_code": close_code_val,
            "close_note": close_note_val,
            "work_note": work_notes or close_note_val
        }
        
        # Execute update workflow on AutomationEdge T4 server
        res = ae_client.execute_workflow(update_workflow_name, params)
        resp = res.get("workflowResponse", {})
        if isinstance(resp, str):
            try:
                resp = json.loads(resp)
            except Exception:
                resp = {"output": resp}

        # Also sync update directly via Table API if configured
        _direct_snow_update(target_sys_id, state, close_note_val, work_notes, resolution_code)

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
