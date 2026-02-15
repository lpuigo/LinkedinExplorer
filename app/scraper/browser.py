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
        self.playwright = None
        self.on_close_callback = None

    async def start(self):
        """Lance l'instance du navigateur Playwright."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.browser.on("disconnected", lambda b: self._on_disconnected())
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    def set_on_close_callback(self, callback):
        self.on_close_callback = callback

    def _on_disconnected(self):
        print("Navigateur Playwright déconnecté.")
        if self.on_close_callback:
            self.on_close_callback()

    async def stop(self):
        """Ferme proprement les ressources Playwright."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"Erreur lors de la fermeture du navigateur : {e}")

    async def login_manual(self):
        """Ouvre la page de login et attend que l'utilisateur soit sur le feed."""
        try:
            await self.page.goto("https://www.linkedin.com/login")
            print("Veuillez vous connecter manuellement dans la fenêtre du navigateur...")
            # On attend que l'URL contienne 'feed' ou que l'utilisateur valide dans l'UI
            await self.page.wait_for_url("**/feed/**", timeout=0)
        except Exception as e:
             # Playwright peut lever une erreur avec le message "Target page, context or browser has been closed"
             msg = str(e)
             if "Target closed" in msg or "browser has been closed" in msg:
                 print("Le navigateur a été fermé pendant la connexion.")
                 # On relance une erreur plus "propre" ou on laisse remonter
                 # Ici on raise pour interrompre run_app
                 raise RuntimeError("Navigateur fermé par l'utilisateur")
             else:
                 raise e

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