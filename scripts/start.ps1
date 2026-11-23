param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$studioRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $studioRoot
if (-not (Test-Path -LiteralPath '.venv-api/Scripts/python.exe')) { throw 'Chạy scripts/setup.ps1 trước.' }
if ($NoBrowser) { & ./.venv-api/Scripts/python.exe scripts/dev.py --no-browser }
else { & ./.venv-api/Scripts/python.exe scripts/dev.py }
