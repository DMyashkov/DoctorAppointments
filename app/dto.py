from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .enums import AppointmentStatus, CancelledBy
from .models import Appointment, DoctorProfile, PatientProfile
from .schedule_codec import schedule_from_json


@dataclass(frozen=True)
class DoctorDTO:
    user_id: int
    name: str
    email: str
    address: str
    schedule: dict[str, list[tuple[str, str]]]


@dataclass(frozen=True)
class PatientDTO:
    user_id: int
    name: str
    email: str
    phone: str
    doctor_id: int


@dataclass(frozen=True)
class AppointmentDTO:
    id: int
    doctor_id: int
    patient_id: int
    start_at: datetime
    end_at: datetime
    status: AppointmentStatus
    cancelled_by: CancelledBy | None
    cancelled_at: datetime | None
    created_at: datetime


def doctor_from_profile(profile: DoctorProfile) -> DoctorDTO:
    return DoctorDTO(
        user_id=profile.user_id,
        name=profile.user.name,
        email=profile.user.email,
        address=profile.address,
        schedule=schedule_from_json(profile.schedule_json),
    )


def patient_from_profile(profile: PatientProfile) -> PatientDTO:
    return PatientDTO(
        user_id=profile.user_id,
        name=profile.user.name,
        email=profile.user.email,
        phone=profile.phone,
        doctor_id=profile.doctor_id,
    )


def appointment_from_model(appt: Appointment) -> AppointmentDTO:
    return AppointmentDTO(
        id=appt.id,
        doctor_id=appt.doctor_id,
        patient_id=appt.patient_id,
        start_at=appt.start_at,
        end_at=appt.end_at,
        status=appt.status,
        cancelled_by=appt.cancelled_by,
        cancelled_at=appt.cancelled_at,
        created_at=appt.created_at,
    )
