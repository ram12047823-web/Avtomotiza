from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from ..domain.models import AIAgent, AIAgentCreate, AIRequest, AIResponse, ModelType
from ..service.agent_service import agent_service

router = APIRouter(prefix="/agents", tags=["AI Agents"])

@router.post("/", response_model=AIAgent)
async def create_agent(agent_data: AIAgentCreate):
    """
    Добавить новую ИИ-модель (агента) в систему.
    Нужно указать название, IP (base_url) и тип специализации.
    """
    try:
        return await agent_service.create_agent(agent_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[AIAgent])
async def list_agents(model_type: Optional[ModelType] = Query(None)):
    """
    Получить список всех зарегистрированных ИИ-моделей.
    """
    return await agent_service.list_agents(model_type)

@router.post("/execute", response_model=AIResponse)
async def execute_request(request: AIRequest):
    """
    Выполнить запрос к конкретному ИИ-агенту.
    Система автоматически подставит нужный base_url и системный промпт.
    """
    try:
        return await agent_service.execute_agent_request(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{agent_id}", response_model=AIAgent)
async def get_agent(agent_id: UUID):
    """
    Получить детальную информацию об агенте.
    """
    try:
        return await agent_service.get_agent(agent_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
