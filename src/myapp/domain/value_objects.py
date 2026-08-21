"""ValidationResult — Value Object з результатом валідації виконання команди."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResult:
    execution_id: str
    is_success: bool
    reason: str | None = None

    @classmethod
    def success(cls, execution_id: str) -> "ValidationResult":
        return cls(execution_id=execution_id, is_success=True)

    @classmethod
    def failure(cls, execution_id: str, reason: str) -> "ValidationResult":
        return cls(execution_id=execution_id, is_success=False, reason=reason)
