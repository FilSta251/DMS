# -*- coding: utf-8 -*-
"""
Modul Číselníky - Značky vozidel (PRODUKČNÍ VERZE)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QFrame,
                             QComboBox, QLineEdit, QHeaderView, QMessageBox,
                             QDialog, QFormLayout, QCheckBox, QFileDialog,
                             QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QIcon
from datetime import datetime
import csv
import config
from database_manager import db


class BrandsWidget(QWidget):
    """Widget pro správu značek vozidel"""

    data_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Horní panel s akcemi
        top_panel = self.create_top_panel()
        layout.addWidget(top_panel)

        # Filtr
        filter_panel = self.create_filter_panel()
        layout.addWidget(filter_panel)

        # Tabulka
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Název", "Typ", "Oblíbená", "Aktivní", "Akce"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 60)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 80)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 80)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 150)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # Spodní panel s informacemi
        bottom_panel = self.create_bottom_panel()
        layout.addWidget(bottom_panel)

    def create_top_panel(self):
        """Vytvoření horního panelu s akcemi"""
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tlačítka
        add_btn = QPushButton("➕ Přidat značku")
        add_btn.clicked.connect(self.add_brand)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 4px;
            }}
        """)
        layout.addWidget(add_btn)

        import_btn = QPushButton("📥 Import CSV")
        import_btn.clicked.connect(self.import_csv)
        layout.addWidget(import_btn)

        export_btn = QPushButton("📤 Export CSV")
        export_btn.clicked.connect(self.export_csv)
        layout.addWidget(export_btn)

        reset_btn = QPushButton("🔄 Obnovit výchozí")
        reset_btn.clicked.connect(self.reset_to_default)
        layout.addWidget(reset_btn)

        layout.addStretch()

        # Vyhledávání
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Vyhledat značku...")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self.filter_data)
        layout.addWidget(self.search_input)

        return frame

    def create_filter_panel(self):
        """Vytvoření panelu filtrů"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        layout = QHBoxLayout(frame)

        # Filtr typu
        layout.addWidget(QLabel("Typ:"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("Všechny typy", "all")
        self.type_filter.addItem("🚗 Auto", "auto")
        self.type_filter.addItem("🏍️ Motocykl", "moto")
        self.type_filter.addItem("🚗🏍️ Obojí", "both")
        self.type_filter.currentIndexChanged.connect(self.filter_data)
        layout.addWidget(self.type_filter)

        # Filtr aktivní
        layout.addWidget(QLabel("Stav:"))
        self.active_filter = QComboBox()
        self.active_filter.addItem("Všechny", "all")
        self.active_filter.addItem("✅ Aktivní", "active")
        self.active_filter.addItem("❌ Neaktivní", "inactive")
        self.active_filter.currentIndexChanged.connect(self.filter_data)
        layout.addWidget(self.active_filter)

        # Filtr oblíbené
        self.favorite_only = QCheckBox("Pouze oblíbené ⭐")
        self.favorite_only.stateChanged.connect(self.filter_data)
        layout.addWidget(self.favorite_only)

        layout.addStretch()

        # Řazení
        layout.addWidget(QLabel("Řadit:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Abecedně A-Z", "name_asc")
        self.sort_combo.addItem("Abecedně Z-A", "name_desc")
        self.sort_combo.addItem("Oblíbené první", "favorite")
        self.sort_combo.addItem("Podle typu", "type")
        self.sort_combo.currentIndexChanged.connect(self.load_data)
        layout.addWidget(self.sort_combo)

        return frame

    def create_bottom_panel(self):
        """Vytvoření spodního panelu"""
        frame = QFrame()
        layout = QHBoxLayout(frame)

        self.count_label = QLabel("Celkem: 0 značek")
        self.count_label.setStyleSheet("color: #7f8c8d; font-size: 11pt;")
        layout.addWidget(self.count_label)

        layout.addStretch()

        self.last_update_label = QLabel("")
        self.last_update_label.setStyleSheet("color: #95a5a6; font-size: 10pt;")
        layout.addWidget(self.last_update_label)

        return frame

    # =====================================================
    # CRUD OPERACE
    # =====================================================

    def load_data(self):
        """Načtení dat z databáze"""
        try:
            # Sestavení dotazu s řazením
            sort_option = self.sort_combo.currentData() if hasattr(self, 'sort_combo') else "name_asc"

            order_by = "name ASC"
            if sort_option == "name_desc":
                order_by = "name DESC"
            elif sort_option == "favorite":
                order_by = "is_favorite DESC, name ASC"
            elif sort_option == "type":
                order_by = "vehicle_type, name ASC"

            query = f"""
                SELECT id, name, vehicle_type, is_favorite, active
                FROM codebook_brands
                ORDER BY {order_by}
            """
            brands = db.fetch_all(query)

            self.all_data = brands
            self.filter_data()

            self.last_update_label.setText(f"Poslední aktualizace: {datetime.now().strftime('%H:%M:%S')}")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst data:\n{e}")

    def filter_data(self):
        """Filtrování dat podle kritérií"""
        if not hasattr(self, 'all_data'):
            return

        filtered = self.all_data

        # Filtr podle textu
        search_text = self.search_input.text().lower().strip()
        if search_text:
            filtered = [b for b in filtered if search_text in b["name"].lower()]

        # Filtr podle typu
        type_filter = self.type_filter.currentData()
        if type_filter != "all":
            filtered = [b for b in filtered if b["vehicle_type"] == type_filter]

        # Filtr podle stavu
        active_filter = self.active_filter.currentData()
        if active_filter == "active":
            filtered = [b for b in filtered if b["active"] == 1]
        elif active_filter == "inactive":
            filtered = [b for b in filtered if b["active"] == 0]

        # Filtr pouze oblíbené
        if self.favorite_only.isChecked():
            filtered = [b for b in filtered if b["is_favorite"] == 1]

        self.display_data(filtered)

    def display_data(self, data):
        """Zobrazení dat v tabulce"""
        self.table.setRowCount(len(data))

        for row, brand in enumerate(data):
            # ID
            id_item = QTableWidgetItem(str(brand["id"]))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, id_item)

            # Název
            name_item = QTableWidgetItem(brand["name"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, name_item)

            # Typ
            type_labels = {
                "auto": "🚗 Auto",
                "moto": "🏍️ Motocykl",
                "both": "🚗🏍️ Obojí"
            }
            type_item = QTableWidgetItem(type_labels.get(brand["vehicle_type"], brand["vehicle_type"]))
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, type_item)

            # Oblíbená
            fav_item = QTableWidgetItem("⭐" if brand["is_favorite"] else "")
            fav_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            fav_item.setFlags(fav_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, fav_item)

            # Aktivní
            active_item = QTableWidgetItem("✅" if brand["active"] else "❌")
            active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            active_item.setFlags(active_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if not brand["active"]:
                active_item.setForeground(QColor("#e74c3c"))
            self.table.setItem(row, 4, active_item)

            # Akce
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.setSpacing(5)

            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Upravit")
            edit_btn.setFixedSize(30, 30)
            edit_btn.clicked.connect(lambda checked, b=brand: self.edit_brand(b))
            actions_layout.addWidget(edit_btn)

            fav_btn = QPushButton("⭐" if not brand["is_favorite"] else "☆")
            fav_btn.setToolTip("Přepnout oblíbenou")
            fav_btn.setFixedSize(30, 30)
            fav_btn.clicked.connect(lambda checked, b=brand: self.toggle_favorite(b))
            actions_layout.addWidget(fav_btn)

            toggle_btn = QPushButton("🔄")
            toggle_btn.setToolTip("Aktivovat/Deaktivovat")
            toggle_btn.setFixedSize(30, 30)
            toggle_btn.clicked.connect(lambda checked, b=brand: self.toggle_active(b))
            actions_layout.addWidget(toggle_btn)

            delete_btn = QPushButton("🗑️")
            delete_btn.setToolTip("Smazat")
            delete_btn.setFixedSize(30, 30)
            delete_btn.clicked.connect(lambda checked, b=brand: self.delete_brand(b))
            actions_layout.addWidget(delete_btn)

            self.table.setCellWidget(row, 5, actions_widget)

        self.count_label.setText(f"Celkem: {len(data)} značek")

    def add_brand(self):
        """Přidání nové značky"""
        dialog = BrandDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    INSERT INTO codebook_brands (name, vehicle_type, is_favorite, active)
                    VALUES (?, ?, ?, ?)
                """
                db.execute_query(query, (
                    data["name"],
                    data["vehicle_type"],
                    data["is_favorite"],
                    data["active"]
                ))

                QMessageBox.information(self, "Úspěch", f"Značka '{data['name']}' byla přidána.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    QMessageBox.warning(self, "Chyba", f"Značka '{data['name']}' již existuje.")
                else:
                    QMessageBox.critical(self, "Chyba", f"Nepodařilo se přidat značku:\n{e}")

    def edit_brand(self, brand):
        """Úprava značky"""
        dialog = BrandDialog(self, brand)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    UPDATE codebook_brands
                    SET name = ?, vehicle_type = ?, is_favorite = ?, active = ?
                    WHERE id = ?
                """
                db.execute_query(query, (
                    data["name"],
                    data["vehicle_type"],
                    data["is_favorite"],
                    data["active"],
                    brand["id"]
                ))

                QMessageBox.information(self, "Úspěch", "Značka byla upravena.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se upravit značku:\n{e}")

    def delete_brand(self, brand):
        """Smazání značky"""
        # Kontrola použití
        query = "SELECT COUNT(*) as count FROM vehicles WHERE brand = ?"
        result = db.fetch_one(query, (brand["name"],))
        usage_count = result["count"] if result else 0

        if usage_count > 0:
            QMessageBox.warning(
                self,
                "Nelze smazat",
                f"Značka '{brand['name']}' je použita u {usage_count} vozidel.\n\n"
                "Místo smazání ji můžete deaktivovat."
            )
            return

        reply = QMessageBox.question(
            self,
            "Smazat značku",
            f"Opravdu chcete smazat značku '{brand['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = "DELETE FROM codebook_brands WHERE id = ?"
                db.execute_query(query, (brand["id"],))

                QMessageBox.information(self, "Úspěch", "Značka byla smazána.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat značku:\n{e}")

    def toggle_active(self, brand):
        """Přepnutí aktivního stavu"""
        try:
            new_state = 0 if brand["active"] else 1
            query = "UPDATE codebook_brands SET active = ? WHERE id = ?"
            db.execute_query(query, (new_state, brand["id"]))

            self.load_data()
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se změnit stav:\n{e}")

    def toggle_favorite(self, brand):
        """Přepnutí oblíbené"""
        try:
            new_state = 0 if brand["is_favorite"] else 1
            query = "UPDATE codebook_brands SET is_favorite = ? WHERE id = ?"
            db.execute_query(query, (new_state, brand["id"]))

            self.load_data()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se změnit stav:\n{e}")

    # =====================================================
    # IMPORT / EXPORT
    # =====================================================

    def import_csv(self):
        """Import značek z CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importovat značky z CSV",
            "",
            "CSV soubory (*.csv)"
        )

        if not file_path:
            return

        try:
            imported = 0
            skipped = 0

            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')

                for row in reader:
                    name = dict(row).get("name", "").strip()
                    if not name:
                        continue

                    vehicle_type = dict(row).get("vehicle_type", "auto").strip()
                    is_favorite = int(dict(row).get("is_favorite", 0))
                    active = int(dict(row).get("active", 1))

                    # Kontrola existence
                    check_query = "SELECT id FROM codebook_brands WHERE name = ?"
                    existing = db.fetch_one(check_query, (name,))

                    if existing:
                        skipped += 1
                        continue

                    query = """
                        INSERT INTO codebook_brands (name, vehicle_type, is_favorite, active)
                        VALUES (?, ?, ?, ?)
                    """
                    db.execute_query(query, (name, vehicle_type, is_favorite, active))
                    imported += 1

            QMessageBox.information(
                self,
                "Import dokončen",
                f"Importováno: {imported} značek\nPřeskočeno (duplicity): {skipped}"
            )

            self.load_data()
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se importovat CSV:\n{e}")

    def export_csv(self):
        """Export značek do CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportovat značky do CSV",
            f"znacky_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV soubory (*.csv)"
        )

        if not file_path:
            return

        try:
            query = "SELECT name, vehicle_type, is_favorite, active FROM codebook_brands ORDER BY name"
            brands = db.fetch_all(query)

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=["name", "vehicle_type", "is_favorite", "active"], delimiter=';')
                writer.writeheader()

                for brand in brands:
                    writer.writerow({
                        "name": brand["name"],
                        "vehicle_type": brand["vehicle_type"],
                        "is_favorite": brand["is_favorite"],
                        "active": brand["active"]
                    })

            QMessageBox.information(
                self,
                "Export dokončen",
                f"Exportováno {len(brands)} značek do:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se exportovat CSV:\n{e}")

    def reset_to_default(self):
        """Obnovení výchozích značek"""
        reply = QMessageBox.question(
            self,
            "Obnovit výchozí značky",
            "Opravdu chcete obnovit výchozí značky?\n\n"
            "Budou přidány chybějící značky, existující zůstanou.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            default_brands = [
                # Auta
                ("Škoda", "auto", 1), ("Volkswagen", "auto", 1), ("Audi", "auto", 1),
                ("BMW", "both", 1), ("Mercedes-Benz", "auto", 1), ("Toyota", "auto", 0),
                ("Honda", "both", 0), ("Ford", "auto", 0), ("Opel", "auto", 0),
                ("Renault", "auto", 0), ("Peugeot", "auto", 0), ("Citroën", "auto", 0),
                ("Fiat", "auto", 0), ("Hyundai", "auto", 0), ("Kia", "auto", 0),
                ("Mazda", "auto", 0), ("Nissan", "auto", 0), ("Volvo", "auto", 0),
                ("Seat", "auto", 0), ("Dacia", "auto", 0), ("Suzuki", "both", 0),
                ("Mitsubishi", "auto", 0), ("Subaru", "auto", 0), ("Lexus", "auto", 0),

                # Motocykly
                ("Yamaha", "moto", 1), ("Kawasaki", "moto", 1), ("Harley-Davidson", "moto", 0),
                ("Ducati", "moto", 0), ("KTM", "moto", 0), ("Triumph", "moto", 0),
                ("Aprilia", "moto", 0), ("Husqvarna", "moto", 0), ("Piaggio", "moto", 0),
                ("Vespa", "moto", 0), ("Indian", "moto", 0), ("Royal Enfield", "moto", 0),
            ]

            added = 0
            for name, vehicle_type, is_favorite in default_brands:
                check_query = "SELECT id FROM codebook_brands WHERE name = ?"
                existing = db.fetch_one(check_query, (name,))

                if not existing:
                    query = """
                        INSERT INTO codebook_brands (name, vehicle_type, is_favorite, active)
                        VALUES (?, ?, ?, 1)
                    """
                    db.execute_query(query, (name, vehicle_type, is_favorite))
                    added += 1

            QMessageBox.information(
                self,
                "Dokončeno",
                f"Přidáno {added} výchozích značek."
            )

            self.load_data()
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se obnovit výchozí značky:\n{e}")

    # =====================================================
    # POMOCNÉ METODY
    # =====================================================

    def get_count(self):
        """Vrátí počet položek"""
        try:
            query = "SELECT COUNT(*) as count FROM codebook_brands"
            result = db.fetch_one(query)
            return result["count"] if result else 0
        except:
            return 0

    def export_data(self):
        """Export dat pro zálohu"""
        try:
            query = "SELECT name, vehicle_type, is_favorite, active FROM codebook_brands"
            return db.fetch_all(query)
        except:
            return []

    def import_data(self, data):
        """Import dat ze zálohy"""
        try:
            for item in data:
                check_query = "SELECT id FROM codebook_brands WHERE name = ?"
                existing = db.fetch_one(check_query, (item["name"],))

                if existing:
                    query = """
                        UPDATE codebook_brands
                        SET vehicle_type = ?, is_favorite = ?, active = ?
                        WHERE name = ?
                    """
                    db.execute_query(query, (
                        item["vehicle_type"],
                        item["is_favorite"],
                        item["active"],
                        item["name"]
                    ))
                else:
                    query = """
                        INSERT INTO codebook_brands (name, vehicle_type, is_favorite, active)
                        VALUES (?, ?, ?, ?)
                    """
                    db.execute_query(query, (
                        item["name"],
                        item["vehicle_type"],
                        item["is_favorite"],
                        item["active"]
                    ))

            self.load_data()

        except Exception as e:
            print(f"Chyba při importu dat: {e}")

    def refresh(self):
        """Obnovení dat"""
        self.load_data()


# =====================================================
# DIALOG PRO ZNAČKU
# =====================================================

class BrandDialog(QDialog):
    """Dialog pro přidání/úpravu značky"""

    def __init__(self, parent, brand=None):
        super().__init__(parent)
        self.brand = brand
        self.setWindowTitle("Upravit značku" if brand else "Nová značka")
        self.setMinimumWidth(400)
        self.init_ui()

        if brand:
            self.load_brand_data()

    def init_ui(self):
        """Inicializace UI"""
        layout = QFormLayout(self)

        # Název
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Např: Škoda, BMW, Honda...")
        layout.addRow("Název značky:", self.name_input)

        # Typ vozidla
        self.type_combo = QComboBox()
        self.type_combo.addItem("🚗 Automobil", "auto")
        self.type_combo.addItem("🏍️ Motocykl", "moto")
        self.type_combo.addItem("🚗🏍️ Obojí", "both")
        layout.addRow("Typ vozidla:", self.type_combo)

        # Oblíbená
        self.favorite_checkbox = QCheckBox("Označit jako oblíbenou ⭐")
        layout.addRow("", self.favorite_checkbox)

        # Aktivní
        self.active_checkbox = QCheckBox("Aktivní (dostupná pro výběr)")
        self.active_checkbox.setChecked(True)
        layout.addRow("", self.active_checkbox)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Uložit")
        save_btn.clicked.connect(self.save)
        save_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 20px;")
        buttons_layout.addWidget(save_btn)

        layout.addRow(buttons_layout)

    def load_brand_data(self):
        """Načtení dat značky"""
        self.name_input.setText(self.brand["name"])

        index = self.type_combo.findData(self.brand["vehicle_type"])
        if index >= 0:
            self.type_combo.setCurrentIndex(index)

        self.favorite_checkbox.setChecked(self.brand["is_favorite"] == 1)
        self.active_checkbox.setChecked(self.brand["active"] == 1)

    def save(self):
        """Uložení značky"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Chyba", "Vyplňte název značky.")
            return

        self.accept()

    def get_data(self):
        """Vrácení dat"""
        return {
            "name": self.name_input.text().strip(),
            "vehicle_type": self.type_combo.currentData(),
            "is_favorite": 1 if self.favorite_checkbox.isChecked() else 0,
            "active": 1 if self.active_checkbox.isChecked() else 0
        }
