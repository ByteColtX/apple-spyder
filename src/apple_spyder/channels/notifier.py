from __future__ import annotations

import logging
from collections.abc import Sequence

import requests

from apple_spyder.channels.bark import Bark
from apple_spyder.channels.telegram import Telegram
from apple_spyder.channels.weibo import Weibo


logger = logging.getLogger("notifier")


class Notifier:
    def __init__(self) -> None:
        self.telegram = Telegram()
        self.weibo = Weibo()
        self.bark = Bark()

    def _log_failure(self, channel: str, action: str, exc: Exception) -> None:
        if isinstance(exc, requests.HTTPError) and exc.response is not None:
            logger.error("%s %s failed: %s %s", channel, action, exc.response.status_code, exc.response.reason)
            return
        logger.error("%s %s failed: %s", channel, action, exc)

    def send_message(
        self,
        message: str,
        *,
        telegram_chat_ids: Sequence[str] | None = None,
        parse_in_markdown: bool = False,
        weibo_message: str | None = None,
    ) -> None:
        telegram_status = "disabled"
        weibo_status = "disabled"
        bark_status = "disabled"
        telegram_target_count = len(tuple(telegram_chat_ids)) if telegram_chat_ids is not None else len(self.telegram.chat_ids)

        try:
            telegram_status = (
                "sent"
                if self.telegram.send_message(
                    message,
                    chat_ids=telegram_chat_ids,
                    parse_in_markdown=parse_in_markdown,
                )
                else "disabled"
            )
        except Exception as exc:
            telegram_status = "failed"
            self._log_failure("Telegram", "send", exc)

        try:
            weibo_status = "sent" if self.weibo.post_weibo(weibo_message or message) else "disabled"
        except Exception as exc:
            weibo_status = "failed"
            self._log_failure("Weibo", "post", exc)

        try:
            bark_status = "sent" if self.bark.send_message(message) else "disabled"
        except Exception as exc:
            bark_status = "failed"
            self._log_failure("Bark", "send", exc)

        logger.info(
            "Notifier finished: telegram_status=%s telegram_target_count=%s weibo_status=%s bark_status=%s message_length=%s",
            telegram_status,
            telegram_target_count,
            weibo_status,
            bark_status,
            len(message),
        )
