import os
import socket
from dotenv import load_dotenv

# Загрузка переменных окружения ДО импорта сервисов
load_dotenv()

# Очистка переменных окружения от кавычек
for key in ["SUPABASE_URL", "SUPABASE_KEY"]:
    val = os.getenv(key)
    if val:
        os.environ[key] = val.replace('"', '').replace("'", "").strip()

# Проверка DNS для Supabase перед запуском (для Leapcell)
supabase_url = os.getenv("SUPABASE_URL")
if supabase_url:
    try:
        host = supabase_url.replace("https://", "").replace("http://", "").split("/")[0]
        print(f"DNS Check: Resolving host {host}...", flush=True)
        ip = socket.gethostbyname(host)
        print(f"DNS Check: SUCCESS! {host} resolved to {ip}", flush=True)
    except socket.gaierror as e:
        print("\n" + "!"*60, flush=True)
        print("!!! CRITICAL DNS ERROR: Name or service not known !!!", flush=True)
        print(f"!!! Cannot resolve Supabase host: {supabase_url} !!!", flush=True)
        print("!!! This usually means Leapcell cannot reach the internet or DNS is blocked !!!", flush=True)
        print("!"*60 + "\n", flush=True)
    except Exception as e:
        print(f"DNS Check: Unknown error: {e}", flush=True)

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
    """Проверка подключения к БД при запуске через прямой HTTP запрос."""
    import httpx
    from .infrastructure.database_direct import URL, HEADERS
    
    print(f"Startup: Checking database connection to {URL}...", flush=True)
    
    if not URL or "supabase.co" not in URL:
        print("\n" + "!"*60, flush=True)
        print("!!! DATABASE CONNECTION ERROR: SUPABASE_URL is invalid or empty !!!")
        print("!"*60 + "\n", flush=True)
        return

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Пробуем сделать простой запрос к таблице ai_models
            resp = await client.get(f"{URL}/rest/v1/ai_models?select=id&limit=1", headers=HEADERS)
            if resp.status_code < 400:
                print("Startup: Database connection SUCCESS!", flush=True)
            else:
                print("\n" + "!"*60, flush=True)
                print(f"!!! DATABASE CONNECTION ERROR: Status {resp.status_code} !!!")
                print(f"!!! Detail: {resp.text} !!!")
                print("!"*60 + "\n", flush=True)
    except Exception as e:
        print("\n" + "!"*60, flush=True)
        print(f"!!! DATABASE CONNECTION ERROR: {e} !!!")
        print("!"*60 + "\n", flush=True)


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
