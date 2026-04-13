from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    doctor = "doctor"
    patient = "patient"


class AppointmentStatus(StrEnum):
    active = "active"
    cancelled = "cancelled"


class CancelledBy(StrEnum):
    doctor = "doctor"
    patient = "patient"
