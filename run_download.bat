@echo off
cd /d C:\crawl_web
call venv\Scripts\activate.bat
python download_all_357_files.py
pause
