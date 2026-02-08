import sys
import asyncio
import yaml
import qasync
from PyQt6.QtWidgets import QApplication

from app.scraper.browser import LinkedInBrowser
from app.scraper.parsers import LinkedInParser
from app.gui.main_window import MainWindow

from app.core.services import WorkflowManager
from app.infra.storage.excel_storage import ExcelRepository

async def run_app():
    """
    Initialise la configuration, le repository, le workflow et l'IHM.
    """
    # Chargement config
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Initialisation de la couche Persistence & Métier
    excel_path = config['settings']['export_path']
    repo = ExcelRepository(excel_path)
    workflow = WorkflowManager(repo)
    
    # Chargement des données existantes (Liste "Analysé intéressante")
    workflow.load_initial_data()

    # Initialisation technique (Scraper)
    browser = LinkedInBrowser(headless=config['settings']['headless'])
    await browser.start()
    
    # Connexion manuelle
    await browser.login_manual()

    # Initialisation IHM
    parser = LinkedInParser()
    window = MainWindow(workflow, browser, parser, config)
    window.show()
    
    return window

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        with loop:
            # On lance l'initialisation asynchrone (attente de start browser, login...)
            # On récupère la fenêtre pour éviter qu'elle soit garbage collected
            window = loop.run_until_complete(run_app())
            
            # Une fois l'init terminée, on lance la boucle d'événements Qt infinie
            loop.run_forever()
            
    except KeyboardInterrupt:
        pass