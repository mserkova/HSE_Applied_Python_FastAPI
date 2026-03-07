# API-сервис сокращения ссылок

Сервис для сокращения URL на FastAPI с кэшированием в Redis и хранением данных в PostgreSQL.

Развернутый сервис на Render: https://hse-applied-python-fastapi.onrender.com 

## 💡 Описание

API предоставляет функционал для:
- Регистрации и аутентификации пользователей
- Создания коротких ссылок
- Редиректа по коротким ссылкам с кэшированием
- Отслеживания статистики переходов
- Управления своими ссылками

## 💡 Структура проекта

fastapi/

├── app/

│   ├── __init__.py

│   ├── config.py           # Настройки приложения

│   ├── database.py         # Подключение к БД

│   ├── main.py             # Точка входа, эндпоинты

│   ├── models.py           # SQLAlchemy модели

│   ├── schemas.py          # Pydantic схемы

│   ├── redis.py            # Redis

│   └── utils.py            # Вспомогательные функции

├── .env.example            # Шаблон переменных окружения

├── .gitignore

├── docker-compose.yml      # Docker Compose конфигурация

├── Dockerfile

├── requirements.txt        # Зависимости

└── README.md
Подробное описание каждого модуля и функций представлено в соответствующих файлах

## 💡 Установка и запуск

### Инструкция для локального запуска

1. **Клонируйте репозиторий:**

git clone https://github.com/mserkova/HSE_Applied_Python_FastAPI.git
cd HSE_Applied_Python_FastAPI

2. **Активируйте окружение**
python -m venv .venv
.venv\Scripts\activate  (для Windows)

3. **Установите зависимости**
pip install -r requirements.txt

4. **Создайте файл .env на основе .env.example со своими данными**

5. **Запустите PostgreSQL и Redis**

6. **Запустите сервис командой uvicorn app.main:app --reload**

## Инструкция для запуска при помощи Docker

1. **Создайте файл .env на основе .env.example со своими данными**

2. **Запустите контейнеры командой docker-compose up -d --build**


## 💡 Примеры запросов

1. **POST /auth/register (регистрация пользователя)**

Request:
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user1@example.com",
    "password": "user1"
  }'

Response:
{
  "id": "1",
  "email": "user1@example.com",
  "is_active": true,
  "created_at": "2026-03-07T16:17:37.305522Z"
}

2. **POST /auth/login (вход)**

Request:
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user1@example.com",
    "password": "user1"
  }'

 Response:
 {
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyNEBleGFtcGxlLmNvbSIsImV4cCI6MTc3MjkwMjA5MH0.wSSRfRkIf6ltZzgvn9_pULxsznLpiQncepCFil0ELnc",
  "token_type": "bearer"
}

3. **POST/links/shorten (создание короткой ссылки)**

Request:
curl -X POST "http://localhost:8000/links/shorten" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "original_url": "https://www.harvard.edu/",
    "custom_alias": "Harvard",
    "expires_at": "2026-03-20T16:19:23.515Z",
    "project_name": "University" 
  }'
  
Response:
curl -X 'POST' \
  'http://localhost:8000/links/shorten' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyNEBleGFtcGxlLmNvbSIsImV4cCI6MTc3MjkwMjExNH0.pYH8psZXgIGykx_fWg3C7-AtFGVyhxY7QRBQAvXc7Gc' \
  -H 'Content-Type: application/json' \
  -d '{
  "original_url": "https://www.harvard.edu/",
  "custom_alias": "Harvard",
  "expires_at": "2026-03-20T16:19:23.515Z",
  "project_name": "University"
}'

4. **GET/{short_code} (редирект по короткой ссылке)**

Request:
curl -X GET "http://localhost:8000/Harvard"

Response: HTTP 307 Temporary Redirect → оригинальный URL

5. **GET /links/{short_code}/stats (получение статистики по ссылке)**

Request:
curl -X 'GET' \
  'http://localhost:8000/links/Harvard/stats' \
  -H 'accept: application/json'

Response:
{
  "original_url": "https://www.harvard.edu/",
  "short_code": "Harvard",
  "click_count": 2,
  "created_at": "2026-03-07T16:19:44.105264Z",
  "last_accessed_at": "2026-03-07T16:21:28.338855Z",
  "expires_at": "2026-03-20T16:19:23.515000Z"
}



