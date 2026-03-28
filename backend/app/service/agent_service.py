from typing import List, Optional
from uuid import UUID
from supabase import create_client, Client
from ..domain.models import AIAgent, AIAgentCreate, AIRequest, AIResponse, ModelType
from ..infrastructure.ai_client import ai_client
import os

class AgentService:
    def __init__(self):
        # В реальном приложении эти данные берутся из .env
        supabase_url = os.getenv("SUPABASE_URL", "")
        supabase_key = os.getenv("SUPABASE_KEY", "")
        self.supabase: Client = create_client(supabase_url, supabase_key)

    async def create_agent(self, agent_data: AIAgentCreate) -> AIAgent:
        """Сохраняет нового ИИ-агента в Supabase."""
        response = self.supabase.table("ai_models").insert(agent_data.model_dump()).execute()
        if not response.data:
            raise Exception("Не удалось создать агента в базе данных.")
        return AIAgent(**response.data[0])

    async def get_agent(self, agent_id: UUID) -> AIAgent:
        """Получает данные об агенте по ID."""
        response = self.supabase.table("ai_models").select("*").eq("id", str(agent_id)).execute()
        if not response.data:
            raise Exception(f"Агент с ID {agent_id} не найден.")
        return AIAgent(**response.data[0])

    async def list_agents(self, model_type: Optional[ModelType] = None) -> List[AIAgent]:
        """Возвращает список всех доступных агентов, опционально фильтруя по типу."""
        query = self.supabase.table("ai_models").select("*")
        if model_type:
            query = query.eq("model_type", model_type.value)
        
        response = query.execute()
        return [AIAgent(**item) for item in response.data]

    async def execute_agent_request(self, request: AIRequest) -> AIResponse:
        """
        Основная логика: получает данные об агенте из БД и делает запрос через LiteLLM.
        Приоритет отдается конфигурации из запроса (ai_config).
        """
        agent = await self.get_agent(request.agent_id)
        
        if not agent.is_active:
            raise Exception(f"Агент {agent.name} деактивирован.")

        # Определяем параметры: приоритет у request.ai_config, затем данные из БД
        api_key = request.ai_config.api_key if (request.ai_config and request.ai_config.api_key) else agent.api_key
        model_name = request.ai_config.model_name if (request.ai_config and request.ai_config.model_name) else agent.model_name
        base_url = request.ai_config.ip_url if (request.ai_config and request.ai_config.ip_url) else agent.base_url

        if not api_key:
            raise Exception("API Key не предоставлен ни в запросе, ни в конфигурации агента.")

        # Вызов инфраструктурного слоя для работы с LiteLLM
        return await ai_client.complete(
            model_name=model_name,
            base_url=base_url,
            api_key=api_key,
            model_type=agent.model_type,
            user_prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

agent_service = AgentService()
