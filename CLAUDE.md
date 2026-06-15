# Agentic ERP Patterns — Claude Guide

## What This Repo Is

Enterprise Agentic AI patterns for **Microsoft Dynamics 365 / Dataverse / Power Platform** using the **Anthropic Claude SDK**. The codebase is structured as a Python package (`agentic_erp`) with independently testable agents, orchestration patterns, and simulated ERP tool stubs.

---

## Project Layout

```
src/agentic_erp/
  agents/
    base.py                            # BaseERPAgent — core Claude tool-use loop (max 10 turns)
    async_base.py                      # Async variant of BaseERPAgent
    autonomous_profitability_agent.py  # ★ Autonomous Profitability Agent (see below)
    order_agent.py                     # Order lifecycle management
    inventory_agent.py                 # Stock monitoring + PO creation
    cashflow_forecast_agent.py
    compliance_agent.py
    crypto_payment_agent.py
    fraud_detection_agent.py
    game_analytics_agent.py
    vendor_risk_agent.py
  prompts/
    autonomous_prompts.py  # ★ 10 specialist persona prompts + composite system prompt
  patterns/
    multi_agent.py           # Keyword-based task router → specialist agents
    human_in_loop.py         # Approval-gated tool calls (Teams / callback)
    async_orchestrator.py    # Async multi-agent orchestration
    teams_approval.py        # MS Teams Adaptive Card approval flow
  tools/
    erp_tools.py             # Stub D365/Dataverse calls (replace for production)
    analytics_tools.py
    finance_tools.py
    vendor_tools.py
  connectors/
    d365.py                  # Dynamics 365 REST connector

tests/
  test_agents.py                       # Unit tests — Anthropic client fully mocked
  test_autonomous_profitability.py     # ★ Tests for profitability agent + prompts
  integration/                         # Live D365 + Teams tests (skipped without secrets)

dynamics-365-agentic-rag/    # Separate RAG sub-project
docs/                        # Strategic innovation report
```

---

## Development Commands

```bash
make install        # pip install -e ".[dev]"
make test           # pytest unit tests (no API key needed)
make test-cov       # pytest with HTML coverage report
make lint           # ruff check + mypy
make format         # black + ruff --fix
make all            # lint + test-cov
```

---

## Key Architectural Rules

1. **`BaseERPAgent`** (`agents/base.py`) drives the agentic loop. All agents subclass it and override `_dispatch_tool()`.
2. **Tool stubs** in `tools/` return realistic fake data. Swap them for real Dataverse Web API calls in production.
3. **Unit tests** mock `anthropic.Anthropic` — no live key needed. Use `ANTHROPIC_API_KEY=sk-test-placeholder` as the env var.
4. **Integration tests** under `tests/integration/` are gated behind GitHub Actions secrets and skipped automatically on forks.
5. **Human-in-the-loop** gates are triggered by tool names matching `update_order_status` or `create_purchase_order`. Wire the approval callback to Teams Adaptive Cards or Power Automate.

---

## Environment Variables

See `.env.example` for the full list. Copy to `.env` to run locally:

```bash
cp .env.example .env
```

Required for live integration only — unit tests need none of these.

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API access |
| `D365_TENANT_ID` | Azure AD tenant |
| `D365_CLIENT_ID` | App registration client ID |
| `D365_CLIENT_SECRET` | App registration secret |
| `D365_ENVIRONMENT_URL` | e.g. `https://yourorg.crm.dynamics.com` |
| `TEAMS_WEBHOOK_URL` | Incoming webhook for approval cards |
| `TEAMS_RESPONSE_URL` | Power Automate trigger for responses |

---

## Running Tests

```bash
# Unit tests only (always works, no credentials)
pytest --ignore=tests/integration

# With coverage
pytest --ignore=tests/integration --cov=src/agentic_erp --cov-report=html

# Integration (requires .env with D365 + Teams secrets)
pytest tests/integration
```

---

## Autonomous Profitability Layer

All work in this repo is governed by the principle of **autonomous, continuous
profitability improvement**.  The `AutonomousProfitabilityAgent` embeds ten
specialist engineering personas that Claude cycles through on every task:

| # | Persona | Profitability Contribution |
|---|---------|---------------------------|
| 1 | Startup Engineer | Deliver value fast; avoid over-engineering waste |
| 2 | Codebase Auditor | Surface quality debt that increases maintenance cost |
| 3 | Production Debugger | Root-cause failures that erode reliability and revenue |
| 4 | Performance Optimizer | Cut latency and infra cost; raise throughput |
| 5 | Architecture Rebuilder | Reduce coupling so the system scales cheaply |
| 6 | Systems Architect | Design for real growth; avoid costly re-architecture |
| 7 | Technical Lead | Challenge decisions; prefer long-term ROI |
| 8 | Security Auditor | Prevent breaches that destroy margin and trust |
| 9 | DevOps Engineer | Maximise uptime; automate toil; ship faster |
| 10 | Profitability Analyst | Translate every metric into financial impact |

### Using the agent

```python
from agentic_erp.agents import AutonomousProfitabilityAgent

agent = AutonomousProfitabilityAgent()
report = agent.run("Run a full profitability analysis and give me the top 3 actions.")
print(report)
```

### Using a single persona prompt

```python
from agentic_erp.prompts import get_persona_prompt, AUTONOMOUS_PROFITABILITY_SYSTEM

# Embed in any agent's system_prompt
security_directive = get_persona_prompt("security_auditor")
```

### Persona names

`startup_engineer` · `codebase_auditor` · `production_debugger` ·
`performance_optimizer` · `architecture_rebuilder` · `systems_architect` ·
`technical_lead` · `security_auditor` · `devops_engineer` ·
`autonomous_profitability`

---

## Adding a New Agent

1. Create `src/agentic_erp/agents/my_agent.py`
2. Subclass `BaseERPAgent`
3. Define `TOOLS` list (Claude tool schemas)
4. Override `_dispatch_tool(tool_name, tool_input)` to handle each tool
5. Add unit tests in `tests/` using the mocked client pattern from `test_agents.py`
6. Consider embedding one or more persona prompts from `agentic_erp.prompts` to
   ensure the agent reasons through a profitability lens by default
