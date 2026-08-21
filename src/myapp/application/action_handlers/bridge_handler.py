from __future__ import annotations

from myapp.domain.actions.bridge_action import BridgeAction
from myapp.domain.commands import Command


class BridgeActionHandler:
    def build_command(self, action: BridgeAction) -> Command:
        args: str = f"{action.destination}?timeout={action.timeout_sec}"
        return Command(application="bridge", channel_id=action.channel_id, args=args)
