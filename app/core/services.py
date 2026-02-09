from collections import deque
from typing import List, Optional, Dict
from app.core.models import Personne
from app.core.repository import PersonRepository

class WorkflowManager:
    """Gère la logique métier du workflow de recrutement : file d'attente, états, et persistence."""
    def __init__(self, repository: PersonRepository):
        self.repository = repository
        self.all_persons: Dict[str, Personne] = {} # URL -> Personne (cache global)
        self.queue: deque = deque() # File d'attente des "A_TRAITER"
        self.current_person: Optional[Personne] = None

    def load_initial_data(self):
        """Charge les données depuis le repo et initialise l'état."""
        loaded_persons = self.repository.load_existing_persons()
        for p in loaded_persons:
            p.analyzed = True
            p.interesting = True
            self.all_persons[p.url] = p
            # Ils sont déjà intéressants, donc pas dans la queue A_TRAITER
            # Mais on les garde dans le cache pour affichage et dédoublonnage

    def add_person(self, url: str, source_url: Optional[str] = None, 
                   nom: Optional[str] = None, titre: Optional[str] = None) -> Optional[Personne]:
        """Ajoute une personne à la file si elle n'existe pas déjà."""
        # Nettoyage URL basique
        clean_url = url.split("?")[0]
        
        if clean_url in self.all_persons:
            return None # Doublon
        
        # Si le nom n'est pas fourni, on tente de l'extraire de l'URL
        if not nom:
            # ex: https://www.linkedin.com/in/christelle-b-a3b6242/ -> christelle-b-a3b6242
            # on retire le slash de fin s'il existe, puis on prend le dernier segment
            nom = clean_url.rstrip("/").split("/")[-1]

        p = Personne(
            url=clean_url, 
            source_url=source_url,
            nom=nom,
            titre=titre,
            analyzed=False,
            interesting=False
        )
        self.all_persons[clean_url] = p
        self.queue.append(p)
        return p

    def get_next_person(self) -> Optional[Personne]:
        """Récupère la prochaine personne à traiter."""
        if not self.queue:
            return None
        
        self.current_person = self.queue.popleft()
        # self.current_person.analyzed = True # On pourrait marquer analysé ici ?
        return self.current_person

    def set_current_person_decision(self, is_interesting: bool):
        """Valide la décision pour la personne en cours."""
        if not self.current_person:
            return

        self.current_person.analyzed = True
        self.current_person.interesting = is_interesting
        
        if is_interesting:
            self.repository.save_person(self.current_person)
        else:
            self.repository.remove_person(self.current_person)

    def update_current_person_info(self, info: dict):
        """Met à jour les infos de la personne courante après scraping."""
        if not self.current_person:
            return
        
        if 'nom' in info: self.current_person.nom = info['nom']
        if 'titre' in info: self.current_person.titre = info['titre']
        if 'societe' in info: self.current_person.societe = info['societe']
        if 'lieu' in info: self.current_person.lieu = info['lieu']
