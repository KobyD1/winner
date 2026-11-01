@echo off
set timestamp=%date:~-4%-%date:~3,2%-%date:~0,2%_%time:~0,2%-%time:~3,2%
set timestamp=%timestamp: =0%
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

set project_root=C:\Users\dkdk1\PycharmProjects\PythonProjectNew
set script_path=%project_root%\winner_final

cd /d %script_path%

set PYTHONPATH=%project_root%
wnba_game_final.py > "C:\Users\Public\Winner\results\output_%timestamp%.txt" 2>&1
