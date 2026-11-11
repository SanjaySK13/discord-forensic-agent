Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Starting Discord Confession Attribution Web App..." -ForegroundColor Green
Write-Host "Open in your browser: http://localhost:5000" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan

Set-Location -Path $PSScriptRoot
python server.py

