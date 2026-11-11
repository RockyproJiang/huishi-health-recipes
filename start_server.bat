@echo off
title Flask-Waitress Server
cd /d "%~dp0"
echo Installing dependencies...
python -m pip install -r requirements.txt
echo Starting Flask application with Waitress...
waitress-serve --port=5001 --threads=4 wsgi:app
pause
