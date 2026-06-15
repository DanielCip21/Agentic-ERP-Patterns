"""API-key authentication middleware.

Any path not in ``exempt_paths`` requires the ``X-API-Key`` header to match
the configured secret.  The health endpoint is always exempt so load-balancers
and monitoring tools can probe it without credentials.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# Paths that skip auth checks (documentation + health).
_DEFAULT_EXEMPT: frozenset[str] = frozenset({
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/docs/oauth2-redirect",
})


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Reject requests without a valid ``X-API-Key`` header.

    Parameters
    ----------
    api_key:
        The expected secret value.  All non-exempt routes return HTTP 401
        when the header is absent or does not match.
    exempt_paths:
        Paths that bypass auth.  Defaults to docs + health.
    """

    def __init__(
        self,
        app,
        api_key: str,
        exempt_paths: frozenset[str] = _DEFAULT_EXEMPT,
    ) -> None:
        super().__init__(app)
        self._api_key = api_key
        self._exempt_paths = exempt_paths

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self._exempt_paths:
            return await call_next(request)

        provided = request.headers.get("X-API-Key")
        if provided != self._api_key:
            return JSONResponse(
                {"detail": "Invalid or missing API key."},
                status_code=401,
                headers={"WWW-Authenticate": 'ApiKey realm="Agentic ERP API"'},
            )
        return await call_next(request)
