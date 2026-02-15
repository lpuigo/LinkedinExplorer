from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import asyncio
import random
from app.scraper.browser import LinkedInBrowser
from app.scraper.parsers import LinkedInParser

class BrowserService(ABC):
    """Abstract interface for browser interactions."""

    @abstractmethod
    async def start(self):
        """Starts the browser service."""
        pass

    @abstractmethod
    async def stop(self):
        """Stops the browser service."""
        pass

    @abstractmethod
    async def login_manual(self):
        """Performs manual login."""
        pass

    @abstractmethod
    async def get_profile_data(self, url: str) -> Dict:
        """Navigates to a profile and extracts data."""
        pass

    @abstractmethod
    async def get_relations(self) -> List[Dict]:
        """Opens the 'show all' modal and extracts suggestions."""
        pass

    @abstractmethod
    def set_on_close_callback(self, callback):
        """Sets a callback for when the browser is closed."""
        pass


class RealBrowserService(BrowserService):
    """Implementation using real Playwright browser."""

    def __init__(self, headless: bool = False):
        self.browser = LinkedInBrowser(headless=headless)
        self.parser = LinkedInParser()

    async def start(self):
        await self.browser.start()

    async def stop(self):
        await self.browser.stop()

    async def login_manual(self):
        await self.browser.login_manual()

    async def get_profile_data(self, url: str) -> Dict:
        await self.browser.go_to_profile(url)
        return await self.parser.extract_main_profile(self.browser.page, url)

    async def get_relations(self) -> List[Dict]:
        await self.browser.open_show_all_modal()
        suggestions = await self.parser.extract_modal_suggestions(self.browser.page)
        # Close the modal
        try:
            await self.browser.page.click('button[aria-label="Dismiss"]', timeout=2000)
        except:
            pass
        return suggestions

    def set_on_close_callback(self, callback):
        self.browser.set_on_close_callback(callback)


class MockBrowserService(BrowserService):
    """Implementation using mock data."""

    def __init__(self):
        self.on_close_callback = None

    async def start(self):
        print("Mock Browser started.")

    async def stop(self):
        print("Mock Browser stopped.")

    async def login_manual(self):
        print("Mock Login successful.")

    async def get_profile_data(self, url: str) -> Dict:
        print(f"Mock navigating to {url}...")
        await asyncio.sleep(0.1) # Simulate network delay
        return {
            "nom": "Jean Dupont (Mock)",
            "titre": "Développeur Python Senior",
            "societe": "Mock Corp",
            "lieu": "Paris, France",
            "url": url
        }

    async def get_relations(self) -> List[Dict]:
        print("Mock fetching relations...")
        await asyncio.sleep(0.1) # Simulate network delay
        return [
            {
                "nom": f"Relation Mock {i}",
                "titre": "Ingenieur Mock",
                "url": f"https://www.linkedin.com/in/mock-relation-{i}/"
            }
            for i in range(1, 6)
        ]

    def set_on_close_callback(self, callback):
        self.on_close_callback = callback
