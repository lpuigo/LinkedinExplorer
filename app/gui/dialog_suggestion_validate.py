from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QCheckBox, QAbstractItemView, QHeaderView, QWidget,
    QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QFont

from app.core.services import WorkflowManager

class SuggestionsDialog(QDialog):
    """Boîte de dialogue permettant de valider les suggestions de nouvelles relations."""
    def __init__(self, suggestions: List[Dict], workflow: WorkflowManager, config: Dict[str, Any]):
        super().__init__()
        self.suggestions = suggestions if suggestions is not None else []
        self.workflow = workflow
        self.config = config
        self.selected_items = []
        
        self.setWindowTitle("Valider les nouvelles relations")
        self.resize(800, 600)
        self._init_ui()

    def set_loading(self, loading: bool):
        """Active ou désactive l'état de chargement."""
        self.table.setVisible(not loading)
        self.btn_add.setEnabled(not loading)
        if loading:
            self.loading_label.show()
        else:
            self.loading_label.hide()

    def update_suggestions(self, suggestions: List[Dict]):
        """Met à jour la liste des suggestions et rafraîchit le tableau."""
        self.suggestions = suggestions
        self._populate_table()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Tableau
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Nom", "Titre", "A Analyser"])
        
        # Permettre à l'utilisateur de modifier la largeur des colonnes
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(False) # On évite stretch auto pour laisser la main
        
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 400) # Largeur par défaut pour le titre
        self.table.setColumnWidth(2, 100)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.table)

        # Label de chargement
        self.loading_label = QLabel("Analyse en cours...", self)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.loading_label.setFont(font)
        layout.addWidget(self.loading_label)
        self.loading_label.hide() # Caché par défaut
        
        # Remplissage
        self._populate_table()

        # Boutons
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Ajouter à la liste")
        self.btn_add.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def _populate_table(self):
        self.table.setRowCount(0)
        if not self.suggestions:
            return

        self.table.setRowCount(len(self.suggestions))
        keywords = self.config.get('filters', {}).get('keywords', [])

        for i, s in enumerate(self.suggestions):
            nom = s.get('nom', '')
            titre = s.get('titre', '')
            url = s.get('url', '') # Devrait être nettoyée
            
            # 1. Nom & Titre
            item_nom = QTableWidgetItem(nom)
            item_titre = QTableWidgetItem(titre)
            
            self.table.setItem(i, 0, item_nom)
            self.table.setItem(i, 1, item_titre)
            
            # 2. Checkbox "A Analyser"
            # Widget conteneur pour centrer la checkbox
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk = QCheckBox()
            chk_layout.addWidget(chk)
            
            # Logique d'intérêt
            is_interesting = any(kw.lower() in titre.lower() for kw in keywords)
            chk.setChecked(is_interesting)
            
            # Logique doublon
            if url in self.workflow.all_persons:
                chk.setChecked(False)
                chk.setEnabled(False)
                # Griser la ligne
                item_nom.setBackground(QBrush(QColor("#F0F0F0")))
                item_nom.setForeground(QBrush(QColor("gray")))
                item_titre.setBackground(QBrush(QColor("#F0F0F0")))
                item_titre.setForeground(QBrush(QColor("gray")))
            else:
                if is_interesting:
                    item_nom.setBackground(QBrush(QColor("#E8F5E9"))) # Vert très clair
            
            self.table.setCellWidget(i, 2, chk_widget)
            # On stocke la réf à la checkbox pour récupération
            self.table.setItem(i, 2, QTableWidgetItem()) # Item vide pour la structure
            self.table.item(i, 2).setData(Qt.ItemDataRole.UserRole, chk) # Hacky mais efficace

    def get_selected(self) -> List[Dict]:
        """Retourne la liste des suggestions cochées par l'utilisateur."""
        selected = []
        for i in range(self.table.rowCount()):
            # Récupération de la checkbox via le widget cell
            widget = self.table.cellWidget(i, 2)
            if widget:
                 # Le layout contient la checkbox à l'index 0
                chk = widget.findChild(QCheckBox)
                if chk and chk.isChecked():
                    selected.append(self.suggestions[i])
        return selected