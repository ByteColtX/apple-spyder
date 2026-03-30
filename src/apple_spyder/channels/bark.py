from __future__ import annotations

import base64
import logging

import requests

from apple_spyder.settings import get_bark_config


logger = logging.getLogger("bark")
_GROUP = "Apple Release"


class Bark:
    def __init__(self) -> None:
        config = get_bark_config()
        self.enabled = config.enabled
        self.server_url = config.server_url.rstrip("/")
        self.device_key = config.device_key
        self.username = config.username
        self.password = config.password

    def send_message(self, message: str, *, title: str = "Apple Spyder") -> bool:
        if not self.enabled:
            logger.warning("Bark posting feature is DISABLED.")
            return False

        token = base64.b64encode(f"{self.username}:{self.password}".encode("utf-8")).decode("ascii")
        response = requests.post(
            f"{self.server_url}/push",
            json={
                "device_key": self.device_key,
                "title": title,
                "body": message,
                "group": _GROUP,
            },
            headers={
                "Authorization": f"Basic {token}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        response.raise_for_status()
        logger.info("Bark send succeeded: message_length=%s", len(message))
        return True
