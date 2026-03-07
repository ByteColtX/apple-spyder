from __future__ import annotations

from apple_spyder.repositories.database import DatabaseUtil


class SoftwareReleaseRepository:
    def __init__(self, db: DatabaseUtil | None = None) -> None:
        self.db = db or DatabaseUtil()
        self._owns_db = db is None

    def get_last_feed_update_time(self) -> str | None:
        rows = self.db.db_select("SELECT update_time FROM apple_developer_rss WHERE id = ?", ("RSS_FEED_UPDATE_TIME",))
        return rows[0][0] if rows else None

    def update_feed_update_time(self, value: str) -> None:
        self.db.db_operate("UPDATE apple_developer_rss SET update_time = ? WHERE id = ?", (value, "RSS_FEED_UPDATE_TIME"))

    def close(self) -> None:
        if self._owns_db:
            self.db.close()
