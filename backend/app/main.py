from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.agents import router as agents_router
from .api.tests import router as tests_router
from .api.reports import router as reports_router
from dotenv import load_dotenv
import os

# Загрузка переменных окружения из .env
load_dotenv()

app = FastAPI(
    title="AI Multi-factor Testing Platform API",
    description="Backend for AI-driven website testing using Playwright and LiteLLM",
    version="0.1.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(agents_router)
app.include_router(tests_router)
app.include_router(reports_router)

@app.get("/")
async def root():
    return {"message": "AI Multi-factor Testing API is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
