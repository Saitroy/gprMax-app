# Public Release Checklist

Last updated: 2026-04-07

This checklist is the release gate for the first public bundled Windows build.

Do not cut a public release until every required item below is complete.

## 1. Repository and versioning

- [ ] `main` is green in GitHub Actions CI.
- [ ] The release commit is tagged and matches the version in `pyproject.toml`.
- [ ] `README.md`, `docs/CURRENT_STATE.md`, and `docs/FIRST_RELEASE_READINESS.md` reflect the release state.
- [ ] The release notes draft lists major user-facing changes, known limits, and upgrade notes.

## 2. Core quality gates

- [ ] `python -m ruff check src tests packaging tools` passes.
- [ ] `python -m unittest discover tests` passes.
- [ ] Desktop smoke checks still behave correctly at `1366x768` and `1920x1080`.
- [ ] No critical regressions remain in `Welcome`, `Project`, `Simulation`, or `Results`.

## 3. Bundled engine

- [ ] The engine bundle is rebuilt on the release machine with `packaging/engine/build_engine_bundle.ps1`.
- [ ] `engine/manifest.json` is present and matches the intended release version.
- [ ] The engine smoke test passes.
- [ ] CPU baseline execution works without external Python configuration.

## 4. Desktop bundle

- [ ] Release dependencies are installed with `pip install -e .[dev,release]`.
- [ ] `packaging/windows/build_desktop_bundle.ps1` completes successfully.
- [ ] `packaging/windows/smoke_test_bundle.ps1` passes on the produced bundle.
- [ ] The bundle contains:
- `GPRMax Workbench.exe`
- `engine/`
- `licenses/`
- `docs/`
- `support/collect_support_bundle.py`
- `release-manifest.json`

## 5. Installer

- [ ] `packaging/windows/build_installer.ps1` completes successfully.
- [ ] The installer output is archived with the release build record.
- [ ] Install/uninstall is validated on a clean Windows machine or VM.
- [ ] The installed app launches without manually configuring Python, `gprMax`, or `PATH`.

## 6. Licensing and compliance

- [ ] The review in `docs/BUNDLED_LICENSE_REVIEW.md` is completed for this release.
- [ ] The generated license inventories for app and engine runtimes are attached to the release record.
- [ ] Required license texts and notices are included in the bundle and installer payload.
- [ ] The distribution model for bundled `gprMax` has explicit maintainer sign-off.

## 7. Supportability

- [ ] Issue templates are present in `.github/ISSUE_TEMPLATE/`.
- [ ] `SUPPORT.md` matches the current support flow.
- [ ] `tools/collect_support_bundle.py` produces a usable support archive from a real project.
- [ ] Release notes include bug-report instructions and where logs live.

## 8. Clean-machine smoke test

- [ ] Fresh install on Windows x64.
- [ ] Create a new project from `Welcome`.
- [ ] Open an existing project.
- [ ] Edit the model and save.
- [ ] Preview and export generated input.
- [ ] Run a CPU simulation with live logs visible.
- [ ] Open run/output folders from the UI.
- [ ] Open results and verify A-scan and bounded B-scan behavior on a known sample.
- [ ] Open `Settings` and verify runtime diagnostics.

## 9. Release publication

- [ ] Installer, bundle manifest, license inventories, and release notes are attached to the release record.
- [ ] Checksums are generated for published artifacts.
- [ ] A maintainer signs off on product quality.
- [ ] A maintainer signs off on licensing/compliance.
- [ ] A maintainer signs off on support readiness.

## 10. Post-release follow-up

- [ ] Open a post-release tracking issue for regressions and support feedback.
- [ ] Capture first-run installation feedback from real users.
- [ ] Schedule the next stabilization pass for installer, diagnostics, and support flow improvements.
