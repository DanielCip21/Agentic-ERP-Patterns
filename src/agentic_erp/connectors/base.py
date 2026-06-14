"""Base HTTP connector with retry logic, structured error handling, and GET caching."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

if TYPE_CHECKING:
    from agentic_erp.cache.response_cache import ResponseCache

logger = logging.getLogger(__name__)


class ConnectorError(RuntimeError):
    """Base error for all connector HTTP failures."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(ConnectorError):
    """Raised on HTTP 429 — caller should respect Retry-After."""


class NotFoundError(ConnectorError):
    """Raised on HTTP 404."""


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, ConnectorError) and exc.status_code in {500, 502, 503, 504}:
        return True
    if isinstance(exc, httpx.TransportError):
        return True
    return False


def retryable(func):
    """Decorator: retry transient failures up to 4 times with exponential back-off."""
    return retry(
        retry=retry_if_exception(_is_retryable),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=16),
        reraise=True,
    )(func)


class BaseHTTPConnector:
    """Shared HTTP plumbing for all ERP/CRM connectors.

    Subclasses must implement ``_auth_headers()`` and set ``_base_url``.
    Set ``self._cache = ResponseCache(...)`` on an instance to enable
    automatic GET-response caching (POST/PATCH/DELETE always bypass the cache).
    """

    _base_url: str = ""
    _timeout: float = 30.0
    _cache: "ResponseCache | None" = None

    def _auth_headers(self) -> dict[str, str]:
        raise NotImplementedError

    def _default_headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **self._auth_headers(),
        }

    @retryable
    def _get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        return self._request("GET", path, params=params)

    @retryable
    def _post(self, path: str, json: dict | None = None) -> dict[str, Any]:
        return self._request("POST", path, json=json)

    @retryable
    def _patch(self, path: str, json: dict | None = None) -> dict[str, Any]:
        return self._request("PATCH", path, json=json)

    @retryable
    def _delete(self, path: str) -> dict[str, Any]:
        return self._request("DELETE", path)

    def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json: dict | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}/{path.lstrip('/')}"
        logger.debug("%s %s params=%s", method, url, params)

        if method == "GET" and self._cache is not None:
            from agentic_erp.cache.response_cache import ResponseCache
            cache_key = ResponseCache.make_key("GET", url, params)
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug("cache hit: %s", cache_key)
                return cached

        response = httpx.request(
            method,
            url,
            headers=self._default_headers(),
            params=params,
            json=json,
            timeout=self._timeout,
        )
        result = self._handle_response(response)

        if method == "GET" and self._cache is not None:
            self._cache.set(cache_key, result)  # type: ignore[possibly-undefined]

        return result

    @staticmethod
    def _handle_response(response: httpx.Response) -> dict[str, Any]:
        if response.status_code == 204:
            return {"status": "no_content"}
        if response.status_code == 404:
            raise NotFoundError(f"Resource not found: {response.url}", status_code=404)
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "unknown")
            raise RateLimitError(
                f"Rate limited (Retry-After: {retry_after}s)", status_code=429
            )
        if response.status_code >= 400:
            raise ConnectorError(
                f"HTTP {response.status_code}: {response.text[:400]}",
                status_code=response.status_code,
            )
        if not response.content:
            return {}
        return response.json()
