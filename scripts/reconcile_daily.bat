@echo off
REM Daily Stock Reconciliation - run via Task Scheduler
REM Set PROJECT_ROOT to your Sales project directory
set PROJECT_ROOT=%~dp0..
cd /d "%PROJECT_ROOT%"

REM Activate venv if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Create logs directory if not exists
if not exist "logs" mkdir logs

REM Run reconciliation and log output
REM Use --fix to automatically correct mismatches, or omit to just report
echo Running Stock Reconciliation at %date% %time% >> logs\reconcile_log.txt
python manage.py reconcile_stock >> logs\reconcile_log.txt 2>&1

if errorlevel 1 (
    echo Reconciliation failed at %date% %time% >> logs\reconcile_log.txt
    exit /b 1
)

echo Reconciliation completed at %date% %time% >> logs\reconcile_log.txt
exit /b 0
