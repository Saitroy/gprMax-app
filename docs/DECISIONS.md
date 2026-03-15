# Architectural Decisions

## Русский

## 2026-03-15: Использовать `GPRMax Workbench` / `gprmax_workbench` как стартовое имя проекта

Статус: принято

Обоснование:

- имя явно связано с экосистемой `gprMax`;
- звучит как серьёзный инженерный инструмент, а не как демо;
- достаточно нейтрально для open-source контрибьюторов и институциональных пользователей.

## 2026-03-15: Строить GUI на PySide6 и Qt6

Статус: принято

Обоснование:

- соответствует desktop-first цели продукта;
- даёт сильную поддержку Windows и зрелую widget ecosystem;
- хорошо подходит для долгоживущего научного инструмента.

## 2026-03-15: Считать `gprMax` источником правды и изолировать его за adapter boundary

Статус: принято

Обоснование:

- desktop app не должен дублировать или переопределять core simulation behavior;
- integration нужна стабильная seam, чтобы обновления `gprMax` не требовали переписывать UI;
- это сохраняет тестируемость GUI без загрузки полного runtime.

## 2026-03-15: Предпочесть `subprocess-first` интеграцию с `gprMax`

Статус: принято

Обоснование:

- CLI — наиболее стабильная и наблюдаемая execution surface;
- process isolation упрощает failure handling и log capture;
- direct imports остаются возможной оптимизацией, но не архитектурной базой.

Следствие:

- run requests, logs, exit codes и artifacts становятся first-class domain/application concepts;
- будущие hybrid integrations должны соответствовать тому же adapter contract.

## 2026-03-15: Держать project state отдельно от generated и executed artifacts

Статус: принято

Обоснование:

- пользователям нужны и чистые editable project data, и воспроизводимая run history;
- generated `.in` files и run logs должны быть доступны для просмотра и сохранения;
- это повышает прозрачность и для новичков, и для advanced users.

## 2026-03-15: Использовать versioned JSON project manifest, выровненный по command families `gprMax`

Статус: принято

Обоснование:

- Stage 2 требует стабильного persistence contract до появления полного editor'а;
- data model должна отражать concepts `gprMax`: domain, materials, waveforms, sources, receivers и geometry;
- JSON легко diff'ить, читать и тестировать;
- ordered geometry entries сохраняют порядок будущей command generation без преждевременных GUI abstractions.

## 2026-03-15: Держать Stage 3 execution subprocess-first и artifact-centric

Статус: принято

Обоснование:

- у `gprMax` есть documented CLI surface, более стабильная, чем прямые UI-level imports;
- stdout/stderr capture и per-run folders проще для reasoning, чем in-process execution side effects;
- это приземляет run history, cancellation, error reporting и future post-processing на явные artifacts.

Следствие:

- каждый run получает свой metadata manifest и log files;
- UI общается с application services и run records, а не с `subprocess.Popen`;
- будущий hybrid API path должен всё равно укладываться в тот же run-artifact contract.

## 2026-03-15: Держать Stage 4 model editing form-based и tab-oriented

Статус: принято

Обоснование:

- current project schema и input-generation coverage сильнее, чем любой scene/canvas model, который можно было бы честно оправдать на этом этапе;
- непограммистам explicit forms и validation полезнее, чем преждевременный pseudo-CAD workflow;
- tabs и list-detail editors дают стабильный путь для роста coverage.

Следствие:

- top-level model editing остаётся организованным по command families или entity groups;
- entity tabs могут развиваться независимо по мере роста coverage `gprMax`;
- будущий visual scene editor, если появится, должен строиться поверх тех же domain/application services, а не заменять их.

## 2026-03-15: MVP subset Stage 4 — это materials, waveforms, sources, receivers и три volumetric geometry primitives

Статус: принято

Обоснование:

- этот subset уже даёт реальный end-to-end authoring workflow при разумной инженерной стоимости;
- `box`, `sphere` и `cylinder` хорошо ложатся на текущие input generator и validation layer;
- waveforms и focused source subset достаточно, чтобы Stage 3 execution оставался практически полезным без притворства, что покрыта вся surface `gprMax`.

Следствие:

- unsupported commands остаются future work, а не скрытым частичным UI;
- input generation, validation, persistence и editor UX могут расти вместе от рабочей базы.

## 2026-03-15: Держать Stage 5 results reading за HDF5 adapter/repository layer

Статус: принято

Обоснование:

- result files `gprMax` основаны на HDF5, и UI не должен знать их internal layout;
- file-format handling, corrupt-file errors и dependency issues должны оставаться вне widgets;
- это создаёт стабильную seam для будущих analyzers и exporters.

Следствие:

- viewer разговаривает с services и typed result models, а не с `h5py`;
- отсутствие `h5py` превращается в понятную runtime capability error, а не в import crash на старте приложения.

## 2026-03-15: Использовать embedded QtCharts для A-scan plotting и bounded custom image widget для B-scan preview

Статус: принято

Обоснование:

- QtCharts уже доступен в составе PySide6 stack и не требует лишнего plotting dependency для MVP;
- A-scan естественно ложится на line chart;
- B-scan на этом этапе требует только bounded preview, поэтому custom image widget достаточно и не требует более тяжёлого plotting stack.

Следствие:

- Stage 5 даёт embedded plotting без преждевременной фиксации тяжёлой plotting abstraction;
- будущие advanced analysis tools при необходимости смогут добавить richer plotting backends за отдельными widgets/services.

## English

## 2026-03-15: Treat the bundled engine as the default runtime baseline

Status: accepted

Rationale:

- the product target is a single-installer desktop experience for non-programmers;
- relying on user-managed Python, Conda, or Git environments contradicts that goal;
- `gprMax` already exposes a stable CLI contract that can run inside a managed bundled runtime.

Consequences:

- the default execution path is a bundled Python runtime plus bundled `gprMax`;
- external Python/gprMax stays only as an advanced fallback and development path;
- packaging decisions must preserve a clear separation between app files, engine files, project data, and user settings.

## 2026-03-15: Use installer-oriented path management and runtime diagnostics as first-class architecture

Status: accepted

Rationale:

- desktop packaging becomes fragile when runtime discovery depends on the current working directory or ad hoc relative paths;
- bundled delivery needs explicit diagnostics for damaged or incomplete installs;
- CPU baseline and optional GPU/MPI capabilities need a clear model instead of implicit failure modes.

Consequences:

- a dedicated runtime layer resolves installation paths, engine paths, and user-data paths;
- the settings screen becomes a runtime diagnostics surface, not just a manual configuration form;
- future installer and release work can build on a stable engine manifest and capability contract.

## 2026-03-15: Use `GPRMax Workbench` / `gprmax_workbench` as the initial project name

Status: accepted

Rationale:

- clearly tied to the `gprMax` ecosystem;
- sounds like a serious engineering tool, not a demo app;
- neutral enough for open-source contributors and institutional users.

## 2026-03-15: Build the GUI with PySide6 and Qt6

Status: accepted

Rationale:

- matches the desktop-first product goal;
- gives strong Windows support and a mature widget ecosystem;
- supports long-lived scientific tooling better than lightweight GUI stacks.

## 2026-03-15: Treat `gprMax` as the source of truth and isolate it behind an adapter

Status: accepted

Rationale:

- the desktop app should not duplicate or reinterpret core simulation behavior;
- integration needs a stable seam so `gprMax` upgrades do not force UI rewrites;
- this keeps the GUI testable without loading the full runtime.

## 2026-03-15: Prefer `subprocess-first` integration with `gprMax`

Status: accepted

Rationale:

- the CLI is the most stable and observable execution surface;
- process isolation improves failure handling and log capture;
- direct imports remain a possible optimization, not the architectural baseline.

Consequence:

- run requests, logs, exit codes, and artifacts become first-class domain/application concepts;
- later hybrid integrations must conform to the same adapter contract.

## 2026-03-15: Keep project state separate from generated and executed artifacts

Status: accepted

Rationale:

- users need both clean editable project data and reproducible run history;
- generated `.in` files and run logs should be inspectable and preserved;
- this supports transparency for both novice and advanced users.

## 2026-03-15: Use a versioned JSON project manifest aligned with `gprMax` command families

Status: accepted

Rationale:

- Stage 2 needs stable persistence before a full editor exists;
- the data model should reflect `gprMax` concepts such as domain, materials, waveforms, sources, receivers, and geometry;
- JSON keeps the file easy to diff, inspect, and test;
- ordered geometry entries preserve future command-generation order without forcing premature GUI abstractions.

## 2026-03-15: Keep Stage 3 execution subprocess-first and artifact-centric

Status: accepted

Rationale:

- `gprMax` has a documented CLI surface that is more stable than direct UI-level imports;
- stdout/stderr capture and per-run folders are easier to reason about than in-process execution side effects;
- this keeps run history, cancellation, error reporting, and future post-processing grounded in explicit artifacts.

Consequence:

- each run gets its own metadata manifest and log files;
- the UI talks to application services and run records, not to `subprocess.Popen`;
- a future hybrid API path must still conform to the same run-artifact contract.

## 2026-03-15: Keep Stage 4 model editing form-based and tab-oriented

Status: accepted

Rationale:

- the current project schema and input-generation coverage are stronger than any scene/canvas model we could justify at this stage;
- non-programmer users benefit more from explicit forms and validation than from a premature pseudo-CAD workflow;
- tabs plus list-detail editors give a stable path to incremental coverage growth.

Consequence:

- top-level model editing stays organized by command family or entity group;
- entity tabs can evolve independently as more `gprMax` coverage is added;
- a future visual scene editor, if introduced, should sit on top of the same domain/application services rather than replace them.

## 2026-03-15: Stage 4 MVP entity subset is materials, waveforms, sources, receivers, and three volumetric geometry primitives

Status: accepted

Rationale:

- this subset gives a real end-to-end authoring workflow with manageable engineering cost;
- `box`, `sphere`, and `cylinder` map cleanly to the current input generator and validation layer;
- waveforms plus a focused source subset are enough to keep Stage 3 execution useful without pretending to cover the full `gprMax` surface.

Consequence:

- unsupported commands remain future work instead of hidden partial UI;
- input generation, validation, persistence, and editor UX can grow together from a working base.

## 2026-03-15: Keep Stage 5 results reading behind an HDF5 adapter/repository layer

Status: accepted

Rationale:

- `gprMax` result files are HDF5-based and the UI should not know their internal layout;
- file-format handling, corrupt-file errors, and dependency issues need to stay outside widgets;
- this creates a stable seam for future richer analyzers and exporters.

Consequence:

- the viewer talks to services and typed result models, not to `h5py`;
- missing `h5py` becomes a user-facing runtime capability error rather than an import crash at app startup.

## 2026-03-15: Use embedded QtCharts for A-scan plotting and a bounded custom image widget for B-scan previews

Status: accepted

Rationale:

- QtCharts is already available through the PySide6 stack and avoids pulling in an extra plotting dependency for the MVP;
- A-scans map cleanly to line charts;
- B-scan needs only a bounded preview for now, so a custom image widget is sufficient without introducing a larger plotting stack.

Consequence:

- Stage 5 delivers embedded plotting without committing the project to a heavyweight plotting abstraction too early;
- future advanced analysis tools can still add richer plotting backends behind separate widgets/services if justified.
