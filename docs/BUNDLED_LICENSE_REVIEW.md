# Bundled License Review

Last updated: 2026-04-07

This document is a release gate for any public build that bundles `gprMax`.

It is not legal advice. It is the engineering review checklist that must be completed before public distribution.

## 1. Distribution model under review

Target release:

- Windows desktop application bundle
- bundled `gprMax` engine under `engine/`
- bundled Python runtimes for the app build path and the engine runtime
- open-source dependency notices shipped with the release artifact

The app source repository currently declares `MIT` for `gprmax-workbench` itself. The bundled release also includes components with different license obligations, so the final public artifact must be reviewed as a combined distribution, not as the app package alone.

## 2. Known first-order components

Current known components that require explicit review:

- `gprmax-workbench`: MIT
- `gprMax`: GPLv3+
- CPython runtime: PSF License
- `PySide6`: LGPL/commercial dual-license distribution terms
- `numpy`: BSD-style license
- `h5py`: BSD-style license
- transitive runtime dependencies captured by the generated inventory files

Do not assume this list is complete. The generated inventories are the source of truth for each release candidate.

## 3. Required review questions

The reviewer must explicitly answer the following before a public bundled release:

1. Does bundling `gprMax` inside the installer change the effective distribution obligations for the released product?
2. What source-offer, build-recipe, or corresponding-source expectations apply to the distributed artifact?
3. What notices, attribution files, and license texts must ship inside the installer and bundle?
4. Are there any additional obligations triggered by `PySide6` or other bundled runtime dependencies?
5. Are installer screens, release notes, and repository docs aligned with the final compliance position?

## 4. Engineering assets for the review

The repository now provides the following assets for review and release records:

- `LICENSE` for the app repository
- `packaging/licenses/export_dependency_licenses.py`
- generated inventory folders for app and engine runtimes
- `engine/manifest.json`
- `release-manifest.json` in the desktop bundle
- `docs/PUBLIC_RELEASE_CHECKLIST.md`

Expected generated artifacts per release candidate:

- `licenses/app-python/inventory-app-python.json`
- `licenses/engine-python/inventory-engine-python.json`
- copied license texts discovered from bundled distributions

## 5. Required release outputs

Before public shipment, the release artifact must include:

- app license text
- `gprMax` license text
- third-party license inventory for the app runtime
- third-party license inventory for the engine runtime
- any additional notice files required by bundled dependencies
- a reproducible build recipe or documented build path

## 6. Current status

Status as of 2026-04-07:

- engineering scaffolding exists
- license inventory export exists
- review documentation exists
- public legal/compliance sign-off is still pending

That means the bundled public release remains blocked until a human review is completed and signed off.
