"""CommandExecution — Entity з ідентичністю (job_uuid) та lifecycle-станом.

Ядро логіки кореляції "команда -> подія": відстежує, чи очікує ще команда
на результат виконання, і гарантує дозволені переходи статусів.
"""

from __future__ import annotations

from enum import Enum

from myapp.domain.actions.base import Action
from myapp.domain.exceptions import InvalidExecutionStateError
from myapp.shared.base_entity import Entity


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class CommandExecution(Entity):
    """id — job_uuid, згенерований клієнтом при відправці команди
    (через Event-UUID header у sendmsg execute) і повернений FreeSwitch
    у Application-UUID відповідної CHANNEL_EXECUTE_COMPLETE події."""

    def __init__(
        self,
        id: str,
        channel_id: str,
        action: Action,
        status: ExecutionStatus = ExecutionStatus.PENDING,
        failure_reason: str | None = None,
    ) -> None:
        self.id: str = id
        self.channel_id: str = channel_id
        self.action: Action = action
        self.status: ExecutionStatus = status
        self.failure_reason: str | None = failure_reason

    @classmethod
    def pending(cls, id: str, channel_id: str, action: Action) -> "CommandExecution":
        return cls(id=id, channel_id=channel_id, action=action, status=ExecutionStatus.PENDING)

    def mark_succeeded(self) -> None:
        self._ensure_pending()
        self.status = ExecutionStatus.SUCCEEDED

    def mark_failed(self, reason: str) -> None:
        self._ensure_pending()
        self.status = ExecutionStatus.FAILED
        self.failure_reason = reason

    def mark_cancelled(self, reason: str) -> None:
        """Канал завершився (hangup) до отримання результату виконання команди."""
        self._ensure_pending()
        self.status = ExecutionStatus.CANCELLED
        self.failure_reason = reason

    def _ensure_pending(self) -> None:
        if self.status != ExecutionStatus.PENDING:
            raise InvalidExecutionStateError(
                f"Cannot transition execution {self.id!r} from status {self.status}"
            )
