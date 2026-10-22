"""Structured failures; a resource limit is not a linguistic refutation."""

from __future__ import annotations

from typing import Any


class NabtError(ValueError):
    """A named rejection or an explicitly incomplete computation."""

    def __init__(
        self, code: str, message: str, *, status: str = "REJECT", details: Any = None
    ) -> None:
        super().__init__(message)
        if status not in {"REJECT", "DEFER"}:
            raise ValueError("Unsupported NABT error status")
        self.code = code
        self.message = message
        self.status = status
        self.details = details

    def as_dict(self) -> dict[str, Any]:
        result = {"status": self.status, "code": self.code, "message": self.message}
        if self.details is not None:
            result["details"] = self.details
        return result


def natural(value: object, name: str, *, maximum: int | None = None) -> int:
    """Require an actual natural integer; Python booleans are not numbers here."""
    if type(value) is not int or value < 0:
        raise NabtError("INVALID_NATURAL", f"{name} must be a non-negative integer")
    if maximum is not None and value > maximum:
        raise NabtError("OUTSIDE_DOMAIN", f"{name} exceeds its declared domain")
    return value


def resource_limit(message: str, **details: Any) -> NabtError:
    return NabtError("RESOURCE_LIMIT", message, status="DEFER", details=details or None)
