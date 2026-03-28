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
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY", "")
        
        if not supabase_url or not supabase_key:
            print("Warning: Supabase credentials not found in TestService. DB operations will be skipped.")
            self.supabase = None
        else:
            try:
                self.supabase: Client = create_client(supabase_url, supabase_key)
            except Exception as e:
                print(f"Error initializing Supabase client in TestService: {e}")
                self.supabase = None

    async def run_test(self, url: str, level: TestLevel, ai_agent_id: Optional[UUID] = None, ai_configs: List[AIConfig] = []) -> TestTask:
        """Запуск теста в зависимости от уровня."""
        # 1. Создание записи о тесте в БД (опционально)
        test_data = {
            "url": url,
            "level": level.value,
            "status": TestStatus.RUNNING.value
        }
        
        test_task = None
        if self.supabase:
            try:
                response = self.supabase.table("tests").insert(test_data).execute()
                if response.data:
                    test_task = TestTask(**response.data[0])
            except Exception as e:
                print(f"Error saving test to DB: {e}")

        if not test_task:
            # Создаем временный объект если БД недоступна
            test_task = TestTask(id=UUID(int=0), url=url, level=level, status=TestStatus.RUNNING)

        try:
            if level == TestLevel.EXPRESS:
                await self._run_express_test(test_task, ai_agent_id, ai_configs)
            elif level == TestLevel.DEEP:
                await self._run_deep_test(test_task, ai_agent_id, ai_configs)
            
            # Обновление статуса на Completed
            if self.supabase and test_task.id != UUID(int=0):
                self.supabase.table("tests").update({"status": TestStatus.COMPLETED.value}).eq("id", str(test_task.id)).execute()
            test_task.status = TestStatus.COMPLETED
            
        except Exception as e:
            print(f"Test failed: {e}")
            if self.supabase and test_task.id != UUID(int=0):
                self.supabase.table("tests").update({"status": TestStatus.FAILED.value}).eq("id", str(test_task.id)).execute()
            test_task.status = TestStatus.FAILED

        return test_task

    async def _run_express_test(self, test_task: TestTask, ai_agent_id: Optional[UUID], ai_configs: List[AIConfig] = []):
        """Логика экспресс-теста."""
        info = await playwright_client.get_page_info(test_task.url)
        
        # Загрузка скриншота в Storage (если клиент инициализирован)
        screenshot_url = None
        if storage_client.supabase:
            screenshot_url = await storage_client.upload_media(info['screenshot_path'], str(test_task.id))
        
        issues = []
        # Если предоставлены конфиги, используем их
        if ai_configs:
            for config in ai_configs:
                try:
                    # Создаем фиктивный запрос для автономного выполнения
                    ai_response = await agent_service.execute_agent_request(AIRequest(
                        agent_id=UUID(int=0), # Не используется в автономном режиме
                        prompt=f"Проанализируй сайт {test_task.url}. Статус-код: {info['status_code']}. "
                               f"Найди критические ошибки на главной странице.",
                        ai_config=config
                    ))
                    
                    issues.append(TestIssue(
                        description=ai_response.content,
                        recommendation=f"Рекомендации от ИИ ({config.category}): Следуйте советам выше.",
                        screenshot_url=screenshot_url or info['screenshot_path']
                    ))
                except Exception as e:
                    print(f"Error executing autonomous AI request for {config.category}: {e}")

        # Если конфигов нет, но есть agent_id и база доступна, используем старую логику
        elif ai_agent_id and self.supabase:
            try:
                agent = await agent_service.get_agent(ai_agent_id)
                ai_response = await agent_service.execute_agent_request(AIRequest(
                    agent_id=ai_agent_id,
                    prompt=f"Проанализируй сайт {test_task.url}. Статус-код: {info['status_code']}. "
                           f"Найди критические ошибки на главной странице."
                ))
                
                issues.append(TestIssue(
                    description=ai_response.content,
                    recommendation="Следуйте советам ИИ выше.",
                    screenshot_url=screenshot_url or info['screenshot_path']
                ))
            except Exception as e:
                print(f"Error executing DB-based AI request: {e}")

        result = TestResult(
            test_id=test_task.id,
            url=test_task.url,
            status_code=info['status_code'],
            issues=issues
        )
        
        if self.supabase:
            try:
                self.supabase.table("test_results").insert(result.model_dump(exclude={"id", "created_at"})).execute()
            except Exception as e:
                print(f"Error saving result to DB: {e}")

    async def _run_deep_test(self, test_task: TestTask, ai_agent_id: Optional[UUID], ai_configs: List[AIConfig] = []):
        """Логика глубокого теста с краулером."""
        results = await playwright_client.crawl_and_test(test_task.url, max_pages=5)
        
        for res in results:
            # Загрузка скриншота и видео в Storage (если клиент инициализирован)
            screenshot_url = None
            video_url = None
            if storage_client.supabase:
                screenshot_url = await storage_client.upload_media(res['screenshot_path'], str(test_task.id))
                video_url = await storage_client.upload_media(res['video_path'], str(test_task.id)) if res.get('video_path') else None

            issues = []
            # Если предоставлены конфиги, используем их для анализа каждой страницы
            if ai_configs:
                for config in ai_configs:
                    try:
                        ai_response = await agent_service.execute_agent_request(AIRequest(
                            agent_id=UUID(int=0),
                            prompt=f"Проанализируй страницу {res['url']}. Статус-код: {res['status_code']}. "
                                   f"Найди ошибки UX/UI или безопасности.",
                            ai_config=config
                        ))
                        
                        if "ошибка" in ai_response.content.lower() or "проблема" in ai_response.content.lower():
                            issues.append(TestIssue(
                                description=ai_response.content,
                                recommendation=f"Исправьте найденные ИИ ({config.category}) недочеты.",
                                screenshot_url=screenshot_url or res['screenshot_path']
                            ))
                    except Exception as e:
                        print(f"Error executing autonomous deep AI request for {config.category}: {e}")

            # Если конфигов нет, но есть agent_id и база доступна
            elif ai_agent_id and self.supabase:
                try:
                    ai_response = await agent_service.execute_agent_request(AIRequest(
                        agent_id=ai_agent_id,
                        prompt=f"Проанализируй страницу {res['url']}. Статус-код: {res['status_code']}. "
                               f"Найди ошибки UX/UI или безопасности."
                    ))
                    
                    if "ошибка" in ai_response.content.lower() or "проблема" in ai_response.content.lower():
                        issues.append(TestIssue(
                            description=ai_response.content,
                            recommendation="Исправьте найденные ИИ недочеты.",
                            screenshot_url=screenshot_url or res['screenshot_path']
                        ))
                except Exception as e:
                    print(f"Error executing DB-based deep AI request: {e}")

            result = TestResult(
                test_id=test_task.id,
                url=res['url'],
                status_code=res['status_code'],
                issues=issues,
                video_url=video_url or res.get('video_path')
            )
            
            if self.supabase:
                try:
                    self.supabase.table("test_results").insert(result.model_dump(exclude={"id", "created_at"})).execute()
                except Exception as e:
                    print(f"Error saving deep test result to DB: {e}")

test_service = TestService()
