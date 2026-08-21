from __future__ import annotations

from dataclasses import dataclass

from myapp.domain.events.base import EventType, ExecutionCorrelatedEvent


@dataclass(frozen=True)
class ChannelExecuteCompleteEvent(ExecutionCorrelatedEvent):
    type: EventType = EventType.CHANNEL_EXECUTE_COMPLETE
    channel_id: str = ""
    job_uuid: str = ""
    application: str = ""
    app_response: str = ""
