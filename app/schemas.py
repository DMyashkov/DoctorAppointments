from __future__ import annotations

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, Field, field_validator, model_validator

from .dto import AppointmentDTO, DoctorDTO, PatientDTO
from .enums import AppointmentStatus, CancelledBy
from .schedule_codec import normalize_schedule, schedule_from_json, validate_api_schedule

if TYPE_CHECKING:
    from .models import DoctorProfile, PatientProfile


def _validate_schedule_input(v: object) -> dict[str, list[tuple[str, str]]]:
    validate_api_schedule(v)
    assert isinstance(v, dict)
    return normalize_schedule(v)


def _utc_naive_datetime(v: datetime) -> datetime:
    if v.tzinfo is not None:
        v = v.astimezone(UTC)
    return v.replace(tzinfo=None)


Schedule = Annotated[dict[str, list[tuple[str, str]]], BeforeValidator(_validate_schedule_input)]


class TokenResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "token_type": "bearer"},
            ]
        }
    )

    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"email": "dr@example.com", "password": "secret12"}]}
    )

    email: EmailStr
    password: str = Field(min_length=6)


class DoctorRegisterRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Dr Ivan Petrov",
                    "email": "dr@example.com",
                    "address": "Sofia, 1 Example Street",
                    "password": "secret12",
                    "schedule": {
                        "monday": [["08:30", "12:00"], ["13:00", "18:30"]],
                        "tuesday": [["08:30", "12:00"], ["13:00", "18:30"]],
                        "wednesday": [["08:30", "12:00"], ["13:00", "18:30"]],
                        "thursday": [["08:30", "12:00"], ["13:00", "18:30"]],
                        "friday": [["08:30", "12:00"], ["13:00", "18:30"]],
                        "saturday": [["09:00", "12:30"]],
                        "sunday": [],
                    },
                }
            ]
        }
    )

    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    address: str = Field(min_length=1, max_length=500)
    password: str = Field(min_length=6)
    schedule: Schedule = Field(default_factory=dict)


class DoctorResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "name": "Dr Ivan Petrov",
                    "email": "dr@example.com",
                    "address": "Sofia, 1 Example Street",
                    "schedule": {
                        "monday": [["08:30", "12:00"], ["13:00", "18:30"]],
                        "tuesday": [["08:30", "12:00"], ["13:00", "18:30"]],
                        "wednesday": [["08:30", "12:00"], ["13:00", "18:30"]],
                        "thursday": [["08:30", "12:00"], ["13:00", "18:30"]],
                        "friday": [["08:30", "12:00"], ["13:00", "18:30"]],
                        "saturday": [["09:00", "12:30"]],
                        "sunday": [],
                    },
                }
            ]
        },
    )

    id: int
    name: str
    email: EmailStr
    address: str
    schedule: dict[str, list[tuple[str, str]]]

    @classmethod
    def from_doctor_profile(cls, doctor: DoctorProfile) -> DoctorResponse:
        return cls.model_validate(
            {
                "id": doctor.user_id,
                "name": doctor.user.name,
                "email": doctor.user.email,
                "address": doctor.address,
                "schedule": schedule_from_json(doctor.schedule_json),
            }
        )

    @classmethod
    def from_doctor_dto(cls, d: DoctorDTO) -> DoctorResponse:
        return cls.model_validate(
            {"id": d.user_id, "name": d.name, "email": d.email, "address": d.address, "schedule": d.schedule}
        )


class PatientRegisterRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Maria Ivanova",
                    "email": "patient@example.com",
                    "phone": "+359888000000",
                    "password": "secret12",
                    "doctor_id": 1,
                }
            ]
        }
    )

    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    phone: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^\+?[0-9][0-9 -]{2,49}$",
        description="Phone number; digits with optional leading +, spaces, or hyphens.",
    )
    password: str = Field(min_length=6)
    doctor_id: int = Field(gt=0)


class PatientResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 2,
                    "name": "Maria Ivanova",
                    "email": "patient@example.com",
                    "phone": "+359888000000",
                    "doctor_id": 1,
                }
            ]
        },
    )

    id: int
    name: str
    email: EmailStr
    phone: str
    doctor_id: int

    @classmethod
    def from_patient_profile(cls, patient: PatientProfile) -> PatientResponse:
        return cls.model_validate(
            {
                "id": patient.user_id,
                "name": patient.user.name,
                "email": patient.user.email,
                "phone": patient.phone,
                "doctor_id": patient.doctor_id,
            }
        )

    @classmethod
    def from_patient_dto(cls, d: PatientDTO) -> PatientResponse:
        return cls.model_validate(
            {
                "id": d.user_id,
                "name": d.name,
                "email": d.email,
                "phone": d.phone,
                "doctor_id": d.doctor_id,
            }
        )


class ScheduleUpdateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "schedule": {
                        "monday": [["09:00", "12:00"], ["13:00", "17:00"]],
                        "tuesday": [["09:00", "12:00"], ["13:00", "17:00"]],
                        "wednesday": [["09:00", "12:00"], ["13:00", "17:00"]],
                        "thursday": [["09:00", "12:00"], ["13:00", "17:00"]],
                        "friday": [["09:00", "12:00"]],
                        "saturday": [],
                        "sunday": [],
                    }
                }
            ]
        }
    )

    schedule: Schedule


class TemporaryScheduleChangeRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "start_at": "2026-04-20T00:00:00Z",
                    "end_at": "2026-04-27T00:00:00Z",
                    "schedule": {"monday": [["10:00", "14:00"]], "tuesday": [], "wednesday": [], "thursday": [], "friday": [], "saturday": [], "sunday": []},
                }
            ]
        }
    )

    start_at: datetime
    end_at: datetime
    schedule: Schedule

    @field_validator("start_at", "end_at", mode="after")
    @classmethod
    def _utc_naive(cls, v: datetime) -> datetime:
        return _utc_naive_datetime(v)

    @model_validator(mode="after")
    def _validate_interval(self) -> TemporaryScheduleChangeRequest:
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class PermanentScheduleChangeRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "effective_from_date": "2026-05-01",
                    "schedule": {
                        "monday": [["08:00", "12:00"], ["13:00", "16:00"]],
                        "tuesday": [["08:00", "12:00"], ["13:00", "16:00"]],
                        "wednesday": [["08:00", "12:00"], ["13:00", "16:00"]],
                        "thursday": [["08:00", "12:00"], ["13:00", "16:00"]],
                        "friday": [["08:00", "12:00"]],
                        "saturday": [],
                        "sunday": [],
                    },
                }
            ]
        }
    )

    effective_from_date: date
    schedule: Schedule


class AppointmentCreateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"doctor_id": 1, "start_at": "2026-04-20T09:00:00Z", "end_at": "2026-04-20T09:30:00Z"}
            ]
        }
    )

    doctor_id: int = Field(gt=0)
    start_at: datetime
    end_at: datetime

    @field_validator("start_at", "end_at", mode="after")
    @classmethod
    def _utc_naive(cls, v: datetime) -> datetime:
        return _utc_naive_datetime(v)

    @model_validator(mode="after")
    def _validate_interval(self) -> AppointmentCreateRequest:
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 10,
                    "doctor_id": 1,
                    "patient_id": 2,
                    "start_at": "2026-04-20T09:00:00Z",
                    "end_at": "2026-04-20T09:30:00Z",
                    "status": "active",
                    "cancelled_by": None,
                    "cancelled_at": None,
                    "created_at": "2026-04-10T12:00:00Z",
                }
            ]
        },
    )

    id: int
    doctor_id: int
    patient_id: int
    start_at: datetime
    end_at: datetime
    status: AppointmentStatus
    cancelled_by: CancelledBy | None = None
    cancelled_at: datetime | None = None
    created_at: datetime

    @classmethod
    def from_appointment_dto(cls, d: AppointmentDTO) -> AppointmentResponse:
        return cls.model_validate(
            {
                "id": d.id,
                "doctor_id": d.doctor_id,
                "patient_id": d.patient_id,
                "start_at": d.start_at,
                "end_at": d.end_at,
                "status": d.status,
                "cancelled_by": d.cancelled_by,
                "cancelled_at": d.cancelled_at,
                "created_at": d.created_at,
            }
        )


class MessageResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"message": "Permanent schedule change added", "details": None}]}
    )

    message: str
    details: dict[str, str] | None = None

    @classmethod
    def with_message(cls, message: str, *, details: dict[str, str] | None = None) -> MessageResponse:
        return cls.model_validate({"message": message, "details": details})
