import os
import sqlite3
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from core.models import IncidentTicket, ApprovalRecord, ApprovalStatus, ApprovalDecisionChannel

def get_db_path() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "data", "cases.db")

class CaseStore:
    """
    SQLite-backed persistent case store.
    Enables asynchronous pause when an approval is requested and robust resumption
    upon webhook confirmation or email reply, persisting state across process restarts.
    """
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_db_path()
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    case_id TEXT PRIMARY KEY,
                    ticket_id TEXT NOT NULL,
                    approval_id TEXT UNIQUE,
                    reference_token TEXT,
                    specialist_name TEXT,
                    workflow_name TEXT,
                    parameters_json TEXT,
                    ticket_json TEXT,
                    context_graph_json TEXT,
                    status TEXT,
                    decision TEXT,
                    manager_notes TEXT,
                    channel TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            for col in ["decision", "manager_notes", "channel"]:
                try:
                    cursor.execute(f"ALTER TABLE cases ADD COLUMN {col} TEXT")
                except Exception:
                    pass
            conn.commit()

    def save_case(self, ticket: IncidentTicket, context_graph: Any, approval_id: str,
                  workflow_name: str, parameters: Dict[str, Any], specialist_name: str,
                  reference_token: Optional[str] = None) -> str:
        case_id = f"CASE-{ticket.ticket_id}"
        ticket_data = ticket.model_dump() if hasattr(ticket, "model_dump") else ticket.dict()
        graph_data = context_graph.snapshot() if hasattr(context_graph, "snapshot") else {}
        now = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO cases (
                    case_id, ticket_id, approval_id, reference_token, specialist_name,
                    workflow_name, parameters_json, ticket_json, context_graph_json,
                    status, decision, manager_notes, channel, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case_id, ticket.ticket_id, approval_id, reference_token or "",
                specialist_name, workflow_name, json.dumps(parameters, default=str),
                json.dumps(ticket_data, default=str), json.dumps(graph_data, default=str),
                ticket.status, "PENDING", "", "", now, now
            ))
            conn.commit()
        return case_id

    def record_decision(self, ref_id: str, decision: str, notes: str = "", channel: str = "WEBHOOK"):
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE cases 
                SET status = ?, decision = ?, manager_notes = ?, channel = ?, updated_at = ? 
                WHERE approval_id = ? OR reference_token = ? OR ticket_id = ?
            """, (decision, decision, notes, channel, now, ref_id, ref_id, ref_id))
            conn.commit()

    def get_case_by_approval_id(self, approval_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cases WHERE approval_id = ?", (approval_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d["parameters"] = json.loads(d["parameters_json"])
                d["ticket"] = json.loads(d["ticket_json"])
                d["context_graph"] = json.loads(d["context_graph_json"])
                return d
        return None

    def get_case_by_ticket_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cases WHERE ticket_id = ?", (ticket_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d["parameters"] = json.loads(d["parameters_json"])
                d["ticket"] = json.loads(d["ticket_json"])
                d["context_graph"] = json.loads(d["context_graph_json"])
                return d
        return None

    def get_case_by_reference_token(self, ref_token: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cases WHERE reference_token = ?", (ref_token,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d["parameters"] = json.loads(d["parameters_json"])
                d["ticket"] = json.loads(d["ticket_json"])
                d["context_graph"] = json.loads(d["context_graph_json"])
                return d
        return None

    def update_case_status(self, case_id: str, status: str, ticket_data: Optional[Dict[str, Any]] = None):
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if ticket_data:
                cursor.execute("""
                    UPDATE cases SET status = ?, ticket_json = ?, updated_at = ? WHERE case_id = ?
                """, (status, json.dumps(ticket_data, default=str), now, case_id))
            else:
                cursor.execute("""
                    UPDATE cases SET status = ?, updated_at = ? WHERE case_id = ?
                """, (status, now, case_id))
            conn.commit()

    def list_all_cases(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT case_id, ticket_id, approval_id, status, decision, manager_notes, created_at FROM cases ORDER BY created_at DESC")
            return [dict(r) for r in cursor.fetchall()]
