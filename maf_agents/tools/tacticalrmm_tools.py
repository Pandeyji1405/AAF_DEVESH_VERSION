from typing import Dict, Any, List
from agent_framework import tool

def create_tacticalrmm_tools(ae_client):
    """
    Creates Microsoft Agent Framework (@tool) tools for TacticalRMM Endpoint Operations.
    """

    @tool(
        name="get_endpoint_metrics",
        description="Queries real-time hardware telemetry, CPU, RAM, disk, and agent checks from TacticalRMM."
    )
    def get_endpoint_metrics(agent_id: str) -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Get_Endpoint_Metrics_Bot", {
            "agent_id": agent_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="kill_process",
        description="Terminates an unresponsive or rogue process on a TacticalRMM managed endpoint."
    )
    def kill_process(agent_id: str, pid_or_name: str, ticket_id: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Kill_Process_Workflow", {
            "agent_id": agent_id,
            "pid_or_name": pid_or_name,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="restart_service",
        description="Restarts a Windows or Linux system service via TacticalRMM."
    )
    def restart_service(agent_id: str, service_name: str, ticket_id: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Restart_Service_Workflow", {
            "agent_id": agent_id,
            "service_name": service_name,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="fetch_patch_package",
        description="Fetches and validates the remediation patch package metadata for a CVE or software release."
    )
    def fetch_patch_package(cve_id_or_patch_name: str) -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Fetch_Patch_Package_Bot", {
            "cve_id_or_patch_name": cve_id_or_patch_name
        })
        return res.get("workflowResponse", {})

    @tool(
        name="execute_patch",
        description="Applies an approved patch or hotfix via TacticalRMM script execution."
    )
    def execute_patch(agent_id: str, patch_id: str, ticket_id: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Execute_TacticalRMM_Patch_Workflow", {
            "agent_id": agent_id,
            "patch_id": patch_id,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="verify_software_version",
        description="Verifies installed software version on an endpoint after patch execution."
    )
    def verify_software_version(agent_id: str, package_name: str) -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Verify_Software_Version_Workflow", {
            "agent_id": agent_id,
            "package_name": package_name
        })
        return res.get("workflowResponse", {})

    @tool(
        name="scan_disk_usage",
        description="Runs diagnostic scanner across drives to identify large files, temp directories, and storage hogs."
    )
    def scan_disk_usage(agent_id: str) -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Disk_Usage_Scanner_Bot", {
            "agent_id": agent_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="safe_temp_cleanup",
        description="Safely purges temporary directories, recycle bin, and stale caches."
    )
    def safe_temp_cleanup(agent_id: str, ticket_id: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Safe_Temp_Cleanup_Workflow", {
            "agent_id": agent_id,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="archive_user_folder",
        description="Compresses and archives large user directories to cold storage with confirmation."
    )
    def archive_user_folder(agent_id: str, folder_path: str, ticket_id: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Archive_User_Folder_Workflow", {
            "agent_id": agent_id,
            "folder_path": folder_path,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="network_diagnostics",
        description="Runs network connectivity, latency, gateway ping, and DNS resolution diagnostics."
    )
    def network_diagnostics(agent_id: str) -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Endpoint_Network_Diag_Bot", {
            "agent_id": agent_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="restart_vpn_daemon",
        description="Restarts the endpoint VPN client daemon and re-establishes corporate tunnel."
    )
    def restart_vpn_daemon(agent_id: str, ticket_id: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Restart_VPN_Daemon_Workflow", {
            "agent_id": agent_id,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="flush_dns_test_ping",
        description="Flushes local DNS resolver cache, resets adapter stack, and executes ping check."
    )
    def flush_dns_test_ping(agent_id: str, target_host: str = "enterprise.local") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_Flush_DNS_Test_Ping_Workflow", {
            "agent_id": agent_id,
            "target_host": target_host
        })
        return res.get("workflowResponse", {})

    @tool(
        name="run_compliance_check_script",
        description="Executes TacticalRMM compliance audit script (disk encryption, patch level, AV status)."
    )
    def run_compliance_check_script(agent_id: str) -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_DEV_021_RunComplianceCheckScript", {
            "agent_id": agent_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="apply_remediation_script",
        description="Runs the targeted fix script for a failed TacticalRMM check."
    )
    def apply_remediation_script(agent_id: str, check_name: str, ticket_id: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_DEV_022_ApplyRemediationScript", {
            "agent_id": agent_id,
            "check_name": check_name,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="restart_device",
        description="Sends a remote restart script execution command to an endpoint via TacticalRMM."
    )
    def restart_device(agent_id: str, force_reboot: bool = True, ticket_id: str = "") -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_DEV_011_RestartDevice", {
            "agent_id": agent_id,
            "force_reboot": str(force_reboot).lower(),
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    @tool(
        name="get_bitlocker_recovery_key",
        description="Retrieves the 48-digit BitLocker volume encryption recovery key from Microsoft Graph Key Vault."
    )
    def get_bitlocker_recovery_key(device_id: str, requester_upn: str, ticket_id: str) -> Dict[str, Any]:
        res = ae_client.execute_workflow("AE_DEV_002_GetBitLockerKey", {
            "device_id": device_id,
            "requester_upn": requester_upn,
            "ticket_id": ticket_id
        })
        return res.get("workflowResponse", {})

    return [
        get_endpoint_metrics,
        kill_process,
        restart_service,
        fetch_patch_package,
        execute_patch,
        verify_software_version,
        scan_disk_usage,
        safe_temp_cleanup,
        archive_user_folder,
        network_diagnostics,
        restart_vpn_daemon,
        flush_dns_test_ping,
        run_compliance_check_script,
        apply_remediation_script,
        restart_device,
        get_bitlocker_recovery_key
    ]
