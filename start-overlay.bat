@echo off
setlocal
cd /d "%~dp0"
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw -m keycast_overlay %*
) else (
    start "" pyw -m keycast_overlay %*
)
