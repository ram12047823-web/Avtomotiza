from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from uuid import UUID
from ..domain.models import TestTask, TestLevel, TestResult, AIConfig, ScanRequest
from ..service.test_service import test_service

router = APIRouter(prefix="/tests", tags=["Testing"])

@router.post("/run-scan", response_model=TestTask)
async def run_test(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    ai_agent_id: Optional[UUID] = None
):
    """
    Запустить новый тест для указанного URL.
    - Экспресс: Статус-коды + скриншот главной.
    - Глубокий: Полный crawler + видео.
    - ScanRequest: Содержит URL, уровень, список ai_configs и опциональный api_key.
    """
    try:
        # Запуск теста в фоне, чтобы не блокировать API
        test_task = await test_service.run_test(
            request.url, 
            request.level, 
            ai_agent_id, 
            request.ai_configs
        )
        return test_task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{test_id}", response_model=TestTask)
async def get_test_status(test_id: UUID):
    """Получить статус теста."""
    # Реализация через сервис получения статуса
    pass

@router.get("/{test_id}/results", response_model=List[TestResult])
async def get_test_results(test_id: UUID):
    """Получить детальные результаты теста (все страницы, ошибки, ссылки на медиа)."""
    # Реализация через сервис получения результатов
    pass
