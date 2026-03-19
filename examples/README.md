# Examples

## Русский

В этой директории лежат переносимые example-проекты для `GPRMax Workbench`.

Что включено:

- `cylinder_ascan_2d/` — готовый A-scan проект на основе `gprMax` reference-модели `cylinder_Ascan_2D`.
- `cylinder_bscan_2d/` — готовый B-scan проект на основе `gprMax` reference-модели `cylinder_Bscan_2D`.
- `screenshots/` — реальные скриншоты Results Viewer, снятые после прогонов встроенным ядром.
- `summary.json` — краткая машинно-читаемая сводка по example-проектам.

Особенности:

- Оба проекта уже содержат сохранённые run artifacts, поэтому их можно открыть в приложении и сразу перейти в `Результаты`.
- `cylinder_bscan_2d` использует advanced raw overrides для `#src_steps` и `#rx_steps`, потому что в текущем Model Editor для них ещё нет отдельной guided-формы.
- Run metadata в examples сохранены в переносимом виде с относительными путями, чтобы проекты открывались из любого расположения репозитория.

Рекомендуемый сценарий:

1. Открыть в приложении папку `examples/cylinder_ascan_2d`.
2. Посмотреть `Редактор модели`, затем `Симуляция`, затем `Результаты`.
3. Повторить для `examples/cylinder_bscan_2d`.

## English

This directory contains portable example projects for `GPRMax Workbench`.

Included:

- `cylinder_ascan_2d/` — a ready-to-open A-scan project based on the `gprMax` `cylinder_Ascan_2D` reference model.
- `cylinder_bscan_2d/` — a ready-to-open B-scan project based on the `gprMax` `cylinder_Bscan_2D` reference model.
- `screenshots/` — actual Results Viewer screenshots captured after running the bundled engine.
- `summary.json` — a compact machine-readable summary of the example projects.

Notes:

- Both projects already contain saved run artifacts, so they can be opened in the app and inspected immediately in `Results`.
- `cylinder_bscan_2d` uses advanced raw overrides for `#src_steps` and `#rx_steps`, because the current Model Editor does not yet expose dedicated guided controls for them.
- Run metadata inside the examples use relative paths so the projects remain portable across different repository locations.
