import json
from typing import Dict, Any, List, Optional

class ZeroHallucinationViolation(Exception):
    """Raised when an agent proposes execution with uncorroborated entity parameters."""
    pass

class ContextGraph:
    def __init__(self, ticket_id: str, requester_email: str):
        self.ticket_id = ticket_id
        self.requester_email = requester_email
        self.facts: Dict[str, Any] = {}
        self.evidence_logs: List[str] = []
        self.entities: Dict[str, Dict[str, Any]] = {
            "users": {},
            "devices": {},
            "hardware_assets": {},
            "entitlements": {}
        }
        self.history: List[Dict[str, Any]] = []

    def add_fact(self, key: str, value: Any, source: str = "TELEMETRY"):
        """Records an immutable ground-truth fact into the graph."""
        self.facts[key] = {
            "value": value,
            "source": source
        }
        self.evidence_logs.append(f"[{source}] Fact added: {key} = {value}")

    def add_entity(self, entity_type: str, entity_id: str, data: Dict[str, Any]):
        """Associates a discovered and verified entity object into the graph."""
        if entity_type not in self.entities:
            self.entities[entity_type] = {}
        self.entities[entity_type][entity_id] = data
        self.evidence_logs.append(f"[DISCOVERY] Added {entity_type}: {entity_id}")

    def get_fact(self, key: str) -> Optional[Any]:
        fact = self.facts.get(key)
        return fact["value"] if fact else None

    def query_assigned_device(self, user_email: str) -> Optional[Dict[str, Any]]:
        """Answers: 'Which device is assigned to this user?'"""
        for dev_id, dev_data in self.entities.get("devices", {}).items():
            if dev_data.get("primary_user_upn") == user_email:
                return dev_data
        return None

    def validate_action_parameters(self, workflow_name: str, parameters: Dict[str, Any]) -> bool:
        """
        Zero-Hallucination Guardrail:
        Verifies that any target parameter physically exists in the graph's verified entities or facts.
        """
        # Verified evidence excludes raw user query text
        verified_facts = {
            k: v for k, v in self.facts.items()
            if k != "query_text" and not (isinstance(v, dict) and v.get("source") == "USER_QUERY")
        }
        all_graph_text = json.dumps({
            "facts": verified_facts,
            "entities": self.entities
        }).lower()

        # Critical entity fields that MUST be corroborated before write
        critical_keys = [
            "user_id", "device_id", "agent_id", "group_id", 
            "sku_id", "serial_number", "ci_id", "entitlement_id", "host_id"
        ]

        for key, val in parameters.items():
            if key in critical_keys and val:
                val_str = str(val).lower()
                if val_str not in all_graph_text:
                    raise ZeroHallucinationViolation(
                        f"Zero-Hallucination Violation in {workflow_name}: "
                        f"Parameter '{key}' with value '{val}' does NOT exist in verified Context Graph evidence! "
                        f"Run a read-only diagnostic lookup first."
                    )
        return True

    def snapshot(self) -> Dict[str, Any]:
        """Returns a serializable snapshot of the current Context Graph state."""
        return {
            "ticket_id": self.ticket_id,
            "requester_email": self.requester_email,
            "facts": self.facts,
            "entities": self.entities,
            "evidence_count": len(self.evidence_logs)
        }
