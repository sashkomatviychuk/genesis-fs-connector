"""Базові абстракції для подій ESL.

Розділення на дві категорії за типом кореляції з CommandExecution:
- ExecutionCorrelatedEvent: відповідає на конкретну команду (є job_uuid).
- ChannelLifecycleEvent: подія життєвого циклу каналу, не прив'язана
  до конкретної команди.
"""

from __future__ import annotations

from abc import ABC
from enum import Enum


class EventType(str, Enum):
    CHANNEL_CREATE = "CHANNEL_CREATE"
    CHANNEL_EXECUTE_COMPLETE = "CHANNEL_EXECUTE_COMPLETE"
    CHANNEL_HANGUP_COMPLETE = "CHANNEL_HANGUP_COMPLETE"


class ChannelEvent(ABC):
    """Базовий клас для всіх подій ESL. channel_id (Unique-ID) є завжди."""

    type: EventType
    channel_id: str


class ExecutionCorrelatedEvent(ChannelEvent):
    """Події, що є прямою відповіддю на конкретну команду (мають job_uuid)."""

    job_uuid: str


class ChannelLifecycleEvent(ChannelEvent):
    """Події життєвого циклу каналу, не прив'язані до конкретної команди."""
