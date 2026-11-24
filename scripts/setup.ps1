param([string]$Python = 'python', [switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$studioRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $studioRoot
node -e "const [a,b,c]=process.versions.node.split('.').map(Number);process.exit(a===24&&(b>14||b===14&&c>=1)?0:1)"
if ($LASTEXITCODE -ne 0) { throw 'Cần Node 24.14.1 trở lên trong nhánh 24.x.' }
if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) { throw 'Không tìm thấy Python. Dùng -Python với đường dẫn interpreter 3.12.' }
& $Python -c "import sys;sys.exit(0 if sys.version_info[:2]==(3,12) else 1)"
if ($LASTEXITCODE -ne 0) { throw 'Cần Python 3.12. Dùng ./scripts/setup.ps1 -Python <đường-dẫn-python.exe>.' }
if ($CheckOnly) { Write-Output 'Node/Python version checks passed.'; return }
if (-not (Test-Path -LiteralPath '.venv-api/Scripts/python.exe')) {
  & $Python -m venv .venv-api
  if ($LASTEXITCODE -ne 0) { throw 'Cần Python 3.12 để tạo môi trường API.' }
}
& ./.venv-api/Scripts/python.exe -m pip install -r services/local-api/requirements.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Cài Python dependency thất bại.' }
npm.cmd ci
if ($LASTEXITCODE -ne 0) { throw 'Cài npm dependency thất bại.' }
npm.cmd run types
if ($LASTEXITCODE -ne 0) { throw 'Sinh types thất bại.' }
node scripts/prepare-browser.mjs
if ($LASTEXITCODE -ne 0) { throw 'Chuẩn bị browser thất bại.' }
Write-Output 'Đã chuẩn bị. Chạy ./scripts/start.ps1 để mở studio.'
