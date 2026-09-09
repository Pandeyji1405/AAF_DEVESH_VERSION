import json
import os
import uuid
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class MockAutomationEdgeEngine:
    """
    Simulates AutomationEdge T4 execution engine and backend systems
    (Entra ID, Microsoft Graph, TacticalRMM, ServiceNow CMDB).
    Exclusively utilized for offline automated test suites.
    """
    def __init__(self, data_dir: Optional[str] = None):
        if not data_dir:
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.data_dir = data_dir
        self._load_data()

    def _load_data(self):
        with open(os.path.join(self.data_dir, "employees.json"), "r", encoding="utf-8") as f:
            self.employees = json.load(f)
        with open(os.path.join(self.data_dir, "devices.json"), "r", encoding="utf-8") as f:
            self.devices = json.load(f)
        with open(os.path.join(self.data_dir, "hardware_assets.json"), "r", encoding="utf-8") as f:
            self.hardware_assets = json.load(f)
        with open(os.path.join(self.data_dir, "entitlements.json"), "r", encoding="utf-8") as f:
            self.entitlements = json.load(f)

    def execute(self, workflow_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches the workflow execution to the simulated handler."""
        handler_name = f"_handle_{workflow_name}"
        handler = getattr(self, handler_name, None)
        
        req_id = f"AE-REQ-{uuid.uuid4().hex[:6].upper()}"

        if not handler:
            from automationedge.workflow_registry import AE_WORKFLOW_REGISTRY
            if workflow_name in AE_WORKFLOW_REGISTRY:
                spec = AE_WORKFLOW_REGISTRY[workflow_name]
                out: Dict[str, Any] = {
                    "execution_status": "SUCCESS",
                    "workflow_name": workflow_name,
                    "target_system": spec.target_system,
                    "executed_at": utc_iso()
                }
                for field in spec.output_fields:
                    field_lower = field.lower()
                    if "status" in field_lower or "state" in field_lower:
                        if "isolation" in field_lower:
                            out[field] = "ISOLATED"
                        elif "compliance" in field_lower:
                            out[field] = "COMPLIANT"
                        elif "health" in field_lower:
                            out[field] = "HEALTHY"
                        elif "batch" in field_lower:
                            out[field] = "COMPLETED"
                        else:
                            out[field] = "SUCCESS"
                    elif "id" in field_lower or "guid" in field_lower or "token" in field_lower:
                        out[field] = f"{field.upper()[:4]}-{uuid.uuid4().hex[:8].upper()}"
                    elif "count" in field_lower:
                        out[field] = 1
                    elif "code" in field_lower:
                        out[field] = 200
                    elif "timestamp" in field_lower or "time" in field_lower:
                        out[field] = utc_iso()
                    elif "latency" in field_lower:
                        out[field] = 42
                    elif "output" in field_lower or "result" in field_lower or "summary" in field_lower or "body" in field_lower or "notes" in field_lower:
                        out[field] = f"Simulated execution output for {workflow_name} on target system {spec.target_system}."
                    else:
                        out[field] = params.get(field, f"SIMULATED_{field.upper()}")
                return {
                    "workflowName": workflow_name,
                    "automationRequestId": req_id,
                    "status": "Complete",
                    "message": f"Workflow {workflow_name} completed successfully.",
                    "workflowResponse": out
                }
            return {
                "workflowName": workflow_name,
                "automationRequestId": req_id,
                "status": "Failure",
                "message": f"Workflow {workflow_name} not found on AE server.",
                "workflowResponse": {"status": "FAILED", "error": f"Unknown workflow {workflow_name}"}
            }

        try:
            output = handler(params)
            return {
                "workflowName": workflow_name,
                "automationRequestId": req_id,
                "status": "Complete",
                "message": f"Workflow {workflow_name} completed successfully.",
                "workflowResponse": output
            }
        except Exception as e:
            return {
                "workflowName": workflow_name,
                "automationRequestId": req_id,
                "status": "Failure",
                "message": f"Execution error in {workflow_name}: {str(e)}",
                "workflowResponse": {"status": "FAILED", "error": str(e)}
            }

    # ── ACCESS HANDLERS ──
    def _handle_AE_ACC_001_ResolveUser(self, p: Dict[str, Any]) -> Dict[str, Any]:
        email = p.get("user_email", "").strip().lower()
        for emp in self.employees:
            if emp["email"].lower() == email:
                return {
                    "user_id": emp["user_id"],
                    "upn": emp["user_principal_name"],
                    "display_name": emp["display_name"],
                    "department": emp["department"],
                    "job_title": emp["job_title"],
                    "manager_email": emp["manager_email"],
                    "assigned_device_id": emp["assigned_device_id"],
                    "account_status": emp["account_status"]
                }
        raise ValueError(f"User with email '{email}' not found in Entra ID directory.")

    def _handle_AE_ACC_002_GetEntitlements(self, p: Dict[str, Any]) -> Dict[str, Any]:
        user_id = p.get("user_id")
        for emp in self.employees:
            if emp["user_id"] == user_id:
                return {
                    "user_id": user_id,
                    "assigned_groups": emp.get("assigned_groups", []),
                    "assigned_licenses": emp.get("assigned_licenses", []),
                    "assigned_roles": ["ROLE-STANDARD-USER"]
                }
        raise ValueError(f"User ID '{user_id}' not found.")

    def _handle_AE_ACC_003_ResolveCatalog(self, p: Dict[str, Any]) -> Dict[str, Any]:
        query = p.get("app_or_group_name", "").lower()
        for item in self.entitlements:
            if item["catalog_item_id"].lower() == query or query in item["friendly_name"].lower():
                return item
            for kw in item.get("alias_keywords", []):
                if kw in query:
                    return item

        for item in self.entitlements:
            fn_words = [w for w in item["friendly_name"].lower().split() if len(w) > 3]
            if any(w in query for w in fn_words):
                return item

        clean_name = query
        for noise in ["please add me to group ", "please grant me access to ", "permission for ", "access to ", "can i get ", "i need ", "permission to ", "add me to "]:
            if clean_name.startswith(noise):
                clean_name = clean_name[len(noise):]
        for noise in ["please", "asap", "thanks", "for my project", "for my sprint", "for work", "right now"]:
            clean_name = clean_name.replace(noise, "")
        clean_name = clean_name.strip().title()
        if not clean_name:
            clean_name = "Enterprise Application"

        target_slug = re.sub(r'[^A-Za-z0-9]+', '-', clean_name).strip('-').upper()[:24]
        return {
            "catalog_item_id": f"CAT-DYN-{uuid.uuid4().hex[:6].upper()}",
            "friendly_name": f"{clean_name} Access",
            "alias_keywords": [clean_name.lower()],
            "type": "GROUP",
            "target_object_id": f"GRP-{target_slug}",
            "risk_tier": "R2",
            "approval_required": True,
            "approver_role": "MANAGER",
            "description": f"Dynamic entitlement grant for {clean_name}"
        }

    def _handle_AE_ACC_011_AddGroupMember(self, p: Dict[str, Any]) -> Dict[str, Any]:
        user_id = p.get("user_id")
        group_id = p.get("group_id")
        for emp in self.employees:
            if emp["user_id"] == user_id:
                if group_id not in emp["assigned_groups"]:
                    emp["assigned_groups"].append(group_id)
                return {
                    "execution_status": "SUCCESS",
                    "membership_id": f"MBR-{uuid.uuid4().hex[:8]}",
                    "user_id": user_id,
                    "group_id": group_id,
                    "added_timestamp": utc_iso()
                }
        raise ValueError(f"User '{user_id}' not found.")

    def _handle_AE_ACC_013_AssignLicense(self, p: Dict[str, Any]) -> Dict[str, Any]:
        user_id = p.get("user_id")
        sku_id = p.get("sku_id")
        for emp in self.employees:
            if emp["user_id"] == user_id:
                if sku_id not in emp["assigned_licenses"]:
                    emp["assigned_licenses"].append(sku_id)
                return {
                    "execution_status": "SUCCESS",
                    "assignment_id": f"LIC-{uuid.uuid4().hex[:8]}",
                    "user_id": user_id,
                    "consumed_sku": sku_id,
                    "assigned_timestamp": utc_iso()
                }
        raise ValueError(f"User '{user_id}' not found.")

    def _handle_AE_ACC_021_RevokeSessions(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"execution_status": "SUCCESS", "revoked_token_count": 3, "timestamp": utc_iso()}

    # ── TACTICALRMM & DEVICE HANDLERS ──
    def _handle_AE_DEV_001_GetDeviceStatus(self, p: Dict[str, Any]) -> Dict[str, Any]:
        val = p.get("device_name_or_serial", "").lower()
        for dev in self.devices:
            if dev["device_id"].lower() == val or dev["hostname"].lower() == val or dev["serial_number"].lower() == val or dev.get("agent_id", "").lower() == val:
                return {
                    "device_id": dev["device_id"],
                    "agent_id": dev.get("agent_id", "agent-trmm-001"),
                    "hostname": dev["hostname"],
                    "serial_number": dev["serial_number"],
                    "os_version": dev.get("os", "Windows 11"),
                    "primary_user_upn": dev["primary_user_upn"],
                    "checks": dev.get("checks", []),
                    "compliance_state": "COMPLIANT" if not any(c.get("status") == "FAIL" for c in dev.get("checks", [])) else "NON_COMPLIANT"
                }
        return {
            "device_id": "DEV-WIN-102",
            "agent_id": "agent-trmm-002",
            "hostname": "LAPTOP-AMURPHY-W11",
            "serial_number": "PF4B7719",
            "os_version": "Windows 11 22H2",
            "primary_user_upn": "alex.murphy@enterprise.com",
            "checks": [{"name": "disk_encryption", "status": "FAIL"}],
            "compliance_state": "NON_COMPLIANT"
        }

    def _handle_AE_DEV_002_GetBitLockerKey(self, p: Dict[str, Any]) -> Dict[str, Any]:
        device_id = p.get("device_id")
        for dev in self.devices:
            if dev["device_id"] == device_id or dev.get("agent_id") == device_id:
                return {
                    "bitlocker_recovery_key_id": dev.get("bitlocker_recovery_key_id", "BL-KEY-8812"),
                    "bitlocker_recovery_key": dev.get("bitlocker_recovery_key", "491823-198273-091823-881923-901823-119283-772819-019283"),
                    "retrieved_timestamp": utc_iso()
                }
        return {
            "bitlocker_recovery_key_id": "BL-KEY-5541",
            "bitlocker_recovery_key": "123456-789012-345678-901234-567890-123456-789012-345678",
            "retrieved_timestamp": utc_iso()
        }

    def _handle_AE_DEV_010_TriggerSync(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"sync_status": "SUCCESS", "timestamp": utc_iso()}

    def _handle_AE_DEV_011_RestartDevice(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"restart_job_id": f"TRMM-REBOOT-{uuid.uuid4().hex[:6].upper()}", "execution_status": "SUCCESS"}

    def _handle_AE_DEV_012_RemediateCompliance(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"remediation_status": "SUCCESS", "new_compliance_state": "COMPLIANT", "applied_timestamp": utc_iso()}

    def _handle_AE_DEV_021_RunComplianceCheckScript(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"compliance_status": "COMPLIANT", "check_results": [{"name": "disk_encryption", "status": "PASS"}, {"name": "patch_level", "status": "PASS"}]}

    def _handle_AE_DEV_022_ApplyRemediationScript(self, p: Dict[str, Any]) -> Dict[str, Any]:
        agent_id = p.get("agent_id")
        for dev in self.devices:
            if dev.get("agent_id") == agent_id:
                for c in dev.get("checks", []):
                    c["status"] = "PASS"
        return {"remediation_status": "SUCCESS", "output_log": "Script applied. Check status set to PASS."}

    def _handle_AE_Get_Endpoint_Metrics_Bot(self, p: Dict[str, Any]) -> Dict[str, Any]:
        agent_id = p.get("agent_id")
        for dev in self.devices:
            if dev.get("agent_id") == agent_id or dev.get("device_id") == agent_id:
                return dev
        return {
            "agent_id": agent_id or "agent-trmm-002",
            "hostname": "LAPTOP-AMURPHY-W11",
            "cpu_pct": 14.2,
            "ram_pct": 48.1,
            "disk_free_gb": 42.5,
            "checks": [{"name": "disk_encryption", "status": "PASS"}]
        }

    def _handle_AE_Kill_Process_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"kill_status": "SUCCESS", "process_terminated": p.get("pid_or_name", "w3wp.exe")}

    def _handle_AE_Restart_Service_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"service_status": "RUNNING", "restart_timestamp": utc_iso()}

    def _handle_AE_Fetch_Patch_Package_Bot(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"patch_id": "PATCH-2026-SEC-01", "severity": "CRITICAL", "package_url": "https://repo.enterprise.local/patches/sec-01.pkg"}

    def _handle_AE_Execute_TacticalRMM_Patch_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"patch_status": "INSTALLED", "applied_timestamp": utc_iso()}

    def _handle_AE_Verify_Software_Version_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"package_name": p.get("package_name"), "installed_version": "v2.14.0-sec", "patch_status": "INSTALLED"}

    def _handle_AE_Disk_Usage_Scanner_Bot(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"disk_free_gb": 4.8, "temp_files_gb": 12.5, "large_directories": ["C:\\Windows\\Temp", "C:\\Users\\Default\\AppData"]}

    def _handle_AE_Safe_Temp_Cleanup_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"cleanup_status": "SUCCESS", "freed_space_gb": 12.5}

    def _handle_AE_Archive_User_Folder_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"archive_status": "SUCCESS", "archive_file_path": "D:\\Archives\\user_data_2026.zip"}

    def _handle_AE_Endpoint_Network_Diag_Bot(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"gateway_reachable": True, "dns_latency_ms": 12, "packet_loss_pct": 0.0}

    def _handle_AE_Restart_VPN_Daemon_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"vpn_status": "CONNECTED", "tunnel_established": True}

    def _handle_AE_Flush_DNS_Test_Ping_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"dns_flushed": True, "ping_success": True}

    # ── ONBOARDING & SECOPS HANDLERS ──
    def _handle_AE_Package_Deployer_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"deployment_status": "COMPLETED", "installed_packages": ["VSCode", "Python3", "Git", "Teams", "Defender"]}

    def _handle_AE_Configure_Local_Policies_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"policy_status": "APPLIED", "applied_policies": ["PASSWORD_COMPLEXITY", "SCREEN_LOCK_5MIN", "BITLOCKER_STRICT"]}

    def _handle_AE_Send_Welcome_Kit_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"delivery_status": "DISPATCHED", "dispatch_id": f"WK-{uuid.uuid4().hex[:6].upper()}"}

    def _handle_AE_Isolate_Endpoint_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"isolation_state": "ISOLATED", "isolation_id": f"ISO-{uuid.uuid4().hex[:6].upper()}"}

    def _handle_AE_SEC_001_IsolateHost(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return self._handle_AE_Isolate_Endpoint_Workflow(p)

    def _handle_AE_Extract_Memory_Forensics_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"forensics_status": "CAPTURED", "dump_path": f"s3://soc-forensics/{p.get('case_id')}/memory.dmp"}

    def _handle_AE_SEC_002_CaptureMemoryForensics(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return self._handle_AE_Extract_Memory_Forensics_Workflow(p)

    def _handle_AE_ONB_001_DeployPackageBundle(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return self._handle_AE_Package_Deployer_Workflow(p)

    def _handle_AE_ONB_002_ApplySecurityBaseline(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return self._handle_AE_Configure_Local_Policies_Workflow(p)

    def _handle_AE_Execute_Fleet_Batch_Script(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return self._handle_AE_Batch_Script_Runner_Workflow(p)

    def _handle_AE_Update_SIEM_Ticket_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"siem_update_status": "UPDATED", "ticket_id": p.get("ticket_id")}

    # ── RMM COPILOT & INFRA OPS HANDLERS ──
    def _handle_AE_RMM_Query_Bot(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"match_count": 3, "matching_agent_ids": ["agent-trmm-001", "agent-trmm-002", "agent-trmm-004"]}

    def _handle_AE_Batch_Script_Runner_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"batch_id": f"BATCH-{uuid.uuid4().hex[:6].upper()}", "batch_status": "COMPLETED", "target_count": 3}

    def _handle_AE_Stream_Execution_Status_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"batch_id": p.get("batch_id"), "completed_count": 3, "failed_count": 0, "status": "COMPLETED"}

    def _handle_AE_Collect_Process_Dump_Bot(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"dump_status": "SUCCESS", "dump_file": "D:\\CrashDumps\\w3wp_pid_4812.dmp"}

    def _handle_AE_Restart_AppPool_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"app_pool_status": "STARTED", "recycled_timestamp": utc_iso()}

    def _handle_AE_Http_Health_Check_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"http_status": 200, "latency_ms": 45, "health_state": "HEALTHY"}

    def _handle_AE_Scan_DB_Directory_Bot(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"db_name": p.get("db_name", "ProductionDB"), "data_size_gb": 120, "log_size_gb": 480, "drive_free_pct": 1.8}

    def _handle_AE_Backup_SQL_Logs_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"backup_status": "SUCCESS", "backup_file": f"N:\\SQLBackups\\{p.get('db_name')}_log_pit.trn"}

    def _handle_AE_Truncate_SQL_Logs_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "truncation_status": "SUCCESS",
            "free_space_status": "Drive C: 42% Free",
            "reclaimed_gb": 468.5,
            "timestamp": utc_iso()
        }

    # ── HARDWARE & CMDB HANDLERS ──
    def _handle_AE_HW_001_GetAssetDetails(self, p: Dict[str, Any]) -> Dict[str, Any]:
        val = p.get("asset_tag_or_serial", "").lower()
        for hw in self.hardware_assets:
            if (hw.get("ci_id", "").lower() == val or 
                hw.get("serial_number", "").lower() == val or 
                hw.get("asset_tag", "").lower() == val or 
                hw.get("device_id", "").lower() == val or
                hw.get("device_name", "").lower() == val or
                hw.get("assigned_user_email", "").lower() == val):
                return hw
        return {
            "ci_id": "CI-HW-5002",
            "asset_tag": "ASSET-L-102",
            "serial_number": "PF4B7719",
            "device_name": "LAPTOP-AMURPHY-W11",
            "model_name": "ThinkPad X1 Carbon Gen 11",
            "manufacturer": "Lenovo",
            "assigned_user_email": "alex.murphy@enterprise.com",
            "install_status": "In Use",
            "warranty_status": "Active (Premier Support)",
            "warranty_expiry": "2027-11-30"
        }

    def _handle_AE_HW_002_CheckWarranty(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"warranty_active": True, "warranty_expiry": "2027-11-30", "service_level": "Premier Onsite NBD"}

    def _handle_AE_HW_010_UpdateCIState(self, p: Dict[str, Any]) -> Dict[str, Any]:
        ci_id = p.get("ci_id")
        for hw in self.hardware_assets:
            if hw["ci_id"] == ci_id:
                hw["install_status"] = p.get("new_install_status", hw["install_status"])
        return {"update_status": "SUCCESS", "ci_id": ci_id, "modified_timestamp": utc_iso()}

    def _handle_AE_HW_020_OrderReplacement(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "order_id": f"ORD-{uuid.uuid4().hex[:6].upper()}",
            "tracking_number": "1Z99999999AA4826",
            "carrier": "FedEx Enterprise Express",
            "estimated_delivery": "2 Business Days",
            "status": "DISPATCHED"
        }

    # ── SERVICENOW HANDLERS ──
    def _handle_AE_SNOW_001_CreateTicket(self, p: Dict[str, Any]) -> Dict[str, Any]:
        tkt_num = f"INC-{uuid.uuid4().hex[:8].upper()}"
        return {
            "sys_id": f"sys_{uuid.uuid4().hex[:12]}",
            "ticket_number": tkt_num,
            "Incident_Number": tkt_num,
            "SysId": f"sys_{uuid.uuid4().hex[:12]}",
            "state": "New",
            "created_at": utc_iso()
        }

    def _handle_Servicenow_Incident_Creation(self, p: Dict[str, Any]) -> Dict[str, Any]:
        tkt_num = f"INC-{uuid.uuid4().hex[:8].upper()}"
        sys_id = f"sys_{uuid.uuid4().hex[:12]}"
        return {
            "sys_id": sys_id,
            "SysId": sys_id,
            "ticket_number": tkt_num,
            "Incident_Number": tkt_num,
            "ticket_id": tkt_num,
            "state": "New",
            "created_at": utc_iso()
        }

    def _handle_AE_SNOW_003_UpdateTicket(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "update_status": "SUCCESS",
            "ticket_id": p.get("ticket_id"),
            "state": p.get("state"),
            "updated_at": utc_iso()
        }

    def _handle_ServiceNow_Update_Incident(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "update_status": "SUCCESS",
            "SysId": p.get("SysId"),
            "state": p.get("state"),
            "updated_at": utc_iso()
        }

    # ── NOTIFICATIONS & EMAIL APPROVAL ──
    def _handle_AE_NOTIFY_001_SendApprovalEmail(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "send_status": "SENT",
            "message_id": f"MSG-{uuid.uuid4().hex[:12]}",
            "recipient": p.get("recipient"),
            "sent_at": utc_iso()
        }

    # ── TACTICAL RMM HANDLERS ──
    def _handle_Get_Agent_Run_Cmd(self, p: Dict[str, Any]) -> Dict[str, Any]:
        cmd = p.get("P_Command") or p.get("Command") or "ipconfig /all"
        hostname = p.get("P_Hostname") or p.get("Hostname") or "Apoorva"
        run_as_user = str(p.get("P_RunAsUser") or p.get("RunAsUser") or "true").lower()
        cmd_lower = cmd.lower()

        if "shutdown" in cmd_lower or "restart-computer" in cmd_lower:
            output = (
                f"Initiating remote system reboot on {hostname} (Exit Code: 0).\n"
                f"Execution Mode: RunAsUser = {run_as_user} (Elevated SYSTEM/Administrator)\n"
                f"Status: Shutdown signal dispatched. Target machine rebooting in 5 seconds."
            )
        elif "cpu" in cmd_lower or "get-process" in cmd_lower:
            output = (
                f"Id    ProcessName     CPU        WorkingSet64\n"
                f"--    -----------     ---        ------------\n"
                f"4820  chrome          124.50     329416704\n"
                f"7104  Code            88.20      221048832\n"
                f"2912  ms-teams        34.10      126144512\n"
                f"1044  powershell      12.05       82208768\n"
                f"512   svchost          5.40       41943040\n"
                f"\nTop CPU consumers analyzed on {hostname} (RunAsUser={run_as_user})."
            )
        elif "whoami" in cmd_lower:
            output = f"APOORVA-PC\\Apoorva\nUser Profile: C:\\Users\\Apoorva\nExecution Mode: RunAsUser ({run_as_user})"
        elif "win32_operatingsystem" in cmd_lower and "memory" in cmd_lower:
            output = (
                f"TotalMemoryGB FreeMemoryGB UsedMemoryGB\n"
                f"------------- ------------ ------------\n"
                f"        15.85         6.24         9.61\n"
            )
        elif "get-psdrive" in cmd_lower or "filesystem" in cmd_lower:
            output = (
                f"Name   Used       Free     TotalGB  FreeGB\n"
                f"----   ----       ----     -------  ------\n"
                f"C      234567890  278912345  478.2    265.9\n"
            )
        elif "get-service" in cmd_lower:
            output = (
                f"Name               DisplayName                         Status\n"
                f"----               -----------                         ------\n"
                f"Spooler            Print Spooler                       Running\n"
                f"wuauserv           Windows Update                      Running\n"
                f"WinDefend          Microsoft Defender Antivirus Service Running\n"
                f"LanmanWorkstation  Workstation                         Running\n"
                f"Dnscache           DNS Client                          Running\n"
            )
        elif "win32_operatingsystem" in cmd_lower and ("caption" in cmd_lower or "lastbootuptime" in cmd_lower):
            output = (
                f"Caption        : Microsoft Windows 11 Enterprise\n"
                f"Version        : 10.0.22631\n"
                f"BuildNumber    : 22631\n"
                f"OSArchitecture : 64-bit\n"
                f"LastBootUpTime : 20260901083015.000000+330\n"
            )
        elif "win32_battery" in cmd_lower:
            output = (
                f"EstimatedChargeRemaining BatteryStatus Status\n"
                f"------------------------ ------------- ------\n"
                f"                      94             2 OK    \n"
            )
        elif "uninstall" in cmd_lower:
            output = (
                f"DisplayName                              DisplayVersion   Publisher\n"
                f"-----------                              --------------   ---------\n"
                f"Microsoft 365 Apps for enterprise        16.0.17928.20156 Microsoft Corporation\n"
                f"Microsoft Teams                          24193.1805.3040  Microsoft Corporation\n"
                f"Google Chrome                            128.0.6613.114   Google LLC\n"
                f"Visual Studio Code                       1.93.0           Microsoft Corporation\n"
                f"Tactical RMM Agent                       2.4.1            Amiscode LLC\n"
            )
        elif "nettcpconnection" in cmd_lower:
            output = (
                f"LocalAddress   LocalPort RemoteAddress  RemotePort State\n"
                f"------------   --------- -------------  ---------- -----\n"
                f"192.168.1.105  52344     52.114.132.80  443        Established\n"
                f"192.168.1.105  52348     20.190.159.4   443        Established\n"
                f"192.168.1.105  52350     142.250.190.46 443        Established\n"
            )
        elif "win32_bios" in cmd_lower:
            output = (
                f"Manufacturer : Lenovo\n"
                f"Name         : N34ET52W (1.52 )\n"
                f"SerialNumber : PF39XK12\n"
                f"Version      : LENOVO - 1520\n"
            )
        elif "get-eventlog" in cmd_lower:
            output = (
                f"TimeGenerated       Source           EventID Message\n"
                f"-------------       ------           ------- -------\n"
                f"09/08/2026 09:12:00 Service Control    7034 The Print Spooler service terminated unexpectedly.\n"
                f"09/08/2026 08:45:12 Disk                153 The IO operation at logical block address was retried.\n"
            )
        elif "test-connection" in cmd_lower:
            output = (
                f"Source        Destination     IPV4Address      IPV6Address  Bytes    Time(ms)\n"
                f"------        -----------     -----------      -----------  -----    --------\n"
                f"{hostname}     8.8.8.8         8.8.8.8                       32       14\n"
                f"{hostname}     8.8.8.8         8.8.8.8                       32       13\n"
                f"{hostname}     8.8.8.8         8.8.8.8                       32       15\n"
                f"{hostname}     8.8.8.8         8.8.8.8                       32       14\n"
            )
        elif "netfirewallprofile" in cmd_lower:
            output = (
                f"Name    Enabled\n"
                f"----    -------\n"
                f"Domain     True\n"
                f"Private    True\n"
                f"Public     True\n"
            )
        elif "computerinfo" in cmd_lower:
            output = (
                f"CsName             : {hostname}\n"
                f"WindowsProductName : Windows 11 Enterprise\n"
                f"WindowsVersion     : 2009\n"
                f"TotalPhysicalMemory: 17042436096\n"
                f"OsUptime           : 6.22:15:43\n"
            )
        else:
            output = (
                f"Windows IP Configuration\n\n"
                f"   Host Name . . . . . . . . . . . . : {hostname}\n"
                f"   Primary Dns Suffix  . . . . . . . : enterprise.corp\n"
                f"   Node Type . . . . . . . . . . . . : Hybrid\n"
                f"   IP Routing Enabled. . . . . . . . : No\n"
                f"   WINS Proxy Enabled. . . . . . . . : No\n\n"
                f"Ethernet adapter vEthernet (Default Switch):\n\n"
                f"   Connection-specific DNS Suffix  . : \n"
                f"   IPv4 Address. . . . . . . . . . . : 192.168.1.105\n"
                f"   Subnet Mask . . . . . . . . . . . : 255.255.255.0\n"
                f"   Default Gateway . . . . . . . . . : 192.168.1.1\n"
                f"   DNS Servers . . . . . . . . . . . : 1.1.1.1, 8.8.8.8"
            )
        return {
            "status": "SUCCESS",
            "hostname": hostname,
            "command": cmd,
            "run_as_user": run_as_user,
            "output": output,
            "exit_code": 0,
            "executed_at": utc_iso()
        }

    def _handle_TRMM_Run_IP_Config(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return self._handle_Get_Agent_Run_Cmd(p)

    def _handle_TRMM_Execute_Command(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return self._handle_Get_Agent_Run_Cmd(p)

    def _handle_Get_Machine_Summary(self, p: Dict[str, Any]) -> Dict[str, Any]:
        hostname = p.get("P_Hostname") or p.get("Hostname") or "Apoorva"
        summary_text = (
            f"Hardware & System Summary for {hostname}:\n"
            f"• Hostname       : {hostname}\n"
            f"• Operating System: Windows 11 Enterprise (Build 22631.3880, 64-bit)\n"
            f"• Processor (CPU): 12th Gen Intel(R) Core(TM) i7-12700H (14 Cores, 20 Threads @ 2.70 GHz)\n"
            f"• Installed Memory: 32.0 GB DDR5 (24.2 GB Available / 7.8 GB Used)\n"
            f"• Primary Storage : NVMe 1TB SSD (C: Drive: 642 GB Free / 953 GB Total)\n"
            f"• System Uptime   : 4 days, 18 hours, 22 minutes\n"
            f"• Tactical Agent : Connected (Agent ID: zAltxZhbdHrygGpGRhnwqGSbOLSHozfDAZOTntXu)\n"
            f"• Security Health : BitLocker Enabled (XTS-AES 256), Windows Defender Active"
        )
        return {
            "status": "SUCCESS",
            "hostname": hostname,
            "os": "Windows 11 Enterprise",
            "cpu": "Intel(R) Core(TM) i7-12700H",
            "ram": "32.0 GB",
            "disk": "642 GB Free of 953 GB",
            "body": summary_text,
            "output": summary_text,
            "summary": summary_text
        }

    def _handle_Get_Agents_List(self, p: Dict[str, Any]) -> Dict[str, Any]:
        agents_text = (
            f"Tactical RMM Connected Agents Fleet (3 Online / 0 Offline):\n\n"
            f"ID                                       Hostname            OS                      Status   IP Address\n"
            f"---------------------------------------- ------------------- ----------------------- -------- ---------------\n"
            f"zAltxZhbdHrygGpGRhnwqGSbOLSHozfDAZOTntXu Apoorva             Windows 11 Enterprise   Online   192.168.1.105\n"
            f"agent-trmm-001                           LAPTOP-SCONNOR-W11  Windows 11 Pro          Online   10.0.4.12\n"
            f"agent-trmm-002                           LAPTOP-AMURPHY-W11  Windows 11 Enterprise   Online   10.0.4.45\n"
            f"agent-trmm-004                           LAPTOP-DCHEN-W11    Windows 11 Enterprise   Online   10.0.4.88"
        )
        return {
            "status": "SUCCESS",
            "agents_count": 4,
            "online_count": 4,
            "body": agents_text,
            "output": agents_text,
            "agents": agents_text
        }

    def _handle_Get_Software_List(self, p: Dict[str, Any]) -> Dict[str, Any]:
        hostname = p.get("P_Hostname") or p.get("Hostname") or "Apoorva"
        sw_text = (
            f"Installed Software Inventory on {hostname}:\n\n"
            f"Application Name                         Version          Publisher\n"
            f"---------------------------------------- ---------------- ------------------------\n"
            f"Microsoft 365 Apps for enterprise        16.0.17928.20156 Microsoft Corporation\n"
            f"Microsoft Teams (work or school)         24193.1805.3040  Microsoft Corporation\n"
            f"Google Chrome                            128.0.6613.114   Google LLC\n"
            f"Visual Studio Code                       1.93.0           Microsoft Corporation\n"
            f"Tactical RMM Agent                       2.4.1            Amiscode LLC\n"
            f"7-Zip 24.08 (x64)                        24.08.00.0       Igor Pavlov\n"
            f"Python 3.12.10 (64-bit)                  3.12.10150.0     Python Software Foundation\n"
            f"Git version 2.45.2.windows.1             2.45.2           The Git Development Community"
        )
        return {
            "status": "SUCCESS",
            "hostname": hostname,
            "software_count": 8,
            "body": sw_text,
            "output": sw_text,
            "installed_software": sw_text
        }

    def _handle_Get_Windows_Patches(self, p: Dict[str, Any]) -> Dict[str, Any]:
        hostname = p.get("P_Hostname") or p.get("Hostname") or "Apoorva"
        patches_text = (
            f"Windows Updates and Security Patch Telemetry on {hostname}:\n\n"
            f"KB ID      Title                                                       Classification     Status\n"
            f"---------- ----------------------------------------------------------- ------------------ -----------\n"
            f"KB5041585  2026-08 Cumulative Update for Windows 11 Version 23H2       Security Updates   Installed\n"
            f"KB5041580  2026-08 .NET Framework 3.5 and 4.8.1 Cumulative Update      Critical Updates   Installed\n"
            f"KB5041578  Security Intelligence Update for Microsoft Defender Antivirus Definition Update Installed\n"
            f"\nPending Updates: 0 pending patches (Device 100% compliant with enterprise baseline)."
        )
        return {
            "status": "SUCCESS",
            "hostname": hostname,
            "installed_count": 3,
            "pending_count": 0,
            "body": patches_text,
            "output": patches_text,
            "patches": patches_text
        }

    def _handle_Software_Installation(self, p: Dict[str, Any]) -> Dict[str, Any]:
        hostname = p.get("P_Hostname") or p.get("Hostname") or "Apoorva"
        software_name = p.get("P_SoftwareName") or p.get("SoftwareName") or "7-Zip"
        output_text = (
            f"Software Installation Log for {software_name} on {hostname}:\n"
            f"• Deployment Mode : Tactical RMM Remote Choco/Winget Silent Deployment\n"
            f"• Execution User  : NT AUTHORITY\\SYSTEM (RunAsUser: false)\n"
            f"• Package Name    : {software_name}\n"
            f"• Status          : Installation Succeeded (ExitCode: 0)\n"
            f"• Verification    : Package verified in Windows Registry Uninstall hive."
        )
        return {
            "status": "SUCCESS",
            "hostname": hostname,
            "software_name": software_name,
            "exit_code": 0,
            "body": output_text,
            "output": output_text
        }





