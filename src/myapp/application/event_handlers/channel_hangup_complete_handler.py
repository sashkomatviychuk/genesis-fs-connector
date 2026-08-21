"""Обробник CHANNEL_HANGUP_COMPLETE.

Закриває всі PENDING execution'и каналу, що так і не отримали
CHANNEL_EXECUTE_COMPLETE до завершення каналу — запобігає orphaned
pending-записам.
"""
from __future__ import annotations

from myapp.application.ports import ResultPublisherPort
from myapp.domain.entities import CommandExecution
from myapp.domain.events.channel_hangup_complete import ChannelHangupCompleteEvent
from myapp.domain.repositories import CommandExecutionRepository


class ChannelHangupCompleteHandler:
    def __init__(
        self,
        repository: CommandExecutionRepository,
        publisher: ResultPublisherPort,
    ) -> None:
        self._repository: CommandExecutionRepository = repository
        self._publisher: ResultPublisherPort = publisher

    async def handle(self, event: ChannelHangupCompleteEvent) -> None:
        pending: list[CommandExecution] = self._repository.get_pending_by_channel_id(
            event.channel_id
        )

        for execution in pending:
            execution.mark_cancelled(reason=f"Channel hangup: {event.hangup_cause}")
            self._repository.save(execution)
            await self._publisher.publish_result(execution)
