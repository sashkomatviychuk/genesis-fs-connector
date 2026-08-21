"""Реалізація ResultPublisherPort.

StubResultPublisher — мінімальна демонстраційна async-реалізація (лог
замість реального брокера). У проді замінюється на конкретний async-адаптер
(aio-pika/aiokafka/aiobotocore SQS) з такою ж сигнатурою publish_result().
"""
from __future__ import annotations

import dataclasses
import logging
from typing import Any

from myapp.domain.entities import CommandExecution
from myapp.domain.value_objects import ResultPayload

logger = logging.getLogger(__name__)


class StubResultPublisher:
    async def publish_result(
        self, execution: CommandExecution, payload: ResultPayload | None = None
    ) -> None:
        message: dict[str, Any] = {
            "job_uuid": execution.id,
            "channel_id": execution.channel_id,
            "status": execution.status.value,
            "reason": execution.failure_reason,
        }
        if payload is not None:
            # payload — dataclass (конкретний підклас ResultPayload),
            # asdict() коректно розгортає його поля для логу/серіалізації.
            message.update(dataclasses.asdict(payload))
        logger.info("Publishing execution result: %s", message)
