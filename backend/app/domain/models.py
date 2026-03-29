from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime

class ModelType(str, Enum):
    UX = "UX"
    SECURITY = "Security"
    PERFORMANCE = "Performance"
    ACCESSIBILITY = "Accessibility"
    GENERAL = "General"

class TestLevel(str, Enum):
    EXPRESS = "Express"
    STANDARD = "Standard"
    DEEP = "Deep"

class TestStatus(str, Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"

class AIAgent(BaseModel):
    id: Optional[UUID] = None
    name: str
    base_url: str
    api_key: Optional[str] = None
    model_type: ModelType
    model_name: str = "gpt-3.5-turbo"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator('model_type', mode='before')
    @classmethod
    def normalize_model_type(cls, v):
        if isinstance(v, str):
            # Переводим в Title Case (например, performance -> Performance)
            # Если это UX, оставляем в верхнем регистре
            v_title = v.strip().title()
            if v_title == "Ux": return "UX"
            return v_title
        return v

class AIAgentCreate(BaseModel):
    name: str
    base_url: str
    api_key: Optional[str] = None
    model_type: ModelType
    model_name: str = "gpt-3.5-turbo"

    @field_validator('model_type', mode='before')
    @classmethod
    def normalize_model_type(cls, v):
        if isinstance(v, str):
            v_title = v.strip().title()
            if v_title == "Ux": return "UX"
            return v_title
        return v

class AIConfig(BaseModel):
    category: str
    ip_url: str = Field(..., alias="endpoint")  # Поддержка старого формата 'endpoint'
    api_key: Optional[str] = None
    model_name: Optional[str] = "gpt-3.5-turbo"

    class Config:
        populate_by_name = True

    @field_validator('category', mode='before')
    @classmethod
    def normalize_category(cls, v):
        if isinstance(v, str):
            v_lower = v.strip().lower()
            # Маппинг специфичных названий
            if v_lower in ['usability', 'ux']: return "UX"
            if v_lower in ['compatibility', 'general']: return "General"
            if v_lower == 'security': return "Security"
            if v_lower == 'performance': return "Performance"
            if v_lower == 'accessibility': return "Accessibility"
            # По умолчанию приводим к Title Case
            return v.strip().title()
        return v

class ScanRequest(BaseModel):
    id: Optional[UUID] = Field(None, alias="scan_id")
    url: str
    level: TestLevel = Field(..., alias="mode")
    ai_configs: List[AIConfig] = Field(..., alias="ai_config")
    api_key: Optional[str] = None

    class Config:
        populate_by_name = True

    @field_validator('level', mode='before')
    @classmethod
    def normalize_level(cls, v):
        if isinstance(v, str):
            v_title = v.strip().title()
            # Валидатор нормализует регистр (например, 'standard' -> 'Standard')
            # Pydantic затем проверит соответствие Enum TestLevel
            return v_title
        return v

class AIRequest(BaseModel):
    agent_id: UUID
    prompt: str
    ai_config: Optional[AIConfig] = Field(None, alias="ai_configs")
    max_tokens: Optional[int] = 1000
    temperature: float = 0.7

    class Config:
        populate_by_name = True

class AIResponse(BaseModel):
    content: str
    usage: Optional[dict] = None
    model: str

class TestTask(BaseModel):
    id: Optional[UUID] = None
    url: str
    level: TestLevel
    status: TestStatus = TestStatus.PENDING
    created_at: Optional[datetime] = None

class TestIssue(BaseModel):
    description: str
    recommendation: str
    screenshot_url: Optional[str] = None
    severity: str = "medium"

class TestResult(BaseModel):
    id: Optional[UUID] = None
    test_id: UUID
    url: str
    status_code: int
    issues: List[TestIssue] = []
    video_url: Optional[str] = None
    created_at: Optional[datetime] = None
