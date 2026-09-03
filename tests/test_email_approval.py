import unittest
import time
from core.models import ApprovalRecord, ApprovalStatus
from core.hitl import HumanInTheLoopManager
from core.case_store import CaseStore
from notifications.email_approval import generate_signed_url, verify_signature, build_approval_email
from notifications.email_reply_listener import classify_approval_reply, handle_incoming_reply

class TestEmailApprovalLoop(unittest.TestCase):
    def setUp(self):
        self.hitl = HumanInTheLoopManager()
        self.case_store = CaseStore()

    def test_signed_url_generation_and_verification(self):
        url = generate_signed_url("APPR-TEST1234", "approve", ttl_hours=72)
        self.assertIn("approval_id=APPR-TEST1234", url)
        self.assertIn("decision=approve", url)
        self.assertIn("sig=", url)

        # Parse and verify
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(url).query)
        sig = qs["sig"][0]
        expiry = int(qs["expiry"][0])
        self.assertTrue(verify_signature("APPR-TEST1234", "approve", expiry, sig))

    def test_expired_signature_rejected(self):
        # Expiry in the past
        past_expiry = int(time.time()) - 100
        with self.assertRaises(ValueError):
            verify_signature("APPR-TEST1234", "approve", past_expiry, "fakesig")

    def test_tampered_signature_rejected(self):
        future_expiry = int(time.time()) + 3600
        with self.assertRaises(PermissionError):
            verify_signature("APPR-TEST1234", "approve", future_expiry, "invalid_tampered_signature")

    def test_build_approval_email_contains_hidden_reference_token(self):
        record = self.hitl.create_approval_request(
            ticket_id="INC-9999",
            approver_email="manager@enterprise.com",
            action_name="AE_Execute_TacticalRMM_Patch_Workflow",
            parameters={"agent_id": "agent-001"}
        )
        email = build_approval_email(record)
        self.assertIn("[[REF:", email["html_body"])
        self.assertIn(record.reference_token, email["html_body"])

    def test_email_reply_with_conditions_produces_approved_with_notes(self):
        record = self.hitl.create_approval_request(
            ticket_id="INC-9999",
            approver_email="manager@enterprise.com",
            action_name="AE_Execute_TacticalRMM_Patch_Workflow",
            parameters={"agent_id": "agent-001"}
        )
        
        reply_message = {
            "from": {"emailAddress": {"address": "manager@enterprise.com"}},
            "body": {"content": f"Approved, provided that you attach the change request form. [[REF:{record.reference_token}]]"}
        }

        res = handle_incoming_reply(reply_message, self.hitl, self.case_store)
        self.assertEqual(res["status"], "APPROVED")
        self.assertTrue(len(res["conditions"]) > 0 or len(res["notes"]) > 0)
        
        updated_rec = self.hitl.get_approval(record.approval_id)
        self.assertEqual(updated_rec.status, ApprovalStatus.APPROVED)
        self.assertTrue(updated_rec.token_consumed)

    def test_untrusted_sender_reply_is_rejected(self):
        record = self.hitl.create_approval_request(
            ticket_id="INC-9999",
            approver_email="manager@enterprise.com",
            action_name="AE_Execute_TacticalRMM_Patch_Workflow",
            parameters={"agent_id": "agent-001"}
        )
        
        spoofed_message = {
            "from": {"emailAddress": {"address": "attacker@evil.com"}},
            "body": {"content": f"Approved immediately! [[REF:{record.reference_token}]]"}
        }

        res = handle_incoming_reply(spoofed_message, self.hitl, self.case_store)
        self.assertEqual(res["status"], "UNTRUSTED_SENDER")
        
        # Original record must stay PENDING
        updated_rec = self.hitl.get_approval(record.approval_id)
        self.assertEqual(updated_rec.status, ApprovalStatus.PENDING)

if __name__ == "__main__":
    unittest.main()
