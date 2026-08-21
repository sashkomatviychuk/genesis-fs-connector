"""Абстракція репозиторію для CommandExecution (порт).

Залишається синхронною: in-memory реалізація не потребує I/O. Якщо
з'явиться async-клієнт (напр. redis.asyncio), інтерфейс можна буде
змінити на async — use case'и вже async і легко адаптуються (просто
додати await у виклики репозиторію).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from myapp.domain.entities import CommandExecution


class CommandExecutionRepository(ABC):
    @abstractmethod
    def get_by_id(self, job_uuid: str) -> CommandExecution | None:
        """Повертає CommandExecution за job_uuid або None, якщо не знайдено."""

    @abstractmethod
    def get_pending_by_channel_id(self, channel_id: str) -> list[CommandExecution]:
        """Повертає всі PENDING-виконання конкретного каналу (для batch-cancel
        при CHANNEL_HANGUP_COMPLETE)."""

    @abstractmethod
    def save(self, execution: CommandExecution) -> None:
        """Створює або оновлює запис виконання (upsert)."""
