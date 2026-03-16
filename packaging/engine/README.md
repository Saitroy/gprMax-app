# Engine Bundle Build

## Русский

Этот каталог содержит foundation для сборки встроенного `gprMax`-ядра, которое затем кладётся в installer вместе с приложением.

Ключевой принцип:

- пользователь не компилирует `gprMax` у себя;
- MSVC Build Tools и Python runtime нужны только на build/release-машине;
- результатом сборки является готовый `engine/` bundle.

### Что делает `build_engine_bundle.ps1`

1. Берёт исходники `gprMax` из `vendor/gprMax-source` или указанного пути.
2. Создаёт isolated virtual environment в `engine/python`.
3. Устанавливает runtime-зависимости `gprMax` для CPU-first baseline.
4. Загружает MSVC environment через `vcvars64.bat`.
5. Выполняет `python setup.py build` и `python setup.py install`.
6. Копирует license/readme в `engine/licenses`.
7. Генерирует `engine/manifest.json`.
8. Выполняет smoke test built engine.

### Release prerequisites

- Windows x64 build machine
- установленный CPython 3.11 x64
- Microsoft Build Tools for Visual Studio 2022/2025
- workload `Desktop development with C++`
- MSVC x64/x86 build tools
- Windows SDK

### Почему используется `venv` layout

Для первого рабочего билда это самый прямой путь:

- `pip` и `setuptools` доступны сразу;
- проще собирать и устанавливать compiled Python packages;
- проще запускать `python -m gprMax` из уже готового managed runtime;
- проще дебажить build issues, чем с embeddable Python ZIP.

Installer затем должен упаковывать весь каталог `engine/`.

## English

This directory contains the foundation for building the bundled `gprMax` engine that will be shipped with the application installer.

Core principle:

- users do not compile `gprMax` on their own machines;
- MSVC Build Tools and a Python runtime are needed only on the build/release machine;
- the output is a ready-to-ship `engine/` bundle.

### What `build_engine_bundle.ps1` Does

1. Takes `gprMax` source from `vendor/gprMax-source` or a specified path.
2. Creates an isolated virtual environment in `engine/python`.
3. Installs `gprMax` runtime dependencies for the CPU-first baseline.
4. Loads the MSVC environment through `vcvars64.bat`.
5. Runs `python setup.py build` and `python setup.py install`.
6. Copies license/readme files into `engine/licenses`.
7. Generates `engine/manifest.json`.
8. Runs a smoke test against the built engine.

### Release prerequisites

- Windows x64 build machine
- CPython 3.11 x64 installed
- Microsoft Build Tools for Visual Studio 2022/2025
- `Desktop development with C++` workload
- MSVC x64/x86 build tools
- Windows SDK

### Why a `venv` Layout Is Used

For the first working build this is the most direct path:

- `pip` and `setuptools` are immediately available;
- compiled Python packages are easier to build and install;
- `python -m gprMax` can run directly from the managed runtime;
- build issues are easier to debug than with the embeddable Python ZIP.

The installer should then package the entire `engine/` directory.

