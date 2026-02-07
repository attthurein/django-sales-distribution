#!/bin/bash

# Daily Stock Reconciliation - run via Cron
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

# Run reconciliation and log output
# Use --fix to automatically correct mismatches, or omit to just report
echo "Running Stock Reconciliation at $(date)" >> logs/reconcile_log.txt
python manage.py reconcile_stock >> logs/reconcile_log.txt 2>&1

if [ $? -ne 0 ]; then
    echo "Reconciliation failed at $(date)" >> logs/reconcile_log.txt
    exit 1
fi

echo "Reconciliation completed at $(date)" >> logs/reconcile_log.txt
exit 0
