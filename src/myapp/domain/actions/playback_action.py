from __future__ import annotations

from dataclasses import dataclass

from myapp.domain.actions.base import Action, ActionType


@dataclass(frozen=True)
class PlaybackAction(Action):
    type: ActionType = ActionType.PLAYBACK
    channel_id: str = ""
    file_path: str = ""
    loop: bool = False

    def __post_init__(self) -> None:
        if not self.channel_id:
            raise ValueError("PlaybackAction requires channel_id")
        if not self.file_path:
            raise ValueError("PlaybackAction requires file_path")
