# Скрипт для переустановки виртуального окружения
# Использование: .\reinstall_venv.ps1

Write-Host "Удаление старого виртуального окружения..." -ForegroundColor Yellow

# Удаляем старое venv, если оно существует
if (Test-Path "venv") {
    Remove-Item -Recurse -Force "venv"
    Write-Host "Старое venv удалено" -ForegroundColor Green
} else {
    Write-Host "Старое venv не найдено" -ForegroundColor Gray
}

Write-Host "`nСоздание нового виртуального окружения..." -ForegroundColor Yellow
python -m venv venv

Write-Host "Активация виртуального окружения..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

Write-Host "Обновление pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

Write-Host "`nУстановка зависимостей из requirements.txt..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host "`n✓ Виртуальное окружение успешно переустановлено!" -ForegroundColor Green
Write-Host "`nДля активации в будущем используйте:" -ForegroundColor Cyan
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "`nSwagger UI будет доступен по адресу:" -ForegroundColor Cyan
Write-Host "  http://localhost:8000/docs" -ForegroundColor White
Write-Host "  http://localhost:8000/redoc" -ForegroundColor White

