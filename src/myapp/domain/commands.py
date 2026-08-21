"""Command — Value Object, що описує реальну ESL-інструкцію
(application + args на конкретному каналі)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Command:
    application: str
    channel_id: str
    args: str = ""
