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
$enginePythonExe = Join-Path $resolvedBundleRoot "engine\python\Scripts\python.exe"
if (-not (Test-Path $enginePythonExe)) {
    throw "Bundled engine python.exe not found at $enginePythonExe"
}

$probeCommand = "import json, pathlib; manifest = json.loads(pathlib.Path(r'$engineManifestPath').read_text(encoding='utf-8')); assert manifest.get('gprmax_version'); print(manifest['gprmax_version'])"
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
