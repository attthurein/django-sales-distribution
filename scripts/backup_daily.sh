#!/bin/bash

# Daily Database Backup - run via Cron
# Set PROJECT_ROOT to your Sales project directory
# Resolve the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Activate venv if exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Create logs directory if not exists
mkdir -p logs

# Run backup and log output
echo "Starting Backup at $(date)" >> logs/backup_log.txt
python manage.py backup_db --keep-days=30 >> logs/backup_log.txt 2>&1

if [ $? -ne 0 ]; then
    echo "Backup failed at $(date)" >> logs/backup_log.txt
    exit 1
fi

echo "Backup completed at $(date)" >> logs/backup_log.txt
exit 0
