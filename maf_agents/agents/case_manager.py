import asyncio
import json
import re
from typing import Tuple, Dict, Any
from agent_framework import Agent, Message, Role
from core.models import UserQuery, IncidentTicket, IntentCategory
from core.context_graph import ContextGraph
from core.nlu import NaturalLanguageUnderstander

from maf_agents.tools.access_tools import create_access_tools
from maf_agents.tools.tacticalrmm_tools import create_tacticalrmm_tools
from maf_agents.tools.itsm_tools import create_itsm_tools, get_active_itsm_connector_name
from maf_agents.client_factory import get_maf_chat_client

class MAFCaseManagerAgent:
    """
    Microsoft Agent Framework (MAF): Case Manager & Triage Agent.
    Coordinates incident intake, entity resolution, and ServiceNow incident creation
    using agent_framework.Agent and Google Gemini API.
    """

    def __init__(self, ae_client, policy_engine, hitl_manager):
        self.ae_client = ae_client
        self.policy_engine = policy_engine
        self.hitl_manager = hitl_manager
        
        self.chat_client = get_maf_chat_client()
        self.access_tools = {t.name: t for t in create_access_tools(ae_client)}
        self.device_tools = {t.name: t for t in create_tacticalrmm_tools(ae_client)}
        self.snow_tools = {t.name: t for t in create_itsm_tools(ae_client)}
        self.itsm_tools = self.snow_tools

        self.maf_agent = Agent(
            client=self.chat_client,
            name="MAF_Case_Manager",
            description="Microsoft Agent Framework Triage Agent for IT Service Desk intake and entity resolution"
        )
        self.underlying_manager = NaturalLanguageUnderstander()
        self.nlu = self.underlying_manager

    def detect_intent(self, query_text: str) -> IntentCategory:
        return self.underlying_manager.detect_intent(query_text)

    def generate_empathy_response(self, query_text: str) -> Dict[str, str]:
        return self.nlu.generate_empathy_response(query_text)

    def analyze_query_details(self, query_text: str) -> Dict[str, Any]:
        """Uses Microsoft Agent Framework with Gemini or fallback to analyze user request."""
        try:
            prompt = (
                f"Analyze this enterprise IT request:\n\"{query_text}\"\n\n"
                "Return ONLY valid JSON with keys:\n"
                "- intent: DEVICE, ACCESS, HARDWARE, ONBOARDING, SECOPS, RMM_COPILOT, or INFRA_OPS\n"
                "- domain_name: Full category name\n"
                "- detected_issue: Short summary of detected issue\n"
                "- proposed_solution: Plain-English remediation plan\n"
            )
            resp = asyncio.run(self.chat_client.get_response(messages=[Message(role=Role.USER, content=prompt)]))
            content = resp.text or ""
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                intent_raw = str(data.get("intent", "")).upper()
                intent_map = {
                    "ACCESS": IntentCategory.ACCESS,
                    "DEVICE": IntentCategory.DEVICE,
                    "HARDWARE": IntentCategory.HARDWARE,
                    "ONBOARDING": IntentCategory.ONBOARDING,
                    "SECOPS": IntentCategory.SECOPS,
                    "RMM_COPILOT": IntentCategory.RMM_COPILOT,
                    "INFRA_OPS": IntentCategory.INFRA_OPS
                }
                intent = intent_map.get(intent_raw, self.underlying_manager.detect_intent(query_text))
                return {
                    "intent": intent,
                    "domain_name": data.get("domain_name", "Enterprise IT Support"),
                    "detected_issue": data.get("detected_issue", query_text),
                    "proposed_solution": data.get("proposed_solution", "Diagnose and resolve via Microsoft Agent Framework")
                }
        except Exception:
            pass

        return self.underlying_manager.analyze_query_details(query_text)

    def process_incoming_query(self, user_query: UserQuery) -> Tuple[IncidentTicket, ContextGraph]:
        intent = self.detect_intent(user_query.query_text)

        # 1. Initialize Context Graph
        ticket_id = user_query.ticket_id or "INC-PENDING"
        context_graph = ContextGraph(ticket_id=ticket_id, requester_email=user_query.requester_email)
        context_graph.add_fact("requester_email", user_query.requester_email, source="USER_QUERY")
        context_graph.add_fact("query_text", user_query.query_text, source="USER_QUERY")
        context_graph.add_fact("intent", intent.value, source="MAF_CASE_MANAGER")

        # 2. Resolve User Profile via MAF tool
        user_data = self.access_tools["resolve_user"](user_email=user_query.requester_email)
        context_graph.add_entity("users", user_data.get("user_id", "unknown_user"), user_data)
        context_graph.add_fact("user_id", user_data.get("user_id"))
        context_graph.add_fact("department", user_data.get("department"))
        context_graph.add_fact("manager_email", user_data.get("manager_email"))

        # 3. Check Assigned Device via TacticalRMM
        assigned_device_id = user_data.get("assigned_device_id")
        if assigned_device_id:
            context_graph.add_fact("assigned_device_id", assigned_device_id, source="MICROSOFT_ENTRA_ID")
            # Map assigned device to TacticalRMM agent_id
            if "APOORVA" in assigned_device_id.upper() or "apoorva" in str(user_query.requester_email).lower():
                agent_id = "zAltxZhbdHrygGpGRhnwqGSbOLSHozfDAZOTntXu"
                hostname = "Apoorva"
            elif "101" in assigned_device_id:
                agent_id = "agent-trmm-001"
                hostname = "LAPTOP-SCONNOR-W11"
            elif "102" in assigned_device_id:
                agent_id = "agent-trmm-002"
                hostname = "LAPTOP-AMURPHY-W11"
            else:
                agent_id = "agent-trmm-004"
                hostname = "LAPTOP-DCHEN-W11"

            context_graph.add_fact("agent_id", agent_id, source="TACTICAL_RMM")
            context_graph.add_fact("device_name", hostname)
            context_graph.add_fact("hostname", hostname)
            try:
                metrics = self.device_tools["get_endpoint_metrics"](agent_id=agent_id)
                context_graph.add_entity("devices", assigned_device_id, metrics)
            except Exception:
                pass

        # 4. Register or create Official ITSM Incident Ticket via MAF tool
        conn_name = get_active_itsm_connector_name()
        if getattr(user_query, "ticket_id", None):
            ticket_number = user_query.ticket_id
            tkt_data = {"ticket_id": ticket_number, "number": ticket_number}
        else:
            tkt_data = self.snow_tools["create_incident"](
                requester_email=user_query.requester_email,
                short_description=user_query.query_text[:80],
                description=user_query.query_text,
                category=intent.value,
                urgency="Medium"
            )
            ticket_number = tkt_data.get("ticket_id") or tkt_data.get("number") or tkt_data.get("ticket_number") or f"INC-{user_query.timestamp.strftime('%Y%m%d%H%M')}"
        
        context_graph.ticket_id = ticket_number
        context_graph.add_fact("ticket_id", ticket_number, source=f"{conn_name}_MAF")
        if tkt_data.get("sys_id"):
            context_graph.add_fact("itsm_sys_id", tkt_data.get("sys_id"), source=f"{conn_name}_API")
            context_graph.add_fact("servicenow_sys_id", tkt_data.get("sys_id"), source=f"{conn_name}_API")
        context_graph.add_fact("itsm_payload", tkt_data, source=f"{conn_name}_API")

        assigned_agent = f"MAF_{intent.value.title()}_Specialist_Agent"
        ticket = IncidentTicket(
            ticket_id=ticket_number,
            sys_id=tkt_data.get("sys_id"),
            requester_email=user_query.requester_email,
            intent=intent,
            assigned_agent=assigned_agent,
            short_description=user_query.query_text[:80],
            status="OPEN"
        )
        ticket.work_notes.append(f"Microsoft Agent Framework Case Manager triaged query into {ticket_number} under route {assigned_agent}.")
        return ticket, context_graph
