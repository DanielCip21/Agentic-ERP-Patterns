"""Minimal HTTP API server exposing the Master ERP+CRM Orchestrator.

Endpoints:
  POST /run          - Run a natural-language task
  POST /reconcile    - Run full daily reconciliation
  POST /workflow     - Trigger an n8n workflow
  GET  /health       - Infrastructure health check
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from agentic_erp.patterns.master_orchestrator import MasterERPCRMOrchestrator

_orchestrator = MasterERPCRMOrchestrator(
    n8n_url=os.getenv("N8N_BASE_URL", "http://localhost:5678"),
    n8n_api_key=os.getenv("N8N_API_KEY", ""),
    uptime_kuma_url=os.getenv("UPTIME_KUMA_URL", "http://localhost:3001"),
    coolify_url=os.getenv("COOLIFY_URL", "http://localhost:8000"),
    coolify_token=os.getenv("COOLIFY_TOKEN", ""),
)


def _read_json(handler: "ERPHandler") -> dict:
    length = int(handler.headers.get("Content-Length", 0))
    body = handler.rfile.read(length) if length else b"{}"
    return json.loads(body)


def _send_json(handler: "ERPHandler", status: int, data: object) -> None:
    payload = json.dumps(data, default=str).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


class ERPHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # suppress default CLF logging
        pass

    def do_GET(self):
        if self.path == "/health":
            _send_json(self, 200, _orchestrator.infrastructure_health())
        else:
            _send_json(self, 404, {"error": "Not found"})

    def do_POST(self):
        body = _read_json(self)
        if self.path == "/run":
            task = body.get("task", "")
            if not task:
                _send_json(self, 400, {"error": "task is required"})
                return
            _send_json(self, 200, _orchestrator.run(task))
        elif self.path == "/reconcile":
            _send_json(self, 200, _orchestrator.run_daily_reconciliation())
        elif self.path == "/workflow":
            key = body.get("workflow")
            payload = body.get("payload", {})
            if not key:
                _send_json(self, 400, {"error": "workflow key is required"})
                return
            _send_json(self, 200, _orchestrator.trigger_workflow(key, payload))
        else:
            _send_json(self, 404, {"error": "Not found"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), ERPHandler)
    print(f"ERP+CRM API running on port {port}")
    server.serve_forever()
