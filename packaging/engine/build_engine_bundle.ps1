param(
    [string]$PythonExe = "",
    [string]$GprMaxSource = "vendor/gprMax-source",
    [string]$OutputRoot = "engine",
    [string]$AppVersion = "0.2.1",
    [switch]$SkipSmokeTest
)

$ErrorActionPreference = "Stop"

function Resolve-RepoPath([string]$PathValue) {
    $resolved = Resolve-Path $PathValue -ErrorAction SilentlyContinue
    if ($resolved) {
        return $resolved.Path
    }
    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $PathValue))
}

function Find-VcVars64 {
    $candidates = @()
    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $vswhere) {
        $installPath = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
        if ($LASTEXITCODE -eq 0 -and $installPath) {
            $candidates += (Join-Path $installPath "VC\Auxiliary\Build\vcvars64.bat")
        }
    }
    $candidates += Get-ChildItem "C:\Program Files (x86)\Microsoft Visual Studio" -Recurse -Filter vcvars64.bat -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
    return $candidates | Select-Object -First 1
}

function Assert-WindowsSdkAvailable {
    $sdkHeader = Get-ChildItem "C:\Program Files (x86)\Windows Kits\10\Include" -Recurse -Filter io.h -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $sdkHeader) {
        throw "Windows SDK / UCRT headers were not found. Install Build Tools with Windows 10 or Windows 11 SDK."
    }
}

function Get-GprMaxVersion([string]$SourceRoot) {
    $versionFile = Join-Path $SourceRoot "gprMax\_version.py"
    $match = Select-String -Path $versionFile -Pattern "__version__ = '(.+)'" | Select-Object -First 1
    if (-not $match) {
        throw "Could not parse gprMax version from $versionFile"
    }
    return $match.Matches[0].Groups[1].Value
}

$sourceRoot = Resolve-RepoPath $GprMaxSource
$outputRoot = Resolve-RepoPath $OutputRoot

if (-not (Test-Path (Join-Path $sourceRoot "setup.py"))) {
    throw "gprMax source not found at $sourceRoot"
}

if (-not $PythonExe) {
    $PythonExe = (Get-Command python -ErrorAction Stop).Source
}

$vcvars64 = Find-VcVars64
if (-not $vcvars64) {
    throw "vcvars64.bat not found. Install Microsoft Build Tools with Desktop development with C++."
}
Assert-WindowsSdkAvailable

$enginePythonRoot = Join-Path $outputRoot "python"
$enginePythonExe = Join-Path $enginePythonRoot "Scripts\python.exe"
$engineLicenses = Join-Path $outputRoot "licenses"

if (Test-Path $outputRoot) {
    Remove-Item -Recurse -Force $outputRoot
}

New-Item -ItemType Directory -Path $outputRoot | Out-Null

Write-Host "Creating bundled runtime venv at $enginePythonRoot"
& $PythonExe -m venv $enginePythonRoot
if ($LASTEXITCODE -ne 0) {
    throw "Failed to create engine venv."
}

& $enginePythonExe -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) {
    throw "Failed to bootstrap pip/setuptools/wheel."
}

$runtimeDeps = @(
    "colorama",
    "Cython",
    "h5py",
    "jupyter",
    "matplotlib",
    "numpy",
    "psutil",
    "scipy",
    "terminaltables",
    "tqdm"
)

Write-Host "Installing runtime dependencies"
& $enginePythonExe -m pip install @runtimeDeps
if ($LASTEXITCODE -ne 0) {
    throw "Failed to install gprMax runtime dependencies."
}

$buildCommand = "`"$enginePythonExe`" setup.py build"
$installCommand = "`"$enginePythonExe`" setup.py install"
$cmd = "call `"$vcvars64`" && cd /d `"$sourceRoot`" && $buildCommand && $installCommand"

Write-Host "Building and installing gprMax from source"
cmd.exe /c $cmd
if ($LASTEXITCODE -ne 0) {
    throw "gprMax build/install failed."
}

New-Item -ItemType Directory -Path $engineLicenses -Force | Out-Null
Copy-Item (Join-Path $sourceRoot "LICENSE") (Join-Path $engineLicenses "gprMax-LICENSE.txt")
Copy-Item (Join-Path $sourceRoot "README.rst") (Join-Path $engineLicenses "gprMax-README.rst")

$gprMaxVersion = Get-GprMaxVersion $sourceRoot
& $enginePythonExe (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "build_manifest.py") `
    --source-root $sourceRoot `
    --engine-root $outputRoot `
    --app-version $AppVersion `
    --python-executable "python/Scripts/python.exe" `
    --gprmax-version $gprMaxVersion
if ($LASTEXITCODE -ne 0) {
    throw "Failed to write engine manifest."
}

if (-not $SkipSmokeTest) {
    & (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "smoke_test_engine.ps1") `
        -EngineRoot $outputRoot `
        -GprMaxSource $sourceRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Bundled engine smoke test failed."
    }
}

Write-Host "Bundled engine created at $outputRoot"
