import os
import json
import base64
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

class ServiceNowClient:
    """
    Direct ServiceNow Table API REST Client.
    Allows real-time creation, querying, and updating of Incident tickets in ServiceNow instances.
    Credentials and instance URL are loaded from environment variables (.env).
    """

    def __init__(self, instance_url: Optional[str] = None, username: Optional[str] = None, password: Optional[str] = None):
        self.instance_url = (instance_url or os.environ.get("SERVICENOW_INSTANCE_URL", "")).rstrip("/")
        self.username = username or os.environ.get("SERVICENOW_USERNAME", "")
        self.password = password or os.environ.get("SERVICENOW_PASSWORD", "")
        self._sys_id_cache = {}

    def is_configured(self) -> bool:
        """Checks whether valid ServiceNow live credentials are configured."""
        return bool(
            self.instance_url and
            self.username and
            self.password and
            "dev12345" not in self.instance_url and
            "your_servicenow" not in self.password
        )

    def _get_auth_header(self) -> str:
        raw = f"{self.username}:{self.password}".encode("utf-8")
        return f"Basic {base64.b64encode(raw).decode('utf-8')}"

    def create_incident(self, requester_email: str, short_description: str, description: str, 
                        category: str = "Hardware", urgency: str = "2", impact: str = "2",
                        extra_fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calls POST /api/now/table/incident to create an official incident ticket in ServiceNow.
        Returns the created record and maps all fields for LLM parameter extraction.
        """
        if not self.is_configured():
            # Return structured simulation payload
            import uuid
            ticket_num = f"INC-{uuid.uuid4().hex[:8].upper()}"
            sys_id = f"sys_{uuid.uuid4().hex[:16]}"
            return {
                "ticket_id": ticket_num,
                "number": ticket_num,
                "sys_id": sys_id,
                "state": "New",
                "short_description": short_description,
                "description": description,
                "category": category,
                "requester_email": requester_email,
                "source": "SIMULATED_SERVICENOW_STORE",
                "raw_result": {
                    "sys_id": sys_id,
                    "number": ticket_num,
                    "short_description": short_description,
                    "state": "1"
                }
            }

        endpoint = f"{self.instance_url}/api/now/table/incident"
        payload = {
            "short_description": short_description,
            "description": description,
            "category": category.lower(),
            "urgency": str(urgency),
            "impact": str(impact),
            "contact_type": "virtual_agent",
            "comments": f"Opened by Autonomous IT Virtual Agent on behalf of {requester_email}"
        }
        if extra_fields:
            payload.update(extra_fields)

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": self._get_auth_header(),
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result = data.get("result", {})
            ticket_id = result.get("number", "")
            sys_id = result.get("sys_id", "")
            if ticket_id and sys_id:
                self._sys_id_cache[ticket_id] = sys_id

            return {
                "ticket_id": ticket_id,
                "number": ticket_id,
                "sys_id": sys_id,
                "state": result.get("state", "1"),
                "short_description": result.get("short_description", short_description),
                "category": result.get("category", category),
                "sys_created_on": result.get("sys_created_on", ""),
                "caller_id": result.get("caller_id", {}).get("value", requester_email) if isinstance(result.get("caller_id"), dict) else result.get("caller_id", requester_email),
                "source": "LIVE_SERVICENOW_REST_API",
                "raw_result": result
            }

    def get_sys_id_by_ticket_number(self, ticket_number: str) -> Optional[str]:
        """Resolves the 32-char sys_id for a given incident ticket number (e.g. INC0010001)."""
        if ticket_number in self._sys_id_cache:
            return self._sys_id_cache[ticket_number]

        if not self.is_configured():
            return None

        endpoint = f"{self.instance_url}/api/now/table/incident?sysparm_query=number={ticket_number}&sysparm_limit=1"
        req = urllib.request.Request(
            endpoint,
            headers={
                "Authorization": self._get_auth_header(),
                "Accept": "application/json"
            },
            method="GET"
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("result", [])
            if results:
                sys_id = results[0].get("sys_id")
                if sys_id:
                    self._sys_id_cache[ticket_number] = sys_id
                    return sys_id
        return None

    def update_incident(self, ticket_id: str, state: str, resolution_code: str = "",
                        work_notes: str = "", customer_summary: str = "") -> Dict[str, Any]:
        """
        Calls PATCH /api/now/table/incident/{sys_id} to update ticket state, work notes, and close notes.
        """
        if not self.is_configured():
            return {
                "ticket_id": ticket_id,
                "state": state,
                "resolution_code": resolution_code,
                "work_notes": work_notes,
                "customer_summary": customer_summary,
                "source": "SIMULATED_SERVICENOW_STORE",
                "status": "UPDATED"
            }

        sys_id = self.get_sys_id_by_ticket_number(ticket_id) or ticket_id
        endpoint = f"{self.instance_url}/api/now/table/incident/{sys_id}"

        # ServiceNow standard state mapping:
        # 1: New, 2: In Progress, 3: On Hold, 6: Resolved, 7: Closed, 8: Canceled
        state_code_map = {
            "New": "1",
            "In Progress": "2",
            "Pending Approval": "3",
            "On Hold": "3",
            "Resolved": "6",
            "Closed Complete": "7",
            "Closed": "7",
            "Closed Rejected": "8",
            "Rejected": "8"
        }
        snow_state = state_code_map.get(state, "2")

        payload = {
            "state": snow_state
        }
        if work_notes:
            payload["work_notes"] = work_notes
        if customer_summary:
            payload["comments"] = customer_summary
        if resolution_code:
            payload["close_code"] = resolution_code
            payload["close_notes"] = customer_summary or f"Resolved with code: {resolution_code}"

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": self._get_auth_header(),
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            method="PATCH"
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result = data.get("result", {})
            return {
                "ticket_id": ticket_id,
                "sys_id": sys_id,
                "state": result.get("state", snow_state),
                "source": "LIVE_SERVICENOW_REST_API",
                "raw_result": result
            }
