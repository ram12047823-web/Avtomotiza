from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List, Optional
from uuid import UUID
from ..service.report_service import report_service
from ..service.notification_service import notification_service
from ..domain.models import TestTask
import os

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/{test_id}/pdf")
async def download_report_pdf(test_id: UUID):
    """Генерирует и скачивает PDF отчет для теста."""
    try:
        file_path = await report_service.generate_pdf_report(test_id)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Отчет не найден")
        
        return FileResponse(
            path=file_path,
            filename=f"report_{test_id}.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{test_id}/notify-telegram")
async def notify_telegram(test_id: UUID, background_tasks: BackgroundTasks):
    """Отправить уведомление о завершенном тесте в Telegram."""
    try:
        # 1. Получение данных о тесте из БД (в реальном приложении — через сервис)
        test_res = report_service.supabase.table("tests").select("*").eq("id", str(test_id)).execute()
        if not test_res.data:
            raise HTTPException(status_code=404, detail="Тест не найден")
        
        test_task = TestTask(**test_res.data[0])
        
        # 2. Получение количества ошибок
        results_res = report_service.supabase.table("test_results").select("issues").eq("test_id", str(test_id)).execute()
        issues_count = sum(len(r['issues']) for r in results_res.data)

        # 3. Отправка в Telegram через фоновую задачу
        background_tasks.add_task(
            notification_service.send_telegram_summary,
            test_id=test_id,
            url=test_task.url,
            level=test_task.level,
            status=test_task.status,
            issues_count=issues_count
        )
        
        return {"message": "Уведомление в Telegram запланировано на отправку."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
