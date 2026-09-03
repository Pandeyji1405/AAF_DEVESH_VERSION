"""
Microsoft Agent Framework (MAF) Implementation
Powered strictly by Microsoft's official `agent-framework` and `agent-framework-gemini` packages.
"""

from maf_agents.client_factory import get_maf_chat_client
from maf_agents.agents.case_manager import MAFCaseManagerAgent
from maf_agents.agents.device_specialist import MAFDeviceOpsAgent
from maf_agents.agents.access_specialist import MAFAccessGovAgent
from maf_agents.agents.hardware_specialist import MAFHardwareAgent
from maf_agents.agents.onboarding_specialist import MAFOnboardingAgent
from maf_agents.agents.secops_specialist import MAFSecOpsAgent
from maf_agents.agents.rmm_copilot_agent import MAFRMMCopilotAgent
from maf_agents.agents.infra_ops_specialist import MAFInfraOpsAgent

__all__ = [
    "get_maf_chat_client",
    "MAFCaseManagerAgent",
    "MAFDeviceOpsAgent",
    "MAFAccessGovAgent",
    "MAFHardwareAgent",
    "MAFOnboardingAgent",
    "MAFSecOpsAgent",
    "MAFRMMCopilotAgent",
    "MAFInfraOpsAgent"
]
