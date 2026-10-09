Write-Host "Starting Forest Fire Platform..." -ForegroundColor Green
$root = $PSScriptRoot
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; .venv\Scripts\uvicorn.exe services.api.app.main:app --host 0.0.0.0 --port 8000 --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\apps\web'; npm.cmd run dev"
Start-Sleep -Seconds 3
Start-Process "http://localhost:5173"
Write-Host "Both servers launched and browser opened to http://localhost:5173" -ForegroundColor Green
