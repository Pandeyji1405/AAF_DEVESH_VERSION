import unittest
from core.context_graph import ContextGraph, ZeroHallucinationViolation
from core.policy_engine import PolicyDecisionPoint
from core.hitl import HumanInTheLoopManager
from automationedge.client import AutomationEdgeClient
from core.base_agent import BaseAgent




class TestGuardrails(unittest.TestCase):
    def setUp(self):
        self.ae_client = AutomationEdgeClient(use_mock=True)
        self.policy_engine = PolicyDecisionPoint()
        self.hitl_manager = HumanInTheLoopManager()
        self.agent = BaseAgent("Test_Agent", self.ae_client, self.policy_engine, self.hitl_manager)

    def test_zero_hallucination_blocks_unverified_id(self):
        # Empty Context Graph with no corroborated evidence
        graph = ContextGraph(ticket_id="INC-TEST-001", requester_email="test@enterprise.com")
        
        # Agent tries to execute a group addition on an unverified hallucinated group GUID
        hallucinated_params = {
            "user_id": "USR-1001",
            "group_id": "GRP-HALLUCINATED-9999",
            "ticket_id": "INC-TEST-001"
        }

        # Should raise ZeroHallucinationViolation
        with self.assertRaises(ZeroHallucinationViolation) as ctx:
            self.agent.call_tool(graph, "AE_ACC_011_AddGroupMember", hallucinated_params)
        
        self.assertIn("Zero-Hallucination Violation", str(ctx.exception))

    def test_policy_blocks_unregistered_workflow(self):
        graph = ContextGraph(ticket_id="INC-TEST-002", requester_email="test@enterprise.com")
        graph.add_fact("user_id", "USR-1001")
        
        with self.assertRaises(PermissionError) as ctx:
            self.agent.call_tool(graph, "AE_UNREGISTERED_WORKFLOW_DELETE_ALL", {"user_id": "USR-1001"})
        
        self.assertIn("DENIED by policy", str(ctx.exception))

if __name__ == "__main__":
    unittest.main()
