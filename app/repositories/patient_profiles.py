from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from .persistence import commit_or_flush_and_refresh


def get_patient_profile_by_user_id(db: Session, user_id: int) -> models.PatientProfile | None:
    stmt = select(models.PatientProfile).where(models.PatientProfile.user_id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def create_patient_profile(
    db: Session,
    *,
    user_id: int,
    phone: str,
    doctor_id: int,
    commit: bool = True,
) -> models.PatientProfile:
    profile = models.PatientProfile(user_id=user_id, phone=phone, doctor_id=doctor_id)
    db.add(profile)
    return commit_or_flush_and_refresh(db, profile, commit=commit)
