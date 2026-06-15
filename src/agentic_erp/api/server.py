"""FastAPI server — exposes all ERP agents as HTTP endpoints for Power Automate."""

from __future__ import annotations

import time
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agentic_erp.agents.order_agent import OrderProcessingAgent
from agentic_erp.agents.inventory_agent import InventoryAgent
from agentic_erp.agents.fraud_detection_agent import FraudDetectionAgent
from agentic_erp.agents.crypto_payment_agent import CryptoPaymentAgent
from agentic_erp.agents.compliance_agent import ComplianceAgent
from agentic_erp.agents.cashflow_forecast_agent import CashFlowForecastAgent
from agentic_erp.agents.vendor_risk_agent import VendorRiskAgent
from agentic_erp.agents.game_analytics_agent import GameRevenueAnalyticsAgent
from agentic_erp.agents.fixed_assets_agent import FixedAssetsAgent
from agentic_erp.patterns.multi_agent import ERPOrchestrator

VERSION = "0.1.0"

_AGENT_REGISTRY: dict[str, dict[str, Any]] = {
    "order": {
        "cls": OrderProcessingAgent,
        "description": "Order lifecycle management: retrieve details, verify inventory, update status.",
    },
    "inventory": {
        "cls": InventoryAgent,
        "description": "Automated stock replenishment: scan low-stock items, create purchase orders.",
    },
    "fraud": {
        "cls": FraudDetectionAgent,
        "description": "Transaction anomaly detection: scan accounts, score risk, flag suspicious transactions.",
    },
    "crypto": {
        "cls": CryptoPaymentAgent,
        "description": "Crypto vendor payments via RippleNet (XRP) and Ethereum (USDT/ETH).",
    },
    "compliance": {
        "cls": ComplianceAgent,
        "description": "Multi-jurisdiction tax and AML compliance: rules lookup, transaction checks, reports.",
    },
    "cashflow": {
        "cls": CashFlowForecastAgent,
        "description": "Multi-currency cash flow forecasting: balances, FX rates, horizon projections.",
    },
    "vendor": {
        "cls": VendorRiskAgent,
        "description": "Vendor risk scoring and SLA-gated smart contract payment release.",
    },
    "analytics": {
        "cls": GameRevenueAnalyticsAgent,
        "description": "Game revenue analytics: player cohort health, revenue breakdown, genre forecasts.",
    },
    "fixed_assets": {
        "cls": FixedAssetsAgent,
        "description": "Fixed assets automation: depreciation runs, disposal gain/loss, revaluation, asset register.",
    },
}

app = FastAPI(
    title="Agentic ERP Patterns API",
    description=(
        "REST endpoints exposing Dynavyx ERP AI agents for Microsoft Power Automate, "
        "Copilot Studio, and Teams integrations."
    ),
    version=VERSION,
)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    task: str = Field(..., min_length=1, description="Natural-language task for the agent to execute")


class AgentRunResponse(BaseModel):
    domain: str
    result: str
    duration_ms: float


class OrchestratorRunResponse(BaseModel):
    results: dict[str, str]


class AgentInfo(BaseModel):
    domain: str
    description: str


class HealthResponse(BaseModel):
    status: str
    agents: int
    version: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    """Service health check — returns agent count and API version."""
    return HealthResponse(status="ok", agents=len(_AGENT_REGISTRY), version=VERSION)


@app.get("/agents", response_model=list[AgentInfo], tags=["agents"])
def list_agents() -> list[AgentInfo]:
    """List all available ERP agent domains with descriptions."""
    return [AgentInfo(domain=k, description=v["description"]) for k, v in _AGENT_REGISTRY.items()]


@app.post("/agents/{domain}/run", response_model=AgentRunResponse, tags=["agents"])
def run_agent(domain: str, body: RunRequest) -> AgentRunResponse:
    """Run a specific ERP agent by domain name and return its response."""
    if domain not in _AGENT_REGISTRY:
        raise HTTPException(
            status_code=404,
            detail=f"Agent domain '{domain}' not found. Available domains: {list(_AGENT_REGISTRY)}",
        )
    agent = _AGENT_REGISTRY[domain]["cls"]()
    t0 = time.perf_counter()
    result = agent.run(body.task)
    duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    return AgentRunResponse(domain=domain, result=result, duration_ms=duration_ms)


@app.post("/orchestrator/run", response_model=OrchestratorRunResponse, tags=["orchestrator"])
def run_orchestrator(body: RunRequest) -> OrchestratorRunResponse:
    """Route a task through the ERP orchestrator — dispatches to all matching agents."""
    orchestrator = ERPOrchestrator()
    results = orchestrator.run(body.task)
    return OrchestratorRunResponse(results=results)
