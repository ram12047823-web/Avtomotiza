import os
import json
from typing import List, Optional
from uuid import UUID
from supabase import create_client, Client
from ..domain.models import TestTask, TestResult, TestLevel, TestStatus, TestIssue, ModelType, AIRequest, AIConfig
from ..infrastructure.playwright_client import playwright_client
from ..infrastructure.storage_client import storage_client
from ..service.agent_service import agent_service

class TestService:
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL", "")
        supabase_key = os.getenv("SUPABASE_KEY", "")
        self.supabase: Client = create_client(supabase_url, supabase_key)

    async def run_test(self, url: str, level: TestLevel, ai_agent_id: Optional[UUID] = None, ai_configs: List[AIConfig] = []) -> TestTask:
        """Запуск теста в зависимости от уровня."""
        # 1. Создание записи о тесте в БД
        test_data = {
            "url": url,
            "level": level.value,
            "status": TestStatus.RUNNING.value
        }
        response = self.supabase.table("tests").insert(test_data).execute()
        test_task = TestTask(**response.data[0])

        try:
            if level == TestLevel.EXPRESS:
                await self._run_express_test(test_task, ai_agent_id, ai_configs)
            elif level == TestLevel.DEEP:
                await self._run_deep_test(test_task, ai_agent_id, ai_configs)
            
            # Обновление статуса на Completed
            self.supabase.table("tests").update({"status": TestStatus.COMPLETED.value}).eq("id", str(test_task.id)).execute()
            test_task.status = TestStatus.COMPLETED
            
        except Exception as e:
            print(f"Test failed: {e}")
            self.supabase.table("tests").update({"status": TestStatus.FAILED.value}).eq("id", str(test_task.id)).execute()
            test_task.status = TestStatus.FAILED

        return test_task

    async def _run_express_test(self, test_task: TestTask, ai_agent_id: Optional[UUID], ai_configs: List[AIConfig] = []):
        """Логика экспресс-теста."""
        info = await playwright_client.get_page_info(test_task.url)
        
        # Загрузка скриншота в Storage
        screenshot_url = await storage_client.upload_media(info['screenshot_path'], str(test_task.id))
        
        issues = []
        if ai_agent_id:
            # Получаем агента, чтобы узнать его категорию
            agent = await agent_service.get_agent(ai_agent_id)
            
            # Ищем конфиг для этой категории
            config = next((c for c in ai_configs if c.category == agent.model_type), None)

            ai_response = await agent_service.execute_agent_request(AIRequest(
                agent_id=ai_agent_id,
                prompt=f"Проанализируй сайт {test_task.url}. Статус-код: {info['status_code']}. "
                       f"Найди критические ошибки на главной странице.",
                ai_config=config
            ))
            
            # Парсинг ответа ИИ (упрощенно)
            issues.append(TestIssue(
                description=ai_response.content,
                recommendation="Следуйте советам ИИ выше.",
                screenshot_url=screenshot_url or info['screenshot_path']
            ))

        result = TestResult(
            test_id=test_task.id,
            url=test_task.url,
            status_code=info['status_code'],
            issues=issues
        )
        
        self.supabase.table("test_results").insert(result.model_dump(exclude={"id", "created_at"})).execute()

    async def _run_deep_test(self, test_task: TestTask, ai_agent_id: Optional[UUID], ai_configs: List[AIConfig] = []):
        """Логика глубокого теста с краулером."""
        results = await playwright_client.crawl_and_test(test_task.url, max_pages=5)
        
        # Получаем агента заранее, если он есть
        agent = await agent_service.get_agent(ai_agent_id) if ai_agent_id else None
        config = next((c for c in ai_configs if agent and c.category == agent.model_type), None) if agent else None

        for res in results:
            # Загрузка скриншота и видео в Storage
            screenshot_url = await storage_client.upload_media(res['screenshot_path'], str(test_task.id))
            video_url = await storage_client.upload_media(res['video_path'], str(test_task.id)) if res.get('video_path') else None

            issues = []
            if ai_agent_id:
                ai_response = await agent_service.execute_agent_request(AIRequest(
                    agent_id=ai_agent_id,
                    prompt=f"Проанализируй страницу {res['url']}. Статус-код: {res['status_code']}. "
                           f"Найди ошибки UX/UI или безопасности.",
                    ai_config=config
                ))
                
                # Если ИИ нашел ошибку (логика может быть сложнее)
                if "ошибка" in ai_response.content.lower() or "проблема" in ai_response.content.lower():
                    issues.append(TestIssue(
                        description=ai_response.content,
                        recommendation="Исправьте найденные ИИ недочеты.",
                        screenshot_url=screenshot_url or res['screenshot_path']
                    ))

            result = TestResult(
                test_id=test_task.id,
                url=res['url'],
                status_code=res['status_code'],
                issues=issues,
                video_url=video_url or res.get('video_path')
            )
            
            self.supabase.table("test_results").insert(result.model_dump(exclude={"id", "created_at"})).execute()

test_service = TestService()
