from __future__ import annotations

from myapp.domain.actions.answer_action import AnswerAction
from myapp.domain.commands import Command


class AnswerActionHandler:
    def build_command(self, action: AnswerAction) -> Command:
        return Command(application="answer", channel_id=action.channel_id, args="")
