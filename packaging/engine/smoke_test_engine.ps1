param(
    [string]$EngineRoot = "engine",
    [string]$GprMaxSource = "vendor/gprMax-source"
)

$ErrorActionPreference = "Stop"

$engineRoot = (Resolve-Path $EngineRoot).Path
$sourceRoot = (Resolve-Path $GprMaxSource).Path
$pythonExe = Join-Path $engineRoot "python\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "Bundled runtime python.exe not found: $pythonExe"
}

& $pythonExe -c "import gprMax, gprMax.fields_updates_ext, gprMax.geometry_primitives_ext; print(gprMax.__version__)"
if ($LASTEXITCODE -ne 0) {
    throw "Compiled gprMax modules failed to import."
}

& $pythonExe -m gprMax (Join-Path $sourceRoot "user_models\cylinder_Ascan_2D.in") --geometry-only
if ($LASTEXITCODE -ne 0) {
    throw "gprMax geometry-only smoke test failed."
}

Write-Host "Bundled engine smoke test passed."

