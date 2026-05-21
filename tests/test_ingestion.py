from tests.conftest import signed_ingest_request


def test_ingest_returns_202(client, sample_event):
    body, headers = signed_ingest_request(sample_event)
    response = client.post("/api/v1/ingest", content=body, headers=headers)
    assert response.status_code == 202
    body = response.json()
    assert body["accepted"] is True
    assert body["event_id"] == sample_event["event_id"]


def test_ingest_rejects_invalid_signature(client, sample_event):
    response = client.post(
        "/api/v1/ingest",
        json=sample_event,
        headers={"X-Webhook-Signature": "bad", "X-Webhook-Timestamp": "123"},
    )
    assert response.status_code == 401


def test_ingest_rejects_malformed_payload(client):
    payload = {"event_id": "only_field"}
    body, headers = signed_ingest_request(payload)
    response = client.post("/api/v1/ingest", content=body, headers=headers)
    assert response.status_code == 422


def test_health_endpoint(client):
    assert client.get("/health").json()["status"] == "ok"
