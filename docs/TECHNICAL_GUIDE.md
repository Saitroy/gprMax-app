# Technical Guide

Last updated: 2026-04-08

This document is the technical entry point for contributors, developers, and release maintainers.

If you are looking for the product overview and end-user workflow, start with [README](../README.md).

## Running from source

Install development dependencies:

```bash
pip install -e .[dev]
```

Run the application:

```bash
python -m gprmax_workbench
```

Open a project on startup:

```bash
python -m gprmax_workbench --project /path/to/project
```

After editable installation you can also use:

```bash
gprmax-workbench
```

## Local verification

Run lint:

```bash
python -m ruff check src tests packaging tools
```

Run tests:

```bash
python tools/run_tests.py
```

`tools/run_tests.py` keeps temporary test files under `.tmp_test_runs`, which avoids Windows `%TEMP%` permission issues on locked-down machines.

## Repository structure

```text
docs/                     Product, architecture, runtime, and release documents
packaging/                Engine, license, and Windows packaging scripts
src/gprmax_workbench/     Application package
tests/                    Automated tests
tools/                    Developer and support tooling
```

Inside `src/gprmax_workbench/`:

```text
ui/                       Qt windows, views, widgets, theme
application/              Use cases, orchestration services, app state
domain/                   Domain models and validation rules
infrastructure/           Persistence, runtime, gprMax adapters, settings
jobs/                     Background job primitives
```

## Architecture and implementation documents

- System architecture: [ARCHITECTURE.md](./ARCHITECTURE.md)
- Product and technical decisions: [DECISIONS.md](./DECISIONS.md)
- Current product state: [CURRENT_STATE.md](./CURRENT_STATE.md)
- `gprMax` integration: [GPRMAX_INTEGRATION.md](./GPRMAX_INTEGRATION.md)
- Model editor details: [MODEL_EDITOR.md](./MODEL_EDITOR.md)
- Results viewer details: [RESULTS_VIEWER.md](./RESULTS_VIEWER.md)
- UI workstream: [UI_WORKSTREAM.md](./UI_WORKSTREAM.md)
- Roadmap: [ROADMAP.md](./ROADMAP.md)

## Runtime, packaging, and installation

- Runtime and packaging strategy: [RUNTIME_AND_PACKAGING.md](./RUNTIME_AND_PACKAGING.md)
- Installation strategy: [INSTALLATION_STRATEGY.md](./INSTALLATION_STRATEGY.md)
- Engine bundle build scripts: [../packaging/engine/README.md](../packaging/engine/README.md)
- Windows bundle and installer pipeline: [../packaging/windows/README.md](../packaging/windows/README.md)

## Release engineering

- First release readiness: [FIRST_RELEASE_READINESS.md](./FIRST_RELEASE_READINESS.md)
- Public release checklist: [PUBLIC_RELEASE_CHECKLIST.md](./PUBLIC_RELEASE_CHECKLIST.md)
- Bundled license review: [BUNDLED_LICENSE_REVIEW.md](./BUNDLED_LICENSE_REVIEW.md)
- Support flow: [../SUPPORT.md](../SUPPORT.md)

Repository assets added for the first release line:

- CI workflow: [../.github/workflows/ci.yml](../.github/workflows/ci.yml)
- [../.github/ISSUE_TEMPLATE/bug_report.yml](../.github/ISSUE_TEMPLATE/bug_report.yml)
- [../.github/ISSUE_TEMPLATE/feature_request.yml](../.github/ISSUE_TEMPLATE/feature_request.yml)
- Support bundle tool: [../tools/collect_support_bundle.py](../tools/collect_support_bundle.py)
- Dependency license inventory export: [../packaging/licenses/export_dependency_licenses.py](../packaging/licenses/export_dependency_licenses.py)

## Notes

- The application is still under active development.
- The repository already contains release-engineering scaffolding, but a public bundled release still requires real dry-runs, installer validation, and human compliance sign-off.
