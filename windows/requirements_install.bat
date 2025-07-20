@echo off
REM ==============================================================
REM PocketOption Signal Generator - Windows Installation Script
REM ==============================================================
REM This script will:
REM 1. Install Python 3.10 if not present
REM 2. Create virtual environment
REM 3. Install required packages
REM 4. Configure TA-Lib technical analysis library
REM 5. Set up environment variables
REM ==============================================================

echo.
echo [1/7] Checking system requirements...
echo.

REM Check OS version
ver | findstr /i "10.0" > nul
if %errorlevel% neq 0 (
    echo ERROR: This application requires Windows 10 or later
    pause
    exit /b 1
)

REM Check architecture
if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    set ARCH=x64
) else (
    set ARCH=x86
)

echo Detected system: Windows 10 %ARCH%
echo.

REM ==============================================================
echo [2/7] Checking Python installation...
echo.

where python >nul 2>nul
if %errorlevel% equ 0 (
    python --version
) else (
    echo Python not found. Installing Python 3.10...
    
    REM Download Python installer
    curl -L -o python_installer.exe https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe
    
    if not exist python_installer.exe (
        echo ERROR: Failed to download Python installer
        pause
        exit /b 1
    )
    
    REM Install Python silently
    echo Installing Python 3.10...
    start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
    
    REM Verify installation
    where python >nul 2>nul
    if %errorlevel% neq 0 (
        echo ERROR: Python installation failed
        pause
        exit /b 1
    )
)

REM ==============================================================
echo [3/7] Creating virtual environment...
echo.

python -m venv venv
if not exist venv\Scripts\activate.bat (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

REM ==============================================================
echo [4/7] Installing required packages...
echo.

call venv\Scripts\activate.bat
pip install --upgrade pip wheel setuptools

REM Install requirements
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ERROR: Package installation failed
    pause
    exit /b 1
)

REM ==============================================================
echo [5/7] Installing TA-Lib technical analysis library...
echo.

REM Download TA-Lib binary
if "%ARCH%"=="x64" (
    curl -L -o TA_Lib-0.4.24-cp310-cp310-win_amd64.whl https://github.com/mrjbq7/ta-lib/releases/download/v0.4.24/TA_Lib-0.4.24-cp310-cp310-win_amd64.whl
) else (
    curl -L -o TA_Lib-0.4.24-cp310-cp310-win32.whl https://github.com/mrjbq7/ta-lib/releases/download/v0.4.24/TA_Lib-0.4.24-cp310-cp310-win32.whl
)

if not exist TA_Lib-*.whl (
    echo WARNING: Failed to download TA-Lib binary. Using standard installation...
    pip install TA-Lib
) else (
    pip install TA_Lib-*.whl
    del TA_Lib-*.whl
)

REM ==============================================================
echo [6/7] Creating desktop shortcut...
echo.

set SCRIPT_PATH=%~dp0
set SHORTCUT_PATH=%PUBLIC%\Desktop\PocketOption Signal Generator.lnk

REM Create shortcut VBS script
echo Set oWS = WScript.CreateObject("WScript.Shell") > create_shortcut.vbs
echo sLinkFile = "%SHORTCUT_PATH%" >> create_shortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> create_shortcut.vbs
echo oLink.TargetPath = "%SCRIPT_PATH%venv\Scripts\pythonw.exe" >> create_shortcut.vbs
echo oLink.Arguments = """%SCRIPT_PATH%main.py""" >> create_shortcut.vbs
echo oLink.WorkingDirectory = "%SCRIPT_PATH%" >> create_shortcut.vbs
echo oLink.Description = "PocketOption Signal Generator" >> create_shortcut.vbs
echo oLink.IconLocation = "%SCRIPT_PATH%windows\icon.ico" >> create_shortcut.vbs
echo oLink.Save >> create_shortcut.vbs

cscript //nologo create_shortcut.vbs
del create_shortcut.vbs

if exist "%SHORTCUT_PATH%" (
    echo Shortcut created on desktop
) else (
    echo WARNING: Failed to create desktop shortcut
)

REM ==============================================================
echo [7/7] Finalizing installation...
echo.

REM Create default config if not exists
if not exist config\config.ini (
    copy config\config.ini.template config\config.ini
)

echo Installation complete!
echo.
echo Next steps:
echo 1. Edit config\config.ini with your Telegram credentials
echo 2. Customize assets in config\assets_list.json
echo 3. Double-click the desktop shortcut to start
echo 4. For automated signals, create a scheduled task to run windows\start.bat
echo.

pause
