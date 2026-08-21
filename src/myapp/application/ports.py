"""Ports application-шару — інтерфейси зовнішніх залежностей use case'ів.

Обидва порти асинхронні: FreeSwitchGatewayPort реалізується через greenswitch
(asyncio-native клієнт ESL), ResultPublisherPort — через асинхронний клієнт
черги (aio-pika/aiokafka тощо).
"""

from __future__ import annotations

from typing import Protocol

from myapp.domain.commands import Command
from myapp.domain.entities import CommandExecution


class FreeSwitchGatewayPort(Protocol):
    async def send_command(self, command: Command) -> str:
        """Надсилає команду в FreeSwitch, повертає job_uuid, по якому пізніше
        прийде CHANNEL_EXECUTE_COMPLETE."""
        ...


class ResultPublisherPort(Protocol):
    async def publish_result(self, execution: CommandExecution) -> None:
        """Публікує success/failed результат виконання команди у вихідну чергу."""
        ...
