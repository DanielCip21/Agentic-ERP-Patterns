"""Pattern: Webhook processor agent — classify, route, acknowledge, and dead-letter webhooks."""

from __future__ import annotations

from typing import Any
from datetime import datetime

from agentic_erp.agents.base import BaseERPAgent

# ---------------------------------------------------------------------------
# Simulated backend data
# ---------------------------------------------------------------------------
_ROUTING_TABLE: dict[str, str] = {
    "order.created": "order_processing_workflow",
    "order.shipped": "fulfillment_notification_workflow",
    "payment.received": "accounts_receivable_workflow",
    "payment.failed": "dunning_workflow",
    "customer.created": "crm_sync_workflow",
    "lead.converted": "sales_handoff_workflow",
    "invoice.overdue": "collections_workflow",
}

_PROCESSED_WEBHOOKS: dict[str, dict] = {}
_DEAD_LETTERS: list[dict] = []


def _classify_webhook(payload: dict) -> dict[str, Any]:
    event_type = (
        payload.get("event_type") or payload.get("type") or payload.get("event")
    )
    source = payload.get("source") or "unknown"
    if not event_type:
        return {
            "error": "Could not determine event_type from payload",
            "payload_keys": list(payload.keys()),
        }
    is_known = event_type in _ROUTING_TABLE
    return {
        "event_type": event_type,
        "source": source,
        "is_known_event": is_known,
        "suggested_workflow": _ROUTING_TABLE.get(event_type),
        "classified_at": datetime.utcnow().isoformat(),
    }


def _route_to_workflow(event_type: str, payload: dict) -> dict[str, Any]:
    workflow = _ROUTING_TABLE.get(event_type)
    if not workflow:
        return {"error": f"No workflow registered for event_type '{event_type}'"}
    webhook_id = f"WH-{len(_PROCESSED_WEBHOOKS) + 1:06d}"
    _PROCESSED_WEBHOOKS[webhook_id] = {
        "webhook_id": webhook_id,
        "event_type": event_type,
        "workflow": workflow,
        "status": "routed",
        "routed_at": datetime.utcnow().isoformat(),
    }
    return {
        "webhook_id": webhook_id,
        "event_type": event_type,
        "routed_to": workflow,
        "status": "routed",
        "routed_at": _PROCESSED_WEBHOOKS[webhook_id]["routed_at"],
    }


def _acknowledge_webhook(webhook_id: str) -> dict[str, Any]:
    wh = _PROCESSED_WEBHOOKS.get(webhook_id)
    if not wh:
        return {"error": f"Webhook {webhook_id} not found"}
    wh["status"] = "acknowledged"
    wh["acknowledged_at"] = datetime.utcnow().isoformat()
    return {
        "webhook_id": webhook_id,
        "status": "acknowledged",
        "acknowledged_at": wh["acknowledged_at"],
    }


def _dead_letter(webhook_id: str, reason: str) -> dict[str, Any]:
    entry = {
        "webhook_id": webhook_id,
        "reason": reason,
        "dead_lettered_at": datetime.utcnow().isoformat(),
        "retry_count": 0,
        "status": "dead_lettered",
    }
    _DEAD_LETTERS.append(entry)
    if webhook_id in _PROCESSED_WEBHOOKS:
        _PROCESSED_WEBHOOKS[webhook_id]["status"] = "dead_lettered"
    return entry


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------
_TOOLS = [
    {
        "name": "classify_webhook",
        "description": "Classify an incoming webhook payload to determine its event type and source.",
        "input_schema": {
            "type": "object",
            "properties": {
                "payload": {
                    "type": "object",
                    "description": "Raw webhook payload dict",
                },
            },
            "required": ["payload"],
        },
    },
    {
        "name": "route_to_workflow",
        "description": "Route a classified webhook event to the appropriate downstream workflow.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "description": "Classified event type (e.g. order.created)",
                },
                "payload": {
                    "type": "object",
                    "description": "Webhook payload to pass to the workflow",
                },
            },
            "required": ["event_type", "payload"],
        },
    },
    {
        "name": "acknowledge_webhook",
        "description": "Acknowledge that a webhook has been successfully processed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "webhook_id": {"type": "string", "description": "Webhook tracking ID"},
            },
            "required": ["webhook_id"],
        },
    },
    {
        "name": "dead_letter",
        "description": "Move a failing webhook to the dead-letter queue with a reason for failure.",
        "input_schema": {
            "type": "object",
            "properties": {
                "webhook_id": {"type": "string", "description": "Webhook tracking ID"},
                "reason": {
                    "type": "string",
                    "description": "Reason the webhook could not be processed",
                },
            },
            "required": ["webhook_id", "reason"],
        },
    },
]

_SYSTEM_PROMPT = """You are a Webhook Processing Agent for an enterprise event-driven platform.
Your responsibilities:
1. Classify incoming webhooks to identify the event type and source system
2. Route classified events to the appropriate downstream workflow
3. Acknowledge webhooks after successful routing to prevent re-delivery
4. Dead-letter webhooks that cannot be processed after exhausting retries

Unknown event types must be dead-lettered with a descriptive reason. Always acknowledge successful routes.
Log all routing decisions for event traceability and replay capability."""


class WebhookProcessorAgent(BaseERPAgent):
    """Processes, classifies, routes, and dead-letters incoming webhook events."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "classify_webhook":
                return _classify_webhook(**inputs)
            case "route_to_workflow":
                return _route_to_workflow(**inputs)
            case "acknowledge_webhook":
                return _acknowledge_webhook(**inputs)
            case "dead_letter":
                return _dead_letter(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
