from __future__ import annotations

class DomainError(Exception):
    """Business/domain rule violation.

    Mapped to transport-specific errors (HTTP) outside the domain layer.
    """

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class BadRequestError(DomainError):
    pass


class UnauthorizedError(DomainError):
    pass


class ForbiddenError(DomainError):
    pass


class NotFoundError(DomainError):
    pass


class ConflictError(DomainError):
    pass
