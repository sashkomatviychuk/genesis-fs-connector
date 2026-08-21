"""Async-адаптер над genesis.Inbound — реалізує FreeSwitchGatewayPort.

genesis — asyncio-native клієнт для FreeSwitch ESL (на відміну від
gevent-based greenswitch), встановлюється звичайним `pip install genesis`.
Реальний API: `Inbound` використовується як async context manager
(`async with Inbound(host, port, password) as client: await client.send(...)`).
Тривале з'єднання на весь час роботи застосунку отримуємо, тримаючи
`async with` відкритим у DI Resource-провайдері (див. containers.py).

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

from genesis import Inbound

from myapp.domain.commands import Command

logger = logging.getLogger(__name__)


class EslGateway:
    """Тонка обгортка над уже підключеним genesis.Inbound-клієнтом.

    Інстанс клієнта створюється й підключається в DI-контейнері
    (providers.Resource, `async with Inbound(...) as client: yield ...`) —
    EslGateway тут лише використовує вже готове з'єднання для відправки
    команд, не керує його life-cycle самостійно.
    """

    def __init__(self, client: Inbound) -> None:
        self._client: Inbound = client

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
        await self._client.send(message)
        return job_uuid
