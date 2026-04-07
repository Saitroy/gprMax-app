# Support

This repository uses GitHub issues for bug reports and feature requests.

Before opening a bug:

1. Confirm the problem on the latest commit or latest bundled build you have.
2. Capture the app version and runtime diagnostics from `Settings`.
3. Export a support bundle when possible.
4. Remove sensitive project data before attaching anything publicly.

## Bug reports

Use the `Bug report` issue template and include:

- app version
- install type: source checkout, portable bundle, or installer build
- Windows version
- exact reproduction steps
- expected behavior
- actual behavior
- screenshots if the problem is visual
- the support bundle archive if available

## Collecting a support bundle

From the repository checkout:

```powershell
python tools\collect_support_bundle.py --project-root D:\path\to\project
```

From an installed bundle, use the shipped copy:

```powershell
python support\collect_support_bundle.py --project-root D:\path\to\project
```

The support bundle collects lightweight diagnostics only:

- application `settings.json`
- application logs under the user settings directory
- project manifest
- the latest run or a specified run
- run metadata, logs, and generated input snapshots

Result files are not included by default because they can be large.

## Feature requests

Use the `Feature request` issue template and describe:

- the workflow problem
- who is affected
- the current workaround
- the expected outcome

## What not to publish

Do not attach:

- confidential project files
- proprietary datasets
- secrets, tokens, or private network paths
- large binary outputs unless a maintainer explicitly asks for them
