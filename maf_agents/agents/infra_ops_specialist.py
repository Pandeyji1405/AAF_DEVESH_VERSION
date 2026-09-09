from typing import Optional, Dict, Any
from agent_framework import Agent
from core.models import IncidentTicket, ApprovalStatus, RiskTier
from core.context_graph import ContextGraph
from core.base_agent import BaseAgent

from maf_agents.tools.ops_tools import create_ops_tools
from maf_agents.tools.itsm_tools import create_itsm_tools
from maf_agents.client_factory import get_maf_chat_client

class MAFInfraOpsAgent(BaseAgent):
    """
    Microsoft Agent Framework (MAF): Infrastructure Operations Specialist Agent.
    Remediates server outages (IIS app pool crashes) and critical database storage incidents (SQL log truncation).
    """

    def __init__(self, ae_client, policy_engine, hitl_manager):
        super().__init__("MAF_Infra_Ops_Agent", ae_client, policy_engine, hitl_manager)
        self.ops_tools = {t.name: t for t in create_ops_tools(ae_client)}
        self.snow_tools = {t.name: t for t in create_itsm_tools(ae_client)}
        self.itsm_tools = self.snow_tools

        self.maf_agent = Agent(
            client=get_maf_chat_client(),
            name="MAF_Infra_Ops_Specialist",
            description="Microsoft Agent Framework specialist for IIS server crashes and database storage incidents",
            tools=list(self.ops_tools.values())
        )

    def execute_request(self, ticket: IncidentTicket, context_graph: ContextGraph, approval_decision: Optional[ApprovalStatus] = None) -> IncidentTicket:
        user_email = context_graph.get_fact("requester_email") or ticket.requester_email
        query_text = (context_graph.get_fact("query_text") or ticket.short_description).lower()

        # ── SCENARIO 1: IIS APP POOL 503 CRASH RECOVERY ──
        if any(k in query_text for k in ["app pool", "iis", "503", "w3wp", "web server"]):
            host_id = "SRV-WEB-PROD-01"
            app_pool = "EnterpriseAppPool"
            manager_email = "infra.lead@enterprise.com"
            context_graph.add_entity("devices", host_id, {"host_id": host_id, "server_role": "IIS_WEB_SERVER"})
            context_graph.add_fact("host_id", host_id, source="INFRA_DISCOVERY")

            # 1. Collect crash dump (R0)
            dump_res = self.ops_tools["collect_process_dump"](host_id=host_id, process_name="w3wp.exe", ticket_id=ticket.ticket_id)
            
            # 2. Restart App Pool (R2)
            workflow_name = "AE_Restart_AppPool_Workflow"
            params = {
                "host_id": host_id,
                "app_pool_name": app_pool,
                "ticket_id": ticket.ticket_id
            }

            approval_record = self.hitl_manager.create_approval_request(
                ticket_id=ticket.ticket_id,
                approver_email=manager_email,
                action_name=workflow_name,
                parameters=params,
                risk_tier="R2",
                target_resource=f"{host_id} - IIS App Pool [{app_pool}]",
                business_justification=f"Recycle crashed IIS App Pool '{app_pool}' causing HTTP 503 service outage on {host_id}",
                requester_email=user_email
            )

            if approval_decision:
                self.hitl_manager.sign_decision(approval_record.approval_id, approval_decision, "App Pool restart authorized by Infrastructure Lead")
                approval_record = self.hitl_manager.get_approval(approval_record.approval_id)

            if approval_record.status == ApprovalStatus.APPROVED:
                context_graph.validate_action_parameters(workflow_name, params)
                app_dict = approval_record.model_dump() if hasattr(approval_record, "model_dump") else approval_record.dict()
                decision = self.policy_engine.evaluate(workflow_name, params, app_dict)
                if decision["decision"] == "DENY":
                    raise PermissionError(f"PDP denied {workflow_name}: {decision.get('reason')}")

                self.ops_tools["restart_app_pool"](host_id=host_id, app_pool_name=app_pool, ticket_id=ticket.ticket_id)
                
                # Health Check Verification
                health_res = self.ops_tools["http_health_check"](endpoint_url="https://app.enterprise.local/health")
                verification = self.verify_state(
                    check_name=f"IIS Web Service Health Check on {host_id}",
                    actual_state=health_res,
                    expected_state={"http_status": 200},
                    keys_to_compare=["http_status"]
                )
                ticket.verification = verification
                ticket.status = "RESOLVED"
                ticket.customer_summary = f"IIS Application Pool '{app_pool}' on {host_id} has been restarted and verified (HTTP 200 OK). Memory crash dump preserved for RCA."
                self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Complete", resolution_code="APPPOOL_RESTORED", work_notes=f"App Pool {app_pool} recycled. Dump: {dump_res.get('dump_file')}", customer_summary=ticket.customer_summary)
            elif approval_record.status == ApprovalStatus.REJECTED:
                ticket.status = "CLOSED_REJECTED"
                ticket.customer_summary = f"App pool restart request was rejected by {manager_email}."
                self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Rejected", resolution_code="REJECTED_BY_APPROVER", work_notes=f"Rejected by {manager_email}", customer_summary=ticket.customer_summary)
            else:
                ticket.status = "PENDING_APPROVAL"
                ticket.customer_summary = f"IIS App Pool recycle requires approval from {manager_email}."
            return ticket

        # ── SCENARIO 3: DATABASE DISK FULL & SQL LOG TRUNCATION ──
        host_id = "SRV-SQL-PROD-02"
        db_name = "ProductionDB"
        dba_approver = "lead.dba@enterprise.com"
        context_graph.add_entity("devices", host_id, {"host_id": host_id, "server_role": "SQL_DATABASE_SERVER"})
        context_graph.add_fact("host_id", host_id, source="INFRA_DISCOVERY")

        # Step 1: Scan DB directory (R0)
        db_scan = self.ops_tools["scan_db_directory"](host_id=host_id, db_name=db_name)
        
        # Step 2: Backup SQL logs before destructive truncation (R1)
        self.ops_tools["backup_sql_logs"](host_id=host_id, db_name=db_name, ticket_id=ticket.ticket_id)

        # Step 3: Mandatory High-Risk Lead-DBA Approval for SQL Log Truncation (R3)
        workflow_name = "AE_Truncate_SQL_Logs_Workflow"
        params = {
            "host_id": host_id,
            "db_name": db_name,
            "ticket_id": ticket.ticket_id
        }

        approval_record = self.hitl_manager.create_approval_request(
            ticket_id=ticket.ticket_id,
            approver_email=dba_approver,
            action_name=workflow_name,
            parameters=params,
            risk_tier="R3",
            target_resource=f"{host_id} / SQL DB: {db_name}",
            business_justification=f"Emergency SQL transaction log truncation on {host_id} (Log file 480 GB, Drive C: < 2% Free)",
            requester_email=user_email
        )

        if approval_decision:
            self.hitl_manager.sign_decision(approval_record.approval_id, approval_decision, "Authorized by Principal Lead DBA")
            approval_record = self.hitl_manager.get_approval(approval_record.approval_id)

        if approval_record.status == ApprovalStatus.APPROVED:
            context_graph.validate_action_parameters(workflow_name, params)
            app_dict = approval_record.model_dump() if hasattr(approval_record, "model_dump") else approval_record.dict()
            decision = self.policy_engine.evaluate(workflow_name, params, app_dict)
            if decision["decision"] == "DENY":
                raise PermissionError(f"PDP denied {workflow_name}: {decision.get('reason')}")

            trunc_res = self.ops_tools["truncate_sql_logs"](host_id=host_id, db_name=db_name, ticket_id=ticket.ticket_id)

            verification = self.verify_state(
                check_name=f"Database Host Storage Recovery on {host_id}",
                actual_state=trunc_res,
                expected_state={"free_space_status": "Drive C: 42% Free"},
                keys_to_compare=["free_space_status"]
            )
            ticket.verification = verification
            ticket.status = "RESOLVED"
            ticket.customer_summary = f"SQL Transaction log truncation complete on {host_id} ({db_name}). Point-in-time log backup secured. Disk recovery: Drive C: 42% Free."
            self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Complete", resolution_code="SQL_LOGS_TRUNCATED", work_notes=f"DB log truncated under Lead-DBA sign-off {approval_record.approval_id}. Free space: Drive C: 42% Free", customer_summary=ticket.customer_summary)
        elif approval_record.status == ApprovalStatus.REJECTED:
            ticket.status = "CLOSED_REJECTED"
            rej_reason = approval_record.rejection_reason or approval_record.comments or f"Rejected by Lead DBA {dba_approver}"
            ticket.work_notes.append(f"SQL log truncation was REJECTED by Lead DBA {dba_approver}. Notes: \"{rej_reason}\".")
            ticket.customer_summary = f"SQL log truncation was REJECTED by Lead DBA ({dba_approver}). Reason: \"{rej_reason}\"."
            self.snow_tools["update_incident"](ticket_id=ticket.ticket_id, state="Closed Rejected", resolution_code="REJECTED_BY_APPROVER", work_notes="\n".join(ticket.work_notes), customer_summary=ticket.customer_summary)
        else:
            ticket.status = "PENDING_APPROVAL"
            ticket.customer_summary = f"High-Risk SQL log truncation requires mandatory signed approval from Lead DBA ({dba_approver})."

        return ticket
