from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

@dataclass
class Personne:
    """Représente un profil LinkedIn avec ses informations et son statut de traitement."""
    url: str
    nom: Optional[str] = None
    titre: Optional[str] = None
    societe: Optional[str] = None
    lieu: Optional[str] = None
    source_url: Optional[str] = None
    analyzed: bool = False
    interesting: bool = False
    
    # Pour l'affichage et la logique métier, on déduit l'intérêt du statut
    @property
    def est_interressante(self) -> bool:
        """Indique si la personne a été qualifiée comme intéressante."""
        return self.interesting

    def __hash__(self):
        return hash(self.url)

    def __eq__(self, other):
        if isinstance(other, Personne):
            return self.url == other.url
        return False