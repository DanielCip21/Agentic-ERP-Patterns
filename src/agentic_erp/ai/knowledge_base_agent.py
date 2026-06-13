"""Pattern: AI knowledge base agent — search, retrieval, authoring, and lifecycle management."""

from __future__ import annotations

from typing import Any
from datetime import datetime

from agentic_erp.agents.base import BaseERPAgent

# ---------------------------------------------------------------------------
# Simulated backend data
# ---------------------------------------------------------------------------
_ARTICLES: dict[str, dict] = {
    "ART-001": {
        "id": "ART-001", "title": "How to Reset Your Password",
        "content": "Navigate to the login page and click 'Forgot Password'. Enter your email address...",
        "tags": ["auth", "account", "password"], "status": "active",
        "created_at": "2025-01-10T09:00:00", "views": 1240,
    },
    "ART-002": {
        "id": "ART-002", "title": "Configuring SSO with Azure AD",
        "content": "Single Sign-On requires an Enterprise plan. Go to Settings > Security > SSO...",
        "tags": ["sso", "azure", "security", "enterprise"], "status": "active",
        "created_at": "2025-03-15T14:00:00", "views": 430,
    },
    "ART-003": {
        "id": "ART-003", "title": "Importing Data via CSV (Legacy)",
        "content": "Use the legacy import tool under Admin > Data. Note: this feature is deprecated...",
        "tags": ["import", "csv", "data", "deprecated"], "status": "active",
        "created_at": "2024-06-01T10:00:00", "views": 88,
    },
}

_ARTICLE_COUNTER = len(_ARTICLES)


def _search_knowledge_base(query: str, top_k: int = 5) -> dict[str, Any]:
    query_lower = query.lower()
    scored = []
    for art in _ARTICLES.values():
        if art["status"] == "outdated":
            continue
        score = 0
        for word in query_lower.split():
            if word in art["title"].lower():
                score += 3
            if word in art["content"].lower():
                score += 1
            if word in [t.lower() for t in art["tags"]]:
                score += 2
        if score > 0:
            scored.append({"article_id": art["id"], "title": art["title"], "relevance_score": score, "tags": art["tags"]})
    scored.sort(key=lambda x: x["relevance_score"], reverse=True)
    return {"query": query, "results": scored[:top_k], "total_found": len(scored)}


def _get_article(article_id: str) -> dict[str, Any]:
    art = _ARTICLES.get(article_id)
    if not art:
        return {"error": f"Article {article_id} not found"}
    art["views"] += 1
    return art


def _create_article(title: str, content: str, tags: list[str]) -> dict[str, Any]:
    global _ARTICLE_COUNTER
    _ARTICLE_COUNTER += 1
    art_id = f"ART-{_ARTICLE_COUNTER:03d}"
    article = {
        "id": art_id, "title": title, "content": content, "tags": tags,
        "status": "active", "created_at": datetime.utcnow().isoformat(), "views": 0,
    }
    _ARTICLES[art_id] = article
    return article


def _mark_article_outdated(article_id: str) -> dict[str, Any]:
    art = _ARTICLES.get(article_id)
    if not art:
        return {"error": f"Article {article_id} not found"}
    art["status"] = "outdated"
    art["marked_outdated_at"] = datetime.utcnow().isoformat()
    return {"article_id": article_id, "title": art["title"], "status": "outdated",
            "marked_outdated_at": art["marked_outdated_at"]}


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------
_TOOLS = [
    {
        "name": "search_knowledge_base",
        "description": "Search the knowledge base for articles relevant to a query string.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "top_k": {"type": "integer", "description": "Maximum number of results to return (default 5)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_article",
        "description": "Retrieve the full content of a specific knowledge base article.",
        "input_schema": {
            "type": "object",
            "properties": {
                "article_id": {"type": "string", "description": "Article ID (e.g. ART-001)"},
            },
            "required": ["article_id"],
        },
    },
    {
        "name": "create_article",
        "description": "Create a new knowledge base article with title, content, and tags.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Article title"},
                "content": {"type": "string", "description": "Full article content"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Classification tags"},
            },
            "required": ["title", "content", "tags"],
        },
    },
    {
        "name": "mark_article_outdated",
        "description": "Mark an existing article as outdated so it is excluded from search results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "article_id": {"type": "string", "description": "Article ID to mark outdated"},
            },
            "required": ["article_id"],
        },
    },
]

_SYSTEM_PROMPT = """You are a Knowledge Base Management Agent for an enterprise support platform.
Your responsibilities:
1. Search the knowledge base to find relevant existing articles before creating new ones
2. Retrieve full article content to check for accuracy and relevance
3. Create new articles when knowledge gaps are identified
4. Mark outdated articles so they are excluded from customer-facing search

Always search before creating to avoid duplicates. Mark deprecated feature articles as outdated.
Ensure new articles have at least 3 relevant tags for discoverability."""


class KnowledgeBaseAgent(BaseERPAgent):
    """Manages enterprise knowledge base — search, retrieval, authoring, lifecycle."""

    def __init__(self, **kwargs) -> None:
        super().__init__(tools=_TOOLS, system_prompt=_SYSTEM_PROMPT, **kwargs)

    def _dispatch_tool(self, name: str, inputs: dict[str, Any]) -> Any:
        match name:
            case "search_knowledge_base":
                return _search_knowledge_base(**inputs)
            case "get_article":
                return _get_article(**inputs)
            case "create_article":
                return _create_article(**inputs)
            case "mark_article_outdated":
                return _mark_article_outdated(**inputs)
            case _:
                return {"error": f"Unknown tool: {name}"}
