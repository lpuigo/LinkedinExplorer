import sys
import asyncio
import yaml
import qasync
from PyQt6.QtWidgets import QApplication

from app.core.browser_service import RealBrowserService, MockBrowserService
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

    # Initialisation technique (Browser Service)
    if config['settings'].get('mock', False):
        print("Démarrage en mode MOCK")
        browser_service = MockBrowserService()
    else:
        print("Démarrage en mode PLAYWRIGHT")
        browser_service = RealBrowserService(headless=config['settings']['headless'])

    await browser_service.start()
    
    try:
        # Connexion (manuelle ou mock)
        await browser_service.login_manual()

        # Initialisation IHM
        window = MainWindow(workflow, browser_service, config)
        
        # Si le navigateur est fermé, on ferme l'application (la fenêtre principale)
        browser_service.set_on_close_callback(window.close)
        
        window.show()
        
        return window
    except Exception as e:
        # En cas d'erreur pendant l'initialisation (ex: fermeture prématurée du navigateur),
        # on s'assure de tout arrêter proprement ici car le main ne pourra pas le faire via 'window'
        await browser_service.stop()
        raise e

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        window = None
        
        with loop:
            try:
                # On lance l'initialisation asynchrone (attente de start browser, login...)
                # On récupère la fenêtre pour éviter qu'elle soit garbage collected
                window = loop.run_until_complete(run_app())
                
                # Une fois l'init terminée, on lance la boucle d'événements Qt infinie
                loop.run_forever()
            except Exception as e:
                print(f"L'application s'est arrêtée : {e}")
            finally:
                # Nettoyage propre à la sortie, même en cas d'erreur
                if window and window.browser:
                     print("Arrêt du navigateur lié à la fermeture de l'application...")
                     try:
                        loop.run_until_complete(window.browser.stop())
                     except Exception:
                         pass
                
                # S'assurer que toutes les tâches asynchrones sont terminées
                # Cela évite "Task was destroyed but it is pending"
                try:
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except Exception:
                    pass
            
    except KeyboardInterrupt:
        pass