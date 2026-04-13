from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from sqlalchemy.orm import Session

from .. import models
from ..repositories.schedule_changes import (
    get_latest_permanent_schedule_change_on_or_before,
    get_temporary_schedule_change_by_doctor_user_id,
)
from ..schedule_codec import WEEKDAYS, schedule_from_json, time_from_hhmm
from ..time_utils import utc_today


@dataclass(frozen=True)
class EffectiveSchedule:
    schedule: dict[str, list[tuple[str, str]]]
    source: Literal["base", "permanent", "temporary"]


def get_effective_schedule(db: Session, doctor: models.DoctorProfile, at: datetime) -> EffectiveSchedule:
    temp = get_temporary_schedule_change_by_doctor_user_id(db, doctor.user_id)
    if temp and temp.start_at <= at < temp.end_at:
        return EffectiveSchedule(schedule=schedule_from_json(temp.schedule_json), source="temporary")

    perm = get_latest_permanent_schedule_change_on_or_before(db, doctor_user_id=doctor.user_id, on_date=at.date())
    if perm:
        return EffectiveSchedule(schedule=schedule_from_json(perm.schedule_json), source="permanent")

    return EffectiveSchedule(schedule=schedule_from_json(doctor.schedule_json), source="base")


def is_interval_within_working_hours(
    *,
    schedule: dict[str, list[tuple[str, str]]],
    start_at: datetime,
    end_at: datetime,
) -> bool:
    if end_at <= start_at:
        return False
    if start_at.date() != end_at.date():
        return False

    weekday = WEEKDAYS[start_at.weekday()]
    intervals = schedule.get(weekday, [])
    if not intervals:
        return False

    start_t = start_at.time()
    end_t = end_at.time()

    for s, e in intervals:
        s_t = time_from_hhmm(s)
        e_t = time_from_hhmm(e)
        if s_t <= start_t and end_t <= e_t:
            return True
    return False


def earliest_permanent_change_date(min_days: int = 7) -> date:
    return utc_today().fromordinal(utc_today().toordinal() + min_days)
