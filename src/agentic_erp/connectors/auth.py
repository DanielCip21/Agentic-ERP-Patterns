"""OAuth2 token managers for Azure AD and Salesforce with in-memory caching."""

from __future__ import annotations

import time
from typing import ClassVar

import httpx


# ---------------------------------------------------------------------------
# Azure AD — client_credentials grant
# Used by: Dynamics 365, Power Platform, Dataverse
# ---------------------------------------------------------------------------

class AzureADTokenManager:
    """Fetches and caches Azure AD access tokens (client_credentials flow).

    Tokens are cached per (tenant_id, client_id, scope) and refreshed
    60 seconds before expiry.
    """

    _cache: ClassVar[dict[str, tuple[str, float]]] = {}
    AAD_TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    @classmethod
    def get_token(
        cls, tenant_id: str, client_id: str, client_secret: str, scope: str
    ) -> str:
        cache_key = f"{tenant_id}:{client_id}:{scope}"
        cached = cls._cache.get(cache_key)
        if cached:
            token, expiry = cached
            if time.monotonic() < expiry:
                return token
        token, expires_in = cls._fetch(tenant_id, client_id, client_secret, scope)
        cls._cache[cache_key] = (token, time.monotonic() + expires_in - 60)
        return token

    @classmethod
    def _fetch(
        cls, tenant_id: str, client_id: str, client_secret: str, scope: str
    ) -> tuple[str, int]:
        url = cls.AAD_TOKEN_URL.format(tenant_id=tenant_id)
        resp = httpx.post(
            url,
            data={"grant_type": "client_credentials", "client_id": client_id,
                  "client_secret": client_secret, "scope": scope},
            timeout=15,
        )
        if resp.status_code != 200:
            raise AuthenticationError(f"AAD token fetch failed ({resp.status_code}): {resp.text}")
        data = resp.json()
        return data["access_token"], int(data["expires_in"])

    @classmethod
    def clear_cache(cls) -> None:
        cls._cache.clear()


# ---------------------------------------------------------------------------
# Salesforce — Connected App OAuth2 client_credentials grant
# ---------------------------------------------------------------------------

class SalesforceTokenManager:
    """Fetches and caches Salesforce OAuth2 tokens via Connected App.

    Supports the OAuth 2.0 client_credentials flow (available in API v51+).
    For orgs that can't use client_credentials, pass `access_token` directly
    in SalesforceConfig instead.
    """

    _cache: ClassVar[dict[str, tuple[str, float]]] = {}
    SF_TOKEN_URL = "{login_url}/services/oauth2/token"

    @classmethod
    def get_token(
        cls,
        client_id: str,
        client_secret: str,
        login_url: str = "https://login.salesforce.com",
    ) -> str:
        cache_key = f"{login_url}:{client_id}"
        cached = cls._cache.get(cache_key)
        if cached:
            token, expiry = cached
            if time.monotonic() < expiry:
                return token
        token, expires_in = cls._fetch(client_id, client_secret, login_url)
        cls._cache[cache_key] = (token, time.monotonic() + expires_in - 60)
        return token

    @classmethod
    def _fetch(
        cls, client_id: str, client_secret: str, login_url: str
    ) -> tuple[str, int]:
        url = cls.SF_TOKEN_URL.format(login_url=login_url)
        resp = httpx.post(
            url,
            data={"grant_type": "client_credentials", "client_id": client_id,
                  "client_secret": client_secret},
            timeout=15,
        )
        if resp.status_code != 200:
            raise AuthenticationError(
                f"Salesforce token fetch failed ({resp.status_code}): {resp.text}"
            )
        data = resp.json()
        # Salesforce doesn't always return expires_in; default 2 hours
        return data["access_token"], int(data.get("expires_in", 7200))

    @classmethod
    def clear_cache(cls) -> None:
        cls._cache.clear()


class AuthenticationError(RuntimeError):
    """Raised when an OAuth2 token cannot be obtained."""
