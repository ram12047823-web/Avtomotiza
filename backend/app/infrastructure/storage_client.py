import os
import time
import uuid
import mimetypes
from typing import Optional
from supabase import create_client, Client

class StorageClient:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        # Используем SERVICE_ROLE_KEY для записи в Storage
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY", "")
        
        if not self.supabase_url or not self.supabase_key:
            print("Warning: Supabase credentials not found in StorageClient.")
            self.supabase = None
        else:
            try:
                self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            except Exception as e:
                print(f"Error initializing Supabase client in StorageClient: {e}")
                self.supabase = None

    async def upload_media(self, local_path: str, scan_id: str) -> Optional[str]:
        """
        Загружает локальный файл в Supabase Storage и возвращает Public URL.
        После успешной загрузки удаляет локальный файл.
        """
        if not self.supabase:
            print("Supabase client not initialized in StorageClient. Skipping upload.")
            if os.path.exists(local_path):
                os.remove(local_path)
            return None
        if not os.path.exists(local_path):
            print(f"File not found: {local_path}")
            return None

        # Определение бакета по расширению
        ext = os.path.splitext(local_path)[1].lower()
        bucket = "screenshots" if ext in [".png", ".jpg", ".jpeg"] else "videos"
        
        # Генерация уникального имени файла
        timestamp = int(time.time())
        random_hash = uuid.uuid4().hex[:8]
        file_name = f"scan_{scan_id}/{timestamp}_{random_hash}{ext}"
        
        # Определение content-type
        content_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"

        try:
            with open(local_path, 'rb') as f:
                # Загрузка в Storage
                self.supabase.storage.from_(bucket).upload(
                    path=file_name,
                    file=f,
                    file_options={"content-type": content_type}
                )
            
            # Получение публичного URL
            public_url = self.supabase.storage.from_(bucket).get_public_url(file_name)
            
            # Удаление локального файла
            os.remove(local_path)
            
            return public_url
        except Exception as e:
            print(f"Error uploading to Storage: {e}")
            return None

storage_client = StorageClient()
