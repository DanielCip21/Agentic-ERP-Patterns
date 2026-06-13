"""Connectors sub-package — Dynamics 365, Salesforce, Power Platform, Azure AI, Dataverse."""

from agentic_erp.connectors.dynamics365 import Dynamics365Connector
from agentic_erp.connectors.salesforce import SalesforceConnector
from agentic_erp.connectors.power_platform import PowerPlatformConnector
from agentic_erp.connectors.azure_ai import AzureAIConnector
from agentic_erp.connectors.dataverse import DataverseConnector

__all__ = [
    "Dynamics365Connector",
    "SalesforceConnector",
    "PowerPlatformConnector",
    "AzureAIConnector",
    "DataverseConnector",
]
