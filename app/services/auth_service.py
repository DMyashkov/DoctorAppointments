from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import schemas
from ..auth import create_access_token, hash_password, verify_password
from ..dto import DoctorDTO, PatientDTO, doctor_from_profile, patient_from_profile
from ..enums import UserRole
from ..exceptions import ConflictError, NotFoundError, UnauthorizedError
from ..interfaces.repositories import Repositories
from ..repositories.sqlalchemy_impl import get_repositories
from ..schedule_codec import schedule_to_json


def register_doctor(*, db: Session, payload: schemas.DoctorRegisterRequest, repos: Repositories | None = None) -> DoctorDTO:
    repos_ = repos or get_repositories()
    existing = repos_.users.get_user_by_email(db, payload.email)
    if existing:
        raise ConflictError("Email already registered")

    try:
        user = repos_.users.create_user(
            db,
            email=payload.email,
            name=payload.name,
            password_hash=hash_password(payload.password),
            role=UserRole.doctor,
            commit=False,
        )
        profile = repos_.doctor_profiles.create_doctor_profile(
            db,
            user_id=user.id,
            address=payload.address,
            schedule_json=schedule_to_json(payload.schedule),
            commit=False,
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("Email already registered") from None
    except Exception:
        db.rollback()
        raise
    db.refresh(profile)
    return doctor_from_profile(profile)


def register_patient(
    *, db: Session, payload: schemas.PatientRegisterRequest, repos: Repositories | None = None
) -> PatientDTO:
    repos_ = repos or get_repositories()
    existing = repos_.users.get_user_by_email(db, payload.email)
    if existing:
        raise ConflictError("Email already registered")

    doctor_user = repos_.users.get_user_by_id(db, payload.doctor_id)
    if not doctor_user or doctor_user.role != UserRole.doctor:
        raise NotFoundError("Doctor not found")
    if repos_.doctor_profiles.get_doctor_profile_by_user_id(db, doctor_user.id) is None:
        raise NotFoundError("Doctor not found")

    try:
        user = repos_.users.create_user(
            db,
            email=payload.email,
            name=payload.name,
            password_hash=hash_password(payload.password),
            role=UserRole.patient,
            commit=False,
        )
        profile = repos_.patient_profiles.create_patient_profile(
            db, user_id=user.id, phone=payload.phone, doctor_id=doctor_user.id, commit=False
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("Email already registered") from None
    except Exception:
        db.rollback()
        raise
    db.refresh(profile)
    return patient_from_profile(profile)


def login(*, db: Session, payload: schemas.LoginRequest, repos: Repositories | None = None) -> schemas.TokenResponse:
    repos_ = repos or get_repositories()
    user = repos_.users.get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError("Invalid credentials")

    return schemas.TokenResponse.model_validate({"access_token": create_access_token(user_id=user.id)})
