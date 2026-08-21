"""Composition root, побудований через dependency-injector.

esl_gateway зібраний як providers.Resource — асинхронний provider, що
викликає await gateway.connect() один раз при container.init_resources()
і повертає вже підключений інстанс. Це ідіоматичний спосіб dependency-injector
керувати ресурсами з асинхронною ініціалізацією/завершенням роботи.
"""
from __future__ import annotations

from collections.abc import AsyncIterator

from dependency_injector import containers, providers
from genesis import Inbound

from myapp.application.action_handlers.answer_handler import AnswerActionHandler
from myapp.application.action_handlers.base import ActionHandler
from myapp.application.action_handlers.bridge_handler import BridgeActionHandler
from myapp.application.action_handlers.hangup_handler import HangupActionHandler
from myapp.application.action_handlers.playback_handler import PlaybackActionHandler
from myapp.application.event_handlers.application_complete.answer_complete_handler import (
    AnswerCompleteHandler,
)
from myapp.application.event_handlers.application_complete.base import (
    ApplicationCompleteHandler,
)
from myapp.application.event_handlers.application_complete.playback_complete_handler import (
    PlaybackCompleteHandler,
)
from myapp.application.event_handlers.base import EventHandler
from myapp.application.event_handlers.channel_create_handler import ChannelCreateHandler
from myapp.application.event_handlers.channel_execute_complete_handler import (
    ChannelExecuteCompleteHandler,
)
from myapp.application.event_handlers.channel_hangup_complete_handler import (
    ChannelHangupCompleteHandler,
)
from myapp.application.use_cases.execute_action import ExecuteActionUseCase
from myapp.application.use_cases.handle_channel_event import HandleChannelEventUseCase
from myapp.domain.actions.base import ActionType
from myapp.domain.events.base import EventType
from myapp.infrastructure.esl.esl_event_listener import EslEventListener
from myapp.infrastructure.esl.esl_gateway import EslGateway
from myapp.infrastructure.queue.result_publisher import StubResultPublisher
from myapp.infrastructure.repositories.in_memory_execution_repository import (
    InMemoryCommandExecutionRepository,
)
from myapp.presentation.action_consumer import ActionQueueConsumer


async def _init_esl_gateway(host: str, port: int, password: str) -> AsyncIterator[EslGateway]:
    """Async-ініціалізатор для providers.Resource.

    genesis.Inbound — асинхронний контекст-менеджер; тримаємо `async with`
    відкритим для всього часу життя застосунку через генератор з yield
    всередині блоку. Код після yield виконується при
    container.shutdown_resources() — саме там genesis коректно закриє
    з'єднання через __aexit__.
    """
    async with Inbound(host, port, password) as client:
        yield EslGateway(client)


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # ---- infrastructure -------------------------------------------------
    execution_repository = providers.Singleton(InMemoryCommandExecutionRepository)

    result_publisher = providers.Singleton(StubResultPublisher)

    esl_gateway = providers.Resource(
        _init_esl_gateway,
        host=config.esl.host,
        port=config.esl.port,
        password=config.esl.password,
    )

    # ---- action handlers registry ---------------------------------------
    answer_action_handler = providers.Singleton(AnswerActionHandler)
    playback_action_handler = providers.Singleton(PlaybackActionHandler)
    bridge_action_handler = providers.Singleton(BridgeActionHandler)
    hangup_action_handler = providers.Singleton(HangupActionHandler)

    action_handlers: providers.Dict[ActionType, ActionHandler] = providers.Dict(
        {
            ActionType.ANSWER: answer_action_handler,
            ActionType.PLAYBACK: playback_action_handler,
            ActionType.BRIDGE: bridge_action_handler,
            ActionType.HANGUP: hangup_action_handler,
        }
    )

    # ---- CHANNEL_EXECUTE_COMPLETE: per-application handlers registry -----
    answer_complete_handler = providers.Singleton(
        AnswerCompleteHandler,
        repository=execution_repository,
        publisher=result_publisher,
    )

    playback_complete_handler = providers.Singleton(
        PlaybackCompleteHandler,
        repository=execution_repository,
        publisher=result_publisher,
    )

    application_complete_handlers: providers.Dict[str, ApplicationCompleteHandler] = (
        providers.Dict(
            {
                "answer": answer_complete_handler,
                "playback": playback_complete_handler,
            }
        )
    )

    # ---- event handlers registry ------------------------------------------
    channel_create_handler = providers.Singleton(ChannelCreateHandler)

    channel_execute_complete_handler = providers.Singleton(
        ChannelExecuteCompleteHandler,
        repository=execution_repository,
        application_handlers=application_complete_handlers,
    )

    channel_hangup_complete_handler = providers.Singleton(
        ChannelHangupCompleteHandler,
        repository=execution_repository,
        publisher=result_publisher,
    )

    event_handlers: providers.Dict[EventType, EventHandler] = providers.Dict(
        {
            EventType.CHANNEL_CREATE: channel_create_handler,
            EventType.CHANNEL_EXECUTE_COMPLETE: channel_execute_complete_handler,
            EventType.CHANNEL_HANGUP_COMPLETE: channel_hangup_complete_handler,
        }
    )

    # ---- use cases ----------------------------------------------------------
    execute_action_use_case = providers.Factory(
        ExecuteActionUseCase,
        repository=execution_repository,
        gateway=esl_gateway,
        action_handlers=action_handlers,
    )

    handle_channel_event_use_case = providers.Factory(
        HandleChannelEventUseCase,
        event_handlers=event_handlers,
    )

    # ---- ESL event listener (окреме genesis.Consumer з'єднання) -------------
    esl_event_listener = providers.Factory(
        EslEventListener,
        host=config.esl.host,
        port=config.esl.port,
        password=config.esl.password,
        use_case=handle_channel_event_use_case,
    )

    # ---- presentation -------------------------------------------------------
    action_consumer = providers.Factory(
        ActionQueueConsumer,
        use_case=execute_action_use_case,
    )
