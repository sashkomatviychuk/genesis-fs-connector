from __future__ import annotations

from myapp.domain.actions.hangup_action import HangupAction
from myapp.domain.commands import Command


class HangupActionHandler:
    def build_command(self, action: HangupAction) -> Command:
        return Command(application="hangup", channel_id=action.channel_id, args=action.cause)
