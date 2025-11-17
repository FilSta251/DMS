# -*- coding: utf-8 -*-
"""
Správa kategorií skladu - PROFESIONÁLNÍ
Stromová struktura, CRUD, barvy
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLabel, QMessageBox, QDialog,
    QFormLayout, QLineEdit, QComboBox, QTextEdit, QColorDialog,
    QGroupBox, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush
import config
from database_manager import db


class WarehouseCategoriesWindow(QMainWindow):
    """Okno pro správu kategorií"""

    categories_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("📁 Kategorie skladu")
        self.setMinimumSize(900, 700)

        self.init_ui()
        self.load_categories()

    def init_ui(self):
        """Inicializace UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === HORNÍ LIŠTA ===
        self.create_action_bar(main_layout)

        # === OBSAH ===
        content = QHBoxLayout()

        # Levý panel - strom kategorií
        left_panel = self.create_tree_panel()
        content.addWidget(left_panel, 2)

        # Pravý panel - akce
        right_panel = self.create_actions_panel()
        content.addWidget(right_panel, 1)

        main_layout.addLayout(content)

    def create_action_bar(self, parent_layout):
        """Horní lišta"""
        action_bar = QWidget()
        action_bar.setFixedHeight(60)
        action_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {config.COLOR_PRIMARY};
                border-bottom: 2px solid #2c3e50;
            }}
        """)
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(15, 10, 15, 10)

        # Nadpis
        title = QLabel("📁 KATEGORIE SKLADU")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        action_layout.addWidget(title)

        action_layout.addStretch()

        # Tlačítko zavřít
        btn_close = QPushButton("✕ Zavřít")
        btn_close.setStyleSheet(self.get_button_style("#7f8c8d"))
        btn_close.clicked.connect(self.close)
        action_layout.addWidget(btn_close)

        parent_layout.addWidget(action_bar)

    def create_tree_panel(self):
        """Levý panel se stromem"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Info
        info = QLabel("📂 Stromová struktura kategorií")
        info.setStyleSheet("padding: 10px; background-color: #ecf0f1; font-weight: bold;")
        layout.addWidget(info)

        # Strom
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Název kategorie", "Počet položek", "ID"])
        self.tree.setColumnHidden(2, True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setStyleSheet("""
            QTreeWidget {
                font-size: 13px;
                border: 1px solid #ddd;
            }
            QTreeWidget::item {
                padding: 5px;
            }
            QTreeWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)

        # Kontextové menu
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

        # Double click pro editaci
        self.tree.doubleClicked.connect(self.edit_category)

        layout.addWidget(self.tree)

        return panel

    def create_actions_panel(self):
        """Pravý panel s akcemi"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Info
        info_group = QGroupBox("ℹ️ Informace")
        info_layout = QVBoxLayout(info_group)

        self.lbl_total_categories = QLabel("Celkem kategorií: 0")
        info_layout.addWidget(self.lbl_total_categories)

        self.lbl_total_items = QLabel("Celkem položek: 0")
        info_layout.addWidget(self.lbl_total_items)

        layout.addWidget(info_group)

        # Akce
        actions_group = QGroupBox("⚙️ Akce")
        actions_layout = QVBoxLayout(actions_group)

        # Nová hlavní kategorie
        btn_new_main = QPushButton("➕ Nová hlavní kategorie")
        btn_new_main.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
                text-align: left;
            }}
        """)
        btn_new_main.clicked.connect(self.add_main_category)
        actions_layout.addWidget(btn_new_main)

        # Nová podkategorie
        btn_new_sub = QPushButton("📂 Nová podkategorie")
        btn_new_sub.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
                text-align: left;
            }}
        """)
        btn_new_sub.clicked.connect(self.add_subcategory)
        actions_layout.addWidget(btn_new_sub)

        actions_layout.addSpacing(10)

        # Editovat
        btn_edit = QPushButton("✏️ Editovat vybranou")
        btn_edit.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px;
                border-radius: 5px;
                text-align: left;
            }
        """)
        btn_edit.clicked.connect(self.edit_category)
        actions_layout.addWidget(btn_edit)

        # Smazat
        btn_delete = QPushButton("🗑️ Smazat vybranou")
        btn_delete.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_DANGER};
                color: white;
                padding: 10px;
                border-radius: 5px;
                text-align: left;
            }}
        """)
        btn_delete.clicked.connect(self.delete_category)
        actions_layout.addWidget(btn_delete)

        actions_layout.addStretch()

        layout.addWidget(actions_group)

        # Rychlé přidání vzorových kategorií
        sample_group = QGroupBox("🎨 Vzorové kategorie")
        sample_layout = QVBoxLayout(sample_group)

        sample_label = QLabel("Klikněte pro rychlé vytvoření vzorových kategorií:")
        sample_label.setWordWrap(True)
        sample_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        sample_layout.addWidget(sample_label)

        btn_samples = QPushButton("✨ Vytvořit vzorové kategorie")
        btn_samples.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        btn_samples.clicked.connect(self.create_sample_categories)
        sample_layout.addWidget(btn_samples)

        layout.addWidget(sample_group)

        layout.addStretch()

        return panel

    def get_button_style(self, color):
        """Styl tlačítek"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }}
        """

    def load_categories(self):
        """Načtení kategorií"""
        try:
            self.tree.clear()

            # Načtení všech kategorií
            categories = db.execute_query(
                """SELECT c.id, c.name, c.parent_id, c.color, c.description,
                   COUNT(w.id) as item_count
                   FROM warehouse_categories c
                   LEFT JOIN warehouse w ON w.category_id = c.id
                   GROUP BY c.id, c.name, c.parent_id, c.color, c.description
                   ORDER BY c.name"""
            )

            if not categories:
                self.update_stats(0, 0)
                return

            # Vytvoření mapy kategorií
            category_map = {}
            total_items = 0

            for cat in categories:
                cat_id = cat[0]
                name = cat[1]
                parent_id = cat[2]
                color = cat[3]
                description = cat[4]
                item_count = cat[5]

                total_items += item_count

                # Vytvoření položky
                item = QTreeWidgetItem([name, str(item_count), str(cat_id)])

                # Aplikace barvy
                if color:
                    item.setForeground(0, QBrush(QColor(color)))
                    item.setToolTip(0, description or name)

                category_map[cat_id] = {
                    'item': item,
                    'parent_id': parent_id
                }

            # Sestavení stromu
            for cat_id, cat_data in category_map.items():
                item = cat_data['item']
                parent_id = cat_data['parent_id']

                if parent_id and parent_id in category_map:
                    # Přidání jako podkategorie
                    category_map[parent_id]['item'].addChild(item)
                else:
                    # Přidání jako hlavní kategorie
                    self.tree.addTopLevelItem(item)

            # Rozbalení všech
            self.tree.expandAll()

            # Aktualizace statistik
            self.update_stats(len(categories), total_items)

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při načítání kategorií:\n{str(e)}")

    def update_stats(self, total_categories, total_items):
        """Aktualizace statistik"""
        self.lbl_total_categories.setText(f"Celkem kategorií: {total_categories}")
        self.lbl_total_items.setText(f"Celkem položek: {total_items}")

    def add_main_category(self):
        """Přidání hlavní kategorie"""
        dialog = CategoryDialog(parent=self)
        if dialog.exec():
            self.load_categories()
            self.categories_changed.emit()

    def add_subcategory(self):
        """Přidání podkategorie"""
        # Zjištění vybrané kategorie
        current = self.tree.currentItem()

        if not current:
            QMessageBox.information(
                self,
                "Vyberte kategorii",
                "Nejprve vyberte nadřazenou kategorii"
            )
            return

        parent_id = int(current.text(2))

        dialog = CategoryDialog(parent_id=parent_id, parent=self)
        if dialog.exec():
            self.load_categories()
            self.categories_changed.emit()

    def edit_category(self):
        """Editace kategorie"""
        current = self.tree.currentItem()

        if not current:
            QMessageBox.information(self, "Info", "Vyberte kategorii k editaci")
            return

        category_id = int(current.text(2))

        dialog = CategoryDialog(category_id=category_id, parent=self)
        if dialog.exec():
            self.load_categories()
            self.categories_changed.emit()

    def delete_category(self):
        """Smazání kategorie"""
        current = self.tree.currentItem()

        if not current:
            QMessageBox.information(self, "Info", "Vyberte kategorii ke smazání")
            return

        category_id = int(current.text(2))
        category_name = current.text(0)
        item_count = int(current.text(1))

        # Kontrola podkategorií
        if current.childCount() > 0:
            QMessageBox.warning(
                self,
                "Nelze smazat",
                f"Kategorie '{category_name}' má {current.childCount()} podkategorií.\n\n"
                "Nejprve smažte nebo přesuňte podkategorie."
            )
            return

        # Kontrola položek
        if item_count > 0:
            reply = QMessageBox.question(
                self,
                "Položky v kategorii",
                f"Kategorie '{category_name}' obsahuje {item_count} položek.\n\n"
                "Chcete je přesunout do jiné kategorie nebo smazat kategorii?\n\n"
                "Položky ztratí přiřazení ke kategorii.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                return

        # Potvrzení smazání
        reply = QMessageBox.question(
            self,
            "Smazat kategorii?",
            f"Opravdu smazat kategorii '{category_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Odstranění přiřazení kategorie u položek
                db.execute_query(
                    "UPDATE warehouse SET category_id = NULL WHERE category_id = ?",
                    [category_id]
                )

                # Smazání kategorie
                db.execute_query(
                    "DELETE FROM warehouse_categories WHERE id = ?",
                    [category_id]
                )

                QMessageBox.information(self, "Úspěch", "Kategorie byla smazána")
                self.load_categories()
                self.categories_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Chyba při mazání:\n{str(e)}")

    def show_context_menu(self, position):
        """Kontextové menu"""
        current = self.tree.currentItem()

        if not current:
            return

        menu = QMenu()

        action_edit = menu.addAction("✏️ Editovat")
        action_edit.triggered.connect(self.edit_category)

        action_add_sub = menu.addAction("📂 Přidat podkategorii")
        action_add_sub.triggered.connect(self.add_subcategory)

        menu.addSeparator()

        action_delete = menu.addAction("🗑️ Smazat")
        action_delete.triggered.connect(self.delete_category)

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def create_sample_categories(self):
        """Vytvoření vzorových kategorií"""
        reply = QMessageBox.question(
            self,
            "Vytvořit vzorové kategorie?",
            "Chcete vytvořit vzorové kategorie pro automobilový servis?\n\n"
            "Budou vytvořeny hlavní kategorie s podkategoriemi.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        try:
            # Kontrola, zda už existují kategorie
            existing = db.execute_query("SELECT COUNT(*) FROM warehouse_categories")
            if existing and existing[0][0] > 0:
                reply2 = QMessageBox.question(
                    self,
                    "Existující kategorie",
                    "Již máte vytvořené kategorie. Chcete přesto pokračovat?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply2 == QMessageBox.StandardButton.No:
                    return

            # Vzorové kategorie
            samples = [
                {
                    'name': 'Díly motoru',
                    'color': '#e74c3c',
                    'description': 'Součásti motorů a příslušenství',
                    'subcategories': [
                        'Filtry',
                        'Těsnění',
                        'Řemeny a řetězy',
                        'Zapalovací svíčky',
                        'Píst a válec'
                    ]
                },
                {
                    'name': 'Elektrické díly',
                    'color': '#3498db',
                    'description': 'Elektroinstalace a elektronika',
                    'subcategories': [
                        'Žárovky',
                        'Baterie',
                        'Startéry a alternátory',
                        'Pojistky',
                        'Kabely'
                    ]
                },
                {
                    'name': 'Karoserie',
                    'color': '#95a5a6',
                    'description': 'Karosářské díly',
                    'subcategories': [
                        'Blatníky',
                        'Zrcátka',
                        'Světla',
                        'Nárazníky'
                    ]
                },
                {
                    'name': 'Brzdový systém',
                    'color': '#e67e22',
                    'description': 'Brzdy a související díly',
                    'subcategories': [
                        'Brzdové destičky',
                        'Brzdové kotouče',
                        'Brzdová kapalina',
                        'Brzdové hadice'
                    ]
                },
                {
                    'name': 'Oleje a kapaliny',
                    'color': '#27ae60',
                    'description': 'Provozní kapaliny',
                    'subcategories': [
                        'Motorové oleje',
                        'Převodové oleje',
                        'Chladicí kapaliny',
                        'Nemrznoucí směsi'
                    ]
                },
                {
                    'name': 'Chemie',
                    'color': '#9b59b6',
                    'description': 'Chemické přípravky',
                    'subcategories': [
                        'Čističe',
                        'Maziva',
                        'Těsnící tmely',
                        'WD-40 a podobné'
                    ]
                },
                {
                    'name': 'Pneumatiky',
                    'color': '#34495e',
                    'description': 'Pneumatiky a příslušenství',
                    'subcategories': [
                        'Letní pneumatiky',
                        'Zimní pneumatiky',
                        'Celoroční pneumatiky',
                        'Ráfky'
                    ]
                }
            ]

            # Vytvoření kategorií
            for sample in samples:
                # Hlavní kategorie
                cursor = db.execute_query(
                    """INSERT INTO warehouse_categories (name, parent_id, color, description)
                       VALUES (?, NULL, ?, ?)""",
                    [sample['name'], sample['color'], sample['description']]
                )

                parent_id = cursor.lastrowid if hasattr(cursor, 'lastrowid') else None

                # Podkategorie
                if parent_id and 'subcategories' in sample:
                    for subcat in sample['subcategories']:
                        db.execute_query(
                            """INSERT INTO warehouse_categories (name, parent_id, color, description)
                               VALUES (?, ?, ?, ?)""",
                            [subcat, parent_id, sample['color'], f"Podkategorie: {subcat}"]
                        )

            QMessageBox.information(
                self,
                "Úspěch",
                f"Vytvořeno {len(samples)} hlavních kategorií s podkategoriemi!"
            )

            self.load_categories()
            self.categories_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při vytváření:\n{str(e)}")


class CategoryDialog(QDialog):
    """Dialog pro přidání/editaci kategorie"""

    def __init__(self, category_id=None, parent_id=None, parent=None):
        super().__init__(parent)
        self.category_id = category_id
        self.parent_id = parent_id
        self.is_new = category_id is None
        self.selected_color = "#3498db"

        if self.is_new:
            if parent_id:
                self.setWindowTitle("📂 Nová podkategorie")
            else:
                self.setWindowTitle("➕ Nová hlavní kategorie")
        else:
            self.setWindowTitle("✏️ Editace kategorie")

        self.setModal(True)
        self.setMinimumWidth(500)

        self.init_ui()

        if not self.is_new:
            self.load_category_data()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # Hlavička
        if self.parent_id:
            header_text = "📂 NOVÁ PODKATEGORIE"
        elif self.is_new:
            header_text = "➕ NOVÁ HLAVNÍ KATEGORIE"
        else:
            header_text = "✏️ EDITACE KATEGORIE"

        header = QLabel(header_text)
        header.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {config.COLOR_PRIMARY};
            padding: 15px;
            background-color: #ecf0f1;
            border-radius: 5px;
        """)
        layout.addWidget(header)

        # Formulář
        form = QFormLayout()

        # Název
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Název kategorie...")
        form.addRow("Název *:", self.input_name)

        # Nadřazená kategorie (jen pokud editace)
        if not self.is_new or self.parent_id is None:
            self.combo_parent = QComboBox()
            self.load_parent_categories()
            form.addRow("Nadřazená kategorie:", self.combo_parent)

        # Barva
        color_layout = QHBoxLayout()

        self.lbl_color_preview = QLabel("     ")
        self.lbl_color_preview.setStyleSheet(f"""
            background-color: {self.selected_color};
            border: 2px solid #ddd;
            border-radius: 3px;
        """)
        color_layout.addWidget(self.lbl_color_preview)

        btn_choose_color = QPushButton("Vybrat barvu")
        btn_choose_color.clicked.connect(self.choose_color)
        color_layout.addWidget(btn_choose_color)

        color_layout.addStretch()

        form.addRow("Barva:", color_layout)

        # Popis
        self.text_description = QTextEdit()
        self.text_description.setMaximumHeight(80)
        self.text_description.setPlaceholderText("Volitelný popis kategorie...")
        form.addRow("Popis:", self.text_description)

        layout.addLayout(form)

        # Tlačítka
        buttons = QHBoxLayout()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾 Uložit")
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 12px 30px;
                border-radius: 5px;
                font-weight: bold;
            }}
        """)
        btn_save.clicked.connect(self.save)

        buttons.addStretch()
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

    def load_parent_categories(self):
        """Načtení nadřazených kategorií"""
        try:
            self.combo_parent.clear()
            self.combo_parent.addItem("-- Žádná (hlavní kategorie) --", None)

            # Načtení jen hlavních kategorií (bez parent_id)
            categories = db.execute_query(
                "SELECT id, name FROM warehouse_categories WHERE parent_id IS NULL ORDER BY name"
            )

            if categories:
                for cat in categories:
                    # Přeskočit sebe sama při editaci
                    if not self.is_new and cat[0] == self.category_id:
                        continue
                    self.combo_parent.addItem(cat[1], cat[0])

        except Exception as e:
            print(f"Chyba: {e}")

    def load_category_data(self):
        """Načtení dat kategorie"""
        try:
            cat = db.execute_query(
                "SELECT name, parent_id, color, description FROM warehouse_categories WHERE id = ?",
                [self.category_id]
            )

            if not cat:
                return

            self.input_name.setText(cat[0][0])

            if hasattr(self, 'combo_parent'):
                if cat[0][1]:
                    index = self.combo_parent.findData(cat[0][1])
                    if index >= 0:
                        self.combo_parent.setCurrentIndex(index)

            if cat[0][2]:
                self.selected_color = cat[0][2]
                self.lbl_color_preview.setStyleSheet(f"""
                    background-color: {self.selected_color};
                    border: 2px solid #ddd;
                    border-radius: 3px;
                """)

            self.text_description.setPlainText(cat[0][3] or "")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba:\n{str(e)}")

    def choose_color(self):
        """Výběr barvy"""
        color = QColorDialog.getColor(QColor(self.selected_color), self, "Vyberte barvu kategorie")

        if color.isValid():
            self.selected_color = color.name()
            self.lbl_color_preview.setStyleSheet(f"""
                background-color: {self.selected_color};
                border: 2px solid #ddd;
                border-radius: 3px;
            """)

    def save(self):
        """Uložení kategorie"""
        if not self.input_name.text():
            QMessageBox.warning(self, "Chyba", "Vyplňte název kategorie!")
            self.input_name.setFocus()
            return

        try:
            name = self.input_name.text()
            description = self.text_description.toPlainText()

            # Určení parent_id
            if self.parent_id:
                # Pevně nastavená podkategorie
                parent_id = self.parent_id
            elif hasattr(self, 'combo_parent'):
                # Z combo boxu
                parent_id = self.combo_parent.currentData()
            else:
                parent_id = None

            if self.is_new:
                # Nová kategorie
                db.execute_query(
                    """INSERT INTO warehouse_categories (name, parent_id, color, description)
                       VALUES (?, ?, ?, ?)""",
                    [name, parent_id, self.selected_color, description]
                )
                QMessageBox.information(self, "Úspěch", "Kategorie byla přidána")
            else:
                # Aktualizace
                db.execute_query(
                    """UPDATE warehouse_categories
                       SET name=?, parent_id=?, color=?, description=?
                       WHERE id=?""",
                    [name, parent_id, self.selected_color, description, self.category_id]
                )
                QMessageBox.information(self, "Úspěch", "Kategorie byla aktualizována")

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při ukládání:\n{str(e)}")
