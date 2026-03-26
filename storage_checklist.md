# Чек-лист: Supabase Storage Integration

## 1. Конфигурация Supabase
- [ ] Бакет `screenshots` (Public: True).
- [ ] Бакет `videos` (Public: True).
- [ ] RLS Policy (Storage.objects): `INSERT` для `service_role`.
- [ ] RLS Policy (Storage.objects): `SELECT` для `anon` (public).

## 2. Переменные окружения (.env)
- [ ] `SUPABASE_URL`.
- [ ] `SUPABASE_SERVICE_ROLE_KEY`.

## 3. Модуль загрузки (Infrastructure)
- [ ] Определение бакета по расширению файла (`.png` -> `screenshots`, `.mp4` -> `videos`).
- [ ] Определение `content-type` (`image/png`, `video/mp4`).
- [ ] Генерация уникального имени файла (`scan_{id}/{timestamp}_{hash}.{ext}`).
- [ ] Использование асинхронного метода `storage.from_().upload()`.
- [ ] Получение Public URL через `storage.from_().get_public_url()`.
- [ ] Удаление локального файла после подтверждения успешной загрузки (`os.remove()`).

## 4. Интеграция в сервис (Service)
- [ ] Вызов `upload_media` в методах `_run_express_test` и `_run_deep_test`.
- [ ] Обновление поля `screenshot_url` в таблице `test_results`.
- [ ] Обновление поля `video_url` в таблице `test_results`.
- [ ] Обработка `try-except` для предотвращения блокировки теста при ошибке загрузки.
- [ ] Логирование ошибок загрузки в БД (текст ошибки вместо URL).

## 5. Безопасность и Валидация
- [ ] Проверка, что загрузка выполняется только на стороне сервера.
- [ ] Проверка, что `service_role` ключ не доступен на клиенте.
