from __future__ import annotations

from dataclasses import dataclass

from myapp.domain.actions.base import Action, ActionType


@dataclass(frozen=True)
class BridgeAction(Action):
    type: ActionType = ActionType.BRIDGE
    channel_id: str = ""
    destination: str = ""
    timeout_sec: int = 30

    def __post_init__(self) -> None:
        if not self.channel_id:
            raise ValueError("BridgeAction requires channel_id")
        if not self.destination:
            raise ValueError("BridgeAction requires destination")
        if self.timeout_sec <= 0:
            raise ValueError("BridgeAction timeout_sec must be positive")
