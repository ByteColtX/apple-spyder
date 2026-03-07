from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from apple_spyder.settings import DATABASE_PATH


class DatabaseUtil:
    def __init__(self, db_path: Path | str = DATABASE_PATH):
        self.db_path = Path(db_path)
        self._ensure_database_initialized()
        self.conn = sqlite3.connect(str(self.db_path))

    def _ensure_database_initialized(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        schema_path = Path(__file__).with_name("init_db.sql")
        with sqlite3.connect(str(self.db_path)) as conn:
            schema_sql = schema_path.read_text(encoding="utf-8")
            conn.executescript(schema_sql)
            conn.commit()

    def db_select(self, sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
        cursor = self.conn.execute(sql, params)
        return cursor.fetchall()

    def db_operate(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.conn.execute(sql, params)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
