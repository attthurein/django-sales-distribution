#!/bin/bash

# Archive Audit Logs (Older than 6 months) - run via Cron
# Set PROJECT_ROOT to your Sales project directory
# Using $(dirname "$0")/.. to get the parent directory of the script
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Activate venv if exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Create logs directory if not exists
if [ ! -d "logs" ]; then
    mkdir logs
fi

# Log file path
LOG_FILE="logs/archive_log.txt"

# Run archiving and log output
echo "Running Audit Log Archiving at $(date)" >> "$LOG_FILE"
python3 manage.py archive_audit_logs >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "Archiving failed at $(date)" >> "$LOG_FILE"
    exit 1
fi

echo "Archiving completed at $(date)" >> "$LOG_FILE"
exit 0
