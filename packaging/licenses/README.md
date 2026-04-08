# License Inventory Export

This directory contains helper tooling for release-time dependency license review.

## Purpose

The first public bundled release ships more than just the app source:

- the desktop application bundle
- the bundled `gprMax` engine
- Python runtimes
- transitive runtime dependencies

That means each release candidate needs a concrete inventory of bundled Python distributions and any discoverable license files.

## Tool

`export_dependency_licenses.py` scans the current Python environment and writes:

- `inventory-<scope>.json`
- copied license and notice files, when present in installed distributions

## Typical usage

App build environment:

```powershell
python packaging\licenses\export_dependency_licenses.py --output-root .tmp\licenses\app-python --scope app-python
```

Bundled engine environment:

```powershell
engine\python\Scripts\python.exe packaging\licenses\export_dependency_licenses.py --output-root .tmp\licenses\engine-python --scope engine-python
```

The Windows desktop bundle script calls this tool automatically for both app and engine runtimes.
