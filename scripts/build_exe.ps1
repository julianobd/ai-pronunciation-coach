# Builds dist/PronunciationCoach/PronunciationCoach.exe using a clean,
# dedicated virtualenv (.venv-build). A clean venv keeps PyInstaller's
# analysis away from unrelated packages installed in the global Python.
#
# Usage:  powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$venv = Join-Path $root ".venv-build"
$python = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Creating build venv at $venv ..."
    python -m venv $venv
}

Write-Host "Installing app + PyInstaller into the build venv ..."
& $python -m pip install --upgrade pip --quiet
& $python -m pip install . pyinstaller --quiet

Write-Host "Building executable ..."
& $python -m PyInstaller PronunciationCoach.spec --noconfirm

Write-Host ""
Write-Host "Done: $root\dist\PronunciationCoach\PronunciationCoach.exe"
