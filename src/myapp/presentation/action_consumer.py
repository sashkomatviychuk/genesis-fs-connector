"""Driving adapter: приймає сирі повідомлення (Action) із зовнішньої
вхідної черги і викликає ExecuteActionUseCase.

Конкретний брокер (RabbitMQ/Kafka/SQS) навмисно не прив'язаний тут —
handle_message() приймає вже розпарсений dict; підключення до реального
async-брокера і виклик handle_message() у callback'у відбувається в
infrastructure-шарі (залежить від обраного брокера).
"""
from __future__ import annotations

import logging
from typing import Any

from myapp.application.use_cases.execute_action import ExecuteActionUseCase
from myapp.domain.actions.base import Action
from myapp.domain.actions.factory import action_from_payload
from myapp.domain.exceptions import DomainError

logger = logging.getLogger(__name__)


class ActionQueueConsumer:
    def __init__(self, use_case: ExecuteActionUseCase) -> None:
        self._use_case: ExecuteActionUseCase = use_case

    async def handle_message(self, payload: dict[str, Any]) -> None:
        try:
            action: Action = action_from_payload(payload)
        except DomainError:
            logger.exception("Failed to parse action payload: %s", payload)
            return

        try:
            job_uuid: str = await self._use_case.execute(action)
        except DomainError:
            logger.exception("Failed to execute action: %s", action)
            return

        logger.info("Action %s dispatched, job_uuid=%s", action.type, job_uuid)
