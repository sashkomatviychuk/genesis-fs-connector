"""Мапінг сирої genesis-події -> доменний ChannelEvent.

Це єдине місце, що знає про конкретні заголовки протоколу ESL
(Event-Name, Application-UUID, Unique-ID тощо) — domain-класи подій
про них нічого не знають.

genesis представляє події та відповіді ESL як dict-подібні об'єкти
(документація показує голий dict на кшталт {'Content-Type': ...,
'Reply-Text': ...}), тому _header() спершу пробує `.get(name)`, а якщо
конкретна версія бібліотеки віддає щось з окремим атрибутом `.headers` —
підстраховується і цим шляхом.
"""
from __future__ import annotations

from typing import Any

from myapp.domain.events.base import ChannelEvent, EventType
from myapp.domain.events.channel_create import ChannelCreateEvent
from myapp.domain.events.channel_execute_complete import ChannelExecuteCompleteEvent
from myapp.domain.events.channel_hangup_complete import ChannelHangupCompleteEvent


def _header(raw_event: Any, name: str) -> str:
    get = getattr(raw_event, "get", None)
    if callable(get):
        value: str | None = get(name)
        return value or ""
    headers: dict[str, str] = getattr(raw_event, "headers", {})
    return headers.get(name) or ""


def map_esl_event(raw_event: Any) -> ChannelEvent | None:
    """Повертає None, якщо подія не з переліку EventType, які цікавлять
    систему — виклик коду вище тоді просто її ігнорує."""
    event_name: str = _header(raw_event, "Event-Name")
    channel_id: str = _header(raw_event, "Unique-ID")

    if event_name == EventType.CHANNEL_CREATE.value:
        return ChannelCreateEvent(
            channel_id=channel_id,
            caller_number=_header(raw_event, "Caller-Caller-ID-Number"),
            destination_number=_header(raw_event, "Caller-Destination-Number"),
        )

    if event_name == EventType.CHANNEL_EXECUTE_COMPLETE.value:
        return ChannelExecuteCompleteEvent(
            channel_id=channel_id,
            job_uuid=_header(raw_event, "Application-UUID"),
            application=_header(raw_event, "Application"),
            app_response=_header(raw_event, "Application-Response"),
        )

    if event_name == EventType.CHANNEL_HANGUP_COMPLETE.value:
        return ChannelHangupCompleteEvent(
            channel_id=channel_id,
            hangup_cause=_header(raw_event, "Hangup-Cause"),
        )

    return None
