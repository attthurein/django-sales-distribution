@echo off
echo Updating translations...
cd ..
call venv\Scripts\activate
python manage.py compilemessages
echo Done.
pause
