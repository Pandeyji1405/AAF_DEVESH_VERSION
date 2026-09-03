import unittest
from core.models import ApprovalStatus
from core.context_graph import ZeroHallucinationViolation
from orchestrator import AutonomousITOrchestrator

class TestTacticalRMMWorkflows(unittest.TestCase):
    def setUp(self):
        self.orch = AutonomousITOrchestrator(use_mock_ae=True)

    def test_tacticalrmm_compliance_remediation_with_approval(self):
        res = self.orch.process_request(
            query_text="my laptop DEV-WIN-102 failed compliance checks and is blocking Teams",
            requester_email="alex.murphy@enterprise.com",
            approval_decision=ApprovalStatus.APPROVED
        )
        self.assertEqual(res["ticket"]["status"], "RESOLVED")
        self.assertIn("TacticalRMM", res["user_response"])
        self.assertIsNotNone(res["verification"])
        self.assertTrue(res["verification"]["verified"])

    def test_tacticalrmm_patch_management_flow(self):
        res = self.orch.process_request(
            query_text="apply critical security vulnerability patch for CVE-2026-PATCH-KIT on DEV-WIN-102",
            requester_email="alex.murphy@enterprise.com",
            approval_decision=ApprovalStatus.APPROVED
        )
        self.assertEqual(res["ticket"]["status"], "RESOLVED")
        self.assertIn("applied and verified", res["user_response"])

    def test_tacticalrmm_disk_cleanup(self):
        res = self.orch.process_request(
            query_text="my laptop has low storage and disk space full",
            requester_email="alex.murphy@enterprise.com",
            approval_decision=ApprovalStatus.APPROVED
        )
        self.assertEqual(res["ticket"]["status"], "RESOLVED")
        self.assertIn("freed", res["user_response"].lower())

    def test_bitlocker_key_retrieval_unaffected_by_migration(self):
        res = self.orch.process_request(
            query_text="I need my BitLocker recovery key for DEV-WIN-101",
            requester_email="sarah.connor@enterprise.com",
            approval_decision=ApprovalStatus.APPROVED
        )
        self.assertEqual(res["ticket"]["status"], "RESOLVED")
        self.assertIn("BitLocker recovery key", res["user_response"])

if __name__ == "__main__":
    unittest.main()
