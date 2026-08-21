# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Async hexagonal-architecture app that controls FreeSwitch over ESL (Event Socket Library) Inbound.
It accepts Action commands (PLAYBACK, BRIDGE, HANGUP, ANSWER), sends them to FreeSwitch, listens
for channel events (`CHANNEL_CREATE`, `CHANNEL_EXECUTE_COMPLETE`, `CHANNEL_HANGUP_COMPLETE`), and
publishes success/failed results to an outbound queue. Uses `genesis` (asyncio-native ESL client)
and `dependency-injector` for composition.

The README.md (in Ukrainian) is the primary design doc and is kept in sync with the code — read it
for full rationale; this file summarizes what's needed to navigate and extend the codebase.

## Commands

```bash
pip install -e .              # install package + deps
pip install -e ".[dev]"       # + ruff, pytest, pytest-asyncio, pytest-cov

python -m myapp.main          # run (dev config by default)
APP_ENV=prod python -m myapp.main   # run with config/config-prod.yaml

ruff check .                  # lint (rules: E, F, I — see pyproject.toml)
ruff check --fix .            # lint with autofix
ruff format .                 # format

pytest                                    # run tests + coverage report (addopts in pyproject.toml)
pytest tests/domain/test_action_factory.py           # single file
pytest tests/domain/test_action_factory.py::test_unknown_type_raises_domain_error  # single test
pytest --no-cov                           # skip coverage for a faster loop
```

Requires a reachable FreeSwitch with `mod_event_socket` enabled, matching the host/port/password in
`config/config-{APP_ENV}.yaml`.

## Architecture

Strict hexagonal layering under `src/myapp/`: `domain/` → `application/` → `infrastructure/` /
`presentation/`, wired together in `containers.py`. Dependencies only point inward; `domain/` has
no knowledge of ESL, DI, or queues. The app also follows basic DDD building blocks: `domain/entities.py`
holds the entity with identity and lifecycle (`CommandExecution`), `domain/value_objects.py` and
`domain/commands.py` hold immutable value objects (`ValidationResult`, `Command`), and
`domain/repositories.py` defines the repository port — keep new domain concepts sorted into these
same categories rather than as loose dicts/dataclasses of convenience.

### Typed DTOs — avoid `Any`

Every DTO/payload crossing a boundary (`Action`, `ChannelEvent`, `ResultPayload`, command handler
inputs/outputs, etc.) must be a concrete class — a `dataclass` subclass of the relevant ABC, not a
`dict[str, Any]` or a bare `dict`. This is deliberate (see the `ResultPayload` pattern below): it
gives static field-name/type checking at write time instead of runtime `KeyError`s. When adding a
new Action, Event, or ResultPayload, define its own dataclass with explicit fields and types rather
than reusing a generic dict or adding an `Any`-typed field. Reach for `Any` only at true I/O
boundaries where the shape is genuinely unknown (e.g. raw genesis event objects in
`esl_event_mapper.py` before they're mapped into a domain type) — and narrow away from it as soon as
possible after that boundary.

- **`domain/`** — pure core, no I/O.
  - `actions/` — `Action` ABC + one dataclass subclass per action type (`playback_action.py`,
    `bridge_action.py`, `hangup_action.py`, ...), plus `factory.py` (`action_from_payload(dict) -> Action`).
  - `events/` — `ChannelEvent`/`ExecutionCorrelatedEvent`/`ChannelLifecycleEvent` base classes and
    one subclass per FreeSwitch event type.
  - `entities.py` — `CommandExecution`, the command↔event correlation entity (lifecycle:
    `PENDING → SUCCEEDED/FAILED/CANCELLED`).
  - `repositories.py` — `CommandExecutionRepository` port (sync interface).

- **`application/`**
  - `action_handlers/` — **sync**, pure CPU logic (building the ESL command string from an
    `Action`). No I/O, so no need for async here.
  - `event_handlers/` — **async**, because handling an event means publishing a result (I/O).
    `event_handlers/application_complete/` holds one handler per FreeSwitch _application_ name
    (`answer`, `playback`, ...) — see below.
  - `use_cases/` — `ExecuteActionUseCase` (send a command through the gateway) and
    `HandleChannelEventUseCase` (dispatch an incoming event to its handler). Both stay unchanged
    when adding new actions/events — only the registries in `containers.py` grow.
  - `ports.py` — `FreeSwitchGatewayPort`, `ResultPublisherPort` (async Protocols).

- **`infrastructure/`**
  - `esl/esl_gateway.py` — adapter over `genesis.Inbound`, sends commands. Generates its own
    `job_uuid` (`uuid.uuid4()`) and passes it as the `Event-UUID` header — FreeSwitch echoes it
    back as `Application-UUID` on the matching `CHANNEL_EXECUTE_COMPLETE`, which is how
    command↔event correlation is guaranteed (no need to parse the `sendmsg` reply itself).
  - `esl/esl_event_listener.py` — separate adapter over `genesis.Consumer`, its own long-lived
    connection dedicated to receiving events, subscribed declaratively via `@app.handle("EVENT_NAME")`.
    **Two independent inbound ESL connections exist by design**: one for commands (`Inbound`), one
    for events (`Consumer`).
  - `esl/esl_event_mapper.py` — raw genesis event → domain `ChannelEvent`. Defensive `_header()`
    helper: tries `raw_event.get(name)` first, falls back to a `.headers` attribute, since different
    genesis versions may represent events differently.
  - `queue/result_publisher.py` — `StubResultPublisher`, a placeholder to be swapped for a real
    broker.
  - `repositories/in_memory_execution_repository.py` — sync, in-memory `CommandExecutionRepository`.

- **`presentation/action_consumer.py`** — async driving adapter for the inbound Action queue. Not
  yet wired into `main.py` — production wiring would run it via `asyncio.gather` alongside the
  event listener, invoking `container.action_consumer().handle_message(payload)` per message from a
  real broker (e.g. aio-pika/aiokafka).

- **`containers.py`** — the composition root (`dependency_injector.containers.DeclarativeContainer`).
  `esl_gateway` is a `providers.Resource` wrapping an async generator (`_init_esl_gateway`) that
  holds `async with genesis.Inbound(...)` open for the app's lifetime; it's opened by
  `container.init_resources()` and closed by `container.shutdown_resources()`. Action/event/
  application-complete handlers are registered as `providers.Dict` keyed by their type enum/string —
  this is the extension point (see below).

- **`main.py`** — entry point. Loads `config/config-{APP_ENV}.yaml` (`APP_ENV` env var, default
  `dev`) via `container.config.from_yaml(...)`, calls `init_resources()`, runs
  `esl_event_listener.run_forever()`, and `shutdown_resources()` in a `finally` block.

### CHANNEL_EXECUTE_COMPLETE dispatch (per-application handlers)

`ChannelExecuteCompleteHandler` looks up the `CommandExecution` by `job_uuid` and delegates to an
`ApplicationCompleteHandler` keyed by `event.application` (`answer`, `playback`, ...). Each
application handler validates its own `app_response`, builds its own typed result payload, publishes
it, and **deletes** the execution from the repository (its correlation job is done once handled).
If `job_uuid` is unknown (already handled, duplicate, foreign event), that's normal — the handler
skips and logs, no exception.

Result payloads are typed dataclasses, not `dict[str, Any]`: `ResultPayload` ABC with subclasses
like `AnswerResultPayload`, `PlaybackResultPayload` (mirrors the `Action`/`ChannelEvent` pattern of
ABC + frozen dataclass subclasses). `StubResultPublisher` serializes via `dataclasses.asdict()`.

### Extending

**New Action**: add a file in `domain/actions/` + `application/action_handlers/`, then register it
in `Container.action_handlers`. Use cases don't change.

**New Event**: add a file in `domain/events/` + `application/event_handlers/`, add a branch in
`esl_event_mapper.py`, register in `Container.event_handlers`, and add the event name to
`_SUBSCRIBED_EVENTS` in `esl_event_listener.py`.

**New FreeSwitch application** (for `CHANNEL_EXECUTE_COMPLETE`): add a file in
`application/event_handlers/application_complete/` + register in
`Container.application_complete_handlers`. `ChannelExecuteCompleteHandler` itself doesn't change.

## Testing

`pytest` (+ `pytest-asyncio` for coroutines, `pytest-cov` for coverage — all in the `dev` extra).
Tests live in `tests/`, mirroring the `src/myapp/` package layout (e.g. `tests/domain/` for
`myapp/domain/`). Coverage runs by default via `addopts` in `pyproject.toml` and is scoped to
`src/myapp` (`[tool.coverage.run]`); use `pytest --no-cov` for a faster inner loop.

`tests/conftest.py` holds shared fixtures — notably raw **Action payload fixtures**
(`answer_action_payload`, `playback_action_payload`, `bridge_action_payload`,
`hangup_action_payload`), each a plain `dict` shaped like what actually arrives off the inbound
queue before `action_from_payload()` parses it into a typed `Action`. There's also a parametrized
`any_action_payload` fixture (indirect via `request.getfixturevalue`) for assertions that should
hold across every action type (e.g. `channel_id` handling). Add an equivalent fixture whenever a new
Action/Event/payload type is introduced, rather than constructing dicts inline in each test.

When testing a new layer, follow the same shape as `tests/domain/test_action_factory.py`: exercise
the public function/use case through its payload fixtures, assert on the resulting typed domain
object (not on the raw dict), and add one test for the invalid/unknown-input path (raises the
correct `DomainError` subclass from `domain/exceptions.py`).

## Configuration

`config/config-{APP_ENV}.yaml`, selected via the `APP_ENV` env var (default `dev`). Currently holds
only `esl.host` / `esl.port` / `esl.password`. `config-prod.yaml` keeps the password in plaintext
for demo purposes — README notes that a real deployment should override it via a deploy pipeline or
`container.config.esl.password.from_env("ESL_PASSWORD")` instead of committing it.
