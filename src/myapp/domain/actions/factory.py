"""Фабрика для перетворення сирого payload (dict) у конкретний доменний Action."""

from __future__ import annotations

from typing import Any

from myapp.domain.actions.answer_action import AnswerAction
from myapp.domain.actions.base import Action, ActionType
from myapp.domain.actions.bridge_action import BridgeAction
from myapp.domain.actions.hangup_action import HangupAction
from myapp.domain.actions.playback_action import PlaybackAction
from myapp.domain.exceptions import UnknownActionTypeError

_ACTION_CLASSES: dict[ActionType, type[Action]] = {
    ActionType.ANSWER: AnswerAction,
    ActionType.PLAYBACK: PlaybackAction,
    ActionType.BRIDGE: BridgeAction,
    ActionType.HANGUP: HangupAction,
}


def action_from_payload(payload: dict[str, Any]) -> Action:
    """payload приклад: {"type": "PLAYBACK", "channel_id": "...", "file_path": "..."}"""
    raw_type: Any = payload.get("type")
    try:
        action_type = ActionType(raw_type)
    except ValueError as exc:
        raise UnknownActionTypeError(str(raw_type)) from exc

    action_cls: type[Action] = _ACTION_CLASSES[action_type]
    kwargs: dict[str, Any] = {k: v for k, v in payload.items() if k != "type"}
    return action_cls(**kwargs)
