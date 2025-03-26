@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

set APP_NAME=Homescanner
set PYTHON=python
set REQUIRED_FILES=main.py requirements.txt
set LOG_DIR=logs
set DATA_DIR=data
set DB_FILE=data\incidents.db
set VENV_DIR=.venv

:print_header
echo.
echo ====================================================
echo      %APP_NAME% Environment Diagnostic Tool
echo ====================================================
echo.
goto :eof

:check_python
%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    call :color_echo red "[FAIL] Python is not installed or not in PATH."
) else (
    for /f "tokens=2 delims= " %%v in ('%PYTHON% --version') do (
        call :color_echo green "[ OK ] Python detected: %%v"
    )
)
goto :eof

:check_pip
pip --version >nul 2>&1
if errorlevel 1 (
    call :color_echo red "[FAIL] pip not found. You may not be able to install dependencies."
) else (
    call :color_echo green "[ OK ] pip is available."
)
goto :eof

:check_virtualenv
if exist "%VENV_DIR%" (
    call :color_echo green "[ OK ] Virtual environment found: %VENV_DIR%"
) else (
    call :color_echo yellow "[WARN] Virtual environment not found. You may need to run 'homescanner.bat run'"
)
goto :eof

:check_required_files
for %%f in (%REQUIRED_FILES%) do (
    if not exist "%%f" (
        call :color_echo red "[FAIL] Required file missing: %%f"
    ) else (
        call :color_echo green "[ OK ] Found: %%f"
    )
)
goto :eof

:check_log_directory
if exist "%LOG_DIR%" (
    call :color_echo green "[ OK ] Log directory exists: %LOG_DIR%"
) else (
    call :color_echo yellow "[WARN] Log directory missing: %LOG_DIR%"
)
goto :eof

:check_data_directory
if exist "%DATA_DIR%" (
    call :color_echo green "[ OK ] Data directory exists: %DATA_DIR%"
) else (
    call :color_echo yellow "[WARN] Data directory missing: %DATA_DIR%"
)
goto :eof

:check_database_file
if exist "%DB_FILE%" (
    call :color_echo green "[ OK ] Database file found: %DB_FILE%"
) else (
    call :color_echo red "[FAIL] Database file missing: %DB_FILE%"
)
goto :eof

:check_internet
powershell -Command "try { $r = Invoke-WebRequest -Uri 'https://www.google.com' -UseBasicParsing -TimeoutSec 5; exit 0 } catch { exit 1 }"
if errorlevel 1 (
    call :color_echo red "[FAIL] No internet connection or firewall blocking."
) else (
    call :color_echo green "[ OK ] Internet connectivity verified."
)
goto :eof

:check_sqlite_support
%PYTHON% -c "import sqlite3" 2>nul
if errorlevel 1 (
    call :color_echo red "[FAIL] Python sqlite3 module is missing!"
) else (
    call :color_echo green "[ OK ] Python sqlite3 module is available."
)
goto :eof

:color_echo
set COLOR=%1
shift
powershell -Command "Write-Host '%*' -ForegroundColor %COLOR%"
goto :eof

:run_diagnostics
call :print_header
call :check_python
call :check_pip
call :check_virtualenv
call :check_required_files
call :check_log_directory
call :check_data_directory
call :check_database_file
call :check_sqlite_support
call :check_internet
goto :eof

:footer
echo.
call :color_echo cyan "Diagnostics completed."
echo.
goto :eof

REM ==== MAIN ====
call :run_diagnostics
call :footer

endlocal
