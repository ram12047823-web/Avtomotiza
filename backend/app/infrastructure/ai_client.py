import litellm
from typing import List, Dict, Any, Optional
from ..domain.models import ModelType, AIResponse

class AIClient:
    def __init__(self):
        # Предопределенные системные промпты по специализациям
        self.system_prompts = {
            ModelType.UX: (
                "Вы — эксперт по UX/UI и пользовательскому опыту. "
                "Ваша задача — анализировать веб-страницы на предмет удобства, "
                "интуитивности и визуальной иерархии. Найдите ошибки в интерфейсе "
                "и предложите улучшения."
            ),
            ModelType.SECURITY: (
                "Вы — специалист по кибербезопасности. "
                "Анализируйте веб-сайт на предмет уязвимостей (XSS, SQL Injection, "
                "небезопасные заголовки, открытые данные). Ваша цель — найти потенциальные дыры в защите."
            ),
            ModelType.PERFORMANCE: (
                "Вы — инженер по производительности. "
                "Ваша задача — анализировать скорость загрузки, размер ресурсов "
                "и эффективность рендеринга. Дайте рекомендации по оптимизации Core Web Vitals."
            ),
            ModelType.ACCESSIBILITY: (
                "Вы — эксперт по доступности (WCAG). "
                "Проверьте, насколько сайт удобен для людей с ограниченными возможностями "
                "(контрастность, теги alt, навигация с клавиатуры, ARIA-атрибуты)."
            ),
            ModelType.GENERAL: "Вы — универсальный ИИ-помощник для тестирования веб-сайтов."
        }

    async def complete(
        self, 
        model_name: str, 
        base_url: str, 
        api_key: Optional[str], 
        model_type: ModelType, 
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AIResponse:
        """
        Выполняет запрос к ИИ с динамическим base_url и системным промптом.
        """
        system_prompt = self.system_prompts.get(model_type, self.system_prompts[ModelType.GENERAL])
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            # LiteLLM позволяет динамически задавать base_url и api_key для каждого вызова
            response = await litellm.acompletion(
                model=model_name,
                messages=messages,
                api_base=base_url,
                api_key=api_key or "no-key", # LiteLLM требует ключ, даже если он не нужен модели
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return AIResponse(
                content=response.choices[0].message.content,
                usage=response.get("usage", {}),
                model=model_name
            )
        except Exception as e:
            # В реальном приложении здесь должна быть более детальная обработка ошибок
            raise Exception(f"Ошибка при вызове ИИ модели: {str(e)}")

ai_client = AIClient()
