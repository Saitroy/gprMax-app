param(
    [string]$BundleRoot = "dist/windows/GPRMax Workbench",
    [string]$OutputRoot = "dist/installer",
    [string]$AppVersion = ""
)

$ErrorActionPreference = "Stop"

function Resolve-AbsolutePath([string]$PathValue, [string]$BaseRoot) {
    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return [System.IO.Path]::GetFullPath($PathValue)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $BaseRoot $PathValue))
}

function Find-ISCC {
    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
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
$resolvedOutputRoot = Resolve-AbsolutePath $OutputRoot $repoRoot
$releaseManifestPath = Join-Path $resolvedBundleRoot "release-manifest.json"
$iscc = Find-ISCC

if (-not $iscc) {
    throw "ISCC.exe was not found. Install Inno Setup 6 on the release machine."
}

if (-not (Test-Path (Join-Path $resolvedBundleRoot "GPRMax Workbench.exe"))) {
    throw "Desktop bundle not found at $resolvedBundleRoot"
}

if (-not $AppVersion) {
    if (-not (Test-Path $releaseManifestPath)) {
        throw "release-manifest.json not found at $releaseManifestPath"
    }
    $releaseManifest = Get-Content $releaseManifestPath -Raw | ConvertFrom-Json
    $AppVersion = $releaseManifest.app_version
}

New-Item -ItemType Directory -Path $resolvedOutputRoot -Force | Out-Null

& $iscc `
    "/DAppVersion=$AppVersion" `
    "/DSourceDir=$resolvedBundleRoot" `
    "/DOutputDir=$resolvedOutputRoot" `
    (Join-Path $scriptRoot "gprmax_workbench.iss")

if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup build failed."
}

Write-Host "Installer created under $resolvedOutputRoot"
