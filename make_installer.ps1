<#
PowerShell helper to build the Inno Setup installer.

Usage:
1. Ensure `AutoWifiHelperGUI.exe` exists in the project root (build with `build_exe.ps1`).
2. If Inno Setup (ISCC.exe) is installed and available on PATH, this script will run it.
3. If ISCC.exe is not found, the script will print instructions.
#>

$exeName = "AutoWifiHelperGUI.exe"
$issFile = Join-Path $PSScriptRoot "installer.iss"

if (-not (Test-Path (Join-Path $PSScriptRoot $exeName))) {
    Write-Error "Built exe not found: $exeName. Run .\build_exe.ps1 first."
    exit 1
}

# Try to find ISCC.exe on PATH or common install locations
$iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source -ErrorAction SilentlyContinue
if (-not $iscc) {
    $common = @(
        "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe",
        "C:\\Program Files\\Inno Setup 6\\ISCC.exe"
    )
    foreach ($p in $common) {
        if (Test-Path $p) { $iscc = $p; break }
    }
}

if ($iscc) {
    Write-Host "Found ISCC: $iscc`nCompiling installer..."
    & "$iscc" "$issFile"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Installer built successfully. Output is in the current folder (see installer filename Auto_login_wifi_Setup.exe)."
    } else {
        Write-Error "ISCC exited with code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
} else {
    Write-Host "Inno Setup compiler (ISCC.exe) not found on PATH."
    Write-Host "Options:"
    Write-Host "  1) Install Inno Setup from https://jrsoftware.org/ and run this script again."
    Write-Host "  2) Manually compile: open Inno Setup IDE, load 'installer.iss' and press Compile."
}
