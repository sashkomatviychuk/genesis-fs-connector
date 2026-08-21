"""Базові абстракції для Action."""

from __future__ import annotations

from abc import ABC
from enum import Enum


class ActionType(str, Enum):
    ANSWER = "ANSWER"
    PLAYBACK = "PLAYBACK"
    BRIDGE = "BRIDGE"
    HANGUP = "HANGUP"


class Action(ABC):
    """Базовий клас для всіх Action. channel_id присутній завжди."""

    type: ActionType
    channel_id: str
