from abc import ABC, abstractmethod
from typing import List, Optional
from app.core.models import Personne

class PersonRepository(ABC):
    """Interface abstraite définissant les opérations de persistence pour les personnes."""
    @abstractmethod
    def load_existing_persons(self) -> List[Personne]:
        """Charge les personnes déjà existantes (persistées)."""
        pass

    @abstractmethod
    def save_person(self, person: Personne) -> None:
        """Sauvegarde ou met à jour une personne."""
        pass

    @abstractmethod
    def remove_person(self, person: Personne) -> None:
        """Supprime une personne du stockage."""
        pass

    @abstractmethod
    def exists(self) -> bool:
        """Vérifie si le support de stockage existe."""
        pass

    @abstractmethod
    def save_all(self, persons: List[Personne]) -> None:
        """Sauvegarde une liste complète de personnes."""
        pass
