"""Async-адаптер над greenswitch.InboundESL — реалізує FreeSwitchGatewayPort.

greenswitch — asyncio-native клієнт для FreeSwitch ESL (на відміну від
блокуючого python-ESL), встановлюється звичайним `pip install greenswitch`.

Примітка щодо job_uuid: замість того, щоб парсити відповідь FreeSwitch на
sendmsg, ми самі генеруємо job_uuid і передаємо його в заголовку
`Event-UUID`. Це стандартна поведінка протоколу ESL — FreeSwitch використає
саме це значення як Application-UUID у відповідній CHANNEL_EXECUTE_COMPLETE
події, тому кореляція гарантована незалежно від деталей конкретної
обгортки бібліотеки над сирим ESL-протоколом.
"""
from __future__ import annotations

import logging
import uuid as uuid_lib

import greenswitch

from myapp.domain.commands import Command

logger = logging.getLogger(__name__)


class EslConnectionError(RuntimeError):
    """Не вдалося встановити або підтримати Inbound ESL-з'єднання."""


class EslGateway:
    """Inbound ESL-з'єднання: система сама конектиться до FreeSwitch
    (mod_event_socket) і надсилає команди через InboundESL.
    """

    def __init__(self, host: str, port: int, password: str) -> None:
        self._host: str = host
        self._port: int = port
        self._password: str = password
        self._connection: greenswitch.InboundESL | None = None

    async def connect(self) -> None:
        self._connection = greenswitch.InboundESL(
            host=self._host, port=self._port, password=self._password
        )
        await self._connection.connect()
        logger.info("Connected to FreeSwitch ESL at %s:%s", self._host, self._port)

    @property
    def connection(self) -> greenswitch.InboundESL:
        if self._connection is None:
            raise EslConnectionError("ESL connection is not established, call connect() first")
        return self._connection

    async def send_command(self, command: Command) -> str:
        """Надсилає sendmsg execute на канал. Повертає job_uuid, згенерований
        клієнтом (див. docstring модуля щодо Event-UUID)."""
        job_uuid: str = str(uuid_lib.uuid4())
        message: str = (
            f"sendmsg {command.channel_id}\n"
            f"call-command: execute\n"
            f"execute-app-name: {command.application}\n"
            f"execute-app-arg: {command.args}\n"
            f"Event-UUID: {job_uuid}\n"
        )
        await self.connection.send(message)
        return job_uuid
