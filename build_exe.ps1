<#
PowerShell helper to build a single-file .exe from `main.py` using PyInstaller.

Usage (PowerShell):
  .\build_exe.ps1

What it does:
- Creates a virtual environment in `.venv_build` (if not exists)
- Activates it, upgrades pip and installs `pyinstaller`
- Runs `pyinstaller --onefile --console --name AutoWifiHelper main.py`
- Copies the produced exe to project root as `AutoWifiHelper.exe`

Notes:
- Run in an elevated shell if you encounter permission issues when exporting or adding profiles.
- The produced exe is console-based (keeps interactive menu). To hide console, remove `--console` and test UI changes.
#>

Set-StrictMode -Version Latest

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $projectRoot

$venv = Join-Path $projectRoot ".venv_build"
if (-not (Test-Path $venv)) {
    Write-Host "Creating virtual environment at $venv"
    python -m venv $venv
}

$activate = Join-Path $venv "Scripts\Activate.ps1"
if (-not (Test-Path $activate)) {
    Write-Error "Activate script not found at $activate. Ensure Python is installed and available as 'python'."
    Pop-Location
    exit 1
}

Write-Host "Activating venv and installing PyInstaller..."
& $activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install pyinstaller

Write-Host "Building single-file exe with PyInstaller (this can take a minute)"
# If gui_main.py exists, build GUI exe without console, otherwise build console exe from main.py
if (Test-Path (Join-Path $projectRoot "gui_main.py")) {
    Write-Host "Detected gui_main.py — building GUI executable AutoWifiHelperGUI.exe (no console)"
    pyinstaller --onefile --noconsole --name AutoWifiHelperGUI gui_main.py
    $distExe = Join-Path $projectRoot "dist\AutoWifiHelperGUI.exe"
    if (Test-Path $distExe) {
        Copy-Item -Path $distExe -Destination (Join-Path $projectRoot "AutoWifiHelperGUI.exe") -Force
        Write-Host "Built GUI exe copied to: $projectRoot\AutoWifiHelperGUI.exe"
    } else {
        Write-Error "GUI build failed or output not found at $distExe"
    }
} else {
    Write-Host "No GUI file detected; building console exe AutoWifiHelper.exe from main.py"
    pyinstaller --onefile --console --name AutoWifiHelper main.py
    $distExe = Join-Path $projectRoot "dist\AutoWifiHelper.exe"
    if (Test-Path $distExe) {
        Copy-Item -Path $distExe -Destination (Join-Path $projectRoot "AutoWifiHelper.exe") -Force
        Write-Host "Built exe copied to: $projectRoot\AutoWifiHelper.exe"
    } else {
        Write-Error "Build failed or output not found at $distExe"
    }
}

Write-Host "Done. To clean build artifacts, remove 'build', 'dist', '*.spec', and '.venv_build' if desired."
Pop-Location
