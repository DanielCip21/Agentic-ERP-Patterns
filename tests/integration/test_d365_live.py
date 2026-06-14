"""Live integration tests for D365Connector — require real env vars.

Skipped automatically when D365_ENVIRONMENT_URL is not set.
"""

from __future__ import annotations

import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("D365_ENVIRONMENT_URL"),
    reason="D365 secrets not configured",
)

from agentic_erp.connectors.d365 import D365Connector


@pytest.fixture(scope="module")
def d365():
    return D365Connector()


def test_connector_obtains_token(d365):
    token = d365._get_token()
    assert isinstance(token, str) and len(token) > 20


def test_list_accounts(d365):
    """Smoke test: list up to 5 accounts from Dataverse."""
    accounts = d365.list_records("accounts", top=5)
    assert isinstance(accounts, list)


def test_list_contacts(d365):
    contacts = d365.list_records("contacts", top=5)
    assert isinstance(contacts, list)


def test_list_orders(d365):
    orders = d365.list_records("salesorders", top=5)
    assert isinstance(orders, list)
