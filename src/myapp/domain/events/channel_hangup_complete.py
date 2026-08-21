from __future__ import annotations

from dataclasses import dataclass

from myapp.domain.events.base import ChannelLifecycleEvent, EventType


@dataclass(frozen=True)
class ChannelHangupCompleteEvent(ChannelLifecycleEvent):
    type: EventType = EventType.CHANNEL_HANGUP_COMPLETE
    channel_id: str = ""
    hangup_cause: str = ""
