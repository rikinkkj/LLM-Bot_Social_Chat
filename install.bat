@echo off
setlocal enabledelayedexpansion

:: Installer script for bot_social_network on Windows
:: - Checks for Python
:: - Guides user for manual installation if needed
:: - Sets up the application

:main
    call :print_header "Bot Social Network Installer for Windows"
    call :check_python
    call :run_setup
    goto :eof

:check_python
    call :print_header "Checking for Python"
    where python >nul 2>nul
    if %errorlevel% == 0 (
        echo [V] Python is installed.
    ) else (
        echo [!] ERROR: Python is not found in your PATH.
        echo.
        echo Please install Python 3.9+ from the official website:
        echo https://www.python.org/downloads/
        echo.
        echo IMPORTANT: During installation, make sure to check the box that says
        echo "'Add Python to PATH'".
        echo.
        pause
        start https://www.python.org/downloads/
        exit /b 1
    )
    goto :eof

:run_setup
    call :print_header "Application Setup"
    
    set "INSTALL_DIR=%cd%"
    set /p "USER_INSTALL_DIR=Enter installation directory [%cd%]: "
    if defined USER_INSTALL_DIR set "INSTALL_DIR=%USER_INSTALL_DIR%"

    echo.
    echo Select Python environment type:
    echo   1. Python venv (recommended)
    echo   2. Use base Python environment (not recommended)
    set /p "ENV_CHOICE=Enter your choice (1-2): "
    if "%ENV_CHOICE%" == "2" (
        set "ENV_TYPE=base"
    ) else (
        set "ENV_TYPE=venv"
    )

    set "VENV_DIR=%INSTALL_DIR%\venv"
    
    if not "%INSTALL_DIR%" == "%cd%" (
        echo INFO: Copying project files to %INSTALL_DIR%...
        xcopy "%cd%" "%INSTALL_DIR%" /e /i /y /exclude:.gitexclude
        echo .git\ > .gitexclude
        echo *.tmp >> .gitexclude
        echo tests\ >> .gitexclude
        echo logs\ >> .gitexclude
    )

    cd /d "%INSTALL_DIR%"

    if "%ENV_TYPE%" == "venv" (
        echo INFO: Creating Python venv environment...
        python -m venv "%VENV_DIR%"
        call "%VENV_DIR%\Scripts\activate.bat"
    )

    echo INFO: Installing Python packages from requirements.txt...
    pip install -r requirements.txt

    call :print_header "Installation Complete"
    echo.
    echo To run the application, navigate to your installation directory:
    echo cd /d "%INSTALL_DIR%"
    echo.
    echo Then, run the main script:
    echo python main.py
    echo.
    echo Enjoy the simulation!
    goto :eof

:print_header
    echo =================================================
    echo  %~1
    echo =================================================
    goto :eof