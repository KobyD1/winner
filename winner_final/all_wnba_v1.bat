@echo off
set timestamp=%date:~-4%-%date:~3,2%-%date:~0,2%_%time:~0,2%-%time:~3,2%
set timestamp=%timestamp: =0%
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set project_root=C:\Users\USER\PycharmProjects\PythonProjectNew
set script_path=%project_root%\winner_final
cd /d %script_path%
set PYTHONPATH=%project_root%

@REM pip install pandas
@REM playwright install
"C:\Users\USER\AppData\Local\Programs\Python\Python313\python.exe" wnba_game_final.py > "C:\Users\Public\Winner\results\nba_output_%timestamp%.txt" 2>&1
