from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models


def get_temporary_schedule_change_by_doctor_user_id(
    db: Session, doctor_user_id: int
) -> models.TemporaryScheduleChange | None:
    stmt = select(models.TemporaryScheduleChange).where(models.TemporaryScheduleChange.doctor_id == doctor_user_id)
    return db.execute(stmt).scalar_one_or_none()


def replace_temporary_schedule_change(
    db: Session,
    *,
    doctor_user_id: int,
    start_at: datetime,
    end_at: datetime,
    schedule_json: str,
    commit: bool = True,
) -> None:
    existing = get_temporary_schedule_change_by_doctor_user_id(db, doctor_user_id)
    if existing:
        db.delete(existing)
    change = models.TemporaryScheduleChange(
        doctor_id=doctor_user_id,
        start_at=start_at,
        end_at=end_at,
        schedule_json=schedule_json,
    )
    db.add(change)
    if commit:
        db.commit()
    else:
        db.flush()


def find_permanent_schedule_change_for_doctor_on_date(
    db: Session,
    *,
    doctor_user_id: int,
    effective_from_date: date,
) -> models.PermanentScheduleChange | None:
    stmt = (
        select(models.PermanentScheduleChange)
        .where(models.PermanentScheduleChange.doctor_id == doctor_user_id)
        .where(models.PermanentScheduleChange.effective_from_date == effective_from_date)
    )
    return db.execute(stmt).scalar_one_or_none()


def create_permanent_schedule_change(
    db: Session,
    *,
    doctor_user_id: int,
    effective_from_date: date,
    schedule_json: str,
    created_at: datetime,
    commit: bool = True,
) -> models.PermanentScheduleChange:
    change = models.PermanentScheduleChange(
        doctor_id=doctor_user_id,
        effective_from_date=effective_from_date,
        schedule_json=schedule_json,
        created_at=created_at,
    )
    db.add(change)
    if commit:
        db.commit()
        db.refresh(change)
    else:
        db.flush()
        db.refresh(change)
    return change


def get_latest_permanent_schedule_change_on_or_before(
    db: Session,
    *,
    doctor_user_id: int,
    on_date: date,
) -> models.PermanentScheduleChange | None:
    stmt = (
        select(models.PermanentScheduleChange)
        .where(models.PermanentScheduleChange.doctor_id == doctor_user_id)
        .where(models.PermanentScheduleChange.effective_from_date <= on_date)
        .order_by(models.PermanentScheduleChange.effective_from_date.desc())
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()
