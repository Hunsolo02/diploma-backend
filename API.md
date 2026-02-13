# API Documentation (для фронтенда)

Базовый URL: `http://localhost:8000` (или хост, где запущен backend).

Интерактивная документация: **GET** `/docs` (Swagger UI).

---

## Аутентификация

Используется **JWT Bearer token**. После логина передавайте токен в заголовке:

```
Authorization: Bearer <access_token>
```

Токен выдаётся на **POST /api/auth/login**. Время жизни задаётся в настройках сервера (`ACCESS_TOKEN_EXPIRE_MINUTES`, по умолчанию 30 минут).

---

## Общие замечания

- **Content-Type** для JSON: `application/json`.
- Ответы с ошибкой: `{ "detail": "сообщение" }` или `{ "detail": [...] }` для валидации.
- Пагинация: параметры запроса `skip` (смещение) и `limit` (макс. записей), по умолчанию `skip=0`, `limit=100`.
- Даты в ответах в формате ISO 8601: `created_at`, `updated_at`.

---

## 1. Auth — `/api/auth`

### POST /api/auth/register

Регистрация нового пользователя.

**Тело запроса:**

```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "secret",
  "name": "Имя Фамилия"
}
```

| Поле       | Тип     | Обязательное | Описание        |
|-----------|---------|---------------|-----------------|
| email     | string  | да            | Валидный email  |
| username  | string  | да            | Уникальный логин|
| password  | string  | да            | Пароль          |
| name      | string  | нет           | Отображаемое имя|

**Ответ 200:** объект пользователя (см. UserResponse).

**Ошибки:** 400 — `Email already registered` или `Username already taken`.

---

### POST /api/auth/login

Вход. Возвращает JWT.

**Тело запроса:**

```json
{
  "username": "username",
  "password": "secret"
}
```

**Ответ 200:**

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Ошибки:** 401 — `Incorrect username or password`.

---

### GET /api/auth/me

Текущий пользователь. **Требуется авторизация.**

**Заголовок:** `Authorization: Bearer <token>`

**Ответ 200 (UserResponse):**

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "name": "Имя",
  "role": "user",
  "is_active": true,
  "created_at": "2025-02-12T12:00:00"
}
```

**Ошибки:** 401 — неверный или отсутствующий токен.

---

## 2. Items — `/api/items`

CRUD для сущности «элемент». **Создание (POST) требует авторизации.** Остальные эндпоинты — без авторизации.

### GET /api/items/

Список элементов. Параметры: `skip`, `limit`.

**Ответ 200:** массив `ItemResponse`:

```json
[
  {
    "id": 1,
    "title": "Заголовок",
    "description": "Описание",
    "created_at": "...",
    "updated_at": "..."
  }
]
```

---

### POST /api/items/

Создать элемент. **Требуется Authorization: Bearer.**

**Тело (ItemCreate):**

```json
{
  "title": "Заголовок",
  "description": "Описание"
}
```

**Ответ 200:** один объект ItemResponse.

---

### GET /api/items/{item_id}

Один элемент по ID.

**Ответ 200:** ItemResponse. **404** — не найден.

---

### PATCH /api/items/{item_id}

Обновить элемент. Тело — частичное (только нужные поля).

```json
{
  "title": "Новый заголовок",
  "description": "Новое описание"
}
```

**Ответ 200:** ItemResponse. **404** — не найден.

---

### DELETE /api/items/{item_id}

Удалить элемент. **Ответ 204** без тела. **404** — не найден.

---

## 3. Analyze — `/api/analyze`

Анализ лица: загрузка изображения, вопросы, ответы, результат.

### POST /api/analyze/landmarks

Детекция landmark’ов по загруженному файлу. Без авторизации.

**Запрос:** `multipart/form-data`, поле `file` — файл изображения (JPEG, PNG, WebP).

**Ответ 200:**

```json
{
  "points": [[x1, y1], [x2, y2], ...],
  "annotated_image_base64": "base64 строка PNG с нарисованными точками"
}
```

**Ошибки:** 400 — неверный тип файла или пустой файл. 422 — лицо не найдено или ошибка обработки.

---

### POST /api/analyze/landmarks/bytes

То же, но изображение передаётся **телом запроса** с `Content-Type: image/jpeg`, `image/png` или `image/webp`.

**Ответ:** как у POST /api/analyze/landmarks.

---

### POST /api/analyze

Старт сессии анализа: загрузка изображения и получение списка вопросов.

**Тело (AnalyzeRequest):**

```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

`image` — data URL (строка `data:image/<тип>;base64,<base64>`).

**Ответ 200 (AnalyzeResponse):**

```json
{
  "sessionId": "uuid-строка",
  "questions": [
    {
      "id": "skin_type",
      "label": "Тип кожи",
      "type": "select",
      "options": ["сухая", "жирная", "комбинированная", "нормальная"]
    },
    {
      "id": "notes",
      "label": "Дополнительные наблюдения",
      "type": "text",
      "options": null
    }
  ]
}
```

Типы вопроса: `text`, `select`, `number`. Для `select` в `options` — массив строк.

**Ошибки:** 400 — неверный формат data URL или изображения.

---

### POST /api/analyze/answers

Отправка ответов по сессии.

**Тело (SubmitAnswersRequest):**

```json
{
  "sessionId": "uuid-строка из POST /api/analyze",
  "answers": {
    "skin_type": "нормальная",
    "reaction": "загораю постепенно",
    "notes": "текст"
  }
}
```

`answers` — объект: ключи = id вопроса, значения = строка или число.

**Ответ 200:**

```json
{
  "result": {
    "phenotype": "...",
    "origin": "...",
    "concentration": "...",
    "recommendations": ["...", "..."],
    "summary": "...",
    "raw": { ... }
  }
}
```

**Ошибки:** 404 — сессия не найдена.

---

### GET /api/analyze/sessions/{session_id}

Получить результат сессии по `session_id` (для истории/повторного отображения).

**Ответ 200:**

```json
{
  "sessionId": "uuid",
  "result": { ... }
}
```

**Ошибки:** 404 — сессия не найдена.

---

## 4. Regions — `/api/regions`

Справочник регионов. Без авторизации.

### GET /api/regions/

Список. Параметры: `skip`, `limit`.

**Ответ 200:** массив RegionResponse:

```json
[
  {
    "id": 1,
    "view_name": "Отображаемое имя",
    "name": "Внутреннее имя",
    "created_at": "...",
    "updated_at": "..."
  }
]
```

---

### POST /api/regions/

**Тело (RegionCreate):** `{ "view_name": "...", "name": "..." }`. **Ответ 200:** один RegionResponse.

---

### GET /api/regions/{region_id}

Один регион. **Ответ 200** или **404**.

---

### PATCH /api/regions/{region_id}

Частичное обновление: `view_name`, `name` (опционально). **Ответ 200** или **404**.

---

### DELETE /api/regions/{region_id}

Удаление. **Ответ 204** или **404**.

---

## 5. Phenotypes — `/api/phenotypes`

Справочник фенотипов. Структура как у Regions.

- **GET /api/phenotypes/** — список (`skip`, `limit`).
- **POST /api/phenotypes/** — создание: `{ "view_name": "...", "name": "..." }`.
- **GET /api/phenotypes/{phenotype_id}** — один объект.
- **PATCH /api/phenotypes/{phenotype_id}** — обновление.
- **DELETE /api/phenotypes/{phenotype_id}** — удаление.

Формат объекта (PhenotypeResponse): `id`, `view_name`, `name`, `created_at`, `updated_at`.

---

## 6. Face features — `/api/face-features`

Справочник признаков лица. Структура как у Regions/Phenotypes.

- **GET /api/face-features/** — список (`skip`, `limit`).
- **POST /api/face-features/** — создание: `{ "view_name": "...", "name": "..." }`.
- **GET /api/face-features/{face_feature_id}** — один объект.
- **PATCH /api/face-features/{face_feature_id}** — обновление.
- **DELETE /api/face-features/{face_feature_id}** — удаление.

Формат объекта (FaceFeatureResponse): `id`, `view_name`, `name`, `created_at`, `updated_at`.

---

## 7. User profiles — `/api/user-profiles`

Профили пользователей (регион, фенотип, изображения, связь с face features).

### GET /api/user-profiles/

Список. Параметры: `skip`, `limit`.

**Ответ 200:** массив UserProfileResponse (см. ниже).

---

### POST /api/user-profiles/

Создание профиля.

**Тело (UserProfileCreate):**

```json
{
  "region_id": 1,
  "phenotype_analyze": { "key": "value" },
  "original_image_base64": "base64 строка или null",
  "analyzed_image_base64": "base64 строка или null",
  "face_feature_ids": [1, 2, 3]
}
```

**Ответ 200:** UserProfileResponse.

---

### GET /api/user-profiles/{profile_id}

Один профиль. **Ответ 200** или **404**.

---

### PATCH /api/user-profiles/{profile_id}

Частичное обновление. Поля как в UserProfileCreate (все опциональны). Для сброса связей с face features можно передать `face_feature_ids: []`.

**Ответ 200** или **404**.

---

### DELETE /api/user-profiles/{profile_id}

Удаление. **Ответ 204** или **404**.

---

**UserProfileResponse:**

```json
{
  "id": 1,
  "region_id": 1,
  "phenotype_analyze": {},
  "original_image_base64": "base64 или null",
  "analyzed_image_base64": "base64 или null",
  "create_time": 1707721200,
  "update_time": 1707721200,
  "face_features": [
    { "id": 1, "view_name": "...", "name": "..." }
  ]
}
```

`create_time` / `update_time` — Unix timestamp (секунды).

---

## Коды ответов (сводка)

| Код | Значение        |
|-----|-----------------|
| 200 | OK, тело по контракту |
| 204 | Успех без тела (DELETE) |
| 400 | Неверный запрос (тело, тип файла и т.д.) |
| 401 | Не авторизован (нет/неверный Bearer) |
| 404 | Ресурс не найден |
| 422 | Ошибка обработки (например, лицо не обнаружено) |

---

## CORS

Сервер по умолчанию разрешает запросы с origins из настроек (`CORS_ORIGINS`), например `http://localhost:3000`, `http://localhost:5173`. Для запросов с учётными данными (cookies/Authorization) фронт должен отправлять `credentials: 'include'` при необходимости и использовать указанный origin.
