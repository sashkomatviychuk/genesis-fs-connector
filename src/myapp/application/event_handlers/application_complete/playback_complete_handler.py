"""Обробник CHANNEL_EXECUTE_COMPLETE для application="playback".

Власні критерії success ("FILE PLAYED"), власний payload (включно з
file_path, який брали з початкового PlaybackAction), публікація і
очищення execution.
"""

from __future__ import annotations

from myapp.application.ports import ResultPublisherPort
from myapp.domain.actions.playback_action import PlaybackAction
from myapp.domain.entities import CommandExecution
from myapp.domain.events.channel_execute_complete import ChannelExecuteCompleteEvent
from myapp.domain.repositories import CommandExecutionRepository
from myapp.domain.value_objects import PlaybackResultPayload

_SUCCESS_RESPONSES: frozenset[str] = frozenset({"FILE PLAYED", "SUCCESS"})


class PlaybackCompleteHandler:
    def __init__(
        self,
        repository: CommandExecutionRepository,
        publisher: ResultPublisherPort,
    ) -> None:
        self._repository: CommandExecutionRepository = repository
        self._publisher: ResultPublisherPort = publisher

    async def handle(self, event: ChannelExecuteCompleteEvent, execution: CommandExecution) -> None:
        self._apply_validation(execution, event)

        payload: PlaybackResultPayload = self._build_payload(execution)
        await self._publisher.publish_result(execution, payload)

        self._repository.delete(execution.id)

    @staticmethod
    def _apply_validation(execution: CommandExecution, event: ChannelExecuteCompleteEvent) -> None:
        response: str = event.app_response.strip().upper()
        if response in _SUCCESS_RESPONSES:
            execution.mark_succeeded()
        else:
            execution.mark_failed(reason=event.app_response or "Unknown failure")

    @staticmethod
    def _build_payload(execution: CommandExecution) -> PlaybackResultPayload:
        action = execution.action
        file_path: str = action.file_path if isinstance(action, PlaybackAction) else ""
        return PlaybackResultPayload(channel_id=execution.channel_id, file_path=file_path)
