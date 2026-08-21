from __future__ import annotations

from dataclasses import dataclass

from myapp.domain.actions.base import Action, ActionType


@dataclass(frozen=True)
class AnswerAction(Action):
    type: ActionType = ActionType.ANSWER
    channel_id: str = ""

    def __post_init__(self) -> None:
        if not self.channel_id:
            raise ValueError("AnswerAction requires channel_id")
