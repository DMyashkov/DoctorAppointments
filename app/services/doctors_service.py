from __future__ import annotations

from sqlalchemy.orm import Session

from .. import models, schemas
from ..exceptions import BadRequestError, ConflictError
from ..interfaces.repositories import Repositories
from ..repositories.sqlalchemy_impl import get_repositories
from ..schedule_codec import schedule_to_json
from ..time_utils import utc_now_naive
from .schedule import earliest_permanent_change_date


def set_temporary_schedule_change(
    *,
    db: Session,
    doctor: models.DoctorProfile,
    payload: schemas.TemporaryScheduleChangeRequest,
    repos: Repositories | None = None,
) -> None:
    repos_ = repos or get_repositories()
    if payload.end_at <= payload.start_at:
        raise BadRequestError("Invalid interval")

    repos_.schedule_changes.replace_temporary_schedule_change(
        db,
        doctor_user_id=doctor.user_id,
        start_at=payload.start_at,
        end_at=payload.end_at,
        schedule_json=schedule_to_json(payload.schedule),
        commit=False,
    )
    db.commit()


def add_permanent_schedule_change(
    *,
    db: Session,
    doctor: models.DoctorProfile,
    payload: schemas.PermanentScheduleChangeRequest,
    repos: Repositories | None = None,
) -> None:
    repos_ = repos or get_repositories()
    min_date = earliest_permanent_change_date(7)
    if payload.effective_from_date < min_date:
        raise BadRequestError("Permanent schedule must start at least 7 days in the future")

    existing_same_date = repos_.schedule_changes.find_permanent_schedule_change_for_doctor_on_date(
        db, doctor_user_id=doctor.user_id, effective_from_date=payload.effective_from_date
    )
    if existing_same_date:
        raise ConflictError("Permanent schedule change for that date already exists")

    repos_.schedule_changes.create_permanent_schedule_change(
        db,
        doctor_user_id=doctor.user_id,
        effective_from_date=payload.effective_from_date,
        schedule_json=schedule_to_json(payload.schedule),
        created_at=utc_now_naive(),
        commit=False,
    )
    db.commit()
