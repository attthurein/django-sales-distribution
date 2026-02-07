@echo off
REM Daily database backup - run via Task Scheduler
REM Set PROJECT_ROOT to your Sales project directory
set PROJECT_ROOT=%~dp0..
cd /d "%PROJECT_ROOT%"

REM Activate venv if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python manage.py backup_db --keep-days=30
if errorlevel 1 (
    echo Backup failed at %date% %time%
    exit /b 1
)
echo Backup completed at %date% %time%
exit /b 0
