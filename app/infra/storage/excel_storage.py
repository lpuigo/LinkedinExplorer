import pandas as pd
import os
from typing import List
from app.core.models import Personne, PersonStatus
from app.core.repository import PersonRepository

class ExcelRepository(PersonRepository):
    """Implémentation du repository utilisant un fichier Excel comme source de données."""
    COLUMNS = ["Nom", "Titre", "Société", "Région", "Lien Linkedin", "Source"]
    # COLUMNS_WIDTH = [40, 80, 30, 30, 50, 50]

    def __init__(self, file_path: str):
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            # Création du fichier vide avec les en-têtes
            df = pd.DataFrame(columns=self.COLUMNS)
            # Setup largeur colonnes via ExcelWriter si besoin, mais pour l'init simple:
            df.to_excel(self.file_path, index=False)

    def load_existing_persons(self) -> List[Personne]:
        """Charge tous les profils existants depuis le fichier Excel."""
        if not os.path.exists(self.file_path):
            return []
        
        try:
            df = pd.read_excel(self.file_path)
            # Vérification basique des colonnes pour éviter les crashs si fichier corrompu
            if df.empty or not all(col in df.columns for col in self.COLUMNS):
                return []
            
            persons = []
            for _, row in df.iterrows():
                url = row.get("Lien Linkedin")
                if pd.isna(url) or not isinstance(url, str):
                    continue
                
                try:
                    p = Personne(
                        url=url,
                        nom=row.get("Nom") if pd.notna(row.get("Nom")) else None,
                        titre=row.get("Titre") if pd.notna(row.get("Titre")) else None,
                        societe=row.get("Société") if pd.notna(row.get("Société")) else None,
                        lieu=row.get("Région") if pd.notna(row.get("Région")) else None,
                        source_url=row.get("Source") if pd.notna(row.get("Source")) else None,
                        statut=PersonStatus.ANALYSE_INTERRESSANT # Par défaut, ceux dans le fichier sont intéressants
                    )
                    persons.append(p)
                except Exception as e:
                    print(f"Erreur chargement ligne Excel: {e}")
                    continue
            return persons

        except Exception as e:
            print(f"Erreur lecture Excel: {e}")
            return []

    def save_person(self, p: Personne) -> None:
        """Ajoute une personne au fichier Excel de manière durable."""
        if not p.est_interressante:
            return  # On ne sauvegarde que les intéressants

        new_data = {
            "Nom": p.nom,
            "Titre": p.titre,
            "Société": p.societe,
            "Région": p.lieu,
            "Lien Linkedin": p.url,
            "Source": p.source_url
        }
        df_new = pd.DataFrame([new_data], columns=self.COLUMNS)

        try:
            if os.path.exists(self.file_path):
                # Mode append avec openpyxl pour ne pas tout écraser
                with pd.ExcelWriter(self.file_path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                    # On charge pour trouver la dernière ligne ? 
                    # Pandas append directement est plus simple si on recharge tout, 
                    # mais pour la perf on va append.
                    # Simplification: on relit pour éviter doublons et on réécrit (plus sûr pour petit volume < 1000)
                    df_existing = pd.read_excel(self.file_path)
                    
                    # Vérif doublon URL
                    if p.url in df_existing["Lien Linkedin"].values:
                        # Update (suppression ancienne ligne + ajout nouvelle à la fin)
                        df_existing = df_existing[df_existing["Lien Linkedin"] != p.url]
                    
                    df_final = pd.concat([df_existing, df_new], ignore_index=True)
                    df_final.to_excel(self.file_path, index=False)
            else:
                df_new.to_excel(self.file_path, index=False)
                
        except Exception as e:
            print(f"Erreur sauvegarde Excel: {e}")
            # Fallback ou raise selon besoin
