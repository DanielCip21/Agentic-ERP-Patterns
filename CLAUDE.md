# Agentic ERP+CRM — Claude Code Project Guide

## Project Purpose
Agentic ERP+CRM platform using Claude AI agents for enterprise automation.
Currently in **DEMO / TEST / CONCEPT MODE** — no live credentials configured yet.

## Active Branch
Development branch: `claude/monitoring-system-concept-seamra`
Never push directly to `main` — always develop on feature or claude/* branches.

## Architecture Summary
- **src/agentic_erp/agents/** — ERP + CRM agents (OrderAgent, InventoryAgent, CRMAgent, etc.)
- **src/agentic_erp/tools/** — Tool definitions for agent tool-use loops
- **src/agentic_erp/patterns/** — Orchestration patterns (multi-agent, async, human-in-loop)
- **src/agentic_erp/connectors/** — Infrastructure connectors (n8n, Uptime Kuma, Coolify, D365)
- **dynamics-365-agentic-rag/** — Dynamics 365 RAG sub-project with 10 specialised agents
- **monitor/** — Demo monitoring system (no credentials required)
- **tests/** — Full mock test suite (94+ tests, all run without API keys)

## Daily Monitoring Routine
Run these commands every session to verify health:

```bash
# 1. Run all mock-safe tests
pytest tests/ --ignore=tests/integration -q

# 2. Show live dashboard
python monitor/demo_monitor.py

# 3. Generate dated report (saved to monitor/reports/)
python monitor/daily_report.py
```

The GitHub Actions workflow `.github/workflows/daily_monitor.yml` runs this automatically at 06:00 UTC.

## Coding Standards
- All agents extend `BaseERPAgent` (src/agentic_erp/agents/base.py)
- D365 agents extend `BaseAgent` (dynamics-365-agentic-rag/agents/base_agent.py)
- Every new agent needs a corresponding test file in tests/
- Tests must use `unittest.mock.MagicMock` for the Anthropic client — never real API keys in tests
- Default model: `claude-haiku-4-5-20251001` (fast, cheap for ERP tasks)
- Use `claude-sonnet-4-6` for complex reasoning tasks (pipeline optimisation, revenue intelligence)

## Credentials Status
No credentials configured yet. When ready, add to `.env` (see `.env.example`):
- `ANTHROPIC_API_KEY` — required for live agent runs
- `D365_*` vars — for Dynamics 365 integration
- `TEAMS_WEBHOOK_URL` — for Teams approval flows
- n8n / Coolify / Uptime Kuma URLs — for infrastructure connectors

## Git Workflow
- Commit frequently with clear messages
- Push to `claude/monitoring-system-concept-seamra` regularly
- Tag milestones: `git tag v0.x.0-concept`
- Integration tests only run when secrets are present (safe for demo mode)

## What to Do Each Session
1. Pull latest from origin
2. Run `python monitor/demo_monitor.py` for instant status
3. Run tests: `pytest tests/ --ignore=tests/integration -q`
4. Work on whatever task is requested
5. Commit and push before session ends

## Project Status Tracker

| Component | Status | Notes |
|-----------|--------|-------|
| Core ERP Agents | COMPLETE | 6 agents, all tested |
| CRM Agent | COMPLETE | Leads, contacts, pipeline |
| D365 RAG Agents | COMPLETE | 10 agents + MCP server |
| Orchestration Patterns | COMPLETE | 5 patterns |
| Infrastructure Connectors | COMPLETE | 4 connectors (structure only) |
| Demo Monitoring System | COMPLETE | No credentials needed |
| Daily CI Workflow | COMPLETE | Runs at 06:00 UTC |
| Live Agent Runs | PENDING | Needs ANTHROPIC_API_KEY |
| D365 Integration | PENDING | Needs D365 credentials |
| Teams Approval Flow | PENDING | Needs Teams webhook |
| n8n Automation | PENDING | Needs n8n URL |
| Uptime Kuma | PENDING | Needs UptimeKuma URL |
