"""Live integration tests for TeamsApprovalCallback — require real env vars.

These tests POST a real Adaptive Card to Teams and poll the Power Automate
response URL. They are skipped when TEAMS_WEBHOOK_URL is not set.

NOTE: These tests send a real Teams message. Run them manually or in a
dedicated integration environment — not in a shared channel.
"""

from __future__ import annotations

import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("TEAMS_WEBHOOK_URL"),
    reason="Teams secrets not configured",
)

from agentic_erp.patterns.teams_approval import TeamsApprovalCallback


@pytest.fixture(scope="module")
def callback():
    return TeamsApprovalCallback(
        webhook_url=os.environ["TEAMS_WEBHOOK_URL"],
        response_url=os.environ["TEAMS_RESPONSE_URL"],
        timeout_s=120,
        poll_interval_s=5,
    )


def test_card_posts_without_error(callback):
    """Verify the card is accepted by the Teams webhook (HTTP 200/202)."""
    card = callback._build_card(
        "create_purchase_order",
        {"sku": "SKU-B", "quantity": 50, "supplier": "Acme Supplies"},
    )
    # _post_to_teams raises on non-200 — if it returns, the card was accepted
    callback._post_to_teams(card)
