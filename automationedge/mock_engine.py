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

    def _handle_AE_Extract_Memory_Forensics_Workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"forensics_status": "CAPTURED", "dump_path": f"s3://soc-forensics/{p.get('case_id')}/memory.dmp"}

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
