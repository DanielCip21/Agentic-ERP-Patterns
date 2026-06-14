"""Pattern: Full ERP multi-agent orchestrator routing tasks to all specialist agents.

Covers all 8 product domains from the PTW America D365 Innovation Roadmap:
  GL, AP, AR, Treasury, Supply Chain, HR/Payroll, Sales, Financial Forecasting
"""

from __future__ import annotations

from agentic_erp.agents.gl_agent import GLAutomationAgent
from agentic_erp.agents.ap_agent import APAutomationAgent
from agentic_erp.agents.ar_agent import ARCollectionsAgent
from agentic_erp.agents.treasury_agent import TreasuryManagementAgent
from agentic_erp.agents.supply_chain_agent import SupplyChainAgent
from agentic_erp.agents.hr_agent import HRPayrollAgent
from agentic_erp.agents.sales_agent import SalesPipelineAgent
from agentic_erp.agents.forecasting_agent import FinancialForecastingAgent

_ROUTING_MAP: dict[str, list[str]] = {
    "gl": ["gl", "journal", "reconcil", "ledger", "trial balance", "budget", "expense categor", "anomal"],
    "ap": ["invoice", "vendor", "payable", "supplier", "purchase order", "duplicate", "three-way", "3-way", "discount"],
    "ar": ["receivable", "collection", "overdue", "credit score", "customer credit", "cash application", "reminder"],
    "treasury": ["cash position", "liquidity", "fx", "hedge", "crypto", "xrp", "currency convert", "bank reconcil", "treasury", "fraud payment"],
    "supply_chain": ["supply chain", "shipment", "freight", "logistics", "demand forecast", "supplier select", "procure", "reorder"],
    "hr": ["employee", "payroll", "skills gap", "attrition", "labor law", "compliance hr", "salary", "workforce"],
    "sales": ["sales", "pipeline", "opportunity", "deal", "revenue forecast", "project health", "customer retention", "milestone invoice"],
    "forecasting": ["financial forecast", "scenario", "esg", "tax liabilit", "fraud pattern", "stress test", "risk model", "compliance report"],
}


def _classify_task(task: str) -> list[str]:
    task_lower = task.lower()
    matched: list[str] = []
    for domain, keywords in _ROUTING_MAP.items():
        if any(kw in task_lower for kw in keywords):
            matched.append(domain)
    return matched if matched else list(_ROUTING_MAP.keys())


class ERPOrchestrator:
    """Routes any ERP task to the appropriate specialist agent(s)."""

    def __init__(self, **agent_kwargs) -> None:
        self._agents = {
            "gl": GLAutomationAgent(**agent_kwargs),
            "ap": APAutomationAgent(**agent_kwargs),
            "ar": ARCollectionsAgent(**agent_kwargs),
            "treasury": TreasuryManagementAgent(**agent_kwargs),
            "supply_chain": SupplyChainAgent(**agent_kwargs),
            "hr": HRPayrollAgent(**agent_kwargs),
            "sales": SalesPipelineAgent(**agent_kwargs),
            "forecasting": FinancialForecastingAgent(**agent_kwargs),
        }

    def run(self, task: str) -> dict[str, str]:
        """Classify the task, dispatch to relevant agents, and return all responses."""
        domains = _classify_task(task)
        return {domain: self._agents[domain].run(task) for domain in domains}

    def run_domain(self, domain: str, task: str) -> str:
        """Run a task against a specific agent domain directly."""
        agent = self._agents.get(domain)
        if not agent:
            raise ValueError(f"Unknown domain '{domain}'. Available: {list(self._agents.keys())}")
        return agent.run(task)
