"""Shared helpers for API tests: schedules, time slots, registration shortcuts."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient

from app.time_utils import utc_now_naive, utc_today


def schedule_mon_fri() -> dict[str, list[list[str]]]:
    slot = [["08:30", "12:00"], ["13:00", "18:30"]]
    return {
        "monday": slot,
        "tuesday": slot,
        "wednesday": slot,
        "thursday": slot,
        "friday": slot,
        "saturday": [],
        "sunday": [],
    }


def schedule_all_week() -> dict[str, list[list[str]]]:
    day = [["08:00", "20:00"]]
    return {d: list(day) for d in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]}


def schedule_weekdays_only() -> dict[str, list[list[str]]]:
    day = [["08:00", "20:00"]]
    return {
        "monday": list(day),
        "tuesday": list(day),
        "wednesday": list(day),
        "thursday": list(day),
        "friday": list(day),
        "saturday": [],
        "sunday": [],
    }


def slot_weekday_at_least_24h_ahead(hour: int, minute: int = 0) -> tuple[Any, Any]:
    now = utc_now_naive()
    start = (now + timedelta(days=2)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    while start.weekday() >= 5:
        start += timedelta(days=1)
    while start - now < timedelta(hours=24):
        start += timedelta(days=1)
    return start, start + timedelta(minutes=30)


def next_saturday_at_least_24h() -> tuple[Any, Any]:
    now = utc_now_naive()
    start = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    while start.weekday() != 5:
        start += timedelta(days=1)
    while start - now < timedelta(hours=24):
        start += timedelta(days=7)
    return start, start + timedelta(minutes=30)


def register_doctor(
    client: TestClient,
    *,
    email: str,
    name: str = "Dr",
    address: str = "Sofia",
    password: str = "secret12",
    schedule: dict[str, Any] | None = None,
) -> int:
    schedule = schedule or schedule_all_week()
    r = client.post(
        "/auth/register-doctor",
        json={"name": name, "email": email, "address": address, "password": password, "schedule": schedule},
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def register_patient(
    client: TestClient,
    *,
    email: str,
    doctor_id: int,
    phone: str,
    name: str = "P",
    password: str = "secret12",
) -> None:
    r = client.post(
        "/auth/register-patient",
        json={"name": name, "email": email, "phone": phone, "password": password, "doctor_id": doctor_id},
    )
    assert r.status_code == 200, r.text


def login_access_token(client: TestClient, email: str, password: str = "secret12") -> str:
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def doctor_and_patient_tokens(
    client: TestClient,
    *,
    doc_email: str,
    pat_email: str,
    pat_phone: str,
    schedule: dict[str, Any] | None = None,
) -> tuple[int, str, str]:
    doctor_id = register_doctor(client, email=doc_email, schedule=schedule)
    register_patient(client, email=pat_email, doctor_id=doctor_id, phone=pat_phone)
    token_patient = login_access_token(client, pat_email)
    token_doctor = login_access_token(client, doc_email)
    return doctor_id, token_patient, token_doctor
