# Agentic ERP Patterns

Enterprise Agentic AI architecture patterns for **Microsoft Dynamics 365**, **Power Platform**, **Azure AI**, **Copilot Studio**, and **Dataverse** — built with the Anthropic Claude SDK.

Inspired by the PTW America AI-Driven D365 Finance Innovation Roadmap — 100+ innovations across 8 financial domains.

---

## Products (8 AI Agent Domains)

| Domain | Agent Class | Key Capabilities |
|--------|-------------|-----------------|
| **General Ledger** | `GLAutomationAgent` | GL reconciliation, anomaly detection, expense categorization, budget vs actual |
| **Accounts Payable** | `APAutomationAgent` | Duplicate invoice detection, 3-way matching, vendor scoring, dynamic discounting |
| **Accounts Receivable** | `ARCollectionsAgent` | Collections forecasting, customer credit scoring, cash application, reminder generation |
| **Treasury** | `TreasuryManagementAgent` | Cash position, liquidity forecasting, FX hedging, crypto/fiat conversion, fraud detection |
| **Supply Chain** | `SupplyChainAgent` | AI supplier selection, demand forecasting, shipment tracking, risk assessment, freight optimization |
| **HR & Payroll** | `HRPayrollAgent` | Skills gap analysis, attrition prediction, multi-country payroll, labor law compliance |
| **Sales & Projects** | `SalesPipelineAgent` | Revenue forecasting, deal risk, customer retention, project health, milestone invoicing |
| **Financial Forecasting** | `FinancialForecastingAgent` | Multi-scenario forecasts, tax liability, ESG reporting, fraud patterns, stress testing |

---

## What's Inside

| Pattern | File | Description |
|---|---|---|
| Tool-use agent | `agents/order_agent.py` | Manages order lifecycle: retrieve, verify inventory, update status |
| Tool-use agent | `agents/inventory_agent.py` | Monitors stock levels, auto-creates purchase orders |
| Multi-agent orchestration | `patterns/multi_agent.py` | Routes tasks across specialist agents |
| Human-in-the-loop | `patterns/human_in_loop.py` | Gates high-value actions on human approval |
| Async orchestrator | `patterns/async_orchestrator.py` | Runs multiple agents concurrently |
| Teams approval | `patterns/teams_approval.py` | Microsoft Teams Adaptive Card approval callback |
| Full ERP orchestrator | `patterns/erp_orchestrator.py` | Routes to all 8 financial domains automatically |
| Simulated ERP tools | `tools/erp_tools.py` | Drop-in stubs for Dynamics 365 / Dataverse calls |

All patterns share a single `BaseERPAgent` agentic loop (`agents/base.py`) and are independently testable with no live API required.

---

## Architecture

```
ERPOrchestrator
├── GLAutomationAgent         ← gl_tools.py
├── APAutomationAgent         ← ap_tools.py
├── ARCollectionsAgent        ← ar_tools.py
├── TreasuryManagementAgent   ← treasury_tools.py
├── SupplyChainAgent          ← supply_chain_tools.py
├── HRPayrollAgent            ← hr_tools.py
├── SalesPipelineAgent        ← sales_tools.py
└── FinancialForecastingAgent ← forecasting_tools.py
```

---

## Setup

```bash
# 1. Install
pip install -e ".[dev]"

# 2. Set your API key
cp .env.example .env
# edit .env → ANTHROPIC_API_KEY=sk-...

# 3. Run tests (no API key needed — client is mocked)
pytest
```

---

## Quick Start

### Full ERP Orchestrator (routes automatically)

```python
import anthropic
from agentic_erp.patterns.erp_orchestrator import ERPOrchestrator

orchestrator = ERPOrchestrator(client=anthropic.Anthropic())

# Routes to the right agent(s) automatically
results = orchestrator.run("Check liquidity forecast and flag any cash shortages")

# Or target a specific domain directly
gl_result = orchestrator.run_domain("gl", "Reconcile GL for period 2025-01 and detect anomalies")
```

### Individual Domain Agents

```python
from agentic_erp.agents.treasury_agent import TreasuryManagementAgent

agent = TreasuryManagementAgent()
print(agent.run("Convert 50000 USD to XRP and check fraud risk on VND-001 for 45000 USD"))
```

### Order Processing Agent

```python
from agentic_erp.agents.order_agent import OrderProcessingAgent

agent = OrderProcessingAgent()
print(agent.run("Check inventory for ORD-001 and mark it as processing if stock is available."))
```

### Multi-Agent Orchestrator

```python
from agentic_erp.patterns.multi_agent import MultiAgentOrchestrator

orch = MultiAgentOrchestrator()
results = orch.run("Run the daily ERP reconciliation — check orders and replenish stock.")
for agent_name, response in results.items():
    print(f"[{agent_name}] {response}")
```

### Human-in-the-Loop (approval gate)

```python
from agentic_erp.patterns.human_in_loop import HumanInLoopAgent

def my_approval(tool_name, inputs):
    # wire to Teams Adaptive Card, Power Automate flow, Slack, etc.
    return True  # or False to block

agent = HumanInLoopAgent(approval_callback=my_approval)
print(agent.run("Cancel order ORD-002 due to customer request."))
```

---

## Connecting to Real Dynamics 365 / Dataverse

The functions in `tools/erp_tools.py` are stubs. Swap them for real calls:

```python
# Example: replace get_order with a Dataverse Web API call
import requests, os

def get_order(order_id: str) -> dict:
    url = f"{os.environ['D365_URL']}/api/data/v9.2/salesorders({order_id})"
    headers = {"Authorization": f"Bearer {get_token()}"}
    r = requests.get(url, headers=headers)
    return r.json()
```

---

## Innovation Roadmap Coverage

### A. General Ledger
- AI-powered GL reconciliation to auto-detect mismatches
- AI-driven expense categorization using machine learning
- Automated bank reconciliation with AI anomaly detection
- AI-powered fraud detection in financial transactions
- Predictive AI-driven budgeting

### B. Accounts Payable
- AI-driven duplicate invoice detection
- Automated three-way matching (invoices, POs, receipts)
- AI-based supplier performance tracking & vendor credit scoring
- Dynamic discounting AI for early payment optimization

### C. Accounts Receivable
- AI-driven collections forecasting for unpaid invoices
- AI-based credit scoring for clients
- Real-time payment matching & cash application automation
- AI-generated collection reminders

### D. Cash & Bank Management
- Instant crypto-fiat conversions (XRP/USDT) inside D365
- AI-based liquidity forecasting
- AI-automated FX hedging
- AI-driven payment fraud detection
- Multi-entity treasury management

### E. Supply Chain & Procurement
- AI-powered supplier selection
- AI-driven demand forecasting
- IoT-based smart shipment tracking
- Predictive supply chain risk analytics
- AI-based freight cost optimization

### F. HR & Payroll
- AI-driven skills gap analysis
- Automated compliance in multi-country payroll
- AI-based payroll fraud detection
- AI-driven attrition prediction analytics
- Real-time labor law compliance alerts

### G. Sales & Project Management
- AI-generated customer retention insights
- Predictive analytics for revenue forecasting
- AI-powered deal risk assessment
- Automated invoice generation from project milestones
- Project margin optimization

### H. Advanced Innovations
- AI-based sustainability tracking (ESG compliance)
- Multi-scenario financial risk modeling
- Automated international tax compliance reporting
- AI fraud pattern detection (structuring, self-approval)
- Financial stress testing & scenario analysis

---

## Docs

- [Strategic Innovation Report](docs/strategic-innovation-report.md) — AI-driven ERP transformation roadmap mapped to these patterns

---

## Requirements

- Python 3.11+
- `anthropic >= 0.40.0`
- `pydantic >= 2.0.0`
- `python-dotenv >= 1.0.0`
