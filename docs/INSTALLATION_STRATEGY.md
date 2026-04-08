# Installation Strategy

## Русский

## Продуктовый принцип

Installer должен ставить готовый к работе desktop-продукт. Пользователь не должен:

- ставить Python;
- ставить `gprMax` вручную;
- настраивать `PATH`;
- разбираться с Git, Conda или терминалом.

## Windows-first стратегия

Для первых релизов приоритетен Windows installer c one-folder install layout. Это лучше подходит для:

- PySide6 desktop app;
- bundled Python runtime;
- отдельного каталога `engine/`;
- прозрачного обновления app и engine как одного release artifact.

## Что должно попасть в дистрибутив

- приложение;
- ресурсы UI;
- bundled Python runtime;
- установленный внутрь него и уже собранный `gprMax`;
- зависимости, необходимые для CPU-first baseline;
- bundled licenses/notices для open-source dependencies;
- `engine/manifest.json`.

## Что не должно попадать в пользовательский workflow

- `pip install`;
- `conda create`;
- `git clone`;
- сборка Cython extensions;
- установка MSVC Build Tools;
- ручной выбор Python executable как обязательный шаг.

## Сборка engine bundle

`gprMax` требует сборки Cython-модулей на Windows через MSVC/OpenMP toolchain. Поэтому:

- source repo `gprMax` используется только на build/release-стороне;
- release-сторона собирает managed `engine/python` venv;
- installer включает уже готовый bundle;
- пользователь не взаимодействует с `setup.py build/install`.

## Обновления

На данном этапе считается, что desktop app release и bundled engine release публикуются вместе. Это даёт простую модель совместимости:

- один installer;
- одна протестированная связка app + engine;
- одна documented compatibility matrix.

В будущем engine updates можно вынести в отдельную managed стратегию, но не раньше, чем появится стабильный release process.

## Open-source и лицензии

Так как проект open-source и в дистрибутив входит `gprMax` плюс другие зависимости, release structure должна предусматривать:

- bundled license texts/notices;
- явную фиксацию версий engine/dependencies;
- воспроизводимый build recipe для community contributors.

Это архитектурное требование. Юридические детали оформляются отдельно в release process.

## English

## Product Principle

The installer must deliver a ready-to-run desktop product. The user should not need to:

- install Python;
- install `gprMax` manually;
- configure `PATH`;
- understand Git, Conda, or the terminal.

## Windows-first Strategy

For the first releases, a Windows installer with a one-folder install layout is preferred. This fits:

- the PySide6 desktop app;
- a bundled Python runtime;
- a dedicated `engine/` directory;
- transparent app+engine updates as a single release artifact.

## What Must Be Shipped

- the application;
- UI resources;
- a bundled Python runtime;
- a bundled and already built `gprMax` installed into that runtime;
- dependencies required for the CPU-first baseline;
- bundled licenses/notices for open-source dependencies;
- `engine/manifest.json`.

## What Must Stay Out of the User Workflow

- `pip install`;
- `conda create`;
- `git clone`;
- Cython extension compilation;
- MSVC Build Tools installation;
- manual Python executable selection as a required step.

For accuracy, the Windows installer may still expose an optional advanced task that downloads Microsoft Visual Studio Build Tools with the C++ workload. This is not part of the normal end-user path for the bundled app. It exists only for users who intentionally want to rebuild or repair the `gprMax` engine on the target machine.

## Engine Bundle Build

`gprMax` requires Windows Cython modules to be built through an MSVC/OpenMP toolchain. Therefore:

- the `gprMax` source repository is used only on the build/release side;
- the release side builds a managed `engine/python` venv;
- the installer ships the ready-made bundle;
- users never interact with `setup.py build/install`.

## Updates

At this stage, the desktop app release and the bundled engine release are assumed to ship together. That gives a simple compatibility model:

- one installer;
- one tested app + engine combination;
- one documented compatibility matrix.

In the future, engine updates can move to a separate managed strategy, but not before the project has a stable release process.

## Open-source and Licensing

Because the project is open-source and the distribution bundles `gprMax` and other dependencies, the release structure must include:

- bundled license texts/notices;
- explicit engine and dependency version tracking;
- a reproducible build recipe for community contributors.

That is an architectural requirement. Legal details belong to the release process documentation.
