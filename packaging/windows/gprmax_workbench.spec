# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


repo_root = Path(SPECPATH).resolve().parents[1]
src_root = repo_root / "src"
launcher = Path(SPECPATH).resolve() / "launch_gprmax_workbench.py"

datas = [
    (str(repo_root / "README.md"), "."),
    (str(repo_root / "LICENSE"), "."),
]

a = Analysis(
    [str(launcher)],
    pathex=[str(src_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GPRMax Workbench",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="GPRMax Workbench",
)
