import os
import socket
from dotenv import load_dotenv

# Загрузка переменных окружения ДО импорта сервисов
load_dotenv()

# Проверка DNS для Supabase перед запуском (для Leapcell)
supabase_url = os.getenv("SUPABASE_URL")
if supabase_url:
    try:
        host = supabase_url.replace("https://", "").replace("http://", "").split("/")[0]
        print(f"DNS Check: Resolving host {host}...")
        ip = socket.gethostbyname(host)
        print(f"DNS Check: SUCCESS! {host} resolved to {ip}")
    except socket.gaierror as e:
        print("\n" + "!"*60)
        print("!!! CRITICAL DNS ERROR: Name or service not known !!!")
        print(f"!!! Cannot resolve Supabase host: {supabase_url} !!!")
        print("!!! This usually means Leapcell cannot reach the internet or DNS is blocked !!!")
        print("!"*60 + "\n")
    except Exception as e:
        print(f"DNS Check: Unknown error: {e}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.agents import router as agents_router
from .api.tests import router as tests_router
from .api.reports import router as reports_router
from .infrastructure.supabase_client import get_supabase

app = FastAPI(
    title="AI Multi-factor Testing Platform API",
    description="Backend for AI-driven website testing using Playwright and LiteLLM",
    version="0.1.0"
)

@app.on_event("startup")
async def startup_event():
    """Проверка подключения к БД при запуске."""
    print("Startup: Checking database connection...")
    supabase = get_supabase()
    if not supabase:
        print("\n" + "!"*60)
        print("!!! DATABASE CONNECTION ERROR: Supabase client not initialized !!!")
        print("!"*60 + "\n")
        # Мы не выходим принудительно, чтобы дать серверу запуститься, 
        # но логи будут очень заметными.
        return

    try:
        # Пробуем сделать простой запрос к любой таблице
        # Используем .limit(1) для минимальной нагрузки
        supabase.table("ai_models").select("*").limit(1).execute()
        print("Startup: Database connection SUCCESS!")
    except Exception as e:
        print("\n" + "!"*60)
        print(f"!!! DATABASE CONNECTION ERROR: {e} !!!")
        print("!"*60 + "\n")
        # В облаке лучше упасть сразу, если база недоступна
        # Но для отладки пока оставим только лог


# Настройка CORS для всех источников
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(agents_router, prefix="/api", tags=["Agents"])
app.include_router(tests_router, prefix="/api", tags=["Tests"])
app.include_router(reports_router, prefix="/api", tags=["Reports"])

@app.get("/")
async def root():
    return {"message": "AI Multi-factor Testing API is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
