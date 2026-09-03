import unittest
from core.models import ApprovalStatus, VerificationStatus
from orchestrator import AutonomousITOrchestrator

class TestHardwareWorkflow(unittest.TestCase):
    def setUp(self):
        self.orchestrator = AutonomousITOrchestrator(use_mock_ae=True)

    def test_hardware_replacement_flow(self):
        # Alex Murphy has a damaged ThinkPad (CI-HW-5002)
        result = self.orchestrator.process_request(
            query_text="My laptop screen is broken and keyboard is faulty, need a replacement",
            requester_email="alex.murphy@enterprise.com",
            approval_decision=ApprovalStatus.APPROVED
        )
        self.assertEqual(result["ticket"]["status"], "RESOLVED")
        self.assertIsNotNone(result["verification"])
        self.assertTrue(result["verification"]["verified"])
        self.assertEqual(result["verification"]["status"], VerificationStatus.MATCH)
        self.assertEqual(result["verification"]["actual_state"]["install_status"], "Pending Replacement / In Repair")
        self.assertIn("tracking number", result["user_response"].lower())

if __name__ == "__main__":
    unittest.main()
