from typing import List, Optional
from uuid import UUID
from supabase import create_client, Client
from ..domain.models import AIAgent, AIAgentCreate, AIRequest, AIResponse, ModelType
from ..infrastructure.ai_client import ai_client
import os

class AgentService:
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        
        self.supabase = None
        if supabase_url and supabase_key:
            try:
                self.supabase: Client = create_client(supabase_url, supabase_key)
            except Exception:
                print("Supabase disabled")
        else:
            print("Supabase disabled")

    async def create_agent(self, agent_data: AIAgentCreate) -> AIAgent:
        """Сохраняет нового ИИ-агента в Supabase."""
        if not self.supabase:
            raise Exception("Database not available. Cannot create agent.")
        
        response = self.supabase.table("ai_models").insert(agent_data.model_dump()).execute()
        if not response.data:
            raise Exception("Не удалось создать агента в базе данных.")
        return AIAgent(**response.data[0])

    async def get_agent(self, agent_id: UUID) -> AIAgent:
        """Получает данные об агенте по ID."""
        if not self.supabase:
            raise Exception("Database not available. Cannot fetch agent.")
            
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
        
        try:
            response = query.execute()
            return [AIAgent(**item) for item in response.data]
        except Exception as e:
            print(f"Error listing agents: {e}")
            return []

    async def execute_agent_request(self, request: AIRequest) -> AIResponse:
        """
        Логика: воркер берет api_key и ip_url только из входящего запроса (ai_config).
        Если данных в запросе нет, возвращает ошибку (полная автономность).
        """
        if not request.ai_config or not request.ai_config.api_key or not request.ai_config.ip_url:
            raise Exception("Autonomous mode: api_key and ip_url (Base URL) must be provided in request.")

        api_key = request.ai_config.api_key
        base_url = request.ai_config.ip_url
        model_name = request.ai_config.model_name or "gpt-3.5-turbo"
        model_type = request.ai_config.category or ModelType.GENERAL

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
