import hashlib
import hmac
import time
from typing import Annotated

from fastapi import Header, HTTPException, Request, status

from app.core.config import get_settings


def compute_signature(payload: bytes, secret: str, timestamp: str) -> str:
    """Stripe-style HMAC-SHA256 over ``{timestamp}.{body}``."""
    signed = f"{timestamp}.".encode() + payload
    return hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()


def verify_webhook_signature(
    payload: bytes,
    signature_header: str | None,
    timestamp_header: str | None,
) -> None:
    if not signature_header or not timestamp_header:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Missing signature headers")

    try:
        ts = int(timestamp_header)
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid timestamp") from exc

    if abs(time.time() - ts) > 300:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Timestamp outside tolerance window",
        )

    settings = get_settings()
    expected = compute_signature(payload, settings.webhook_secret, timestamp_header)

    # Header format: t=<ts>,v1=<hex>
    provided = signature_header.split(",")[-1].removeprefix("v1=")
    if not hmac.compare_digest(expected, provided):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")


async def require_webhook_signature(
    request: Request,
    x_webhook_signature: Annotated[str | None, Header(alias="X-Webhook-Signature")] = None,
    x_webhook_timestamp: Annotated[str | None, Header(alias="X-Webhook-Timestamp")] = None,
) -> bytes:
    body = await request.body()
    verify_webhook_signature(body, x_webhook_signature, x_webhook_timestamp)
    return body


def verify_ws_token(token: str | None) -> None:
    if not token or token != get_settings().ws_auth_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid stream token")
