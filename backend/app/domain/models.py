from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
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

class AIAgentCreate(BaseModel):
    name: str
    base_url: str
    api_key: Optional[str] = None
    model_type: ModelType
    model_name: str = "gpt-3.5-turbo"

class AIConfig(BaseModel):
    category: ModelType
    ip_url: str  # IP адрес или URL модели (Base URL)
    api_key: Optional[str] = None
    model_name: Optional[str] = "gpt-3.5-turbo"

class ScanRequest(BaseModel):
    url: str
    level: TestLevel
    ai_configs: List[AIConfig]
    api_key: Optional[str] = None

class AIRequest(BaseModel):
    agent_id: UUID
    prompt: str
    ai_config: Optional[AIConfig] = None
    max_tokens: Optional[int] = 1000
    temperature: float = 0.7

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
