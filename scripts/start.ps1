param([switch]$NoBrowser, [switch]$Restart)
$ErrorActionPreference = 'Stop'
$studioRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $studioRoot
if (-not (Test-Path -LiteralPath '.venv-api/Scripts/python.exe')) { throw 'Chạy scripts/setup.ps1 trước.' }
$studioArguments = @('scripts/dev.py')
if ($NoBrowser) { $studioArguments += '--no-browser' }
if ($Restart) { $studioArguments += '--restart' }
& ./.venv-api/Scripts/python.exe @studioArguments
