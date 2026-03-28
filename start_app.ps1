# TesseractX Unified Production Launcher
Write-Host "🚀 Launching TesseractX Production Environment..." -ForegroundColor Cyan

# 1. Start Backend
Write-Host "📦 Starting FastAPI Backend (Port 8000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m uvicorn main:app --host 0.0.0.0 --port 8000"

# 2. Start Frontend
Write-Host "🌐 Starting Next.js Frontend (Port 3000)..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run start"

Write-Host "✅ System is live!" -ForegroundColor Yellow
Write-Host "----------------------------------"
Write-Host "Local Access: http://localhost:3000"
Write-Host "Network Access: Check your IP with 'ipconfig'"
Write-Host "----------------------------------"
