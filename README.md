# Agentic ERP Patterns

Enterprise Agentic AI architecture patterns for Microsoft Dynamics 365, Power Platform, Azure AI, Copilot Studio, Dataverse, and ERP automation.

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

## Architecture

```
ERPOrchestrator
├── GLAutomationAgent      ← gl_tools.py
├── APAutomationAgent      ← ap_tools.py
├── ARCollectionsAgent     ← ar_tools.py
├── TreasuryManagementAgent← treasury_tools.py
├── SupplyChainAgent       ← supply_chain_tools.py
├── HRPayrollAgent         ← hr_tools.py
├── SalesPipelineAgent     ← sales_tools.py
└── FinancialForecastingAgent ← forecasting_tools.py
```

Each agent follows the **Claude tool-use agentic loop** pattern: the agent receives a task, calls tools iteratively, and returns a final synthesized response.

---

## Quick Start

```python
import anthropic
from agentic_erp.patterns.erp_orchestrator import ERPOrchestrator

orchestrator = ERPOrchestrator(client=anthropic.Anthropic())

# Route automatically to the right agent(s)
results = orchestrator.run("Check liquidity forecast and flag any cash shortages")

# Or target a specific domain
gl_result = orchestrator.run_domain("gl", "Reconcile GL for period 2025-01 and detect anomalies")
```

### Individual agents

```python
from agentic_erp.agents.treasury_agent import TreasuryManagementAgent

agent = TreasuryManagementAgent()
print(agent.run("Convert 50000 USD to XRP and check the fraud risk on VND-001 for 45000 USD"))
```

---

## Setup

```bash
pip install -e .
cp .env.example .env   # add ANTHROPIC_API_KEY
pytest
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
