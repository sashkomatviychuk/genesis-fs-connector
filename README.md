# ESL Controller — Async Hexagonal Architecture (genesis + dependency-injector)

Async-версія міні-застосунку для керування FreeSwitch через **ESL Inbound**.
Приймає Action-и (PLAYBACK, BRIDGE, HANGUP), формує та надсилає команди,
слухає події каналу (`CHANNEL_CREATE`, `CHANNEL_EXECUTE_COMPLETE`,
`CHANNEL_HANGUP_COMPLETE`), робить міні-валідацію та публікує
success/failed результат у вихідну чергу.

Зміни відносно попередньої (sync) версії:

1. **genesis** замість python-ESL — asyncio-native клієнт ESL (на відміну
   від greenswitch, що побудований на Gevent, а не asyncio), встановлюється
   звичайним `pip install genesis`.
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
│   │   ├── esl_gateway.py           # адаптер над genesis.Inbound (команди)
│   │   ├── esl_event_mapper.py      # raw genesis event -> domain ChannelEvent
│   │   └── esl_event_listener.py    # driving adapter над genesis.Consumer (події)
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

## genesis: ключові деталі реалізації

### Два окремі ESL-з'єднання: `Inbound` для команд, `Consumer` для подій

`EslGateway` використовує `genesis.Inbound` (async context manager) —
тримається відкритим на весь час роботи застосунку через DI Resource-
провайдер. `EslEventListener` використовує окремий `genesis.Consumer`,
який керує власним з'єднанням і підпискою на події декларативно, через
`@app.handle("EVENT_NAME")`. Це два незалежні inbound-з'єднання до
FreeSwitch — типовий патерн для genesis: одне для надсилання команд,
інше — для довготривалого прийому подій.

### Кореляція команда↔подія через клієнтський `Event-UUID`

Замість парсингу відповіді FreeSwitch на `sendmsg`, `EslGateway.send_command()`
сам генерує `job_uuid` (`uuid.uuid4()`) і передає його в заголовку
`Event-UUID`. Це стандартна поведінка ESL-протоколу: FreeSwitch поверне
те саме значення як `Application-UUID` у відповідній
`CHANNEL_EXECUTE_COMPLETE` події — кореляція гарантована незалежно від
деталей конкретної версії обгортки над сирим протоколом.

### Обробники подій — корутини, реєстровані через `@app.handle(...)`

```python
self._app.handle(event_name)(self._on_raw_event)
```

`_on_raw_event` — `async def`; genesis документація прямо вимагає, щоб
кожен обробник події був awaitable, і сам await-ить його всередині
`app.start()`. Той самий callback реєструється для кожної цікавої нам
події — конкретна доменна диспетчеризація відбувається вже в
`HandleChannelEventUseCase` за `event.type`.

### `esl_event_mapper.py` захищений від відмінностей у формі події

genesis документація показує події/відповіді як dict-подібні об'єкти
(`{'Content-Type': ..., 'Reply-Text': ...}`), тому `_header()` спершу
пробує `raw_event.get(name)`, а якщо конкретна версія бібліотеки віддає
об'єкт з окремим атрибутом `.headers` — підстраховується і цим шляхом.

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
    async with Inbound(host, port, password) as client:
        yield EslGateway(client)

class Container(containers.DeclarativeContainer):
    esl_gateway = providers.Resource(_init_esl_gateway, host=..., port=..., password=...)
```

`providers.Resource` — ідіоматичний спосіб dependency-injector керувати
залежностями з асинхронною ініціалізацією; тут генератор тримає
`async with Inbound(...)` відкритим до виклику `shutdown_resources()`,
у якому genesis коректно закриє з'єднання через `__aexit__`. В `main.py`:

```python
await container.init_resources()      # відкриває genesis.Inbound з'єднання
listener = container.esl_event_listener()  # окреме genesis.Consumer з'єднання
...
await container.shutdown_resources()   # graceful cleanup при завершенні
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
