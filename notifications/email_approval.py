import os
import hmac
import hashlib
import time
import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

from core.models import ApprovalRecord

SECRET_KEY = os.environ.get("APPROVAL_SECRET_KEY", "maf-enterprise-approval-secret-key-2026")

def get_local_ip() -> str:
    """Finds the machine's local network IP so phone on same Wi-Fi can connect to webhook."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def generate_signed_url(approval_id: str, decision: str, ttl_hours: int = 72, base_url: Optional[str] = None) -> str:
    """Generates a tamper-proof HMAC SHA-256 signed URL for one-click approval/rejection."""
    expiry = int(time.time()) + (ttl_hours * 3600)
    payload = f"{approval_id}:{decision}:{expiry}"
    sig = hmac.new(SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    
    url_base = base_url or os.environ.get("PUBLIC_BASE_URL")
    if not url_base or url_base in ["http://localhost:8000", "http://127.0.0.1:8000"]:
        local_ip = get_local_ip()
        url_base = f"http://{local_ip}:8000"
    url_base = url_base.rstrip("/")
    return f"{url_base}/approval/decision?approval_id={approval_id}&decision={decision}&expiry={expiry}&sig={sig}"

def verify_signature(approval_id: str, decision: str, expiry: int, sig: str) -> bool:
    """Verifies that the HMAC signature is authentic and has not expired."""
    if int(time.time()) > int(expiry):
        raise ValueError("This approval link has expired (72h limit exceeded).")
    payload = f"{approval_id}:{decision}:{expiry}"
    expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_sig, sig):
        raise PermissionError("Invalid cryptographic signature on approval request.")
    return True

def build_approval_email(approval_record: ApprovalRecord, target_email: Optional[str] = None) -> Dict[str, Any]:
    """Builds the rich HTML and text email payload for the designated line manager / approver."""
    accept_url = generate_signed_url(approval_record.approval_id, "approve")
    reject_url = generate_signed_url(approval_record.approval_id, "reject")
    local_accept_url = f"http://localhost:8000/approval/decision?approval_id={approval_record.approval_id}&decision=approve&expiry={int(time.time()) + 259200}&sig={hmac.new(SECRET_KEY.encode('utf-8'), f'{approval_record.approval_id}:approve:{int(time.time()) + 259200}'.encode('utf-8'), hashlib.sha256).hexdigest()}"
    local_reject_url = f"http://localhost:8000/approval/decision?approval_id={approval_record.approval_id}&decision=reject&expiry={int(time.time()) + 259200}&sig={hmac.new(SECRET_KEY.encode('utf-8'), f'{approval_record.approval_id}:reject:{int(time.time()) + 259200}'.encode('utf-8'), hashlib.sha256).hexdigest()}"

    ref_token = approval_record.reference_token or approval_record.approval_id
    recipient = target_email or os.environ.get("APPROVER_EMAIL_OVERRIDE") or approval_record.approver_email
    
    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Action Required: IT Approval Request</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1e293b; background: #f8fafc; padding: 24px; }}
    .card {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px; max-width: 620px; margin: 0 auto; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
    .header {{ border-bottom: 2px solid #3b82f6; padding-bottom: 12px; margin-bottom: 18px; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 4px; font-weight: 600; font-size: 12px; background: #e0f2fe; color: #0369a1; text-transform: uppercase; }}
    .btn {{ display: inline-block; padding: 12px 26px; border-radius: 6px; font-weight: 600; text-decoration: none; text-align: center; margin-right: 12px; font-size: 14px; }}
    .btn-approve {{ background: #16a34a; color: #ffffff !important; }}
    .btn-reject {{ background: #dc2626; color: #ffffff !important; }}
    .meta-table {{ width: 100%; border-collapse: collapse; margin: 18px 0; }}
    .meta-table td {{ padding: 9px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
    .meta-table td.label {{ font-weight: 600; color: #64748b; width: 32%; }}
    .instructions {{ background: #f8fafc; border-left: 4px solid #3b82f6; padding: 12px 16px; margin-top: 20px; font-size: 13px; color: #334155; }}
    .footer {{ font-size: 11px; color: #94a3b8; margin-top: 24px; border-top: 1px solid #e2e8f0; padding-top: 12px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <span class="badge">Tier {approval_record.risk_tier} Governance Authorization</span>
      <h2 style="margin: 8px 0 0 0; color: #0f172a;">IT Action Approval Required</h2>
    </div>
    
    <p>Hello,</p>
    <p>An automated remediation or enterprise access action requires your line manager authorization under <strong>Ticket {approval_record.ticket_id}</strong>.</p>
    
    <table class="meta-table">
      <tr><td class="label">Requester:</td><td>{approval_record.requester_email}</td></tr>
      <tr><td class="label">Action:</td><td><code>{approval_record.action_name}</code></td></tr>
      <tr><td class="label">Target Resource:</td><td><strong>{approval_record.target_resource}</strong></td></tr>
      <tr><td class="label">Business Reason:</td><td>{approval_record.business_justification}</td></tr>
      <tr><td class="label">Approval ID:</td><td><code>{approval_record.approval_id}</code></td></tr>
    </table>
    
    <div style="margin: 28px 0;">
      <a href="{accept_url}" class="btn btn-approve" target="_blank">✅ Approve Action</a>
      <a href="{reject_url}" class="btn btn-reject" target="_blank">❌ Reject Request</a>
    </div>
    
    <div class="instructions">
      <strong>💬 Or reply directly to this email:</strong><br>
      You can reply in free text (e.g. <em>"Approved, please proceed"</em> or <em>"Approved and submit laptop to it team"</em> or <em>"Rejected: out of budget"</em>).
      Our Autonomous Agent reads your reply in real-time and updates ServiceNow.
    </div>
    
    <div class="footer">
      Audit Ref: {approval_record.approval_id} | Security Hash Protected
      <span style="display:none !important; color:transparent; font-size:1px;">[[REF:{ref_token}]]</span>
    </div>
  </div>
</body>
</html>"""

    return {
        "subject": f"Action Required: Approval for {approval_record.action_name} (Ticket {approval_record.ticket_id})",
        "html_body": html_body,
        "recipient": recipient,
        "reference_token": ref_token,
        "approval_id": approval_record.approval_id,
        "accept_url": accept_url,
        "reject_url": reject_url,
        "local_accept_url": local_accept_url,
        "local_reject_url": local_reject_url
    }

def send_approval_email(ae_client: Any, approval_record: ApprovalRecord, target_email: Optional[str] = None) -> Dict[str, Any]:
    """
    Dispatches the approval email via SMTP directly to Gmail, and saves local HTML preview.
    """
    email_payload = build_approval_email(approval_record, target_email)
    recipient = email_payload["recipient"]

    # Save local preview file for instant browser testing
    preview_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "latest_approval_email.html"))
    try:
        os.makedirs(os.path.dirname(preview_path), exist_ok=True)
        with open(preview_path, "w", encoding="utf-8") as f:
            f.write(email_payload["html_body"])
    except Exception:
        pass

    # Direct SMTP dispatch if SMTP settings exist in .env
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASSWORD")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))

    if smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = email_payload["subject"]
            msg["From"] = os.environ.get("SMTP_FROM", smtp_user)
            msg["To"] = recipient
            msg.attach(MIMEText(email_payload["html_body"], "html"))

            if smtp_port == 465 or "gmail" in smtp_host.lower():
                with smtplib.SMTP_SSL(smtp_host, 465, timeout=10) as server:
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)

            return {
                "send_status": "SENT",
                "method": "GMAIL_SMTP_SSL_465",
                "recipient": recipient,
                "preview_path": preview_path,
                "accept_url": email_payload["accept_url"],
                "reject_url": email_payload["reject_url"]
            }
        except Exception as e:
            print(f"⚠️ SMTP Send Warning: {e}. Falling back to AutomationEdge notification workflow.")

    # Fallback to Workflow dispatch
    wf_res = ae_client.execute_workflow("AE_NOTIFY_001_SendApprovalEmail", email_payload)
    return {
        "send_status": "SENT",
        "method": "AUTOMATIONEDGE_WORKFLOW",
        "recipient": recipient,
        "preview_path": preview_path,
        "accept_url": email_payload["accept_url"],
        "reject_url": email_payload["reject_url"],
        "response": wf_res
    }
