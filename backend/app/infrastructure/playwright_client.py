import asyncio
import os
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from urllib.parse import urljoin, urlparse

class PlaywrightClient:
    def __init__(self, video_dir: str = "/tmp/videos"):
        self.video_dir = video_dir
        self.screenshot_dir = "/tmp/screenshots"
        
        # Создаем директории в /tmp
        for d in [self.video_dir, self.screenshot_dir]:
            if not os.path.exists(d):
                os.makedirs(d, exist_ok=True)

    async def get_page_info(self, url: str) -> Dict[str, Any]:
        """Экспресс-тест: статус-код и скриншот."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            response = await page.goto(url)
            status = response.status
            
            screenshot_path = os.path.join(self.screenshot_dir, f"express_{int(asyncio.get_event_loop().time())}.png")
            await page.screenshot(path=screenshot_path)
            await browser.close()
            
            return {
                "status_code": status,
                "screenshot_path": screenshot_path,
                "url": url
            }

    async def crawl_and_test(self, base_url: str, max_pages: int = 10) -> List[Dict[str, Any]]:
        """Глубокое изучение: crawler и видео."""
        results = []
        visited = set()
        to_visit = [base_url]
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            # Настройка контекста с записью видео в /tmp
            context = await browser.new_context(
                record_video_dir=self.video_dir,
                record_video_size={"width": 1280, "height": 720}
            )
            
            count = 0
            while to_visit and count < max_pages:
                current_url = to_visit.pop(0)
                if current_url in visited:
                    continue
                
                visited.add(current_url)
                count += 1
                
                page = await context.new_page()
                try:
                    response = await page.goto(current_url, wait_until="networkidle")
                    status = response.status
                    
                    # Скриншот для анализа в /tmp
                    screenshot_name = f"deep_{count}_{int(asyncio.get_event_loop().time())}.png"
                    screenshot_path = os.path.join(self.screenshot_dir, screenshot_name)
                    await page.screenshot(path=screenshot_path)
                    
                    # Поиск новых ссылок на той же области
                    if count < max_pages:
                        links = await page.query_selector_all("a")
                        for link in links:
                            href = await link.get_attribute("href")
                            if href:
                                full_url = urljoin(base_url, href)
                                if self._is_same_domain(base_url, full_url):
                                    to_visit.append(full_url)
                    
                    video_path = await page.video.path() if page.video else None
                    
                    results.append({
                        "url": current_url,
                        "status_code": status,
                        "screenshot_path": screenshot_path,
                        "video_path": video_path
                    })
                    
                except Exception as e:
                    print(f"Error testing {current_url}: {e}")
                finally:
                    await page.close()
            
            await context.close()
            await browser.close()
            
        return results

    def _is_same_domain(self, base_url: str, target_url: str) -> bool:
        base_domain = urlparse(base_url).netloc
        target_domain = urlparse(target_url).netloc
        return base_domain == target_domain

playwright_client = PlaywrightClient()
