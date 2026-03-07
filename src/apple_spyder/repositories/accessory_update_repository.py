from __future__ import annotations

from apple_spyder.repositories.database import DatabaseUtil


class AccessoryUpdateRepository:
    def __init__(self, db: DatabaseUtil | None = None) -> None:
        self.db = db or DatabaseUtil()
        self._owns_db = db is None

    def get_last_update_time(self, model: str) -> str | None:
        rows = self.db.db_select("SELECT update_time FROM accessory_ota_update WHERE model = ?", (model,))
        return rows[0][0] if rows else None

    def update_last_update_time(self, model: str, value: str) -> None:
        self.db.db_operate("UPDATE accessory_ota_update SET update_time = ? WHERE model = ?", (value, model))

    def close(self) -> None:
        if self._owns_db:
            self.db.close()
