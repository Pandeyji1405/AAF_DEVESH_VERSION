from typing import Dict, Any, List
from pydantic import BaseModel, Field

class WorkflowSpec(BaseModel):
    workflow_name: str
    description: str
    target_system: str
    risk_tier: str
    input_fields: List[str]
    output_fields: List[str]
    read_only: bool = True

AE_WORKFLOW_REGISTRY: Dict[str, WorkflowSpec] = {
    # ── ACCESS WORKFLOWS ──
    "AE_ACC_001_ResolveUser": WorkflowSpec(
        workflow_name="AE_ACC_001_ResolveUser",
        description="Query Entra ID & HR database for user identity and profile metadata.",
        target_system="Entra ID / HR",
        risk_tier="R0",
        input_fields=["user_email"],
        output_fields=["user_id", "upn", "department", "manager_email", "assigned_device_id", "account_status"],
        read_only=True
    ),
    "AE_ACC_002_GetEntitlements": WorkflowSpec(
        workflow_name="AE_ACC_002_GetEntitlements",
        description="Fetch current Entra groups, roles, and M365 licenses assigned to the user.",
        target_system="Microsoft Graph API",
        risk_tier="R0",
        input_fields=["user_id"],
        output_fields=["assigned_groups", "assigned_roles", "assigned_licenses"],
        read_only=True
    ),
    "AE_ACC_003_ResolveCatalog": WorkflowSpec(
        workflow_name="AE_ACC_003_ResolveCatalog",
        description="Look up friendly application/group name in the Entitlement Catalog to resolve tenant GUID.",
        target_system="Entitlement Catalog",
        risk_tier="R0",
        input_fields=["app_or_group_name"],
        output_fields=["catalog_item_id", "target_object_id", "type", "risk_tier", "approval_required", "approver_role"],
        read_only=True
    ),
    "AE_ACC_004_EvaluateEligibility": WorkflowSpec(
        workflow_name="AE_ACC_004_EvaluateEligibility",
        description="Evaluates user eligibility against entitlement rules and role prerequisites.",
        target_system="Entra ID / Policy",
        risk_tier="R0",
        input_fields=["user_id", "entitlement_id"],
        output_fields=["eligible", "reason"],
        read_only=True
    ),
    "AE_ACC_005_GetApprovalChain": WorkflowSpec(
        workflow_name="AE_ACC_005_GetApprovalChain",
        description="Determines required approver hierarchy and designated signers for requested entitlement.",
        target_system="HR / Entra ID",
        risk_tier="R0",
        input_fields=["user_id", "entitlement_id"],
        output_fields=["approver_email", "approval_level"],
        read_only=True
    ),
    "AE_ACC_006_GetApprovalStatus": WorkflowSpec(
        workflow_name="AE_ACC_006_GetApprovalStatus",
        description="Queries approval status from ServiceNow or approval engine.",
        target_system="ServiceNow",
        risk_tier="R0",
        input_fields=["approval_id"],
        output_fields=["status", "decided_at"],
        read_only=True
    ),
    "AE_ACC_010_AssignAccessPackage": WorkflowSpec(
        workflow_name="AE_ACC_010_AssignAccessPackage",
        description="Assigns an Entra ID Entitlement Management Access Package.",
        target_system="Microsoft Graph API",
        risk_tier="R2",
        input_fields=["user_id", "package_id", "ticket_id"],
        output_fields=["assignment_id", "status"],
        read_only=False
    ),
    "AE_ACC_011_AddGroupMember": WorkflowSpec(
        workflow_name="AE_ACC_011_AddGroupMember",
        description="Add a user to an Entra ID security or M365 group.",
        target_system="Microsoft Graph API",
        risk_tier="R2",
        input_fields=["user_id", "group_id", "ticket_id", "reason"],
        output_fields=["execution_status", "membership_id", "added_timestamp"],
        read_only=False
    ),
    "AE_ACC_012_AssignAppRole": WorkflowSpec(
        workflow_name="AE_ACC_012_AssignAppRole",
        description="Assign enterprise application role in Entra ID.",
        target_system="Entra Enterprise App",
        risk_tier="R2",
        input_fields=["user_id", "app_id", "role_name", "ticket_id"],
        output_fields=["execution_status", "assignment_id"],
        read_only=False
    ),
    "AE_ACC_013_AssignLicense": WorkflowSpec(
        workflow_name="AE_ACC_013_AssignLicense",
        description="Assign a licensed SKU (e.g. M365 E5, Salesforce) to a user in Entra ID.",
        target_system="Microsoft Graph / SaaS",
        risk_tier="R2",
        input_fields=["user_id", "sku_id", "ticket_id"],
        output_fields=["execution_status", "consumed_sku", "assigned_timestamp"],
        read_only=False
    ),
    "AE_ACC_014_ProvisionSaaS": WorkflowSpec(
        workflow_name="AE_ACC_014_ProvisionSaaS",
        description="Provision account or license in external SaaS platform.",
        target_system="SaaS SCIM / API",
        risk_tier="R2",
        input_fields=["user_id", "saas_app", "plan_tier", "ticket_id"],
        output_fields=["execution_status", "saas_user_id"],
        read_only=False
    ),
    "AE_ACC_015_GrantPrivilegedPIM": WorkflowSpec(
        workflow_name="AE_ACC_015_GrantPrivilegedPIM",
        description="Activate short-lived Privileged Identity Management role in Entra.",
        target_system="Entra ID PIM",
        risk_tier="R3",
        input_fields=["user_id", "pim_role", "duration_hours", "ticket_id"],
        output_fields=["execution_status", "pim_activation_id", "expiry_timestamp"],
        read_only=False
    ),
    "AE_ACC_016_ResetMFA": WorkflowSpec(
        workflow_name="AE_ACC_016_ResetMFA",
        description="Require user to re-register MFA methods in Entra ID.",
        target_system="Entra ID MFA",
        risk_tier="R2",
        input_fields=["user_id", "ticket_id"],
        output_fields=["execution_status", "mfa_reset_timestamp"],
        read_only=False
    ),
    "AE_ACC_020_RemoveEntitlement": WorkflowSpec(
        workflow_name="AE_ACC_020_RemoveEntitlement",
        description="Remove group membership or revoke license from user in Entra ID.",
        target_system="Microsoft Graph API",
        risk_tier="R2",
        input_fields=["user_id", "entitlement_id", "ticket_id"],
        output_fields=["execution_status", "removed_timestamp"],
        read_only=False
    ),
    "AE_ACC_021_RevokeSessions": WorkflowSpec(
        workflow_name="AE_ACC_021_RevokeSessions",
        description="Revoke all active refresh tokens and user sessions in Entra ID.",
        target_system="Entra ID",
        risk_tier="R3",
        input_fields=["user_id", "reason", "ticket_id"],
        output_fields=["execution_status", "revoked_token_count"],
        read_only=False
    ),
    "AE_ACC_030_CreateAccessReview": WorkflowSpec(
        workflow_name="AE_ACC_030_CreateAccessReview",
        description="Creates an access certification campaign in Entra ID.",
        target_system="Entra ID Governance",
        risk_tier="R1",
        input_fields=["group_id", "review_name"],
        output_fields=["review_id", "status"],
        read_only=False
    ),
    "AE_ACC_031_ApplyReviewDecisions": WorkflowSpec(
        workflow_name="AE_ACC_031_ApplyReviewDecisions",
        description="Applies approved or denied decisions from completed access review.",
        target_system="Entra ID Governance",
        risk_tier="R2",
        input_fields=["review_id", "ticket_id"],
        output_fields=["applied_count", "status"],
        read_only=False
    ),
    "AE_ACC_040_GetLicenseUsage": WorkflowSpec(
        workflow_name="AE_ACC_040_GetLicenseUsage",
        description="Queries user activity and last login timestamp for assigned software license.",
        target_system="Microsoft Graph / SaaS",
        risk_tier="R0",
        input_fields=["user_id", "sku_id"],
        output_fields=["last_active_date", "days_inactive"],
        read_only=True
    ),
    "AE_ACC_041_ReclaimLicense": WorkflowSpec(
        workflow_name="AE_ACC_041_ReclaimLicense",
        description="Reclaims unutilized license seat and returns to pool.",
        target_system="Microsoft Graph / SaaS",
        risk_tier="R2",
        input_fields=["user_id", "sku_id", "ticket_id"],
        output_fields=["reclaim_status", "timestamp"],
        read_only=False
    ),

    # ── TACTICALRMM & DEVICE WORKFLOWS ──
    "AE_DEV_001_GetDeviceStatus": WorkflowSpec(
        workflow_name="AE_DEV_001_GetDeviceStatus",
        description="Retrieve agent status, hostname, and telemetry from TacticalRMM.",
        target_system="TacticalRMM",
        risk_tier="R0",
        input_fields=["device_name_or_serial"],
        output_fields=["device_id", "agent_id", "hostname", "compliance_state", "os_version"],
        read_only=True
    ),
    "AE_DEV_002_GetBitLockerKey": WorkflowSpec(
        workflow_name="AE_DEV_002_GetBitLockerKey",
        description="Retrieve BitLocker recovery key from Microsoft Graph / Key Vault with audit logging.",
        target_system="Microsoft Graph API",
        risk_tier="R2",
        input_fields=["device_id", "requester_upn", "ticket_id"],
        output_fields=["bitlocker_recovery_key_id", "bitlocker_recovery_key", "retrieved_timestamp"],
        read_only=True
    ),
    "AE_DEV_010_TriggerSync": WorkflowSpec(
        workflow_name="AE_DEV_010_TriggerSync",
        description="Send an immediate TacticalRMM check-in notification to refresh telemetry.",
        target_system="TacticalRMM",
        risk_tier="R1",
        input_fields=["agent_id"],
        output_fields=["sync_status", "timestamp"],
        read_only=False
    ),
    "AE_DEV_011_RestartDevice": WorkflowSpec(
        workflow_name="AE_DEV_011_RestartDevice",
        description="Execute remote reboot script on managed endpoint via TacticalRMM.",
        target_system="TacticalRMM",
        risk_tier="R2",
        input_fields=["agent_id", "force_reboot", "ticket_id"],
        output_fields=["restart_job_id", "execution_status"],
        read_only=False
    ),
    "AE_DEV_012_RemediateCompliance": WorkflowSpec(
        workflow_name="AE_DEV_012_RemediateCompliance",
        description="Execute compliance remediation script via TacticalRMM.",
        target_system="TacticalRMM",
        risk_tier="R2",
        input_fields=["agent_id", "policy_name", "ticket_id"],
        output_fields=["remediation_status", "new_compliance_state"],
        read_only=False
    ),
    "AE_DEV_013_UpdateAntivirusSignatures": WorkflowSpec(
        workflow_name="AE_DEV_013_UpdateAntivirusSignatures",
        description="Force antivirus definition update and quick scan on endpoint.",
        target_system="TacticalRMM / Defender",
        risk_tier="R1",
        input_fields=["agent_id"],
        output_fields=["update_status", "signature_version"],
        read_only=False
    ),
    "AE_DEV_014_DeployWifiProfile": WorkflowSpec(
        workflow_name="AE_DEV_014_DeployWifiProfile",
        description="Repush 802.1x enterprise corporate Wi-Fi profile and certificate payload.",
        target_system="TacticalRMM",
        risk_tier="R2",
        input_fields=["agent_id", "profile_name", "ticket_id"],
        output_fields=["deployment_status", "profile_id"],
        read_only=False
    ),
    "AE_DEV_015_ResetWindowsHello": WorkflowSpec(
        workflow_name="AE_DEV_015_ResetWindowsHello",
        description="Reset Windows Hello PIN / biometric container on managed endpoint.",
        target_system="TacticalRMM / Entra",
        risk_tier="R2",
        input_fields=["agent_id", "ticket_id"],
        output_fields=["reset_status", "temporary_pin_prompted"],
        read_only=False
    ),
    "AE_DEV_016_LockDevice": WorkflowSpec(
        workflow_name="AE_DEV_016_LockDevice",
        description="Remotely lock lost or misplaced managed endpoint.",
        target_system="TacticalRMM",
        risk_tier="R2",
        input_fields=["agent_id", "ticket_id"],
        output_fields=["lock_status", "locked_timestamp"],
        read_only=False
    ),
    "AE_DEV_017_RedeployAppPackage": WorkflowSpec(
        workflow_name="AE_DEV_017_RedeployAppPackage",
        description="Force reinstallation or repair of enterprise application package.",
        target_system="TacticalRMM",
        risk_tier="R2",
        input_fields=["agent_id", "app_name", "ticket_id"],
        output_fields=["package_status", "install_job_id"],
        read_only=False
    ),
    "AE_DEV_018_ClearStorageCache": WorkflowSpec(
        workflow_name="AE_DEV_018_ClearStorageCache",
        description="Purge OS temp files, delivery optimization cache, and crash dumps.",
        target_system="TacticalRMM",
        risk_tier="R1",
        input_fields=["agent_id"],
        output_fields=["cleanup_status", "freed_bytes_mb"],
        read_only=False
    ),
    "AE_DEV_020_WipeRetire": WorkflowSpec(
        workflow_name="AE_DEV_020_WipeRetire",
        description="Retire or wipe a corporate-managed device from inventory.",
        target_system="TacticalRMM",
        risk_tier="R3",
        input_fields=["agent_id", "action_type", "approval_id", "ticket_id"],
        output_fields=["wipe_job_id", "status"],
        read_only=False
    ),
    "AE_DEV_021_RunComplianceCheckScript": WorkflowSpec(
        workflow_name="AE_DEV_021_RunComplianceCheckScript",
        description="Runs compliance check script across disk encryption, patch level, and antivirus.",
        target_system="TacticalRMM",
        risk_tier="R0",
        input_fields=["agent_id"],
        output_fields=["compliance_status", "check_results"],
        read_only=True
    ),
    "AE_DEV_022_ApplyRemediationScript": WorkflowSpec(
        workflow_name="AE_DEV_022_ApplyRemediationScript",
        description="Executes targeted remediation script for failed check via TacticalRMM.",
        target_system="TacticalRMM",
        risk_tier="R2",
        input_fields=["agent_id", "check_name", "ticket_id"],
        output_fields=["remediation_status", "output_log"],
        read_only=False
    ),
    "AE_Get_Endpoint_Metrics_Bot": WorkflowSpec(
        workflow_name="AE_Get_Endpoint_Metrics_Bot",
        description="Retrieves CPU, RAM, disk usage, and check status from TacticalRMM.",
        target_system="TacticalRMM",
        risk_tier="R0",
        input_fields=["agent_id"],
        output_fields=["agent_id", "hostname", "cpu_pct", "ram_pct", "disk_free_gb", "checks"],
        read_only=True
    ),
    "AE_Kill_Process_Workflow": WorkflowSpec(
        workflow_name="AE_Kill_Process_Workflow",
        description="Terminates rogue or unresponsive process on endpoint.",
        target_system="TacticalRMM",
        risk_tier="R1",
        input_fields=["agent_id", "pid_or_name", "ticket_id"],
        output_fields=["kill_status", "process_terminated"],
        read_only=False
    ),
    "AE_Restart_Service_Workflow": WorkflowSpec(
        workflow_name="AE_Restart_Service_Workflow",
        description="Restarts a Windows or Linux system service.",
        target_system="TacticalRMM",
        risk_tier="R1",
        input_fields=["agent_id", "service_name", "ticket_id"],
        output_fields=["service_status", "restart_timestamp"],
        read_only=False
    ),
    "AE_Fetch_Patch_Package_Bot": WorkflowSpec(
        workflow_name="AE_Fetch_Patch_Package_Bot",
        description="Validates and stages patch package for target CVE.",
        target_system="Patch Catalog",
        risk_tier="R0",
        input_fields=["cve_id_or_patch_name"],
        output_fields=["patch_id", "severity", "package_url"],
        read_only=True
    ),
    "AE_Execute_TacticalRMM_Patch_Workflow": WorkflowSpec(
        workflow_name="AE_Execute_TacticalRMM_Patch_Workflow",
        description="Deploys and installs patch via TacticalRMM script.",
        target_system="TacticalRMM",
        risk_tier="R2",
        input_fields=["agent_id", "patch_id", "ticket_id"],
        output_fields=["patch_status", "applied_timestamp"],
        read_only=False
    ),
    "AE_Verify_Software_Version_Workflow": WorkflowSpec(
        workflow_name="AE_Verify_Software_Version_Workflow",
        description="Verifies installed software version on endpoint.",
        target_system="TacticalRMM",
        risk_tier="R0",
        input_fields=["agent_id", "package_name"],
        output_fields=["package_name", "installed_version", "patch_status"],
        read_only=True
    ),
    "AE_Disk_Usage_Scanner_Bot": WorkflowSpec(
        workflow_name="AE_Disk_Usage_Scanner_Bot",
        description="Scans drive usage and identifies space hogs.",
        target_system="TacticalRMM",
        risk_tier="R0",
        input_fields=["agent_id"],
        output_fields=["disk_free_gb", "temp_files_gb", "large_directories"],
        read_only=True
    ),
    "AE_Safe_Temp_Cleanup_Workflow": WorkflowSpec(
        workflow_name="AE_Safe_Temp_Cleanup_Workflow",
        description="Purges temp files and stale caches.",
        target_system="TacticalRMM",
        risk_tier="R1",
        input_fields=["agent_id", "ticket_id"],
        output_fields=["cleanup_status", "freed_space_gb"],
        read_only=False
    ),
    "AE_Archive_User_Folder_Workflow": WorkflowSpec(
        workflow_name="AE_Archive_User_Folder_Workflow",
        description="Compresses and archives large user folder to secondary storage.",
        target_system="TacticalRMM",
        risk_tier="R2",
        input_fields=["agent_id", "folder_path", "ticket_id"],
        output_fields=["archive_status", "archive_file_path"],
        read_only=False
    ),
    "AE_Endpoint_Network_Diag_Bot": WorkflowSpec(
        workflow_name="AE_Endpoint_Network_Diag_Bot",
        description="Runs ping, DNS, and latency diagnostics.",
        target_system="TacticalRMM",
        risk_tier="R0",
        input_fields=["agent_id"],
        output_fields=["gateway_reachable", "dns_latency_ms", "packet_loss_pct"],
        read_only=True
    ),
    "AE_Restart_VPN_Daemon_Workflow": WorkflowSpec(
        workflow_name="AE_Restart_VPN_Daemon_Workflow",
        description="Restarts endpoint VPN daemon.",
        target_system="TacticalRMM",
        risk_tier="R1",
        input_fields=["agent_id", "ticket_id"],
        output_fields=["vpn_status", "tunnel_established"],
        read_only=False
    ),
    "AE_Flush_DNS_Test_Ping_Workflow": WorkflowSpec(
        workflow_name="AE_Flush_DNS_Test_Ping_Workflow",
        description="Flushes DNS resolver cache and tests target ping.",
        target_system="TacticalRMM",
        risk_tier="R1",
        input_fields=["agent_id", "target_host"],
        output_fields=["dns_flushed", "ping_success"],
        read_only=False
    ),

    # ── ONBOARDING & SECOPS WORKFLOWS ──
    "AE_Package_Deployer_Workflow": WorkflowSpec(
        workflow_name="AE_Package_Deployer_Workflow",
        description="Deploys standardized workstation software package.",
        target_system="TacticalRMM",
        risk_tier="R2",
        input_fields=["agent_id", "package_bundle", "ticket_id"],
        output_fields=["deployment_status", "installed_packages"],
        read_only=False
    ),
    "AE_Configure_Local_Policies_Workflow": WorkflowSpec(
        workflow_name="AE_Configure_Local_Policies_Workflow",
        description="Enforces local security policies on endpoint.",
        target_system="TacticalRMM",
        risk_tier="R2",
        input_fields=["agent_id", "policy_set", "ticket_id"],
        output_fields=["policy_status", "applied_policies"],
        read_only=False
    ),
    "AE_Send_Welcome_Kit_Workflow": WorkflowSpec(
        workflow_name="AE_Send_Welcome_Kit_Workflow",
        description="Dispatches onboarding kit and credentials to new hire.",
        target_system="Enterprise Notification Service",
        risk_tier="R1",
        input_fields=["user_email", "recipient_name", "ticket_id"],
        output_fields=["delivery_status", "dispatch_id"],
        read_only=False
    ),
    "AE_Isolate_Endpoint_Workflow": WorkflowSpec(
        workflow_name="AE_Isolate_Endpoint_Workflow",
        description="Isolates infected endpoint from network while keeping RMM active.",
        target_system="EDR / TacticalRMM",
        risk_tier="R2",
        input_fields=["agent_id", "reason", "ticket_id"],
        output_fields=["isolation_state", "isolation_id"],
        read_only=False
    ),
    "AE_Extract_Memory_Forensics_Workflow": WorkflowSpec(
        workflow_name="AE_Extract_Memory_Forensics_Workflow",
        description="Captures live memory triage and volatile processes.",
        target_system="Forensics Agent",
        risk_tier="R2",
        input_fields=["agent_id", "case_id", "ticket_id"],
        output_fields=["forensics_status", "dump_path"],
        read_only=False
    ),
    "AE_Update_SIEM_Ticket_Workflow": WorkflowSpec(
        workflow_name="AE_Update_SIEM_Ticket_Workflow",
        description="Updates SIEM incident record.",
        target_system="SIEM API",
        risk_tier="R1",
        input_fields=["alert_id", "status", "notes", "ticket_id"],
        output_fields=["siem_update_status", "ticket_id"],
        read_only=False
    ),
    "AE_SEC_001_IsolateEndpoint": WorkflowSpec(
        workflow_name="AE_SEC_001_IsolateEndpoint",
        description="Isolate infected endpoint from enterprise network.",
        target_system="Microsoft Defender for Endpoint",
        risk_tier="R3",
        input_fields=["device_id", "reason", "ticket_id"],
        output_fields=["isolation_status", "isolation_id"],
        read_only=False
    ),
    "AE_SEC_002_AuthorizeUsbException": WorkflowSpec(
        workflow_name="AE_SEC_002_AuthorizeUsbException",
        description="Apply temporary USB exemption policy.",
        target_system="Endpoint Security",
        risk_tier="R2",
        input_fields=["device_id", "justification", "duration_hours", "ticket_id"],
        output_fields=["exemption_status", "policy_guid"],
        read_only=False
    ),
    "AE_SEC_003_QuarantineRemediate": WorkflowSpec(
        workflow_name="AE_SEC_003_QuarantineRemediate",
        description="Quarantine detected malicious file.",
        target_system="Endpoint Security",
        risk_tier="R2",
        input_fields=["device_id", "threat_name", "ticket_id"],
        output_fields=["remediation_status"],
        read_only=False
    ),

    # ── RMM COPILOT & INFRASTRUCTURE OPS ──
    "AE_RMM_Query_Bot": WorkflowSpec(
        workflow_name="AE_RMM_Query_Bot",
        description="Executes cross-fleet query across TacticalRMM agents.",
        target_system="TacticalRMM",
        risk_tier="R0",
        input_fields=["query_filter"],
        output_fields=["match_count", "matching_agent_ids"],
        read_only=True
    ),
    "AE_Batch_Script_Runner_Workflow": WorkflowSpec(
        workflow_name="AE_Batch_Script_Runner_Workflow",
        description="Executes batch script across multiple endpoints.",
        target_system="TacticalRMM",
        risk_tier="R2",
        input_fields=["target_agent_ids", "script_name", "ticket_id"],
        output_fields=["batch_id", "batch_status", "target_count"],
        read_only=False
    ),
    "AE_Stream_Execution_Status_Workflow": WorkflowSpec(
        workflow_name="AE_Stream_Execution_Status_Workflow",
        description="Streams status of running batch execution.",
        target_system="TacticalRMM",
        risk_tier="R0",
        input_fields=["batch_id"],
        output_fields=["batch_id", "completed_count", "failed_count", "status"],
        read_only=True
    ),
    "AE_Collect_Process_Dump_Bot": WorkflowSpec(
        workflow_name="AE_Collect_Process_Dump_Bot",
        description="Generates memory dump of target server process (e.g. w3wp.exe).",
        target_system="Windows Server Diagnostics",
        risk_tier="R0",
        input_fields=["host_id", "process_name", "ticket_id"],
        output_fields=["dump_status", "dump_file"],
        read_only=True
    ),
    "AE_Restart_AppPool_Workflow": WorkflowSpec(
        workflow_name="AE_Restart_AppPool_Workflow",
        description="Recycles crashed IIS Application Pool.",
        target_system="IIS Web Server",
        risk_tier="R2",
        input_fields=["host_id", "app_pool_name", "ticket_id"],
        output_fields=["app_pool_status", "recycled_timestamp"],
        read_only=False
    ),
    "AE_Http_Health_Check_Workflow": WorkflowSpec(
        workflow_name="AE_Http_Health_Check_Workflow",
        description="Performs HTTP health probe on endpoint URL.",
        target_system="Synthetic Monitor",
        risk_tier="R0",
        input_fields=["endpoint_url"],
        output_fields=["http_status", "latency_ms", "health_state"],
        read_only=True
    ),
    "AE_Scan_DB_Directory_Bot": WorkflowSpec(
        workflow_name="AE_Scan_DB_Directory_Bot",
        description="Scans database host storage directories.",
        target_system="SQL Server Host",
        risk_tier="R0",
        input_fields=["host_id", "db_name"],
        output_fields=["db_name", "data_size_gb", "log_size_gb", "drive_free_pct"],
        read_only=True
    ),
    "AE_Backup_SQL_Logs_Workflow": WorkflowSpec(
        workflow_name="AE_Backup_SQL_Logs_Workflow",
        description="Performs point-in-time backup of SQL transaction logs.",
        target_system="SQL Server",
        risk_tier="R1",
        input_fields=["host_id", "db_name", "ticket_id"],
        output_fields=["backup_status", "backup_file"],
        read_only=False
    ),
    "AE_Truncate_SQL_Logs_Workflow": WorkflowSpec(
        workflow_name="AE_Truncate_SQL_Logs_Workflow",
        description="Truncates inactive virtual log files to reclaim disk space (High Risk - Lead DBA sign-off).",
        target_system="SQL Server",
        risk_tier="R3",
        input_fields=["host_id", "db_name", "ticket_id"],
        output_fields=["truncation_status", "free_space_status", "reclaimed_gb"],
        read_only=False
    ),

    # ── SAAS WORKFLOWS ──
    "AE_SAAS_001_AssignSaaSRole": WorkflowSpec(
        workflow_name="AE_SAAS_001_AssignSaaSRole",
        description="Assign workspace role or elevate seat in SaaS platform.",
        target_system="Enterprise SaaS API",
        risk_tier="R2",
        input_fields=["user_id", "saas_platform", "role_name", "ticket_id"],
        output_fields=["assignment_status", "saas_grant_id"],
        read_only=False
    ),
    "AE_SAAS_002_ReclaimSaaSSeat": WorkflowSpec(
        workflow_name="AE_SAAS_002_ReclaimSaaSSeat",
        description="Reclaim unused enterprise SaaS license seat.",
        target_system="Enterprise SaaS API",
        risk_tier="R2",
        input_fields=["user_id", "saas_platform", "ticket_id"],
        output_fields=["reclaim_status", "released_seat_id"],
        read_only=False
    ),

    # ── HARDWARE & CMDB WORKFLOWS ──
    "AE_HW_001_GetAssetDetails": WorkflowSpec(
        workflow_name="AE_HW_001_GetAssetDetails",
        description="Query ServiceNow / CMDB for physical asset attributes, serial number, and assigned owner.",
        target_system="ServiceNow CMDB",
        risk_tier="R0",
        input_fields=["asset_tag_or_serial"],
        output_fields=["ci_id", "asset_tag", "serial_number", "device_name", "model_name", "manufacturer", "assigned_user_email", "install_status", "warranty_status", "warranty_expiry"],
        read_only=True
    ),
    "AE_HW_002_CheckWarranty": WorkflowSpec(
        workflow_name="AE_HW_002_CheckWarranty",
        description="Check OEM warranty status via serial number lookup.",
        target_system="OEM Warranty API",
        risk_tier="R0",
        input_fields=["serial_number", "manufacturer"],
        output_fields=["warranty_active", "warranty_expiry", "service_level"],
        read_only=True
    ),
    "AE_HW_010_UpdateCIState": WorkflowSpec(
        workflow_name="AE_HW_010_UpdateCIState",
        description="Update CMDB Configuration Item install status and condition notes.",
        target_system="ServiceNow CMDB",
        risk_tier="R1",
        input_fields=["ci_id", "new_install_status", "condition_notes", "ticket_id"],
        output_fields=["update_status", "modified_timestamp"],
        read_only=False
    ),
    "AE_HW_020_OrderReplacement": WorkflowSpec(
        workflow_name="AE_HW_020_OrderReplacement",
        description="Dispatch a hardware replacement shipment order via enterprise procurement.",
        target_system="Procurement / Dispatch API",
        risk_tier="R2",
        input_fields=["ci_id", "serial_number", "shipping_address", "approval_id", "ticket_id"],
        output_fields=["order_id", "tracking_number", "estimated_delivery", "status"],
        read_only=False
    ),

    # ── SERVICENOW TICKET MANAGEMENT ──
    "AE_SNOW_001_CreateTicket": WorkflowSpec(
        workflow_name="AE_SNOW_001_CreateTicket",
        description="Create an incident or service request ticket in ServiceNow.",
        target_system="ServiceNow Table API",
        risk_tier="R1",
        input_fields=["requester_email", "short_description", "description", "category", "urgency"],
        output_fields=["sys_id", "ticket_number", "state", "created_at"],
        read_only=False
    ),
    "AE_SNOW_001_CreateRequest": WorkflowSpec(
        workflow_name="AE_SNOW_001_CreateRequest",
        description="Creates a service catalog request in ServiceNow.",
        target_system="ServiceNow Table API",
        risk_tier="R1",
        input_fields=["requester_email", "short_description"],
        output_fields=["sys_id", "request_number"],
        read_only=False
    ),
    "AE_SNOW_002_CreateApproval": WorkflowSpec(
        workflow_name="AE_SNOW_002_CreateApproval",
        description="Creates sysapproval_approver record in ServiceNow.",
        target_system="ServiceNow Table API",
        risk_tier="R1",
        input_fields=["ticket_id", "approver_email"],
        output_fields=["approval_sys_id", "status"],
        read_only=False
    ),
    "AE_SNOW_003_UpdateTicket": WorkflowSpec(
        workflow_name="AE_SNOW_003_UpdateTicket",
        description="Update work notes, resolution code, and state of a ServiceNow ticket.",
        target_system="ServiceNow Table API",
        risk_tier="R1",
        input_fields=["ticket_id", "work_notes", "state", "resolution_code", "customer_summary"],
        output_fields=["update_status", "updated_at"],
        read_only=False
    ),
    "AE_SNOW_004_WriteAuditEvidence": WorkflowSpec(
        workflow_name="AE_SNOW_004_WriteAuditEvidence",
        description="Writes immutable governance audit evidence to ticket work notes.",
        target_system="ServiceNow Table API",
        risk_tier="R1",
        input_fields=["ticket_id", "evidence_payload"],
        output_fields=["audit_logged"],
        read_only=False
    ),

    # ── NOTIFICATIONS & EMAIL APPROVAL ──
    "AE_NOTIFY_001_SendApprovalEmail": WorkflowSpec(
        workflow_name="AE_NOTIFY_001_SendApprovalEmail",
        description="Sends structured manager approval email via Microsoft Graph sendMail.",
        target_system="Microsoft Graph API",
        risk_tier="R1",
        input_fields=["subject", "html_body", "recipient"],
        output_fields=["send_status", "message_id", "sent_at"],
        read_only=False
    )
}
