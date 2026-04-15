# GPRMax Workbench Alpha 0.2.1

Приложение доступно на двух языках: русский и английский.
The application is available in two languages: Russian and English.

## Русский

### Назначение релиза

Эта сборка предназначена для управляемого alpha-тестирования на Windows x64 и закрывает UX-fix milestone после Alpha `0.2.0`.

Она подходит для геологов, геофизиков, студентов и ранних партнёров по тестированию, которым нужен desktop-интерфейс вокруг `gprMax` без CLI-first сценария работы.

Это ещё не первый публичный bundled production release. Следующий целевой milestone — Alpha `0.3.0` Installer Candidate, где главный фокус будет на installer-first сценарии.

### Рекомендуемые метаданные GitHub prerelease

- Заголовок релиза: `GPRMax Workbench Alpha 0.2.1`
- Тип релиза: GitHub `pre-release`
- Рекомендуемые assets:
  - Windows installer `gprmax-workbench-0.2.1-windows-x64.exe`
  - `release-manifest.json`
  - generated license inventories для runtime приложения и engine
  - checksum file для опубликованных артефактов
  - эти alpha release notes как body релиза

Рекомендуемый prerelease tag: `v0.2.1-alpha.1`. Application version metadata синхронизирована как `0.2.1`.

### Что могут протестировать alpha-тестеры

- создать новый проект из `Welcome`
- открыть существующий проект и работать с recent projects
- пройти сценарий “создать модель -> настроить материалы -> разместить источник/приёмник -> проверить сцену -> сохранить”
- редактировать модель через guided workspace sections
- проверить подписи сцены, фильтры слоёв и summary состояния модели
- просматривать и экспортировать сгенерированный `gprMax` input
- запускать CPU simulations с live logs и run history
- анализировать outputs через `Results`, включая A-scan и bounded B-scan workflows
- смотреть runtime diagnostics через `Settings`

### Что уже проверено для этого alpha-кандидата

- `python -m ruff check src tests packaging tools` прошёл успешно
- `.venv\Scripts\python.exe tools\run_tests.py` прошёл: `119` tests OK
- локальная сборка Windows desktop bundle прошла успешно
- bundle smoke test прошёл успешно
- сборка Windows installer прошла успешно
- silent install, launch и uninstall dry-run прошли на рабочей машине сопровождающего

### Известные ограничения

- размеры splitter'ов пока не сохраняются между сессиями
- покрытие guided editor пока намеренно неполное относительно полного набора возможностей `gprMax`
- workflows анализа и экспорта результатов пока ограничены
- installer для alpha-тестеров может быть неподписанным; code signing переносится на beta-подготовку
- clean-machine validation вне рабочей машины сопровождающего остаётся обязательным gate для Alpha `0.3.0`
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

Используйте [GitHub Issues](https://github.com/Saitroy/gprMax-app/issues) и прикладывайте:

- версию приложения, например `0.2.1`
- версию Windows
- краткое описание того, что вы делали
- screenshots, если они помогают понять проблему
- проект или run, где возникла ошибка, если это известно
- logs или support bundle, если они доступны

## English

### Release intent

This build is intended for guided alpha testing on Windows x64 and closes the UX-fix milestone after Alpha `0.2.0`.

It is suitable for geologists, geophysicists, students, and early design partners who need a desktop workflow around `gprMax` without working directly through a CLI-first setup.

This is not yet the first public bundled production release. The next target milestone is Alpha `0.3.0` Installer Candidate, focused on the installer-first path.

### Suggested GitHub prerelease metadata

- Release title: `GPRMax Workbench Alpha 0.2.1`
- Release type: GitHub `pre-release`
- Suggested assets:
  - Windows installer `gprmax-workbench-0.2.1-windows-x64.exe`
  - `release-manifest.json`
  - generated license inventories for app and engine runtimes
  - checksum file for the published artifacts
  - these alpha release notes as the release body

Recommended prerelease tag: `v0.2.1-alpha.1`. Application version metadata is aligned as `0.2.1`.

### What alpha testers can do

- create a new project from `Welcome`
- open an existing project and work with recent projects
- complete the “create model -> configure materials -> place source/receiver -> check scene -> save” workflow
- edit the model through guided workspace sections
- check scene labels, layer filters, and model-state summary
- preview and export generated `gprMax` input
- run CPU simulations with live logs and run history
- inspect outputs through `Results`, including A-scan and bounded B-scan workflows
- inspect runtime diagnostics through `Settings`

### Validation completed for this alpha candidate

- `python -m ruff check src tests packaging tools` passed
- `.venv\Scripts\python.exe tools\run_tests.py` passed: `119` tests OK
- local Windows desktop bundle build passed
- bundle smoke test passed
- Windows installer build passed
- silent install, launch, and uninstall dry-run passed on the maintainer workstation

### Known limits

- splitter sizes are not yet persisted between sessions
- guided editor coverage is still intentionally partial relative to the full `gprMax` command surface
- broader results analysis and export workflows are still limited
- the alpha installer may be unsigned for trusted testers; code signing is deferred to beta preparation
- clean-machine validation outside the maintainer workstation remains a required gate for Alpha `0.3.0`
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

Please use [GitHub Issues](https://github.com/Saitroy/gprMax-app/issues) and include:

- application version, for example `0.2.1`
- Windows version
- a short description of what you were doing
- screenshots when relevant
- the project or run where the problem occurred, if known
- logs or a support bundle when available
