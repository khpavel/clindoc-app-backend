@echo off
REM Скрипт для запуска сервера разработки
REM Использование: run_server.bat

echo Проверка виртуального окружения...
if not exist venv (
    echo ОШИБКА: Виртуальное окружение не найдено!
    echo Сначала выполните: reinstall_venv.bat
    pause
    exit /b 1
)

echo Активация виртуального окружения...
call venv\Scripts\activate.bat

echo.
echo Запуск сервера на http://localhost:8000
echo Нажмите Ctrl+C для остановки
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause





