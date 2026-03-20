# Advanced Editor Foundation

## Русский

### Что добавлено

- `Сцена`: orthographic multi-plane canvas `XY/XZ/YZ` с drag-and-drop добавлением объектов и перемещением маркеров сущностей.
- `Библиотеки и импорт`: typed editor для `#geometry_objects_read` и библиотечных антенн.
- `Advanced`: command-template registry + raw command workspace + Python blocks workspace.

### Архитектурные решения

- Canvas редактирует typed project model через `ModelEditorService`, а не напрямую меняет input text.
- Широкий coverage команд достигается не сотнями форм, а `GprMaxCommandRegistry` и advanced workspace.
- Антенны сериализуются в `#python` blocks, geometry import — в `#geometry_objects_read`.
- Advanced workspace хранится в проекте как `python_blocks` и `advanced_input_overrides`, поэтому сохраняется, попадает в preview и уходит в runner без отдельного скрытого состояния.

### Ограничения текущего этапа

- 3D реализован как multi-plane orthographic foundation, не как полноценный interactive 3D viewport.
- Dragging geometry меняет anchor/center объекта, но не даёт ещё полноценного resize/rotate editing.
- Command registry покрывает широкий практический subset, а оставшиеся команды по-прежнему можно вводить вручную в advanced workspace.

## English

### What was added

- `Scene`: an orthographic multi-plane `XY/XZ/YZ` canvas with drag-and-drop entity placement and movable entity anchors.
- `Libraries and import`: a typed editor for `#geometry_objects_read` and library-based antenna models.
- `Advanced`: a command-template registry plus raw command and Python block workspaces.

### Architectural decisions

- The canvas edits the typed project model through `ModelEditorService`; it does not mutate generated input text directly.
- Broad command coverage is achieved through `GprMaxCommandRegistry` and the advanced workspace instead of hundreds of dedicated forms.
- Antenna models are serialized into `#python` blocks, while geometry imports are emitted as `#geometry_objects_read`.
- The advanced workspace is stored in the project as `python_blocks` and `advanced_input_overrides`, so it persists, appears in preview, and flows into the runner without hidden UI-only state.

### Current limitations

- 3D is implemented as a multi-plane orthographic foundation, not a full interactive 3D viewport.
- Dragging geometry updates the entity anchor/center, but not full resize/rotate editing yet.
- The command registry covers a broad practical subset; any remaining commands can still be authored manually in the advanced workspace.

## Phase 2

### Русский

- `Сцена` получила selection inspector: точное редактирование координат, snap-to-grid, nudge по шагу, duplicate/delete.
- `Libraries and import` теперь показывает реальные previews:
  - команду `#geometry_objects_read`;
  - состояние файлов геометрии и материалов;
  - catalog summary и Python preview для антенн.
- `Advanced` теперь умеет работать не только как raw text area, но и как block-organized workspace:
  - списки command blocks и Python blocks;
  - перемещение блоков вверх/вниз;
  - удаление блоков;
  - сохранение порядка в проекте.

### English

- `Scene` now includes a selection inspector with exact coordinate editing, snap-to-grid, step-based nudging, and duplicate/delete actions.
- `Libraries and import` now exposes real previews:
  - the generated `#geometry_objects_read` command;
  - geometry/material file status;
  - catalog summary and Python preview for antenna models.
- `Advanced` now works not only as a raw text area but also as a block-organized workspace:
  - command block and Python block lists;
  - move up/down actions;
  - block deletion;
  - order preservation in the project model.
