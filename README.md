# CSR Assistant Backend

Backend API для приложения CSR Assistant на FastAPI.

## Требования

- Python 3.8+
- PostgreSQL
- Виртуальное окружение (venv)

## Установка

1. Создайте виртуальное окружение (если еще не создано):
   ```bash
   python -m venv venv
   ```

2. Активируйте виртуальное окружение:
   - Windows (CMD): `venv\Scripts\activate.bat`
   - Windows (PowerShell): `venv\Scripts\Activate.ps1`
   - Linux/Mac: `source venv/bin/activate`

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

## Настройка

1. Создайте файл `.env.dev` в корне проекта со следующим содержимым:
   ```env
   database_url=postgresql://username:password@localhost:5432/dbname
   secret_key=your-secret-key-here-minimum-32-characters-long
   access_token_expire_minutes=60
   ```

   **Важно:** Замените `username`, `password`, `localhost`, `5432` и `dbname` на ваши реальные данные PostgreSQL.

2. Для генерации секретного ключа можно использовать:
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```

## Запуск сервера

### Вариант 1: Через uvicorn напрямую
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Вариант 2: Через Python модуль
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Сервер будет доступен по адресу: `http://localhost:8000`

## API Документация

После запуска сервера доступна интерактивная документация:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Настройка клиента (Frontend)

**Важно:** Клиент должен обращаться к бэкенду по адресу `http://localhost:8000`, а не к своему собственному порту.

### Если используется Vite

Настройте прокси в `vite.config.js` или `vite.config.ts`:

```javascript
export default {
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
}
```

Тогда клиент может использовать относительные пути: `/api/v1/auth/token`

### Если прокси не используется

В клиентском коде (например, в `authApi.ts`) установите базовый URL:

```typescript
const API_BASE_URL = 'http://localhost:8000';

// Пример использования:
fetch(`${API_BASE_URL}/api/v1/auth/token`, {
  method: 'POST',
  // ...
});
```

## Структура проекта

```
.
├── app/
│   ├── api/          # API endpoints
│   │   └── v1/       # API версия 1
│   ├── core/         # Основные настройки (config, security)
│   ├── db/           # Настройки базы данных
│   ├── models/       # SQLAlchemy модели
│   ├── schemas/      # Pydantic схемы
│   └── main.py       # Точка входа приложения
├── alembic/          # Миграции базы данных
├── requirements.txt  # Зависимости Python
└── .env.dev         # Переменные окружения (создать вручную)
```

## Решение проблем

### Ошибка "ERR_CONNECTION_REFUSED"

Убедитесь, что:
1. Бэкенд запущен на порту 8000
2. Клиент обращается к правильному URL (`http://localhost:8000`, а не `http://localhost:5173`)
3. Настроен прокси в Vite (если используется) или правильный базовый URL в клиентском коде

### Ошибка 500 при авторизации

Проверьте:
1. Существует ли файл `.env.dev` с правильными настройками
2. Запущена ли база данных PostgreSQL
3. Правильно ли указан `database_url` в `.env.dev`
4. Созданы ли таблицы в базе данных (они создаются автоматически при запуске)

### Проверка работы сервера

Откройте в браузере: http://localhost:8000/health

Должен вернуться ответ: `{"status": "ok"}`

## Разработка

Для разработки используйте флаг `--reload` при запуске uvicorn, чтобы сервер автоматически перезагружался при изменении кода.

## Миграции базы данных

Для работы с миграциями используется Alembic. См. документацию Alembic для подробностей.

