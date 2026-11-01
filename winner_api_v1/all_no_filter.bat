@echo on
:: מעבר לתיקיית הפרויקט הראשי
cd /d "C:\Users\dkdk1\PycharmProjects\PythonProjectNew"
set timestamp=%date:~-4%-%date:~3,2%-%date:~0,2%_%time:~0,2%-%time:~3,2%
set timestamp=%timestamp: =0%
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set PYTHONPATH=C:\Users\dkdk1\PycharmProjects\PythonProjectNew


py -3.12 winner_final\table_game_no_filter.py
pause