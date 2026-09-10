"""Unit tests for Webhook Dispatcher and HMAC signatures."""

from contracthub.core.webhook_dispatcher import WebhookDispatcher


def test_calculate_signature():
    secret = "my_top_secret_token"
    payload = b'{"event":"VERSION_REGISTERED","subject":"order-events"}'
    sig = WebhookDispatcher.calculate_signature(secret, payload)
    assert sig.startswith("sha256=")
    assert len(sig) == 7 + 64  # 'sha256=' + 64 hex characters
