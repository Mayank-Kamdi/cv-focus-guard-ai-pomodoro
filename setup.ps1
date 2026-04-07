$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = $scriptDir

Set-Location $projectRoot

$pythonCmd = $null
if (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
}
else {
    Write-Error "Python is not installed or not on PATH."
    exit 1
}

if (-not (Test-Path -Path ".venv")) {
    & $pythonCmd -m venv .venv
}

# Activate venv for this shell session.
. .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host "Setup complete. Run: .\\.venv\\Scripts\\Activate.ps1"
Write-Host "Then start the app: python main.py"
