# Runtime And Packaging

## Русский

## Цель Stage 6

Приложение должно поставляться как единый desktop-продукт. Пользователь не должен отдельно устанавливать `gprMax`, Python, Git, Conda или вручную искать пути к вычислительному ядру.

Базовый сценарий продукта:

1. пользователь устанавливает приложение через installer;
2. приложение уже содержит встроенное вычислительное ядро;
3. GUI автоматически находит встроенный runtime;
4. обычный CPU-сценарий запуска работает из коробки;
5. GPU и MPI остаются опциональными capability-расширениями.

## Принятая стратегия

- execution остаётся `subprocess-first`;
- runtime становится `bundled-first`;
- основной путь запуска: встроенный Python executable внутри install layout;
- `gprMax` считается частью managed engine bundle;
- внешний Python/gprMax допускается только как optional advanced fallback и development path.

Это сохраняет стабильный CLI-контракт `python -m gprMax ...`, но убирает зависимость от пользовательского окружения как основного сценария.

## Install Layout

Windows-first layout для installer/portable bundle:

```text
<install-root>/
  GPRMax Workbench.exe
  engine/
    manifest.json
    python/
      Scripts/
        python.exe
      Lib/
      Include/
      pyvenv.cfg
      Lib/site-packages/
        gprMax/
    licenses/
```

Пользовательские данные не должны храниться внутри installation directory:

```text
%LOCALAPPDATA%/gprmax_workbench/
  settings.json
  logs/
  cache/
  temp/
```

Проекты и артефакты запусков продолжают жить в выбранном каталоге проекта:

```text
<project-root>/
  project.gprwb.json
  runs/
  results/
  generated/
  assets/
```

## Runtime Resolution

Порядок выбора runtime:

1. встроенный `engine/python/...`;
2. если встроенный runtime отсутствует и включён advanced mode, используется явно заданный внешний fallback Python;
3. если и он не задан, development-сборка может использовать текущий интерпретатор как fallback, но это не считается production baseline.

## Build-time vs user-time requirements

Требования `gprMax` к C compiler/OpenMP/MSVC относятся к build/release-машине, а не к машине пользователя.

Для первого Windows рабочего билда это означает:

- build-агент или release workstation устанавливает CPython 3.11 x64;
- там же стоят Microsoft Build Tools и Windows SDK;
- там создаётся `engine/python` venv;
- там компилируются Cython extensions `gprMax`;
- в installer попадает уже готовый `engine/` bundle.

Пользователь получает только результат этой сборки.

## Capability Model

- `CPU`: обязательный bundled baseline.
- `GPU`: опционально. Зависит от bundled environment и наличия GPU-specific dependencies.
- `MPI`: опционально. Зависит от bundled environment и MPI-related dependencies.

Отсутствие GPU/MPI не должно блокировать базовый сценарий CPU.

## Diagnostics

Stage 6 добавляет runtime diagnostics report, который показывает:

- текущий runtime mode;
- install root и engine root;
- путь к Python executable;
- версию приложения;
- версию engine bundle из `engine/manifest.json`, если она доступна;
- обнаруженную версию `gprMax`, если модуль импортируется;
- capability state для CPU/GPU/MPI;
- понятные сообщения о missing/corrupt runtime.

## Зачем нужен `engine/manifest.json`

Manifest не обязателен для dev-сборки, но обязателен для installer-oriented distribution. Он должен связывать:

- версию desktop app release;
- версию bundled engine;
- версию `gprMax`;
- версию Python runtime;
- release/build metadata;
- ссылки на bundled license notices.

Это упрощает future updates и compatibility tracking.

## Ограничения текущего этапа

- здесь ещё нет полноценного production installer;
- нет auto-update механизма;
- нет полного GPU/MPI deployment story;
- нет автоматического скачивания/сборки bundled engine в CI.

Stage 6 создаёт foundation, а не закрывает весь release engineering pipeline.

## References

- `gprMax` documentation: https://docs.gprmax.com/en/latest/
- installation guidance: https://docs.gprmax.com/en/latest/include_readme.html
- GPU notes: https://docs.gprmax.com/en/latest/gpu.html
- OpenMP/MPI notes: https://docs.gprmax.com/en/latest/openmp_mpi.html

## English

## Stage 6 Goal

The application must ship as a single desktop product. Users should not separately install `gprMax`, Python, Git, Conda, or manually configure engine paths.

Base product flow:

1. the user installs the application through an installer;
2. the application already contains the compute engine;
3. the GUI automatically resolves the bundled runtime;
4. the default CPU path works out of the box;
5. GPU and MPI remain optional capability extensions.

## Adopted Strategy

- execution stays `subprocess-first`;
- runtime becomes `bundled-first`;
- the default launch path uses an internal Python executable from the install layout;
- `gprMax` is treated as part of a managed engine bundle;
- external Python/gprMax remains only an optional advanced fallback and development path.

This keeps the stable public CLI contract `python -m gprMax ...` while removing the user environment as the primary runtime dependency.

## Install Layout

Windows-first layout for installer/portable distribution:

```text
<install-root>/
  GPRMax Workbench.exe
  engine/
    manifest.json
    python/
      Scripts/
        python.exe
      Lib/
      Include/
      pyvenv.cfg
      Lib/site-packages/
        gprMax/
    licenses/
```

User data must stay outside the installation directory:

```text
%LOCALAPPDATA%/gprmax_workbench/
  settings.json
  logs/
  cache/
  temp/
```

Projects and run artifacts continue to live in the chosen project directory:

```text
<project-root>/
  project.gprwb.json
  runs/
  results/
  generated/
  assets/
```

## Runtime Resolution

Runtime selection order:

1. bundled `engine/python/...`;
2. if the bundled runtime is missing and advanced mode is enabled, use the configured external fallback Python;
3. if neither is available, development builds may use the current interpreter as a fallback, but this is not a production baseline.

## Build-time vs user-time requirements

The `gprMax` requirement for a C compiler, OpenMP, and MSVC applies to the build/release machine, not to the end-user machine.

For the first working Windows build this means:

- the build agent or release workstation installs CPython 3.11 x64;
- the same machine has Microsoft Build Tools and Windows SDK installed;
- it creates the `engine/python` venv;
- it compiles the `gprMax` Cython extensions;
- the installer ships the finished `engine/` bundle.

The user receives only the build output.

## Capability Model

- `CPU`: required bundled baseline.
- `GPU`: optional, depends on bundled environment and GPU-specific dependencies.
- `MPI`: optional, depends on bundled environment and MPI-related dependencies.

Missing GPU/MPI support must not break the base CPU workflow.

## Diagnostics

Stage 6 adds a runtime diagnostics report showing:

- current runtime mode;
- install root and engine root;
- Python executable path;
- application version;
- engine bundle version from `engine/manifest.json`, when present;
- detected `gprMax` version, when the module can be imported;
- CPU/GPU/MPI capability states;
- clear messages for missing or corrupted runtime state.

## Why `engine/manifest.json` Exists

The manifest is optional in development, but required for installer-oriented distributions. It should connect:

- desktop app release version;
- bundled engine version;
- `gprMax` version;
- Python runtime version;
- release/build metadata;
- bundled license notice references.

This simplifies future updates and compatibility tracking.

## Current Limits

- there is no full production installer yet;
- there is no auto-update mechanism;
- there is no full GPU/MPI deployment story;
- there is no CI pipeline yet that builds or downloads the bundled engine automatically.

Stage 6 creates the foundation, not the entire release engineering pipeline.

## References

- `gprMax` documentation: https://docs.gprmax.com/en/latest/
- installation guidance: https://docs.gprmax.com/en/latest/include_readme.html
- GPU notes: https://docs.gprmax.com/en/latest/gpu.html
- OpenMP/MPI notes: https://docs.gprmax.com/en/latest/openmp_mpi.html
