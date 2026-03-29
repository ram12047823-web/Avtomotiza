import os
import socket
from supabase import create_client, Client

class SupabaseSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            supabase_url = os.getenv("SUPABASE_URL")
            
            if not supabase_url:
                print("CRITICAL: SUPABASE_URL IS EMPTY")
            else:
                # Очистка от кавычек и лишних пробелов
                supabase_url = supabase_url.strip().strip('"').strip("'").rstrip('/')
                
                # Диагностика DNS
                try:
                    host = supabase_url.replace("https://", "").replace("http://", "").split("/")[0]
                    print(f"DIAGNOSTIC: Attempting to resolve IP for host: {host}")
                    ip = socket.gethostbyname(host)
                    print(f"DIAGNOSTIC: IP for host is {ip}")
                except Exception as dns_err:
                    print(f"DIAGNOSTIC: DNS RESOLUTION FAILED for {supabase_url}: {dns_err}")

                # Исправление ситуации с двойным протоколом или опечатками
                if "http" in supabase_url:
                    parts = supabase_url.split("://")
                    if len(parts) > 2: # Например http://https://...
                        supabase_url = "https://" + parts[-1]
                
            print(f'DEBUG: Full URL being used: "{supabase_url}"')
            print(f'DEBUG: URL type: {type(supabase_url)}')
            
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
            if supabase_key:
                supabase_key = supabase_key.strip().strip('"').strip("'")
            
            if supabase_url and supabase_key:
                try:
                    # Безопасное логирование URL при инициализации
                    url_to_log = supabase_url[:15] + "..." + supabase_url[-4:] if len(supabase_url) > 20 else supabase_url
                    print(f"SupabaseSingleton: Initializing client for {url_to_log}")
                    cls._instance = create_client(supabase_url, supabase_key)
                except Exception as e:
                    print(f"SupabaseSingleton: CRITICAL: Failed to initialize Supabase client: {e}")
                    cls._instance = None
            else:
                print(f"SupabaseSingleton: Warning: Supabase credentials missing. URL present: {bool(supabase_url)}, Key present: {bool(supabase_key)}")
                cls._instance = None
        return cls._instance

def get_supabase() -> Client:
    return SupabaseSingleton()
