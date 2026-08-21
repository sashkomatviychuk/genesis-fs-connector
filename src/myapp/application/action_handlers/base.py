from __future__ import annotations

from typing import Protocol

from myapp.domain.actions.base import Action
from myapp.domain.commands import Command


class ActionHandler(Protocol):
    def build_command(self, action: Action) -> Command:
        """Перетворює Action (намір) на Command. Синхронний метод — це чиста
        CPU-логіка без I/O, async тут не додає жодної користі."""
        ...
