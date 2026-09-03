"""
Backward-compatibility adapter for TacticalRMM device tools.
Delegates to maf_agents.tools.tacticalrmm_tools.create_tacticalrmm_tools.
"""
from maf_agents.tools.tacticalrmm_tools import create_tacticalrmm_tools

def create_device_tools(ae_client):
    """Returns TacticalRMM tools for endpoint device operations."""
    return create_tacticalrmm_tools(ae_client)
