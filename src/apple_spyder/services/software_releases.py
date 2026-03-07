from __future__ import annotations

import logging
import re
from typing import Any

from apple_spyder.channels.apple_rss import AppleDeveloperRssChannel
from apple_spyder.channels.notifier import Notifier
from apple_spyder.repositories.software_release_repository import SoftwareReleaseRepository
from apple_spyder.utils.time_utils import is_a_previous_time

_DEFAULT_LAST_UPDATE_TIME = "Thu, 01 Jan 1970 00:00:00 UTC"
_SOFTWARE_RELEASE_KEYWORDS = ["iOS", "iPadOS", "watchOS", "tvOS", "macOS", "visionOS", "Xcode"]
_BETA_KEYWORDS = ["RC", "Release Candidate", "beta"]
_SOFTWARE_RELEASE_PATTERN = re.compile(r"\b(" + "|".join(_SOFTWARE_RELEASE_KEYWORDS) + r")\b")
_BETA_RELEASE_PATTERN = re.compile(r"\b(" + "|".join(_BETA_KEYWORDS) + r")\b", flags=re.IGNORECASE)


logger = logging.getLogger("software_releases")

def _collect_release_titles(entries: list[object], last_feed_update_time: str) -> tuple[list[str], list[str]]:
    beta_release: list[str] = []
    prod_release: list[str] = []

    for entry in entries:
        published = getattr(entry, "published", None)
        title = getattr(entry, "title", None)
        if not published or not title:
            continue
        if not is_a_previous_time(last_feed_update_time, published):
            continue
        if not _SOFTWARE_RELEASE_PATTERN.search(title):
            continue
        if _BETA_RELEASE_PATTERN.search(title):
            beta_release.append(title)
            logger.info("Append a BETA release item: %s", title)
        else:
            prod_release.append(title)
            logger.info("Append a PROD release item: %s", title)

    return beta_release, prod_release


def _notify_releases(notifier: Notifier, beta_release: list[str], prod_release: list[str]) -> int:
    sent_count = 0

    if beta_release:
        beta_release_message = "🧪 Apple 发布 [测试版] 软件更新\n\n * " + "\n * ".join(beta_release)
        logger.info(beta_release_message)
        notifier.send_message(beta_release_message)
        sent_count += 1

    if prod_release:
        prod_release_message = "📲 Apple 发布 [正式版] 软件更新\n\n * " + "\n * ".join(prod_release)
        logger.info(prod_release_message)
        notifier.send_message(prod_release_message)
        sent_count += 1

    return sent_count


def main() -> dict[str, Any]:
    rss_channel = AppleDeveloperRssChannel()
    notifier = Notifier()
    repository = SoftwareReleaseRepository()

    try:
        rss_feed = rss_channel.fetch_feed()
        entries = list(getattr(rss_feed, "entries", []) or [])
        if not entries:
            raise RuntimeError("RSS feed has no entries")

        feed_publish_time = getattr(rss_feed.feed, "updated", None) or getattr(entries[0], "published", None)
        if not feed_publish_time:
            raise RuntimeError("RSS feed updated time not found")

        logger.info("Feed Update time: %s", feed_publish_time)

        last_feed_update_time = repository.get_last_feed_update_time()
        if not last_feed_update_time:
            last_feed_update_time = _DEFAULT_LAST_UPDATE_TIME
            logger.warning("last_feed_update_time is empty in database, set timestamp to: %s", last_feed_update_time)

        beta_release: list[str] = []
        prod_release: list[str] = []
        has_update = last_feed_update_time != feed_publish_time
        if has_update:
            beta_release, prod_release = _collect_release_titles(entries, last_feed_update_time)

        notification_count = _notify_releases(notifier, beta_release, prod_release)
        repository.update_feed_update_time(feed_publish_time)
        logger.info("Update feed publish time in database: %s", feed_publish_time)

        return {
            "feed_updated_at": feed_publish_time,
            "last_feed_updated_at": last_feed_update_time,
            "has_update": has_update,
            "entry_count": len(entries),
            "beta_titles": beta_release,
            "prod_titles": prod_release,
            "notification_count": notification_count,
        }
    finally:
        repository.close()
