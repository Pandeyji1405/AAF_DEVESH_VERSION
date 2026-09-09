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
        description="Sends a remote restart script execution command to an endpoint via TacticalRMM with elevated Administrator (SYSTEM) privileges."
    )
    def restart_device(agent_id: str = "zAltxZhbdHrygGpGRhnwqGSbOLSHozfDAZOTntXu", hostname: str = "Apoorva", force_reboot: bool = True, ticket_id: str = "") -> Dict[str, Any]:
        reboot_cmd = 'shutdown /r /t 5 /f /c "Automated IT Service Desk remote restart initiated via Tactical RMM"'
        trmm_res = execute_tactical_command(
            command=reboot_cmd,
            hostname=hostname,
            run_as_user="false",
            ticket_id=ticket_id
        )
        ae_res = ae_client.execute_workflow("AE_DEV_011_RestartDevice", {
            "agent_id": agent_id,
            "force_reboot": str(force_reboot).lower(),
            "ticket_id": ticket_id
        })
        merged = {}
        if isinstance(ae_res, dict):
            merged.update(ae_res.get("workflowResponse", ae_res))
        if isinstance(trmm_res, dict):
            merged.update(trmm_res)
        merged["reboot_dispatched"] = True
        merged["run_as_user"] = "false"
        merged["command"] = reboot_cmd
        return merged

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

    @tool(
        name="execute_tactical_command",
        description="Executes a live PowerShell or shell command on an endpoint via Tactical RMM AutomationEdge workflow (Get_Agent_Run_Cmd), automatically choosing Administrator (SYSTEM) or Standard User context based on command safety and requirements."
    )
    def execute_tactical_command(
        command: str = "whoami",
        hostname: str = "Apoorva",
        run_as_user: Any = None,
        shell: str = "powershell",
        timeout: str = "30",
        ticket_id: str = ""
    ) -> Dict[str, Any]:
        import os
        from core.privilege_manager import PrivilegeClassifier, ExecutionPrivilege
        
        token = os.environ.get("TACTICAL_RMM_API_KEY", "859IXUFIGD76Z5J3ET18IT8YTD7PFHYG")
        ngrok_url = os.environ.get("TACTICAL_RMM_BASE_URL", "https://wish-aim-tall.ngrok-free.dev")
        wf_name = os.environ.get("AE_WORKFLOW_TRMM_CMD", "Get_Agent_Run_Cmd")
        
        # Smart Privilege Resolution: classify automatically if not provided or enforce admin if required
        if run_as_user is None or str(run_as_user).lower() in ["auto", "none", ""]:
            effective_run_as_user = PrivilegeClassifier.get_run_as_user_flag(command)
        else:
            priv, _ = PrivilegeClassifier.classify_command(command)
            if priv == ExecutionPrivilege.ADMINISTRATOR and str(run_as_user).lower() == "true":
                effective_run_as_user = "false"  # Promote to admin
            else:
                effective_run_as_user = str(run_as_user).lower()
        
        params = {
            "P_TacticalToken": token,
            "P_NgrokURL": ngrok_url,
            "P_Hostname": hostname,
            "P_Command": command,
            "P_RunAsUser": effective_run_as_user,
            "P_Shell": shell,
            "P_Timeout": str(timeout)
        }
        res = ae_client.execute_workflow(wf_name, params)
        wf_resp = res.get("workflowResponse", {})
        if not wf_resp:
            wf_resp = res
        if isinstance(wf_resp, dict):
            wf_resp.setdefault("command", command)
            wf_resp.setdefault("hostname", hostname)
            wf_resp.setdefault("run_as_user", effective_run_as_user)
            wf_resp.setdefault("workflow_name", wf_name)
        return wf_resp

    @tool(
        name="get_ip_config",
        description="Executes 'ipconfig /all' on target device via Tactical RMM AutomationEdge workflow (run as user) to retrieve live IP and network configuration."
    )
    def get_ip_config(hostname: str = "Apoorva", ticket_id: str = "") -> Dict[str, Any]:
        return execute_tactical_command(command="ipconfig /all", hostname=hostname, ticket_id=ticket_id)

    @tool(
        name="get_high_cpu_processes",
        description="Queries top CPU consuming processes and diagnostics on target endpoint via Tactical RMM (run as user)."
    )
    def get_high_cpu_processes(hostname: str = "Apoorva", ticket_id: str = "") -> Dict[str, Any]:
        cmd = "Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 -Property Id, ProcessName, CPU, WorkingSet64 | Format-Table -AutoSize | Out-String"
        return execute_tactical_command(command=cmd, hostname=hostname, ticket_id=ticket_id)

    @tool(
        name="get_machine_summary",
        description="Retrieves comprehensive hardware, OS, CPU, RAM, and disk summary for the target agent machine via Tactical RMM AutomationEdge workflow (Get_Machine_Summary)."
    )
    def get_machine_summary(hostname: str = "Apoorva", ticket_id: str = "") -> Dict[str, Any]:
        import os
        token = os.environ.get("TACTICAL_RMM_API_KEY", "859IXUFIGD76Z5J3ET18IT8YTD7PFHYG")
        ngrok_url = os.environ.get("TACTICAL_RMM_BASE_URL", "https://wish-aim-tall.ngrok-free.dev")
        wf_name = os.environ.get("AE_WORKFLOW_TRMM_MACHINE_SUMMARY", "Get_Machine_Summary")
        params = {
            "P_TacticalToken": token,
            "P_NgrokURL": ngrok_url,
            "P_Hostname": hostname
        }
        res = ae_client.execute_workflow(wf_name, params)
        wf_resp = res.get("workflowResponse", {}) if isinstance(res, dict) else {}
        if not wf_resp and isinstance(res, dict):
            wf_resp = res
        if isinstance(wf_resp, dict):
            wf_resp.setdefault("hostname", hostname)
            wf_resp.setdefault("workflow_name", wf_name)
        return wf_resp

    @tool(
        name="get_agents_list",
        description="Retrieves the list and status of all agents currently running and connected on the Tactical RMM server via AutomationEdge workflow (Get_Agents_List)."
    )
    def get_agents_list(ticket_id: str = "") -> Dict[str, Any]:
        import os
        token = os.environ.get("TACTICAL_RMM_API_KEY", "859IXUFIGD76Z5J3ET18IT8YTD7PFHYG")
        ngrok_url = os.environ.get("TACTICAL_RMM_BASE_URL", "https://wish-aim-tall.ngrok-free.dev")
        wf_name = os.environ.get("AE_WORKFLOW_TRMM_AGENTS_LIST", "Get_Agents_List")
        params = {
            "P_TacticalToken": token,
            "P_NgrokURL": ngrok_url
        }
        res = ae_client.execute_workflow(wf_name, params)
        wf_resp = res.get("workflowResponse", {}) if isinstance(res, dict) else {}
        if not wf_resp and isinstance(res, dict):
            wf_resp = res
        if isinstance(wf_resp, dict):
            wf_resp.setdefault("workflow_name", wf_name)
        return wf_resp

    @tool(
        name="get_software_list",
        description="Retrieves the inventory of installed software on the agent machine via Tactical RMM AutomationEdge workflow (Get_Software_List)."
    )
    def get_software_list(hostname: str = "Apoorva", ticket_id: str = "") -> Dict[str, Any]:
        import os
        token = os.environ.get("TACTICAL_RMM_API_KEY", "859IXUFIGD76Z5J3ET18IT8YTD7PFHYG")
        ngrok_url = os.environ.get("TACTICAL_RMM_BASE_URL", "https://wish-aim-tall.ngrok-free.dev")
        wf_name = os.environ.get("AE_WORKFLOW_TRMM_SOFTWARE_LIST", "Get_Software_List")
        params = {
            "P_TacticalToken": token,
            "P_NgrokURL": ngrok_url,
            "P_Hostname": hostname
        }
        res = ae_client.execute_workflow(wf_name, params)
        wf_resp = res.get("workflowResponse", {}) if isinstance(res, dict) else {}
        if not wf_resp and isinstance(res, dict):
            wf_resp = res
        if isinstance(wf_resp, dict):
            wf_resp.setdefault("hostname", hostname)
            wf_resp.setdefault("workflow_name", wf_name)
        return wf_resp

    @tool(
        name="get_windows_patches",
        description="Retrieves Windows updates and patch status for the respective agent machine via Tactical RMM AutomationEdge workflow (Get_Windows_Patches)."
    )
    def get_windows_patches(hostname: str = "Apoorva", ticket_id: str = "") -> Dict[str, Any]:
        import os
        token = os.environ.get("TACTICAL_RMM_API_KEY", "859IXUFIGD76Z5J3ET18IT8YTD7PFHYG")
        ngrok_url = os.environ.get("TACTICAL_RMM_BASE_URL", "https://wish-aim-tall.ngrok-free.dev")
        wf_name = os.environ.get("AE_WORKFLOW_TRMM_WINDOWS_PATCHES", "Get_Windows_Patches")
        params = {
            "P_TacticalToken": token,
            "P_NgrokURL": ngrok_url,
            "P_Hostname": hostname
        }
        res = ae_client.execute_workflow(wf_name, params)
        wf_resp = res.get("workflowResponse", {}) if isinstance(res, dict) else {}
        if not wf_resp and isinstance(res, dict):
            wf_resp = res
        if isinstance(wf_resp, dict):
            wf_resp.setdefault("hostname", hostname)
            wf_resp.setdefault("workflow_name", wf_name)
        return wf_resp

    @tool(
        name="install_software",
        description="Installs specified software on the agent machine via Tactical RMM AutomationEdge workflow (Software_Installation) under Administrator (SYSTEM) context."
    )
    def install_software(software_name: str, hostname: str = "Apoorva", ticket_id: str = "") -> Dict[str, Any]:
        import os
        token = os.environ.get("TACTICAL_RMM_API_KEY", "859IXUFIGD76Z5J3ET18IT8YTD7PFHYG")
        ngrok_url = os.environ.get("TACTICAL_RMM_BASE_URL", "https://wish-aim-tall.ngrok-free.dev")
        wf_name = os.environ.get("AE_WORKFLOW_TRMM_SOFTWARE_INSTALL", "Software_Installation")
        params = {
            "P_TacticalToken": token,
            "P_NgrokURL": ngrok_url,
            "P_Hostname": hostname,
            "P_SoftwareName": software_name
        }
        res = ae_client.execute_workflow(wf_name, params)
        wf_resp = res.get("workflowResponse", {}) if isinstance(res, dict) else {}
        if not wf_resp and isinstance(res, dict):
            wf_resp = res
        if isinstance(wf_resp, dict):
            wf_resp.setdefault("hostname", hostname)
            wf_resp.setdefault("software_name", software_name)
            wf_resp.setdefault("workflow_name", wf_name)
        return wf_resp

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
        get_bitlocker_recovery_key,
        execute_tactical_command,
        get_ip_config,
        get_high_cpu_processes,
        get_machine_summary,
        get_agents_list,
        get_software_list,
        get_windows_patches,
        install_software
    ]

