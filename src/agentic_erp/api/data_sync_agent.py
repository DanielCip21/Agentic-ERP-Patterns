"""Pattern: Data sync agent — delta extraction, change application, conflict resolution, result logging."""

from __future__ import annotations

from typing import Any
from datetime import datetime

from agentic_erp.agents.base import BaseERPAgent

# ---------------------------------------------------------------------------
# Simulated backend data
# ---------------------------------------------------------------------------
_SYNC_DELTAS: dict[str, list[dict]] = {
    "salesforce": [
        {"record_id": "SF-001", "entity": "Contact", "operation": "update",
         "fields": {"email": "new@example.com", "phone": "555-1234"}},
        {"record_id": "SF-002", "entity": "Lead", "operation": "create",
         "fields": {"name": "New Lead", "company": "Startup Co"}},
    ],
    "dynamics365": [
        {"record_id": "D365-001", "entity": "Account", "operation": "update",
         "fields": {"annual_revenue": 500000, "employees": 120}},
    ],
}

_CONFLICT_STRATEGIES = ["source_wins", "target_wins", "latest_timestamp_wins", "manual_review"]
_SYNC_RESULTS: list[dict] = []


def _get_sync_delta(source_system: str, since_timestamp: str) -> dict[str, Any]:
    deltas = _SYNC_DELTAS.get(source_system)
    if deltas is None:
        return {"error": f"Source system '{source_system}' not found"}
    return {
        "source_system": source_system,
        "since_timestamp": since_timestamp,
        "changes": deltas,
        "total_changes": len(deltas),
        "retrieved_at": datetime.utcnow().isoformat(),
    }


def _apply_changes(target_system: str, changes: list[dict]) -> dict[str, Any]:
    applied = []
    failed = []
    for change in changes:
        record_id = change.get("record_id", "unknown")
        operation = change.get("operation", "unknown")
        # Simulate 95% success rate
        import random
        if random.random() > 0.05:
            applied.append({"record_id": record_id, "operation": operation, "status": "applied"})
        else:
            failed.append({"record_id": record_id, "operation": operation, "error": "Simulated write failure"})
    return {
        "target_system": target_system,
        "applied": len(applied),
        "failed": len(failed),
        "applied_records": applied,
        "failed_records": failed,
        "applied_at": datetime.utcnow().isoformat(),
    }


def _resolve_conflict(record_id: str, strategy: str) -> dict[str, Any]:
    if strategy not in _CONFLICT_STRATEGIES:
        return {"error": f"Invalid strategy '{strategy}'. Valid: {_CONFLICT_STRATEGIES}"}
    return {
        "record_id": record_id,
        "strategy_applied": strategy,
        "resolution": f"Record {record_id} resolved using '{strategy}' strategy",
        "resolved_at": datetime.utcnow().isoformat(),
    }


def _log_sync_result(source: str, target: str, stats: dict) -> dict[str, Any]:
    result = {
        "sync_id": f"SYNC-{len(_SYNC_RESULTS) + 1:05d}",
        "source": source,
        "target": target,
        "stats": stats,
        "logged_at": datetime.utcnow().isoformat(),
    }
    _SYNC_RESULTS.append(result)
    return result


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------
_TOOLS = [
    {
        "name": "get_sync_delta",
        "description": "Retrieve changed records from a source system since a given timestamp.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source_system": {"type": "string", "description": "Source system name (e.g. salesforce, dynamics365)"},
                "since_timestamp": {"type": "string", "description": "ISO 8601 timestamp — only return changes after this time"},
            },
            "required": ["source_system", "since_timestamp"],
        },
    },
    {
        "name": "apply_changes",
        "description": "Apply a list of change records to a target system.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_system": {"type": "string", "description": "Target system name"},
                "changes": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of change records to apply",
                },
            },
            "required": ["target_system", "changes"],
        },
    },
    {
        "name": "resolve_conflict",
        "description": "Resolve a data conflict for a specific record using a chosen strategy.",
        "input_schema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string", "description": "Record ID with a conflict"},
                "strategy": {"type": "string", "description": "Conflict resolution strategy: source_wins, target_wins, latest_timestamp_wins, manual_review"},
            },
            "required": ["record_id", "strategy"],
        },
    },
    {
        "name": "log_sync_result",
        "description": "Log the outcome of a sync operation with statistics for audit purposes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Source system name"},
                "target": {"type": "string", "description": "Target system name"},
                "stats": {"type": "object", "description": "Sync statistics dict (applied, failed, conflicts, etc.)"},
            },
            "required": ["source", "target", "stats"],
        },
    },
]

_SYSTEM_PROMPT = """You are a Data Synchronisation Agent managing bi-directional sync between enterprise systems.
Your responsibilities:
1. Extract change deltas from source systems using incremental timestamps
2. Apply changes to target systems while handling errors gracefully
3. Resolve data conflicts using configurable strategies
4. Log all sync operations with detailed statistics for audit and replay

Failed records must be logged with error details. Conflicts must be resolved before retrying.
Prefer 'latest_timestamp_wins' for most entities; escalate to 'manual_review' for financial records."""


class DataSyncAgent(BaseERPAgent):
    """Synchronises data between enterprise systems with conflict resolution."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "get_sync_delta":
                return _get_sync_delta(**inputs)
            case "apply_changes":
                return _apply_changes(**inputs)
            case "resolve_conflict":
                return _resolve_conflict(**inputs)
            case "log_sync_result":
                return _log_sync_result(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
