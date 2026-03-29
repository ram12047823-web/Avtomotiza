# Чек-лист реализации (Checklist.md)

## 1. Конфигурация
- [ ] Настройка переменных окружения (`.env`):
    - [ ] `SUPABASE_URL`, `SUPABASE_KEY`.
    - [ ] `LITELLM_API_KEY`, `LITELLM_BASE_URL`.
    - [ ] `TELEGRAM_BOT_TOKEN`, `EMAIL_PASS`.

## 2. Модуль Playwright
- [x] Функция `take_screenshot(url, element_selector)`.
- [x] Функция `record_video(url, duration)`.
- [x] Логика обхода ссылок (`get_links(url, depth)`).

## 3. Модуль LiteLLM (ИИ)
- [x] Адаптер для вызова моделей.
- [x] Промпты для анализа UI (напр., "Найди ошибки контрастности").
- [x] Парсинг ответов ИИ в структурированный JSON.

## 4. Модуль PDF
- [x] Шаблон отчета (Логотип, Дата, URL).
- [x] Секция "Обнаруженные ошибки" с вложенными фото.
- [x] Секция "Технические метрики".

## 5. Бэкенд API (FastAPI)
- [x] POST `/tests/start`: Запуск асинхронной задачи (BackgroundTasks).
- [x] GET `/tests/{id}`: Получение текущего статуса и логов.
- [x] GET `/tests/history`: Список всех тестов пользователя.
- [x] POST `/ai-models/add`: Добавление новой модели.

## 6. Фронтенд (React)
- [ ] Компонент `URLInput`.
- [ ] Компонент `LevelSelector` (Экспресс/Стандарт/Глубокий).
- [ ] Визуализация процесса теста (ProgressBar/Logs).
- [ ] Компонент просмотра медиа (скриншоты/видео).

## 7. Уведомления
- [x] Интеграция с Telegram API.
- [ ] Настройка SMTP для Email.
