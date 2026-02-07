#!/bin/bash

# Exit on error
set -e

echo "Updating translations..."

# Navigate to project root (parent of scripts directory)
cd "$(dirname "$0")/.."

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Error: venv not found. Please ensure virtual environment is created."
    exit 1
fi

# Compile messages
python manage.py compilemessages

echo "Done. Translations updated."
