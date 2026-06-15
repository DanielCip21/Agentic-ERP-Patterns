"""Structured JSON logging for ERP agents and connectors."""

from __future__ import annotations

import json
import logging
from typing import Any

_STANDARD_ATTRS = frozenset(
    {
        "args",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
    }
)


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON — machine-readable and grep-friendly."""

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        data: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.message,
        }
        for key, val in vars(record).items():
            if key not in _STANDARD_ATTRS:
                data[key] = val
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data, default=str)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a named logger with JSON formatting attached."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False
    return logger


class ERPLogger:
    """Structured log helper with ERP-specific event methods.

    Usage::

        from agentic_erp.observability.logging import ERPLogger, get_logger

        erp_log = ERPLogger(get_logger("my_agent"))
        erp_log.agent_start("SalesforceCRMAgent", "List open leads")
        erp_log.tool_call("soql_query", {"query": "SELECT Id FROM Lead"}, result={}, duration_ms=42.3)
        erp_log.agent_end("SalesforceCRMAgent", duration_ms=1234.5)
    """

    def __init__(self, logger: logging.Logger) -> None:
        self._log = logger

    def agent_start(self, agent: str, task: str) -> None:
        self._log.info("agent.start", extra={"agent": agent, "task": task[:200]})

    def agent_end(self, agent: str, duration_ms: float, status: str = "ok") -> None:
        self._log.info(
            "agent.end",
            extra={
                "agent": agent,
                "duration_ms": round(duration_ms, 2),
                "status": status,
            },
        )

    def tool_call(
        self, tool: str, inputs: dict, result: Any, duration_ms: float
    ) -> None:
        self._log.info(
            "tool.call",
            extra={"tool": tool, "duration_ms": round(duration_ms, 2)},
        )

    def http_request(
        self, method: str, url: str, status_code: int, duration_ms: float
    ) -> None:
        level = logging.WARNING if status_code >= 400 else logging.DEBUG
        self._log.log(
            level,
            "http.request",
            extra={
                "method": method,
                "url": url,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )

    def cache_event(self, event: str, key: str) -> None:
        """event: 'hit' | 'miss' | 'set' | 'invalidate'"""
        self._log.debug("cache.%s" % event, extra={"cache_key": key[:120]})

    def circuit_breaker_transition(
        self, platform: str, from_state: str, to_state: str
    ) -> None:
        self._log.warning(
            "circuit_breaker.transition",
            extra={
                "platform": platform,
                "from_state": from_state,
                "to_state": to_state,
            },
        )
