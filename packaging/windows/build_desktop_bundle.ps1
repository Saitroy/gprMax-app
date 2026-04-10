param(
    [string]$PythonExe = "",
    [string]$OutputRoot = "dist/windows",
    [string]$BuildRoot = "build/windows",
    [string]$EngineRoot = "engine",
    [string]$AppVersion = "",
    [switch]$SkipSmokeTest
)

$ErrorActionPreference = "Stop"

function Resolve-AbsolutePath([string]$PathValue, [string]$BaseRoot) {
    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return [System.IO.Path]::GetFullPath($PathValue)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $BaseRoot $PathValue))
}

function Copy-DirectoryTree([string]$SourceRoot, [string]$DestinationRoot) {
    New-Item -ItemType Directory -Path $DestinationRoot -Force | Out-Null
    $null = robocopy $SourceRoot $DestinationRoot /E /NFL /NDL /NJH /NJS /NP
    if ($LASTEXITCODE -gt 7) {
        throw "robocopy failed while copying '$SourceRoot' to '$DestinationRoot' with exit code $LASTEXITCODE"
    }
}

function Resolve-DefaultPythonExe([string]$RepoRoot) {
    $candidates = @(
        (Join-Path $RepoRoot ".venv\Scripts\python.exe"),
        (Join-Path $RepoRoot "venv\Scripts\python.exe")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return (Get-Command python -ErrorAction Stop).Source
}

function Get-FreeDriveLetter {
    foreach ($letter in @("Z", "Y", "X", "W", "V", "U", "T", "S", "R")) {
        if (-not (Test-Path "${letter}:\")) {
            return "${letter}:"
        }
    }
    throw "Could not find a free drive letter for subst."
}

function Remove-DirectoryTree([string]$PathValue) {
    if (-not (Test-Path $PathValue)) {
        return
    }

    $drive = Get-FreeDriveLetter
    $emptyRoot = Join-Path $env:TEMP "gprmax-workbench-empty-dir"
    New-Item -ItemType Directory -Path $emptyRoot -Force | Out-Null

    cmd.exe /c "subst $drive `"$PathValue`""
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to map '$PathValue' to a temporary drive."
    }

    try {
        $null = robocopy $emptyRoot "$drive\" /MIR /NFL /NDL /NJH /NJS /NP
        if ($LASTEXITCODE -gt 7) {
            throw "robocopy failed while cleaning '$PathValue' with exit code $LASTEXITCODE"
        }
    }
    finally {
        cmd.exe /c "subst $drive /d" | Out-Null
    }

    cmd.exe /c "rmdir /s /q `"$PathValue`""
    if (Test-Path $PathValue) {
        throw "Failed to remove directory tree '$PathValue'"
    }
}

function Remove-PathIfExists([string]$PathValue) {
    if (-not (Test-Path $PathValue)) {
        return
    }

    $item = Get-Item $PathValue -Force
    if ($item.PSIsContainer) {
        Remove-DirectoryTree $PathValue
        return
    }

    Remove-Item -Force $PathValue
}

function Remove-PathsByPattern([string]$Root, [string[]]$Patterns) {
    foreach ($pattern in $Patterns) {
        Get-ChildItem -Path $Root -Filter $pattern -Force -ErrorAction SilentlyContinue | ForEach-Object {
            Remove-Item -Recurse -Force $_.FullName
        }
    }
}

function Optimize-EngineRuntime([string]$BundleRoot) {
    $engineRoot = Join-Path $BundleRoot "engine"
    $sitePackages = Join-Path $engineRoot "python\Lib\site-packages"
    $scriptsRoot = Join-Path $engineRoot "python\Scripts"

    Remove-PathIfExists (Join-Path $engineRoot "python\etc\jupyter")
    Remove-PathIfExists (Join-Path $engineRoot "python\share\jupyter")

    if (Test-Path $sitePackages) {
        $explicitRemovals = @(
            "IPython",
            "ipykernel",
            "ipywidgets",
            "jupyterlab",
            "jupyterlab_pygments",
            "jupyterlab_server",
            "jupyterlab_widgets",
            "jupyter_client",
            "jupyter_console",
            "jupyter_core",
            "jupyter_events",
            "jupyter_lsp",
            "jupyter_server",
            "jupyter_server_terminals",
            "nbclient",
            "nbconvert",
            "nbformat",
            "notebook",
            "notebook_shim",
            "widgetsnbextension",
            "comm",
            "debugpy",
            "jsonschema",
            "jsonschema_specifications",
            "referencing",
            "rpds",
            "argon2",
            "async_lru",
            "bs4",
            "bleach",
            "defusedxml",
            "mistune",
            "prometheus_client",
            "send2trash",
            "stack_data",
            "tinycss2",
            "traitlets",
            "webcolors",
            "webencodings",
            "websocket",
            "fqdn",
            "isoduration",
            "uri_template",
            "json5",
            "fastjsonschema",
            "jedi",
            "parso",
            "prompt_toolkit",
            "terminado",
            "tornado",
            "zmq",
            "yaml",
            "winpty",
            "_argon2_cffi_bindings"
        )

        foreach ($entry in $explicitRemovals) {
            Remove-PathIfExists (Join-Path $sitePackages $entry)
        }

        Remove-PathsByPattern $sitePackages @(
            "comm*",
            "jupyter*",
            "nbclient*",
            "nbconvert*",
            "nbformat*",
            "notebook*",
            "ipykernel*",
            "ipython*",
            "ipywidgets*",
            "widgetsnbextension*",
            "debugpy*",
            "jsonschema*",
            "referencing*",
            "rpds*",
            "argon2*",
            "async_lru*",
            "beautifulsoup4*",
            "bleach*",
            "defusedxml*",
            "mistune*",
            "prometheus_client*",
            "python_json_logger*",
            "pythonjsonlogger*",
            "rfc3339_validator*",
            "rfc3986_validator*",
            "rfc3987_syntax*",
            "send2trash*",
            "stack_data*",
            "tinycss2*",
            "traitlets*",
            "webcolors*",
            "webencodings*",
            "websocket*",
            "fqdn*",
            "isoduration*",
            "uri_template*",
            "json5*",
            "fastjsonschema*",
            "jedi*",
            "parso*",
            "prompt_toolkit*",
            "terminado*",
            "tornado*",
            "pywinpty*",
            "winpty*",
            "pyzmq*"
        )

        Get-ChildItem -Path $sitePackages -Directory -Recurse -Force -ErrorAction SilentlyContinue | Where-Object {
            $_.Name -in @("__pycache__", "benchmarks", "docs", "doc", "examples", "example", "tests", "test")
        } | Sort-Object FullName -Descending | ForEach-Object {
            Remove-Item -Recurse -Force $_.FullName
        }

        Get-ChildItem -Path $sitePackages -Include *.pyc,*.pyo,*.whl -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
            Remove-Item -Force $_.FullName
        }
    }

    if (Test-Path $scriptsRoot) {
        Get-ChildItem -Path $scriptsRoot -File -Force -ErrorAction SilentlyContinue | Where-Object {
            $_.Name -like "jupyter*" -or
            $_.Name -like "ipython*" -or
            $_.Name -like "debugpy*" -or
            $_.Name -like "jlpm*" -or
            $_.Name -like "jsonschema*" -or
            $_.Name -like "pyjson5*" -or
            $_.Name -like "pygmentize*" -or
            $_.Name -like "wsdump*"
        } | ForEach-Object {
            Remove-Item -Force $_.FullName
        }
    }
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-AbsolutePath "..\.." $scriptRoot

if (-not $PythonExe) {
    $PythonExe = Resolve-DefaultPythonExe $repoRoot
}

if (-not $AppVersion) {
    $versionCommand = "import pathlib, tomllib; root = pathlib.Path(r'$repoRoot'); data = tomllib.loads((root / 'pyproject.toml').read_text(encoding='utf-8')); print(data['project']['version'])"
    $AppVersion = (& $PythonExe -c $versionCommand).Trim()
}

& $PythonExe -m PyInstaller --version | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller is not installed. Install release dependencies with: pip install -e .[release]"
}

$distRoot = Resolve-AbsolutePath $OutputRoot $repoRoot
$workRoot = Resolve-AbsolutePath $BuildRoot $repoRoot
$sourceEngineRoot = Resolve-AbsolutePath $EngineRoot $repoRoot
$bundleRoot = Join-Path $distRoot "GPRMax Workbench"
$engineManifestPath = Join-Path $sourceEngineRoot "manifest.json"

if (-not (Test-Path $engineManifestPath)) {
    throw "Engine bundle manifest not found at $engineManifestPath"
}

if (Test-Path $distRoot) {
    Remove-DirectoryTree $distRoot
}
if (Test-Path $workRoot) {
    Remove-DirectoryTree $workRoot
}
New-Item -ItemType Directory -Path $distRoot | Out-Null
New-Item -ItemType Directory -Path $workRoot | Out-Null

Push-Location $repoRoot
try {
    & $PythonExe -m PyInstaller `
        --noconfirm `
        --clean `
        --distpath $distRoot `
        --workpath $workRoot `
        (Join-Path $repoRoot "packaging\windows\gprmax_workbench.spec")
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed."
    }
}
finally {
    Pop-Location
}

if (-not (Test-Path $bundleRoot)) {
    throw "Desktop bundle directory was not created at $bundleRoot"
}

$docsRoot = Join-Path $bundleRoot "docs"
$licensesRoot = Join-Path $bundleRoot "licenses"
$supportRoot = Join-Path $bundleRoot "support"
New-Item -ItemType Directory -Path $docsRoot -Force | Out-Null
New-Item -ItemType Directory -Path $licensesRoot -Force | Out-Null
New-Item -ItemType Directory -Path $supportRoot -Force | Out-Null

Copy-DirectoryTree $sourceEngineRoot (Join-Path $bundleRoot "engine")
Optimize-EngineRuntime $bundleRoot
Copy-Item (Join-Path $repoRoot "README.md") (Join-Path $docsRoot "README.md")
Copy-Item (Join-Path $repoRoot "SUPPORT.md") (Join-Path $docsRoot "SUPPORT.md")
Copy-Item (Join-Path $repoRoot "docs\PUBLIC_RELEASE_CHECKLIST.md") (Join-Path $docsRoot "PUBLIC_RELEASE_CHECKLIST.md")
Copy-Item (Join-Path $repoRoot "docs\BUNDLED_LICENSE_REVIEW.md") (Join-Path $docsRoot "BUNDLED_LICENSE_REVIEW.md")
Copy-Item (Join-Path $repoRoot "LICENSE") (Join-Path $licensesRoot "GPRMax-Workbench-LICENSE.txt")
Copy-Item (Join-Path $repoRoot "tools\collect_support_bundle.py") (Join-Path $supportRoot "collect_support_bundle.py")
Copy-Item (Join-Path $repoRoot "packaging\windows\install_vs_build_tools.ps1") (Join-Path $supportRoot "install_vs_build_tools.ps1")

& $PythonExe `
    (Join-Path $repoRoot "packaging\licenses\export_dependency_licenses.py") `
    --output-root (Join-Path $licensesRoot "app-python") `
    --scope "app-python"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to export app runtime license inventory."
}

$enginePythonExe = Join-Path $bundleRoot "engine\python\Scripts\python.exe"
if (-not (Test-Path $enginePythonExe)) {
    throw "Bundled engine Python executable not found at $enginePythonExe"
}

& $enginePythonExe `
    (Join-Path $repoRoot "packaging\licenses\export_dependency_licenses.py") `
    --output-root (Join-Path $licensesRoot "engine-python") `
    --scope "engine-python"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to export engine runtime license inventory."
}

& $PythonExe `
    (Join-Path $repoRoot "packaging\windows\build_release_manifest.py") `
    --repo-root $repoRoot `
    --bundle-root $bundleRoot `
    --app-version $AppVersion
if ($LASTEXITCODE -ne 0) {
    throw "Failed to build release manifest."
}

if (-not $SkipSmokeTest) {
    & (Join-Path $scriptRoot "smoke_test_bundle.ps1") -BundleRoot $bundleRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Desktop bundle smoke test failed."
    }
}

Write-Host "Desktop bundle created at $bundleRoot"
