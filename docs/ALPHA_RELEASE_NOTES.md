# GPRMax Workbench Alpha 0.3.0

> Приложение доступно на двух языках: русском и английском.  
> The application is available in two languages: Russian and English.

## Русский

### Назначение релиза

Alpha `0.3.0` — installer-first сборка для управляемого тестирования на Windows x64.

Главная цель этой версии: дать тестерам один установочный файл, проверить bundled runtime без отдельной установки Python или `gprMax`, собрать обратную связь по установке, запуску, диагностике runtime и базовому рабочему сценарию `Welcome -> Project -> Simulation -> Results`.

Это prerelease для доверенных тестеров, не первый публичный production release.

### GitHub prerelease

- Заголовок релиза: `GPRMax Workbench Alpha 0.3.0`
- Тип релиза: GitHub `pre-release`
- Рекомендуемый tag: `v0.3.0-alpha.1`
- Application version metadata: `0.3.0`
- Bundled engine: `gprMax 3.1.7`

### Assets для публикации

- `gprmax-workbench-0.3.0-windows-x64.exe`
- `release-manifest.json`
- `inventory-app-python.json`
- `inventory-engine-python.json`
- `SHA256SUMS.txt`
- эти release notes как body релиза

### Что тестировать

- установку на Windows x64 через installer;
- запуск приложения без ручной настройки Python, `gprMax` или `PATH`;
- создание нового проекта из `Welcome`;
- открытие существующего проекта и recent projects;
- редактирование модели в секциях `Project`;
- preview/export сгенерированного `gprMax` input;
- CPU simulation flow с live logs и run history;
- просмотр результатов через `Results`, включая A-scan и bounded B-scan workflows;
- runtime diagnostics в `Settings`;
- сбор support bundle при воспроизводимой проблеме.

### Проверено для этого кандидата

- `.venv\Scripts\python.exe -m pip install -e .[dev,release]` синхронизировал package metadata на `0.3.0`.
- `.venv\Scripts\python.exe -m ruff check src tests packaging tools` прошёл успешно.
- `.venv\Scripts\python.exe tools\run_tests.py` прошёл: `120` tests OK.
- Windows desktop bundle собран в `dist/windows-0.3.0-release/GPRMax Workbench`.
- `packaging/windows/smoke_test_bundle.ps1` прошёл в составе bundle build.
- Windows installer собран в `dist/installer-0.3.0-release`.
- Release assets, manifest, license inventories и checksums находятся рядом в `dist/installer-0.3.0-release`.

### Известные ограничения

- installer для alpha-тестеров неподписанный; code signing остаётся задачей beta/public-release подготовки;
- clean-machine install/launch/uninstall проверка на отдельной Windows VM не выполнялась в этом локальном прогоне;
- guided editor покрывает не весь command surface `gprMax`;
- splitter/layout state пока не полностью сохраняется между сессиями;
- результаты и экспорт анализа пока ограничены текущими A-scan и bounded B-scan workflows;
- licensing/compliance sign-off всё ещё нужен перед публичным bundled release.

### Баг-репорты

Используйте [GitHub Issues](https://github.com/Saitroy/gprMax-app/issues) и прикладывайте:

- версию приложения `0.3.0`;
- версию Windows;
- install type: bundled installer build;
- key runtime diagnostics из `Settings`;
- шаги воспроизведения;
- screenshots, logs или support bundle, если доступны.

## English

### Release Intent

Alpha `0.3.0` is the installer-first build for guided Windows x64 testing.

The main goal is to give testers one installer file, validate the bundled runtime without a separate Python or `gprMax` setup, and collect feedback on installation, launch, runtime diagnostics, and the baseline `Welcome -> Project -> Simulation -> Results` workflow.

This is a trusted-tester prerelease, not the first public production release.

### GitHub Prerelease

- Release title: `GPRMax Workbench Alpha 0.3.0`
- Release type: GitHub `pre-release`
- Recommended tag: `v0.3.0-alpha.1`
- Application version metadata: `0.3.0`
- Bundled engine: `gprMax 3.1.7`

### Assets To Publish

- `gprmax-workbench-0.3.0-windows-x64.exe`
- `release-manifest.json`
- `inventory-app-python.json`
- `inventory-engine-python.json`
- `SHA256SUMS.txt`
- these release notes as the release body

### Tester Focus

- install on Windows x64 through the installer;
- launch without configuring Python, `gprMax`, or `PATH`;
- create a new project from `Welcome`;
- open an existing project and recent projects;
- edit the model in `Project` sections;
- preview/export generated `gprMax` input;
- run the CPU simulation flow with live logs and run history;
- inspect outputs through `Results`, including A-scan and bounded B-scan workflows;
- inspect runtime diagnostics in `Settings`;
- collect a support bundle for reproducible issues.

### Validation Completed For This Candidate

- `.venv\Scripts\python.exe -m pip install -e .[dev,release]` synchronized package metadata to `0.3.0`.
- `.venv\Scripts\python.exe -m ruff check src tests packaging tools` passed.
- `.venv\Scripts\python.exe tools\run_tests.py` passed: `120` tests OK.
- Windows desktop bundle was built at `dist/windows-0.3.0-release/GPRMax Workbench`.
- `packaging/windows/smoke_test_bundle.ps1` passed as part of the bundle build.
- Windows installer was built at `dist/installer-0.3.0-release`.
- Release assets, manifest, license inventories, and checksums are staged together in `dist/installer-0.3.0-release`.

### Known Limits

- the alpha installer is unsigned; code signing remains deferred to beta/public-release preparation;
- clean-machine install/launch/uninstall validation on a separate Windows VM was not performed in this local pass;
- guided editor coverage is still partial relative to the full `gprMax` command surface;
- splitter/layout state is not fully persisted between sessions yet;
- broader results analysis and export workflows are still limited to the current A-scan and bounded B-scan paths;
- licensing/compliance sign-off is still required before a public bundled release.

### Bug Reporting

Please use [GitHub Issues](https://github.com/Saitroy/gprMax-app/issues) and include:

- application version `0.3.0`;
- Windows version;
- install type: bundled installer build;
- key runtime diagnostics from `Settings`;
- reproduction steps;
- screenshots, logs, or a support bundle when available.
