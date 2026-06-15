"""Tests for observability — JSON logging and tracing."""

import json
import logging
import time
from io import StringIO
from unittest.mock import MagicMock

import pytest

from agentic_erp.observability.logging import ERPLogger, JsonFormatter, get_logger
from agentic_erp.observability.tracing import Span, Tracer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_logger(name):
    log = logging.getLogger(name)
    log.handlers.clear()
    buf = StringIO()
    h = logging.StreamHandler(buf)
    h.setFormatter(JsonFormatter())
    log.addHandler(h)
    log.setLevel(logging.DEBUG)
    log.propagate = False
    return log, buf


# ---------------------------------------------------------------------------
# TestJsonFormatter
# ---------------------------------------------------------------------------


class TestJsonFormatter:
    def test_output_is_valid_json(self):
        log, buf = _make_logger("jf.valid_json")
        log.info("hello world")
        output = buf.getvalue().strip()
        # Should not raise
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_contains_required_fields(self):
        log, buf = _make_logger("jf.required_fields")
        log.info("check fields")
        parsed = json.loads(buf.getvalue().strip())
        for field in ("ts", "level", "logger", "msg"):
            assert field in parsed, f"Missing required field: {field}"

    def test_level_name_correct(self):
        log, buf = _make_logger("jf.level_name")
        log.info("info message")
        parsed = json.loads(buf.getvalue().strip())
        assert parsed["level"] == "INFO"

    def test_extra_fields_included(self):
        log, buf = _make_logger("jf.extra_fields")
        log.info("test", extra={"agent": "myagent"})
        parsed = json.loads(buf.getvalue().strip())
        assert parsed["agent"] == "myagent"

    def test_exception_info_captured(self):
        log, buf = _make_logger("jf.exception_info")
        try:
            raise ValueError("boom")
        except ValueError:
            log.error("caught error", exc_info=True)
        output = buf.getvalue().strip()
        assert "exception" in output


# ---------------------------------------------------------------------------
# TestGetLogger
# ---------------------------------------------------------------------------


class TestGetLogger:
    def test_returns_logger_instance(self):
        result = get_logger("get_logger.instance_test")
        assert isinstance(result, logging.Logger)

    def test_no_duplicate_handlers_on_second_call(self):
        name = "get_logger.dedup_test"
        # Clear any existing state
        existing = logging.getLogger(name)
        existing.handlers.clear()

        get_logger(name)
        get_logger(name)
        logger = logging.getLogger(name)
        assert len(logger.handlers) == 1


# ---------------------------------------------------------------------------
# TestERPLogger
# ---------------------------------------------------------------------------


class TestERPLogger:
    def _make_erp(self):
        mock_log = MagicMock()
        erp = ERPLogger(mock_log)
        return erp, mock_log

    def test_agent_start_logs_info(self):
        erp, mock_log = self._make_erp()
        erp.agent_start("MyAgent", "task")
        mock_log.info.assert_called_once()
        call_args = mock_log.info.call_args
        # First positional arg is the message
        assert call_args[0][0] == "agent.start"
        # extra kwarg contains agent and task
        extra = call_args[1]["extra"]
        assert extra["agent"] == "MyAgent"
        assert extra["task"] == "task"

    def test_agent_end_logs_info(self):
        erp, mock_log = self._make_erp()
        erp.agent_end("MyAgent", 123.4)
        mock_log.info.assert_called_once()

    def test_tool_call_logs_info(self):
        erp, mock_log = self._make_erp()
        erp.tool_call("soql_query", {}, {}, 42.0)
        mock_log.info.assert_called_once()

    def test_http_request_uses_warning_for_4xx(self):
        erp, mock_log = self._make_erp()
        erp.http_request("GET", "https://x", 429, 10.0)
        mock_log.log.assert_called_once()
        level_arg = mock_log.log.call_args[0][0]
        assert level_arg == logging.WARNING

    def test_circuit_breaker_logs_warning(self):
        erp, mock_log = self._make_erp()
        erp.circuit_breaker_transition("sf", "closed", "open")
        mock_log.warning.assert_called_once()


# ---------------------------------------------------------------------------
# TestSpan
# ---------------------------------------------------------------------------


class TestSpan:
    def test_span_has_unique_span_id(self):
        s1 = Span(name="op1", trace_id="trace-a")
        s2 = Span(name="op2", trace_id="trace-a")
        assert s1.span_id != s2.span_id

    def test_duration_ms_none_before_finish(self):
        span = Span(name="op", trace_id="trace-x")
        assert span.duration_ms is None

    def test_duration_ms_positive_after_finish(self):
        span = Span(name="op", trace_id="trace-x")
        time.sleep(0.001)
        span.finish()
        assert span.duration_ms is not None
        assert span.duration_ms > 0

    def test_to_dict_has_required_keys(self):
        span = Span(name="op", trace_id="trace-x")
        span.finish()
        d = span.to_dict()
        for key in (
            "name",
            "trace_id",
            "span_id",
            "duration_ms",
            "status",
            "attributes",
        ):
            assert key in d, f"Missing key in to_dict(): {key}"


# ---------------------------------------------------------------------------
# TestTracer
# ---------------------------------------------------------------------------


class TestTracer:
    def test_start_trace_returns_hex_string(self):
        tracer = Tracer()
        trace_id = tracer.start_trace()
        assert len(trace_id) == 32
        int(trace_id, 16)  # raises ValueError if not hex

    def test_span_context_manager_records_span(self):
        tracer = Tracer()
        with tracer.span("op"):
            pass
        assert tracer.span_count == 1

    def test_span_attributes_stored(self):
        tracer = Tracer()
        with tracer.span("op", tool="echo"):
            pass
        spans = tracer.get_spans()
        assert spans[0].attributes["tool"] == "echo"

    def test_nested_spans_set_parent_id(self):
        tracer = Tracer()
        with tracer.span("outer") as outer:
            with tracer.span("inner") as inner:
                pass
        assert inner.parent_id == outer.span_id

    def test_span_status_ok_on_success(self):
        tracer = Tracer()
        with tracer.span("op"):
            pass
        spans = tracer.get_spans()
        assert spans[0].status == "ok"

    def test_span_status_error_on_exception(self):
        tracer = Tracer()
        with pytest.raises(RuntimeError):
            with tracer.span("op"):
                raise RuntimeError("oops")
        spans = tracer.get_spans()
        assert spans[0].status == "error"
        assert "error" in spans[0].attributes

    def test_clear_resets_spans(self):
        tracer = Tracer()
        with tracer.span("op1"):
            pass
        with tracer.span("op2"):
            pass
        assert tracer.span_count == 2
        tracer.clear()
        assert tracer.span_count == 0

    def test_export_json_is_valid_json(self):
        tracer = Tracer()
        with tracer.span("op", key="val"):
            pass
        exported = tracer.export_json()
        parsed = json.loads(exported)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
