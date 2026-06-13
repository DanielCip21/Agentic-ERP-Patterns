# Agentic ERP Patterns

Enterprise Agentic AI architecture patterns for **Microsoft Dynamics 365**, **Power Platform**, **Azure AI**, **Copilot Studio**, and **Dataverse** — built with the Anthropic Claude SDK.

---

## What's Inside

| Pattern | File | Description |
|---|---|---|
| Tool-use agent | `agents/order_agent.py` | Manages order lifecycle: retrieve, verify inventory, update status |
| Tool-use agent | `agents/inventory_agent.py` | Monitors stock levels, auto-creates purchase orders |
| Multi-agent orchestration | `patterns/multi_agent.py` | Routes tasks across specialist agents |
| Human-in-the-loop | `patterns/human_in_loop.py` | Gates high-value actions on human approval |
| Simulated ERP tools | `tools/erp_tools.py` | Drop-in stubs for Dynamics 365 / Dataverse calls |

All patterns share a single `BaseERPAgent` agentic loop (`agents/base.py`) and are independently testable with no live API required.

---

## Quick Start

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

## Usage Examples

### Order Processing Agent

```python
from agentic_erp.agents.order_agent import OrderProcessingAgent

agent = OrderProcessingAgent()
print(agent.run("Check inventory for ORD-001 and mark it as processing if stock is available."))
```

### Inventory Replenishment Agent

```python
from agentic_erp.agents.inventory_agent import InventoryAgent

agent = InventoryAgent()
print(agent.run("Scan for low-stock items and create purchase orders."))
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

## Docs

- [Strategic Innovation Report](docs/strategic-innovation-report.md) — AI-driven ERP transformation roadmap mapped to these patterns

---

## Requirements

- Python 3.11+
- `anthropic >= 0.40.0`
- `pydantic >= 2.0.0`
- `python-dotenv >= 1.0.0`
