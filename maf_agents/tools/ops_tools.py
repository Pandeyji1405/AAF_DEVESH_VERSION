from typing import Dict, Any, List
from agent_framework import tool

def create_ops_tools(ae_client):
    """
    Creates Microsoft Agent Framework (@tool) tools for Onboarding, SecOps, RMM Copilot, and Infrastructure Operations.
    """

    # ── Onboarding Tools ──
    @tool(
        name="deploy_package",
        description="Deploys standardized enterprise software packages to a newly provisioned endpoint."
    )
    def deploy_package(agent_id: str, package_bundle: str, ticket_id: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Package_Deployer_Workflow", {
            "agent_id": agent_id,
            "package_bundle": package_bundle,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="configure_local_policies",
        description="Enforces local security policies, baseline firewall, and auditing rules on an endpoint."
    )
    def configure_local_policies(agent_id: str, policy_set: str, ticket_id: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Configure_Local_Policies_Workflow", {
            "agent_id": agent_id,
            "policy_set": policy_set,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="send_welcome_kit",
        description="Dispatches credentials, onboarding guide, and IT welcome kit to new employee."
    )
    def send_welcome_kit(user_email: str, recipient_name: str, ticket_id: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Send_Welcome_Kit_Workflow", {
            "user_email": user_email,
            "recipient_name": recipient_name,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    # ── SecOps Tools ──
    @tool(
        name="isolate_endpoint",
        description="Isolates a compromised endpoint from the network while maintaining RMM management channel."
    )
    def isolate_endpoint(agent_id: str, reason: str, ticket_id: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Isolate_Endpoint_Workflow", {
            "agent_id": agent_id,
            "reason": reason,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="extract_memory_forensics",
        description="Captures live memory triage, volatile process list, and forensic snapshot."
    )
    def extract_memory_forensics(agent_id: str, case_id: str, ticket_id: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Extract_Memory_Forensics_Workflow", {
            "agent_id": agent_id,
            "case_id": case_id,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="update_siem_ticket",
        description="Updates SIEM / EDR security incident ticket with containment and forensic evidence."
    )
    def update_siem_ticket(alert_id: str, status: str, notes: str, ticket_id: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Update_SIEM_Ticket_Workflow", {
            "alert_id": alert_id,
            "status": status,
            "notes": notes,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    # ── RMM Copilot Tools ──
    @tool(
        name="query_endpoints",
        description="Executes cross-fleet query across all TacticalRMM endpoints matching criteria."
    )
    def query_endpoints(query_filter: str) -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_RMM_Query_Bot", {
            "query_filter": query_filter
        })
        return res.get("workflowResponse", {})

    @tool(
        name="batch_execute",
        description="Executes a verified script or command batch across multiple targeted endpoints."
    )
    def batch_execute(target_agent_ids: str, script_name: str, ticket_id: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Batch_Script_Runner_Workflow", {
            "target_agent_ids": target_agent_ids,
            "script_name": script_name,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="stream_execution_status",
        description="Streams real-time batch execution status and summary stats across agent nodes."
    )
    def stream_execution_status(batch_id: str) -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Stream_Execution_Status_Workflow", {
            "batch_id": batch_id
        })
        return res.get("workflowResponse", {})

    # ── Infra Ops Tools ──
    @tool(
        name="collect_process_dump",
        description="Generates memory crash dump of w3wp or target server application pool process for root cause analysis."
    )
    def collect_process_dump(host_id: str, process_name: str = "w3wp.exe", ticket_id: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Collect_Process_Dump_Bot", {
            "host_id": host_id,
            "process_name": process_name,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="restart_app_pool",
        description="Recycles or restarts a crashed IIS application pool on an enterprise server."
    )
    def restart_app_pool(host_id: str, app_pool_name: str, ticket_id: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Restart_AppPool_Workflow", {
            "host_id": host_id,
            "app_pool_name": app_pool_name,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="http_health_check",
        description="Performs HTTP endpoint health check, verifies status code 200 and latency."
    )
    def http_health_check(endpoint_url: str) -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Http_Health_Check_Workflow", {
            "endpoint_url": endpoint_url
        })
        return res.get("workflowResponse", {})

    @tool(
        name="scan_db_directory",
        description="Scans database host storage directories and returns SQL log/data file sizes and free disk space."
    )
    def scan_db_directory(host_id: str, db_name: str = "ProductionDB") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Scan_DB_Directory_Bot", {
            "host_id": host_id,
            "db_name": db_name
        })
        return res.get("workflowResponse", {})

    @tool(
        name="backup_sql_logs",
        description="Performs point-in-time backup of SQL transaction logs to backup storage."
    )
    def backup_sql_logs(host_id: str, db_name: str, ticket_id: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Backup_SQL_Logs_Workflow", {
            "host_id": host_id,
            "db_name": db_name,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="truncate_sql_logs",
        description="Truncates inactive virtual log files (VLF) to reclaim critical disk space (Mandatory Lead-DBA Approval)."
    )
    def truncate_sql_logs(host_id: str, db_name: str, ticket_id: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Truncate_SQL_Logs_Workflow", {
            "host_id": host_id,
            "db_name": db_name,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    return [
        deploy_package,
        configure_local_policies,
        send_welcome_kit,
        isolate_endpoint,
        extract_memory_forensics,
        update_siem_ticket,
        query_endpoints,
        batch_execute,
        stream_execution_status,
        collect_process_dump,
        restart_app_pool,
        http_health_check,
        scan_db_directory,
        backup_sql_logs,
        truncate_sql_logs
    ]
