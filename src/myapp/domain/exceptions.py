"""Доменні винятки."""
from __future__ import annotations


class DomainError(Exception):
    """Базовий клас усіх доменних помилок застосунку."""


class UnknownActionTypeError(DomainError):
    def __init__(self, action_type: str) -> None:
        self.action_type: str = action_type
        super().__init__(f"Unknown action type: {action_type!r}")


class UnknownExecutionError(DomainError):
    """CHANNEL_EXECUTE_COMPLETE прийшов для job_uuid, якого немає в репозиторії."""

    def __init__(self, job_uuid: str) -> None:
        self.job_uuid: str = job_uuid
        super().__init__(f"No pending execution found for job_uuid={job_uuid!r}")


class InvalidExecutionStateError(DomainError):
    """Спроба виконати недозволений перехід статусу CommandExecution."""
