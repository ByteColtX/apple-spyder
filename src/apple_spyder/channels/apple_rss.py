from __future__ import annotations

import fastfeedparser

from apple_spyder.settings import get_urls_config


class AppleDeveloperRssChannel:
    def fetch_feed(self):
        config = get_urls_config()
        return fastfeedparser.parse(config.apple_developer_rss)
