# GPRMax Workbench 0.1.0 Alpha

Приложение доступно на двух языках: русский и английский.
The application is available in two languages: Russian and English.

## RUS

### Назначение релиза

Эта сборка предназначена для управляемого alpha-тестирования на Windows x64.

Она подходит для геологов, геофизиков, студентов и ранних партнёров по тестированию, которым нужен desktop-интерфейс вокруг `gprMax` без CLI-first сценария работы.

Это ещё не первый публичный bundled production release.

### Рекомендуемые метаданные GitHub prerelease

- Заголовок релиза: `GPRMax Workbench 0.1.0 Alpha`
- Тип релиза: GitHub `pre-release`
- Рекомендуемые assets:
  - Windows installer `gprmax-workbench-0.1.0-windows-x64.exe`
  - `release-manifest.json`
  - generated license inventories для runtime приложения и engine
  - checksum file для опубликованных артефактов
  - эти alpha release notes как body релиза

Если вы хотите alpha-версионирование на GitHub, используйте prerelease tag, например `v0.1.0-alpha.1`, и заранее согласуйте application version metadata перед публикацией финального тега.

### Что могут протестировать alpha-тестеры

- создать новый проект из `Welcome`
- открыть существующий проект и работать с recent projects
- редактировать модель через guided workspace sections
- просматривать и экспортировать сгенерированный `gprMax` input
- запускать CPU simulations с live logs и run history
- анализировать outputs через `Results`, включая A-scan и bounded B-scan workflows
- смотреть runtime diagnostics через `Settings`

### Что уже проверено для этого alpha-кандидата

- `python -m ruff check src tests packaging tools` прошёл успешно
- `python -m unittest discover tests` прошёл с результатом `107 OK`
- локальная сборка Windows desktop bundle прошла успешно
- bundle smoke test прошёл успешно
- сборка Windows installer прошла успешно
- silent install, launch и uninstall dry-run прошли на рабочей машине сопровождающего

### Известные ограничения

- размеры splitter'ов пока не сохраняются между сессиями
- покрытие guided editor пока намеренно неполное относительно полного набора возможностей `gprMax`
- workflows анализа и экспорта результатов пока ограничены
- clean-machine validation вне рабочей машины сопровождающего всё ещё не завершена
- licensing и compliance sign-off всё ещё обязательны перед первым публичным bundled release

### На что тестерам стоит обратить внимание

- создание проектов и повторное открытие проектов
- flow редактирования модели для типовых учебных и полевых сценариев
- понятность simulation readiness feedback и live logs
- удобство просмотра результатов на реальных project data
- installer experience на обычных Windows x64 машинах
- runtime diagnostics в неполной или нестандартной среде

### Примечания по установке

- поддерживаемая alpha-платформа: Windows x64
- bundled application должна работать без отдельной установки Python или `gprMax`
- optional Visual Studio Build Tools task нужен только для advanced engine rebuild или repair workflows

### Сообщения об ошибках

Используйте GitHub issue templates этого репозитория и прикладывайте:

- краткое описание того, что вы делали
- screenshots, если они помогают понять проблему
- проект или run, где возникла ошибка, если это известно
- logs или support bundle, если они доступны

## ENG

### Release intent

This build is intended for guided alpha testing on Windows x64.

It is suitable for geologists, geophysicists, students, and early design partners who need a desktop workflow around `gprMax` without working directly through a CLI-first setup.

This is not yet the first public bundled production release.

### Suggested GitHub prerelease metadata

- Release title: `GPRMax Workbench 0.1.0 Alpha`
- Release type: GitHub `pre-release`
- Suggested assets:
  - Windows installer `gprmax-workbench-0.1.0-windows-x64.exe`
  - `release-manifest.json`
  - generated license inventories for app and engine runtimes
  - checksum file for the published artifacts
  - these alpha release notes as the release body

If you want alpha-specific versioning on GitHub, prefer a prerelease tag such as `v0.1.0-alpha.1` and align application version metadata before publishing the final tag.

### What alpha testers can do

- create a new project from `Welcome`
- open an existing project and work with recent projects
- edit the model through guided workspace sections
- preview and export generated `gprMax` input
- run CPU simulations with live logs and run history
- inspect outputs through `Results`, including A-scan and bounded B-scan workflows
- inspect runtime diagnostics through `Settings`

### Validation completed for this alpha candidate

- `python -m ruff check src tests packaging tools` passed
- `python -m unittest discover tests` passed with `107 OK`
- local Windows desktop bundle build passed
- bundle smoke test passed
- Windows installer build passed
- silent install, launch, and uninstall dry-run passed on the maintainer workstation

### Known limits

- splitter sizes are not yet persisted between sessions
- guided editor coverage is still intentionally partial relative to the full `gprMax` command surface
- broader results analysis and export workflows are still limited
- clean-machine validation outside the maintainer workstation is still pending
- licensing and compliance sign-off are still required before a first public bundled release

### Tester focus areas

- project creation and project reopening
- model editing flow for common classroom and field scenarios
- simulation readiness feedback and live log clarity
- results browsing on real project data
- installer experience on typical Windows x64 machines
- runtime diagnostics when the environment is incomplete or unusual

### Installation notes

- Windows x64 is the supported alpha target
- the bundled application is intended to run without requiring a separate Python or `gprMax` installation
- the optional Visual Studio Build Tools task is only for advanced engine rebuild or repair workflows

### Bug reporting

Please use the GitHub issue templates in this repository and include:

- a short description of what you were doing
- screenshots when relevant
- the project or run where the problem occurred, if known
- logs or a support bundle when available
