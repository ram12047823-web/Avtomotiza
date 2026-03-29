import httpx
import os
import sys
import socket

# Очистка и резолв URL
RAW_URL = os.getenv("SUPABASE_URL", "").strip().strip('"').strip("'").rstrip("/")
URL = RAW_URL
KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY", "").strip().strip('"').strip("'")

# Попытка ручного DNS резолва
if RAW_URL:
    try:
        host = RAW_URL.replace("https://", "").replace("http://", "").split("/")[0]
        ip_address = socket.gethostbyname(host)
        print(f"DNS_RESOLVE_SUCCESS: {host} -> {ip_address}", flush=True)
    except Exception as e:
        print(f"DNS_RESOLVE_FAILED: {e}", flush=True)

HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

async def update_scan_status(scan_id, status):
    """Обновление статуса сканирования в таблице scans."""
    endpoint = f"{URL}/rest/v1/scans?id=eq.{scan_id}"
    print(f"SENDING POST TO: {URL}/rest/v1/scans (status: {status})", flush=True)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.patch(
                endpoint,
                json={"status": status},
                headers=HEADERS
            )
            print(f"DIRECT_DB: Status Update Response: {response.status_code}", flush=True)
            if response.status_code >= 400:
                print(f"DIRECT_DB: Error Detail: {response.text}", flush=True)
            return response.json() if response.status_code < 400 and response.content else None
        except Exception as e:
            print(f"DIRECT_DB: CRITICAL HTTP ERROR: {e}", flush=True)
            return None

async def get_test_status(test_id: str):
    """Прямое получение статуса теста."""
    endpoint = f"{URL}/rest/v1/scans?id=eq.{test_id}&select=status"
    print(f"SENDING POST TO: {URL}/rest/v1/scans (get_status)", flush=True)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                endpoint,
                headers=HEADERS
            )
            if response.status_code < 400 and response.json():
                return response.json()[0].get('status')
            return None
        except Exception as e:
            print(f"DIRECT_DB: CRITICAL DNS/HTTP ERROR in get_status: {e}", flush=True)
            return None

async def list_ai_models(model_type: str = None):
    """Прямое получение списка ИИ моделей."""
    endpoint = f"{URL}/rest/v1/ai_models?select=*"
    if model_type:
        endpoint += f"&model_type=eq.{model_type}"
    
    print(f"SENDING POST TO: {URL}/rest/v1/ai_models (list_models)", flush=True)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                endpoint,
                headers=HEADERS
            )
            if response.status_code < 400:
                return response.json()
            return []
        except Exception as e:
            print(f"DIRECT_DB: CRITICAL DNS/HTTP ERROR in list_models: {e}", flush=True)
            return []

async def create_ai_model(data: dict):
    """Прямое создание ИИ модели."""
    endpoint = f"{URL}/rest/v1/ai_models"
    print(f"SENDING POST TO: {URL}/rest/v1/ai_models (create_model)", flush=True)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                endpoint,
                json=data,
                headers=HEADERS
            )
            if response.status_code < 400:
                return response.json()[0] if response.json() else None
            return None
        except Exception as e:
            print(f"DIRECT_DB: CRITICAL DNS/HTTP ERROR in create_model: {e}", flush=True)
            return None

async def save_test_result(test_id: str, url: str, status_code: int, issues: list, video_url: str = None):
    """Прямое сохранение результата теста в таблицу scan_reports."""
    endpoint = f"{URL}/rest/v1/scan_reports"
    print(f"SENDING POST TO: {URL}/rest/v1/scan_reports (save_result)", flush=True)
    
    data = {
        "scan_id": test_id,
        "url": url,
        "status_code": status_code,
        "issues": issues,
        "video_url": video_url
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                endpoint,
                json=data,
                headers=HEADERS
            )
            print(f"DIRECT_DB: Save Result Response: {response.status_code}", flush=True)
            if response.status_code >= 400:
                print(f"DIRECT_DB: Error Detail: {response.text}", flush=True)
            return response.json() if response.status_code < 400 and response.content else None
        except Exception as e:
            print(f"DIRECT_DB: CRITICAL HTTP ERROR: {e}", flush=True)
            return None

async def create_new_scan(url: str, level: str):
    """Создание новой записи сканирования."""
    endpoint = f"{URL}/rest/v1/scans"
    print(f"SENDING POST TO: {URL}/rest/v1/scans (create_scan)", flush=True)
    
    data = {
        "url": url,
        "level": level,
        "status": "Running"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                endpoint,
                json=data,
                headers=HEADERS
            )
            print(f"DIRECT_DB: Create Scan Response: {response.status_code}", flush=True)
            if response.status_code >= 400:
                print(f"DIRECT_DB: Error Detail: {response.text}", flush=True)
            return response.json()[0] if response.status_code < 400 and response.json() else None
        except Exception as e:
            print(f"DIRECT_DB: CRITICAL HTTP ERROR: {e}", flush=True)
            return None
