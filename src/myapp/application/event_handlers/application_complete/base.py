"""Protocol для per-application обробника CHANNEL_EXECUTE_COMPLETE.

На відміну від верхньорівневого EventHandler (диспетчеризація за
event.type — CHANNEL_CREATE/CHANNEL_EXECUTE_COMPLETE/CHANNEL_HANGUP_COMPLETE),
ApplicationCompleteHandler диспетчеризується за event.application
(answer/playback/bridge/...) — кожен FreeSwitch-application має власну
логіку побудови payload і власні критерії success/failure.
"""
from __future__ import annotations

from typing import Protocol

from myapp.domain.entities import CommandExecution
from myapp.domain.events.channel_execute_complete import ChannelExecuteCompleteEvent


class ApplicationCompleteHandler(Protocol):
    async def handle(
        self, event: ChannelExecuteCompleteEvent, execution: CommandExecution
    ) -> None:
        """Валідує результат, будує application-специфічний payload, публікує
        його та очищує (видаляє) execution з репозиторію — його роль
        (кореляція команда↔подія) вичерпана після обробки цієї події."""
        ...
