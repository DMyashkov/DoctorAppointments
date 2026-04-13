from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..enums import UserRole


def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.execute(select(models.User).where(models.User.email == email)).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: int) -> models.User | None:
    return db.get(models.User, user_id)


def create_user(
    db: Session,
    *,
    email: str,
    name: str,
    password_hash: str,
    role: UserRole,
    commit: bool = True,
) -> models.User:
    user = models.User(email=email, name=name, password_hash=password_hash, role=role)
    db.add(user)
    if commit:
        db.commit()
        db.refresh(user)
    else:
        db.flush()
        db.refresh(user)
    return user
