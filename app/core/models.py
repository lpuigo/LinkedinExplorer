from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class PersonStatus(Enum):
    """Enumération des différents statuts possibles pour une personne dans le workflow."""
    A_TRAITER = "A traiter"
    EN_COURS = "En cours d'analyse"
    ANALYSE_INTERRESSANT = "Analysé intéressante"
    ANALYSE_NON_INTERRESSANT = "Analysé non intéressante"

@dataclass
class Personne:
    """Représente un profil LinkedIn avec ses informations et son statut de traitement."""
    url: str
    nom: Optional[str] = None
    titre: Optional[str] = None
    societe: Optional[str] = None
    lieu: Optional[str] = None
    source_url: Optional[str] = None
    statut: PersonStatus = PersonStatus.A_TRAITER
    
    # Pour l'affichage et la logique métier, on déduit l'intérêt du statut
    @property
    def est_interressante(self) -> bool:
        """Indique si la personne a été qualifiée comme intéressante."""
        return self.statut == PersonStatus.ANALYSE_INTERRESSANT

    def __hash__(self):
        return hash(self.url)

    def __eq__(self, other):
        if isinstance(other, Personne):
            return self.url == other.url
        return False