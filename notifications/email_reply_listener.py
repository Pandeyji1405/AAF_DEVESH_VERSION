import re
import os
import json
import logging
import smtplib
import imaplib
import email
import email.utils
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from core.models import ApprovalStatus, ApprovalDecisionChannel

logger = logging.getLogger("EmailReplyListener")

def strip_quoted_reply(text: str) -> str:
    """Removes quoted original thread headers from an email reply."""
    if not text:
        return ""
    cleaned = text.strip()
    patterns = [
        r"(?i)\r?\n\s*On\s+.*?\s+wrote:\s*",
        r"(?i)\r?\n\s*-{3,}\s*Original Message\s*-{3,}",
        r"(?i)\r?\n\s*From:\s+.*",
        r"(?i)\r?\n\s*>.*"
    ]
    for p in patterns:
        parts = re.split(p, cleaned, maxsplit=1)
        if parts:
            cleaned = parts[0]
    return cleaned.strip()

def extract_reference_token(email_body: str) -> Optional[str]:
    """Extracts hidden reference token formatted as [[REF:<token>]] or APPR- or INC- from content or subject."""
    if not email_body:
        return None
    match = re.search(r"\[\[REF:([A-Za-z0-9\-_]+)\]\]", email_body)
    if match:
        return match.group(1)
    match_appr = re.search(r"(APPR-[A-Z0-9]{8})", email_body)
    if match_appr:
        return match_appr.group(1)
    match_inc = re.search(r"(INC-[A-Z0-9]{8,14})", email_body)
    if match_inc:
        return match_inc.group(1)
    return None

def classify_approval_reply(approval_id: str, reply_text: str) -> Dict[str, Any]:
    """
    Classifies natural language email replies with instantaneous fast-path parsing.
    """
    cleaned = strip_quoted_reply(reply_text)
    lower = cleaned.lower()

    if any(w in lower for w in ["approve", "approved", "grant", "go ahead", "authorized", "looks good", "proceed", "yes"]):
        lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
        notes = cleaned
        additional_info = []
        if len(lines) > 1:
            notes = " ".join(lines[1:])
            additional_info.append(notes)
        elif len(cleaned.split()) > 2:
            notes = cleaned
            additional_info.append(cleaned)

        return {
            "decision": "APPROVE",
            "requested_additional_info": additional_info,
            "notes": notes,
            "rejection_reason": None
        }
    elif any(w in lower for w in ["reject", "rejected", "deny", "denied", "do not approve", "halt", "cancel", "no"]):
        lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
        reason = cleaned
        if len(lines) > 1:
            reason = " ".join(lines[1:])
        return {
            "decision": "REJECT",
            "requested_additional_info": [],
            "notes": cleaned,
            "rejection_reason": reason
        }

    return {
        "decision": "UNCLEAR",
        "requested_additional_info": [],
        "notes": cleaned,
        "rejection_reason": None
    }

def handle_incoming_reply(message: Dict[str, Any], hitl_manager: Any, case_store: Any, orchestrator: Any = None) -> Dict[str, Any]:
    """
    Processes an incoming reply from an approver's mailbox.
    Validates sender identity against recorded approver, classifies reply, and updates HITL/Case state.
    """
    content = message.get("body", {}).get("content", "") or message.get("content", "")
    sender_email = message.get("from", {}).get("emailAddress", {}).get("address", "") or message.get("sender", "")

    cleaned = strip_quoted_reply(content)
    ref = extract_reference_token(content) or extract_reference_token(message.get("subject", ""))
    
    # Fallback: if single pending case in store, match to it
    if not ref:
        pending = [c for c in case_store.list_all_cases() if c.get("status") == "PENDING" or c.get("decision") == "PENDING"]
        if pending:
            ref = pending[0]["approval_id"]

    if not ref:
        logger.warning("No valid reference token found in incoming email reply.")
        return {"status": "IGNORED", "reason": "No reference token found"}

    # Look up record in memory or case store
    record = hitl_manager.get_approval(ref)
    case_data = case_store.get_case_by_approval_id(ref) or case_store.get_case_by_reference_token(ref) or case_store.get_case_by_ticket_id(ref)

    # Untrusted sender guard
    if sender_email and record and record.approver_email:
        appr = record.approver_email.lower().strip()
        override = (os.environ.get("APPROVER_EMAIL_OVERRIDE") or "").lower().strip()
        sender = sender_email.lower().strip()
        if not (sender in appr or appr in sender or (override and (sender in override or override in sender))):
            logger.error(f"SECURITY ALERT: Untrusted sender '{sender_email}' tried to action approval for '{appr}'.")
            return {"status": "UNTRUSTED_SENDER", "reason": "Sender email mismatch"}

    # Classify Reply
    classification = classify_approval_reply(ref, cleaned)
    decision = classification["decision"]

    if decision == "UNCLEAR":
        logger.info(f"Reply intent for {ref} was UNCLEAR.")
        return {"status": "CLARIFICATION_NEEDED", "ref": ref}

    if decision == "APPROVE":
        notes_text = classification["notes"]
        if classification["requested_additional_info"]:
            notes_text = f"Approved with Conditions: {', '.join(classification['requested_additional_info'])} | Verbatim: {cleaned}"

        if record:
            hitl_manager.sign_decision(
                record.approval_id,
                ApprovalStatus.APPROVED,
                comments=notes_text,
                channel=ApprovalDecisionChannel.EMAIL_REPLY
            )
            if classification["requested_additional_info"]:
                hitl_manager.set_requested_info(record.approval_id, classification["requested_additional_info"])
            hitl_manager.mark_token_consumed(record.approval_id)
        
        target_appr = record.approval_id if record else (case_data["approval_id"] if case_data else ref)
        case_store.record_decision(target_appr, "APPROVED", notes_text, "EMAIL_REPLY")

        return {
            "status": "APPROVED",
            "ref": target_appr,
            "conditions": classification["requested_additional_info"],
            "notes": notes_text
        }
    else:
        rejection_text = cleaned
        if record:
            hitl_manager.sign_decision(
                record.approval_id,
                ApprovalStatus.REJECTED,
                comments=rejection_text,
                channel=ApprovalDecisionChannel.EMAIL_REPLY,
                rejection_reason=rejection_text
            )
            hitl_manager.mark_token_consumed(record.approval_id)

        target_appr = record.approval_id if record else (case_data["approval_id"] if case_data else ref)
        case_store.record_decision(target_appr, "REJECTED", rejection_text, "EMAIL_REPLY")

        return {
            "status": "REJECTED",
            "ref": target_appr,
            "notes": rejection_text,
            "rejection_reason": rejection_text
        }

def poll_inbox_for_replies(hitl_manager: Any, case_store: Any, active_approval_id: Optional[str] = None,
                           created_after: Optional[datetime] = None, timeout_sec: int = 5) -> Optional[Dict[str, Any]]:
    """
    Connects to Gmail IMAP inbox, checks the latest messages for approval replies, parses the body, and updates case status.
    Ensures that only replies sent AFTER the approval was created are matched to the active request.
    """
    user = os.environ.get("SMTP_USER") or os.environ.get("IMAP_USER")
    pwd = os.environ.get("SMTP_PASSWORD") or os.environ.get("IMAP_PASSWORD")
    host = os.environ.get("IMAP_HOST", "imap.gmail.com")
    port = int(os.environ.get("IMAP_PORT", "993"))

    if not user or not pwd:
        return None

    try:
        mail = imaplib.IMAP4_SSL(host, port, timeout=timeout_sec)
        mail.login(user, pwd)
        mail.select("INBOX")

        status, messages = mail.search(None, "ALL")
        if status != "OK" or not messages[0]:
            mail.logout()
            return None

        all_ids = messages[0].split()
        latest_ids = all_ids[-10:]

        active_case = case_store.get_case_by_approval_id(active_approval_id) if active_approval_id else None
        active_ticket_id = active_case.get("ticket_id") if active_case else None

        for num in reversed(latest_ids):
            status, data = mail.fetch(num, "(RFC822)")
            if status != "OK":
                continue

            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            # 1. Timestamp validation
            msg_date_str = msg.get("Date")
            if msg_date_str and created_after:
                try:
                    msg_date = email.utils.parsedate_to_datetime(msg_date_str)
                    if msg_date < (created_after - timedelta(seconds=20)):
                        continue
                except Exception:
                    pass

            subject = msg.get("Subject", "")
            # Look for reply subjects
            if not ("Re:" in subject or "Action Required" in subject or "INC-" in subject or "Approval" in subject):
                continue

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get("Content-Disposition"))
                    if ctype == "text/plain" and "attachment" not in cdispo:
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")

            cleaned_reply = strip_quoted_reply(body)
            if not cleaned_reply:
                continue

            lower = cleaned_reply.lower()
            if not any(k in lower for k in ["approve", "approved", "reject", "rejected", "deny", "grant"]):
                continue

            ref = extract_reference_token(body) or extract_reference_token(subject)
            
            # If an active approval is requested, enforce strict match on Ticket ID or Approval ID
            if active_approval_id:
                matches_active = False
                if ref and (ref == active_approval_id or (active_ticket_id and ref == active_ticket_id)):
                    matches_active = True
                elif active_ticket_id and (active_ticket_id in subject or active_ticket_id in body):
                    matches_active = True
                elif active_approval_id and (active_approval_id in subject or active_approval_id in body):
                    matches_active = True
                
                if not matches_active:
                    continue
            elif not ref:
                pending = [c for c in case_store.list_all_cases() if c.get("status") == "PENDING" or c.get("decision") == "PENDING"]
                if pending:
                    ref = pending[0]["approval_id"]

            if active_approval_id or ref:
                msg_payload = {
                    "body": {"content": cleaned_reply},
                    "sender": msg.get("From", ""),
                    "subject": subject
                }
                res = handle_incoming_reply(msg_payload, hitl_manager, case_store)
                mail.logout()
                return res

        mail.logout()
    except Exception as e:
        logger.debug(f"IMAP check error: {e}")
    return None

def start_background_inbox_poller(hitl_manager: Any, case_store: Any, active_approval_id: str,
                                   created_after: Optional[datetime] = None, stop_event: Optional[Any] = None) -> Any:
    """
    Runs IMAP inbox checking in a background thread so the main terminal loop never blocks or hangs.
    """
    import threading
    import time
    def _worker():
        while stop_event is None or not stop_event.is_set():
            try:
                res = poll_inbox_for_replies(hitl_manager, case_store, active_approval_id=active_approval_id,
                                             created_after=created_after, timeout_sec=5)
                if res and res.get("status") in ["APPROVED", "REJECTED"]:
                    break
            except Exception:
                pass
            time.sleep(2.0)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t
