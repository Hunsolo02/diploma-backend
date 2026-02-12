# Модели/таблицы и связанные файлы фронтенда

Обзор структур данных проекта и файлов, в которых они определены или используются.

---

## 1. Модели БД (Prisma)

### User

| Поле          | Тип      | Описание                    |
|---------------|----------|-----------------------------|
| id            | String   | CUID, первичный ключ        |
| email         | String   | Уникальный                  |
| name          | String?  | Необязательное имя          |
| passwordHash  | String   | Хэш пароля                  |
| role          | String   | По умолчанию "user"         |
| isActive      | Boolean  | По умолчанию true           |
| createdAt     | DateTime | Время создания              |
| updatedAt     | DateTime | Время обновления            |

**Файлы:**
- `prisma/schema.prisma` — определение модели

---

## 2. Модели/типы на фронтенде

### User (клиентский, авторизация)

Используется в контексте авторизации (localStorage). Не совпадает с полной моделью Prisma.

| Поле  | Тип     |
|-------|---------|
| email | string  |
| name  | string? |

**Файлы:**
- `lib/auth-context.tsx` — определение типа, хранение, signIn/signOut/updateUser
- `app/auth/page.tsx` — форма входа, signIn(email, password)
- `app/auth/signup/page.tsx` — форма регистрации, signIn(email, password, name)
- `app/dashboard/page.tsx` — отображение user.email, передача email в addAnalysisEntry
- `app/profile/page.tsx` — отображение и редактирование email/name
- `app/page.tsx` — проверка isAuthenticated

---

### AnalysisQuestion

Вопрос дополнительной анкеты при анализе.

| Поле    | Тип                    |
|---------|------------------------|
| id      | string                 |
| label   | string                 |
| type    | "text" \| "select" \| "number" |
| options | string[]? (для select) |

**Файлы:**
- `lib/api.ts` — определение типа, использование в AnalyzeResponse
- `app/dashboard/page.tsx` — рендер вопросов (select, number, textarea), ответы
- `app/api/analyze/route.ts` — формирование массива questions в ответе

---

### AnalyzeResponse

Ответ API анализа изображения.

| Поле       | Тип                |
|------------|--------------------|
| sessionId  | string             |
| questions  | AnalysisQuestion[] |

**Файлы:**
- `lib/api.ts` — определение типа, возврат из analyzeImage()
- `app/dashboard/page.tsx` — приём data.sessionId, data.questions после analyzeImage()

---

### SubmitAnswersResponse

Ответ API отправки ответов на вопросы.

| Поле   | Тип                              |
|--------|----------------------------------|
| result | Record<string, unknown> \| string |

**Файлы:**
- `lib/api.ts` — определение типа, возврат из submitAnswers()
- `app/dashboard/page.tsx` — приём data.result, отображение (phenotype, origin, concentration, recommendations, summary)
- `app/api/analyze/answers/route.ts` — формирование result в ответе

---

### Результат анализа (формат result)

Используемая на фронте форма объекта результата (когда result — объект):

| Поле            | Тип           | Описание                    |
|-----------------|---------------|-----------------------------|
| phenotype       | string?       | Фенотип                     |
| origin          | string?       | Происхождение               |
| concentration   | string?       | Наибольшая концентрация     |
| recommendations | string[]?     | Рекомендации                |
| summary         | string?       | Итог                        |
| raw             | unknown?      | Сырые ответы (в моке API)   |

**Файлы:**
- `app/dashboard/page.tsx` — отображение результата (phenotype, origin, concentration, recommendations, summary)
- `app/profile/page.tsx` — отображение в истории проверок (те же поля)
- `app/api/analyze/answers/route.ts` — пример объекта result (phenotype, origin, concentration, raw)

---

### HistoryEntry

Одна запись в истории проверок (localStorage).

| Поле      | Тип                              |
|-----------|----------------------------------|
| id        | string (sessionId)               |
| createdAt | string (ISO дата)                |
| result    | Record<string, unknown> \| string |

**Файлы:**
- `lib/analysis-history.ts` — определение типа, getAnalysisHistory(), addAnalysisEntry(), formatHistoryDate()
- `app/dashboard/page.tsx` — вызов addAnalysisEntry() после успешной отправки ответов
- `app/profile/page.tsx` — getAnalysisHistory(), отображение списка и деталей

---

## 3. API-маршруты (request/response)

### POST /api/analyze

**Тело запроса:** `{ image: string }` (data URL изображения)

**Ответ:** `{ sessionId: string, questions: AnalysisQuestion[] }` или `{ error: string }`

**Файлы:**
- `app/api/analyze/route.ts` — обработчик
- `lib/api.ts` — вызов (analyzeImage)

---

### POST /api/analyze/answers

**Тело запроса:** `{ sessionId: string, answers: Record<string, string | number> }`

**Ответ:** `{ result: Record<string, unknown> | string }` или `{ error: string }`

**Файлы:**
- `app/api/analyze/answers/route.ts` — обработчик
- `lib/api.ts` — вызов (submitAnswers)

---

## 4. Сводная таблица файлов по назначению

| Файл | Назначение |
|------|------------|
| `prisma/schema.prisma` | Модель User (БД) |
| `lib/auth-context.tsx` | Тип User, контекст авторизации, updateUser |
| `lib/api.ts` | AnalysisQuestion, AnalyzeResponse, SubmitAnswersResponse, клиент analyze/submitAnswers |
| `lib/analysis-history.ts` | HistoryEntry, работа с историей в localStorage |
| `lib/utils.ts` | validateEmail, cn (без моделей) |
| `app/api/analyze/route.ts` | API: приём image, возврат sessionId + questions |
| `app/api/analyze/answers/route.ts` | API: приём sessionId + answers, возврат result |
| `app/auth/page.tsx` | Вход, использование User/signIn |
| `app/auth/signup/page.tsx` | Регистрация, использование User/signIn |
| `app/dashboard/page.tsx` | Анализ фенотипа: вопросы, ответы, результат, сохранение в историю |
| `app/profile/page.tsx` | Личный кабинет: User, история проверок (HistoryEntry, result) |
| `app/page.tsx` | Главная, проверка isAuthenticated |

---

## 5. Список файлов, необходимых для фронтенда (по моделям)

Файлы, в которых определены или активно используются перечисленные модели/типы:

- `prisma/schema.prisma`
- `lib/auth-context.tsx`
- `lib/api.ts`
- `lib/analysis-history.ts`
- `app/api/analyze/route.ts`
- `app/api/analyze/answers/route.ts`
- `app/auth/page.tsx`
- `app/auth/signup/page.tsx`
- `app/dashboard/page.tsx`
- `app/profile/page.tsx`
- `app/page.tsx`
- `lib/utils.ts` (вспомогательный: валидация email для форм)

Компоненты UI (`components/ui/*`) и `app/layout.tsx` в этом списке не перечислены — они не определяют доменных моделей, а используются страницами выше.
