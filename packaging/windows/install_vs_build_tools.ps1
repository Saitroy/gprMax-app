param(
    [string]$DownloadUrl = "https://aka.ms/vs/17/release/vs_BuildTools.exe",
    [string]$WorkloadId = "Microsoft.VisualStudio.Workload.VCTools",
    [switch]$Passive
)

$ErrorActionPreference = "Stop"

function Find-VsWhere {
    $candidates = @(
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe",
        "${env:ProgramFiles}\Microsoft Visual Studio\Installer\vswhere.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }
    return $null
}

function Test-VsBuildToolsInstalled {
    $vswhere = Find-VsWhere
    if (-not $vswhere) {
        return $false
    }

    $installPath = & $vswhere `
        -latest `
        -products * `
        -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
        -property installationPath

    return ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($installPath))
}

if (Test-VsBuildToolsInstalled) {
    Write-Host "Visual Studio Build Tools with C++ support are already installed."
    exit 0
}

$downloadRoot = Join-Path $env:TEMP "gprmax-workbench"
New-Item -ItemType Directory -Path $downloadRoot -Force | Out-Null
$bootstrapperPath = Join-Path $downloadRoot "vs_BuildTools.exe"

Write-Host "Downloading Visual Studio Build Tools bootstrapper from $DownloadUrl"
Invoke-WebRequest -Uri $DownloadUrl -OutFile $bootstrapperPath

$arguments = @(
    "--add", $WorkloadId,
    "--includeRecommended"
)

if ($Passive) {
    $arguments += @("--passive", "--wait", "--norestart")
}

Write-Host "Starting Visual Studio Build Tools installer"
$process = Start-Process -FilePath $bootstrapperPath -ArgumentList $arguments -PassThru -Wait

if ($process.ExitCode -notin @(0, 3010)) {
    throw "Visual Studio Build Tools installer exited with code $($process.ExitCode)."
}

Write-Host "Visual Studio Build Tools installer finished with code $($process.ExitCode)"
