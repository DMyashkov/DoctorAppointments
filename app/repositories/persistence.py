from __future__ import annotations

from typing import TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")


def commit_or_flush(db: Session, *, commit: bool) -> None:
    if commit:
        db.commit()
    else:
        db.flush()


def commit_or_flush_and_refresh(db: Session, instance: T, *, commit: bool) -> T:
    if commit:
        db.commit()
        db.refresh(instance)
    else:
        db.flush()
        db.refresh(instance)
    return instance
