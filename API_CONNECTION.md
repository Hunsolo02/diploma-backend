# Подключение к Diploma Backend API

## Базовый URL

```
http://localhost:8000
```

Для production замените на адрес вашего сервера.

---

## Запуск сервера

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск (по умолчанию на порту 8000)
uvicorn main:app --reload

# Запуск на другом хосте/порту
uvicorn main:app --host 0.0.0.0 --port 8000
```

Интерактивная документация: **http://localhost:8000/docs**

---

## Конфигурация (.env)

Создайте файл `.env` в корне проекта (или скопируйте из `.env.example`):

| Переменная | Описание | Пример |
|------------|----------|--------|
| `DATABASE_URL` | Подключение к БД | `sqlite:///./app.db` или `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | Ключ для JWT (сгенерировать: `openssl rand -hex 32`) | `a1b2c3d4...` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни токена (мин) | `30` |
| `LANDMARK_WEIGHTS_PATH` | Путь к файлу весов модели (landmarks) | `/path/to/landmark_model.pth` |
| `CORS_ORIGINS` | Разрешённые origin'ы для CORS (через запятую) | `http://localhost:3000,http://localhost:5173` |
| `DEBUG` | Режим отладки | `true` / `false` |
| `APP_NAME` | Название приложения | `Diploma Backend` |

---

## Аутентификация (JWT)

### Регистрация
```
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "user",
  "password": "secret123",
  "name": "Иван"  // опционально
}
```

### Вход
```
POST /api/auth/login
Content-Type: application/json

{
  "username": "user",
  "password": "secret123"
}

→ {"access_token": "eyJ...", "token_type": "bearer"}
```

### Защищённые запросы
Добавьте заголовок:
```
Authorization: Bearer <access_token>
```

### Текущий пользователь
```
GET /api/auth/me
Authorization: Bearer <token>

→ {"id": 1, "email": "...", "username": "...", "name": "...", "role": "user", "is_active": true, ...}
```

---

## API Endpoints

### Публичные (без авторизации)

#### Анализ изображения (data URL)
```
POST /api/analyze
Content-Type: application/json

{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}

→ {"sessionId": "uuid-here", "questions": [{"id": "skin_type", "label": "Тип кожи", "type": "select", "options": [...]}, ...]}
```

#### Отправка ответов на вопросы
```
POST /api/analyze/answers
Content-Type: application/json

{
  "sessionId": "uuid-from-previous-step",
  "answers": {"skin_type": "нормальная", "reaction": "загораю постепенно"}
}

→ {"result": {"phenotype": "...", "origin": "...", "recommendations": [...], "summary": "...", "raw": {...}}}
```

#### Получить результат сессии
```
GET /api/analyze/sessions/{sessionId}

→ {"sessionId": "...", "result": {...}}
```

#### Анализ landmarks (файл)
```
POST /api/analyze/landmarks
Content-Type: multipart/form-data
Body: file=<image file>

→ {"points": [[x1,y1], ...], "annotated_image_base64": "..."}
```

#### Справочники
- `GET /api/regions/` — список регионов
- `GET /api/phenotypes/` — список фенотипов
- `GET /api/face-features/` — список признаков лица
- `GET /api/user-profiles/` — профили
- `GET /api/items/` — items (пример)

---

### CRUD (большинство — без авторизации)

| Ресурс | GET / | POST / | GET /{id} | PATCH /{id} | DELETE /{id} |
|--------|-------|--------|-----------|-------------|--------------|
| regions | ✅ | ✅ | ✅ | ✅ | ✅ |
| phenotypes | ✅ | ✅ | ✅ | ✅ | ✅ |
| face-features | ✅ | ✅ | ✅ | ✅ | ✅ |
| user-profiles | ✅ | ✅ | ✅ | ✅ | ✅ |
| items | ✅ | ✅* | ✅ | ✅ | ✅ |

\* POST /api/items требует Bearer токен

---

## Пример для фронтенда (JavaScript/fetch)

```javascript
const BASE_URL = 'http://localhost:8000';

// Вход и сохранение токена
const login = async (username, password) => {
  const res = await fetch(`${BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  const { access_token } = await res.json();
  localStorage.setItem('token', access_token);
  return access_token;
};

// Защищённый запрос
const me = async () => {
  const token = localStorage.getItem('token');
  const res = await fetch(`${BASE_URL}/api/auth/me`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return res.json();
};

// Анализ изображения (data URL с canvas/file)
const analyzeImage = async (dataUrl) => {
  const res = await fetch(`${BASE_URL}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image: dataUrl }),
  });
  return res.json(); // { sessionId, questions }
};

// Отправка ответов
const submitAnswers = async (sessionId, answers) => {
  const res = await fetch(`${BASE_URL}/api/analyze/answers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sessionId, answers }),
  });
  return res.json(); // { result }
};
```

---

## Сводка переменных окружения

```
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=<openssl rand -hex 32>
ACCESS_TOKEN_EXPIRE_MINUTES=30
LANDMARK_WEIGHTS_PATH=/path/to/landmark_model.pth
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
DEBUG=false
APP_NAME=Diploma Backend
```

---

## CORS

CORS настроен в приложении. Источники задаются через `CORS_ORIGINS` (через запятую). Для разработки можно использовать `*` (уже учтено, если `CORS_ORIGINS` пустой).
