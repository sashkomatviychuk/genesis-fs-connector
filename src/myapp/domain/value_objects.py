"""ValidationResult — Value Object з результатом валідації виконання команди.

ResultPayload — базовий клас для application-специфічних payload, що
публікуються разом з результатом виконання команди. Кожен FreeSwitch
application (answer/playback/...) має власний набір полів, тому це не
один спільний dict[str, Any], а власний dataclass на кожен тип — так само,
як Action чи ChannelEvent мають власні підкласи на кожен конкретний тип.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationResult:
    execution_id: str
    is_success: bool
    reason: str | None = None

    @classmethod
    def success(cls, execution_id: str) -> "ValidationResult":
        return cls(execution_id=execution_id, is_success=True)

    @classmethod
    def failure(cls, execution_id: str, reason: str) -> "ValidationResult":
        return cls(execution_id=execution_id, is_success=False, reason=reason)


class ResultPayload(ABC):
    """Базовий клас для payload, що публікується разом з результатом
    CommandExecution. application — назва FreeSwitch application, за якою
    ChannelExecuteCompleteHandler і публікатор можуть відрізняти типи."""

    application: str


@dataclass(frozen=True)
class AnswerResultPayload(ResultPayload):
    application: str = "answer"
    channel_id: str = ""


@dataclass(frozen=True)
class PlaybackResultPayload(ResultPayload):
    application: str = "playback"
    channel_id: str = ""
    file_path: str = ""
