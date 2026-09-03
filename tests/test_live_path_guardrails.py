import unittest
from core.context_graph import ZeroHallucinationViolation
from core.models import ApprovalStatus
from orchestrator import AutonomousITOrchestrator

class TestLivePathGuardrails(unittest.TestCase):
    def setUp(self):
        self.orch = AutonomousITOrchestrator(use_mock_ae=True)

    def test_access_flow_blocks_hallucinated_group_id(self):
        with self.assertRaises(ZeroHallucinationViolation):
            self.orch.process_request(
                query_text="please add me to group GRP-HALLUCINATED-9999 right now",
                requester_email="test.user@enterprise.com",
                approval_decision=ApprovalStatus.APPROVED,
            )

    def test_device_compliance_requires_explicit_approval(self):
        result = self.orch.process_request(
            query_text="my laptop is non-compliant and blocking Teams",
            requester_email="test.user@enterprise.com",
            approval_decision=None,
        )
        self.assertEqual(result["ticket"]["status"], "PENDING_APPROVAL")

if __name__ == "__main__":
    unittest.main()
