# Autonomous IT Service Desk — Microsoft Agent Framework (MAF)

[![Microsoft Agent Framework](https://img.shields.io/badge/Framework-Microsoft%20Agent%20Framework%201.16-0078D4?logo=microsoft)](https://github.com/microsoft/agent-framework)
[![Google Gemini API](https://img.shields.io/badge/LLM-Google%20Gemini%202.0-4285F4?logo=google)](https://ai.google.dev/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-11%20Passed-brightgreen)](https://pytest.org)

An enterprise Autonomous IT Service Desk orchestrator built strictly on Microsoft's official production **Microsoft Agent Framework (`agent-framework` v1.16.0)**, **`agent-framework-gemini`**, and **AutomationEdge**.

Enforces **Zero-Hallucination Context Graphs**, **Deterministic Policy Decision Points (PDP)**, and cryptographically signed **Human-in-the-Loop (HITL) ServiceNow Approval Cards** before any write action is dispatched to Microsoft Intune, Microsoft Entra ID, or ServiceNow CMDB.

---

## 📁 Clean Repository Structure

```
c:/MAF_INTUNE_AE_PROJECT/
├── .env.example                 # Environment variable template for GEMINI_API_KEY
├── .gitignore                   # Ignore caches and local credentials
├── README.md                    # Project overview and operational guide
│
├── automationedge/              # AutomationEdge API client & mock gateway
│   ├── __init__.py
│   ├── client.py                # Enterprise AutomationEdge REST client
│   └── mock_engine.py           # Mock engine with 150 enterprise entities
│
├── core/                        # Core governance, models & context graph
│   ├── __init__.py
│   ├── base_agent.py            # Base agent with 4-stage governance pipeline & verification
│   ├── context_graph.py         # Zero-hallucination entity graph
│   ├── hitl.py                  # Human-in-the-loop approval store & adaptive cards
│   ├── models.py                # Pydantic domain models, tickets, and risk tiers
│   ├── nlu.py                   # Natural language understanding & query diagnosis
│   └── policy_engine.py         # Deterministic Policy Decision Point (PDP)
│
├── data/                        # Master enterprise catalogs & datasets
│   ├── entitlements.json        # 10 enterprise SaaS / security group entitlements
│   ├── hardware_cmdb.json       # 10 enterprise hardware assets & warranty states
│   ├── intune_devices.json      # 10 corporate laptop endpoints in Intune
│   ├── policies.json            # PDP risk tiers (R1/R2/R3) and approval constraints
│   ├── realtime_scenarios.json  # 150 real-time IT scenarios dataset
│   └── users.json               # Enterprise user directory with manager hierarchies
│
├── maf_agents/                  # Official Microsoft Agent Framework (agent-framework)
│   ├── __init__.py
│   ├── client_factory.py        # Google Gemini & offline local chat client factory
│   ├── agents/
│   │   ├── case_manager.py      # MAF Case Manager Agent
│   │   ├── device_specialist.py # MAF Device Ops Agent (Intune & Defender)
│   │   ├── access_specialist.py # MAF Access Governance Agent (Entra ID)
│   │   └── hardware_specialist.py# MAF Hardware Lifecycle Agent (CMDB & Logistics)
│   └── tools/
│       ├── device_tools.py      # @tool for Intune compliance & BitLocker
│       ├── access_tools.py      # @tool for Entra ID groups & licenses
│       ├── hardware_tools.py    # @tool for CMDB asset lookups & replacement
│       └── servicenow_tools.py  # @tool for ServiceNow Incident Table API
│
├── tests/                       # Automated unit tests (100% Pass)
│   ├── test_access_workflow.py
│   ├── test_case_manager.py
│   ├── test_device_workflow.py
│   ├── test_guardrails.py
│   └── test_hardware_workflow.py
│
├── demo.py                      # Interactive Conversational IT Service Desk Virtual Agent
├── orchestrator.py              # Master orchestrator binding MAF & AutomationEdge
├── run_realtime_scenarios.py    # Batch scenario runner for real-time IT datasets
└── realtime_resolution_catalog.md # Comprehensive 150-scenario resolution catalog
```

---

## 🚀 Quickstart Guide

### 1. Configure Gemini API Key (Optional for live LLM reasoning)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your key:
```ini
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL_ID=gemini-2.0-flash
```
*(If no API key is provided, the framework operates offline using the deterministic local NLU engine with 0ms latency)*.

### 2. Run the Interactive Chatbot
```bash
python demo.py
```
- Engages employee in natural language.
- Diagnoses the issue and proposes a concrete remediation plan.
- Asks for confirmation to raise a ServiceNow ticket.
- Triages via **Microsoft Agent Framework**.
- Generates a **Human-in-the-Loop (HITL) ServiceNow Approval Card**.
- If manager approves (`a`), dispatches AutomationEdge workflow and runs read-back verification.
- If manager rejects (`r`), closes the ticket with resolution code `REJECTED_BY_APPROVER`.

### 3. Run Real-Time Batch Scenarios
```bash
python run_realtime_scenarios.py --count 5
```

### 4. Run the Test Suite
```bash
python -m pytest -v
```
All 11 unit tests execute in under 1 second.
