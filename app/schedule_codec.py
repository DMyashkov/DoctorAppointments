from __future__ import annotations

import json
import re
from datetime import time
from typing import Any

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
_HHMM = re.compile(r"^\d{1,2}:\d{2}$")


def parse_hhmm(value: str) -> tuple[int, int]:
    if not _HHMM.match(value):
        raise ValueError(f"Invalid time format (expected HH:MM): {value!r}")
    hh_s, mm_s = value.split(":", 1)
    hh, mm = int(hh_s), int(mm_s)
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        raise ValueError(f"Invalid time values: {value!r}")
    return hh, mm


def time_from_hhmm(value: str) -> time:
    hh, mm = parse_hhmm(value)
    return time(hour=hh, minute=mm)


def validate_api_schedule(raw: Any) -> None:
    if raw is None:
        raise ValueError("Schedule is required")
    if not isinstance(raw, dict):
        raise ValueError("Schedule must be an object")
    norm: dict[str, Any] = {str(k).lower(): v for k, v in raw.items()}
    unknown = set(norm) - set(WEEKDAYS)
    if unknown:
        bad = next(iter(unknown))
        raise ValueError(f"Unknown weekday key: {bad!r}")
    for day in WEEKDAYS:
        intervals = norm.get(day, [])
        if intervals is None:
            continue
        if not isinstance(intervals, list):
            raise ValueError(f"Intervals for {day} must be a list")
        parsed_times: list[tuple[time, time, str, str]] = []
        for item in intervals:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                raise ValueError(f"Each interval for {day} must be [start, end]")
            s, e = item[0], item[1]
            if not isinstance(s, str) or not isinstance(e, str):
                raise ValueError(f"Interval bounds for {day} must be strings (HH:MM)")
            st = time_from_hhmm(s)
            et = time_from_hhmm(e)
            if st >= et:
                raise ValueError(f"On {day}, interval start must be before end ({s!r} - {e!r})")
            parsed_times.append((st, et, s, e))
        parsed_times.sort(key=lambda x: x[0])
        for i in range(len(parsed_times) - 1):
            cur_end = parsed_times[i][1]
            nxt_start = parsed_times[i + 1][0]
            if cur_end > nxt_start:
                raise ValueError(f"Overlapping intervals on {day}")


def normalize_schedule(schedule: dict[Any, Any]) -> dict[str, list[tuple[str, str]]]:
    normalized: dict[str, list[tuple[str, str]]] = {}
    for day, intervals in (schedule or {}).items():
        day_l = str(day).lower()
        if day_l not in WEEKDAYS:
            continue
        normalized[day_l] = [(str(s), str(e)) for (s, e) in intervals]
    for day in WEEKDAYS:
        normalized.setdefault(day, [])
    return normalized


def schedule_to_json(schedule: dict[str, list[tuple[str, str]]]) -> str:
    return json.dumps(normalize_schedule(schedule), ensure_ascii=False, separators=(",", ":"))


def schedule_from_json(value: str) -> dict[str, list[tuple[str, str]]]:
    raw = json.loads(value or "{}")
    if not isinstance(raw, dict):
        raise ValueError("Stored schedule JSON must be an object")
    return normalize_schedule(raw)
