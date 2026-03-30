from __future__ import annotations

import apple_spyder.channels.notifier as notifier_module
from apple_spyder.channels.notifier import Notifier


class DummyTelegram:
    def __init__(self) -> None:
        self.chat_ids = ("10001", "10002")
        self.calls: list[dict[str, object]] = []

    def send_message(self, message, *, chat_ids=None, parse_in_markdown=False):
        self.calls.append(
            {
                "message": message,
                "chat_ids": chat_ids,
                "parse_in_markdown": parse_in_markdown,
            }
        )
        return True


class DummyWeibo:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def post_weibo(self, message: str) -> bool:
        self.calls.append(message)
        return True


class DummyBark:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def send_message(self, message: str, *, title: str = "Apple Spyder") -> bool:
        self.calls.append({"message": message, "title": title})
        return True


def test_notifier_sends_to_bark_too(monkeypatch):
    dummy_telegram = DummyTelegram()
    dummy_weibo = DummyWeibo()
    dummy_bark = DummyBark()
    monkeypatch.setattr(notifier_module, "Telegram", lambda: dummy_telegram)
    monkeypatch.setattr(notifier_module, "Weibo", lambda: dummy_weibo)
    monkeypatch.setattr(notifier_module, "Bark", lambda: dummy_bark)

    notifier = Notifier()
    notifier.send_message("hello world", parse_in_markdown=True, weibo_message="hello weibo")

    assert dummy_telegram.calls == [
        {
            "message": "hello world",
            "chat_ids": None,
            "parse_in_markdown": True,
        }
    ]
    assert dummy_weibo.calls == ["hello weibo"]
    assert dummy_bark.calls == [{"message": "hello world", "title": "Apple Spyder"}]
