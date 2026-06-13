"""Azure AD OAuth2 client-credentials token manager with in-memory caching."""

from __future__ import annotations

import time
from typing import ClassVar

import httpx


class AzureADTokenManager:
    """Fetches and caches Azure AD access tokens using the client_credentials flow.

    Tokens are cached per (tenant_id, client_id, scope) tuple and refreshed
    automatically 60 seconds before they expire.
    """

    _cache: ClassVar[dict[str, tuple[str, float]]] = {}

    AAD_TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    @classmethod
    def get_token(
        cls,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        scope: str,
    ) -> str:
        """Return a valid access token, fetching a new one only when necessary."""
        cache_key = f"{tenant_id}:{client_id}:{scope}"
        cached = cls._cache.get(cache_key)
        if cached:
            token, expiry = cached
            if time.monotonic() < expiry:
                return token

        token, expires_in = cls._fetch_token(tenant_id, client_id, client_secret, scope)
        # Cache with 60-second safety buffer
        cls._cache[cache_key] = (token, time.monotonic() + expires_in - 60)
        return token

    @classmethod
    def _fetch_token(
        cls,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        scope: str,
    ) -> tuple[str, int]:
        url = cls.AAD_TOKEN_URL.format(tenant_id=tenant_id)
        response = httpx.post(
            url,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": scope,
            },
            timeout=15,
        )
        if response.status_code != 200:
            raise AuthenticationError(
                f"AAD token fetch failed ({response.status_code}): {response.text}"
            )
        data = response.json()
        return data["access_token"], int(data["expires_in"])

    @classmethod
    def clear_cache(cls) -> None:
        cls._cache.clear()


class AuthenticationError(RuntimeError):
    """Raised when an OAuth2 token cannot be obtained."""
