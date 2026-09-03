import unittest
from core.models import UserQuery, IntentCategory
from core.policy_engine import PolicyDecisionPoint
from core.hitl import HumanInTheLoopManager
from automationedge.client import AutomationEdgeClient
from maf_agents import MAFCaseManagerAgent

class TestCaseManager(unittest.TestCase):
    def setUp(self):
        self.ae_client = AutomationEdgeClient(use_mock=True)
        self.policy_engine = PolicyDecisionPoint()
        self.hitl_manager = HumanInTheLoopManager()
        self.case_manager = MAFCaseManagerAgent(self.ae_client, self.policy_engine, self.hitl_manager)

    def test_intent_detection_access(self):
        intent = self.case_manager.detect_intent("I need access to Salesforce CRM")
        self.assertEqual(intent, IntentCategory.ACCESS)

        intent = self.case_manager.detect_intent("Please add me to GitHub Enterprise group")
        self.assertEqual(intent, IntentCategory.ACCESS)

    def test_intent_detection_device(self):
        intent = self.case_manager.detect_intent("My laptop failed compliance check, blocking my Teams")
        self.assertEqual(intent, IntentCategory.DEVICE)

        intent = self.case_manager.detect_intent("Need BitLocker recovery key for my laptop")
        self.assertEqual(intent, IntentCategory.DEVICE)

    def test_intent_detection_hardware(self):
        intent = self.case_manager.detect_intent("My laptop screen is broken and keyboard is faulty")
        self.assertEqual(intent, IntentCategory.HARDWARE)

        intent = self.case_manager.detect_intent("Need hardware replacement for my damaged docking station")
        self.assertEqual(intent, IntentCategory.HARDWARE)

    def test_intent_detection_new_specialists(self):
        intent_onboard = self.case_manager.detect_intent("Stage new hire developer laptop and send welcome kit")
        self.assertEqual(intent_onboard, IntentCategory.ONBOARDING)

        intent_secops = self.case_manager.detect_intent("High-priority EDR malware alert, isolate endpoint DEV-WIN-102 immediately")
        self.assertEqual(intent_secops, IntentCategory.SECOPS)

        intent_copilot = self.case_manager.detect_intent("Find all endpoints and apply patch kit across fleet")
        self.assertEqual(intent_copilot, IntentCategory.RMM_COPILOT)

        intent_infra = self.case_manager.detect_intent("Production web server SRV-WEB-PROD-01 503 error, restart w3wp app pool")
        self.assertEqual(intent_infra, IntentCategory.INFRA_OPS)

    def test_case_intake_and_ticket_creation(self):
        query = UserQuery(
            query_text="I need access to Salesforce CRM",
            requester_email="sarah.connor@enterprise.com"
        )
        ticket, context_graph = self.case_manager.process_incoming_query(query)
        self.assertTrue(ticket.ticket_id.startswith("INC"))
        self.assertEqual(ticket.intent, IntentCategory.ACCESS)
        self.assertEqual(context_graph.get_fact("user_id"), "USR-1001")
        self.assertEqual(context_graph.get_fact("manager_email"), "john.anderson@enterprise.com")

if __name__ == "__main__":
    unittest.main()
