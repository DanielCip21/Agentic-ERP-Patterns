"""Agentic ERP Patterns — Claude-powered agent patterns for enterprise ERP systems."""

from agentic_erp.agents.order_agent import OrderProcessingAgent
from agentic_erp.agents.inventory_agent import InventoryAgent
from agentic_erp.patterns.multi_agent import MultiAgentOrchestrator
from agentic_erp.patterns.human_in_loop import HumanInLoopAgent
from agentic_erp.agents.fraud_detection_agent import FraudDetectionAgent
from agentic_erp.agents.crypto_payment_agent import CryptoPaymentAgent
from agentic_erp.agents.compliance_agent import ComplianceAgent
from agentic_erp.agents.cashflow_forecast_agent import CashFlowForecastAgent
from agentic_erp.agents.vendor_risk_agent import VendorRiskAgent
from agentic_erp.agents.game_analytics_agent import GameRevenueAnalyticsAgent

__all__ = [
    "OrderProcessingAgent",
    "InventoryAgent",
    "MultiAgentOrchestrator",
    "HumanInLoopAgent",
    "FraudDetectionAgent",
    "CryptoPaymentAgent",
    "ComplianceAgent",
    "CashFlowForecastAgent",
    "VendorRiskAgent",
    "GameRevenueAnalyticsAgent",
]
