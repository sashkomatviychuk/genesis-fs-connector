from __future__ import annotations

from myapp.domain.actions.playback_action import PlaybackAction
from myapp.domain.commands import Command


class PlaybackActionHandler:
    def build_command(self, action: PlaybackAction) -> Command:
        args: str = action.file_path
        if action.loop:
            args = f"loop {args}"
        return Command(application="playback", channel_id=action.channel_id, args=args)
