import os
from supabase import create_client, Client

class SupabaseSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
            
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
                print("SupabaseSingleton: Warning: Supabase credentials missing.")
                cls._instance = None
        return cls._instance

def get_supabase() -> Client:
    return SupabaseSingleton()
