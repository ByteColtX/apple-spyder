from __future__ import annotations

import logging

import requests

from apple_spyder.settings import get_weibo_config


logger = logging.getLogger("weibo")

class Weibo:
    def __init__(self):
        config = get_weibo_config()
        self.enabled = config.enabled
        self.access_token = config.access_token
        self.redirect_uri = config.redirect_uri
        self.real_ip = config.real_ip

    def post_weibo(self, message: str) -> bool:
        if not self.enabled:
            logger.warning("Weibo posting feature is DISABLED.")
            return False

        response = requests.post(
            "https://api.weibo.com/2/statuses/share.json",
            data={
                "access_token": self.access_token,
                "status": message,
                "rip": self.real_ip,
            },
            timeout=30,
        )
        response.raise_for_status()
        logger.info("Weibo post succeeded: message_length=%s", len(message))
        return True
