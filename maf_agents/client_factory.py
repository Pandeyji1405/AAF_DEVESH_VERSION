import os
import json
from typing import Sequence, Mapping, Any, Awaitable
from dotenv import load_dotenv

from agent_framework import BaseChatClient, ChatResponse, Message, Role, ResponseStream, ChatResponseUpdate
from agent_framework._tools import FunctionInvocationLayer

load_dotenv()

class OfflineLocalChatClient(FunctionInvocationLayer, BaseChatClient):
    """
    Offline local deterministic chat client implementing Microsoft Agent Framework BaseChatClient.
    Enables zero-latency, zero-cost execution when GEMINI_API_KEY is not configured.
    """


    async def _inner_get_response(
        self,
        *,
        messages: Sequence[Message],
        stream: bool,
        options: Mapping[str, Any],
        **kwargs: Any,
    ) -> Awaitable[ChatResponse]:
        await self._validate_options(options)

        user_content = ""
        for m in messages:
            if m.role == Role.USER:
                user_content = m.text or str(m.content)

        text_lower = user_content.lower()

        # Classify intent deterministically
        if any(w in text_lower for w in ["bitlocker", "recovery key", "blue screen"]):
            intent = "DEVICE"
            domain = "Microsoft Intune & Endpoint Security"
            issue = "BitLocker Encryption Lockout & Key Retrieval"
            sol = "Retrieve 48-digit recovery key from Intune Key Vault under manager authorization."
        elif any(w in text_lower for w in ["screen", "keyboard", "coffee", "spill", "broken", "damaged", "dock"]):
            intent = "HARDWARE"
            domain = "Enterprise Hardware Lifecycle & CMDB Asset Operations"
            issue = "Physical Hardware Component Fault Requiring Replacement"
            sol = "Verify warranty status in enterprise CMDB and dispatch approved replacement hardware via FedEx Express."
        elif any(w in text_lower for w in ["intune", "compliance", "non-compliant", "teams", "outlook", "reboot", "restart", "wifi", "antivirus"]):
            intent = "DEVICE"
            domain = "Microsoft Intune & Endpoint Operations"
            issue = "Intune Device Non-Compliance Blocking Corporate Apps"
            sol = "Remediate failed security baselines (WIN11_SEC_BASELINE_V2), re-evaluate compliance, and verify access."
        else:
            intent = "ACCESS"
            domain = "Microsoft Entra ID & Enterprise Identity Governance"
            issue = "Corporate Application & Security Group Entitlement"
            sol = "Evaluate Entra ID entitlements, request line manager authorization, and provision membership."

        structured_json = json.dumps({
            "intent": intent,
            "domain_name": domain,
            "detected_issue": issue,
            "proposed_solution": sol
        })

        reply_msg = Message(role=Role.ASSISTANT, content=structured_json)
        return ChatResponse(messages=[reply_msg])


def get_maf_chat_client() -> BaseChatClient:
    """
    Returns the appropriate chat client for Microsoft Agent Framework:
    - GeminiChatClient (from agent_framework_gemini) if GEMINI_API_KEY is available.
    - OfflineLocalChatClient if running offline without an API key.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    gemini_model = os.environ.get("GEMINI_MODEL_ID", "gemini-2.0-flash")

    if gemini_key:
        try:
            from agent_framework_gemini import GeminiChatClient
            return GeminiChatClient(api_key=gemini_key, model=gemini_model)
        except Exception as e:
            print(f"🔴 GEMINI INIT FAILED — running OFFLINE/keyword-only mode: {e}")
            print("🔴 If you intended live Gemini reasoning, fix this before presenting.")

    return OfflineLocalChatClient()
