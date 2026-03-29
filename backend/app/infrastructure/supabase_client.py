import os
import socket
import sys
from supabase import create_client, Client

class SupabaseSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            raw_url = os.getenv("SUPABASE_URL")
            print(f"DEBUG_RAW_URL: |{raw_url}|")
            sys.stdout.flush()
            
            supabase_url = raw_url
            if not supabase_url:
                print("CRITICAL: SUPABASE_URL IS EMPTY", flush=True)
            else:
                # Очистка от кавычек, пробелов и переносов строк
                supabase_url = supabase_url.strip().strip('"').strip("'").strip()
                # Удаление завершающего слэша
                supabase_url = supabase_url.rstrip('/')
                
                # Исправление ситуации с двойным протоколом (https://https://)
                if "https://https://" in supabase_url:
                    print("FALLBACK: Detected double https:// protocol, fixing...", flush=True)
                    supabase_url = supabase_url.replace("https://https://", "https://")
                
                # Общая чистка двойных протоколов
                if "http" in supabase_url:
                    parts = supabase_url.split("://")
                    if len(parts) > 2:
                        supabase_url = "https://" + parts[-1]
                
                # Диагностика DNS
                try:
                    # Тест google.com
                    test_host = "google.com"
                    print(f"DNS_TEST: {test_host} is {socket.gethostbyname(test_host)}", flush=True)
                    
                    # Тест домена supabase
                    sb_host = supabase_url.replace("https://", "").replace("http://", "").split("/")[0]
                    print(f"DIAGNOSTIC: Attempting to resolve IP for host: {sb_host}", flush=True)
                    print(f"DNS_TEST_SUPABASE: {sb_host} is {socket.gethostbyname(sb_host)}", flush=True)
                except Exception as dns_err:
                    print(f"DNS_CRITICAL_ERROR: {dns_err}", flush=True)

            print(f'DEBUG: Final URL being used: "{supabase_url}"', flush=True)
            print(f'DEBUG: URL type: {type(supabase_url)}', flush=True)
            
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
            if supabase_key:
                supabase_key = supabase_key.strip().strip('"').strip("'")
            
            if supabase_url and supabase_key:
                try:
                    # Безопасное логирование URL при инициализации
                    url_to_log = supabase_url[:15] + "..." + supabase_url[-4:] if len(supabase_url) > 20 else supabase_url
                    print(f"SupabaseSingleton: Initializing client for {url_to_log}", flush=True)
                    cls._instance = create_client(supabase_url, supabase_key)
                except Exception as e:
                    print(f"SupabaseSingleton: CRITICAL: Failed to initialize Supabase client: {e}", flush=True)
                    cls._instance = None
            else:
                print(f"SupabaseSingleton: Warning: Supabase credentials missing. URL present: {bool(supabase_url)}, Key present: {bool(supabase_key)}", flush=True)
                cls._instance = None
        return cls._instance

def get_supabase() -> Client:
    return SupabaseSingleton()
