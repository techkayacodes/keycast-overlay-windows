<#
.SYNOPSIS
Installs keycast-overlay-windows and optionally creates a Windows Startup shortcut.
#>
param(
    [switch]$Autostart
)

$ErrorActionPreference = "Stop"
$repoDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Installing keycast-overlay-windows..."
if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv tool install --force $repoDir
} elseif (Get-Command pip -ErrorAction SilentlyContinue) {
    pip install --user $repoDir
} else {
    throw "Neither uv nor pip was found on PATH. Install Python 3.10+ first."
}

if ($Autostart) {
    $startupDir = [Environment]::GetFolderPath("Startup")
    $shortcutPath = Join-Path $startupDir "keycast-overlay.lnk"
    $wsh = New-Object -ComObject WScript.Shell
    $sc = $wsh.CreateShortcut($shortcutPath)
    $sc.TargetPath = Join-Path $repoDir "start-overlay.bat"
    $sc.WorkingDirectory = $repoDir
    $sc.WindowStyle = 7
    $sc.Description = "Start keycast-overlay on Windows login"
    $sc.Save()
    Write-Host "Added Startup shortcut: $shortcutPath"
}

Write-Host "Done! Run 'keycast-overlay' or double-click start-overlay.bat to launch."
