from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..db import get_db
from ..services.auth_service import login as login_service
from ..services.auth_service import register_doctor as register_doctor_service
from ..services.auth_service import register_patient as register_patient_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register-doctor", response_model=schemas.DoctorResponse)
def register_doctor(payload: schemas.DoctorRegisterRequest, db: Session = Depends(get_db)):
    dto = register_doctor_service(db=db, payload=payload)
    return schemas.DoctorResponse.from_doctor_dto(dto)


@router.post("/register-patient", response_model=schemas.PatientResponse)
def register_patient(payload: schemas.PatientRegisterRequest, db: Session = Depends(get_db)):
    dto = register_patient_service(db=db, payload=payload)
    return schemas.PatientResponse.from_patient_dto(dto)


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    return login_service(db=db, payload=payload)
