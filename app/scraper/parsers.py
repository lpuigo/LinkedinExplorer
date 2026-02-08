from playwright.async_api import Page
from typing import List, Dict
import asyncio

class LinkedInParser:
    """Utilitaires d'extraction de données depuis les pages LinkedIn."""
    @staticmethod
    async def extract_main_profile(page: Page, url: str) -> Dict:
        """Extrait les informations principales (nom, titre, société...) d'un profil."""
        # Attente du chargement du bloc identité
        await page.wait_for_selector("h1")

        nom = await page.locator("h1").first.inner_text()
        # Titre juste en dessous du nom
        titre = await page.locator(".text-body-medium.break-words").first.inner_text()

        # Société via aria-label (votre capture 4)
        societe = ""
        societe_loc = page.locator('button[aria-label^="Current company:"]')
        if await societe_loc.count() > 0:
            societe = (await societe_loc.inner_text()).strip()

        # Lieu (votre capture 5)
        lieu = await page.locator("span.text-body-small.inline.t-black--light.break-words").first.inner_text()

        return {
            "nom": nom.strip(),
            "titre": titre.strip(),
            "societe": societe,
            "lieu": lieu.strip(),
            "url": url
        }

    @staticmethod
    async def extract_modal_suggestions(page: Page) -> List[Dict]:
        """Scrape la liste des profils suggérés dans la modale 'People also viewed'."""
        suggestions = []
        # On attend que la modale soit visible (votre trait jaune)
        await page.wait_for_selector('div[data-test-modal]')

        # Liste des items (votre trait bleu), on cible uniquement ce qui est dans la modale
        items = page.locator("div[data-test-modal] li.artdeco-list__item")
        count = await items.count()

        for i in range(count):
            item = items.nth(i)
            try:
                # On s'assure que l'élément est visible (scroll si besoin) pour déclencher le chargement (lazy load)
                # On cible un élément interne (le lien) pour être sûr
                await item.locator('a[data-field="browsemap_card_click"]').first.scroll_into_view_if_needed()
                # Petite pause pour laisser le temps au rendu si nécessaire
                await asyncio.sleep(0.1)

                # Récupération de l'élément
                link_el = item.locator('a[data-field="browsemap_card_click"]')
                # Récupération de l'URL dans le premier sous élément
                url = await link_el.first.get_attribute("href")
                
                # Récupération des texte dans le second sous élément
                # Note: locator() n'est pas awaitable
                text_el = link_el.nth(1).locator('span[aria-hidden="true"]')
                # Le Nom est dans la premier span, et le titre dans le dernière
                nom = await text_el.first.inner_text()
                titre = await text_el.nth(-1).inner_text()

                suggestions.append({
                    "nom": nom.strip(),
                    "titre": titre.strip(),
                    "url": url.split('?')[0] # Nettoyage des paramètres d'URL
                })
            except Exception as e:
                # On ignore silencieusement les erreurs si ce n'est pas un profil valide ou si timeout
                # print(f"Erreur extraction item {i}: {e}")
                continue
            
        return suggestions