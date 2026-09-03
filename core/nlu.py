import re
from typing import Dict, Any
from core.models import IntentCategory

class NaturalLanguageUnderstander:
    """
    Core Natural Language Understanding (NLU) engine for IT Service Desk requests.
    Routes intents across TacticalRMM Device Ops, Identity Access, Hardware, Onboarding, SecOps, RMM Copilot, and Infra Ops.
    """

    def detect_intent(self, query_text: str) -> IntentCategory:
        analysis = self.analyze_query_details(query_text)
        return analysis["intent"]

    def analyze_query_details(self, query_text: str) -> Dict[str, Any]:
        text = query_text.lower()

        # ── Infra Ops patterns ──
        if any(k in text for k in ["app pool", "iis", "503", "w3wp", "database disk", "transaction log", "truncate", "sql log"]):
            return {
                "intent": IntentCategory.INFRA_OPS,
                "domain_name": "Enterprise Infrastructure & Database Operations",
                "detected_issue": "Server Application Pool Crash / Critical SQL Storage Exhaustion",
                "proposed_solution": "Execute diagnostic dump, recycle IIS App Pool, or perform governed SQL log backup and truncation."
            }

        # ── SecOps patterns ──
        if any(k in text for k in ["malware", "suspicious process", "edr alert", "isolate", "compromised", "ransomware", "threat detected"]):
            return {
                "intent": IntentCategory.SECOPS,
                "domain_name": "Enterprise Security Operations (SecOps)",
                "detected_issue": "High-Severity Security Incident Requiring Immediate Containment",
                "proposed_solution": "Isolate endpoint from enterprise network, capture live memory forensics, and update SIEM incident."
            }

        # ── Onboarding patterns ──
        if any(k in text for k in ["new hire", "onboarding", "provision", "welcome kit", "stage laptop", "new employee"]):
            return {
                "intent": IntentCategory.ONBOARDING,
                "domain_name": "Workforce Identity & Device Provisioning",
                "detected_issue": "New Hire Workstation Provisioning & Welcome Dispatch",
                "proposed_solution": "Deploy standard workstation package bundle, apply local security baseline, and dispatch welcome kit."
            }

        # ── RMM Copilot patterns ──
        if any(k in text for k in ["find all endpoints", "apply patch kit", "fleet query", "batch execute", "fleet script", "fleet", "batch", "all endpoints", "cross-fleet"]):
            return {
                "intent": IntentCategory.RMM_COPILOT,
                "domain_name": "TacticalRMM Fleet Management Copilot",
                "detected_issue": "Cross-Fleet Query and Batch Script Deployment",
                "proposed_solution": "Query target fleet nodes across TacticalRMM and trigger governed batch script deployment."
            }

        # ── Physical Hardware damage & Asset Replacement patterns ──
        physical_damage_words = [
            "cracked", "crack", "broken", "broke", "shattered", "shatter", "damaged", "damage",
            "accident", "acciden", "mishap", "drop", "dropped", "fell", "fall", "hit",
            "separated", "seperated", "hinge", "chassis", "bent", "crushed", "torn", "detached",
            "flicker", "flickering", "lines on screen", "screen is seperated", "screen separated",
            "spill", "spilled", "coffee", "water", "liquid", "tea",
            "keys stuck", "keyboard fault", "trackpad", "touchpad",
            "swelling", "swollen", "hardware replacement", "damaged laptop", "replace laptop", "hardware issue", "hardware",
            "stolen", "theft", "lost laptop", "laptop stolen", "new laptop", "want new laptop", "need new laptop", "replace my laptop",
            "replacement laptop", "lost my laptop", "misplaced laptop"
        ]
        if any(re.search(r"\b" + re.escape(w) + r"\b", text) for w in physical_damage_words):
            if any(k in text for k in ["stolen", "theft", "lost"]):
                detected_issue = "Lost / Stolen Enterprise Asset & Hardware Replacement Request"
            elif any(k in text for k in ["screen", "flicker", "seperated", "separated", "hinge"]):
                detected_issue = "Physical Display / Cracked Screen & Component Separation Defect"
            elif any(k in text for k in ["spill", "coffee", "water", "liquid", "tea"]):
                detected_issue = "Liquid Damage & Non-Functional Hardware Ingress"
            elif any(k in text for k in ["keyboard", "keys", "trackpad"]):
                detected_issue = "Keyboard & Input Peripheral Physical Defect"
            elif "swelling" in text or "battery" in text:
                detected_issue = "Critical Battery Swelling & Power Retention Failure"
            elif "dock" in text:
                detected_issue = "Defective Docking Station & Peripheral Connectivity Fault"
            else:
                detected_issue = "Physical Hardware Component Fault Requiring Replacement"
            return {
                "intent": IntentCategory.HARDWARE,
                "domain_name": "Enterprise Hardware Lifecycle & CMDB Asset Operations",
                "detected_issue": detected_issue,
                "proposed_solution": "Verify warranty status in enterprise CMDB and dispatch approved replacement hardware via FedEx Express."
            }

        # ── Device / TacticalRMM patterns ──
        if any(k in text for k in ["bitlocker", "recovery key", "blue screen", "bsod"]):
            return {
                "intent": IntentCategory.DEVICE,
                "domain_name": "Endpoint Security & Key Recovery",
                "detected_issue": "BitLocker Encryption Lockout & Key Retrieval",
                "proposed_solution": "Retrieve 48-digit BitLocker recovery key from Microsoft Graph Key Vault under manager authorization."
            }

        if any(k in text for k in ["patch", "cve", "vulnerability"]):
            return {
                "intent": IntentCategory.DEVICE,
                "domain_name": "TacticalRMM Endpoint Vulnerability Management",
                "detected_issue": "Unpatched Security Vulnerability / CVE Remediation",
                "proposed_solution": "Fetch approved hotfix package and deploy via TacticalRMM script execution."
            }

        if any(k in text for k in ["disk space", "low storage", "storage full", "clear cache"]):
            return {
                "intent": IntentCategory.DEVICE,
                "domain_name": "TacticalRMM Storage Optimization",
                "detected_issue": "Critical Low Storage on Local Disk",
                "proposed_solution": "Execute diagnostic disk scan and safely purge temporary cache files via TacticalRMM."
            }

        if any(k in text for k in ["vpn", "dns", "wifi", "wlan", "network"]):
            return {
                "intent": IntentCategory.DEVICE,
                "domain_name": "TacticalRMM Network Connectivity Operations",
                "detected_issue": "Endpoint Network Stack / VPN Daemon Connectivity Degradation",
                "proposed_solution": "Flush DNS resolver cache, test gateway ping, and restart VPN daemon via TacticalRMM."
            }

        if any(k in text for k in ["reboot", "restart", "frozen", "hanging", "stuck"]):
            return {
                "intent": IntentCategory.DEVICE,
                "domain_name": "TacticalRMM Endpoint Management",
                "detected_issue": "Unresponsive Endpoint Requiring Remote Restart",
                "proposed_solution": "Dispatch remote restart script execution via TacticalRMM."
            }

        if any(k in text for k in ["compliance", "non-compliant", "compliant", "baseline", "teams", "outlook"]):
            return {
                "intent": IntentCategory.DEVICE,
                "domain_name": "TacticalRMM Endpoint Compliance",
                "detected_issue": "Endpoint Compliance Check Failure Blocking Corporate Apps",
                "proposed_solution": "Run compliance check script and apply targeted TacticalRMM remediation script."
            }

        # ── Access / Entra ID patterns ──
        access_patterns = [
            "access", "permission", "permissions", "group", "license", "role", "admin", "pim",
            "github", "gitlab", "repo", "repository", "salesforce", "jira", "confluence",
            "figma", "aws", "azure", "gcp", "snowflake", "databricks", "slack", "zoom",
            "power bi", "powerbi", "m365", "office", "mfa", "2fa", "authenticator", "reset password",
            "entitlement", "grant me", "add me to", "join", "entitlements", "read access", "write access"
        ]
        if any(w in text for w in access_patterns):
            if "github" in text or "repo" in text:
                detected_issue = "GitHub Enterprise Developer Repository Access"
            elif "figma" in text:
                detected_issue = "Figma Enterprise UI/UX Design Seat"
            elif "jira" in text or "confluence" in text:
                detected_issue = "Atlassian Jira & Confluence Collaboration Access"
            elif any(c in text for c in ["aws", "azure", "gcp", "cloud", "admin"]):
                detected_issue = "Privileged Cloud Environment Access"
            elif "power bi" in text or "powerbi" in text:
                detected_issue = "Power BI Pro Analytics Reporting License"
            elif any(m in text for m in ["mfa", "2fa", "authenticator"]):
                detected_issue = "Multi-Factor Authentication (MFA) Re-registration"
            elif "salesforce" in text:
                detected_issue = "Salesforce CRM Enterprise License Assignment"
            else:
                detected_issue = "Corporate Application & Security Group Entitlement"
            return {
                "intent": IntentCategory.ACCESS,
                "domain_name": "Microsoft Entra ID & Enterprise Identity Governance",
                "detected_issue": detected_issue,
                "proposed_solution": "Evaluate Entra ID entitlements, request line manager authorization, and provision membership."
            }

        if "laptop" in text or "macbook" in text:
            return {
                "intent": IntentCategory.DEVICE,
                "domain_name": "TacticalRMM Endpoint Operations",
                "detected_issue": "Endpoint System Health Diagnostics & Check Audit",
                "proposed_solution": "Execute TacticalRMM telemetry metrics lookup and verify audit check baselines."
            }

        return {
            "intent": IntentCategory.ACCESS,
            "domain_name": "Enterprise Service Desk General Request",
            "detected_issue": "Enterprise Application Access Request",
            "proposed_solution": "Analyze corporate catalog, verify authorization with manager, and apply entitlement."
        }

    def generate_empathy_response(self, query_text: str) -> Dict[str, str]:
        """
        Generates warm, empathetic, human-like acknowledgment tailored to the user's situation.
        """
        text = query_text.lower()
        if any(w in text for w in ["drop", "dropped", "crack", "cracked", "break", "broken", "shatter", "spill", "coffee", "water", "damage"]):
            empathy = "Oh no, I'm really sorry to hear that! Hardware accidents and accidental drops happen all the time, so please don't worry. Let's get your replacement sorted right away."
            action_desc = "verify your warranty status in our CMDB and prepare an expedited replacement device"
        elif any(w in text for w in ["locked out", "lockout", "bitlocker", "recovery key", "blue screen"]):
            empathy = "Oh, that sounds really stressful! Being locked out right in the middle of your workday is so frustrating. Let me help you get your BitLocker recovery key from the secure vault."
            action_desc = "safely retrieve your 48-digit recovery key from the secure vault"
        elif any(w in text for w in ["503", "app pool", "crash", "w3wp", "down", "disk is 98", "full", "emergency"]):
            empathy = "I completely understand the urgency here - production outages and server disruptions are high-priority situations. I'm on it."
            action_desc = "run server diagnostics, capture telemetry, and initiate automated recovery"
        elif any(w in text for w in ["malware", "ransomware", "threat", "isolate", "suspicious"]):
            empathy = "Thank you for alerting us promptly! Potential security anomalies need swift containment. I can protect your environment immediately."
            action_desc = "isolate the endpoint to contain the threat and capture memory forensics"
        elif any(w in text for w in ["compliance", "blocked", "teams", "outlook", "antivirus", "failed"]):
            empathy = "That's definitely inconvenient when compliance checks interrupt your work and block essential tools like Teams."
            action_desc = "run automated TacticalRMM diagnostic scripts and bring your device back into compliance"
        elif any(w in text for w in ["access", "permission", "github", "jira", "license", "figma"]):
            empathy = "Got it! Having the right tools and repository access is essential to keep your project momentum going without blockers."
            action_desc = "verify your role requirements and route an entitlement request to your line manager"
        elif any(w in text for w in ["new hire", "onboarding", "welcome"]):
            empathy = "Exciting to welcome a new team member! Setting up the right workstation and software from day one makes a big difference."
            action_desc = "stage the standard workstation package and prepare the welcome kit"
        else:
            empathy = "I'm sorry you're running into this issue! Let's get this resolved for you quickly and smoothly."
            action_desc = "diagnose the issue and execute the resolution workflow"

        return {
            "empathy_message": empathy,
            "action_description": action_desc
        }
