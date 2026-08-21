"""In-memory реалізація CommandExecutionRepository.

Для одного інстансу застосунку; для горизонтального масштабування чи
переживання рестарту — заміна на Redis-реалізацію за тим самим інтерфейсом
(див. рекомендацію в README щодо високого навантаження).
"""
from __future__ import annotations

from myapp.domain.entities import CommandExecution, ExecutionStatus
from myapp.domain.repositories import CommandExecutionRepository


class InMemoryCommandExecutionRepository(CommandExecutionRepository):
    def __init__(self) -> None:
        self._storage: dict[str, CommandExecution] = {}

    def get_by_id(self, job_uuid: str) -> CommandExecution | None:
        return self._storage.get(job_uuid)

    def get_pending_by_channel_id(self, channel_id: str) -> list[CommandExecution]:
        return [
            execution
            for execution in self._storage.values()
            if execution.channel_id == channel_id
            and execution.status == ExecutionStatus.PENDING
        ]

    def save(self, execution: CommandExecution) -> None:
        self._storage[execution.id] = execution

    def delete(self, job_uuid: str) -> None:
        self._storage.pop(job_uuid, None)
