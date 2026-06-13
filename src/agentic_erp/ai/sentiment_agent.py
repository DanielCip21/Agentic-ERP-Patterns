"""Pattern: AI sentiment analysis agent — feedback batches, sentiment tagging, escalation."""

from __future__ import annotations

from typing import Any
from datetime import datetime

from agentic_erp.agents.base import BaseERPAgent

# ---------------------------------------------------------------------------
# Simulated backend data
# ---------------------------------------------------------------------------
_FEEDBACK_BATCHES: dict[str, list[dict]] = {
    "support_tickets": [
        {"id": "FB-001", "text": "The onboarding was seamless and the team was incredibly helpful!", "source": "support_tickets"},
        {"id": "FB-002", "text": "Waited 3 days for a response. Totally unacceptable service.", "source": "support_tickets"},
        {"id": "FB-003", "text": "Product works fine but documentation could be clearer.", "source": "support_tickets"},
    ],
    "nps_survey": [
        {"id": "FB-004", "text": "Love the new dashboard. Makes reporting so much easier.", "source": "nps_survey"},
        {"id": "FB-005", "text": "Integration broke after the last update. Lost 2 hours of work.", "source": "nps_survey"},
    ],
    "reviews": [
        {"id": "FB-006", "text": "Great value for money. Would recommend to any SMB.", "source": "reviews"},
    ],
}

_TAGGED_FEEDBACK: dict[str, dict] = {}
_ESCALATIONS: list[dict] = []


def _get_feedback_batch(source: str, limit: int = 10) -> dict[str, Any]:
    batch = _FEEDBACK_BATCHES.get(source)
    if batch is None:
        return {"error": f"Feedback source '{source}' not found. Available: {list(_FEEDBACK_BATCHES.keys())}"}
    return {"source": source, "feedback": batch[:limit], "total": len(batch)}


def _analyze_sentiment(text: str) -> dict[str, Any]:
    text_lower = text.lower()
    positive_words = {"great", "love", "excellent", "helpful", "seamless", "easy", "good", "recommend", "faster", "amazing"}
    negative_words = {"unacceptable", "broke", "lost", "waited", "terrible", "awful", "broken", "issue", "problem", "bad"}
    pos = sum(1 for w in positive_words if w in text_lower)
    neg = sum(1 for w in negative_words if w in text_lower)
    if neg > pos:
        sentiment = "negative"
        score = -min(neg * 0.3, 1.0)
    elif pos > neg:
        sentiment = "positive"
        score = min(pos * 0.3, 1.0)
    else:
        sentiment = "neutral"
        score = 0.0
    return {"text": text[:100], "sentiment": sentiment, "score": round(score, 2), "analyzed_at": datetime.utcnow().isoformat()}


def _tag_feedback(feedback_id: str, tags: list[str]) -> dict[str, Any]:
    _TAGGED_FEEDBACK[feedback_id] = {"feedback_id": feedback_id, "tags": tags, "tagged_at": datetime.utcnow().isoformat()}
    return _TAGGED_FEEDBACK[feedback_id]


def _escalate_negative_feedback(feedback_id: str, priority: str) -> dict[str, Any]:
    valid_priorities = {"low", "medium", "high", "critical"}
    if priority not in valid_priorities:
        return {"error": f"Invalid priority '{priority}'. Valid: {valid_priorities}"}
    escalation = {
        "escalation_id": f"ESC-{len(_ESCALATIONS) + 1:04d}",
        "feedback_id": feedback_id,
        "priority": priority,
        "escalated_to": "customer_success_team" if priority in {"low", "medium"} else "vp_customer_success",
        "escalated_at": datetime.utcnow().isoformat(),
        "status": "open",
    }
    _ESCALATIONS.append(escalation)
    return escalation


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------
_TOOLS = [
    {
        "name": "get_feedback_batch",
        "description": "Retrieve a batch of customer feedback from a given source.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Feedback source (e.g. support_tickets, nps_survey, reviews)"},
                "limit": {"type": "integer", "description": "Maximum number of feedback items to return (default 10)"},
            },
            "required": ["source"],
        },
    },
    {
        "name": "analyze_sentiment",
        "description": "Analyse the sentiment of a given text string and return sentiment label and score.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Feedback text to analyse"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "tag_feedback",
        "description": "Attach classification tags to a feedback item (e.g. product_bug, onboarding, billing).",
        "input_schema": {
            "type": "object",
            "properties": {
                "feedback_id": {"type": "string", "description": "Feedback item ID"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "List of tags to apply"},
            },
            "required": ["feedback_id", "tags"],
        },
    },
    {
        "name": "escalate_negative_feedback",
        "description": "Escalate a negative feedback item to the customer success team with a priority level.",
        "input_schema": {
            "type": "object",
            "properties": {
                "feedback_id": {"type": "string", "description": "Feedback ID to escalate"},
                "priority": {"type": "string", "description": "Priority level: low, medium, high, or critical"},
            },
            "required": ["feedback_id", "priority"],
        },
    },
]

_SYSTEM_PROMPT = """You are a Customer Sentiment Analysis Agent for an enterprise platform.
Your responsibilities:
1. Retrieve feedback batches from various sources (support tickets, NPS surveys, reviews)
2. Analyse the sentiment of each feedback item
3. Tag feedback with relevant categories for product and operations teams
4. Escalate highly negative feedback immediately with appropriate priority

Escalate critical or highly negative feedback (score <= -0.6) with high/critical priority.
Always tag feedback before escalation to ensure proper routing."""


class SentimentAgent(BaseERPAgent):
    """Analyses customer feedback sentiment, tags items, and escalates negative signals."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "get_feedback_batch":
                return _get_feedback_batch(**inputs)
            case "analyze_sentiment":
                return _analyze_sentiment(**inputs)
            case "tag_feedback":
                return _tag_feedback(**inputs)
            case "escalate_negative_feedback":
                return _escalate_negative_feedback(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
