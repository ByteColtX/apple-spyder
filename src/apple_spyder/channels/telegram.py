from __future__ import annotations

import logging
from collections.abc import Sequence

import requests

from apple_spyder.settings import get_telegram_config


logger = logging.getLogger("telegram")

class Telegram:
    def __init__(self):
        config = get_telegram_config()
        self.enabled = config.enabled
        self.bot_token = config.bot_token
        self.chat_ids = config.chat_ids

    def send_message(
        self,
        message: str,
        chat_id: str | None = None,
        *,
        chat_ids: Sequence[str] | None = None,
        parse_in_markdown: bool = False,
    ) -> bool:
        if not self.enabled:
            logger.warning("Telegram posting feature is DISABLED.")
            return False

        target_chat_ids = self._resolve_target_chat_ids(chat_id=chat_id, chat_ids=chat_ids)
        any_sent = False
        for target_chat_id in target_chat_ids:
            self._send_to_one_chat(target_chat_id=target_chat_id, message=message, parse_in_markdown=parse_in_markdown)
            any_sent = True

        logger.info("Telegram broadcast finished: chat_count=%s message_length=%s", len(target_chat_ids), len(message))
        return any_sent

    def _resolve_target_chat_ids(self, *, chat_id: str | None, chat_ids: Sequence[str] | None) -> tuple[str, ...]:
        if chat_ids:
            return tuple(str(item) for item in chat_ids)
        if chat_id is not None:
            return (str(chat_id),)
        return self.chat_ids

    def _send_to_one_chat(self, *, target_chat_id: str, message: str, parse_in_markdown: bool) -> None:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": target_chat_id,
            "text": message,
        }
        if parse_in_markdown:
            payload["parse_mode"] = "Markdown"

        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        logger.info("Telegram send succeeded: chat_id=%s message_length=%s", target_chat_id, len(message))
