@echo off
echo ===============================
echo Cafe Sales Report Generator
echo ===============================
echo.

cd /d "%~dp0"

echo Running report...
python src\analysis.py

echo.
echo Report generation completed.
pause
