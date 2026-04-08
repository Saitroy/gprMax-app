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

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-AbsolutePath "..\.." $scriptRoot

if (-not $PythonExe) {
    $PythonExe = (Get-Command python -ErrorAction Stop).Source
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
    Remove-Item -Recurse -Force $distRoot
}
if (Test-Path $workRoot) {
    Remove-Item -Recurse -Force $workRoot
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
