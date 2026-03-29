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
        image_url: Optional[str] = None,
        page_source: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AIResponse:
        """
        Выполняет запрос к ИИ с динамическим base_url и системным промптом.
        Поддерживает Vision API и передачу кода страницы.
        """
        system_prompt = self.system_prompts.get(model_type, self.system_prompts[ModelType.GENERAL])
        
        # Улучшенный промпт для получения координат багов
        enhanced_prompt = (
            f"{user_prompt}\n\n"
            "ВАЖНО: Если вы обнаружили визуальный баг, обязательно укажите его координаты "
            "в формате JSON в конце вашего ответа: [COORDINATES]{\"x\": 0, \"y\": 0, \"width\": 0, \"height\": 0}[/COORDINATES]. "
            "Используйте проценты от ширины и высоты экрана (0-100)."
        )

        if page_source:
            enhanced_prompt += f"\n\nКод страницы для анализа:\n{page_source[:5000]}" # Ограничение для контекста

        content = [{"type": "text", "text": enhanced_prompt}]
        
        if image_url:
            content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]

        try:
            # LiteLLM позволяет динамически задавать base_url и api_key для каждого вызова
            response = await litellm.acompletion(
                model=model_name,
                messages=messages,
                api_base=base_url,
                api_key=api_key or "no-key",
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            raw_content = response.choices[0].message.content
            
            # Парсинг координат из ответа
            coordinates = None
            import re
            coord_match = re.search(r"\[COORDINATES\](.*?)\[/COORDINATES\]", raw_content, re.DOTALL)
            if coord_match:
                import json
                try:
                    coordinates = json.loads(coord_match.group(1).strip())
                    # Очищаем основной текст от тегов координат для красоты
                    raw_content = re.sub(r"\[COORDINATES\].*?\[/COORDINATES\]", "", raw_content, flags=re.DOTALL).strip()
                except:
                    pass

            return AIResponse(
                content=raw_content,
                usage=response.get("usage", {}),
                model=model_name,
                coordinates=coordinates
            )
        except Exception as e:
            raise Exception(f"Ошибка при вызове ИИ модели: {str(e)}")

ai_client = AIClient()
