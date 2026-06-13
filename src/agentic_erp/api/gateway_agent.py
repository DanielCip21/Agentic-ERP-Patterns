"""Pattern: API gateway agent — external API calls, health checks, event logging, fallbacks."""

from __future__ import annotations

from typing import Any
from datetime import datetime
import random

from agentic_erp.agents.base import BaseERPAgent

# ---------------------------------------------------------------------------
# Simulated backend data
# ---------------------------------------------------------------------------
_SERVICE_REGISTRY: dict[str, dict] = {
    "payment_service": {"url": "https://payments.internal/api/v2", "status": "healthy", "latency_ms": 45},
    "inventory_service": {"url": "https://inventory.internal/api/v1", "status": "healthy", "latency_ms": 120},
    "notification_service": {"url": "https://notify.internal/api/v1", "status": "degraded", "latency_ms": 890},
    "shipping_service": {"url": "https://shipping.internal/api/v3", "status": "healthy", "latency_ms": 67},
}

_API_EVENTS: list[dict] = []
_FALLBACK_RESPONSES: dict[str, dict] = {
    "notification_service": {"status": "queued", "message": "Notification queued for retry"},
}


def _call_api(endpoint: str, method: str, payload: dict | None = None) -> dict[str, Any]:
    # TODO: use httpx for real calls
    status_code = random.choice([200, 200, 200, 422, 500])
    return {
        "endpoint": endpoint,
        "method": method.upper(),
        "status_code": status_code,
        "response": {"success": status_code == 200, "data": f"Simulated response from {endpoint}"},
        "latency_ms": random.randint(30, 500),
        "called_at": datetime.utcnow().isoformat(),
    }


def _check_api_health(service_name: str) -> dict[str, Any]:
    service = _SERVICE_REGISTRY.get(service_name)
    if not service:
        return {"error": f"Service '{service_name}' not found in registry"}
    return {
        "service": service_name,
        "url": service["url"],
        "status": service["status"],
        "latency_ms": service["latency_ms"],
        "checked_at": datetime.utcnow().isoformat(),
    }


def _log_api_event(service: str, event_type: str, details: str) -> dict[str, Any]:
    event = {
        "event_id": f"EVT-{len(_API_EVENTS) + 1:05d}",
        "service": service,
        "event_type": event_type,
        "details": details,
        "logged_at": datetime.utcnow().isoformat(),
    }
    _API_EVENTS.append(event)
    return event


def _trigger_fallback(service_name: str, payload: dict) -> dict[str, Any]:
    fallback = _FALLBACK_RESPONSES.get(service_name)
    if not fallback:
        return {"error": f"No fallback configured for service '{service_name}'"}
    return {
        "service": service_name,
        "fallback_triggered": True,
        "payload_queued": bool(payload),
        "fallback_response": fallback,
        "triggered_at": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------
_TOOLS = [
    {
        "name": "call_api",
        "description": "Make an HTTP request to an internal or external API endpoint.",
        "input_schema": {
            "type": "object",
            "properties": {
                "endpoint": {"type": "string", "description": "Full URL endpoint to call"},
                "method": {"type": "string", "description": "HTTP method: GET, POST, PUT, DELETE, PATCH"},
                "payload": {"type": "object", "description": "Request body payload (for POST/PUT/PATCH)"},
            },
            "required": ["endpoint", "method"],
        },
    },
    {
        "name": "check_api_health",
        "description": "Check the health status and latency of a registered internal service.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Service name from the registry (e.g. payment_service)"},
            },
            "required": ["service_name"],
        },
    },
    {
        "name": "log_api_event",
        "description": "Log an API interaction event for audit, monitoring, or debugging.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {"type": "string", "description": "Service name"},
                "event_type": {"type": "string", "description": "Event type (e.g. success, error, timeout, fallback)"},
                "details": {"type": "string", "description": "Event details or error message"},
            },
            "required": ["service", "event_type", "details"],
        },
    },
    {
        "name": "trigger_fallback",
        "description": "Trigger a pre-configured fallback response when a service is unavailable.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Name of the degraded service"},
                "payload": {"type": "object", "description": "Original request payload to queue for retry"},
            },
            "required": ["service_name", "payload"],
        },
    },
]

_SYSTEM_PROMPT = """You are an API Gateway Agent managing integrations between enterprise services.
Your responsibilities:
1. Route and execute API calls to internal and external services
2. Monitor service health before routing requests
3. Log all API events for observability and audit compliance
4. Trigger fallback mechanisms when services are degraded or unavailable

Always check service health before routing high-volume requests. Log errors and fallback triggers.
Retry degraded services a maximum of 2 times before triggering fallback."""


class ApiGatewayAgent(BaseERPAgent):
    """Manages API routing, health monitoring, event logging, and fallback handling."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "call_api":
                return _call_api(**inputs)
            case "check_api_health":
                return _check_api_health(**inputs)
            case "log_api_event":
                return _log_api_event(**inputs)
            case "trigger_fallback":
                return _trigger_fallback(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
