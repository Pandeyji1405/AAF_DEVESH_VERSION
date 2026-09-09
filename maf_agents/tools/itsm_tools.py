import os
from typing import Dict, Any, List
from maf_agents.tools.servicenow_tools import create_servicenow_tools

def get_active_itsm_connector_name() -> str:
    """Returns the name of the active ITSM connector (SERVICENOW)."""
    return "SERVICENOW"

def create_itsm_tools(ae_client) -> List[Any]:
    """
    ITSM Connector Tools for Microsoft Agent Framework.
    Provides incident creation and status updates mapped to ServiceNow API & AutomationEdge T4.
    """
    return create_servicenow_tools(ae_client)
