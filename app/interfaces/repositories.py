from __future__ import annotations

from datetime import date, datetime
from typing import Protocol

from sqlalchemy.orm import Session

from .. import models
from ..enums import AppointmentStatus, UserRole


class UsersRepository(Protocol):
    def get_user_by_email(self, db: Session, email: str) -> models.User | None: ...
    def get_user_by_id(self, db: Session, user_id: int) -> models.User | None: ...

    def create_user(
        self,
        db: Session,
        *,
        email: str,
        name: str,
        password_hash: str,
        role: UserRole,
        commit: bool = True,
    ) -> models.User: ...


class DoctorProfilesRepository(Protocol):
    def get_doctor_profile_by_user_id(self, db: Session, user_id: int) -> models.DoctorProfile | None: ...
    def update_doctor_schedule_json(self, db: Session, doctor: models.DoctorProfile, schedule_json: str) -> None: ...
    def create_doctor_profile(
        self,
        db: Session,
        *,
        user_id: int,
        address: str,
        schedule_json: str,
        commit: bool = True,
    ) -> models.DoctorProfile: ...


class PatientProfilesRepository(Protocol):
    def get_patient_profile_by_user_id(self, db: Session, user_id: int) -> models.PatientProfile | None: ...
    def create_patient_profile(
        self,
        db: Session,
        *,
        user_id: int,
        phone: str,
        doctor_id: int,
        commit: bool = True,
    ) -> models.PatientProfile: ...


class AppointmentsRepository(Protocol):
    def get_appointment_by_id(self, db: Session, appointment_id: int) -> models.Appointment | None: ...
    def list_appointments_for_user(self, db: Session, user_id: int, *, as_doctor: bool) -> list[models.Appointment]: ...
    def find_active_overlapping_appointment(
        self, db: Session, *, doctor_user_id: int, start_at: datetime, end_at: datetime
    ) -> models.Appointment | None: ...
    def create_appointment(
        self,
        db: Session,
        *,
        doctor_user_id: int,
        patient_user_id: int,
        start_at: datetime,
        end_at: datetime,
        status: AppointmentStatus = AppointmentStatus.active,
        commit: bool = True,
    ) -> models.Appointment: ...
    def save_appointment(self, db: Session, appt: models.Appointment, *, commit: bool = True) -> models.Appointment: ...


class ScheduleChangesRepository(Protocol):
    def get_temporary_schedule_change_by_doctor_user_id(
        self, db: Session, doctor_user_id: int
    ) -> models.TemporaryScheduleChange | None: ...
    def replace_temporary_schedule_change(
        self,
        db: Session,
        *,
        doctor_user_id: int,
        start_at: datetime,
        end_at: datetime,
        schedule_json: str,
        commit: bool = True,
    ) -> None: ...
    def find_permanent_schedule_change_for_doctor_on_date(
        self,
        db: Session,
        *,
        doctor_user_id: int,
        effective_from_date: date,
    ) -> models.PermanentScheduleChange | None: ...
    def create_permanent_schedule_change(
        self,
        db: Session,
        *,
        doctor_user_id: int,
        effective_from_date: date,
        schedule_json: str,
        created_at: datetime,
        commit: bool = True,
    ) -> models.PermanentScheduleChange: ...
    def get_latest_permanent_schedule_change_on_or_before(
        self, db: Session, *, doctor_user_id: int, on_date: date
    ) -> models.PermanentScheduleChange | None: ...


class Repositories(Protocol):
    users: UsersRepository
    doctor_profiles: DoctorProfilesRepository
    patient_profiles: PatientProfilesRepository
    appointments: AppointmentsRepository
    schedule_changes: ScheduleChangesRepository

