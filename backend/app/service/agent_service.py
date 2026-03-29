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
            # Безопасное логирование URL
            url_to_log = supabase_url[:15] + "..." + supabase_url[-4:] if len(supabase_url) > 20 else supabase_url
            print(f"Attempting to connect to Supabase at: {url_to_log}")
            try:
                self.supabase: Client = create_client(supabase_url, supabase_key)
            except Exception as e:
                print(f"CRITICAL: Invalid SUPABASE_URL format. Error: {e}")
        else:
            print("Supabase disabled: missing credentials")

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
        Логика оркестрации ИИ:
        1. Если в ai_config есть ip_url (Custom IP) — шлем туда.
        2. Иначе используем дефолтный Vision API (GPT-4o Vision или подобное через LiteLLM).
        """
        # Параметры по умолчанию (Vision API)
        api_key = os.getenv("DEFAULT_AI_API_KEY")
        base_url = os.getenv("DEFAULT_AI_BASE_URL")
        model_name = os.getenv("DEFAULT_AI_MODEL_NAME", "gpt-4o")
        model_type = ModelType.GENERAL

        # Если в запросе пришел конфиг, переопределяем
        if request.ai_config:
            if request.ai_config.ip_url:
                # Custom IP mode
                base_url = request.ai_config.ip_url
                api_key = request.ai_config.api_key
                model_name = request.ai_config.model_name or "gpt-3.5-turbo"
            
            if request.ai_config.category:
                try:
                    # Нормализация категории
                    v_lower = request.ai_config.category.strip().lower()
                    if v_lower in ['usability', 'ux']: model_type = ModelType.UX
                    elif v_lower == 'security': model_type = ModelType.SECURITY
                    elif v_lower == 'performance': model_type = ModelType.PERFORMANCE
                    elif v_lower == 'accessibility': model_type = ModelType.ACCESSIBILITY
                except:
                    pass

        # Вызов инфраструктурного слоя
        return await ai_client.complete(
            model_name=model_name,
            base_url=base_url,
            api_key=api_key,
            model_type=model_type,
            user_prompt=request.prompt,
            image_url=request.image_url,
            page_source=request.page_source,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

agent_service = AgentService()
