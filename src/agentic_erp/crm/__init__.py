"""CRM agents sub-package — lead scoring, customer success, sales pipeline, churn prediction."""

from agentic_erp.crm.lead_scoring_agent import LeadScoringAgent
from agentic_erp.crm.customer_success_agent import CustomerSuccessAgent
from agentic_erp.crm.sales_pipeline_agent import SalesPipelineAgent
from agentic_erp.crm.churn_prediction_agent import ChurnPredictionAgent

__all__ = [
    "LeadScoringAgent",
    "CustomerSuccessAgent",
    "SalesPipelineAgent",
    "ChurnPredictionAgent",
]
