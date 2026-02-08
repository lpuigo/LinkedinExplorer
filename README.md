# LinkedinExplorer

**LinkedinExplorer** est un assistant intelligent conçu pour automatiser et simplifier la constitution de listes de contacts qualifiés (prospects) à partir de LinkedIn.

L'outil combine la puissance d'un navigateur automatisé (Playwright) pour scanner les profils et une interface graphique ergonomique (PyQt6) pour permettre à l'utilisateur de valider et qualifier chaque contact.

## 🎯 Besoin Fonctionnel

Le principe est d'assister l'utilisateur dans un workflow de prospection :
1.  **Initialisation** : L'utilisateur fournit une URL de profil LinkedIn de départ.
2.  **Analyse & Collecte** : L'outil extrait automatiquement les informations clés (Nom, Titre, Société, Région).
3.  **Qualification Humaine** :
    - L'utilisateur visualise les données dans l'interface.
    - Il décide si le profil est **"Intéressant"** ou non.
    - Les profils intéressants sont automatiquement sauvegardés dans un fichier Excel.
4.  **Exploration (Relations)** : L'utilisateur peut récupérer les "personnes associées" (relations suggérées par LinkedIn) pour alimenter sa file d'attente.
5.  **Pilotage** : Un tableau de bord permet de suivre l'état de la liste (A traiter, En cours, Traité).

## 🏗 Architecture Technique

Le projet respecte les principes du **Clean Code** et une architecture en couches pour garantir maintenabilité et évolutivité.

### Structure des Dossiers
```
app/
├── core/           # Cœur Métier (Indépendant des frameworks externes)
│   ├── models.py       # Modèles de données (Personne, PersonStatus)
│   ├── services.py     # Logique métier (WorkflowManager)
│   └── repository.py   # Interfaces (Port) pour l'accès aux données
├── infra/          # Implémentation technique (Adapters)
│   └── storage/        # Persistence (ExcelRepository avec Pandas/Openpyxl)
├── scraper/        # Couche d'acquisition (Playwright)
│   ├── browser.py      # Contrôle du navigateur
│   └── parsers.py      # Extraction du DOM
├── gui/            # Interface Utilisateur (PyQt6)
│   ├── main_window.py  # Fenêtre principale (Master/Detail)
│   └── dialogs.py      # Dialogues (Ajout, Suggestions)
└── utils/          # Utilitaires transverses
```

### Composants Clés
- **WorkflowManager (`app/core/services.py`)** : Chef d'orchestre de l'application. Gère la file d'attente (Queue), l'état courant, et applique les règles métier (dédoublonnage).
- **ExcelRepository (`app/infra/storage/excel_storage.py`)** : Gère la persistance des profils "Intéressants" dans un fichier Excel (`.xlsx`). Assure la synchronisation au démarrage.
- **LinkedInBrowser & Parser** : Gèrent l'interaction "bas niveau" avec le site web, isolant la complexité de Playwright du reste de l'application.

## ✅ Tests

Le projet inclut des tests unitaires pour valider la logique métier sans dépendre de l'interface graphique ou du navigateur (ce qui les rend rapides et fiables).

Les tests se trouvent dans le dossier `tests/`.

### Lancer les tests
```bash
python -m unittest tests/test_workflow.py
```

### Couverture
Les tests vérifient :
- **Logique de File** : Ajout, passage au suivant (`get_next_person`).
- **Dédoublonnage** : Impossible d'ajouter deux fois la même URL.
- **Persistence** : Vérification que seuls les profils "Intéressants" déclenchent une sauvegarde.
- **Mise à jour** : Propagation des données extraites vers le modèle métier.
