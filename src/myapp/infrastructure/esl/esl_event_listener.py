"""Driving adapter: слухає Inbound ESL-подій через greenswitch і для кожної
релевантної події викликає HandleChannelEventUseCase.

greenswitch реєструє обробники через register_handle(event_name, callback)
і сам await-ить корутину-callback усередині свого внутрішнього event loop
(handle_events()) — тому _on_raw_event тут async, без потреби вручну
створювати asyncio.Task.
"""
from __future__ import annotations

import logging
from typing import Any

from myapp.application.use_cases.handle_channel_event import HandleChannelEventUseCase
from myapp.domain.events.base import ChannelEvent
from myapp.infrastructure.esl.esl_event_mapper import map_esl_event
from myapp.infrastructure.esl.esl_gateway import EslGateway

logger = logging.getLogger(__name__)

_SUBSCRIBED_EVENTS: tuple[str, ...] = (
    "CHANNEL_CREATE",
    "CHANNEL_EXECUTE_COMPLETE",
    "CHANNEL_HANGUP_COMPLETE",
)


class EslEventListener:
    def __init__(self, gateway: EslGateway, use_case: HandleChannelEventUseCase) -> None:
        self._gateway: EslGateway = gateway
        self._use_case: HandleChannelEventUseCase = use_case

    def _register_handlers(self) -> None:
        connection = self._gateway.connection
        for event_name in _SUBSCRIBED_EVENTS:
            connection.register_handle(event_name, self._on_raw_event)

    async def _on_raw_event(self, raw_event: Any) -> None:
        event: ChannelEvent | None = map_esl_event(raw_event)
        if event is None:
            return
        try:
            await self._use_case.execute(event)
        except Exception:
            logger.exception("Failed to handle ESL event: %s", event)

    async def run_forever(self) -> None:
        """Підписується на потрібні події та блокується в циклі обробки.
        У проді запускається як asyncio.Task, з reconnect-логікою при
        розриві з'єднання (тут не показано для стислості)."""
        self._register_handlers()
        connection = self._gateway.connection
        await connection.send("event plain " + " ".join(_SUBSCRIBED_EVENTS))
        await connection.handle_events()
