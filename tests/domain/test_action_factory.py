"""Tests for myapp.domain.actions.factory.action_from_payload."""

from __future__ import annotations

from typing import Any

import pytest

from myapp.domain.actions.answer_action import AnswerAction
from myapp.domain.actions.base import Action
from myapp.domain.actions.bridge_action import BridgeAction
from myapp.domain.actions.factory import action_from_payload
from myapp.domain.actions.hangup_action import HangupAction
from myapp.domain.actions.playback_action import PlaybackAction
from myapp.domain.exceptions import UnknownActionTypeError


def test_answer_payload_builds_answer_action(answer_action_payload: dict[str, Any]) -> None:
    action = action_from_payload(answer_action_payload)

    assert isinstance(action, AnswerAction)
    assert action.channel_id == "chan-1"


def test_playback_payload_builds_playback_action(playback_action_payload: dict[str, Any]) -> None:
    action = action_from_payload(playback_action_payload)

    assert isinstance(action, PlaybackAction)
    assert action.file_path == "/sounds/welcome.wav"
    assert action.loop is False


def test_bridge_payload_builds_bridge_action(bridge_action_payload: dict[str, Any]) -> None:
    action = action_from_payload(bridge_action_payload)

    assert isinstance(action, BridgeAction)
    assert action.destination == "user/1001"
    assert action.timeout_sec == 30


def test_hangup_payload_builds_hangup_action(hangup_action_payload: dict[str, Any]) -> None:
    action = action_from_payload(hangup_action_payload)

    assert isinstance(action, HangupAction)
    assert action.cause == "NORMAL_CLEARING"


def test_any_action_payload_round_trips_channel_id(any_action_payload: dict[str, Any]) -> None:
    """Every action type shares channel_id — one parametrized test covers all of them."""
    action: Action = action_from_payload(any_action_payload)

    assert action.channel_id == any_action_payload["channel_id"]


def test_unknown_type_raises_domain_error() -> None:
    with pytest.raises(UnknownActionTypeError):
        action_from_payload({"type": "DANCE", "channel_id": "chan-1"})


def test_missing_required_field_raises_value_error(playback_action_payload: dict[str, Any]) -> None:
    del playback_action_payload["file_path"]

    with pytest.raises(ValueError, match="file_path"):
        action_from_payload(playback_action_payload)
