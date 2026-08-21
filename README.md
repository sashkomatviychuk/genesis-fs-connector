# ESL Controller — Async Hexagonal Architecture (greenswitch + dependency-injector)

Async-версія міні-застосунку для керування FreeSwitch через **ESL Inbound**.
Приймає Action-и (PLAYBACK, BRIDGE, HANGUP), формує та надсилає команди,
слухає події каналу (`CHANNEL_CREATE`, `CHANNEL_EXECUTE_COMPLETE`,
`CHANNEL_HANGUP_COMPLETE`), робить міні-валідацію та публікує
success/failed результат у вихідну чергу.

Зміни відносно попередньої (sync) версії:

1. **greenswitch** замість python-ESL — asyncio-native клієнт ESL,
   встановлюється звичайним `pip install` (на відміну від python-ESL,
   що збирається з FreeSwitch source).
2. **Конфігурація з `config/config-{APP_ENV}.yaml`** — через
   `dependency-injector`'s `container.config.from_yaml(...)`.
3. **Повна типізація** — усі функції, методи, атрибути й змінні мають
   явні type hints.

Тести в цій версії навмисно не включені.

## Структура проєкту

```
config/
├── config-dev.yaml
└── config-prod.yaml

src/myapp/
├── domain/                          # Ядро — без залежностей від ESL/DI/черги
│   ├── actions/
│   │   ├── base.py                  # Action (ABC), ActionType
│   │   ├── playback_action.py
│   │   ├── bridge_action.py
│   │   ├── hangup_action.py
│   │   └── factory.py               # action_from_payload(dict) -> Action
│   ├── events/
│   │   ├── base.py                  # ChannelEvent, ExecutionCorrelatedEvent, ChannelLifecycleEvent
│   │   ├── channel_create.py
│   │   ├── channel_execute_complete.py
│   │   └── channel_hangup_complete.py
│   ├── entities.py                  # CommandExecution (lifecycle: PENDING→SUCCEEDED/FAILED/CANCELLED)
│   ├── commands.py                  # Command VO
│   ├── value_objects.py             # ValidationResult
│   ├── exceptions.py
│   └── repositories.py              # CommandExecutionRepository — порт (sync)
│
├── application/
│   ├── action_handlers/             # sync — чиста CPU-логіка, без I/O
│   │   ├── base.py                  # ActionHandler(Protocol)
│   │   ├── playback_handler.py
│   │   ├── bridge_handler.py
│   │   └── hangup_handler.py
│   ├── event_handlers/              # async — публікація в чергу це I/O
│   │   ├── base.py                  # EventHandler(Protocol), async handle()
│   │   ├── channel_create_handler.py
│   │   ├── channel_execute_complete_handler.py
│   │   └── channel_hangup_complete_handler.py
│   ├── use_cases/
│   │   ├── execute_action.py        # async — send_command() йде через greenswitch
│   │   └── handle_channel_event.py  # async — тонкий диспетчер
│   └── ports.py                     # FreeSwitchGatewayPort, ResultPublisherPort (async Protocol)
│
├── infrastructure/
│   ├── esl/
│   │   ├── esl_gateway.py           # адаптер над greenswitch.InboundESL
│   │   ├── esl_event_mapper.py      # raw greenswitch event -> domain ChannelEvent
│   │   └── esl_event_listener.py    # driving adapter, async
│   ├── queue/
│   │   └── result_publisher.py      # StubResultPublisher (async; заміна на реальний брокер)
│   └── repositories/
│       └── in_memory_execution_repository.py  # sync, in-memory
│
├── presentation/
│   └── action_consumer.py           # async driving adapter для вхідної черги Action
│
├── shared/
│   └── base_entity.py               # Entity — спільна абстракція
│
├── containers.py                    # DI-контейнер (dependency-injector), async Resource
└── main.py                          # точка входу, asyncio.run(main())
```

## Чому саме ці частини async, а які лишились sync

| Компонент | Sync чи Async | Чому |
|---|---|---|
| `ActionHandler.build_command()` | **sync** | Чиста CPU-логіка (побудова рядка команди), без I/O — async нічого б не додав |
| `FreeSwitchGatewayPort.send_command()` | **async** | Мережевий I/O через greenswitch (`await connection.send(...)`) |
| `EventHandler.handle()` | **async** | Викликає `ResultPublisherPort.publish_result()` — I/O в чергу |
| `CommandExecutionRepository` | **sync** | In-memory реалізація не потребує I/O; при переході на async-клієнт (напр. `redis.asyncio`) інтерфейс легко зробити async — use case'и вже async |
| `ExecuteActionUseCase.execute()` | **async** | Викликає async gateway |
| `HandleChannelEventUseCase.execute()` | **async** | Викликає async event handler |

## greenswitch: ключові деталі реалізації

### Кореляція команда↔подія через клієнтський `Event-UUID`

Замість парсингу відповіді FreeSwitch на `sendmsg`, `EslGateway.send_command()`
сам генерує `job_uuid` (`uuid.uuid4()`) і передає його в заголовку
`Event-UUID`. Це стандартна поведінка ESL-протоколу: FreeSwitch поверне
те саме значення як `Application-UUID` у відповідній
`CHANNEL_EXECUTE_COMPLETE` події — кореляція гарантована незалежно від
деталей конкретної версії обгортки над сирим протоколом.

### Обробники подій — корутини, awaited самим greenswitch

```python
connection.register_handle("CHANNEL_EXECUTE_COMPLETE", self._on_raw_event)
```

`_on_raw_event` — `async def`; greenswitch очікує на неї всередині свого
internal event loop (`handle_events()`), тому немає потреби вручну
створювати `asyncio.Task` для кожної події.

### `esl_event_mapper.py` захищений від відмінностей у версіях API

Функція `_header()` пробує спершу `raw_event.get_header(name)`, потім
`raw_event.headers.get(name)` — це страхує код від відмінностей точного
API об'єкта події між версіями greenswitch.

## Конфігурація: `config/config-{APP_ENV}.yaml`

```python
# main.py
env: str = os.getenv("APP_ENV", "dev")
config_path: str = f"config/config-{env}.yaml"
container.config.from_yaml(config_path)
```

```yaml
# config/config-dev.yaml
esl:
  host: "127.0.0.1"
  port: 8021
  password: "ClueCon"
```

Перемикання середовища — через змінну `APP_ENV`:

```bash
APP_ENV=prod python -m myapp.main   # завантажить config/config-prod.yaml
```

**Секрети в yaml** (`config-prod.yaml::esl.password`) — прийнятно для
демонстрації; у реальному проді варто підмінювати це значення деплой-
пайплайном (Helm/envsubst) або поверх yaml викликати
`container.config.esl.password.from_env("ESL_PASSWORD")`, щоб пароль
не потрапляв під контроль версій.

## DI: async `providers.Resource` для `EslGateway`

```python
async def _init_esl_gateway(host: str, port: int, password: str) -> AsyncIterator[EslGateway]:
    gateway = EslGateway(host=host, port=port, password=password)
    await gateway.connect()
    yield gateway

class Container(containers.DeclarativeContainer):
    esl_gateway = providers.Resource(_init_esl_gateway, host=..., port=..., password=...)
```

`providers.Resource` — ідіоматичний спосіб dependency-injector керувати
залежностями з асинхронною ініціалізацією. В `main.py`:

```python
await container.init_resources()   # виконує await gateway.connect()
gateway = await container.esl_gateway()  # уже підключений інстанс
...
await container.shutdown_resources()  # graceful cleanup при завершенні
```

## Запуск

```bash
pip install -e .

# dev (config-dev.yaml, за замовчуванням)
python -m myapp.main

# prod
APP_ENV=prod python -m myapp.main
```

Потребує доступного FreeSwitch з увімкненим `mod_event_socket` за
адресою/портом/паролем із відповідного `config-{env}.yaml`.

## Розширення (без зміни use case'ів)

**Новий Action**: новий файл у `domain/actions/` + `application/action_handlers/`
+ рядок у `Container.action_handlers` Dict.

**Новий Event**: новий файл у `domain/events/` + `application/event_handlers/`
+ гілка в `esl_event_mapper.py` + рядок у `Container.event_handlers` Dict
+ додати назву події в `_SUBSCRIBED_EVENTS` (`esl_event_listener.py`).

`ExecuteActionUseCase` і `HandleChannelEventUseCase` залишаються незмінними
в обох випадках.
