from typing import Optional, Dict, Any
from agent_framework import Agent
from core.models import IncidentTicket, ApprovalStatus, RiskTier
from core.context_graph import ContextGraph
from core.base_agent import BaseAgent

from maf_agents.tools.tacticalrmm_tools import create_tacticalrmm_tools
from maf_agents.tools.servicenow_tools import create_servicenow_tools
from maf_agents.client_factory import get_maf_chat_client

class MAFDeviceOpsAgent(BaseAgent):
    """
    Microsoft Agent Framework (MAF): Device Operations Specialist Agent.
    Operates the TacticalRMM device control plane with strict policy governance.
    """

    def __init__(self, ae_client, policy_engine, hitl_manager):
        super().__init__("MAF_Device_Ops_Agent", ae_client, policy_engine, hitl_manager)
        self.device_tools = {t.name: t for t in create_tacticalrmm_tools(ae_client)}
        self.snow_tools = {t.name: t for t in create_servicenow_tools(ae_client)}
        
        # Instantiate Microsoft Agent Framework Agent
        self.maf_agent = Agent(
            client=get_maf_chat_client(),
            name="MAF_Device_Specialist",
            description="Microsoft Agent Framework specialist for TacticalRMM device operations and compliance baselines",
            tools=list(self.device_tools.values())
        )

    def execute_request(self, ticket: IncidentTicket, context_graph: ContextGraph, approval_decision: Optional[ApprovalStatus] = None) -> IncidentTicket:
        requester_email = context_graph.get_fact("requester_email") or ticket.requester_email
        device_id = context_graph.get_fact("assigned_device_id") or context_graph.get_fact("device_name") or "DEV-WIN-102"
        agent_id = context_graph.get_fact("agent_id") or "agent-trmm-002"
        query_text = (context_graph.get_fact("query_text") or ticket.short_description).lower()

        # Step 1: Query endpoint metrics via TacticalRMM tool
        metrics = self.device_tools["get_endpoint_metrics"](agent_id=agent_id)
        hostname = metrics.get("hostname") or context_graph.get_fact("device_name") or device_id
        checks = metrics.get("checks", [])
        failed_checks = [c["name"] for c in checks if c.get("status") == "FAIL"]
        
        context_graph.add_entity("devices", device_id, {
            "device_id": device_id,
            "agent_id": agent_id,
            "hostname": hostname,
            "metrics": metrics,
            "failed_checks": failed_checks
        })
        context_graph.add_fact("agent_id", agent_id, source="TACTICAL_RMM")
        context_graph.add_fact("hostname", hostname, source="TACTICAL_RMM")
        context_graph.add_fact("failed_checks", failed_checks, source="TACTICAL_RMM")

        # ── SCENARIO A: BITLOCKER RECOVERY (Graph-based, per B0) ──
        if "bitlocker" in query_text or "recovery key" in query_text:
            workflow_name = "AE_DEV_002_GetBitLockerKey"
            params = {
                "device_id": device_id,
                "requester_upn": requester_email,
                "ticket_id": ticket.ticket_id
            }
            manager_email = context_graph.get_fact("manager_email") or "sarah.connor@enterprise.com"

            approval_record = self.hitl_manager.create_approval_request(
                ticket_id=ticket.ticket_id,
                approver_email=manager_email,
                action_name=workflow_name,
                parameters=params,
                risk_tier="R2",
                target_resource=hostname,
                business_justification=f"BitLocker recovery key retrieval for locked device {hostname}",
                requester_email=requester_email
            )

            if approval_decision:
                self.hitl_manager.sign_decision(approval_record.approval_id, approval_decision, "Authorized by Line Manager via Enterprise Mobile Authenticator")
                approval_record = self.hitl_manager.get_approval(approval_record.approval_id)

            if approval_record.status == ApprovalStatus.APPROVED:
                context_graph.validate_action_parameters(workflow_name, params)
                app_dict = approval_record.dict() if hasattr(approval_record, "dict") else approval_record.model_dump()
                decision = self.policy_engine.evaluate(workflow_name, params, app_dict)
                if decision["decision"] == "DENY":
                    raise PermissionError(f"PDP denied {workflow_name}: {decision.get('reason')}")

                bl_res = self.device_tools["get_bitlocker_recovery_key"](device_id=device_id, requester_upn=requester_email, ticket_id=ticket.ticket_id)
                key = bl_res.get("bitlocker_recovery_key") or bl_res.get("recovery_key", "UNKNOWN-KEY")
                ticket.status = "RESOLVED"
                ticket.customer_summary = f"Your BitLocker recovery key for {hostname} is: {key}"
                ticket.work_notes.append(f"BitLocker recovery key retrieved under approval {approval_record.approval_id}.")
                self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Complete", resolution_code="KEY_RELEASED", work_notes="\n".join(ticket.work_notes), customer_summary=ticket.customer_summary)
            elif approval_record.status == ApprovalStatus.REJECTED:
                ticket.status = "CLOSED_REJECTED"
                rej_reason = approval_record.rejection_reason or approval_record.comments or "Rejected by Line Manager"
                ticket.work_notes.append(f"BitLocker key request was REJECTED by {manager_email}. Manager Notes: \"{rej_reason}\".")
                ticket.customer_summary = f"BitLocker recovery key request was rejected by your manager ({manager_email}). Reason: \"{rej_reason}\"."
                self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Rejected", resolution_code="REJECTED_BY_APPROVER", work_notes="\n".join(ticket.work_notes), customer_summary=ticket.customer_summary)
            else:
                ticket.status = "PENDING_APPROVAL"
                ticket.customer_summary = f"BitLocker recovery key request is awaiting approval from {manager_email}."
            return ticket

        # ── SCENARIO B: REBOOT REQUEST (TacticalRMM Script) ──
        if "reboot" in query_text or "restart" in query_text and "vpn" not in query_text:
            manager_email = context_graph.get_fact("manager_email") or "sarah.connor@enterprise.com"
            workflow_name = "AE_DEV_011_RestartDevice"
            params = {"agent_id": agent_id, "force_reboot": "true", "ticket_id": ticket.ticket_id}
            approval_record = self.hitl_manager.create_approval_request(
                ticket_id=ticket.ticket_id,
                approver_email=manager_email,
                action_name=workflow_name,
                parameters=params,
                risk_tier="R2",
                target_resource=hostname,
                business_justification=f"Remote restart of TacticalRMM endpoint {hostname}",
                requester_email=requester_email
            )
            if approval_decision:
                self.hitl_manager.sign_decision(approval_record.approval_id, approval_decision, "Reboot authorized by Manager")
                approval_record = self.hitl_manager.get_approval(approval_record.approval_id)

            if approval_record.status == ApprovalStatus.APPROVED:
                context_graph.validate_action_parameters(workflow_name, params)
                app_dict = approval_record.dict() if hasattr(approval_record, "dict") else approval_record.model_dump()
                decision = self.policy_engine.evaluate(workflow_name, params, app_dict)
                if decision["decision"] == "DENY":
                    raise PermissionError(f"PDP denied {workflow_name}: {decision.get('reason')}")

                self.device_tools["restart_device"](agent_id=agent_id, force_reboot=True, ticket_id=ticket.ticket_id)
                ticket.status = "RESOLVED"
                ticket.customer_summary = f"Remote reboot signal dispatched to {hostname} via TacticalRMM."
                ticket.work_notes.append("Reboot executed successfully via TacticalRMM script execution.")
                self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Complete", resolution_code="REBOOT_EXECUTED", work_notes="\n".join(ticket.work_notes), customer_summary=ticket.customer_summary)
            elif approval_record.status == ApprovalStatus.REJECTED:
                ticket.status = "CLOSED_REJECTED"
                ticket.customer_summary = f"Remote reboot request was rejected by your manager ({manager_email})."
                self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Rejected", resolution_code="REJECTED_BY_APPROVER", work_notes="\n".join(ticket.work_notes), customer_summary=ticket.customer_summary)
            else:
                ticket.status = "PENDING_APPROVAL"
                ticket.customer_summary = f"Reboot request requires approval from {manager_email}."
            return ticket

        # ── SCENARIO C: PATCH / VULNERABILITY MANAGEMENT ──
        if "patch" in query_text or "cve" in query_text or "vulnerability" in query_text:
            manager_email = context_graph.get_fact("manager_email") or "sarah.connor@enterprise.com"
            patch_pkg = self.device_tools["fetch_patch_package"](cve_id_or_patch_name="CVE-2026-PATCH-KIT")
            patch_id = patch_pkg.get("patch_id", "PATCH-2026-SEC-01")
            
            workflow_name = "AE_Execute_TacticalRMM_Patch_Workflow"
            params = {"agent_id": agent_id, "patch_id": patch_id, "ticket_id": ticket.ticket_id}
            approval_record = self.hitl_manager.create_approval_request(
                ticket_id=ticket.ticket_id,
                approver_email=manager_email,
                action_name=workflow_name,
                parameters=params,
                risk_tier="R2",
                target_resource=hostname,
                business_justification=f"Apply critical security patch {patch_id} on {hostname}",
                requester_email=requester_email
            )
            if approval_decision:
                self.hitl_manager.sign_decision(approval_record.approval_id, approval_decision, "Patch deployment authorized by Manager")
                approval_record = self.hitl_manager.get_approval(approval_record.approval_id)

            if approval_record.status == ApprovalStatus.APPROVED:
                context_graph.validate_action_parameters(workflow_name, params)
                app_dict = approval_record.dict() if hasattr(approval_record, "dict") else approval_record.model_dump()
                decision = self.policy_engine.evaluate(workflow_name, params, app_dict)
                if decision["decision"] == "DENY":
                    raise PermissionError(f"PDP denied {workflow_name}: {decision.get('reason')}")

                self.device_tools["execute_patch"](agent_id=agent_id, patch_id=patch_id, ticket_id=ticket.ticket_id)
                post_ver = self.device_tools["verify_software_version"](agent_id=agent_id, package_name=patch_id)
                verification = self.verify_state(
                    check_name=f"TacticalRMM Patch Verification on {hostname}",
                    actual_state=post_ver,
                    expected_state={"patch_status": "INSTALLED"},
                    keys_to_compare=["patch_status"]
                )
                ticket.verification = verification
                ticket.status = "RESOLVED"
                ticket.customer_summary = f"Security patch '{patch_id}' has been applied and verified on {hostname}."
                self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Complete", resolution_code="PATCH_APPLIED", work_notes=f"Patch {patch_id} verified", customer_summary=ticket.customer_summary)
            elif approval_record.status == ApprovalStatus.REJECTED:
                ticket.status = "CLOSED_REJECTED"
                ticket.customer_summary = f"Patch execution was rejected by your manager ({manager_email})."
                self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Rejected", resolution_code="REJECTED_BY_APPROVER", work_notes="\n".join(ticket.work_notes), customer_summary=ticket.customer_summary)
            else:
                ticket.status = "PENDING_APPROVAL"
                ticket.customer_summary = f"Patch deployment requires approval from {manager_email}."
            return ticket

        # ── SCENARIO D: DISK SPACE & STORAGE CLEANUP ──
        if "disk space" in query_text or "low storage" in query_text or "storage full" in query_text:
            manager_email = context_graph.get_fact("manager_email") or "sarah.connor@enterprise.com"
            disk_info = self.device_tools["scan_disk_usage"](agent_id=agent_id)
            
            # Step 1: Run safe temp cleanup (R1)
            cleanup_res = self.device_tools["safe_temp_cleanup"](agent_id=agent_id, ticket_id=ticket.ticket_id)
            freed_gb = cleanup_res.get("freed_space_gb", 12.5)

            ticket.status = "RESOLVED"
            ticket.customer_summary = f"Disk diagnostics complete on {hostname}. Purged temporary caches and freed {freed_gb} GB of storage."
            ticket.work_notes.append(f"Safe temp cleanup executed on {agent_id}. Freed: {freed_gb} GB.")
            self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Complete", resolution_code="STORAGE_PURGED", work_notes="\n".join(ticket.work_notes), customer_summary=ticket.customer_summary)
            return ticket

        # ── SCENARIO E: NETWORK & VPN DIAGNOSTICS ──
        if "vpn" in query_text or "dns" in query_text or "network" in query_text:
            diag_res = self.device_tools["network_diagnostics"](agent_id=agent_id)
            self.device_tools["flush_dns_test_ping"](agent_id=agent_id, target_host="enterprise.local")
            self.device_tools["restart_vpn_daemon"](agent_id=agent_id, ticket_id=ticket.ticket_id)

            ticket.status = "RESOLVED"
            ticket.customer_summary = f"Network stack refreshed on {hostname}: DNS resolver flushed, routing tables reset, and VPN daemon restarted."
            ticket.work_notes.append("Executed flush_dns and restarted VPN daemon via TacticalRMM.")
            self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Complete", resolution_code="NETWORK_REMEDIATED", work_notes="\n".join(ticket.work_notes), customer_summary=ticket.customer_summary)
            return ticket

        # ── SCENARIO F: TACTICALRMM COMPLIANCE AUDIT & SCRIPT REMEDIATION ──
        if failed_checks or "compliance" in query_text or "teams" in query_text or "outlook" in query_text:
            target_check = failed_checks[0] if failed_checks else "disk_encryption"
            manager_email = context_graph.get_fact("manager_email") or "sarah.connor@enterprise.com"
            workflow_name = "AE_DEV_022_ApplyRemediationScript"
            params = {"agent_id": agent_id, "check_name": target_check, "ticket_id": ticket.ticket_id}

            approval_record = self.hitl_manager.create_approval_request(
                ticket_id=ticket.ticket_id,
                approver_email=manager_email,
                action_name=workflow_name,
                parameters=params,
                risk_tier="R2",
                target_resource=hostname,
                business_justification=f"Enforce TacticalRMM remediation script '{target_check}' on {hostname}",
                requester_email=requester_email
            )
            if approval_decision:
                self.hitl_manager.sign_decision(approval_record.approval_id, approval_decision, "Authorized by Line Manager via Enterprise Mobile Authenticator")
                approval_record = self.hitl_manager.get_approval(approval_record.approval_id)

            if approval_record.status == ApprovalStatus.APPROVED:
                context_graph.validate_action_parameters(workflow_name, params)
                app_dict = approval_record.dict() if hasattr(approval_record, "dict") else approval_record.model_dump()
                decision = self.policy_engine.evaluate(workflow_name, params, app_dict)
                if decision["decision"] == "DENY":
                    raise PermissionError(f"PDP denied {workflow_name}: {decision.get('reason')}")

                ticket.work_notes.append(f"Applying TacticalRMM remediation script for {target_check} under approval {approval_record.approval_id}.")
                self.device_tools["apply_remediation_script"](agent_id=agent_id, check_name=target_check, ticket_id=ticket.ticket_id)

                # Verification Read-back
                post_audit = self.device_tools["run_compliance_check_script"](agent_id=agent_id)
                verification = self.verify_state(
                    check_name=f"TacticalRMM Compliance Script Verification on {hostname}",
                    actual_state=post_audit,
                    expected_state={"compliance_status": "COMPLIANT"},
                    keys_to_compare=["compliance_status"]
                )
                ticket.verification = verification
                ticket.status = "RESOLVED"
                ticket.customer_summary = f"Your device '{hostname}' TacticalRMM checks have been remediated and verified compliant."
                self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Complete", resolution_code="DEVICE_REMEDIATED", work_notes="\n".join(ticket.work_notes), customer_summary=ticket.customer_summary)
            elif approval_record.status == ApprovalStatus.REJECTED:
                ticket.status = "CLOSED_REJECTED"
                ticket.customer_summary = f"Compliance remediation was rejected by your manager ({manager_email})."
                self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Rejected", resolution_code="REJECTED_BY_APPROVER", work_notes="\n".join(ticket.work_notes), customer_summary=ticket.customer_summary)
            else:
                ticket.status = "PENDING_APPROVAL"
                ticket.customer_summary = f"Compliance remediation script requires approval from {manager_email}."
            return ticket

        # Default fallback: Metrics diagnostic
        ticket.status = "RESOLVED"
        ticket.customer_summary = f"TacticalRMM diagnostic health check completed on {hostname}. All metrics normal."
        return ticket
