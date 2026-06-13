# Agentic ERP Patterns — Documentation Index

A reference guide for choosing and connecting the patterns in this repository.

---

## Pattern Decision Guide

```
Do you need a human to approve high-value actions?
├── YES → HumanInLoopAgent  (patterns/human_in_loop.py)
│          └── Integrate with Teams?  → TeamsApprovalCallback (patterns/teams_approval.py)
└── NO  → Does the task span multiple domains?
           ├── YES, run sequentially → MultiAgentOrchestrator  (patterns/multi_agent.py)
           ├── YES, run in parallel  → AsyncMultiAgentOrchestrator (patterns/async_orchestrator.py)
           └── NO  → Pick the specialist agent for your domain (see table below)
```

---

## Agents

| Agent | File | Domain | Key Tools |
|---|---|---|---|
| `OrderProcessingAgent` | `agents/order_agent.py` | Order lifecycle | `get_order`, `update_order_status`, `check_inventory` |
| `InventoryAgent` | `agents/inventory_agent.py` | Stock & replenishment | `list_low_stock_items`, `create_purchase_order` |
| `FraudDetectionAgent` | `agents/fraud_detection_agent.py` | GL anomaly & fraud | `scan_transactions`, `flag_transaction`, `get_account_risk_profile` |
| `CryptoPaymentAgent` | `agents/crypto_payment_agent.py` | XRP / stablecoin payments | `initiate_crypto_payment`, `get_crypto_payment`, `confirm_payment_settlement` |
| `ComplianceAgent` | `agents/compliance_agent.py` | Multi-jurisdiction tax & AML | `get_jurisdiction_rules`, `check_transaction_compliance`, `generate_compliance_report` |
| `CashFlowForecastAgent` | `agents/cashflow_forecast_agent.py` | Treasury & FX risk | `get_account_balances`, `get_fx_rates`, `forecast_cash_flow` |
| `VendorRiskAgent` | `agents/vendor_risk_agent.py` | Vendor scoring & SLA payments | `get_vendor_profile`, `score_vendor_risk`, `trigger_sla_payment` |
| `GameRevenueAnalyticsAgent` | `agents/game_analytics_agent.py` | Player behaviour & monetization | `get_player_cohort`, `get_revenue_breakdown`, `forecast_game_revenue` |

---

## Patterns

| Pattern | File | When to Use |
|---|---|---|
| `MultiAgentOrchestrator` | `patterns/multi_agent.py` | Route a task to 1–N specialists sequentially; results are collected as a dict |
| `AsyncMultiAgentOrchestrator` | `patterns/async_orchestrator.py` | Same routing, but agents run concurrently via `asyncio.gather` — faster for independent tasks |
| `HumanInLoopAgent` | `patterns/human_in_loop.py` | Gate high-value tool calls on human approval; default callback is stdin |
| `TeamsApprovalCallback` | `patterns/teams_approval.py` | Drop-in approval callback that sends a Teams Adaptive Card and polls Power Automate for the decision |

---

## Base Classes

| Class | File | Notes |
|---|---|---|
| `BaseERPAgent` | `agents/base.py` | Synchronous tool-use loop; subclass and implement `_dispatch_tool` |
| `AsyncBaseERPAgent` | `agents/async_base.py` | Async version; `_dispatch_tool` is a coroutine; use with `AsyncAnthropic` client |

---

## Tools

| Module | File | Contents |
|---|---|---|
| ERP stubs | `tools/erp_tools.py` | Order, inventory, purchase order — swap for D365 connector |
| Finance | `tools/finance_tools.py` | Fraud scan, crypto payments, compliance, cash flow, FX rates |
| Vendor | `tools/vendor_tools.py` | Vendor profile, risk scoring, SLA-triggered payments |
| Analytics | `tools/analytics_tools.py` | Player cohorts, revenue breakdown, game revenue forecast |

---

## Connectors

| Connector | File | Notes |
|---|---|---|
| `D365Connector` | `connectors/d365.py` | Live Dynamics 365 / Dataverse Web API with OAuth 2.0 token caching. Requires `D365_TENANT_ID`, `D365_CLIENT_ID`, `D365_CLIENT_SECRET`, `D365_ENVIRONMENT_URL` env vars. |

---

## Further Reading

- [Strategic Innovation Report](strategic-innovation-report.md) — AI-driven ERP transformation roadmap mapped to these patterns
- [Anthropic Claude API docs](https://docs.anthropic.com)
- [Dynamics 365 Web API reference](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/overview)
- [Power Automate HTTP connector](https://learn.microsoft.com/en-us/connectors/webcontents/)
- [Teams Incoming Webhooks](https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook)
