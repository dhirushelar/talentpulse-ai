@echo off
title TalentPulse AI — Resume Parser Server
echo ====================================================
echo        Starting TalentPulse AI Application
echo ====================================================
echo Opening http://127.0.0.1:5000 in your browser...
start "" "http://127.0.0.1:5000"
.\venv\Scripts\python.exe app.py
pause
