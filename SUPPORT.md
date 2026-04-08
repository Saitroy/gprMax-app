# Support

The application is currently in ALPHA testing.

Bug reports should be sent by email to `gleb.herz@yandex.ru`.

Before sending a bug report:

1. Confirm the problem on the latest commit or latest bundled build you have.
2. Capture the app version and runtime diagnostics from `Settings`.
3. Attach screenshots of the problem.
4. Describe what you were doing right before the bug appeared.
5. Export a support bundle when possible.
6. Remove sensitive project data before attaching anything.

## Bug reports

Please include:

- app version
- install type: source checkout, portable bundle, or installer build
- Windows version
- exact reproduction steps
- expected behavior
- actual behavior
- screenshots of the problem
- a short description of what happened right before the bug
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

## What not to publish

Do not attach:

- confidential project files
- proprietary datasets
- secrets, tokens, or private network paths
- large binary outputs unless a maintainer explicitly asks for them
