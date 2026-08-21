"""Use case: обробити подію ESL.

Тонкий async-диспетчер: знаходить handler по event.type у словнику
event_handlers і делегує йому всю роботу.
"""

from __future__ import annotations

from myapp.application.event_handlers.base import EventHandler
from myapp.domain.events.base import ChannelEvent, EventType


class HandleChannelEventUseCase:
    def __init__(self, event_handlers: dict[EventType, EventHandler]) -> None:
        self._event_handlers: dict[EventType, EventHandler] = event_handlers

    async def execute(self, event: ChannelEvent) -> None:
        handler: EventHandler | None = self._event_handlers.get(event.type)
        if handler is None:
            return
        await handler.handle(event)
