from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from uuid import UUID
from ..domain.models import TestTask, TestLevel, TestResult, AIConfig, ScanRequest
from ..service.test_service import test_service

router = APIRouter(tags=["Testing"])

@router.get("/scans", response_model=List[TestTask])
async def list_scans():
    """Получить список всех сканирований."""
    try:
        # Получение данных из Supabase
        res = test_service.supabase.table("tests").select("*").order("created_at", descending=True).execute()
        return [TestTask(**r) for r in res.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
            url=request.url, 
            level=request.level, 
            ai_agent_id=ai_agent_id, 
            ai_configs=request.ai_configs,
            test_id=request.id
        )
        return test_task
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scans/{test_id}", response_model=TestTask)
async def get_test_status(test_id: UUID):
    """Получить статус теста."""
    try:
        res = test_service.supabase.table("tests").select("*").eq("id", str(test_id)).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Тест не найден")
        return TestTask(**res.data[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scans/{test_id}/results", response_model=List[TestResult])
async def get_test_results(test_id: UUID):
    """Получить детальные результаты теста (все страницы, ошибки, ссылки на медиа)."""
    try:
        res = test_service.supabase.table("test_results").select("*").eq("test_id", str(test_id)).execute()
        return [TestResult(**r) for r in res.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
