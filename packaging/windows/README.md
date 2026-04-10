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

The installer now also exposes an optional post-install task to download and launch Microsoft Visual Studio Build Tools with the C++ workload.

Important distinction:

- normal bundled application use does not require Visual Studio Build Tools;
- Build Tools are only needed on machines where the user wants to rebuild or repair the `gprMax` engine manually.

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

When `-PythonExe` is omitted, the script prefers `.\.venv\Scripts\python.exe` from the repository root and only falls back to `python` from `PATH`.

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

The bundle includes:

- `support\collect_support_bundle.py`
- `support\install_vs_build_tools.ps1`

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
- The optional Build Tools installer task downloads the official Microsoft bootstrapper from `https://aka.ms/vs/17/release/vs_BuildTools.exe` and starts it with the `Microsoft.VisualStudio.Workload.VCTools` workload.
