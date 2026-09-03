import json
import os
from typing import Dict, Any, Optional
from core.models import RiskTier, ApprovalStatus

class PolicyDecisionPoint:
    def __init__(self, policies_path: Optional[str] = None):
        if not policies_path:
            policies_path = os.path.join(os.path.dirname(__file__), "..", "data", "policies.json")
        
        with open(policies_path, "r", encoding="utf-8") as f:
            self.policy_data = json.load(f)
        
        self.risk_tiers = self.policy_data.get("risk_tiers", {})
        self.action_policies = self.policy_data.get("action_policies", {})

    def evaluate(self, action_name: str, parameters: Dict[str, Any], approval_record: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evaluates whether an action is ALLOWED, REQUIRES_APPROVAL, or DENIED.
        """
        policy = self.action_policies.get(action_name)
        if not policy:
            # Unregistered workflow is denied by default (Fail Closed)
            return {
                "decision": "DENY",
                "risk_tier": "R4",
                "reason": f"Workflow '{action_name}' is not in the approved policy catalog."
            }

        risk_tier = policy.get("risk_tier", "R2")
        requires_approval = policy.get("approval_required", False)

        # R0 & R1 are Auto-Approved
        if risk_tier in ["R0", "R1"] or not requires_approval:
            return {
                "decision": "ALLOW",
                "risk_tier": risk_tier,
                "reason": f"Action '{action_name}' is pre-approved under Tier {risk_tier} policy."
            }

        # R2 & R3 require signed approval
        if requires_approval:
            if approval_record and approval_record.get("status") == ApprovalStatus.APPROVED:
                return {
                    "decision": "ALLOW",
                    "risk_tier": risk_tier,
                    "reason": f"Action '{action_name}' has verified signed approval from {approval_record.get('approver_email')}."
                }
            else:
                return {
                    "decision": "APPROVAL_NEEDED",
                    "risk_tier": risk_tier,
                    "approver_type": policy.get("approver_type", "MANAGER"),
                    "reason": f"Action '{action_name}' requires {policy.get('approver_type', 'MANAGER')} approval before execution."
                }

        return {
            "decision": "DENY",
            "risk_tier": risk_tier,
            "reason": "Policy conditions not met."
        }
