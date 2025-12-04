# Скрипт для запуска сервера разработки (PowerShell)
# Использование: .\run_server.ps1

Write-Host "Проверка виртуального окружения..." -ForegroundColor Yellow

if (-not (Test-Path "venv")) {
    Write-Host "ОШИБКА: Виртуальное окружение не найдено!" -ForegroundColor Red
    Write-Host "Сначала выполните: .\reinstall_venv.ps1" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host "Активация виртуального окружения..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "Запуск сервера на http://localhost:8000" -ForegroundColor Green
Write-Host "Нажмите Ctrl+C для остановки" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000



