<#
.SYNOPSIS
Builds a standalone, clickable Windows executable (dist/keycast-overlay.exe) with PyInstaller.
#>
$ErrorActionPreference = "Stop"
$repoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $repoDir
try {
    $argsList = @(
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--name", "keycast-overlay",
        "--icon", "assets\keycast.ico",
        "--add-data", "assets\keycast.ico;assets",
        "keycast-overlay.pyw"
    )
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv run --with pyinstaller pyinstaller @argsList
    } else {
        pyinstaller @argsList
    }
    $exe = Join-Path $repoDir "dist\keycast-overlay.exe"
    if (Test-Path $exe) {
        $sizeMB = [math]::Round((Get-Item $exe).Length / 1MB, 2)
        Write-Host "Built $exe ($sizeMB MB)"
    } else {
        throw "Build completed but $exe was not found."
    }
} finally {
    Pop-Location
}
