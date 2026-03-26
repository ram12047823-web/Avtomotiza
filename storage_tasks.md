# План задач: Supabase Storage Integration

## Этап 1: Supabase Configuration
- [ ] Создать бакеты в панели Supabase:
    - [ ] `screenshots` (public).
    - [ ] `videos` (public).
- [ ] Настроить Storage RLS Policies:
    - [ ] `INSERT` и `SELECT` для `service_role`.
    - [ ] `SELECT` для анонимных пользователей (public).

## Этап 2: Инфраструктурный слой (Python)
- [ ] Добавить `SUPABASE_SERVICE_ROLE_KEY` в `.env`.
- [ ] Реализовать `StorageClient` в `app/infrastructure/storage_client.py`:
    - [ ] Инициализация асинхронного клиента Supabase.
    - [ ] Функция `upload_media(local_path, scan_id, file_type)`:
        - [ ] Определение бакета (png -> screenshots, mp4 -> videos).
        - [ ] Генерация имени файла по шаблону.
        - [ ] Загрузка и получение Public URL.
        - [ ] Удаление локального файла после загрузки.

## Этап 3: Сервисный слой (Integration)
- [ ] Обновить `TestService` в `app/service/test_service.py`:
    - [ ] Добавить вызов `StorageClient.upload_media` после создания скриншотов/видео.
    - [ ] Сохранять полученный Public URL в базу данных (`test_results`).
- [ ] Реализовать обработку ошибок загрузки (логирование в БД без блокировки).

## Этап 4: Тестирование
- [ ] Проверить загрузку PNG-файлов.
- [ ] Проверить загрузку MP4-файлов.
- [ ] Убедиться в автоматическом удалении локальных файлов.
