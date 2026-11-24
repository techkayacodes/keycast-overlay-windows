<#
.SYNOPSIS
Removes the optional Windows Startup shortcut for keycast-overlay-windows.
#>
$startupDir = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupDir "keycast-overlay.lnk"
if (Test-Path $shortcutPath) {
    Remove-Item $shortcutPath -Force
    Write-Host "Removed Startup shortcut: $shortcutPath"
} else {
    Write-Host "No Startup shortcut found."
}
