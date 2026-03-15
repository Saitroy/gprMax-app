# Model Editor MVP

## Русский

## Scope

Model Editor Stage 4 — это guided, form-based MVP для наиболее полезного subset моделирования `gprMax`.

Сейчас поддерживается:

- general model setup: title, domain size, `dx_dy_dz`, `time_window`;
- materials;
- waveforms;
- sources;
- receivers;
- geometry subset: `box`, `sphere`, `cylinder`;
- generated input preview из текущего in-memory model state.

Сознательно отложено:

- 2D/3D canvas editing;
- drag-and-drop scene composition;
- широкий coverage всех `gprMax` commands;
- antenna libraries и external geometry import;
- полноценный advanced raw-input IDE.

## UX structure

Editor использует tabs на верхнем уровне и list-detail editing внутри entity sections.

Почему так:

- top-level tabs делают workflow понятным для непограммистов;
- list-detail panels масштабируются лучше, чем одна гигантская форма;
- MVP остаётся расширяемым, не притворяясь finished CAD environment.

Текущие tabs:

- `General`
- `Materials`
- `Waveforms`
- `Sources`
- `Receivers`
- `Geometry`
- `Input Preview`

## Границы data/services

Editor работает поверх typed project model, введённой на Stage 2 и расширенной на Stage 4.

Правила:

- widgets изменяют project state через `ModelEditorService`;
- validation остаётся в domain/application layer;
- input preview генерируется через `InputPreviewService`;
- save/load flows остаются ответственностью workspace/project services;
- simulation execution остаётся ответственностью Stage 3 runner.

## Validation strategy

Editor валидирует и локальное качество полей, и cross-entity references.

Примеры:

- положительные значения domain и resolution;
- уникальные material и waveform identifiers;
- источники, ссылающиеся на известные waveforms;
- geometry, ссылающаяся на известные materials;
- координаты внутри domain;
- базовые shape-specific constraints, например положительный radius и упорядоченные box bounds.

## Handoff Stage 4 -> Stage 5

После Stage 4 проект уже имеет минимальный editor foundation для реального user workflow:

1. создать или открыть проект;
2. редактировать модель через формы;
3. просматривать validation issues;
4. делать preview generated input;
5. сохранять;
6. запускать через существующий Stage 3 simulation view.

Это позволило Stage 5 заняться results browsing, не изобретая сначала usable model-authoring flow.

## English

## Scope

The Stage 4 model editor is a guided, form-based MVP for the most useful `gprMax` modelling subset.

Supported now:

- general model setup: title, domain size, `dx_dy_dz`, `time_window`;
- materials;
- waveforms;
- sources;
- receivers;
- geometry subset: `box`, `sphere`, `cylinder`;
- generated input preview from the current in-memory model.

Deferred intentionally:

- 2D/3D canvas editing;
- drag-and-drop scene composition;
- broad coverage of every `gprMax` command;
- antenna libraries and external geometry import;
- full advanced raw-input IDE.

## UX structure

The editor uses tabs at the top level and list-detail editing inside entity sections.

Why this shape:

- top-level tabs keep the workflow legible for non-programmers;
- list-detail panels scale better than one giant form;
- the MVP stays extensible without pretending to be a finished CAD environment.

Current tabs:

- `General`
- `Materials`
- `Waveforms`
- `Sources`
- `Receivers`
- `Geometry`
- `Input Preview`

## Data and service boundaries

The editor works against the typed project model already introduced in Stage 2 and extended in Stage 4.

Rules:

- widgets mutate project state through `ModelEditorService`;
- validation stays in the domain/application layer;
- input preview is generated through `InputPreviewService`;
- save/load flows remain owned by workspace/project services;
- simulation execution remains owned by the Stage 3 runner.

## Validation strategy

The editor validates both local field quality and cross-entity references.

Examples:

- positive domain and resolution values;
- unique material and waveform identifiers;
- sources referencing known waveforms;
- geometry referencing known materials;
- coordinates staying inside the domain;
- basic shape-specific constraints such as positive radius and ordered box bounds.

## Stage 4 to Stage 5 handoff

After Stage 4, the project has the minimum editor foundation needed for real user workflows:

1. create or open a project;
2. edit the model through forms;
3. review validation issues;
4. preview the generated input;
5. save;
6. run through the existing Stage 3 simulation view.

Stage 5 can now focus on results browsing without first inventing a usable model-authoring flow.
