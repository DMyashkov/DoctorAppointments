from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models


def get_doctor_profile_by_user_id(db: Session, user_id: int) -> models.DoctorProfile | None:
    stmt = select(models.DoctorProfile).where(models.DoctorProfile.user_id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def update_doctor_schedule_json(db: Session, doctor: models.DoctorProfile, schedule_json: str) -> None:
    doctor.schedule_json = schedule_json
    db.add(doctor)
    db.commit()
    db.refresh(doctor)


def create_doctor_profile(
    db: Session,
    *,
    user_id: int,
    address: str,
    schedule_json: str,
    commit: bool = True,
) -> models.DoctorProfile:
    profile = models.DoctorProfile(user_id=user_id, address=address, schedule_json=schedule_json)
    db.add(profile)
    if commit:
        db.commit()
        db.refresh(profile)
    else:
        db.flush()
        db.refresh(profile)
    return profile
