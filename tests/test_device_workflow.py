import unittest
from core.models import ApprovalStatus, VerificationStatus
from orchestrator import AutonomousITOrchestrator

class TestDeviceWorkflow(unittest.TestCase):
    def setUp(self):
        self.orchestrator = AutonomousITOrchestrator(use_mock_ae=True)

    def test_non_compliant_device_remediation(self):
        # Alex Murphy has a non-compliant Windows 11 device (DEV-WIN-102)
        result = self.orchestrator.process_request(
            query_text="My laptop is showing non-compliant, can you fix it?",
            requester_email="alex.murphy@enterprise.com",
            approval_decision=ApprovalStatus.APPROVED
        )
        self.assertEqual(result["ticket"]["status"], "RESOLVED")
        self.assertIsNotNone(result["verification"])
        self.assertTrue(result["verification"]["verified"])
        self.assertEqual(result["verification"]["status"], VerificationStatus.MATCH)
        self.assertIn("verified", result["user_response"].lower())

    def test_bitlocker_key_retrieval(self):
        result = self.orchestrator.process_request(
            query_text="I need my BitLocker recovery key for my laptop",
            requester_email="sarah.connor@enterprise.com",
            approval_decision=ApprovalStatus.APPROVED
        )
        self.assertEqual(result["ticket"]["status"], "RESOLVED")
        self.assertIn("bitlocker recovery key", result["user_response"].lower())

if __name__ == "__main__":
    unittest.main()
