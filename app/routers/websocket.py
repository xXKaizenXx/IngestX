import asyncio
import json

import redis.asyncio as aioredis
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.config import get_settings

router = APIRouter(prefix="/api/v1", tags=["stream"])


@router.websocket("/stream")
async def ledger_stream(
    websocket: WebSocket,
    token: str = Query(..., description="Bearer-style stream auth token"),
    merchant_id: str | None = Query(None, description="Filter updates to a merchant"),
) -> None:
    if token != get_settings().ws_auth_token:
        await websocket.close(code=1008, reason="Invalid stream token")
        return
    await websocket.accept()

    settings = get_settings()
    client = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = client.pubsub()
    await pubsub.subscribe(settings.redis_pubsub_channel)

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "message":
                data = json.loads(message["data"])
                if merchant_id and data.get("merchant_id") != merchant_id:
                    continue
                await websocket.send_json(data)
            await asyncio.sleep(0.01)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(settings.redis_pubsub_channel)
        await pubsub.close()
        await client.close()
