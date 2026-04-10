param(
    [string]$BundleRoot = "dist/windows/GPRMax Workbench"
)

$ErrorActionPreference = "Stop"

function Resolve-AbsolutePath([string]$PathValue, [string]$BaseRoot) {
    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return [System.IO.Path]::GetFullPath($PathValue)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $BaseRoot $PathValue))
}

function Get-BundledEnginePythonExe([string]$BundleRoot) {
    $candidates = @(
        (Join-Path $BundleRoot "engine\python\python.exe"),
        (Join-Path $BundleRoot "engine\python\Scripts\python.exe"),
        (Join-Path $BundleRoot "engine\python\python"),
        (Join-Path $BundleRoot "engine\python\bin\python.exe"),
        (Join-Path $BundleRoot "engine\python\bin\python")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-AbsolutePath "..\.." $scriptRoot
$resolvedBundleRoot = Resolve-AbsolutePath $BundleRoot $repoRoot
$requiredPaths = @(
    (Join-Path $resolvedBundleRoot "GPRMax Workbench.exe"),
    (Join-Path $resolvedBundleRoot "engine\manifest.json"),
    (Join-Path $resolvedBundleRoot "licenses\GPRMax-Workbench-LICENSE.txt"),
    (Join-Path $resolvedBundleRoot "licenses\app-python\inventory-app-python.json"),
    (Join-Path $resolvedBundleRoot "licenses\engine-python\inventory-engine-python.json"),
    (Join-Path $resolvedBundleRoot "docs\PUBLIC_RELEASE_CHECKLIST.md"),
    (Join-Path $resolvedBundleRoot "support\collect_support_bundle.py"),
    (Join-Path $resolvedBundleRoot "support\install_vs_build_tools.ps1"),
    (Join-Path $resolvedBundleRoot "release-manifest.json")
)

foreach ($requiredPath in $requiredPaths) {
    if (-not (Test-Path $requiredPath)) {
        throw "Missing required bundle artifact: $requiredPath"
    }
}

$engineManifestPath = Join-Path $resolvedBundleRoot "engine\manifest.json"
$enginePythonExe = Get-BundledEnginePythonExe $resolvedBundleRoot
if (-not $enginePythonExe) {
    throw "Bundled engine python executable not found under $resolvedBundleRoot\\engine\\python"
}

$pyvenvPath = Join-Path $resolvedBundleRoot "engine\python\pyvenv.cfg"
if (Test-Path $pyvenvPath) {
    throw "Portable bundle still contains pyvenv.cfg: $pyvenvPath"
}

$directUrlFiles = Get-ChildItem -Path $resolvedBundleRoot -Filter "direct_url.json" -Recurse -Force -ErrorAction SilentlyContinue
if (@($directUrlFiles).Count -gt 0) {
    $firstMatch = @($directUrlFiles)[0].FullName
    throw "Portable bundle still contains direct_url.json metadata: $firstMatch"
}

$probeCommand = "import json, pathlib, sys; manifest = json.loads(pathlib.Path(r'$engineManifestPath').read_text(encoding='utf-8')); assert manifest.get('gprmax_version'); expected = (pathlib.Path(r'$resolvedBundleRoot') / 'engine' / 'python').resolve(); assert pathlib.Path(sys.prefix).resolve() == expected; assert pathlib.Path(sys.base_prefix).resolve() == expected; print(manifest['gprmax_version'])"
& $enginePythonExe -c $probeCommand | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Failed to validate bundled engine manifest with bundled Python."
}

$gprMaxImportCommand = "import gprMax; print(getattr(gprMax, '__version__', 'unknown'))"
& $enginePythonExe -c $gprMaxImportCommand | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Failed to import gprMax from the bundled engine runtime."
}

$releaseManifestPath = Join-Path $resolvedBundleRoot "release-manifest.json"
$releaseManifest = Get-Content $releaseManifestPath -Raw | ConvertFrom-Json
if ($releaseManifest.schema.name -ne "gprmax-workbench-release-manifest") {
    throw "Unexpected release manifest schema."
}

Write-Host "Bundle smoke test passed for $resolvedBundleRoot"
