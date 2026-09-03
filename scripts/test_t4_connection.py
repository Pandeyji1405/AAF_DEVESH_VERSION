import os
import sys
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()

from automationedge.client import AutomationEdgeClient

def main():
    print("="*80)
    print("🌐 AUTOMATIONEDGE T4 SERVER REST API DIAGNOSTIC")
    print("="*80)
    
    base_url = os.environ.get("AE_BASE_URL", "https://t4.automationedge.com")
    username = os.environ.get("AE_USERNAME", "")
    password = os.environ.get("AE_PASSWORD", "")
    org_code = os.environ.get("AE_ORG_CODE", "DEFAULT")

    print(f"• Target Server URL : {base_url}")
    print(f"• Organization Code : {org_code}")
    print(f"• Configured User   : {username}")
    print(f"• Password Set      : {'YES' if password and 'your_t4' not in password else 'NO (Placeholder detected)'}")
    print("="*80)

    if not username or not password or "your_t4" in username or "your_t4" in password:
        print("\n❌ Error: Real AutomationEdge T4 credentials are missing in .env.")
        print("Please update .env with your real username and password:")
        print("  AE_USERNAME=<your_username>")
        print("  AE_PASSWORD=<your_password>")
        print("  AE_ORG_CODE=<your_org_code_or_DEFAULT>")
        return

    print("\n1. Testing Authentication against T4 Endpoints:")
    client = AutomationEdgeClient(
        base_url=base_url,
        username=username,
        password=password,
        org_code=org_code,
        use_mock=False
    )

    try:
        token = client.get_token()
        print(f"  ✅ Authentication Successful! Received Session Token: {token[:12]}...")
    except Exception as e:
        print(f"  ❌ Authentication Failed: {e}")
        return

    print("\n2. Testing Workflow Execution on AutomationEdge T4:")
    create_wf = os.environ.get("AE_WORKFLOW_CREATE_INCIDENT", "Servicenow_Incident_Creation")
    print(f"• Triggering published workflow: {create_wf}")

    snow_url = os.environ.get("SERVICENOW_INSTANCE_URL", "https://dev00000.service-now.com")
    snow_user = os.environ.get("SERVICENOW_USERNAME", "admin")
    snow_pass = os.environ.get("SERVICENOW_PASSWORD", "")

    sample_params = {
        "ServiceNowDeveloperURL": snow_url,
        "Username_Servicenow": snow_user,
        "Password_Servicenow": snow_pass,
        "Caller": "alex.murphy@enterprise.com",
        "Short_Description": "T4 Live Diagnostic Test Incident",
        "Description": "Verification of real AutomationEdge T4 workflow execution.",
        "Impact": "2",
        "Urgency": "2",
        "work_note": "Initiated by Autonomous IT Virtual Agent"
    }

    try:
        res = client.execute_workflow(create_wf, sample_params, timeout_seconds=60)
        print(f"  ✅ Workflow Execution Finished!")
        print(f"  • Automation Request ID: {res.get('automationRequestId')} (Check T4 'Requests' tab)")
        print(f"  • Status               : {res.get('status')}")
        print(f"  • Output Response      : {json.dumps(res.get('workflowResponse', {}), indent=2)}")
    except Exception as e:
        print(f"  ❌ Workflow Execution Error: {e}")

if __name__ == "__main__":
    main()
