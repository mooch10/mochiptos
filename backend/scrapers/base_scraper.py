"""
Clase base para navegadores Playwright con configuraciones Stealth/Anti-bot.
"""

import random
import asyncio
from playwright.async_api import async_playwright, BrowserContext, Page

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
]

class BaseScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context: BrowserContext = None
        self.page: Page = None

    async def init_browser(self):
        """Inicializa Playwright con banderas anti-detección."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--window-size=1920,1080",
            ]
        )

        user_agent = random.choice(USER_AGENTS)
        self.context = await self.browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
            locale="es-AR",
            timezone_id="America/Argentina/Buenos_Aires",
        )

        # Ocultar la propiedad navigator.webdriver
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        self.page = await self.context.new_page()

    async def random_pause(self, min_seconds: float = 1.5, max_seconds: float = 4.0):
        """Genera una pausa aleatoria para simular comportamiento humano."""
        pause_time = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(pause_time)

    async def close(self):
        """Cierra el contexto y navegador de Playwright."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
