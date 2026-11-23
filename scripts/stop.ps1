$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
& ./.venv-api/Scripts/python.exe scripts/dev.py --stop
