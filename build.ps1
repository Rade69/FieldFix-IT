$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Activate = Join-Path $Root ".venv\Scripts\Activate.ps1"
if (Test-Path $Activate) {
    . $Activate
}

pyinstaller fieldfix.spec --noconfirm
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

$Output = Join-Path $Root "dist\FieldFix IT.exe"
Write-Host "Build output: $Output"
