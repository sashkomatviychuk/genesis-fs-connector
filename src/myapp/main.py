"""Точка входу застосунку.

Конфігурація завантажується з config/config-{APP_ENV}.yaml (dev/prod/...).
Піднімає DI-контейнер (dependency-injector), ініціалізує async-ресурси
(EslGateway.connect() через providers.Resource) і запускає ESL event listener.
"""

from __future__ import annotations

import asyncio
import logging
import os

from myapp.containers import Container

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_container() -> Container:
    container = Container()
    env: str = os.getenv("APP_ENV", "dev")
    config_path: str = f"config/config-{env}.yaml"
    container.config.from_yaml(config_path)
    logger.info("Loaded configuration from %s", config_path)
    return container


async def main() -> None:
    container: Container = create_container()

    # Ініціалізує всі providers.Resource у контейнері — тут це esl_gateway,
    # чий async-ініціалізатор (_init_esl_gateway) відкриває genesis.Inbound
    # через `async with` і тримає з'єднання відкритим до shutdown_resources().
    await container.init_resources()  # type: ignore[misc]

    try:
        listener = container.esl_event_listener()

        # У реальному проєкті тут паралельно (asyncio.gather) піднімається
        # ActionQueueConsumer, підписаний на конкретний async-брокер
        # (aio-pika/aiokafka), який на кожне вхідне повідомлення викликає
        # await container.action_consumer().handle_message(payload).
        await listener.run_forever()
    finally:
        await container.shutdown_resources()  # type: ignore[misc]


if __name__ == "__main__":
    asyncio.run(main())
