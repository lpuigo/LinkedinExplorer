from typing import Optional
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QLabel, QMessageBox, QWidget)
from PyQt6.QtCore import Qt

class AddProfileDialog(QDialog):
    """Dialogue modal pour l'ajout manuel d'un profil LinkedIn via son URL."""
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.result_url: Optional[str] = None
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("Ajouter un profil LinkedIn")
        self.setFixedWidth(500)

        layout = QVBoxLayout(self)

        # Label d'instruction
        self.label = QLabel("Saisissez l'URL du profil LinkedIn :")
        layout.addWidget(self.label)

        # Champ de saisie
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.linkedin.com/in/nom-prenom-12345/")
        layout.addWidget(self.url_input)

        # Message d'erreur (caché par défaut)
        self.error_label = QLabel("Format d'URL invalide")
        self.error_label.setStyleSheet("color: red; font-size: 10px;")
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        # Boutons
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Ajouter")
        self.btn_cancel = QPushButton("Annuler")

        self.btn_add.clicked.connect(self._validate_and_accept)
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def _validate_and_accept(self) -> None:
        raw_url: str = self.url_input.text().strip()
        prefix: str = "https://www.linkedin.com/in/"

        # 1. Contrôle du format
        if not raw_url.startswith(prefix):
            self.error_label.setText(f"L'URL doit commencer par {prefix}")
            self.error_label.setVisible(True)
            return

        # 2. Nettoyage de l'URL (suppression des paramètres après le ?)
        # Exemple: .../in/john-doe/?miniProfileUrn... -> .../in/john-doe/
        clean_url: str = raw_url.split('?')[0]

        # On s'assure qu'il reste quelque chose après le préfixe
        if len(clean_url) <= len(prefix):
            self.error_label.setText("L'URL semble incomplète.")
            self.error_label.setVisible(True)
            return

        self.result_url = clean_url
        self.accept()

    def get_url(self) -> Optional[str]:
        """Retourne l'URL saisie et validée."""
        return self.result_url