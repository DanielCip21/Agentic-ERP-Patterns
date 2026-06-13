"""Connectors sub-package — Dynamics 365, Salesforce, Power Platform, Azure AI, Dataverse."""

from agentic_erp.connectors.auth import AzureADTokenManager, AuthenticationError
from agentic_erp.connectors.base import BaseHTTPConnector, ConnectorError, NotFoundError, RateLimitError
from agentic_erp.connectors.dynamics365 import Dynamics365Connector, Dynamics365Config
from agentic_erp.connectors.salesforce import SalesforceConnector, SalesforceConfig
from agentic_erp.connectors.power_platform import PowerPlatformConnector, PowerPlatformConfig
from agentic_erp.connectors.azure_ai import AzureAIConnector, AzureAIConfig
from agentic_erp.connectors.dataverse import DataverseConnector, DataverseConfig

__all__ = [
    "AzureADTokenManager",
    "AuthenticationError",
    "BaseHTTPConnector",
    "ConnectorError",
    "NotFoundError",
    "RateLimitError",
    "Dynamics365Connector",
    "Dynamics365Config",
    "SalesforceConnector",
    "SalesforceConfig",
    "PowerPlatformConnector",
    "PowerPlatformConfig",
    "AzureAIConnector",
    "AzureAIConfig",
    "DataverseConnector",
    "DataverseConfig",
]
