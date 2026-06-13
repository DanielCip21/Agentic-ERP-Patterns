"""ERP agents sub-package — procurement, finance, HR, and manufacturing."""

from agentic_erp.erp.procurement_agent import ProcurementAgent
from agentic_erp.erp.finance_agent import FinanceAgent
from agentic_erp.erp.hr_agent import HRAgent
from agentic_erp.erp.manufacturing_agent import ManufacturingAgent

__all__ = [
    "ProcurementAgent",
    "FinanceAgent",
    "HRAgent",
    "ManufacturingAgent",
]
