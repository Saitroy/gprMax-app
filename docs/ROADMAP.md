# Roadmap

## Русский

### Статус

`GPRMax Workbench` остаётся продуктом в активной разработке.

Что уже заложено:

- Stages 0-5 достигнуты на уровне foundation/MVP: архитектура, project model, persistence, guided editor, simulation runner и results viewer уже существуют;
- проект уже пригоден для раннего тестирования и итеративной доработки;
- packaging для Windows и bundled runtime остаются отложенными задачами, а не ближайшим приоритетом.

Текущий продуктовый фокус:

- `simulation workflow`
- `scene editor`
- `result analysis`

Главный принцип текущего цикла: сначала сделать сильный пользовательский путь `собрал сцену -> запустил расчёт -> понял результат`, и только потом переходить к packaging/distribution work.

### Ближайший roadmap: 8-12 недель

## Milestone 1: Reliable Simulation Workflow

Window:

- Weeks 1-2

GitHub milestone:

- `v0.4 - Simulation Workflow Hardening`

Epics:

- `simulation-preflight-and-readiness`
- `run-lifecycle-and-recovery`
- `run-snapshot-and-reproducibility`
- `simulation-integration-smoke-suite`
- `validation-and-error-copy`

Scope:

- preflight перед запуском: runtime health, validation state, path checks, disk/output checks;
- более надёжные сценарии `start / cancel / retry / rerun from history`;
- сохранение точного generated input, run config и command line для каждого run;
- улучшенные user-facing ошибки вместо слишком технических сообщений;
- integration smoke tests на сценариях success, cancel, timeout, broken runtime, missing output, failed merge.

Exit criteria:

- новый пользователь может создать проект, запустить расчёт, отменить или повторить его без CLI;
- по каждому run видно, что именно было запущено;
- сбои объясняются через UI достаточно ясно, чтобы пользователь понял следующий шаг.

## Milestone 2: Scene Editor Core UX

Window:

- Weeks 3-5

GitHub milestone:

- `v0.5 - Scene Editor Core UX`

Epics:

- `scene-undo-redo`
- `scene-multi-select-and-group-actions`
- `scene-keyboard-workflow`
- `scene-precision-editing`
- `scene-3d-navigation-foundation`

Scope:

- полноценный `undo/redo` для scene actions и inspector edits;
- multi-select, marquee selection, group move/delete/duplicate;
- keyboard workflow: delete, duplicate, undo/redo, nudge, mode switching, fit;
- axis locking, proportional resize, stronger snapping, exact dimension editing from canvas actions;
- depth/slice control и лучшее соответствие 2D plane editing реальной 3D-модели.

Exit criteria:

- типичная модель собирается через canvas быстрее и безопаснее, чем через raw input;
- пользователь не боится редактировать сцену, потому что любое действие обратимо;
- editor поддерживает как быстрые визуальные правки, так и точное числовое редактирование.

## Milestone 3: Results Analysis V2

Window:

- Weeks 6-8

GitHub milestone:

- `v0.6 - Results Analysis V2`

Epics:

- `ascan-analysis-tools`
- `bscan-visual-controls`
- `results-comparison-workflow`
- `results-traceability`
- `reporting-and-export`

Scope:

- для A-scan: cursors, delta measurements, peak picking, FFT/spectrum, export CSV/PNG;
- для B-scan: gain, contrast, colormap presets, time-zero/background controls;
- side-by-side и overlay compare workflows для разных run'ов;
- явная связь results с run config, generated input и metadata;
- экспорт изображений, графиков и компактных summary для отчётов и issue reports.

Exit criteria:

- пользователь может не только открыть output, но и реально анализировать его внутри приложения;
- сравнение run-to-run становится встроенной возможностью, а не ручной работой во внешних инструментах;
- результаты можно удобно экспортировать для публикаций, отчётов и bug reports.

## Milestone 4: OSS Readiness and Stabilization

Window:

- Weeks 9-10

GitHub milestone:

- `v0.7 - OSS Readiness and Stabilization`

Epics:

- `quality-gates-and-ci`
- `sample-projects-and-guides`
- `project-format-stability`
- `supportability`

Scope:

- CI с `tests`, lint и type checks;
- 2-3 example projects и короткие user workflows в документации;
- manifest versioning и foundation для migration hooks;
- crash/log bundle, issue templates и воспроизводимый bug-report checklist.

Exit criteria:

- внешний пользователь может быстро понять, как начать работу;
- внешний контрибьютор может локально поднять проект и внести изменение без скрытого контекста;
- продукт лучше переживает эволюцию project format и пользовательские сбои.

### Что осознанно отложено

- Windows packaging и installer;
- bundled engine distribution;
- широкое покрытие редких/edge-case `gprMax` commands до стабилизации core workflow;
- крупный архитектурный rewrite без давления реальных user scenarios.

### Suggested GitHub Labels / Milestones

- `v0.4 - Simulation Workflow Hardening`
- `v0.5 - Scene Editor Core UX`
- `v0.6 - Results Analysis V2`
- `v0.7 - OSS Readiness and Stabilization`

Cross-milestone epics:

- `guided-editor-command-coverage`
- `project-migration-and-compatibility`
- `user-facing-diagnostics-and-recovery`

## English

### Status

`GPRMax Workbench` is still under active development.

What is already in place:

- Stages 0-6 exist at a foundation/MVP level: architecture, project model, persistence, guided editor, simulation runner, results viewer, and runtime-resolution foundation are already present;
- the desktop shell is already usable for internal testing across `Welcome`, `Project`, `Simulation`, and `Results`;
- packaging and release engineering exist only as a foundation and are still incomplete for a first public release.

Current product focus:

- `simulation workflow`
- `scene editor`
- `result analysis`

The guiding principle of the current cycle is to make the core user path strong first: `build a scene -> run a simulation -> understand the result`, and only then move on to packaging and distribution work.

For the current public-release assessment see [FIRST_RELEASE_READINESS.md](./FIRST_RELEASE_READINESS.md).

### Near-term roadmap: 8-12 weeks

## Milestone 1: Reliable Simulation Workflow

Window:

- Weeks 1-2

GitHub milestone:

- `v0.4 - Simulation Workflow Hardening`

Epics:

- `simulation-preflight-and-readiness`
- `run-lifecycle-and-recovery`
- `run-snapshot-and-reproducibility`
- `simulation-integration-smoke-suite`
- `validation-and-error-copy`

Scope:

- preflight checks before launch: runtime health, validation state, paths, disk/output checks;
- more reliable `start / cancel / retry / rerun from history` flows;
- persist exact generated input, run config, and command line for every run;
- improve user-facing failures instead of exposing overly technical errors;
- add integration smoke tests for success, cancel, timeout, broken runtime, missing output, and failed merge scenarios.

Exit criteria:

- a new user can create a project, launch a simulation, cancel or retry it without CLI usage;
- every run clearly shows what was launched;
- failures are explained well enough through the UI for the user to know what to do next.

## Milestone 2: Scene Editor Core UX

Window:

- Weeks 3-5

GitHub milestone:

- `v0.5 - Scene Editor Core UX`

Epics:

- `scene-undo-redo`
- `scene-multi-select-and-group-actions`
- `scene-keyboard-workflow`
- `scene-precision-editing`
- `scene-3d-navigation-foundation`

Scope:

- full `undo/redo` for scene actions and inspector edits;
- multi-select, marquee selection, group move/delete/duplicate;
- keyboard workflow for delete, duplicate, undo/redo, nudge, mode switching, and fit;
- axis locking, proportional resize, stronger snapping, and exact dimension editing from canvas interactions;
- depth/slice controls and better mapping between 2D plane editing and the underlying 3D model.

Exit criteria:

- a typical model can be built through the canvas faster and more safely than through raw input;
- users are not afraid to edit the scene because every action is reversible;
- the editor supports both quick visual manipulation and precise numeric editing.

## Milestone 3: Results Analysis V2

Window:

- Weeks 6-8

GitHub milestone:

- `v0.6 - Results Analysis V2`

Epics:

- `ascan-analysis-tools`
- `bscan-visual-controls`
- `results-comparison-workflow`
- `results-traceability`
- `reporting-and-export`

Scope:

- for A-scan: cursors, delta measurements, peak picking, FFT/spectrum, CSV/PNG export;
- for B-scan: gain, contrast, colormap presets, time-zero/background controls;
- side-by-side and overlay comparison workflows across runs;
- explicit links from results back to run configuration, generated input, and metadata;
- export images, plots, and compact summaries for reports and issue reports.

Exit criteria:

- users can meaningfully analyze outputs inside the app, not just open them;
- run-to-run comparison becomes a built-in workflow instead of a manual external step;
- results can be exported cleanly for publications, reports, and bug reports.

## Milestone 4: OSS Readiness and Stabilization

Window:

- Weeks 9-10

GitHub milestone:

- `v0.7 - OSS Readiness and Stabilization`

Epics:

- `quality-gates-and-ci`
- `sample-projects-and-guides`
- `project-format-stability`
- `supportability`

Scope:

- CI with `tests`, linting, and type checks;
- 2-3 example projects and short user workflows in the documentation;
- manifest versioning and a foundation for migration hooks;
- crash/log bundles, issue templates, and a reproducible bug-report checklist.

Exit criteria:

- external users can understand how to start quickly;
- external contributors can get the project running locally and contribute without hidden context;
- the product handles project format evolution and user failures more safely.

### Explicitly deferred

- Windows packaging and installer work;
- bundled engine distribution;
- broad coverage of rare or edge-case `gprMax` commands before the core workflow is stable;
- large architectural rewrites without pressure from real user scenarios.

### Suggested GitHub Labels / Milestones

- `v0.4 - Simulation Workflow Hardening`
- `v0.5 - Scene Editor Core UX`
- `v0.6 - Results Analysis V2`
- `v0.7 - OSS Readiness and Stabilization`

Cross-milestone epics:

- `guided-editor-command-coverage`
- `project-migration-and-compatibility`
- `user-facing-diagnostics-and-recovery`
