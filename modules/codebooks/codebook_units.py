# -*- coding: utf-8 -*-
"""
Modul Číselníky - Měrné jednotky (PRODUKČNÍ VERZE)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QFrame,
                             QComboBox, QLineEdit, QHeaderView, QMessageBox,
                             QDialog, QFormLayout, QCheckBox, QFileDialog,
                             QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
import csv
import config
from database_manager import db


class UnitsWidget(QWidget):
    """Widget pro správu měrných jednotek"""

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
            "ID", "Kód", "Název", "Zkratka", "Des. místa", "Aktivní"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 60)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 80)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 100)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 100)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 80)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self.on_double_click)
        layout.addWidget(self.table)

        # Spodní panel
        bottom_panel = self.create_bottom_panel()
        layout.addWidget(bottom_panel)

    def create_top_panel(self):
        """Vytvoření horního panelu"""
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tlačítka
        add_btn = QPushButton("➕ Přidat jednotku")
        add_btn.clicked.connect(self.add_unit)
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
        self.search_input.setPlaceholderText("🔍 Vyhledat jednotku...")
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

        # Filtr aktivní
        layout.addWidget(QLabel("Stav:"))
        self.active_filter = QComboBox()
        self.active_filter.addItem("Všechny", "all")
        self.active_filter.addItem("✅ Aktivní", "active")
        self.active_filter.addItem("❌ Neaktivní", "inactive")
        self.active_filter.currentIndexChanged.connect(self.filter_data)
        layout.addWidget(self.active_filter)

        layout.addStretch()

        # Řazení
        layout.addWidget(QLabel("Řadit:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Podle kódu", "code")
        self.sort_combo.addItem("Podle názvu", "name")
        self.sort_combo.addItem("Podle des. míst", "decimal")
        self.sort_combo.currentIndexChanged.connect(self.load_data)
        layout.addWidget(self.sort_combo)

        return frame

    def create_bottom_panel(self):
        """Vytvoření spodního panelu"""
        frame = QFrame()
        layout = QHBoxLayout(frame)

        self.count_label = QLabel("Celkem: 0 jednotek")
        self.count_label.setStyleSheet("color: #7f8c8d; font-size: 11pt;")
        layout.addWidget(self.count_label)

        layout.addStretch()

        info_label = QLabel("💡 Dvojklik pro rychlou úpravu")
        info_label.setStyleSheet("color: #95a5a6; font-size: 10pt;")
        layout.addWidget(info_label)

        return frame

    # =====================================================
    # CRUD OPERACE
    # =====================================================

    def load_data(self):
        """Načtení dat z databáze"""
        try:
            # Sestavení dotazu s řazením
            sort_option = self.sort_combo.currentData() if hasattr(self, 'sort_combo') else "code"

            order_by = "code ASC"
            if sort_option == "name":
                order_by = "name ASC"
            elif sort_option == "decimal":
                order_by = "decimal_places ASC, code ASC"

            query = f"""
                SELECT id, code, name, abbreviation, decimal_places, active
                FROM codebook_units
                ORDER BY {order_by}
            """
            units = db.fetch_all(query)

            self.all_data = units
            self.filter_data()

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
            filtered = [u for u in filtered if
                       search_text in u["name"].lower() or
                       search_text in u["code"].lower() or
                       search_text in (u["abbreviation"] or "").lower()]

        # Filtr podle stavu
        active_filter = self.active_filter.currentData()
        if active_filter == "active":
            filtered = [u for u in filtered if u["active"] == 1]
        elif active_filter == "inactive":
            filtered = [u for u in filtered if u["active"] == 0]

        self.display_data(filtered)

    def display_data(self, data):
        """Zobrazení dat v tabulce"""
        self.table.setRowCount(len(data))

        for row, unit in enumerate(data):
            # ID
            id_item = QTableWidgetItem(str(unit["id"]))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, id_item)

            # Kód
            code_item = QTableWidgetItem(unit["code"])
            code_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            code_item.setFlags(code_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            code_font = QFont()
            code_font.setBold(True)
            code_item.setFont(code_font)
            self.table.setItem(row, 1, code_item)

            # Název
            name_item = QTableWidgetItem(unit["name"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, name_item)

            # Zkratka
            abbr_item = QTableWidgetItem(unit["abbreviation"] or unit["code"])
            abbr_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            abbr_item.setFlags(abbr_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, abbr_item)

            # Desetinná místa
            decimal_item = QTableWidgetItem(str(unit["decimal_places"]))
            decimal_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            decimal_item.setFlags(decimal_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, decimal_item)

            # Aktivní
            active_item = QTableWidgetItem("✅" if unit["active"] else "❌")
            active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            active_item.setFlags(active_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if not unit["active"]:
                active_item.setForeground(QColor("#e74c3c"))
            self.table.setItem(row, 5, active_item)

        self.count_label.setText(f"Celkem: {len(data)} jednotek")

    def on_double_click(self, row, column):
        """Dvojklik na řádek - otevře editaci"""
        id_item = self.table.item(row, 0)
        if id_item:
            unit_id = int(id_item.text())
            # Najít jednotku v datech
            for unit in self.all_data:
                if unit["id"] == unit_id:
                    self.edit_unit(unit)
                    break

    def add_unit(self):
        """Přidání nové jednotky"""
        dialog = UnitDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    INSERT INTO codebook_units (code, name, abbreviation, decimal_places, active)
                    VALUES (?, ?, ?, ?, ?)
                """
                db.execute_query(query, (
                    data["code"],
                    data["name"],
                    data["abbreviation"],
                    data["decimal_places"],
                    data["active"]
                ))

                QMessageBox.information(self, "Úspěch", f"Jednotka '{data['name']}' byla přidána.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    QMessageBox.warning(self, "Chyba", f"Kód '{data['code']}' již existuje.")
                else:
                    QMessageBox.critical(self, "Chyba", f"Nepodařilo se přidat jednotku:\n{e}")

    def edit_unit(self, unit):
        """Úprava jednotky"""
        dialog = UnitDialog(self, unit)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    UPDATE codebook_units
                    SET code = ?, name = ?, abbreviation = ?, decimal_places = ?, active = ?
                    WHERE id = ?
                """
                db.execute_query(query, (
                    data["code"],
                    data["name"],
                    data["abbreviation"],
                    data["decimal_places"],
                    data["active"],
                    unit["id"]
                ))

                QMessageBox.information(self, "Úspěch", "Jednotka byla upravena.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se upravit jednotku:\n{e}")

    def delete_unit(self, unit):
        """Smazání jednotky"""
        # Kontrola použití
        query = "SELECT COUNT(*) as count FROM warehouse WHERE unit = ?"
        result = db.fetch_one(query, (unit["code"],))
        usage_count = result["count"] if result else 0

        if usage_count > 0:
            QMessageBox.warning(
                self,
                "Nelze smazat",
                f"Jednotka '{unit['name']}' je použita u {usage_count} položek ve skladu.\n\n"
                "Místo smazání ji můžete deaktivovat."
            )
            return

        reply = QMessageBox.question(
            self,
            "Smazat jednotku",
            f"Opravdu chcete smazat jednotku '{unit['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = "DELETE FROM codebook_units WHERE id = ?"
                db.execute_query(query, (unit["id"],))

                QMessageBox.information(self, "Úspěch", "Jednotka byla smazána.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat jednotku:\n{e}")

    # =====================================================
    # IMPORT / EXPORT
    # =====================================================

    def import_csv(self):
        """Import jednotek z CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importovat jednotky z CSV",
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
                    code = dict(row).get("code", "").strip()
                    name = dict(row).get("name", "").strip()
                    if not code or not name:
                        continue

                    abbreviation = dict(row).get("abbreviation", code).strip()
                    decimal_places = int(dict(row).get("decimal_places", 0))
                    active = int(dict(row).get("active", 1))

                    # Kontrola existence
                    check_query = "SELECT id FROM codebook_units WHERE code = ?"
                    existing = db.fetch_one(check_query, (code,))

                    if existing:
                        skipped += 1
                        continue

                    query = """
                        INSERT INTO codebook_units (code, name, abbreviation, decimal_places, active)
                        VALUES (?, ?, ?, ?, ?)
                    """
                    db.execute_query(query, (code, name, abbreviation, decimal_places, active))
                    imported += 1

            QMessageBox.information(
                self,
                "Import dokončen",
                f"Importováno: {imported} jednotek\nPřeskočeno (duplicity): {skipped}"
            )

            self.load_data()
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se importovat CSV:\n{e}")

    def export_csv(self):
        """Export jednotek do CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportovat jednotky do CSV",
            f"jednotky_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV soubory (*.csv)"
        )

        if not file_path:
            return

        try:
            query = """
                SELECT code, name, abbreviation, decimal_places, active
                FROM codebook_units
                ORDER BY code
            """
            units = db.fetch_all(query)

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["code", "name", "abbreviation", "decimal_places", "active"],
                    delimiter=';'
                )
                writer.writeheader()

                for unit in units:
                    writer.writerow({
                        "code": unit["code"],
                        "name": unit["name"],
                        "abbreviation": unit["abbreviation"] or unit["code"],
                        "decimal_places": unit["decimal_places"],
                        "active": unit["active"]
                    })

            QMessageBox.information(
                self,
                "Export dokončen",
                f"Exportováno {len(units)} jednotek do:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se exportovat CSV:\n{e}")

    def reset_to_default(self):
        """Obnovení výchozích jednotek"""
        reply = QMessageBox.question(
            self,
            "Obnovit výchozí jednotky",
            "Opravdu chcete obnovit výchozí jednotky?\n\n"
            "Budou přidány chybějící jednotky, existující zůstanou.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            default_units = [
                ("ks", "kus", "ks", 0),
                ("l", "litr", "l", 2),
                ("ml", "mililitr", "ml", 0),
                ("kg", "kilogram", "kg", 3),
                ("g", "gram", "g", 0),
                ("m", "metr", "m", 2),
                ("cm", "centimetr", "cm", 1),
                ("mm", "milimetr", "mm", 0),
                ("h", "hodina", "hod", 2),
                ("min", "minuta", "min", 0),
                ("bal", "balení", "bal", 0),
                ("sada", "sada", "sada", 0),
                ("pár", "pár", "pár", 0),
                ("m2", "metr čtvereční", "m²", 2),
                ("m3", "metr krychlový", "m³", 3),
            ]

            added = 0
            for code, name, abbreviation, decimal_places in default_units:
                check_query = "SELECT id FROM codebook_units WHERE code = ?"
                existing = db.fetch_one(check_query, (code,))

                if not existing:
                    query = """
                        INSERT INTO codebook_units (code, name, abbreviation, decimal_places, active)
                        VALUES (?, ?, ?, ?, 1)
                    """
                    db.execute_query(query, (code, name, abbreviation, decimal_places))
                    added += 1

            QMessageBox.information(
                self,
                "Dokončeno",
                f"Přidáno {added} výchozích jednotek."
            )

            self.load_data()
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se obnovit výchozí jednotky:\n{e}")

    # =====================================================
    # POMOCNÉ METODY
    # =====================================================

    def get_count(self):
        """Vrátí počet položek"""
        try:
            query = "SELECT COUNT(*) as count FROM codebook_units"
            result = db.fetch_one(query)
            return result["count"] if result else 0
        except:
            return 0

    def export_data(self):
        """Export dat pro zálohu"""
        try:
            query = "SELECT code, name, abbreviation, decimal_places, active FROM codebook_units"
            return db.fetch_all(query)
        except:
            return []

    def import_data(self, data):
        """Import dat ze zálohy"""
        try:
            for item in data:
                check_query = "SELECT id FROM codebook_units WHERE code = ?"
                existing = db.fetch_one(check_query, (item["code"],))

                if existing:
                    query = """
                        UPDATE codebook_units
                        SET name = ?, abbreviation = ?, decimal_places = ?, active = ?
                        WHERE code = ?
                    """
                    db.execute_query(query, (
                        item["name"],
                        item.get("abbreviation", item["code"]),
                        item["decimal_places"],
                        item["active"],
                        item["code"]
                    ))
                else:
                    query = """
                        INSERT INTO codebook_units (code, name, abbreviation, decimal_places, active)
                        VALUES (?, ?, ?, ?, ?)
                    """
                    db.execute_query(query, (
                        item["code"],
                        item["name"],
                        item.get("abbreviation", item["code"]),
                        item["decimal_places"],
                        item["active"]
                    ))

            self.load_data()

        except Exception as e:
            print(f"Chyba při importu dat: {e}")

    def refresh(self):
        """Obnovení dat"""
        self.load_data()


# =====================================================
# DIALOG PRO JEDNOTKU
# =====================================================

class UnitDialog(QDialog):
    """Dialog pro přidání/úpravu jednotky"""

    def __init__(self, parent, unit=None):
        super().__init__(parent)
        self.unit = unit
        self.setWindowTitle("Upravit jednotku" if unit else "Nová jednotka")
        self.setMinimumWidth(400)
        self.init_ui()

        if unit:
            self.load_unit_data()

    def init_ui(self):
        """Inicializace UI"""
        layout = QFormLayout(self)

        # Kód
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Např: ks, l, kg, m, h...")
        self.code_input.setMaxLength(10)
        layout.addRow("Kód:", self.code_input)

        # Název
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Např: kus, litr, kilogram...")
        layout.addRow("Název:", self.name_input)

        # Zkratka
        self.abbreviation_input = QLineEdit()
        self.abbreviation_input.setPlaceholderText("Např: ks, l, kg (zobrazí se ve fakturách)")
        self.abbreviation_input.setMaxLength(10)
        layout.addRow("Zkratka:", self.abbreviation_input)

        # Desetinná místa
        self.decimal_input = QSpinBox()
        self.decimal_input.setRange(0, 6)
        self.decimal_input.setValue(0)
        self.decimal_input.setToolTip(
            "Počet desetinných míst pro tuto jednotku.\n"
            "Např: ks = 0, litr = 2, kg = 3"
        )
        layout.addRow("Desetinná místa:", self.decimal_input)

        # Příklad
        example_label = QLabel("")
        example_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.example_label = example_label
        layout.addRow("Příklad:", example_label)

        self.decimal_input.valueChanged.connect(self.update_example)
        self.update_example()

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

        if self.unit:
            delete_btn = QPushButton("🗑️ Smazat")
            delete_btn.clicked.connect(self.delete_unit)
            delete_btn.setStyleSheet(f"background-color: {config.COLOR_DANGER}; color: white; padding: 8px 20px;")
            buttons_layout.addWidget(delete_btn)

        save_btn = QPushButton("💾 Uložit")
        save_btn.clicked.connect(self.save)
        save_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 20px;")
        buttons_layout.addWidget(save_btn)

        layout.addRow(buttons_layout)

    def load_unit_data(self):
        """Načtení dat jednotky"""
        self.code_input.setText(self.unit["code"])
        self.name_input.setText(self.unit["name"])
        self.abbreviation_input.setText(self.unit["abbreviation"] or "")
        self.decimal_input.setValue(self.unit["decimal_places"])
        self.active_checkbox.setChecked(self.unit["active"] == 1)

    def update_example(self):
        """Aktualizace příkladu"""
        decimals = self.decimal_input.value()
        example_value = 12.345678
        formatted = f"{example_value:.{decimals}f}"
        self.example_label.setText(f"Hodnota 12.345678 se zobrazí jako: {formatted}")

    def delete_unit(self):
        """Smazání jednotky z dialogu"""
        if self.unit:
            self.parent().delete_unit(self.unit)
            self.reject()

    def save(self):
        """Uložení jednotky"""
        code = self.code_input.text().strip()
        name = self.name_input.text().strip()

        if not code:
            QMessageBox.warning(self, "Chyba", "Vyplňte kód jednotky.")
            return

        if not name:
            QMessageBox.warning(self, "Chyba", "Vyplňte název jednotky.")
            return

        self.accept()

    def get_data(self):
        """Vrácení dat"""
        code = self.code_input.text().strip().lower()
        abbreviation = self.abbreviation_input.text().strip()

        return {
            "code": code,
            "name": self.name_input.text().strip(),
            "abbreviation": abbreviation if abbreviation else code,
            "decimal_places": self.decimal_input.value(),
            "active": 1 if self.active_checkbox.isChecked() else 0
        }
