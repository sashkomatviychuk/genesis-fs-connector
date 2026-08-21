"""Обробник CHANNEL_EXECUTE_COMPLETE — верхньорівневий диспетчер.

Знаходить CommandExecution по job_uuid і делегує подальшу обробку
конкретному ApplicationCompleteHandler'у за event.application
(answer/playback/...) — кожен application має власну логіку валідації,
побудови payload і критеріїв success/failure.

Якщо execution не знайдено (job_uuid невідомий — подія вже оброблена
раніше, дублікат, чи прийшла з чужого джерела) — це не помилка процесу,
а нормальна ситуація: подія просто ігнорується (skip), без винятку.
"""

from __future__ import annotations

import logging

from myapp.application.event_handlers.application_complete.base import (
    ApplicationCompleteHandler,
)
from myapp.domain.entities import CommandExecution
from myapp.domain.events.channel_execute_complete import ChannelExecuteCompleteEvent
from myapp.domain.repositories import CommandExecutionRepository

logger = logging.getLogger(__name__)


class ChannelExecuteCompleteHandler:
    def __init__(
        self,
        repository: CommandExecutionRepository,
        application_handlers: dict[str, ApplicationCompleteHandler],
    ) -> None:
        self._repository: CommandExecutionRepository = repository
        self._application_handlers: dict[str, ApplicationCompleteHandler] = application_handlers

    async def handle(self, event: ChannelExecuteCompleteEvent) -> None:
        execution: CommandExecution | None = self._repository.get_by_id(event.job_uuid)
        if execution is None:
            logger.info(
                "No pending execution for job_uuid=%s (already processed or "
                "unknown source) — skipping",
                event.job_uuid,
            )
            return

        handler = self._application_handlers.get(event.application)
        if handler is None:
            logger.warning(
                "No ApplicationCompleteHandler registered for application=%r "
                "(job_uuid=%s) — skipping",
                event.application,
                event.job_uuid,
            )
            return

        await handler.handle(event, execution)
