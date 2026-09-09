"""
Intelligent Command Privilege Management & Execution Classifier.
Determines whether PowerShell/shell commands and AutomationEdge workflows require
Administrator (NT AUTHORITY\\SYSTEM, RunAsUser: false) or Standard User (RunAsUser: true) execution context.
"""

import re
from enum import Enum
from typing import Dict, Any, Tuple

class ExecutionPrivilege(str, Enum):
    ADMINISTRATOR = "ADMINISTRATOR"  # Tactical RMM SYSTEM Service (RunAsUser = "false")
    STANDARD_USER = "STANDARD_USER"  # Logged-in Interactive User (RunAsUser = "true")


class PrivilegeClassifier:
    """
    Intelligently analyzes commands, scripts, and workflows to determine the exact
    required execution privilege level (Administrator vs Standard User).
    """

    # Commands/keywords that strictly require elevated Administrator (SYSTEM / RunAsUser: false)
    ADMIN_PATTERNS = [
        # System Power / Reboot / Shutdown
        r"\bshutdown(\.exe)?\b",
        r"\brestart-computer\b",
        r"\bstop-computer\b",
        r"\bpowercfg\b\s+(?!/batteryreport)",
        r"\breboot\b",

        # Windows Service Management
        r"\brestart-service\b",
        r"\bstop-service\b",
        r"\bstart-service\b",
        r"\bset-service\b",
        r"\bnet\s+(stop|start|pause|continue)\b",
        r"\bsc(\.exe)?\s+(config|stop|start|delete|create)\b",

        # Network Stack, Adapter Reset & Firewall
        r"\bnetsh\b",
        r"\brestart-netadapter\b",
        r"\benable-netadapter\b",
        r"\bdisable-netadapter\b",
        r"\bset-netfirewallrule\b",
        r"\bnew-netfirewallrule\b",
        r"\bset-netipinterface\b",
        r"\bclear-dnsclientcache\b",
        r"\breset-netadapteradvancedproperty\b",

        # Disk, File System, Temp & Shadow Copies
        r"\bchkdsk\b",
        r"\bdefrag\b",
        r"\bvssadmin\b",
        r"\boptimize-volume\b",
        r"\bc:\\windows\\temp\b",
        r"\bremove-item\s+.*c:\\windows\\temp\b",
        r"\bclear-recyclebin\b",

        # System Integrity, DISM & SFC
        r"\bsfc\s+/scannow\b",
        r"\bdism(\.exe)?\b",
        r"\bgpupdate\s+/force\b",
        r"\bwevtutil\s+cl\b",
        r"\bclear-eventlog\b",
        r"\bbcdedit\b",

        # Security, Antivirus, BitLocker & TPM
        r"\bmanage-bde\b",
        r"\bstart-mpscan\b",
        r"\bupdate-mpsignature\b",
        r"\bset-mppreference\b",
        r"\badd-mppreference\b",
        r"\benable-bitlocker\b",
        r"\bdisable-bitlocker\b",
        r"\block-bitlocker\b",
        r"\bunlock-bitlocker\b",
        r"\binitialize-tpm\b",
        r"\bclear-tpm\b",

        # Software Installation & Windows Update
        r"\bwusa(\.exe)?\b",
        r"\binstall-windowsupdate\b",
        r"\bwuauclt\b",
        r"\binstall-package\b",
        r"\buninstall-package\b",
        r"\bmsiexec(\.exe)?\s+/i\b",
        r"\bmsiexec(\.exe)?\s+/x\b",
        r"\bchoco\s+(install|upgrade|uninstall)\b",
        r"\bwinget\s+(install|upgrade|uninstall)\b",

        # Registry Modifications (HKLM / System)
        r"\bhklm:\\",
        r"\bhkey_local_machine\b",
        r"\breg\s+(add|delete)\s+hklm\b",
        r"\bset-itemproperty\s+.*hklm\b",
        r"\bnew-item\s+.*hklm\b",

        # Process Termination (Elevated / Force)
        r"\bstop-process\s+-force\b",
        r"\btaskkill\s+/f\s+/im\b",
        r"\btaskkill\s+/f\s+/pid\b"
    ]

    # Specific workflows that mandate Administrator / Elevated context
    ADMIN_WORKFLOWS = {
        "AE_DEV_011_RestartDevice",
        "AE_DEV_012_RemediateCompliance",
        "AE_DEV_022_ApplyRemediationScript",
        "AE_Safe_Temp_Cleanup_Workflow",
        "AE_Restart_Service_Workflow",
        "AE_Restart_VPN_Daemon_Workflow",
        "AE_Execute_TacticalRMM_Patch_Workflow",
        "AE_SEC_001_IsolateHost",
        "AE_SEC_002_CaptureMemoryForensics",
        "AE_ONB_001_DeployPackageBundle",
        "AE_ONB_002_ApplySecurityBaseline",
        "AE_Execute_Fleet_Batch_Script",
        "AE_Restart_AppPool_Workflow",
        "AE_Truncate_SQL_Logs_Workflow"
    }

    # Commands/keywords that strictly target standard user context (whoami, user environment, read-only telemetry)
    USER_PATTERNS = [
        r"^\s*whoami\s*$",
        r"^\s*whoami\s+/groups\s*$",
        r"^\s*whoami\s+/priv\s*$",
        r"\b\$env:username\b",
        r"\b\$env:userprofile\b",
        r"\b\$env:localappdata\b",
        r"\b\$env:appdata\b",
        r"^\s*ipconfig\s*/all\s*$",
        r"^\s*ipconfig\s*$",
        r"\bget-process\s*\|\s*sort-object\s+cpu\b",
        r"\bget-psdrive\s+-psprovider\s+filesystem\b",
        r"\bget-printer\b",
        r"\bpowercfg\s+/batteryreport\b"
    ]

    @classmethod
    def classify_command(cls, command: str) -> Tuple[ExecutionPrivilege, str]:
        """
        Classifies a shell/PowerShell command into ExecutionPrivilege.ADMINISTRATOR or ExecutionPrivilege.STANDARD_USER.
        Returns a tuple of (ExecutionPrivilege, Reason).
        """
        if not command or not command.strip():
            return ExecutionPrivilege.STANDARD_USER, "Default standard user context for empty command."

        cmd_clean = command.strip().lower()

        # Check explicit admin patterns
        for pattern in cls.ADMIN_PATTERNS:
            if re.search(pattern, cmd_clean, re.IGNORECASE):
                return ExecutionPrivilege.ADMINISTRATOR, f"Command matches elevated administrative operation: '{pattern}'"

        # Check explicit user patterns
        for pattern in cls.USER_PATTERNS:
            if re.search(pattern, cmd_clean, re.IGNORECASE):
                return ExecutionPrivilege.STANDARD_USER, f"Command matches standard user telemetry operation: '{pattern}'"

        # Read-only query heuristics
        if any(cmd_clean.startswith(prefix) for prefix in ["get-ciminstance", "get-wmiobject", "test-connection", "ping", "nslookup", "tracert"]):
            return ExecutionPrivilege.STANDARD_USER, "Read-only inspection/telemetry command safe for user context."

        # Modification / destructive keywords fallback to Admin
        if any(k in cmd_clean for k in ["restart", "reboot", "shutdown", "stop", "start", "kill", "purge", "clear", "remove", "delete", "set-", "new-"]):
            return ExecutionPrivilege.ADMINISTRATOR, "Command contains modification/control verbs requiring elevated privileges."

        # Default to standard user for diagnostic safety
        return ExecutionPrivilege.STANDARD_USER, "Standard diagnostic query execution."

    @classmethod
    def get_run_as_user_flag(cls, command_or_workflow: str) -> str:
        """
        Returns 'false' (Run as Administrator / SYSTEM) or 'true' (Run as Logged-in User)
        compatible with Tactical RMM and AutomationEdge Get_Agent_Run_Cmd.
        """
        if command_or_workflow in cls.ADMIN_WORKFLOWS:
            return "false"

        privilege, _ = cls.classify_command(command_or_workflow)
        return "false" if privilege == ExecutionPrivilege.ADMINISTRATOR else "true"

    @classmethod
    def explain_privilege_requirement(cls, command_or_workflow: str) -> Dict[str, Any]:
        """Returns structured explanation of the execution context."""
        privilege, reason = cls.classify_command(command_or_workflow)
        is_admin = (privilege == ExecutionPrivilege.ADMINISTRATOR) or (command_or_workflow in cls.ADMIN_WORKFLOWS)
        run_as_user = "false" if is_admin else "true"

        return {
            "privilege": ExecutionPrivilege.ADMINISTRATOR.value if is_admin else ExecutionPrivilege.STANDARD_USER.value,
            "run_as_user": run_as_user,
            "execution_context": "NT AUTHORITY\\SYSTEM (Elevated Administrator)" if is_admin else "Logged-in Interactive User Session",
            "reason": reason,
            "security_governance": "Requires administrative policy check / risk authorization" if is_admin else "Safe diagnostic telemetry execution"
        }
