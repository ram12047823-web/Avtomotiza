import os
from uuid import UUID
from typing import List
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from supabase import create_client, Client
from ..domain.models import TestTask, TestResult, TestIssue

class ReportService:
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            print("Warning: Supabase credentials not found in ReportService. DB features will be disabled.")
            self.supabase = None
        else:
            try:
                self.supabase: Client = create_client(supabase_url, supabase_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Supabase client in ReportService: {e}")
                self.supabase = None
        
        self.reports_dir = "/tmp/reports"
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir, exist_ok=True)

    async def generate_pdf_report(self, test_id: UUID) -> str:
        """Собирает данные из Supabase и генерирует PDF отчет."""
        # 1. Получение данных о тесте
        test_res = self.supabase.table("tests").select("*").eq("id", str(test_id)).execute()
        if not test_res.data:
            raise Exception("Тест не найден")
        test_task = TestTask(**test_res.data[0])

        # 2. Получение результатов теста
        results_res = self.supabase.table("test_results").select("*").eq("test_id", str(test_id)).execute()
        results: List[TestResult] = [TestResult(**item) for item in results_res.data]

        # 3. Настройка PDF
        file_path = os.path.join(self.reports_dir, f"report_{test_id}.pdf")
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Заголовок
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20
        )
        elements.append(Paragraph(f"Отчет об ИИ-тестировании: {test_task.url}", title_style))
        elements.append(Paragraph(f"Уровень проверки: {test_task.level}", styles['Normal']))
        elements.append(Paragraph(f"Дата: {test_task.created_at or 'Не указана'}", styles['Normal']))
        elements.append(Spacer(1, 20))

        # Сводка
        elements.append(Paragraph("Сводка результатов", styles['Heading2']))
        total_pages = len(results)
        total_issues = sum(len(r.issues) for r in results)
        elements.append(Paragraph(f"Проверено страниц: {total_pages}", styles['Normal']))
        elements.append(Paragraph(f"Обнаружено проблем: {total_issues}", styles['Normal']))
        elements.append(Spacer(1, 20))

        # Детали по страницам
        for res in results:
            elements.append(Paragraph(f"Страница: {res.url}", styles['Heading3']))
            elements.append(Paragraph(f"Статус-код: {res.status_code}", styles['Normal']))
            
            if res.video_url:
                elements.append(Paragraph(f"Ссылка на видео: <a href='{res.video_url}' color='blue'>Смотреть запись</a>", styles['Normal']))

            if not res.issues:
                elements.append(Paragraph("Ошибок не обнаружено.", styles['Normal']))
            else:
                for issue in res.issues:
                    issue_obj = TestIssue(**issue) if isinstance(issue, dict) else issue
                    elements.append(Spacer(1, 10))
                    
                    # Таблица для ошибки
                    data = [
                        [Paragraph(f"<b>Описание:</b> {issue_obj.description}", styles['Normal'])],
                        [Paragraph(f"<b>Рекомендация:</b> {issue_obj.recommendation}", styles['Normal'])]
                    ]
                    
                    # Добавляем скриншот если есть
                    # В реальном приложении нужно скачивать изображение временно или использовать Image.from_url если поддерживается
                    if issue_obj.screenshot_url:
                        data.append([Paragraph(f"<b>Скриншот:</b> <a href='{issue_obj.screenshot_url}' color='blue'>Открыть фото</a>", styles['Normal'])])

                    t = Table(data, colWidths=[450])
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
                        ('BOX', (0, 0), (-1, -1), 1, colors.grey),
                        ('PADDING', (0, 0), (-1, -1), 10),
                    ]))
                    elements.append(t)
            
            elements.append(Spacer(1, 20))

        doc.build(elements)
        return file_path

report_service = ReportService()
