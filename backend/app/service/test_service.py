import os
import sys
import json
import asyncio
from typing import List, Optional
from uuid import UUID
from supabase import create_client, Client
from ..domain.models import TestTask, TestResult, TestLevel, TestStatus, TestIssue, ModelType, AIRequest, AIConfig
from ..infrastructure.playwright_client import playwright_client
from ..infrastructure.storage_client import storage_client
from ..service.agent_service import agent_service
from ..infrastructure.supabase_client import get_supabase

class TestService:
    def __init__(self):
        self.supabase = get_supabase()

    async def run_test(self, url: str, level: TestLevel, ai_agent_id: Optional[UUID] = None, ai_configs: List[AIConfig] = [], test_id: Optional[UUID] = None) -> TestTask:
        """Запуск теста в зависимости от уровня."""
        print(f"WORKER: Starting test for {url} (ID: {test_id})", flush=True)
        
        # Задержка для инициализации системы
        await asyncio.sleep(1)
        
        try:
            # 1. Если ID уже есть (создан фронтендом), просто обновляем статус
            test_task = None
            if self.supabase and test_id:
                try:
                    print(f"WORKER: Updating status to RUNNING for test {test_id}", flush=True)
                    # Обновляем статус на Running для существующей записи
                    update_res = self.supabase.table("tests").update({"status": TestStatus.RUNNING.value}).eq("id", str(test_id)).execute()
                    if update_res.data:
                        test_task = TestTask(**update_res.data[0])
                    else:
                        print(f"WORKER: Warning: Test with ID {test_id} not found for update.", flush=True)
                except Exception as e:
                    print(f"WORKER: Error updating existing test in DB: {e}", flush=True)

            # 2. Если записи еще нет и ID не был передан, создаем новую
            if not test_task and self.supabase and not test_id:
                print(f"WORKER: Creating new test record for {url}", flush=True)
                test_data = {
                    "url": url,
                    "level": level.value,
                    "status": TestStatus.RUNNING.value
                }
                try:
                    response = self.supabase.table("tests").insert(test_data).execute()
                    if response.data:
                        test_task = TestTask(**response.data[0])
                except Exception as e:
                    print(f"WORKER: Error saving new test to DB: {e}", flush=True)

            if not self.supabase:
                print("WORKER: ABORTING: No DB connection. Check SUPABASE_URL and KEY.", flush=True)
                return TestTask(id=test_id or UUID(int=0), url=url, level=level, status=TestStatus.FAILED)

            if not test_task:
                print("WORKER: ABORTING: No test record found in DB.", flush=True)
                return TestTask(id=test_id or UUID(int=0), url=url, level=level, status=TestStatus.FAILED)

            # ВЫПОЛНЕНИЕ ТЕСТА
            try:
                if level == TestLevel.EXPRESS:
                    print(f"WORKER: Running EXPRESS test for {url}", flush=True)
                    await self._run_express_test(test_task, ai_agent_id, ai_configs)
                elif level == TestLevel.DEEP:
                    print(f"WORKER: Running DEEP test for {url}", flush=True)
                    await self._run_deep_test(test_task, ai_agent_id, ai_configs)
                
                # Обновление статуса на Completed
                if self.supabase and test_task.id != UUID(int=0):
                    print(f"WORKER: Test {test_task.id} COMPLETED. Updating DB...", flush=True)
                    self.supabase.table("tests").update({"status": TestStatus.COMPLETED.value}).eq("id", str(test_task.id)).execute()
                test_task.status = TestStatus.COMPLETED
                
            except Exception as e:
                print(f"WORKER: ERROR during test execution: {e}", flush=True)
                if self.supabase and test_task.id != UUID(int=0):
                    print(f"WORKER: Marking test {test_task.id} as FAILED in DB", flush=True)
                    try:
                        self.supabase.table("tests").update({"status": TestStatus.FAILED.value}).eq("id", str(test_task.id)).execute()
                    except Exception as db_err:
                        print(f"WORKER: Could not update status to FAILED: {db_err}", flush=True)
                test_task.status = TestStatus.FAILED
                raise e # Пробрасываем выше для общего обработчика

            return test_task

        except Exception as global_err:
            print(f"WORKER: CRITICAL GLOBAL ERROR: {global_err}", flush=True)
            # Если мы тут, значит всё совсем плохо, но мы пытаемся еще раз пометить как failed если есть ID
            if test_id and self.supabase:
                try:
                    self.supabase.table("tests").update({"status": TestStatus.FAILED.value}).eq("id", str(test_id)).execute()
                except: pass
            return TestTask(id=test_id or UUID(int=0), url=url, level=level, status=TestStatus.FAILED)

    async def _check_cancellation(self, test_id: UUID):
        """Проверяет, не был ли тест отменен пользователем."""
        if not self.supabase or test_id == UUID(int=0):
            return

        try:
            res = self.supabase.table("tests").select("status").eq("id", str(test_id)).execute()
            if res.data and res.data[0]['status'] == TestStatus.CANCELLED.value:
                print(f"WORKER: Test {test_id} was CANCELLED by user. Stopping...", flush=True)
                raise Exception("Test was cancelled by user")
        except Exception as e:
            if "cancelled" in str(e).lower():
                raise e
            print(f"WORKER: Error checking cancellation status: {e}", flush=True)

    async def _run_express_test(self, test_task: TestTask, ai_agent_id: Optional[UUID], ai_configs: List[AIConfig] = []):
        """Логика экспресс-теста."""
        await self._check_cancellation(test_task.id)
        
        print(f"WORKER: Navigating to {test_task.url}...", flush=True)
        info = await playwright_client.get_page_info(test_task.url)
        
        await self._check_cancellation(test_task.id)
        
        # Загрузка скриншота в Storage (если клиент инициализирован)
        screenshot_url = None
        if storage_client.supabase:
            print(f"WORKER: Uploading screenshot for {test_task.url} to Supabase...", flush=True)
            screenshot_url = await storage_client.upload_media(info['screenshot_path'], str(test_task.id))
        
        issues = []
        # Если предоставлены конфиги, используем их
        if ai_configs:
            for config in ai_configs:
                try:
                    print(f"WORKER: Requesting AI analysis ({config.category}) for {test_task.url}...", flush=True)
                    # Создаем фиктивный запрос для автономного выполнения
                    ai_response = await agent_service.execute_agent_request(AIRequest(
                        agent_id=UUID(int=0), # Не используется в автономном режиме
                        prompt=f"Проанализируй сайт {test_task.url}. Статус-код: {info['status_code']}. "
                               f"Найди критические ошибки на главной странице.",
                        ai_config=config,
                        image_url=screenshot_url or info['screenshot_path'],
                        page_source=info['page_source']
                    ))
                    
                    issues.append(TestIssue(
                        description=ai_response.content,
                        recommendation=f"Рекомендации от ИИ ({config.category}): Следуйте советам выше.",
                        screenshot_url=screenshot_url or info['screenshot_path'],
                        coordinates=ai_response.coordinates
                    ))
                except Exception as e:
                    print(f"WORKER: Error executing autonomous AI request for {config.category}: {e}", flush=True)

        # Если конфигов нет, но есть agent_id и база доступна, используем старую логику
        elif ai_agent_id and self.supabase:
            try:
                print(f"WORKER: Using agent {ai_agent_id} for analysis...", flush=True)
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
                print(f"WORKER: Error executing DB-based AI request: {e}", flush=True)

        result = TestResult(
            test_id=test_task.id,
            url=test_task.url,
            status_code=info['status_code'],
            issues=issues
        )
        
        if self.supabase:
            try:
                print(f"WORKER: Saving express test results to DB...", flush=True)
                self.supabase.table("test_results").insert(result.model_dump(exclude={"id", "created_at"})).execute()
            except Exception as e:
                print(f"WORKER: Error saving result to DB: {e}", flush=True)

    async def _run_deep_test(self, test_task: TestTask, ai_agent_id: Optional[UUID], ai_configs: List[AIConfig] = []):
        """Логика глубокого теста с краулером."""
        await self._check_cancellation(test_task.id)
        
        print(f"WORKER: Starting crawler for {test_task.url}...", flush=True)
        results = await playwright_client.crawl_and_test(test_task.url, max_pages=5)
        
        for res in results:
            await self._check_cancellation(test_task.id)
            
            # Загрузка скриншота и видео в Storage (если клиент инициализирован)
            screenshot_url = None
            video_url = None
            if storage_client.supabase:
                print(f"WORKER: Uploading media for {res['url']}...", flush=True)
                screenshot_url = await storage_client.upload_media(res['screenshot_path'], str(test_task.id))
                video_url = await storage_client.upload_media(res['video_path'], str(test_task.id)) if res.get('video_path') else None

            await self._check_cancellation(test_task.id)
            issues = []
            # Если предоставлены конфиги, используем их для анализа каждой страницы
            if ai_configs:
                for config in ai_configs:
                    try:
                        print(f"WORKER: Requesting AI analysis ({config.category}) for page {res['url']}...", flush=True)
                        ai_response = await agent_service.execute_agent_request(AIRequest(
                            agent_id=UUID(int=0),
                            prompt=f"Проанализируй страницу {res['url']}. Статус-код: {res['status_code']}. "
                                   f"Найди ошибки UX/UI или безопасности.",
                            ai_config=config,
                            image_url=screenshot_url or res['screenshot_path'],
                            page_source=res['page_source']
                        ))
                        
                        if "ошибка" in ai_response.content.lower() or "проблема" in ai_response.content.lower():
                            issues.append(TestIssue(
                                description=ai_response.content,
                                recommendation=f"Исправьте найденные ИИ ({config.category}) недочеты.",
                                screenshot_url=screenshot_url or res['screenshot_path'],
                                coordinates=ai_response.coordinates
                            ))
                    except Exception as e:
                        print(f"WORKER: Error executing autonomous deep AI request for {config.category}: {e}", flush=True)

            # Если конфигов нет, но есть agent_id и база доступна
            elif ai_agent_id and self.supabase:
                try:
                    print(f"WORKER: Using agent {ai_agent_id} for deep analysis of {res['url']}...", flush=True)
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
                    print(f"WORKER: Error executing DB-based deep AI request: {e}", flush=True)

            result = TestResult(
                test_id=test_task.id,
                url=res['url'],
                status_code=res['status_code'],
                issues=issues,
                video_url=video_url or res.get('video_path')
            )
            
            if self.supabase:
                try:
                    print(f"WORKER: Saving page result for {res['url']} to DB...", flush=True)
                    self.supabase.table("test_results").insert(result.model_dump(exclude={"id", "created_at"})).execute()
                except Exception as e:
                    print(f"WORKER: Error saving deep test result to DB: {e}", flush=True)

test_service = TestService()
