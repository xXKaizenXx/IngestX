#!/usr/bin/env python3
"""Send a signed test webhook to a running IngestX instance."""

import argparse
import json
import time
import urllib.request

from app.core.security import compute_signature


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000/api/v1/ingest")
    parser.add_argument("--secret", default="whsec_test_change_in_production")
    args = parser.parse_args()

    payload = {
        "event_id": f"evt_demo_{int(time.time())}",
        "transaction_id": f"txn_demo_{int(time.time())}",
        "amount": "99.99",
        "currency": "ZAR",
        "status": "succeeded",
        "merchant_id": "merchant_demo",
        "customer_email": "demo@ingestx.local",
        "metadata": {"source": "send_test_webhook"},
    }

    body = json.dumps(payload).encode()
    ts = str(int(time.time()))
    sig = compute_signature(body, args.secret, ts)

    req = urllib.request.Request(
        args.url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Timestamp": ts,
            "X-Webhook-Signature": f"t={ts},v1={sig}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req) as resp:
        print(resp.status, resp.read().decode())


if __name__ == "__main__":
    main()
