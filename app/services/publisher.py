import json
from datetime import datetime
from decimal import Decimal

import redis

from app.core.config import get_settings


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


class LedgerPublisher:
    def __init__(self, redis_client: redis.Redis | None = None) -> None:
        settings = get_settings()
        self._redis = redis_client or redis.from_url(settings.redis_url)
        self._channel = settings.redis_pubsub_channel

    def publish_balance_update(
        self,
        merchant_id: str,
        balance: Decimal,
        currency: str,
        transaction_id: str,
        amount: Decimal,
        event_id: str,
    ) -> None:
        message = json.dumps(
            {
                "type": "balance_update",
                "merchant_id": merchant_id,
                "balance": balance,
                "currency": currency,
                "transaction": {
                    "transaction_id": transaction_id,
                    "amount": amount,
                    "event_id": event_id,
                },
                "timestamp": datetime.utcnow().isoformat(),
            },
            cls=DecimalEncoder,
        )
        self._redis.publish(self._channel, message)
