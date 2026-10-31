@echo off
REM מריץ את אפליקציית הניהול המקומפלת (app_v2.pyc) עם הפייתון המובנה בהתקנה,
REM בלי חלון קונסולה (pythonw) ובלי צורך בפייתון מותקן על המחשב של המשתמש.
cd /d "%~dp0app"
start "" "%~dp0python\Scripts\pythonw.exe" app_v2.pyc
