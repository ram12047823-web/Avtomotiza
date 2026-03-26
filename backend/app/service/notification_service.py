import os
import httpx
from typing import Optional
from uuid import UUID

class NotificationService:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def send_telegram_summary(self, test_id: UUID, url: str, level: str, status: str, issues_count: int):
        """Отправляет краткое резюме отчета в Telegram."""
        if not self.bot_token or not self.chat_id:
            print("Telegram Bot Token или Chat ID не настроены. Пропускаем отправку.")
            return

        message = (
            f"🚀 <b>Завершен тест ИИ-платформы</b>\n\n"
            f"📍 <b>URL:</b> {url}\n"
            f"📊 <b>Уровень:</b> {level}\n"
            f"✅ <b>Статус:</b> {status}\n"
            f"⚠️ <b>Обнаружено ошибок:</b> {issues_count}\n\n"
            f"🔗 <i>Полный отчет доступен в личном кабинете.</i>"
        )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": message,
                        "parse_mode": "HTML"
                    }
                )
                if response.status_code != 200:
                    print(f"Ошибка при отправке в Telegram: {response.text}")
            except Exception as e:
                print(f"Не удалось отправить уведомление в Telegram: {str(e)}")

notification_service = NotificationService()
