import unittest
from core.models import ApprovalStatus, VerificationStatus
from orchestrator import AutonomousITOrchestrator

class TestAccessWorkflow(unittest.TestCase):
    def setUp(self):
        self.orchestrator = AutonomousITOrchestrator(use_mock_ae=True)

    def test_access_request_pending_approval(self):
        # Without approval decision -> Should halt at PENDING_APPROVAL
        result = self.orchestrator.process_request(
            query_text="Please grant me GitHub Enterprise developer access",
            requester_email="alex.murphy@enterprise.com",
            approval_decision=None
        )
        self.assertEqual(result["ticket"]["status"], "PENDING_APPROVAL")
        self.assertIn("approval", result["user_response"].lower())

    def test_access_request_approved_and_verified(self):
        # With signed manager approval -> Should execute and verify in Entra ID
        result = self.orchestrator.process_request(
            query_text="Please grant me GitHub Enterprise developer access",
            requester_email="alex.murphy@enterprise.com",
            approval_decision=ApprovalStatus.APPROVED
        )
        self.assertEqual(result["ticket"]["status"], "RESOLVED")
        self.assertIsNotNone(result["verification"])
        self.assertTrue(result["verification"]["verified"])
        self.assertEqual(result["verification"]["status"], VerificationStatus.MATCH)
        self.assertIn("verified in entra id", result["user_response"].lower())

if __name__ == "__main__":
    unittest.main()
