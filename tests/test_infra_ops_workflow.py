import unittest
from core.models import ApprovalStatus
from orchestrator import AutonomousITOrchestrator

class TestInfraOpsWorkflows(unittest.TestCase):
    def setUp(self):
        self.orch = AutonomousITOrchestrator(use_mock_ae=True)

    def test_iis_app_pool_503_recovery(self):
        res = self.orch.process_request(
            query_text="Production web server SRV-WEB-PROD-01 is throwing HTTP 503 errors and w3wp app pool crashed",
            requester_email="infra.admin@enterprise.com",
            approval_decision=ApprovalStatus.APPROVED
        )
        self.assertEqual(res["ticket"]["status"], "RESOLVED")
        self.assertIn("EnterpriseAppPool", res["user_response"])
        self.assertTrue(res["verification"]["verified"])

    def test_sql_log_truncation_requires_lead_dba_approval(self):
        # When approval_decision is None, must stay PENDING_APPROVAL
        res_pending = self.orch.process_request(
            query_text="Emergency: Database disk is 98% full on SRV-SQL-PROD-02, need transaction log truncation",
            requester_email="developer@enterprise.com",
            approval_decision=None
        )
        self.assertEqual(res_pending["ticket"]["status"], "PENDING_APPROVAL")
        self.assertIn("lead.dba@enterprise.com", res_pending["user_response"])

        # When approved by Lead-DBA, executes and verifies Drive C: 42% Free
        res_approved = self.orch.process_request(
            query_text="Emergency: Database disk is 98% full on SRV-SQL-PROD-02, need transaction log truncation",
            requester_email="developer@enterprise.com",
            approval_decision=ApprovalStatus.APPROVED
        )
        self.assertEqual(res_approved["ticket"]["status"], "RESOLVED")
        self.assertIn("Drive C: 42% Free", res_approved["user_response"])
        self.assertTrue(res_approved["verification"]["verified"])

if __name__ == "__main__":
    unittest.main()
