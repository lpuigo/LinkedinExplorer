from playwright.async_api import async_playwright
import random
import asyncio

class LinkedInBrowser:
    """Contrôleur du navigateur Playwright pour l'automatisation LinkedIn."""
    def __init__(self, headless=False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None

    async def start(self):
        """Lance l'instance du navigateur Playwright."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def login_manual(self):
        """Ouvre la page de login et attend que l'utilisateur soit sur le feed."""
        await self.page.goto("https://www.linkedin.com/login")
        print("Veuillez vous connecter manuellement dans la fenêtre du navigateur...")
        # On attend que l'URL contienne 'feed' ou que l'utilisateur valide dans l'UI
        await self.page.wait_for_url("**/feed/**", timeout=0)

    async def go_to_profile(self, url: str):
        """Navigue vers l'URL d'un profil et attend un court instant."""
        await self.page.goto(url)
        # Délai aléatoire "humain" demandé
        await asyncio.sleep(random.uniform(1.5, 3.0))

    async def open_show_all_modal(self):
        """Clique sur le bouton 'Show all' entouré en rouge."""
        selector = 'a[aria-label="Show all other similar profiles"]'
        # Correction: scroll_into_view_if_needed est une méthode de Locator, pas de Page
        await self.page.locator(selector).scroll_into_view_if_needed()
        await asyncio.sleep(1)
        await self.page.click(selector)
        # Attendre que la modale apparaisse
        await self.page.wait_for_selector(".artdeco-modal")