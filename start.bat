@echo off
echo Starting Forest Fire Platform...
cd /d "%~dp0"
start "Forest Fire API (Backend)" cmd /k ".venv\Scripts\uvicorn.exe services.api.app.main:app --host 0.0.0.0 --port 8000 --reload"
start "Forest Fire Web (Frontend)" cmd /k "cd apps\web && npm.cmd run dev"
timeout /t 3 /nobreak >nul
start http://localhost:5173
echo Both servers have been launched! Browser opened to http://localhost:5173
