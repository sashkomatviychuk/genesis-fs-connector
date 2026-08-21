"""Use case: виконати Action.

Диспетчеризує через словник action_handlers (registry, зібраний у DI
контейнері). Async — бо send_command() іде через greenswitch (asyncio I/O).
"""
from __future__ import annotations

from myapp.application.action_handlers.base import ActionHandler
from myapp.application.ports import FreeSwitchGatewayPort
from myapp.domain.actions.base import Action, ActionType
from myapp.domain.commands import Command
from myapp.domain.entities import CommandExecution
from myapp.domain.exceptions import UnknownActionTypeError
from myapp.domain.repositories import CommandExecutionRepository


class ExecuteActionUseCase:
    def __init__(
        self,
        repository: CommandExecutionRepository,
        gateway: FreeSwitchGatewayPort,
        action_handlers: dict[ActionType, ActionHandler],
    ) -> None:
        self._repository: CommandExecutionRepository = repository
        self._gateway: FreeSwitchGatewayPort = gateway
        self._action_handlers: dict[ActionType, ActionHandler] = action_handlers

    async def execute(self, action: Action) -> str:
        handler: ActionHandler | None = self._action_handlers.get(action.type)
        if handler is None:
            raise UnknownActionTypeError(str(action.type))

        command: Command = handler.build_command(action)
        job_uuid: str = await self._gateway.send_command(command)

        execution: CommandExecution = CommandExecution.pending(
            id=job_uuid, channel_id=action.channel_id, action=action
        )
        self._repository.save(execution)

        return job_uuid
