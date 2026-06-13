"""Pattern: AI document intelligence agent — invoice extraction, validation, routing, flagging."""

from __future__ import annotations

from typing import Any
from datetime import datetime

from agentic_erp.agents.base import BaseERPAgent

# ---------------------------------------------------------------------------
# Simulated backend data
# ---------------------------------------------------------------------------
_DOCUMENTS: dict[str, dict] = {
    "DOC-001": {"id": "DOC-001", "type": "invoice", "filename": "inv_acme_jun2026.pdf", "status": "pending", "fields": None},
    "DOC-002": {"id": "DOC-002", "type": "purchase_order", "filename": "po_beta_q2.pdf", "status": "pending", "fields": None},
    "DOC-003": {"id": "DOC-003", "type": "invoice", "filename": "inv_gamma_may2026.pdf", "status": "pending", "fields": None},
}

_EXTRACTED_FIELDS: dict[str, dict] = {
    "DOC-001": {"vendor": "Acme Corp", "invoice_number": "INV-5501", "date": "2026-06-01",
                "total": 4250.00, "line_items": 3, "currency": "USD", "confidence": 0.97},
    "DOC-002": {"po_number": "PO-8812", "buyer": "MyCo Ltd", "date": "2026-05-28",
                "total": 3800.00, "line_items": 5, "currency": "USD", "confidence": 0.91},
    "DOC-003": {"vendor": "Gamma Supplies", "invoice_number": "INV-GS-220", "date": "2026-05-15",
                "total": 1200.00, "line_items": 2, "currency": "USD", "confidence": 0.73},
}

_ROUTING_RULES: dict[str, str] = {
    "invoice": "accounts_payable",
    "purchase_order": "procurement",
    "contract": "legal",
    "receipt": "expense_management",
}

_FLAGS: list[dict] = []


def _extract_invoice_fields(document_id: str) -> dict[str, Any]:
    doc = _DOCUMENTS.get(document_id)
    if not doc:
        return {"error": f"Document {document_id} not found"}
    fields = _EXTRACTED_FIELDS.get(document_id, {"error": "Extraction model returned no fields"})
    _DOCUMENTS[document_id]["fields"] = fields
    _DOCUMENTS[document_id]["status"] = "extracted"
    return {"document_id": document_id, "document_type": doc["type"], "extracted_fields": fields,
            "extracted_at": datetime.utcnow().isoformat()}


def _validate_extracted_data(document_id: str, fields: dict) -> dict[str, Any]:
    doc = _DOCUMENTS.get(document_id)
    if not doc:
        return {"error": f"Document {document_id} not found"}
    required_for_invoice = {"vendor", "invoice_number", "date", "total"}
    missing = [f for f in required_for_invoice if f not in fields]
    is_valid = len(missing) == 0
    confidence = fields.get("confidence", 0.5)
    return {
        "document_id": document_id,
        "is_valid": is_valid,
        "missing_fields": missing,
        "confidence": confidence,
        "needs_manual_review": not is_valid or confidence < 0.8,
        "validated_at": datetime.utcnow().isoformat(),
    }


def _route_document(document_id: str, destination: str) -> dict[str, Any]:
    doc = _DOCUMENTS.get(document_id)
    if not doc:
        return {"error": f"Document {document_id} not found"}
    _DOCUMENTS[document_id]["status"] = "routed"
    _DOCUMENTS[document_id]["destination"] = destination
    return {"document_id": document_id, "routed_to": destination, "routed_at": datetime.utcnow().isoformat()}


def _flag_for_review(document_id: str, reason: str) -> dict[str, Any]:
    doc = _DOCUMENTS.get(document_id)
    if not doc:
        return {"error": f"Document {document_id} not found"}
    flag = {"document_id": document_id, "reason": reason, "flagged_at": datetime.utcnow().isoformat(), "status": "pending_review"}
    _FLAGS.append(flag)
    _DOCUMENTS[document_id]["status"] = "flagged"
    return flag


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------
_TOOLS = [
    {
        "name": "extract_invoice_fields",
        "description": "Run AI extraction to pull structured fields (vendor, date, total, line items) from a document.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "Document ID (e.g. DOC-001)"},
            },
            "required": ["document_id"],
        },
    },
    {
        "name": "validate_extracted_data",
        "description": "Validate extracted fields for completeness and confidence threshold.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "Document ID"},
                "fields": {"type": "object", "description": "Extracted fields dict to validate"},
            },
            "required": ["document_id", "fields"],
        },
    },
    {
        "name": "route_document",
        "description": "Route a validated document to its destination workflow queue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "Document ID"},
                "destination": {"type": "string", "description": "Target queue or department (e.g. accounts_payable)"},
            },
            "required": ["document_id", "destination"],
        },
    },
    {
        "name": "flag_for_review",
        "description": "Flag a document for manual human review with a reason.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "Document ID"},
                "reason": {"type": "string", "description": "Reason for flagging"},
            },
            "required": ["document_id", "reason"],
        },
    },
]

_SYSTEM_PROMPT = """You are a Document Intelligence Agent processing enterprise documents.
Your responsibilities:
1. Extract structured fields from invoices, POs, and receipts using AI models
2. Validate extracted data for completeness and confidence
3. Route validated documents to appropriate downstream workflows
4. Flag low-confidence or incomplete documents for manual review

Documents with extraction confidence < 0.8 or missing required fields must be flagged.
Always route successfully validated documents immediately after validation."""


class DocumentIntelligenceAgent(BaseERPAgent):
    """Extracts, validates, routes, and flags enterprise documents using AI."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "extract_invoice_fields":
                return _extract_invoice_fields(**inputs)
            case "validate_extracted_data":
                return _validate_extracted_data(**inputs)
            case "route_document":
                return _route_document(**inputs)
            case "flag_for_review":
                return _flag_for_review(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
