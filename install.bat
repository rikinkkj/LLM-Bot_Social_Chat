@echo off
setlocal enabledelayedexpansion

:: Installer script for bot_social_network on Windows
:: Supports a non-interactive test mode with the --test flag

:: --- Configuration ---
set "INSTALL_DIR=%cd%"
set "ENV_TYPE=venv"
set "BIN_DIR="

:: --- Main Execution ---
if /i "%1" == "--test" (
    echo INFO: Running in non-interactive test mode.
    set "INSTALL_DIR=%TEMP%\bot_social_network_install\project"
    set "BIN_DIR=%TEMP%\bot_social_network_bin"
    set "ENV_TYPE=venv"
    
    :: Clean up previous test runs
    if exist "%TEMP%\bot_social_network_install" rmdir /s /q "%TEMP%\bot_social_network_install"
    if exist "%TEMP%\bot_social_network_bin" rmdir /s /q "%TEMP%\bot_social_network_bin"
    
    mkdir "%INSTALL_DIR%"
    mkdir "%BIN_DIR%"
) else (
    :: --- Interactive Prompts ---
    set /p "USER_INSTALL_DIR=Enter installation directory [%cd%]: "
    if defined USER_INSTALL_DIR set "INSTALL_DIR=%USER_INSTALL_DIR%"

    echo Select Python environment type:
    echo   1. Python venv (recommended)
    echo   2. Use base Python environment (not recommended)
    set /p "ENV_CHOICE=Enter your choice (1-2): "
    if "%ENV_CHOICE%" == "2" (
        set "ENV_TYPE=base"
    ) else (
        set "ENV_TYPE=venv"
    )

    :: For Windows, we'll just offer to create a launcher in a common location
    :: and let the user add it to their PATH if they wish.
    set "DEFAULT_BIN_DIR=%USERPROFILE%\Scripts"
    echo A launcher script can be created for easy access.
    set /p "CREATE_LAUNCHER=Create a launcher in %DEFAULT_BIN_DIR%? [y/N]: "
    if /i "%CREATE_LAUNCHER%" == "y" (
        set "BIN_DIR=%DEFAULT_BIN_DIR%"
        if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"
        echo NOTE: You may need to add %BIN_DIR% to your system's PATH to run the app from anywhere.
    )
)

:: --- Ollama Check ---
echo ---
echo INFO: Checking for Ollama installation...
where ollama >nul 2>nul
if %errorlevel% == 0 (
    echo [V] Ollama is installed. You can use local models.
) else (
    echo [!] Ollama not found.
    echo    To use local AI models, please install Ollama from https://ollama.com
)
echo ---

set "VENV_DIR=%INSTALL_DIR%\venv"
set "PROJECT_ROOT=%cd%"

:: --- Copy Project Files ---
if not "%INSTALL_DIR%" == "%PROJECT_ROOT%" (
    echo INFO: Copying project files to %INSTALL_DIR%...
    xcopy "%PROJECT_ROOT%" "%INSTALL_DIR%" /e /i /y /exclude:.gitexclude
    echo .git\ > .gitexclude
    echo *.tmp >> .gitexclude
    echo tests\ >> .gitexclude
)

cd /d "%INSTALL_DIR%"

:: --- Environment Setup ---
if "%ENV_TYPE%" == "venv" (
    echo INFO: Creating Python venv environment...
    python -m venv "%VENV_DIR%"
    call "%VENV_DIR%\Scripts\activate.bat"
) else (
    echo INFO: Using base Python environment.
)

:: --- Dependency Installation ---
echo INFO: Installing dependencies from requirements.txt...
pip install -r requirements.txt

:: --- Create Launcher ---
if defined BIN_DIR (
    echo INFO: Creating launcher...
    (
        echo @echo off
        echo call "%INSTALL_DIR%\venv\Scripts\activate.bat"
        echo python "%INSTALL_DIR%\main.py" %*
    ) > "%BIN_DIR%\bot-social-network.bat"
)

:: --- Verification ---
if defined BIN_DIR (
    echo INFO: Verifying installation...
    if exist "%BIN_DIR%\bot-social-network.bat" (
        echo SUCCESS: Launcher created at %BIN_DIR%\bot-social-network.bat
    ) else (
        echo ERROR: Launcher creation failed.
        exit /b 1
    )
)

echo INFO: Installation complete.
if defined BIN_DIR (
    echo You can now run the application by typing: bot-social-network
) else (
    echo To run the application, navigate to the installation directory (%INSTALL_DIR%) and run: python main.py
)

endlocal
