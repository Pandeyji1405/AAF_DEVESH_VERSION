import os
from fastapi import FastAPI, Form, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from core.models import ApprovalStatus, ApprovalDecisionChannel
from core.hitl import HumanInTheLoopManager
from core.case_store import CaseStore
from notifications.email_approval import verify_signature

app = FastAPI(title="MAF IT Service Desk - Approval Webhook Gateway")

# Shared instances for runtime execution
hitl_manager = HumanInTheLoopManager()
case_store = CaseStore()

@app.get("/")
def root():
    return HTMLResponse("<h2>MAF IT Service Desk Approval Webhook Gateway is RUNNING.</h2><p>Access <a href='/health'>/health</a></p>")

@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "service": "approval_webhook"}

@app.get("/approval/decision", response_class=HTMLResponse)
def show_confirmation(approval_id: str, decision: str, expiry: int, sig: str):
    """
    Step 1: Confirm-then-Commit GET endpoint.
    Displays a verification prompt to prevent corporate email link scanners from falsely committing actions.
    """
    try:
        verify_signature(approval_id, decision, expiry, sig)
    except Exception as e:
        return HTMLResponse(f"""
            <html><body style="font-family:sans-serif;padding:30px;background:#fef2f2;color:#991b1b;">
                <h2>⚠️ Invalid or Expired Approval Link</h2>
                <p>{str(e)}</p>
            </body></html>
        """, status_code=400)

    # Check case store first
    case_data = case_store.get_case_by_approval_id(approval_id)
    if case_data and case_data.get("decision") in ["APPROVED", "REJECTED"]:
        return HTMLResponse(f"""
            <html><body style="font-family:sans-serif;padding:30px;background:#fffbeb;color:#92400e;">
                <h2>ℹ️ Already Processed</h2>
                <p>This approval request (<code>{approval_id}</code>) has already been recorded as <strong>{case_data['decision']}</strong>.</p>
            </body></html>
        """, status_code=200)

    record = hitl_manager.get_approval(approval_id)
    if record and record.token_consumed:
        return HTMLResponse("""
            <html><body style="font-family:sans-serif;padding:30px;background:#fffbeb;color:#92400e;">
                <h2>ℹ️ Already Processed</h2>
                <p>This approval decision has already been recorded.</p>
            </body></html>
        """, status_code=200)

    action_label = "APPROVE" if decision.lower() == "approve" else "REJECT"
    btn_color = "#16a34a" if action_label == "APPROVE" else "#dc2626"

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Confirm Decision — Approval {approval_id}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; padding: 40px; display: flex; justify-content: center; }}
            .box {{ background: #ffffff; padding: 32px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.08); max-width: 520px; width: 100%; border: 1px solid #e2e8f0; }}
            .btn {{ background: {btn_color}; color: white; border: none; padding: 14px 24px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 16px; width: 100%; margin-top: 18px; }}
            .btn:hover {{ opacity: 0.9; }}
        </style>
    </head>
    <body>
        <div class="box">
            <h2 style="margin-top:0; color:#0f172a;">Confirm Line Manager Authorization</h2>
            <p style="font-size:15px; color:#334155;">Please confirm your decision to <strong>{action_label}</strong> the IT request under Approval Reference: <code>{approval_id}</code>.</p>
            <form method="post" action="/approval/decision">
                <input type="hidden" name="approval_id" value="{approval_id}">
                <input type="hidden" name="decision" value="{decision}">
                <input type="hidden" name="expiry" value="{expiry}">
                <input type="hidden" name="sig" value="{sig}">
                <label style="font-size:13px; color:#475569; font-weight:600; display:block; margin-top:14px;">Optional Manager Comments / Conditions:</label>
                <input type="text" name="notes" placeholder="e.g., Approved via Manager One-Click" style="width:100%; padding:10px; margin-top:6px; border:1px solid #cbd5e1; border-radius:4px; box-sizing:border-box;">
                <button type="submit" class="btn">Yes, Confirm {action_label}</button>
            </form>
        </div>
    </body>
    </html>
    """)

@app.post("/approval/decision", response_class=HTMLResponse)
def commit_decision(approval_id: str = Form(...), decision: str = Form(...),
                    expiry: int = Form(...), sig: str = Form(...), notes: str = Form("")):
    """
    Step 2: Commit POST endpoint.
    Verifies token authenticity, records decision in persistent store and memory, and marks token consumed.
    """
    try:
        verify_signature(approval_id, decision, expiry, sig)
    except Exception as e:
        return HTMLResponse(f"<h3>Verification Error: {str(e)}</h3>", status_code=400)

    sign_status = ApprovalStatus.APPROVED if decision.lower() == "approve" else ApprovalStatus.REJECTED
    comment_text = notes.strip() or f"Confirmed by Line Manager via Email Button ({sign_status.value})"

    # 1. Update in-memory HITL store if present
    record = hitl_manager.get_approval(approval_id)
    if record:
        hitl_manager.sign_decision(approval_id, sign_status, comments=comment_text, channel=ApprovalDecisionChannel.EMAIL_BUTTON)
        hitl_manager.mark_token_consumed(approval_id)

    # 2. Update persistent SQLite Case Store
    case_store.record_decision(approval_id, sign_status.value, comment_text, "EMAIL_BUTTON")

    bg_color = "#f0fdf4" if sign_status == ApprovalStatus.APPROVED else "#fef2f2"
    txt_color = "#166534" if sign_status == ApprovalStatus.APPROVED else "#991b1b"

    return HTMLResponse(f"""
        <html>
        <head><meta charset="utf-8"><title>Decision Recorded</title></head>
        <body style="font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding:40px; display:flex; justify-content:center; background:#f8fafc;">
            <div style="background:{bg_color}; color:{txt_color}; padding:32px; border-radius:8px; border:1px solid #cbd5e1; max-width:550px; width:100%; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
                <h2 style="margin-top:0;">✅ Decision Recorded: {sign_status.value}</h2>
                <p>Your authorization has been cryptographically signed and recorded in the audit trail.</p>
                <p><strong>Manager Notes:</strong> {comment_text}</p>
                <p style="font-size:14px; margin-top:20px; color:#475569;">The Autonomous IT Specialist agent is now executing the approved action. You can close this window.</p>
            </div>
        </body>
        </html>
    """)
