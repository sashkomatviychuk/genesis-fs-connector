from __future__ import annotations

from dataclasses import dataclass

from myapp.domain.events.base import ChannelLifecycleEvent, EventType


@dataclass(frozen=True)
class ChannelCreateEvent(ChannelLifecycleEvent):
    type: EventType = EventType.CHANNEL_CREATE
    channel_id: str = ""
    caller_number: str = ""
    destination_number: str = ""
