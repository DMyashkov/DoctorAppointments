from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .. import models
from ..dto import AppointmentDTO, appointment_from_model
from ..enums import AppointmentStatus, CancelledBy, UserRole
from ..exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from ..interfaces.repositories import Repositories
from ..repositories.sqlalchemy_impl import get_repositories
from ..time_utils import utc_now_naive
from .schedule import get_effective_schedule, is_interval_within_working_hours


@dataclass(frozen=True)
class CreateAppointmentResult:
    appointment: AppointmentDTO


def create_appointment(
    *,
    db: Session,
    patient: models.PatientProfile,
    doctor_id: int,
    start_at: datetime,
    end_at: datetime,
    now: datetime | None = None,
    repos: Repositories | None = None,
) -> CreateAppointmentResult:
    repos_ = repos or get_repositories()
    if patient.doctor_id != doctor_id:
        raise BadRequestError("Doctor is not patient's personal doctor")

    doctor = repos_.doctor_profiles.get_doctor_profile_by_user_id(db, doctor_id)
    if not doctor:
        raise NotFoundError("Doctor not found")

    now_dt = now or utc_now_naive()
    if start_at - now_dt < timedelta(hours=24):
        raise BadRequestError("Appointment must be created at least 24h in advance")

    effective = get_effective_schedule(db, doctor, start_at)
    if not is_interval_within_working_hours(schedule=effective.schedule, start_at=start_at, end_at=end_at):
        raise BadRequestError("Appointment is outside doctor's working hours")

    overlapping = repos_.appointments.find_active_overlapping_appointment(
        db, doctor_user_id=doctor_id, start_at=start_at, end_at=end_at
    )
    if overlapping:
        raise ConflictError("Appointment overlaps with existing appointment")

    appt = repos_.appointments.create_appointment(
        db,
        doctor_user_id=doctor_id,
        patient_user_id=patient.user_id,
        start_at=start_at,
        end_at=end_at,
        status=AppointmentStatus.active,
        commit=False,
    )
    db.commit()
    db.refresh(appt)
    return CreateAppointmentResult(appointment=appointment_from_model(appt))


def cancel_appointment(
    *,
    db: Session,
    appt: models.Appointment,
    by_role: CancelledBy,
    now: datetime | None = None,
    repos: Repositories | None = None,
) -> AppointmentDTO:
    repos_ = repos or get_repositories()
    if appt.status != AppointmentStatus.active:
        return appointment_from_model(appt)

    now_dt = now or utc_now_naive()
    if appt.start_at - now_dt < timedelta(hours=12):
        raise BadRequestError("Cannot cancel later than 12h before start time")

    appt.status = AppointmentStatus.cancelled
    appt.cancelled_by = by_role
    appt.cancelled_at = now_dt
    saved = repos_.appointments.save_appointment(db, appt, commit=False)
    db.commit()
    db.refresh(saved)
    return appointment_from_model(saved)


def cancel_appointment_as_user(
    *,
    db: Session,
    user_id: int,
    role: UserRole,
    appointment_id: int,
    repos: Repositories | None = None,
) -> AppointmentDTO:
    repos_ = repos or get_repositories()
    appt = repos_.appointments.get_appointment_by_id(db, appointment_id)
    if not appt:
        raise NotFoundError("Appointment not found")

    if role == UserRole.doctor:
        if appt.doctor_id != user_id:
            raise ForbiddenError("Not allowed")
        by_role = CancelledBy.doctor
    elif role == UserRole.patient:
        if appt.patient_id != user_id:
            raise ForbiddenError("Not allowed")
        by_role = CancelledBy.patient
    else:
        raise ForbiddenError("Not allowed")

    return cancel_appointment(db=db, appt=appt, by_role=by_role, repos=repos_)


def list_my_appointments(*, db: Session, user_id: int, role: UserRole) -> list[AppointmentDTO]:
    repos_ = get_repositories()
    rows = repos_.appointments.list_appointments_for_user(db, user_id, as_doctor=(role == UserRole.doctor))
    return [appointment_from_model(a) for a in rows]
