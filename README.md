# Agentic ERP+CRM Platform

Enterprise Agentic AI architecture for **ERP + CRM** — built with the Anthropic Claude SDK and powered by a fully self-hosted open-source stack.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Master ERP+CRM Orchestrator                  │
│                  (Claude AI — claude-haiku-4-5)                 │
├──────────────────────┬──────────────────────────────────────────┤
│     ERP Agents       │           CRM Agents                     │
│  ┌───────────────┐   │   ┌──────────────────────────────────┐   │
│  │ Order Agent   │   │   │        CRM Agent                 │   │
│  │ Inventory     │   │   │  Leads · Contacts · Accounts     │   │
│  │ Finance       │   │   │  Opportunities · Pipeline        │   │
│  │ Compliance    │   │   └──────────────────────────────────┘   │
│  │ Fraud Detect  │   │                                          │
│  └───────────────┘   │                                          │
├──────────────────────┴──────────────────────────────────────────┤
│                  Infrastructure Connectors                      │
│  n8n Automation · Uptime Kuma · Coolify · D365 / Dataverse     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Integrated Open-Source Stack

| Tool | Role | Repo |
|------|------|------|
| **n8n** | Workflow automation engine | [n8n-io/n8n](https://github.com/n8n-io/n8n) |
| **Coolify** | Self-hosted deployment platform | [coollabsio/coolify](https://github.com/coollabsio/coolify) |
| **Uptime Kuma** | Health monitoring & alerting | [louislam/uptime-kuma](https://github.com/louislam/uptime-kuma) |
| **ProxmoxVE Scripts** | VM/container infrastructure | [community-scripts/ProxmoxVE](https://github.com/community-scripts/ProxmoxVE) |
| **Homelab IaC** | GitOps infrastructure patterns | [khedoan/homelab](https://github.com/khedoan/homelab) |
| **Awesome Tunneling** | Secure public access (no VPN) | [anderspitman/awesome-tunneling](https://github.com/anderspitman/awesome-tunneling) |
| **Awesome Selfhosted** | Self-hosted software catalog | [awesome-selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted) |

---

## What's Inside

### ERP Agents

| Agent | File | Description |
|-------|------|-------------|
| Order Processing | `agents/order_agent.py` | Order lifecycle: retrieve, verify inventory, update status |
| Inventory | `agents/inventory_agent.py` | Stock monitoring, auto purchase orders |
| Finance | `agents/cashflow_forecast_agent.py` | Cash flow forecasting |
| Compliance | `agents/compliance_agent.py` | Regulatory compliance checks |
| Fraud Detection | `agents/fraud_detection_agent.py` | Transaction anomaly detection |
| Vendor Risk | `agents/vendor_risk_agent.py` | Supplier risk scoring |

### CRM Agents

| Agent | File | Description |
|-------|------|-------------|
| CRM | `agents/crm_agent.py` | Leads, contacts, accounts, opportunities, pipeline |

### Infrastructure Connectors

| Connector | File | Description |
|-----------|------|-------------|
| n8n | `connectors/n8n.py` | Trigger and monitor automation workflows |
| Uptime Kuma | `connectors/uptime_kuma.py` | Health checks across all services |
| Coolify | `connectors/coolify.py` | Deploy and manage services |
| D365 | `connectors/d365.py` | Microsoft Dynamics 365 / Dataverse |

### Orchestration Patterns

| Pattern | File | Description |
|---------|------|-------------|
| **Master ERP+CRM** | `patterns/master_orchestrator.py` | Unified ERP+CRM orchestrator — routes tasks to all agents |
| Multi-agent | `patterns/multi_agent.py` | ERP-only orchestrator |
| Human-in-the-loop | `patterns/human_in_loop.py` | Approval gates for high-value actions |
| Async orchestrator | `patterns/async_orchestrator.py` | Parallel async agent execution |
| Teams approval | `patterns/teams_approval.py` | Microsoft Teams adaptive card approvals |

---

## Quick Start

```bash
# 1. Install
pip install -e ".[dev]"

# 2. Set your API key
cp .env.example .env
# edit .env → ANTHROPIC_API_KEY=sk-...

# 3. Run tests
pytest
```

---

## Usage Examples

### Master ERP+CRM Orchestrator

```python
from agentic_erp.patterns.master_orchestrator import MasterERPCRMOrchestrator

orch = MasterERPCRMOrchestrator()

# Natural-language task routing — automatically hits the right agents
results = orch.run("Check all at-risk accounts and flag any unassigned leads.")
print(results["crm_agent"])

results = orch.run("Process all pending orders and replenish low stock.")
print(results["order_agent"])
print(results["inventory_agent"])

# Full daily reconciliation — ERP + CRM + infra health in one call
daily = orch.run_daily_reconciliation()
```

### CRM Agent

```python
from agentic_erp.agents.crm_agent import CRMAgent

agent = CRMAgent()

# Lead qualification
print(agent.run("List all unassigned leads, qualify them, and assign the best ones to sales1@erp.io"))

# Pipeline summary
print(agent.run("Give me the current sales pipeline summary with weighted forecast."))

# At-risk account management
print(agent.run("Find all at-risk accounts and log a follow-up call for each."))
```

### Trigger n8n Workflows

```python
from agentic_erp.patterns.master_orchestrator import MasterERPCRMOrchestrator

orch = MasterERPCRMOrchestrator(
    n8n_url="http://localhost:5678",
    n8n_api_key="your-n8n-api-key",
)

# Trigger the order-to-cash pipeline
orch.trigger_workflow("erp_order_pipeline", {
    "order_id": "ORD-003",
    "customer_id": "ACC-001",
    "sku": "SKU-A",
    "account_id": "ACC-001",
})

# Trigger CRM lead nurturing
orch.trigger_workflow("crm_lead_nurturing", {
    "lead_id": "LEAD-002",
    "company_size": 250,
    "source": "web",
})
```

### Infrastructure Health Check

```python
from agentic_erp.connectors.uptime_kuma import UptimeKumaConnector
from agentic_erp.connectors.coolify import CoolifyConnector

kuma = UptimeKumaConnector("http://localhost:3001")
print(kuma.get_all_monitor_status())

coolify = CoolifyConnector("http://localhost:8000", api_token="...")
print(coolify.get_stack_health())
```

---

## Self-Hosted Deployment

### 1. Deploy the Full Stack with Docker Compose

```bash
cp .env.example .env
# Fill in: ANTHROPIC_API_KEY, POSTGRES_PASSWORD, N8N_PASSWORD,
#          N8N_ENCRYPTION_KEY, N8N_API_KEY

docker compose -f deploy/docker-compose.yml up -d
```

Services launched:
- `http://localhost:8080` — ERP+CRM API
- `http://localhost:5678` — n8n workflow automation
- `http://localhost:3001` — Uptime Kuma monitoring

### 2. Deploy to Proxmox VE

Use the community helper scripts to provision a Debian LXC container, then run Docker Compose inside it:

```bash
# On your Proxmox shell:
bash -c "$(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/ct/docker.sh)"
```

### 3. Manage with Coolify

Import `deploy/coolify/project.yml` into your Coolify dashboard for a full GUI-managed deployment with auto-deploys on git push.

### 4. Import n8n Workflows

In n8n UI: **Workflows → Import from file**
- `deploy/n8n/workflows/erp_order_pipeline.json` — Order-to-cash automation
- `deploy/n8n/workflows/crm_lead_nurturing.json` — Lead scoring and assignment

### 5. Configure Uptime Kuma

In Uptime Kuma UI: import monitors from `deploy/uptime-kuma/monitors.json` to track all service health and get alerts.

### 6. Secure Public Access (No VPN)

Configure a zero-trust tunnel to expose services without opening firewall ports:

```bash
# Cloudflare Tunnel (recommended)
cloudflared tunnel login
cloudflared tunnel create erp-crm
cloudflared tunnel run --config deploy/tunnel/config.yml
```

Or use any alternative from `deploy/tunnel/config.yml` (frp, SirTunnel, etc.)

---

## n8n Workflow Triggers

| Workflow Key | Webhook Path | Description |
|---|---|---|
| `erp_order_pipeline` | `/webhook/erp/order-pipeline` | Order-to-cash: validate → check stock → process → update CRM |
| `crm_lead_nurturing` | `/webhook/crm/lead-nurturing` | Score lead → qualify → assign or nurture |
| `inventory_alert` | `/webhook/erp/inventory-alert` | Low-stock alert → create purchase order |
| `customer_health_check` | `/webhook/crm/health-check` | Account health scan → flag at-risk |
| `invoice_approval` | `/webhook/erp/invoice-approval` | Invoice → human approval gate → post |

---

## Connecting to Real Systems

### Microsoft Dynamics 365 / Dataverse

```python
# Replace stubs in tools/erp_tools.py with real Dataverse API calls
import requests, os

def get_order(order_id: str) -> dict:
    url = f"{os.environ['D365_URL']}/api/data/v9.2/salesorders({order_id})"
    r = requests.get(url, headers={"Authorization": f"Bearer {get_token()}"})
    return r.json()
```

### n8n (live instance)

```python
from agentic_erp.connectors.n8n import N8NConnector

n8n = N8NConnector(base_url="https://n8n.yourdomain.com", api_key="your-key")
print(n8n.list_workflows())
```

---

## Requirements

- Python 3.11+
- `anthropic >= 0.40.0`
- `pydantic >= 2.0.0`
- `python-dotenv >= 1.0.0`
- Docker + Docker Compose (for deployment)
