"""Реалізація ResultPublisherPort.

StubResultPublisher — мінімальна демонстраційна async-реалізація (лог
замість реального брокера). У проді замінюється на конкретний async-адаптер
(aio-pika/aiokafka/aiobotocore SQS) з такою ж сигнатурою publish_result().
"""
from __future__ import annotations

import logging
from typing import Any

from myapp.domain.entities import CommandExecution

logger = logging.getLogger(__name__)


class StubResultPublisher:
    async def publish_result(self, execution: CommandExecution) -> None:
        payload: dict[str, Any] = {
            "job_uuid": execution.id,
            "channel_id": execution.channel_id,
            "status": execution.status.value,
            "reason": execution.failure_reason,
        }
        logger.info("Publishing execution result: %s", payload)
