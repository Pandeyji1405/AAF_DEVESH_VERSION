import os
import time
import json
import uuid
import socket
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

# DNS Fallback for AutomationEdge Cloud ALB
_orig_getaddrinfo = socket.getaddrinfo
def _t4_custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    try:
        return _orig_getaddrinfo(host, port, family, type, proto, flags)
    except Exception:
        if "t4.automationedge.com" in host:
            return _orig_getaddrinfo("13.201.160.54", port, family, type, proto, flags)
        raise
socket.getaddrinfo = _t4_custom_getaddrinfo

class AutomationEdgeClient:
    """
    Production AutomationEdge T4 Enterprise REST Client.
    Executes workflows against real AutomationEdge servers.
    Mock engine fallback is strictly forbidden on live paths; only explicit tests (use_mock=True) may use mock engine.
    """
    def __init__(self, base_url: Optional[str] = None, username: Optional[str] = None, 
                 password: Optional[str] = None, org_code: Optional[str] = None, 
                 execution_user: Optional[str] = None, use_mock: bool = False):
        
        self.base_url = (base_url or os.environ.get("AE_BASE_URL", "https://t4.automationedge.com")).rstrip("/")
        self.username = username or os.environ.get("AE_USERNAME", "")
        self.password = password or os.environ.get("AE_PASSWORD", "")
        self.org_code = org_code or os.environ.get("AE_ORG_CODE", "US_MSP")
        self.execution_user = execution_user or os.environ.get("AE_EXECUTION_USER", self.username)
        
        credentials_present = bool(self.base_url and self.username and self.password and self.org_code)
        
        if use_mock:
            self.use_mock = True  # Only reachable when a unit/integration test explicitly passes use_mock=True
            from automationedge.mock_engine import MockAutomationEdgeEngine
            self.mock_engine = MockAutomationEdgeEngine()
        elif not credentials_present:
            raise RuntimeError(
                "AutomationEdge credentials are missing (AE_BASE_URL/AE_USERNAME/AE_PASSWORD/AE_ORG_CODE). "
                "Refusing to start — this build does not run on silent mock data. "
                "Configure live credentials in .env or pass explicit use_mock=True for test harnesses."
            )
        else:
            self.use_mock = False
            self.mock_engine = None
        
        self.token = None
        self.token_expiry = 0

    def get_token(self) -> str:
        """Authenticate with AutomationEdge T4 and cache session token."""
        if self.use_mock:
            return "mock-session-token-12345"

        if self.token and time.time() < self.token_expiry:
            return self.token
        
        # Try standard T4 REST endpoints
        auth_endpoints = [
            f"{self.base_url}/aeengine/rest/authenticate",
            f"{self.base_url}/t4/api/authenticate",
            f"{self.base_url}/t4/api/v1/sessions"
        ]
        
        last_err = None
        for auth_url in auth_endpoints:
            try:
                # Try JSON payload first
                json_data = json.dumps({
                    "username": self.username,
                    "password": self.password,
                    "orgCode": self.org_code
                }).encode("utf-8")
                req = urllib.request.Request(auth_url, data=json_data, method="POST")
                req.add_header("Content-Type", "application/json")
                req.add_header("Accept", "application/json")

                with urllib.request.urlopen(req, timeout=15) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                    self.token = body.get("sessionToken") or body.get("token") or body.get("sessionId")
                    if self.token:
                        self.token_expiry = time.time() + (20 * 60)
                        return self.token
            except Exception as e:
                # Try urlencoded form payload
                try:
                    data = urllib.parse.urlencode({
                        "username": self.username,
                        "password": self.password,
                        "orgCode": self.org_code
                    }).encode("utf-8")
                    req = urllib.request.Request(auth_url, data=data, method="POST")
                    req.add_header("Content-Type", "application/x-www-form-urlencoded")
                    req.add_header("Accept", "application/json")

                    with urllib.request.urlopen(req, timeout=15) as resp:
                        body = json.loads(resp.read().decode("utf-8"))
                        self.token = body.get("sessionToken") or body.get("token")
                        if self.token:
                            self.token_expiry = time.time() + (20 * 60)
                            return self.token
                except Exception as ex:
                    last_err = ex

        raise ConnectionError(f"Failed to authenticate with AutomationEdge T4 server at {self.base_url}: {last_err}")

    def execute_workflow(self, workflow_name: str, parameters: Dict[str, Any], timeout_seconds: int = 60) -> Dict[str, Any]:
        """
        Submits a workflow execution request to AutomationEdge and polls until complete.
        All requests log under the 'Requests' tab on your AutomationEdge T4 portal.
        """
        if self.use_mock:
            return self.mock_engine.execute(workflow_name, parameters)

        # ── REAL LIVE AUTOMATIONEDGE T4 REST API CALL ──
        token = self.get_token()
        execute_url = f"{self.base_url}/aeengine/rest/execute"
        
        formatted_params = [
            {
                "name": k,
                "displayName": k,
                "value": str(v),
                "type": "String",
                "order": idx,
                "optional": False,
                "secret": any(s in k.lower() for s in ["pass", "token", "secret", "key"])
            }
            for idx, (k, v) in enumerate(parameters.items(), start=1)
        ]
        
        body = {
            "orgCode": self.org_code,
            "workflowName": workflow_name,
            "userId": self.execution_user,
            "source": "MAF_AGENT_FRAMEWORK",
            "sourceId": str(uuid.uuid4()),
            "params": formatted_params
        }
        
        req = urllib.request.Request(execute_url, data=json.dumps(body).encode("utf-8"), method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        req.add_header("X-session-token", token)
        
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                exec_resp = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            # Try alternate T4 v1 execution endpoint
            alt_url = f"{self.base_url}/t4/api/v1/requests"
            req_alt = urllib.request.Request(alt_url, data=json.dumps(body).encode("utf-8"), method="POST")
            req_alt.add_header("Content-Type", "application/json")
            req_alt.add_header("Accept", "application/json")
            req_alt.add_header("X-session-token", token)
            with urllib.request.urlopen(req_alt, timeout=20) as resp:
                exec_resp = json.loads(resp.read().decode("utf-8"))
            
        request_id = exec_resp.get("automationRequestId") or exec_resp.get("requestId")
        if not request_id:
            return {"status": "FAILED", "error": "No requestId returned by AutomationEdge", "raw": exec_resp}
            
        # Polling status in AutomationEdge Requests tab
        poll_urls = [
            f"{self.base_url}/aeengine/rest/workflowinstances/{request_id}",
            f"{self.base_url}/t4/api/v1/requests/{request_id}"
        ]
        
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            time.sleep(2.0)
            instance_data = None
            for p_url in poll_urls:
                try:
                    poll_req = urllib.request.Request(p_url, method="GET")
                    poll_req.add_header("X-session-token", self.get_token())
                    poll_req.add_header("Accept", "application/json")
                    with urllib.request.urlopen(poll_req, timeout=15) as poll_resp:
                        instance_data = json.loads(poll_resp.read().decode("utf-8"))
                        break
                except Exception:
                    pass

            if not instance_data:
                continue
                
            status = instance_data.get("status")
            if status in ["Complete", "Failure", "Cancelled"]:
                wf_resp = instance_data.get("workflowResponse")
                merged_resp = {}
                if isinstance(wf_resp, dict):
                    merged_resp.update(wf_resp)
                elif isinstance(wf_resp, str):
                    try:
                        merged_resp.update(json.loads(wf_resp))
                    except Exception:
                        merged_resp["output"] = wf_resp

                out_params = instance_data.get("outputParameters")
                if isinstance(out_params, list):
                    for p in out_params:
                        if isinstance(p, dict) and "name" in p:
                            merged_resp[p["name"]] = p.get("value")
                elif isinstance(out_params, dict):
                    merged_resp.update(out_params)

                return {
                    "workflowName": workflow_name,
                    "automationRequestId": request_id,
                    "status": status,
                    "message": instance_data.get("message"),
                    "workflowResponse": merged_resp,
                    "raw": instance_data
                }
                
        return {"status": "TIMEOUT", "error": f"Workflow exceeded timeout of {timeout_seconds}s", "automationRequestId": request_id}
