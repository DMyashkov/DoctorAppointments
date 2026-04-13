from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from .. import models
from ..enums import AppointmentStatus


def get_appointment_by_id(db: Session, appointment_id: int) -> models.Appointment | None:
    return db.get(models.Appointment, appointment_id)


def list_appointments_for_user(db: Session, user_id: int, *, as_doctor: bool) -> list[models.Appointment]:
    fk = models.Appointment.doctor_id if as_doctor else models.Appointment.patient_id
    stmt = select(models.Appointment).where(fk == user_id).order_by(models.Appointment.start_at.asc())
    return list(db.execute(stmt).scalars().all())


def find_active_overlapping_appointment(
    db: Session,
    *,
    doctor_user_id: int,
    start_at: datetime,
    end_at: datetime,
) -> models.Appointment | None:
    stmt = (
        select(models.Appointment)
        .where(models.Appointment.doctor_id == doctor_user_id)
        .where(models.Appointment.status == AppointmentStatus.active)
        .where(and_(models.Appointment.start_at < end_at, models.Appointment.end_at > start_at))
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def create_appointment(
    db: Session,
    *,
    doctor_user_id: int,
    patient_user_id: int,
    start_at: datetime,
    end_at: datetime,
    status: AppointmentStatus = AppointmentStatus.active,
    commit: bool = True,
) -> models.Appointment:
    appt = models.Appointment(
        doctor_id=doctor_user_id,
        patient_id=patient_user_id,
        start_at=start_at,
        end_at=end_at,
        status=status,
    )
    db.add(appt)
    if commit:
        db.commit()
        db.refresh(appt)
    else:
        db.flush()
        db.refresh(appt)
    return appt


def save_appointment(db: Session, appt: models.Appointment, *, commit: bool = True) -> models.Appointment:
    db.add(appt)
    if commit:
        db.commit()
        db.refresh(appt)
    else:
        db.flush()
        db.refresh(appt)
    return appt
