# Windows Release Pipeline

This directory contains the release-time packaging foundation for the desktop application bundle and installer.

## Tooling choices

- Desktop bundle: `PyInstaller`
- Windows installer: `Inno Setup 6`
- Bundled engine: `packaging/engine/build_engine_bundle.ps1`

The public release path is:

1. build the bundled `engine/`
2. build the desktop bundle with PyInstaller
3. export dependency license inventories
4. assemble the install layout
5. build the installer with Inno Setup
6. run clean-machine smoke tests

## Prerequisites

- Windows x64 release machine
- Python 3.11+ installed
- release dependencies installed with `pip install -e .[dev,release]`
- Inno Setup 6 installed
- bundled engine already built under `engine/` or another specified path

## Build the desktop bundle

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build_desktop_bundle.ps1
```

Optional overrides:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build_desktop_bundle.ps1 `
  -PythonExe C:\Python313\python.exe `
  -EngineRoot D:\release\engine `
  -OutputRoot D:\release\dist\windows
```

Output:

```text
dist/windows/GPRMax Workbench/
  GPRMax Workbench.exe
  engine/
  docs/
  licenses/
  support/
  release-manifest.json
```

## Build the installer

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build_installer.ps1
```

Optional overrides:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build_installer.ps1 `
  -BundleRoot D:\release\dist\windows\GPRMax Workbench `
  -OutputRoot D:\release\dist\installer
```

## Smoke test the bundle

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\smoke_test_bundle.ps1
```

## Important limits

- This is release-machine tooling, not end-user workflow.
- CI validates repository quality gates, not the full Windows installer build.
- A public bundled release still requires a completed review from `docs/BUNDLED_LICENSE_REVIEW.md`.
