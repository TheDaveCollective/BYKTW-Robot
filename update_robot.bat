@echo off
echo ================================================
echo          Steam Robot Firmware Updater
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    echo.
    pause
    exit /b 1
)

REM Check if pyserial is installed
python -c "import serial" >nul 2>&1
if errorlevel 1 (
    echo Installing pyserial dependency...
    python -m pip install pyserial
    if errorlevel 1 (
        echo ERROR: Failed to install pyserial
        echo Please run: pip install pyserial
        echo.
        pause
        exit /b 1
    )
)

REM Run the updater
echo Starting robot updater...
echo.
python robot_updater.py %*

echo.
pause
