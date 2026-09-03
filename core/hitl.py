import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from core.models import ApprovalRecord, ApprovalStatus, ApprovalDecisionChannel

class HumanInTheLoopManager:
    def __init__(self):
        self.approval_store: Dict[str, ApprovalRecord] = {}

    def create_approval_request(self, ticket_id: str, approver_email: str, action_name: str, 
                                parameters: Dict[str, Any], risk_tier: str = "R2",
                                target_resource: Optional[str] = None,
                                business_justification: Optional[str] = None,
                                requester_email: Optional[str] = None) -> ApprovalRecord:
        """Generates a formal approval record (e.g. sysapproval_approver / Jira / Teams Approval)."""
        approval_id = f"APPR-{uuid.uuid4().hex[:8].upper()}"
        ref_token = uuid.uuid4().hex[:16]
        record = ApprovalRecord(
            approval_id=approval_id,
            ticket_id=ticket_id,
            approver_email=approver_email,
            action_name=action_name,
            parameters=parameters,
            status=ApprovalStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            risk_tier=risk_tier,
            target_resource=target_resource or parameters.get("agent_id") or parameters.get("device_id") or parameters.get("host_id") or parameters.get("group_id") or parameters.get("ci_id") or "N/A",
            business_justification=business_justification or f"Execution of {action_name} requested under ticket {ticket_id}",
            requester_email=requester_email or parameters.get("requester_upn") or parameters.get("user_id") or "requester@enterprise.com",
            reference_token=ref_token,
            token_consumed=False
        )
        self.approval_store[approval_id] = record
        return record

    def get_approval(self, approval_id_or_ref: str) -> Optional[ApprovalRecord]:
        if approval_id_or_ref in self.approval_store:
            return self.approval_store[approval_id_or_ref]
        for r in self.approval_store.values():
            if r.reference_token == approval_id_or_ref:
                return r
        return None

    def sign_decision(self, approval_id: str, decision: ApprovalStatus, comments: str = "", 
                      channel: Optional[ApprovalDecisionChannel] = None,
                      rejection_reason: Optional[str] = None) -> Optional[ApprovalRecord]:
        """Records an approver signing off on an action."""
        record = self.approval_store.get(approval_id)
        if record:
            record.status = decision
            record.decided_at = datetime.now(timezone.utc)
            record.comments = comments
            record.manager_notes = comments
            if channel:
                record.decision_channel = channel
            if rejection_reason:
                record.rejection_reason = rejection_reason
        return record

    def mark_token_consumed(self, approval_id: str) -> bool:
        record = self.approval_store.get(approval_id)
        if record:
            record.token_consumed = True
            return True
        return False

    def set_requested_info(self, approval_id: str, requested_info: List[str]):
        record = self.approval_store.get(approval_id)
        if record:
            record.requested_additional_info = requested_info

    def render_teams_adaptive_card(self, approval_record: ApprovalRecord) -> Dict[str, Any]:
        """
        Generates a standard Microsoft Teams Adaptive Card (JSON schema v1.5) payload.
        """
        status_color = "good" if approval_record.status == ApprovalStatus.APPROVED else (
            "attention" if approval_record.status == ApprovalStatus.REJECTED else "warning"
        )
        
        facts = [
            {"title": "Approval ID:", "value": approval_record.approval_id},
            {"title": "Ticket Ref:", "value": approval_record.ticket_id},
            {"title": "Requester:", "value": approval_record.requester_email or "Unknown"},
            {"title": "Approver:", "value": approval_record.approver_email},
            {"title": "Risk Tier:", "value": f"Tier {approval_record.risk_tier}"},
            {"title": "Proposed Action:", "value": approval_record.action_name},
            {"title": "Target Resource:", "value": str(approval_record.target_resource)},
            {"title": "Justification:", "value": str(approval_record.business_justification)}
        ]

        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.5",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "🛡️ Governance Approval Required",
                    "weight": "Bolder",
                    "size": "Medium",
                    "color": status_color
                },
                {
                    "type": "FactSet",
                    "facts": facts
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "✅ Approve Action",
                    "data": {
                        "approval_id": approval_record.approval_id,
                        "action": "APPROVE"
                    }
                },
                {
                    "type": "Action.Submit",
                    "title": "❌ Reject Request",
                    "data": {
                        "approval_id": approval_record.approval_id,
                        "action": "REJECT"
                    }
                }
            ]
        }
        return card

    def render_approval_card(self, approval_id: str) -> str:
        """
        Renders a ServiceNow / TacticalRMM style terminal approval card.
        """
        record = self.get_approval(approval_id)
        if not record:
            return f"[ERROR: Approval {approval_id} not found]"

        status_badge = {
            ApprovalStatus.PENDING: "⏳ [ PENDING HUMAN APPROVAL ]",
            ApprovalStatus.APPROVED: "✅ [ APPROVED & SIGNED ]",
            ApprovalStatus.REJECTED: "❌ [ REJECTED ]",
            ApprovalStatus.NOT_REQUIRED: "⚪ [ AUTO-APPROVED / NOT REQUIRED ]"
        }.get(record.status, str(record.status))

        tier_desc = {
            "R0": "R0 (Read-Only Diagnostic)",
            "R1": "R1 (Low-Risk Reversible Write)",
            "R2": "R2 (Standard User Impacting Write)",
            "R3": "R3 (High Privilege / Security Impact)",
            "R4": "R4 (Prohibited Action)"
        }.get(record.risk_tier, str(record.risk_tier))

        param_lines = []
        for k, v in record.parameters.items():
            param_lines.append(f"  │   • {k:<20}: {v}")
        param_block = "\n".join(param_lines) if param_lines else "  │   • (None)"

        created_str = record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else "NOW"
        lines = [
            "  ┌" + "─"*78 + "┐",
            "  │ 🛡️  SERVICENOW / MAF GOVERNANCE — HUMAN-IN-THE-LOOP APPROVAL CARD       │",
            "  ├" + "─"*78 + "┤",
            f"  │ Approval ID    : {record.approval_id:<25} Status   : {status_badge:<25}│",
            f"  │ Ticket Ref     : {record.ticket_id:<25} Risk Tier: {tier_desc:<25}│",
            f"  │ Created UTC    : {created_str:<25} System   : TacticalRMM / Entra / CMDB │",
            "  ├" + "─"*78 + "┤",
            f"  │ Requester      : {record.requester_email:<60} │",
            f"  │ Designated HITL: {record.approver_email:<60} │",
            "  ├" + "─"*78 + "┤",
            f"  │ Proposed Tool  : {record.action_name:<60} │",
            f"  │ Target Entity  : {str(record.target_resource):<60} │",
            f"  │ Justification  : {str(record.business_justification)[:60]:<60} │",
            "  │ Parameters     :                                                              │",
            param_block,
            "  ├" + "─"*78 + "┤",
            "  │ Policy Check   : PDP verified mandatory approval rule before AE execution     │",
        ]

        if record.status == ApprovalStatus.APPROVED:
            decided_str = record.decided_at.strftime('%Y-%m-%d %H:%M:%S') if record.decided_at else 'NOW'
            lines.extend([
                "  ├" + "─"*78 + "┤",
                f"  │ DECISION SIGNED: ✅ APPROVED by {record.approver_email:<45} │",
                f"  │ Signed At      : {decided_str:<60} │",
                f"  │ Signer Comment : {str(record.comments)[:60]:<60} │",
            ])
        elif record.status == ApprovalStatus.REJECTED:
            lines.extend([
                "  ├" + "─"*78 + "┤",
                f"  │ DECISION SIGNED: ❌ REJECTED by {record.approver_email:<45} │",
                f"  │ Reason         : {str(record.comments)[:60]:<60} │",
            ])
        else:
            lines.extend([
                "  ├" + "─"*78 + "┤",
                "  │ CONTROLS       : [ ✅ 1. APPROVE ]   [ ❌ 2. REJECT ]   [ ℹ️ 3. REQUEST INFO ] │",
            ])

        lines.append("  └" + "─"*78 + "┘")
        return "\n".join(lines)
