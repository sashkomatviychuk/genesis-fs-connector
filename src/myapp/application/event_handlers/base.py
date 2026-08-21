from __future__ import annotations

from typing import Protocol

from myapp.domain.events.base import ChannelEvent


class EventHandler(Protocol):
    async def handle(self, event: ChannelEvent) -> None:
        """Кожен handler сам вирішує, чи потрібен йому CommandExecutionRepository
        чи ResultPublisherPort — резолвинг залежностей живе всередині handler'а,
        не в use case, бо різні події мають різну форму кореляції зі станом."""
        ...
