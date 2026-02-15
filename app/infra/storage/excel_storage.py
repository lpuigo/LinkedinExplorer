import pandas as pd
import os
from typing import List
from app.core.models import Personne
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
                        analyzed=True,
                        interesting=True
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
        """Ajoute ou met à jour une personne dans le fichier Excel."""
        if not p.interesting:
            return  # On ne sauvegarde que les intéressants

        new_row = {
            "Nom": p.nom,
            "Titre": p.titre,
            "Société": p.societe,
            "Région": p.lieu,
            "Lien Linkedin": p.url,
            "Source": p.source_url
        }
        
        try:
            if os.path.exists(self.file_path):
                df_existing = pd.read_excel(self.file_path)
            else:
                df_existing = pd.DataFrame(columns=self.COLUMNS)
                
            # Conversion en DataFrame pour la nouvelle ligne
            df_new = pd.DataFrame([new_row])
            
            # Si l'URL existe déjà, on supprime l'ancienne entrée pour la remplacer
            if "Lien Linkedin" in df_existing.columns and not df_existing.empty:
                 if p.url in df_existing["Lien Linkedin"].values:
                     df_existing = df_existing[df_existing["Lien Linkedin"] != p.url]
            
            # Concaténation
            df_final = pd.concat([df_existing, df_new], ignore_index=True)
            
            # Sauvegarde
            with pd.ExcelWriter(self.file_path, engine='openpyxl', mode='w') as writer:
                df_final.to_excel(writer, index=False)
                
        except Exception as e:
            print(f"Erreur sauvegarde Excel: {e}")

    def remove_person(self, p: Personne) -> None:
        """Supprime une personne du fichier Excel."""
        if not os.path.exists(self.file_path):
            return

        try:
            df = pd.read_excel(self.file_path)
            if p.url in df["Lien Linkedin"].values:
                df = df[df["Lien Linkedin"] != p.url]
                df.to_excel(self.file_path, index=False)
        except Exception as e:
            print(f"Erreur suppression Excel: {e}")

    def exists(self) -> bool:
        """Vérifie si le fichier Excel existe."""
        return os.path.exists(self.file_path)

    def save_all(self, persons: List[Personne]) -> None:
        """Recrée le fichier Excel avec la liste complète des personnes fournies."""
        data = []
        for p in persons:
            if not p.interesting:
                continue
                
            data.append({
                "Nom": p.nom,
                "Titre": p.titre,
                "Société": p.societe,
                "Région": p.lieu,
                "Lien Linkedin": p.url,
                "Source": p.source_url
            })
            
        df = pd.DataFrame(data, columns=self.COLUMNS)
        try:
            # On écrase tout le fichier
            df.to_excel(self.file_path, index=False)
        except Exception as e:
            print(f"Erreur recréation Excel: {e}")
