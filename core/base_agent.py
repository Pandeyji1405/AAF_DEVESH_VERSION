from typing import Dict, Any, Optional
from core.models import (
    WorkflowExecutionStatus, VerificationResult, VerificationStatus
)
from core.context_graph import ContextGraph
from core.policy_engine import PolicyDecisionPoint
from core.hitl import HumanInTheLoopManager
from automationedge.client import AutomationEdgeClient

class BaseAgent:
    """
    Base Agent for Microsoft Agent Framework (MAF).
    Provides the strict 4-stage governance execution pipeline and verification read-back.
    """

    def __init__(self, agent_name: str, ae_client: AutomationEdgeClient, 
                 policy_engine: PolicyDecisionPoint, hitl_manager: HumanInTheLoopManager):
        self.agent_name = agent_name
        self.ae_client = ae_client
        self.policy_engine = policy_engine
        self.hitl_manager = hitl_manager

    def call_tool(self, context_graph: ContextGraph, workflow_name: str, 
                  parameters: Dict[str, Any], approval_record: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes an action through the strict 4-stage governance pipeline:
        1. Context Graph Zero-Hallucination Parameter Verification
        2. Deterministic Policy Decision Point (PDP) Check
        3. Human-In-The-Loop Approval Verification (for R2/R3)
        4. AutomationEdge Execution Call
        """
        # Stage 1: Zero-Hallucination Guardrail
        context_graph.validate_action_parameters(workflow_name, parameters)

        # Stage 2: Policy Decision Point Evaluation
        policy_eval = self.policy_engine.evaluate(workflow_name, parameters, approval_record)
        if policy_eval["decision"] == "DENY":
            raise PermissionError(f"Action '{workflow_name}' DENIED by policy: {policy_eval.get('reason')}")

        if policy_eval["decision"] == "APPROVAL_NEEDED":
            return {
                "status": WorkflowExecutionStatus.PENDING_APPROVAL.value,
                "approver_type": policy_eval.get("approver_type"),
                "reason": policy_eval.get("reason"),
                "workflowResponse": None
            }

        # Stage 4: AutomationEdge API Execution
        ae_response = self.ae_client.execute_workflow(workflow_name, parameters)
        
        # Hydrate raw facts back into Context Graph
        wf_resp = ae_response.get("workflowResponse", {})
        if isinstance(wf_resp, dict):
            for k, v in wf_resp.items():
                if isinstance(v, (str, int, float, bool)):
                    context_graph.add_fact(f"{workflow_name}.{k}", v, source="AE_TELEMETRY")

        return ae_response

    def verify_state(self, check_name: str, actual_state: Dict[str, Any], 
                     expected_state: Dict[str, Any], keys_to_compare: list) -> VerificationResult:
        """
        Strict Verification Step:
        Re-reads actual system state and compares it against expected outcome.
        """
        discrepancies = []
        for key in keys_to_compare:
            actual_val = actual_state.get(key)
            expected_val = expected_state.get(key)
            
            # Special case for lists (e.g. membership checks)
            if isinstance(expected_val, str) and isinstance(actual_val, list):
                if expected_val not in actual_val:
                    discrepancies.append(f"Expected item '{expected_val}' not found in actual list {key}: {actual_val}")
            elif actual_val != expected_val:
                discrepancies.append(f"Field '{key}' mismatch: expected '{expected_val}', got '{actual_val}'")

        is_match = len(discrepancies) == 0
        return VerificationResult(
            verified=is_match,
            status=VerificationStatus.MATCH if is_match else VerificationStatus.NO_MATCH,
            target_entity=check_name,
            actual_state=actual_state,
            expected_state=expected_state,
            discrepancy_notes="; ".join(discrepancies) if discrepancies else "All parameters verified matching expected target state."
        )
