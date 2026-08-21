"""Driving adapter: слухає ESL-події через genesis.Consumer і для кожної
релевантної події викликає HandleChannelEventUseCase.

genesis.Consumer керує власним ESL-з'єднанням (окремим від того, яке
EslGateway використовує для відправки команд) і реєструє обробники подій
декларативно через `@app.handle("EVENT_NAME")`. Ми реєструємо той самий
callback для кожної цікавої нам події — сам callback лише мапить сирий
event у domain-об'єкт і делегує його use case'у; конкретна доменна
диспетчеризація за event.type відбувається вже всередині
HandleChannelEventUseCase.
"""
from __future__ import annotations

import logging
from typing import Any

from genesis import Consumer

from myapp.application.use_cases.handle_channel_event import HandleChannelEventUseCase
from myapp.domain.events.base import ChannelEvent
from myapp.infrastructure.esl.esl_event_mapper import map_esl_event

logger = logging.getLogger(__name__)

_SUBSCRIBED_EVENTS: tuple[str, ...] = (
    "CHANNEL_CREATE",
    "CHANNEL_EXECUTE_COMPLETE",
    "CHANNEL_HANGUP_COMPLETE",
)


class EslEventListener:
    def __init__(
        self,
        host: str,
        port: int,
        password: str,
        use_case: HandleChannelEventUseCase,
    ) -> None:
        self._use_case: HandleChannelEventUseCase = use_case
        self._app: Consumer = Consumer(host, port, password)
        self._register_handlers()

    def _register_handlers(self) -> None:
        for event_name in _SUBSCRIBED_EVENTS:
            self._app.handle(event_name)(self._on_raw_event)

    async def _on_raw_event(self, raw_event: Any) -> None:
        event: ChannelEvent | None = map_esl_event(raw_event)
        if event is None:
            return
        try:
            await self._use_case.execute(event)
        except Exception:
            logger.exception("Failed to handle ESL event: %s", event)

    async def run_forever(self) -> None:
        """Підключається і блокується в циклі обробки подій."""
        logger.info("Starting ESL event listener (genesis.Consumer)...")
        await self._app.start()
