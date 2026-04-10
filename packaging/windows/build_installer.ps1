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
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
        "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe"
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

function Write-ReleaseChecksums([string]$InstallerRoot, [string]$BundleRoot, [string]$AppVersion) {
    $artifacts = @(
        (Join-Path $InstallerRoot "gprmax-workbench-$AppVersion-windows-x64.exe"),
        (Join-Path $BundleRoot "release-manifest.json"),
        (Join-Path $BundleRoot "licenses\app-python\inventory-app-python.json"),
        (Join-Path $BundleRoot "licenses\engine-python\inventory-engine-python.json")
    )

    $lines = @()
    foreach ($artifact in $artifacts) {
        if (-not (Test-Path $artifact)) {
            throw "Expected release artifact not found: $artifact"
        }
        $hash = (Get-FileHash -Algorithm SHA256 $artifact).Hash.ToLowerInvariant()
        $lines += "$hash *$([System.IO.Path]::GetFileName($artifact))"
    }

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllLines((Join-Path $InstallerRoot "SHA256SUMS.txt"), $lines, $utf8NoBom)
}

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

Write-ReleaseChecksums $resolvedOutputRoot $resolvedBundleRoot $AppVersion

Write-Host "Installer created under $resolvedOutputRoot"
