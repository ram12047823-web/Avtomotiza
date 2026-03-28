from typing import List, Optional
from uuid import UUID
from supabase import create_client, Client
from ..domain.models import AIAgent, AIAgentCreate, AIRequest, AIResponse, ModelType
from ..infrastructure.ai_client import ai_client
import os

class AgentService:
    def __init__(self):
        # Используем SERVICE_ROLE_KEY для административных действий
        supabase_url = os.getenv("SUPABASE_URL", "")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY", "")
        
        if not supabase_url or not supabase_key:
            print("Warning: Supabase credentials not found. API might fail.")
            self.supabase = None
        else:
            self.supabase: Client = create_client(supabase_url, supabase_key)

    async def create_agent(self, agent_data: AIAgentCreate) -> AIAgent:
        """Сохраняет нового ИИ-агента в Supabase."""
        if not self.supabase:
            raise Exception("Supabase client not initialized.")
        response = self.supabase.table("ai_models").insert(agent_data.model_dump()).execute()
        if not response.data:
            raise Exception("Не удалось создать агента в базе данных.")
        return AIAgent(**response.data[0])

    async def get_agent(self, agent_id: UUID) -> AIAgent:
        """Получает данные об агенте по ID."""
        if not self.supabase:
            raise Exception("Supabase client not initialized.")
        response = self.supabase.table("ai_models").select("*").eq("id", str(agent_id)).execute()
        if not response.data:
            raise Exception(f"Агент с ID {agent_id} не найден.")
        return AIAgent(**response.data[0])

    async def list_agents(self, model_type: Optional[ModelType] = None) -> List[AIAgent]:
        """Возвращает список всех доступных агентов, опционально фильтруя по типу."""
        if not self.supabase:
            return []
        query = self.supabase.table("ai_models").select("*")
        if model_type:
            query = query.eq("model_type", model_type.value)
        
        response = query.execute()
        return [AIAgent(**item) for item in response.data]

    async def execute_agent_request(self, request: AIRequest) -> AIResponse:
        """
        Основная логика: выполняет запрос через LiteLLM.
        Приоритет отдается конфигурации из запроса (ai_config).
        Если ai_config.api_key и ip_url предоставлены, запрос выполняется БЕЗ обращения к Supabase.
        """
        # Если в запросе переданы ВСЕ необходимые данные для автономной работы
        if request.ai_config and request.ai_config.api_key and request.ai_config.ip_url:
            api_key = request.ai_config.api_key
            base_url = request.ai_config.ip_url
            model_name = request.ai_config.model_name or "gpt-3.5-turbo"
            # Для автономного режима используем тип из запроса или GENERAL
            model_type = request.ai_config.category or ModelType.GENERAL
        else:
            # Иначе пытаемся получить данные из БД по ID агента
            agent = await self.get_agent(request.agent_id)
            if not agent.is_active:
                raise Exception(f"Агент {agent.name} деактивирован.")
            
            api_key = (request.ai_config.api_key if request.ai_config else None) or agent.api_key
            base_url = (request.ai_config.ip_url if request.ai_config else None) or agent.base_url
            model_name = (request.ai_config.model_name if request.ai_config else None) or agent.model_name
            model_type = agent.model_type

        if not api_key:
            raise Exception("API Key не предоставлен.")

        # Вызов инфраструктурного слоя для работы с LiteLLM
        return await ai_client.complete(
            model_name=model_name,
            base_url=base_url,
            api_key=api_key,
            model_type=model_type,
            user_prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

agent_service = AgentService()
