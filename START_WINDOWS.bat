@echo off
REM resonant-archive launcher for Windows
REM Double-click this file to start the daemon.
REM Keep this window open while you use Claude Desktop.

echo ================================================
echo   resonant-archive daemon launcher
echo ================================================
echo.
echo This window keeps the embedding model loaded so
echo MCP queries from Claude Desktop stay fast.
echo.
echo Leave it open while you use the archive.
echo Press Ctrl+C to stop when you're done.
echo.
echo ================================================
echo.

REM Check resonant-archive is installed
where resonant-archive >nul 2>&1
if errorlevel 1 (
    echo ERROR: resonant-archive is not installed or not on PATH.
    echo.
    echo Install with:
    echo     pip install resonant-archive
    echo.
    echo See SETUP_GUIDE.md for details.
    pause
    exit /b 1
)

resonant-archive serve

pause
