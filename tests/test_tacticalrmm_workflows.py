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

    def test_tacticalrmm_ip_config_flow_apoorva(self):
        res = self.orch.process_request(
            query_text="Can you check my IP configuration details for my device?",
            requester_email="apoorva.giri@enterprise.com",
            approval_decision=ApprovalStatus.APPROVED
        )
        self.assertEqual(res["ticket"]["status"], "RESOLVED")
        self.assertIn("IP Configuration", res["user_response"])
        self.assertIn("Apoorva", res["user_response"])

    def test_tacticalrmm_high_cpu_diagnostics_apoorva(self):
        res = self.orch.process_request(
            query_text="Check high CPU usage and top consuming processes on my laptop",
            requester_email="apoorva.giri@enterprise.com",
            approval_decision=ApprovalStatus.APPROVED
        )
        self.assertEqual(res["ticket"]["status"], "RESOLVED")
        self.assertIn("CPU and process diagnostics", res["user_response"])

    def test_tacticalrmm_machine_summary_flow(self):
        res = self.orch.process_request(
            query_text="i want to check my machine summary",
            requester_email="apoorva.giri@enterprise.com",
            approval_decision=ApprovalStatus.APPROVED
        )
        self.assertEqual(res["ticket"]["status"], "RESOLVED")
        self.assertEqual(res["ticket"]["assigned_agent"], "MAF_Device_Specialist_Agent")
        self.assertIn("Get_Machine_Summary", res["user_response"])
        self.assertIn("Apoorva", res["user_response"])

    def test_tacticalrmm_agents_list_flow(self):
        res = self.orch.process_request(
            query_text="get agents list currently running on the server",
            requester_email="apoorva.giri@enterprise.com",
            approval_decision=ApprovalStatus.APPROVED
        )
        self.assertEqual(res["ticket"]["status"], "RESOLVED")
        self.assertIn("Get_Agents_List", res["user_response"])
        self.assertIn("Tactical RMM Connected Agents", res["user_response"])

    def test_tacticalrmm_software_list_flow(self):
        res = self.orch.process_request(
            query_text="get software list installed on my machine",
            requester_email="apoorva.giri@enterprise.com",
            approval_decision=ApprovalStatus.APPROVED
        )
        self.assertEqual(res["ticket"]["status"], "RESOLVED")
        self.assertIn("Get_Software_List", res["user_response"])
        self.assertIn("Installed Software", res["user_response"])

    def test_tacticalrmm_windows_patches_flow(self):
        res = self.orch.process_request(
            query_text="check windows patches and update status on my device",
            requester_email="apoorva.giri@enterprise.com",
            approval_decision=ApprovalStatus.APPROVED
        )
        self.assertEqual(res["ticket"]["status"], "RESOLVED")
        self.assertIn("Get_Windows_Patches", res["user_response"])
        self.assertIn("Windows Updates", res["user_response"])

    def test_tacticalrmm_software_installation_flow(self):
        # Without approval -> PENDING_APPROVAL
        res_pending = self.orch.process_request(
            query_text="install software 7-Zip on my laptop",
            requester_email="apoorva.giri@enterprise.com",
            approval_decision=None
        )
        self.assertEqual(res_pending["ticket"]["status"], "PENDING_APPROVAL")
        self.assertIn("approval", res_pending["user_response"].lower())

        # With approval -> RESOLVED
        res_approved = self.orch.process_request(
            query_text="install software 7-Zip on my laptop",
            requester_email="apoorva.giri@enterprise.com",
            approval_decision=ApprovalStatus.APPROVED
        )
        self.assertEqual(res_approved["ticket"]["status"], "RESOLVED")
        self.assertIn("Software_Installation", res_approved["user_response"])
        self.assertIn("7-Zip", res_approved["user_response"])

if __name__ == "__main__":
    unittest.main()

