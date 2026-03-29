import os
from supabase import create_client, Client

class SupabaseSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            supabase_url = os.getenv("SUPABASE_URL")
            if supabase_url:
                # Очистка от кавычек и лишних пробелов
                supabase_url = supabase_url.strip().strip('"').strip("'").rstrip('/')
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
