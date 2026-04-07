# Architecture

## Русский

## Продуктовая рамка

`GPRMax Workbench` — desktop-приложение, которое оборачивает `gprMax` в guided UI, project system, run management и results access. Это не форк `gprMax` и не переписывание `gprMax-Designer`.

Desktop-приложение владеет:

- жизненным циклом проекта;
- пользовательскими формами и workflow;
- validation и defaults;
- генерацией `gprMax` input artifacts;
- orchestration симуляций и logging;
- discovery и viewing результатов.

`gprMax` остаётся вычислительным ядром и функциональным источником правды.

## Архитектурные принципы

- многослойная структура с явными границами;
- UI зависит от application services, а не от внутренних модулей `gprMax`;
- интеграция с `gprMax` изолирована за adapters;
- project metadata хранится отдельно от generated/executed artifacts;
- длинные операции представлены как jobs и не выполняются в UI thread;
- сгенерированный `gprMax` input file является прозрачным артефактом, а не скрытой внутренней деталью.

## Слои

### `ui/`

Ответственность:

- окна, dialogs, views, композиция интерфейса;
- navigation, actions, empty/error/loading states;
- presentation models для widgets и forms.

Правила:

- слой не должен напрямую запускать `gprMax`;
- слой не должен знать process arguments и filesystem layouts за пределами данных, предоставленных services.

### `application/`

Ответственность:

- orchestration use cases;
- application/session state;
- coordination жизненного цикла проекта;
- preparation симуляций и coordination результатов.

Правила:

- может координировать несколько infrastructure services;
- должен выражать product workflows через стабильные интерфейсы, которые потребляет UI.

### `domain/`

Ответственность:

- core entities, например project, run record и result set;
- validation rules и business constraints;
- стабильные концепции, не завязанные на Qt или process execution.

### `infrastructure/`

Ответственность:

- persistence проекта;
- storage настроек;
- bootstrap logging;
- filesystem interactions;
- реализации adapters для `gprMax`.

### `jobs/`

Ответственность:

- background job contracts и job state;
- cancellation primitives;
- интеграция с будущей execution queue.

## Поток данных

1. Пользователь редактирует project/model data в GUI.
2. UI отправляет команды в application services.
3. Application services валидируют данные и сохраняют project state.
4. Input-generation service сериализует project state в `gprMax` input artifact.
5. Simulation service создаёт typed run configuration и передаёт её в `gprMax` adapter.
6. Subprocess runner запускает `gprMax`, стримит stdout/stderr и пишет run artifacts.
7. Run repository сохраняет metadata/history и возвращает их обратно в UI.
8. Results services индексируют outputs и отдают их в UI.

## Foundation Stage 4: Model Editor

Текущий model editor намеренно использует form-first architecture, а не canvas/CAD scene builder.

Почему:

- это лучше соответствует зрелости current project model и input generation;
- такой интерфейс понятнее для непограммистов;
- он даёт стабильный путь к validation, persistence и preview;
- это не заставляет нас слишком рано фиксировать слабую visual scene model в долгосрочной архитектуре.

Верхнеуровневая композиция editor'а:

- summary/header card с project location и validation state;
- вкладки для general settings, materials, waveforms, sources, receivers, geometry и input preview;
- list-detail editors внутри entity tabs;
- application-layer mutation services, которые обновляют `AppState` и validation state.

Editor сам не генерирует input lines и не строит subprocess commands. Он только редактирует typed project model и обращается к dedicated services за validation и preview.

## Foundation Stage 5: Results Viewer

Results layer организован вокруг трёх явных обязанностей:

- discovery artifacts из run folders;
- чтение HDF5 results через выделенную reader abstraction;
- UI-facing services для summaries, A-scan access и bounded B-scan building.

Текущие модули:

- `ResultArtifactLocator`: находит `.out` files и другие visualisation artifacts внутри run;
- `Hdf5ResultsReader`: читает HDF5 result files `gprMax` и отдаёт typed metadata/traces;
- `ResultRepository`: read-oriented repository, объединяющий run history и HDF5 access;
- `ResultsService`: владеет run/result selection state внутри viewer;
- `TraceService`: грузит metadata, receivers, components и A-scans;
- `BscanService`: строит bounded B-scan previews из merged или stacked trace files.

UI никогда не работает с HDF5 internals и filesystem details напрямую.

## Стратегия интеграции с `gprMax`

### Рекомендуемый дефолт: subprocess-first

Предпочтительный режим интеграции — запуск `gprMax` как внешнего процесса, обычно так:

```text
python -m gprMax <input-file> [options]
```

Почему это базовый вариант:

- он соответствует публичному CLI-контракту `gprMax`;
- он слабее связан с внутренней модульной структурой;
- он естественно отдаёт stdout/stderr для логов;
- он оставляет GPU/MPI/runtime concerns вне GUI process;
- он проще для поддержки на будущих версиях `gprMax`.

### Вторичный режим: optional hybrid integration

Некоторые будущие функции могут выиграть от аккуратных direct imports публичного Python API `gprMax`, но только за тем же adapter boundary и только там, где import path достаточно стабилен.

UI не должен знать, пришёл run из subprocess mode или из будущей in-process реализации.

## Foundation Stage 3: execution layer

Текущий runner намеренно ограничен minimum viable, но расширяемым subset.

Сейчас поддерживается напрямую:

- essential domain commands;
- materials;
- waveforms;
- receivers;
- source subset: `hertzian_dipole`, `magnetic_dipole`, `voltage_source`;
- geometry subset: `box`, `sphere`, `cylinder`;
- `geometry_view`;
- geometry-only execution mode;
- wiring GPU flags;
- future hooks для `-mpi`, `--mpi-no-spawn`, `-n`, `-restart`, `--write-processed`.

Сознательно отложено:

- широкий coverage object commands;
- полноценная HPC orchestration;
- structured results parsing;
- advanced recovery/retry policies;
- polished expert run configuration UX.

## Концепции результатов Stage 5

Results viewer MVP построен вокруг узкого, но полезного subset result concepts `gprMax`:

- `.out` HDF5 files как основной result artifact;
- receiver-centric output components;
- A-scan как default embedded viewing workflow;
- B-scan как merged-output view или controlled stacked-trace preview;
- non-HDF5 visualisation artifacts, например geometry/snapshot files, пока только как external-open artifacts.

Сознательно отложено:

- полноценные signal-processing suites;
- embedded 3D geometry/snapshot viewers;
- сложные multi-run dashboards;
- прямая интеграция со всеми plotting/post-processing utilities `gprMax`.

## Структура run artifacts

Stage 3 использует такую структуру run folders:

```text
project/
  runs/
    20260315-153000-ab12cd34/
      input/
        simulation.in
      logs/
        stdout.log
        stderr.log
        combined.log
      output/
      metadata.json
```

Обоснование:

- одна неизменяемая папка на каждый run;
- явное разделение input snapshot, logs и outputs;
- metadata остаётся человекочитаемой и тестируемой;
- будущие results viewers могут работать с `runs/<run-id>/output` без догадок.

## Layout проекта на диске

Рекомендуемый project folder layout:

```text
MyProject/
  project.gprwb.json
  generated/
    current.in
  runs/
    20260315-153000/
      command.json
      stdout.log
      stderr.log
      generated.in
      output/
  results/
  assets/
```

Примечания:

- `project.gprwb.json` хранит editor-facing project state;
- `generated/` хранит reproducible generated input files;
- `runs/` хранит immutable execution artifacts и logs;
- `results/` может хранить indexed/curated outputs, доступные viewer'ам.

## Project model Stage 2

Persisted project manifest намеренно выровнен по command families `gprMax` из официальной документации, а не по произвольным GUI-only groupings.

Текущие typed sections:

- `metadata`: identity проекта и timestamps;
- `model.domain`: domain size, spatial resolution, time window, PML cells;
- `model.notes` и `model.tags`: editor-facing metadata для guided workflows;
- `model.materials`: material definitions;
- `model.waveforms`: waveform definitions;
- `model.sources`: source definitions с waveform references;
- `model.receivers`: receiver definitions;
- `model.geometry`: ordered geometry primitives с parameters, material references, labels, notes, tags и dielectric-smoothing flag;
- `model.geometry_views`: requests на geometry view;
- `advanced.raw_input_overrides`: raw text hooks для будущего advanced mode.

Это даёт стабильный persistence contract уже сейчас, не притворяясь, что Stage 2 уже покрывает полный editor surface `gprMax`.

## Формат project file

Project manifest file: `project.gprwb.json`

Форма формата:

```json
{
  "schema": {
    "name": "gprmax-workbench-project",
    "version": 1
  },
  "metadata": {},
  "model": {
    "title": "",
    "notes": "",
    "tags": [],
    "domain": {},
    "materials": [],
    "waveforms": [],
    "sources": [],
    "receivers": [],
    "geometry": [],
    "geometry_views": [],
    "python_blocks": []
  },
  "advanced": {
    "raw_input_overrides": []
  }
}
```

Обоснование:

- формат человекочитаемый и удобный для diff в open-source работе;
- schema versioned с самого начала;
- есть явное разделение между editable project state и generated/run artifacts;
- структуры достаточно, чтобы питать Stage 3 generation и validation, не загоняя проект в fake full editor слишком рано.

## Editor services Stage 4

Stage 4 добавляет три application-level service:

- `ModelEditorService`: владеет in-memory CRUD operations для model entities и помечает current project как dirty;
- `ValidationService`: отдаёт filtered validation results для editor sections и summary banners;
- `InputPreviewService`: строит/export'ит previews из current project, не трогая run lifecycle.

Это делает UI достаточно тонким и заменяемым, но при этом даёт editor'у быстрый feedback.

## UI shell

Stage 1 shell организован вокруг пяти top-level workspaces:

- Welcome / Project Manager
- Model Editor
- Simulation Runner
- Results Viewer
- Settings

Это даёт стабильную navigation model, не фиксируя внутреннюю architecture editor'а слишком рано.

## English

## Stage 6 Runtime Foundation

### Русский

Stage 6 добавляет отдельный runtime layer между приложением и subprocess runner.

Новые ответственности:

- `infrastructure/runtime/path_manager.py`: installer-oriented пути, отделённые от project data и user settings;
- `infrastructure/runtime/engine_locator.py`: bundled-first выбор execution engine;
- `infrastructure/runtime/diagnostics.py`: health checks и capability detection;
- `application/services/runtime_service.py`: единая orchestration point для runtime resolution + adapter configuration + diagnostics report;
- `ui/views/settings_view.py`: пользовательский diagnostics screen вместо сценария ручной настройки Python как основного пути.

Поток runtime resolution:

1. `PathManager` вычисляет `install_root`, `engine_root`, `settings/logs/cache/temp`.
2. `EngineLocator` пытается выбрать встроенное ядро.
3. Если bundled runtime отсутствует, advanced mode может использовать внешний fallback.
4. `RuntimeService` конфигурирует `SubprocessGprMaxAdapter` выбранным engine config.
5. `RuntimeDiagnostics` строит report для UI и troubleshooting.

`SimulationService` и UI запуска не знают деталей install layout. Они продолжают работать через adapter boundary.

### English

Stage 6 adds a dedicated runtime layer between the application and the subprocess runner.

New responsibilities:

- `infrastructure/runtime/path_manager.py`: installer-oriented paths separated from project data and user settings;
- `infrastructure/runtime/engine_locator.py`: bundled-first engine selection;
- `infrastructure/runtime/diagnostics.py`: health checks and capability detection;
- `application/services/runtime_service.py`: single orchestration point for runtime resolution, adapter configuration, and diagnostics;
- `ui/views/settings_view.py`: a user-facing diagnostics screen instead of manual Python path configuration as the default workflow.

Runtime resolution flow:

1. `PathManager` resolves `install_root`, `engine_root`, `settings/logs/cache/temp`.
2. `EngineLocator` tries to select the bundled engine.
3. If the bundled runtime is missing, advanced mode may use an external fallback.
4. `RuntimeService` configures `SubprocessGprMaxAdapter` with the selected engine config.
5. `RuntimeDiagnostics` builds a report for the UI and troubleshooting.

`SimulationService` and the run UI do not know install layout details. They continue to work through the adapter boundary.

## Product framing

`GPRMax Workbench` is a desktop application that wraps `gprMax` with a guided UI, project system, run management, and results access. It is not a fork of `gprMax` and not a rewrite of `gprMax-Designer`.

The desktop app owns:

- project lifecycle;
- user-facing forms and workflows;
- validation and defaults;
- generation of `gprMax` input artifacts;
- simulation orchestration and logging;
- results discovery and viewing.

`gprMax` remains the computation engine and functional source of truth.

## Architectural principles

- layered structure with explicit boundaries;
- UI depends on application services, not on `gprMax` internals;
- integration with `gprMax` is isolated behind adapters;
- project metadata is persisted independently from generated simulation artifacts;
- long-running work is represented as jobs, not run on the UI thread;
- the generated `gprMax` input file is a transparent artifact, not a hidden internal detail.

## Layers

### `ui/`

Responsibilities:

- windows, dialogs, views, view composition;
- navigation, actions, empty/error/loading states;
- presentation models for widgets and forms.

Rules:

- should not spawn `gprMax` directly;
- should not know process arguments or filesystem layouts beyond data exposed by services.

### `application/`

Responsibilities:

- use-case orchestration;
- application/session state;
- project lifecycle coordination;
- simulation preparation and results coordination.

Rules:

- may coordinate multiple infrastructure services;
- should express product workflows in stable interfaces that UI can consume.

### `domain/`

Responsibilities:

- core entities such as project, run record, and result set;
- validation rules and business constraints;
- stable concepts that are not tied to Qt or process execution.

### `infrastructure/`

Responsibilities:

- project persistence;
- settings storage;
- logging setup;
- filesystem interactions;
- `gprMax` adapter implementations.

### `jobs/`

Responsibilities:

- background job contracts and job state;
- cancellation primitives;
- future execution queue integration.

## Data flow

1. User edits project/model data in the GUI.
2. UI sends commands to application services.
3. Application services validate input and persist project state.
4. An input-generation service serializes project state into a `gprMax` input artifact.
5. A simulation service creates a typed run configuration and passes it to the `gprMax` adapter.
6. A subprocess runner launches `gprMax`, streams stdout/stderr, and writes run artifacts.
7. A run repository persists metadata/history and exposes it back to the UI.
8. Results services can later index run outputs and expose them back to the UI.

## Stage 4 model editor foundation

The current model editor deliberately uses a form-first architecture instead of a canvas/CAD scene builder.

Why:

- it matches the current project model and input-generation maturity;
- it keeps the GUI understandable for non-programmers;
- it gives a stable path to validation, persistence, and preview;
- it avoids baking a weak visual scene model into the long-term architecture too early.

Top-level editor composition:

- summary/header card with project location and validation state;
- tabbed sections for general settings, materials, waveforms, sources, receivers, geometry, and input preview;
- list-detail editors inside entity tabs;
- application-layer mutation services that update `AppState` and validation state directly.

The editor does not generate input lines or subprocess commands itself. It only edits the typed project model and asks dedicated services for validation and preview.

## Stage 5 results viewer foundation

The results layer is organized around three explicit responsibilities:

- artifact discovery from run folders;
- HDF5-backed result reading behind a dedicated reader abstraction;
- UI-facing services for summaries, A-scan access, and bounded B-scan building.

Current modules:

- `ResultArtifactLocator`: finds `.out` files and other visualisation artifacts in a run;
- `Hdf5ResultsReader`: reads `gprMax` HDF5 result files and exposes typed metadata/traces;
- `ResultRepository`: a read-oriented repository that combines run history and HDF5 access;
- `ResultsService`: owns run/result selection state for the viewer;
- `TraceService`: loads metadata, receivers, components, and A-scans;
- `BscanService`: builds bounded B-scan previews from merged or stacked trace files.

The UI never talks to HDF5 or filesystem internals directly.

## `gprMax` integration strategy

### Recommended default: subprocess-first

The preferred integration mode is launching `gprMax` as an external process, typically via:

```text
python -m gprMax <input-file> [options]
```

Why this is the default:

- it matches `gprMax`'s public CLI contract;
- it is less coupled to internal module structure;
- it naturally exposes stdout/stderr for logs;
- it keeps GPU/MPI/runtime concerns outside the GUI process;
- it is easier to support across future `gprMax` versions.

### Secondary mode: optional hybrid integration

Some future features may benefit from controlled direct imports of a public `gprMax` Python API, but only behind the same adapter boundary and only where the import path is stable enough.

The UI should never care whether a run came from subprocess mode or a future in-process implementation.

## Stage 3 execution foundation

The current runner is intentionally scoped to a minimum viable but extensible subset.

Directly supported now:

- essential domain commands;
- materials;
- waveforms;
- receivers;
- source subset: `hertzian_dipole`, `magnetic_dipole`, `voltage_source`;
- geometry subset: `box`, `sphere`, `cylinder`;
- `geometry_view`;
- geometry-only execution mode;
- GPU flag wiring;
- future hooks for `-mpi`, `--mpi-no-spawn`, `-n`, `-restart`, `--write-processed`.

Deferred deliberately:

- broad object-command coverage;
- full HPC orchestration;
- structured results parsing;
- advanced recovery/retry policies;
- a polished expert run configuration UX.

## Stage 5 result concepts

The results viewer MVP is built around a narrow but high-value subset of `gprMax` result concepts:

- `.out` HDF5 files as the primary result artifact;
- receiver-centric output components;
- A-scan as the default embedded viewing workflow;
- B-scan as either a merged-output view or a controlled stacked-trace preview;
- non-HDF5 visualisation artifacts such as geometry/snapshot files exposed as external-open artifacts for now.

Deferred deliberately:

- full signal-processing suites;
- embedded 3D geometry/snapshot viewers;
- complex multi-run dashboards;
- direct integration with every `gprMax` plotting/post-processing utility.

## Run artifact layout

Stage 3 run folders use the following structure:

```text
project/
  runs/
    20260315-153000-ab12cd34/
      input/
        simulation.in
      logs/
        stdout.log
        stderr.log
        combined.log
      output/
      metadata.json
```

Rationale:

- one immutable folder per run;
- explicit separation of input snapshot, logs, and outputs;
- metadata remains human-readable and testable;
- future results viewers can target `runs/<run-id>/output` without guessing.

## Project layout on disk

Proposed project folder layout:

```text
MyProject/
  project.gprwb.json
  generated/
    current.in
  runs/
    20260315-153000/
      command.json
      stdout.log
      stderr.log
      generated.in
      output/
  results/
  assets/
```

Notes:

- `project.gprwb.json` stores editor-facing project state;
- `generated/` stores reproducible generated input files;
- `runs/` stores immutable execution artifacts and logs;
- `results/` can contain indexed or curated outputs exposed by viewers.

## Stage 2 project model

The persisted project manifest is intentionally aligned to `gprMax` command families from the official documentation instead of arbitrary GUI-only groupings.

Current typed sections:

- `metadata`: project identity and timestamps;
- `model.domain`: domain size, spatial resolution, time window, PML cells;
- `model.notes` and `model.tags`: editor-facing metadata for guided workflows;
- `model.materials`: material definitions;
- `model.waveforms`: waveform definitions;
- `model.sources`: source definitions with waveform references;
- `model.receivers`: receiver definitions;
- `model.geometry`: ordered geometry primitives with parameters, material references, labels, notes, tags, and dielectric-smoothing flag;
- `model.geometry_views`: geometry-view requests;
- `advanced.raw_input_overrides`: raw text hooks for later advanced mode.

This gives us a stable persistence contract now without pretending that Stage 2 already supports the full `gprMax` editor surface.

## Project file format

Project manifest file: `project.gprwb.json`

Format shape:

```json
{
  "schema": {
    "name": "gprmax-workbench-project",
    "version": 1
  },
  "metadata": {},
  "model": {
    "title": "",
    "notes": "",
    "tags": [],
    "domain": {},
    "materials": [],
    "waveforms": [],
    "sources": [],
    "receivers": [],
    "geometry": [],
    "geometry_views": [],
    "python_blocks": []
  },
  "advanced": {
    "raw_input_overrides": []
  }
}
```

Rationale:

- human-readable and diff-friendly for open-source work;
- versioned schema from the start;
- clear separation between editable project state and generated/run artifacts;
- enough structure to drive Stage 3 generation and validation without locking us into a fake full editor too early.

## Stage 4 editor services

The Stage 4 editor introduces three application-level services:

- `ModelEditorService`: owns in-memory CRUD operations for model entities and marks the current project dirty;
- `ValidationService`: exposes filtered validation results for editor sections and summary banners;
- `InputPreviewService`: builds/export previews from the current project without touching the run lifecycle.

This keeps the UI thin enough to stay replaceable while still giving the editor direct, low-latency feedback.

## UI shell

The current shell is organized around four top-level navigation pages plus dialog surfaces:

- `Welcome`
- `Project`
- `Simulation`
- `Results`

Additional shell surfaces:

- `Settings` as a dedicated dialog with runtime diagnostics and advanced-mode controls;
- `Documentation` as a separate dialog launched from the welcome shell.

The `Project` page is intentionally a sectioned workspace rather than a separate top-level page per editor subtool. It currently groups:

- `Scene`
- `Domain / Grid / Time Window`
- `Materials`
- `Waveforms`
- `Sources`
- `Receivers`
- `Geometry`
- `Libraries / Imports`
- `Advanced`
- `Input Preview`

This keeps the start flow, editing flow, simulation flow, and results flow separate without forcing the entire product into one overloaded workbench. Splitter-based desktop layouts are the default composition pattern, with the current UI baseline targeting `1366x768` and `1920x1080`.
