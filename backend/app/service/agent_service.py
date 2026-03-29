from typing import List, Optional
from uuid import UUID
from supabase import create_client, Client
from ..domain.models import AIAgent, AIAgentCreate, AIRequest, AIResponse, ModelType
from ..infrastructure.ai_client import ai_client
from ..infrastructure.supabase_client import get_supabase
from ..infrastructure.database_direct import list_ai_models, create_ai_model

class AgentService:
    def __init__(self):
        self.supabase = get_supabase()

    async def create_agent(self, agent_data: AIAgentCreate) -> AIAgent:
        """Сохраняет нового ИИ-агента в Supabase."""
        print(f"AGENT_SERVICE: Creating agent {agent_data.name}...", flush=True)
        res = await create_ai_model(agent_data.model_dump())
        if not res:
            raise Exception("Не удалось создать агента в базе данных.")
        return AIAgent(**res)

    async def get_agent(self, agent_id: UUID) -> AIAgent:
        """Получает данные об агенте по ID."""
        # Используем list_ai_models с фильтром по ID для простоты
        endpoint = f"{os.getenv('SUPABASE_URL')}/rest/v1/ai_models?id=eq.{agent_id}&select=*"
        print(f"AGENT_SERVICE: Fetching agent {agent_id}...", flush=True)
        
        import httpx
        from ..infrastructure.database_direct import HEADERS
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(endpoint, headers=HEADERS)
                if response.status_code < 400 and response.json():
                    return AIAgent(**response.json()[0])
                raise Exception(f"Агент с ID {agent_id} не найден.")
            except Exception as e:
                print(f"AGENT_SERVICE: Error fetching agent: {e}", flush=True)
                raise e

    async def list_agents(self, model_type: Optional[ModelType] = None) -> List[AIAgent]:
        """Возвращает список всех доступных агентов, опционально фильтруя по типу."""
        print(f"AGENT_SERVICE: Listing agents...", flush=True)
        res = await list_ai_models(model_type.value if model_type else None)
        return [AIAgent(**item) for item in res]

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
