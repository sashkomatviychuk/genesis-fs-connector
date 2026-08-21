from __future__ import annotations

from dataclasses import dataclass

from myapp.domain.actions.base import Action, ActionType


@dataclass(frozen=True)
class HangupAction(Action):
    type: ActionType = ActionType.HANGUP
    channel_id: str = ""
    cause: str = "NORMAL_CLEARING"

    def __post_init__(self) -> None:
        if not self.channel_id:
            raise ValueError("HangupAction requires channel_id")
