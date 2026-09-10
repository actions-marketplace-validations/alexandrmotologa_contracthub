"""Webhook Notification Dispatcher.

Delivers HTTP webhook callbacks signed with HMAC-SHA256 upon schema lifecycle events.
"""

import hashlib
import hmac
import json
from typing import Any

import httpx
from sqlalchemy.orm import Session

from contracthub.storage.database import WebhookModel


class WebhookDispatcher:
    """Dispatches asynchronous or background webhook calls for registry events."""

    @classmethod
    def calculate_signature(cls, secret: str, payload_bytes: bytes) -> str:
        sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
        return f"sha256={sig}"

    @classmethod
    def dispatch(
        cls,
        db: Session,
        event_name: str,
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        # Query active webhooks
        webhooks = db.query(WebhookModel).filter(WebhookModel.is_active.is_(True)).all()

        results = []
        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")

        for wh in webhooks:
            # Check if webhook subscribes to this event
            subscribed_events = [e.strip() for e in wh.events.split(",") if e.strip()]
            if event_name not in subscribed_events and "*" not in subscribed_events:
                continue

            headers = {
                "Content-Type": "application/json",
                "X-ContractHub-Event": event_name,
            }
            if wh.secret:
                headers["X-ContractHub-Signature"] = cls.calculate_signature(
                    wh.secret,
                    payload_bytes,
                )

            try:
                with httpx.Client(timeout=5.0) as client:
                    resp = client.post(wh.url, content=payload_bytes, headers=headers)
                    results.append(
                        {
                            "webhook_id": wh.id,
                            "url": wh.url,
                            "status_code": resp.status_code,
                            "success": 200 <= resp.status_code < 300,
                        }
                    )
            except (httpx.HTTPError, OSError) as exc:
                results.append(
                    {
                        "webhook_id": wh.id,
                        "url": wh.url,
                        "error": str(exc),
                        "success": False,
                    }
                )

        return results
