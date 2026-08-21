"""Обробник CHANNEL_CREATE.

Ця подія не корелює з жодною командою (немає job_uuid) — не потребує
CommandExecutionRepository.
"""
from __future__ import annotations

import logging

from myapp.domain.events.channel_create import ChannelCreateEvent

logger = logging.getLogger(__name__)


class ChannelCreateHandler:
    async def handle(self, event: ChannelCreateEvent) -> None:
        logger.info(
            "Channel created: id=%s from=%s to=%s",
            event.channel_id,
            event.caller_number,
            event.destination_number,
        )
