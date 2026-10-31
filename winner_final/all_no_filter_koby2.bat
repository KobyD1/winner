@echo off
:: מעבר לתיקיית הפרויקט הראשי
cd /d "C:\Users\dkdk1\PycharmProjects\PythonProjectNew"
set timestamp=%date:~-4%-%date:~3,2%-%date:~0,2%_%time:~0,2%-%time:~3,2%
set timestamp=%timestamp: =0%
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
:: הגדרת תיקיית השורש של הפרויקט
set PYTHONPATH=C:\Users\dkdk1\PycharmProjects\PythonProjectNew

:: התקנה מפורשת של fpdf המקורי על פייתון המערכת כדי לפתור את השגיאה
py -3.12 -m pip uninstall --yes pypdf && pip install --upgrade fpdf2

:: הרצת הסקריפט באמצעות פייתון 3.12 של המחשב
py -3.12 winner_final\table_game_no_filter.py > "C:\Users\Public\Winner\games\output_%timestamp%.txt" 2>&1

