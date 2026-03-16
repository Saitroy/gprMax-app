# GPRMax Workbench

## Русский

`GPRMax Workbench` — современное desktop GUI-приложение для `gprMax`, построенное на Python и PySide6.

Проект ориентирован на геофизиков, инженеров, исследователей, преподавателей и студентов, которым нужна вычислительная мощность `gprMax`, но без обязательной работы через CLI, ручного написания input-файлов и самостоятельной сборки Python-окружения.

### Цели

- сделать создание проектов и запуск симуляций доступными для непограммистов;
- сохранить `gprMax` как источник правды по возможностям симуляции;
- обеспечить прозрачный путь от GUI-конфигурации к сгенерированному `gprMax` input;
- поддерживать как guided workflow, так и advanced mode с видимостью raw input;
- оставаться модульным, тестируемым и поддерживаемым open-source desktop-приложением.

### Текущее состояние

Репозиторий уже включает:

- Stage 0: discovery и архитектурную документацию;
- Stage 1: каркас приложения с запускаемой PySide6 оболочкой;
- Stage 2: foundation layer с project model, validation, persistence и settings flows;
- Stage 3: subprocess-first интеграцию с `gprMax`, input generation, run artifacts, live logs и run history;
- Stage 4: Model Editor MVP с guided forms для базовой настройки модели, материалов, waveforms, sources, receivers, geometry и input preview;
- Stage 5: Results Viewer MVP с run-centric навигацией, HDF5 result discovery, A-scan plotting и bounded B-scan previews;
- многослойную структуру пакета для UI, application services, domain, infrastructure и jobs.

### Структура репозитория

```text
docs/                     Архитектура, roadmap, технические решения
src/gprmax_workbench/     Пакет приложения
tests/                    Unit tests для core/non-UI частей
```

Внутри `src/gprmax_workbench/`:

```text
ui/                       Qt-окна, views, theme
application/              Use cases, app state, orchestration services
domain/                   Domain models и правила валидации
infrastructure/           Settings, logging, persistence, gprMax adapters
jobs/                     Примитивы фоновых задач
```

### Архитектурное направление

GUI намеренно отделён от внутренних модулей `gprMax`. Базовая стратегия интеграции — `subprocess-first` через выделенный adapter layer. Это делает desktop-приложение устойчивее к будущим изменениям `gprMax` и не привязывает UI напрямую к внутренней структуре пакета.

Состояние проекта сохраняется как человекочитаемый project manifest плюс отдельные директории для generated input, run artifacts и results.

Project model уровня Stage 2 отражает документацию `gprMax` на базовом уровне:

- essential domain settings (`domain`, `dx_dy_dz`, `time_window`, PML);
- materials;
- waveforms;
- sources и receivers;
- упорядоченные geometry primitives как база для editor-backed commands;
- optional advanced raw input overrides.

Stage 3 сейчас поддерживает:

- input generation для essential domain commands;
- materials, waveforms, receivers, ограниченный source subset и ограниченный geometry subset;
- subprocess execution через `python -m gprMax`;
- geometry-only mode;
- wiring для GPU flags;
- future-ready hooks для MPI и batch-related CLI flags;
- persisted run metadata, logs и output directories для каждого run.

Stage 4 сейчас поддерживает:

- form-based редактирование project/model overview;
- CRUD flows для materials, waveforms, sources, receivers и focused geometry subset;
- model validation, привязанную к editor state и save flow;
- generated input preview из текущего in-memory model state;
- прямую связку model editor state с persistence и существующим simulation runner.

Stage 5 сейчас поддерживает:

- run-centric discovery результатов из persisted run artifacts;
- чтение metadata HDF5 output через выделенный reader layer;
- discovery receivers/components для `.out` файлов;
- встроенные A-scan plots внутри desktop-приложения;
- bounded B-scan previews из merged outputs или stacked single-trace outputs;
- открытие output directory и artifacts из GUI;
- устойчивые состояния для missing/corrupt/unsupported results.

### Разработка

Создание виртуального окружения и установка зависимостей:

```bash
pip install -e .[dev]
```

Запуск приложения:

```bash
python -m gprmax_workbench
```

Запуск тестов:

```bash
python -m unittest discover -s tests
```

### Ближайший инженерный фокус

Следующие шаги разработки:

1. расширить coverage input generation, model editor и advanced-mode support для большего числа `gprMax` commands;
2. углубить post-processing после Stage 5 MVP: FFT/spectral analysis и richer comparison workflows;
3. усилить cancellation/error handling на реальных `gprMax` runtime сценариях;
4. подготовить packaging/runtime-discovery решения для Windows distribution;
5. спроектировать geometry/snapshot integrations и более сильные handoff'ы во внешние инструменты там, где это действительно полезно.

### Ссылки

- `gprMax`: https://github.com/gprMax/gprMax
- исторический GUI reference, не архитектурная база: https://github.com/tomsiwek/gprMax-Designer

## English

`GPRMax Workbench` is a modern desktop GUI for `gprMax` built with Python and PySide6.

The project targets geophysicists, engineers, researchers, teachers, and students who need the power of `gprMax` without forcing them to work through raw CLI flows, handwritten input files, or Python environment setup.

### Goals

- make project creation and simulation runs accessible to non-programmers;
- keep `gprMax` as the source of truth for simulation capabilities;
- provide a clear path from GUI configuration to generated `gprMax` input;
- support both guided workflows and an advanced mode with raw input visibility;
- stay modular, testable, and maintainable as an open-source desktop application.

### Current status

This repository currently contains:

- Stage 0 discovery and architecture documentation;
- Stage 1 application skeleton with a runnable PySide6 shell;
- Stage 2 foundation layer with project model, validation, persistence, and settings flows;
- Stage 3 subprocess-first integration with `gprMax`, input generation, run artifacts, live logs, and run history;
- Stage 4 model editor MVP with guided forms for essential model setup, materials, waveforms, sources, receivers, geometry, and input preview;
- Stage 5 results viewer MVP with run-centric browsing, HDF5 result discovery, A-scan plotting, and bounded B-scan previews;
- Stage 6 bundled-runtime foundation with bundled-first engine resolution, runtime diagnostics, and packaging-aware path management;
- packaging scripts for building a bundled `gprMax` engine on a Windows release machine;
- layered package structure for UI, application services, domain, infrastructure, and jobs.

### Repository structure

```text
docs/                     Architecture, roadmap, tech decisions
src/gprmax_workbench/     Application package
tests/                    Unit tests for core, non-UI parts
```

Inside `src/gprmax_workbench/`:

```text
ui/                       Qt windows, views, theme
application/              Use cases, app state, orchestration services
domain/                   Domain models and validation rules
infrastructure/           Settings, logging, persistence, gprMax adapters
jobs/                     Background job primitives
```

### Architecture direction

The GUI is intentionally decoupled from `gprMax` internals. The default integration strategy is `subprocess-first` through a dedicated adapter layer, which keeps the desktop app resilient to future `gprMax` changes and avoids binding the UI directly to internal modules.

Project state is persisted as a human-readable project manifest plus dedicated folders for generated input, run artifacts, and results.

The Stage 2 project model mirrors the `gprMax` documentation at a foundation level:

- essential domain settings (`domain`, `dx_dy_dz`, `time_window`, PML);
- materials;
- waveforms;
- sources and receivers;
- ordered geometry primitives as future editor-backed commands;
- optional advanced raw input overrides.

Stage 3 currently supports:

- input generation for the essential domain commands;
- materials, waveforms, receivers, a limited source subset, and a limited geometry subset;
- subprocess execution through `python -m gprMax`;
- geometry-only mode;
- GPU flag wiring;
- future-ready hooks for MPI and batch-related CLI flags;
- persisted run metadata, logs, and output directories per run.

Stage 4 currently supports:

- form-based editing of project/model overview data;
- CRUD flows for materials, waveforms, sources, receivers, and a focused geometry subset;
- model validation wired to editor state and save flow;
- generated input preview from the current in-memory model;
- direct wiring from model editor state into persistence and the existing simulation runner.

Stage 5 currently supports:

- run-centric results discovery from persisted run artifacts;
- HDF5-based output metadata reading behind a dedicated reader layer;
- receiver/component discovery for `.out` files;
- embedded A-scan plots in the desktop app;
- bounded B-scan previews from merged outputs or stacked single-trace outputs;
- output directory and artifact opening from the GUI;
- robust missing/corrupt/unsupported result states.

### Development

Create a virtual environment and install dependencies:

```bash
pip install -e .[dev]
```

Run the application:

```bash
python -m gprmax_workbench
```

Run tests:

```bash
python -m unittest discover -s tests
```

### First implementation focus

The next engineering steps are:

1. expand input generation, editor coverage, and advanced-mode support across more `gprMax` commands;
2. deepen post-processing beyond the Stage 5 MVP with FFT/spectral analysis and richer comparison workflows;
3. harden cancellation/error handling with real-world `gprMax` runtime testing;
4. turn the new engine bundle scripts into a repeatable release build and installer pipeline;
5. design geometry/snapshot integrations and richer external-tool handoffs where they add real value.

### Bundled engine note

The product direction is now explicit: end users must not install `gprMax`, Python, Git, Conda, or Visual Studio Build Tools manually.

For Windows builds, `gprMax` is intended to be compiled on the release machine and shipped inside the installer as a bundled `engine/` runtime. The current repository includes the foundation for that approach in [packaging/engine/README.md](packaging/engine/README.md).

### Licensing note

`gprMax` is GPLv3+. Bundling it into the desktop distribution requires a dedicated release/license review before the first public bundled build. This repository already accounts for bundled notices and engine manifests, but that is not a substitute for license review.

### References

- `gprMax`: https://github.com/gprMax/gprMax
- historical GUI reference only: https://github.com/tomsiwek/gprMax-Designer
