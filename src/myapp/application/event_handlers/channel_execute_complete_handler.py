"""Обробник CHANNEL_EXECUTE_COMPLETE.

Подія завжди корелює з конкретним CommandExecution через job_uuid.
Тут відбувається міні-валідація (app_response) і публікація success/failed
результату.
"""
from __future__ import annotations

from myapp.application.ports import ResultPublisherPort
from myapp.domain.entities import CommandExecution
from myapp.domain.events.channel_execute_complete import ChannelExecuteCompleteEvent
from myapp.domain.exceptions import UnknownExecutionError
from myapp.domain.repositories import CommandExecutionRepository

_SUCCESS_RESPONSES: frozenset[str] = frozenset({"FILE PLAYED", "SUCCESS", "OK"})


class ChannelExecuteCompleteHandler:
    def __init__(
        self,
        repository: CommandExecutionRepository,
        publisher: ResultPublisherPort,
    ) -> None:
        self._repository: CommandExecutionRepository = repository
        self._publisher: ResultPublisherPort = publisher

    async def handle(self, event: ChannelExecuteCompleteEvent) -> None:
        execution: CommandExecution | None = self._repository.get_by_id(event.job_uuid)
        if execution is None:
            raise UnknownExecutionError(event.job_uuid)

        self._apply_validation(execution, event)

        self._repository.save(execution)
        await self._publisher.publish_result(execution)

    @staticmethod
    def _apply_validation(
        execution: CommandExecution, event: ChannelExecuteCompleteEvent
    ) -> None:
        response: str = event.app_response.strip().upper()
        if response in _SUCCESS_RESPONSES:
            execution.mark_succeeded()
        else:
            execution.mark_failed(reason=event.app_response or "Unknown failure")
