"""Shared pytest fixtures.

Fixtures here provide raw ``dict`` payloads (the shape that arrives from the
inbound Action queue / ESL events, before being parsed into typed domain
objects) so tests for factories, mappers, and use cases don't each hand-roll
their own dicts.
"""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def answer_action_payload() -> dict[str, Any]:
    return {"type": "ANSWER", "channel_id": "chan-1"}


@pytest.fixture
def playback_action_payload() -> dict[str, Any]:
    return {
        "type": "PLAYBACK",
        "channel_id": "chan-1",
        "file_path": "/sounds/welcome.wav",
        "loop": False,
    }


@pytest.fixture
def bridge_action_payload() -> dict[str, Any]:
    return {
        "type": "BRIDGE",
        "channel_id": "chan-1",
        "destination": "user/1001",
        "timeout_sec": 30,
    }


@pytest.fixture
def hangup_action_payload() -> dict[str, Any]:
    return {"type": "HANGUP", "channel_id": "chan-1", "cause": "NORMAL_CLEARING"}


@pytest.fixture(
    params=[
        "answer_action_payload",
        "playback_action_payload",
        "bridge_action_payload",
        "hangup_action_payload",
    ]
)
def any_action_payload(request: pytest.FixtureRequest) -> dict[str, Any]:
    """Parametrized over every known Action payload — use to test logic that
    should behave the same across all action types (e.g. `channel_id` handling
    in `action_from_payload`)."""
    return request.getfixturevalue(request.param)
