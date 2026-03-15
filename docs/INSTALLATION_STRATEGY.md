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
- установленный внутрь него `gprMax`;
- зависимости, необходимые для CPU-first baseline;
- bundled licenses/notices для open-source dependencies;
- `engine/manifest.json`.

## Что не должно попадать в пользовательский workflow

- `pip install`;
- `conda create`;
- `git clone`;
- ручной выбор Python executable как обязательный шаг.

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
- `gprMax` installed into that runtime;
- dependencies required for the CPU-first baseline;
- bundled licenses/notices for open-source dependencies;
- `engine/manifest.json`.

## What Must Stay Out of the User Workflow

- `pip install`;
- `conda create`;
- `git clone`;
- manual Python executable selection as a required step.

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
