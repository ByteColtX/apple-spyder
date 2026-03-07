from __future__ import annotations

from datetime import UTC, datetime

import dateutil.parser as parser
from dateutil.tz import gettz

_TZINFOS = {
    "UTC": UTC,
    "GMT": UTC,
    "PDT": gettz("America/Los_Angeles"),
    "PST": gettz("America/Los_Angeles"),
    "EDT": gettz("America/New_York"),
    "EST": gettz("America/New_York"),
}


def parse_datetime(value: str) -> datetime:
    dt = parser.parse(value, tzinfos=_TZINFOS)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def is_a_previous_time(last_update_time: str, current_time: str) -> bool:
    return parse_datetime(last_update_time) < parse_datetime(current_time)


def convert_to_local_timezone(value: str) -> datetime:
    return parse_datetime(value).astimezone(tz=None)
