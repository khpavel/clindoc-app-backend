@echo off
REM Скрипт для переустановки виртуального окружения (CMD версия)
REM Использование: reinstall_venv.bat

echo Удаление старого виртуального окружения...
if exist venv (
    rmdir /s /q venv
    echo Старое venv удалено
) else (
    echo Старое venv не найдено
)

echo.
echo Создание нового виртуального окружения...
python -m venv venv

echo.
echo Активация виртуального окружения...
call venv\Scripts\activate.bat

echo.
echo Обновление pip...
python -m pip install --upgrade pip

echo.
echo Установка зависимостей из requirements.txt...
pip install -r requirements.txt

echo.
echo ✓ Виртуальное окружение успешно переустановлено!
echo.
echo Для активации в будущем используйте:
echo   venv\Scripts\activate.bat
echo.
echo Swagger UI будет доступен по адресу:
echo   http://localhost:8000/docs
echo   http://localhost:8000/redoc
echo.

