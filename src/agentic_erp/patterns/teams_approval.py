"""Pattern: Human-in-the-loop approval via Microsoft Teams Adaptive Cards.

Sends an Adaptive Card to a Teams channel via an incoming webhook and polls
the Power Automate response URL for the reviewer's decision.

Drop-in replacement for the stdin approval callback in HumanInLoopAgent:

    from agentic_erp.patterns.teams_approval import TeamsApprovalCallback
    from agentic_erp.patterns.human_in_loop import HumanInLoopAgent

    approver = TeamsApprovalCallback(
        webhook_url=os.environ["TEAMS_WEBHOOK_URL"],
        response_url=os.environ["TEAMS_RESPONSE_URL"],  # Power Automate HTTP trigger
    )
    agent = HumanInLoopAgent(approval_callback=approver)
"""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from typing import Any


class TeamsApprovalCallback:
    """Sends an Adaptive Card to Teams and polls for approval/rejection.

    Args:
        webhook_url: Incoming webhook URL for the target Teams channel.
        response_url: Power Automate HTTP trigger URL that receives the reviewer's
                      response (POST with JSON body ``{"approved": true/false, "tool_use_id": "..."}``)
                      and stores it where ``poll_url`` can retrieve it.
        poll_url:     GET endpoint that returns ``{"approved": true/false}`` once the
                      reviewer has responded. If None, falls back to ``response_url``
                      with a GET request.
        timeout_s:    Seconds to wait for a response before auto-rejecting (default 300).
        poll_interval_s: Seconds between poll attempts (default 5).
    """

    def __init__(
        self,
        webhook_url: str,
        response_url: str,
        poll_url: str | None = None,
        timeout_s: int = 300,
        poll_interval_s: int = 5,
    ) -> None:
        self._webhook_url = webhook_url
        self._response_url = response_url
        self._poll_url = poll_url or response_url
        self._timeout_s = timeout_s
        self._poll_interval_s = poll_interval_s

    def __call__(self, tool_name: str, inputs: dict[str, Any]) -> bool:
        """Send the approval card and block until the reviewer responds or timeout."""
        card = self._build_card(tool_name, inputs)
        self._post_to_teams(card)
        return self._poll_for_decision()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_card(self, tool_name: str, inputs: dict[str, Any]) -> dict:
        """Build a minimal Teams Adaptive Card for the approval request."""
        facts = [{"title": k, "value": str(v)} for k, v in inputs.items()]
        return {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {"type": "TextBlock", "text": "ERP Action Approval Required", "weight": "Bolder", "size": "Medium"},
                            {"type": "TextBlock", "text": f"Tool: **{tool_name}**", "wrap": True},
                            {"type": "FactSet", "facts": facts},
                        ],
                        "actions": [
                            {
                                "type": "Action.Http",
                                "title": "Approve",
                                "method": "POST",
                                "url": self._response_url,
                                "body": json.dumps({"approved": True}),
                            },
                            {
                                "type": "Action.Http",
                                "title": "Reject",
                                "method": "POST",
                                "url": self._response_url,
                                "body": json.dumps({"approved": False}),
                            },
                        ],
                    },
                }
            ],
        }

    def _post_to_teams(self, card: dict) -> None:
        payload = json.dumps(card).encode()
        req = urllib.request.Request(
            self._webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status not in (200, 202):
                raise RuntimeError(f"Teams webhook returned HTTP {resp.status}")

    def _poll_for_decision(self) -> bool:
        deadline = time.monotonic() + self._timeout_s
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(self._poll_url, timeout=5) as resp:
                    body = json.loads(resp.read())
                    if "approved" in body:
                        return bool(body["approved"])
            except (urllib.error.URLError, json.JSONDecodeError):
                pass
            time.sleep(self._poll_interval_s)
        # Timeout — auto-reject for safety
        return False
