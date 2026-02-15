from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
                             QTableWidget, QTableWidgetItem, QLabel, QLineEdit, QCheckBox, QSplitter,
                             QFormLayout, QFrame, QHeaderView, QAbstractItemView, QDialog)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QColor, QBrush, QFont, QCloseEvent

from app.gui.dialogs import AddProfileDialog
from app.core.services import WorkflowManager
from app.core.models import Personne
import qasync
import asyncio
from app.gui.dialog_suggestion_validate import SuggestionsDialog

from app.core.browser_service import BrowserService

class MainWindow(QMainWindow):
    """Fenêtre principale combinant le tableau de bord et le navigateur de profils."""
    def __init__(self, workflow: WorkflowManager, browser: BrowserService, config: Dict[str, Any]) -> None:
        super().__init__()
        self.workflow = workflow
        self.browser = browser
        self.config = config
        self._init_ui()
        self.refresh_table()

    def _init_ui(self) -> None:
        self.setWindowTitle("LinkedIn Explorer")
        self.resize(1200, 800)

        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter pour séparer gauche (Tableau) et droite (Détail)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Partie GAUCHE : Tableau ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Bouton Ajouter
        self.btn_add = QPushButton("➕ Ajouter un profil")
        self.btn_add.clicked.connect(self._show_add_dialog)
        left_layout.addWidget(self.btn_add)

        # Tableau
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Nom", "Titre", "Région", "Société", "Intérêt"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.cellClicked.connect(self._on_table_click)
        left_layout.addWidget(self.table)

        splitter.addWidget(left_widget)

        # --- Partie DROITE : Détail ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        title_label = QLabel("Détail du profil en cours")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        right_layout.addWidget(title_label)

        # Formulaire
        self.form_layout = QFormLayout()
        
        self.chk_interest = QCheckBox("Personne Intéressante")
        self.chk_interest.clicked.connect(self._on_interest_changed)
        
        self.edit_nom = QLineEdit()
        self.edit_titre = QLineEdit()
        self.edit_region = QLineEdit()
        self.edit_societe = QLineEdit()
        self.edit_nom.editingFinished.connect(self._on_field_changed)
        self.edit_titre.editingFinished.connect(self._on_field_changed)
        self.edit_region.editingFinished.connect(self._on_field_changed)
        self.edit_societe.editingFinished.connect(self._on_field_changed)
        self.edit_url = QLineEdit()
        self.edit_url.setReadOnly(True)

        self.form_layout.addRow("Intérêt :", self.chk_interest)
        self.form_layout.addRow("URL :", self.edit_url)
        self.form_layout.addRow("Nom :", self.edit_nom)
        self.form_layout.addRow("Titre :", self.edit_titre)
        self.form_layout.addRow("Région :", self.edit_region)
        self.form_layout.addRow("Société :", self.edit_societe)
        
        right_layout.addLayout(self.form_layout)

        # Boutons d'action
        actions_layout = QHBoxLayout()
        self.btn_relations = QPushButton("Relations...")
        self.btn_relations.clicked.connect(self._open_relations_dialog)
        self.btn_next = QPushButton("Personne suivante")
        self.btn_next.clicked.connect(self.process_next)
        
        actions_layout.addWidget(self.btn_relations)
        actions_layout.addWidget(self.btn_next)
        right_layout.addLayout(actions_layout)
        
        right_layout.addStretch()
        splitter.addWidget(right_widget)

        # Répartition initiale 60% / 40%
        splitter.setSizes([700, 500])
        
        main_layout.addWidget(splitter)
        self.setCentralWidget(central_widget)
        
        # Désactiver les contrôles de droite si pas de personne en cours
        self._set_detail_enabled(False)

    def closeEvent(self, event: QCloseEvent):
        """Détecte la fermeture explicite de la fenêtre par l'utilisateur."""
        print("L'utilisateur a fermé la fenêtre principale.")
        event.accept()

    def _on_field_changed(self):
        """Appelé quand un champ texte perd le focus après modification."""
        if not self.workflow.current_person:
            return

        # Mise à jour du modèle avec les valeurs du formulaire
        info = {
            'nom': self.edit_nom.text(),
            'titre': self.edit_titre.text(),
            'lieu': self.edit_region.text(),
            'societe': self.edit_societe.text()
        }
        
        # On met à jour les infos SANS sauvegarder automatiquement (car interesting va passer à False)
        # Mais pour cela on doit modifier directement les attributs ou utiliser une méthode dédiée
        # qui ne déclenche pas le save si interesting est déjà vrai.
        # Ici on veut FORCER la revalidation, donc on passe interesting à False.
        
        # 1. Mise à jour des données
        self.workflow.update_current_person_info(info)
        
        # 2. Reset de l'état "Intéressante" => False
        # Cela force l'utilisateur à recocher pour sauvegarder
        self.chk_interest.setChecked(False)
        self.workflow.set_current_person_decision(False)
        
        self.refresh_table()

    def _set_detail_enabled(self, enabled: bool):
        self.chk_interest.setEnabled(enabled)
        self.edit_nom.setEnabled(enabled)
        self.edit_titre.setEnabled(enabled)
        self.edit_region.setEnabled(enabled)
        self.edit_societe.setEnabled(enabled)
        self.btn_relations.setEnabled(enabled)
        # Url toujours read-only mais potentiellement disabled visuellement
        self.edit_url.setEnabled(enabled)

    def refresh_table(self):
        """Reconstruit le tableau de gauche avec les données courantes du workflow."""
        self.table.setRowCount(0)
        persons = list(self.workflow.all_persons.values())
        self.table.setRowCount(len(persons))
        
        current_p = self.workflow.current_person

        for i, p in enumerate(persons):
            self.table.setItem(i, 0, QTableWidgetItem(p.nom or ""))
            self.table.setItem(i, 1, QTableWidgetItem(p.titre or ""))
            self.table.setItem(i, 2, QTableWidgetItem(p.lieu or ""))
            self.table.setItem(i, 3, QTableWidgetItem(p.societe or ""))
            
            interet_str = "OUI" if p.interesting else "NON"
            self.table.setItem(i, 4, QTableWidgetItem(interet_str))
            
            # Styling
            color = Qt.GlobalColor.white
            text_color = Qt.GlobalColor.black
            font = QFont()

            # Gestion des couleurs par état (analysed / interesting)
            if p.analyzed:
                if p.interesting:
                    color = QColor("#D1E7DD") # Vert clair
                else:
                    color = QColor("#F0F0F0") # Gris clair
                    text_color = QColor("gray")
            else:
                color = Qt.GlobalColor.white

            # Gestion de la mise en avant de la personne courante (UI state)
            if p == current_p:
                font.setBold(True)
                # On peut aussi changer la couleur de fond pour surligner la ligne active
                # si elle n'a pas encore de couleur spécifique (ou on mixe ?)
                if color == Qt.GlobalColor.white:
                     color = QColor("#E0F7FA") # Cyan clair pour la sélection courante

            for col in range(5):
                item = self.table.item(i, col)
                item.setBackground(QBrush(color))
                item.setForeground(QBrush(text_color))
                item.setFont(font)
                # Stocker l'URL dans le premier item pour retrouver la personne
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, p.url)
        
        # Mise à jour de l'état du bouton "Personne suivante"
        self.btn_next.setEnabled(self.workflow.has_pending_persons())

    def _update_detail_view(self):
        p = self.workflow.current_person
        if not p:
            self._set_detail_enabled(False)
            self.edit_nom.setText("")
            self.edit_titre.setText("")
            self.edit_region.setText("")
            self.edit_societe.setText("")
            self.edit_url.setText("")
            self.chk_interest.setChecked(False)
            return

        self._set_detail_enabled(True)
        self.edit_nom.setText(p.nom or "")
        self.edit_titre.setText(p.titre or "")
        self.edit_region.setText(p.lieu or "")
        self.edit_societe.setText(p.societe or "")
        self.edit_url.setText(p.url)
        self.chk_interest.setChecked(p.interesting)

    def _show_add_dialog(self) -> None:
        dialog = AddProfileDialog(self)
        if dialog.exec():
            url = dialog.get_url()
            if url:
                added_p = self.workflow.add_person(url)
                if added_p:
                    self.refresh_table()
                else:
                    QMessageBox.information(self, "Doublon", "Ce profil est déjà dans la liste.")

    @qasync.asyncSlot(int, int)
    async def _on_table_click(self, row, col):
        """Gère le clic sur une ligne du tableau : charge le profil associé."""
        item = self.table.item(row, 0)
        url = item.data(Qt.ItemDataRole.UserRole)
        new_person = self.workflow.all_persons.get(url)
        
        if new_person:
            self._select_person(new_person)

    def _select_person(self, person: Personne):
        """Sélectionne une personne, met à jour l'UI et lance le traitement background."""
        # Quand une personne devient active, elle est considérée comme analysée
        if not person.analyzed:
            person.analyzed = True
            
        if person != self.workflow.current_person:
             self.workflow.current_person = person
             self._update_detail_view()
             self.refresh_table()
             asyncio.create_task(self._process_profile_background(person))

    async def _process_profile_background(self, p: Personne):
        """Charge la page et le profil en arrière-plan."""
        try:
            # Utilisation du service abstrait pour récupérer les données
            infos = await self.browser.get_profile_data(p.url)
            self.workflow.update_current_person_info(infos)

            # Mise à jour finale de l'UI avec les nouvelles données
            # On vérifie si c'est toujours la personne courante pour éviter des clignotements bizarres
            # si l'utilisateur a cliqué ailleurs entre temps
            if self.workflow.current_person == p:
                 self._update_detail_view()
            
            self.refresh_table() # Mise à jour globale (titre, société, etc.)
        except Exception as e:
            print(f"Erreur background process pour {p.url}: {e}")

    def _on_interest_changed(self):
        is_checked = self.chk_interest.isChecked()
        self.workflow.set_current_person_decision(is_checked)
        self.refresh_table()

    @qasync.asyncSlot()
    async def process_next(self):
        p = self.workflow.get_next_person()
        if p:
            self._select_person(p)
        else:
            QMessageBox.information(self, "Info", "Plus de personnes à traiter dans la file.")

    @qasync.asyncSlot()
    async def _open_relations_dialog(self):
        if not self.workflow.current_person:
            return

        # 1. Création de la fenêtre (avec message d'attente)
        dialog = SuggestionsDialog(None, self.workflow, self.config)
        dialog.set_loading(True)
        
        # 2. Utilisation d'un Future pour attendre la fermeture du dialog
        dialog_future = asyncio.Future()
        
        def on_dialog_finished(result):
             if not dialog_future.done():
                dialog_future.set_result(result)
        
        dialog.finished.connect(on_dialog_finished)
        dialog.open() # Non-blocking (window modal)

        # 3. Lancement du traitement asynchrone (scraping)
        # On définit une coroutine locale qui va faire le travail et mettre à jour le dialog
        async def load_relations():
            try:
                suggestions = await self.browser.get_relations()
                
                # Mise à jour du dialog
                dialog.update_suggestions(suggestions)
                dialog.set_loading(False)
            except Exception as e:
                print(f"Erreur lors du chargement des relations: {e}")
                dialog.set_loading(False)
                # Optionnel: afficher erreur dans le dialog ?

        # On planifie la tâche pour qu'elle s'exécute pendant que le dialog est ouvert
        asyncio.create_task(load_relations())

        # 4. Attente de la fermeture du dialog
        result = await dialog_future
        
        if result == QDialog.DialogCode.Accepted:
            selected = dialog.get_selected()
            count = 0
            for s in selected:
                res = self.workflow.add_person(s['url'], source_url=self.workflow.current_person.url,
                                         nom=s['nom'], titre=s['titre'])
                if res: count += 1
            
            self.refresh_table()
            QMessageBox.information(self, "Ajout", f"{count} nouvelles relations ajoutées à la file.")