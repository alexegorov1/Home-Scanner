@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

REM ===============================
REM Homescanner Project Launcher
REM Author: You
REM Purpose: Start, manage and monitor Python-based Homescanner
REM ===============================

REM === CONFIGURATION (placeholders for GitHub) ===
set PYTHON=python
set ENTRY_FILE=main.py
set REQUIREMENTS=requirements.txt
set VENV_DIR=.venv
set LOG_FILE=logs\system.log
set LOG_DIR=logs
set APP_NAME=Homescanner

REM === FUNCTIONS ===

:print_header
call :color_echo cyan "================================="
call :color_echo cyan "   %APP_NAME% - Security Monitor"
call :color_echo cyan "================================="
echo.
goto :eof

:color_echo
set COLOR=%1
shift
powershell -Command "Write-Host '%*' -ForegroundColor %COLOR%"
goto :eof

:check_python
%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    call :color_echo red "[ERROR] Python not found in PATH. Install Python 3 and try again."
    exit /b 1
)
goto :eof

:create_directories
if not exist "%LOG_DIR%" (
    mkdir "%LOG_DIR%"
    call :color_echo yellow "[*] Created missing log directory: %LOG_DIR%"
)
goto :eof

:create_virtualenv
if not exist "%VENV_DIR%" (
    call :color_echo yellow "[*] Creating virtual environment in '%VENV_DIR%'..."
    %PYTHON% -m venv "%VENV_DIR%"
)
call "%VENV_DIR%\Scripts\activate.bat"
goto :eof

:install_dependencies
if exist "%REQUIREMENTS%" (
    call :color_echo yellow "[*] Installing Python dependencies from '%REQUIREMENTS%'..."
    pip install --upgrade pip >nul
    pip install -r "%REQUIREMENTS%" || (
        call :color_echo red "[!] Failed to install some dependencies."
        exit /b 1
    )
) else (
    call :color_echo red "[!] File '%REQUIREMENTS%' not found. Skipping dependency installation."
)
goto :eof

:start_application
call :color_echo green "[*] Starting %APP_NAME%..."
%PYTHON% "%ENTRY_FILE%"
goto :eof

:tail_logs
if exist "%LOG_FILE%" (
    call :color_echo yellow "[*] Last 50 lines of log:"
    powershell -Command "Get-Content -Path '%LOG_FILE%' -Tail 50"
) else (
    call :color_echo red "[!] Log file not found at '%LOG_FILE%'"
)
goto :eof

:clean_up
call :color_echo yellow "[*] Cleaning up virtual environment and logs..."
if exist "%VENV_DIR%" (
    rmdir /s /q "%VENV_DIR%"
    call :color_echo green "[+] Removed virtual environment."
)
if exist "%LOG_FILE%" (
    del /f /q "%LOG_FILE%"
    call :color_echo green "[+] Removed system log file."
)
goto :eof

:rebuild
call :clean_up
call :create_directories
call :create_virtualenv
call :install_dependencies
goto :eof

:help
call :print_header
echo Usage:
echo   homescanner.bat [command]
echo.
echo Available Commands:
call :color_echo cyan "   run      " & echo - Start the application
call :color_echo cyan "   logs     " & echo - Show last 50 log entries
call :color_echo cyan "   clean    " & echo - Remove logs and virtualenv
call :color_echo cyan "   rebuild  " & echo - Clean and re-install everything
call :color_echo cyan "   help     " & echo - Show this help message
goto :eof

REM === ROUTING ===

if "%1"=="run" (
    call :print_header
    call :check_python
    call :create_directories
    call :create_virtualenv
    call :install_dependencies
    call :start_application
    goto :eof
)

if "%1"=="logs" (
    call :tail_logs
    goto :eof
)

if "%1"=="clean" (
    call :clean_up
    goto :eof
)

if "%1"=="rebuild" (
    call :rebuild
    goto :eof
)

call :help
endlocal
