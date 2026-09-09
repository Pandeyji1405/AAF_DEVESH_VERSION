from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class IntentCategory(str, Enum):
    ACCESS = "ACCESS"
    DEVICE = "DEVICE"
    HARDWARE = "HARDWARE"
    ONBOARDING = "ONBOARDING"
    SECOPS = "SECOPS"
    RMM_COPILOT = "RMM_COPILOT"
    INFRA_OPS = "INFRA_OPS"
    UNKNOWN = "UNKNOWN"

class RiskTier(str, Enum):
    R0 = "R0"  # Read-Only Diagnostic
    R1 = "R1"  # Low-risk / Reversible write
    R2 = "R2"  # Standard user impacting write (Manager approval)
    R3 = "R3"  # High privilege write (CAB / Security / Lead DBA approval)
    R4 = "R4"  # Prohibited autonomous action

class ApprovalStatus(str, Enum):
    APPROVED = "APPROVED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"
    NOT_REQUIRED = "NOT_REQUIRED"

class ApprovalDecisionChannel(str, Enum):
    EMAIL_BUTTON = "email_button"
    EMAIL_REPLY = "email_reply"
    TEAMS_CARD = "teams_card"
    PORTAL = "portal"
    CLI = "cli"

class TicketStatus(str, Enum):
    OPEN = "OPEN"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED_PENDING_INFO = "APPROVED_PENDING_INFO"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    CLOSED_REJECTED = "CLOSED_REJECTED"
    FAILED = "FAILED"

class WorkflowExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    REJECTED = "REJECTED"
    TIMEOUT = "TIMEOUT"

class VerificationStatus(str, Enum):
    MATCH = "MATCH"
    NO_MATCH = "NO_MATCH"
    INCONCLUSIVE = "INCONCLUSIVE"

class UserQuery(BaseModel):
    query_text: str
    requester_email: str
    origin_channel: str = "Chat"
    ticket_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)

class ProposedAction(BaseModel):
    action_id: str
    workflow_name: str
    risk_tier: RiskTier
    target_entity: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    reason: str
    approval_required: bool = False
    approval_id: Optional[str] = None

class ApprovalRecord(BaseModel):
    approval_id: str
    ticket_id: str
    approver_email: str
    action_name: str
    parameters: Dict[str, Any]
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = Field(default_factory=utc_now)
    decided_at: Optional[datetime] = None
    comments: Optional[str] = None
    risk_tier: Optional[str] = "R2"
    target_resource: Optional[str] = None
    business_justification: Optional[str] = None
    requester_email: Optional[str] = None
    email_message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    reference_token: Optional[str] = None
    decision_channel: Optional[ApprovalDecisionChannel] = None
    manager_notes: Optional[str] = None
    requested_additional_info: List[str] = Field(default_factory=list)
    rejection_reason: Optional[str] = None
    token_consumed: bool = False

class AEExecutionResponse(BaseModel):
    workflow_name: str
    automation_request_id: str
    status: str
    message: Optional[str] = None
    output_parameters: Dict[str, Any] = Field(default_factory=dict)
    raw_logs: Optional[str] = None

class VerificationResult(BaseModel):
    verified: bool
    status: VerificationStatus
    target_entity: str
    actual_state: Dict[str, Any]
    expected_state: Dict[str, Any]
    discrepancy_notes: Optional[str] = None

class IncidentTicket(BaseModel):
    ticket_id: str
    requester_email: str
    intent: IntentCategory
    assigned_agent: str
    short_description: str
    status: str = "OPEN"
    created_at: datetime = Field(default_factory=utc_now)
    resolved_at: Optional[datetime] = None
    work_notes: List[str] = Field(default_factory=list)
    actions_executed: List[ProposedAction] = Field(default_factory=list)
    verification: Optional[VerificationResult] = None
    final_resolution: Optional[str] = None
    resolution_code: Optional[str] = None
    sys_id: Optional[str] = None
    customer_summary: Optional[str] = None
