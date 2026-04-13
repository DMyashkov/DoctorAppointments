from __future__ import annotations

from typing import Literal, TypedDict, cast

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import models
from .auth import decode_token
from .db import get_db
from .enums import UserRole
from .repositories.doctor_profiles import get_doctor_profile_by_user_id
from .repositories.patient_profiles import get_patient_profile_by_user_id
from .repositories.users import get_user_by_id

bearer = HTTPBearer(auto_error=False)


class CurrentDoctorUser(TypedDict):
    role: Literal["doctor"]
    general: models.User
    roleSpecific: models.DoctorProfile


class CurrentPatientUser(TypedDict):
    role: Literal["patient"]
    general: models.User
    roleSpecific: models.PatientProfile


CurrentUser = CurrentDoctorUser | CurrentPatientUser


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if creds is None:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = decode_token(creds.credentials)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = get_user_by_id(db, token.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found", headers={"WWW-Authenticate": "Bearer"})

    if user.role == UserRole.doctor:
        doctor = get_doctor_profile_by_user_id(db, user.id)
        if not doctor:
            raise HTTPException(status_code=401, detail="User not found", headers={"WWW-Authenticate": "Bearer"})
        doc_user: CurrentDoctorUser = {"role": "doctor", "general": user, "roleSpecific": doctor}
        return doc_user

    if user.role == UserRole.patient:
        patient = get_patient_profile_by_user_id(db, user.id)
        if not patient:
            raise HTTPException(status_code=401, detail="User not found", headers={"WWW-Authenticate": "Bearer"})
        pat_user: CurrentPatientUser = {"role": "patient", "general": user, "roleSpecific": patient}
        return pat_user

    raise HTTPException(status_code=401, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})


def require_doctor(user: CurrentUser = Depends(get_current_user)) -> models.DoctorProfile:
    if user["general"].role != UserRole.doctor:
        raise HTTPException(status_code=403, detail="Doctor access required")
    return cast(models.DoctorProfile, user["roleSpecific"])


def require_patient(user: CurrentUser = Depends(get_current_user)) -> models.PatientProfile:
    if user["general"].role != UserRole.patient:
        raise HTTPException(status_code=403, detail="Patient access required")
    return cast(models.PatientProfile, user["roleSpecific"])
