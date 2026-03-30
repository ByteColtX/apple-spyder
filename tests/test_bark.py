from __future__ import annotations

import base64
from types import SimpleNamespace

import apple_spyder.channels.bark as bark_module
from apple_spyder.channels.bark import Bark


class DummyResponse:
    def raise_for_status(self) -> None:
        return None


def test_bark_send_message_posts_expected_payload(monkeypatch):
    config = SimpleNamespace(
        enabled=True,
        server_url="https://example.com/",
        device_key="device-key",
        username="admin",
        password="secret",
    )
    monkeypatch.setattr(bark_module, "get_bark_config", lambda: config)

    captured: dict[str, object] = {}

    def fake_post(url, *, json, headers, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return DummyResponse()

    monkeypatch.setattr(bark_module.requests, "post", fake_post)

    channel = Bark()
    sent = channel.send_message("hello bark", title="Notice")

    assert sent is True
    assert captured["url"] == "https://example.com/push"
    assert captured["json"] == {
        "device_key": "device-key",
        "title": "Notice",
        "body": "hello bark",
        "group": "Apple Release",
    }
    assert captured["headers"] == {
        "Authorization": f"Basic {base64.b64encode(b'admin:secret').decode('ascii')}",
        "Content-Type": "application/json",
    }
    assert captured["timeout"] == 30


def test_bark_send_message_returns_false_when_disabled(monkeypatch):
    config = SimpleNamespace(
        enabled=False,
        server_url="https://example.com",
        device_key="device-key",
        username="admin",
        password="secret",
    )
    monkeypatch.setattr(bark_module, "get_bark_config", lambda: config)

    called = False

    def fake_post(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("requests.post should not be called when bark is disabled")

    monkeypatch.setattr(bark_module.requests, "post", fake_post)

    channel = Bark()
    assert channel.send_message("hello bark") is False
    assert called is False
