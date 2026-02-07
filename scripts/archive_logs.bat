@echo off
REM Archive Audit Logs (Older than 6 months) - run via Task Scheduler
REM Set PROJECT_ROOT to your Sales project directory
set PROJECT_ROOT=%~dp0..
cd /d "%PROJECT_ROOT%"

REM Activate venv if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Create logs directory if not exists
if not exist "logs" mkdir logs

REM Run archiving and log output
echo Running Audit Log Archiving at %date% %time% >> logs\archive_log.txt
python manage.py archive_audit_logs >> logs\archive_log.txt 2>&1

if errorlevel 1 (
    echo Archiving failed at %date% %time% >> logs\archive_log.txt
    exit /b 1
)

echo Archiving completed at %date% %time% >> logs\archive_log.txt
exit /b 0
