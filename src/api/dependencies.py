from __future__ import annotations

from fastapi import Header, HTTPException, Request, status

from src.core import config
from src.core.bootstrap import BotContext


def get_bot_context(request: Request) -> BotContext:
    context = getattr(request.app.state, "bot_context", None)
    if context is None:
        raise RuntimeError("Bot context is not initialised. Check startup sequence.")
    return context


def require_bearer_token(authorization: str | None = Header(default=None)) -> None:
    expected = config.OAUTH_CALLBACK_ROUTE_BEARER_TOKEN
    if not expected:
        return

    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization scheme")

    if token.strip() != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid bearer token")


__all__ = ["get_bot_context", "require_bearer_token"]
