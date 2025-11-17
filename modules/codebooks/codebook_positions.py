# -*- coding: utf-8 -*-
"""
Modul Číselníky - Pracovní pozice (PRODUKČNÍ VERZE)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QFrame,
                             QComboBox, QLineEdit, QHeaderView, QMessageBox,
                             QDialog, QFormLayout, QCheckBox, QFileDialog,
                             QDoubleSpinBox, QSpinBox, QTextEdit, QGroupBox,
                             QSlider)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
import csv
import config
from database_manager import db


class PositionsWidget(QWidget):
    """Widget pro správu pracovních pozic"""

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
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Kód", "Název", "Hodinová sazba", "Úroveň přístupu", "Aktivní", "Akce"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 80)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 120)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 130)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 70)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 150)
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
        add_btn = QPushButton("➕ Přidat pozici")
        add_btn.clicked.connect(self.add_position)
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
        self.search_input.setPlaceholderText("🔍 Vyhledat pozici...")
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

        # Filtr úrovně přístupu
        layout.addWidget(QLabel("Úroveň přístupu:"))
        self.access_filter = QComboBox()
        self.access_filter.addItem("Všechny úrovně", 0)
        self.access_filter.addItem("⭐ Level 1 (Základní)", 1)
        self.access_filter.addItem("⭐⭐ Level 2 (Pokročilý)", 2)
        self.access_filter.addItem("⭐⭐⭐ Level 3 (Senior)", 3)
        self.access_filter.addItem("⭐⭐⭐⭐ Level 4 (Vedoucí)", 4)
        self.access_filter.addItem("⭐⭐⭐⭐⭐ Level 5 (Admin)", 5)
        self.access_filter.currentIndexChanged.connect(self.filter_data)
        layout.addWidget(self.access_filter)

        layout.addStretch()

        # Řazení
        layout.addWidget(QLabel("Řadit:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Podle kódu", "code")
        self.sort_combo.addItem("Podle názvu", "name")
        self.sort_combo.addItem("Podle sazby", "rate")
        self.sort_combo.addItem("Podle úrovně", "level")
        self.sort_combo.currentIndexChanged.connect(self.load_data)
        layout.addWidget(self.sort_combo)

        return frame

    def create_bottom_panel(self):
        """Vytvoření spodního panelu"""
        frame = QFrame()
        layout = QHBoxLayout(frame)

        self.count_label = QLabel("Celkem: 0 pozic")
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
            elif sort_option == "rate":
                order_by = "default_hourly_rate DESC"
            elif sort_option == "level":
                order_by = "access_level DESC, name ASC"

            query = f"""
                SELECT id, code, name, description, default_hourly_rate, access_level, active
                FROM codebook_positions
                ORDER BY {order_by}
            """
            positions = db.fetch_all(query)

            self.all_data = positions
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
            filtered = [p for p in filtered if
                       search_text in p["name"].lower() or
                       search_text in p["code"].lower() or
                       search_text in (p["description"] or "").lower()]

        # Filtr podle stavu
        active_filter = self.active_filter.currentData()
        if active_filter == "active":
            filtered = [p for p in filtered if p["active"] == 1]
        elif active_filter == "inactive":
            filtered = [p for p in filtered if p["active"] == 0]

        # Filtr podle úrovně přístupu
        access_level = self.access_filter.currentData()
        if access_level > 0:
            filtered = [p for p in filtered if p["access_level"] == access_level]

        self.display_data(filtered)

    def display_data(self, data):
        """Zobrazení dat v tabulce"""
        self.table.setRowCount(len(data))

        for row, position in enumerate(data):
            # ID
            id_item = QTableWidgetItem(str(position["id"]))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, id_item)

            # Kód
            code_item = QTableWidgetItem(position["code"])
            code_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            code_item.setFlags(code_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            code_font = QFont()
            code_font.setBold(True)
            code_item.setFont(code_font)
            self.table.setItem(row, 1, code_item)

            # Název
            name_item = QTableWidgetItem(position["name"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if position["description"]:
                name_item.setToolTip(position["description"])
            self.table.setItem(row, 2, name_item)

            # Hodinová sazba
            rate_text = f"{position['default_hourly_rate']:,.0f} Kč/h".replace(",", " ")
            rate_item = QTableWidgetItem(rate_text)
            rate_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            rate_item.setFlags(rate_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, rate_item)

            # Úroveň přístupu
            level = position["access_level"]
            stars = "⭐" * level
            level_labels = {
                1: "Základní",
                2: "Pokročilý",
                3: "Senior",
                4: "Vedoucí",
                5: "Admin"
            }
            level_text = f"{stars} ({level_labels.get(level, 'Neznámá')})"
            level_item = QTableWidgetItem(level_text)
            level_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            level_item.setFlags(level_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, level_item)

            # Aktivní
            active_item = QTableWidgetItem("✅" if position["active"] else "❌")
            active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            active_item.setFlags(active_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if not position["active"]:
                active_item.setForeground(QColor("#e74c3c"))
            self.table.setItem(row, 5, active_item)

            # Akce
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.setSpacing(5)

            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Upravit")
            edit_btn.setFixedSize(30, 30)
            edit_btn.clicked.connect(lambda checked, p=position: self.edit_position(p))
            actions_layout.addWidget(edit_btn)

            users_btn = QPushButton("👥")
            users_btn.setToolTip("Zobrazit uživatele")
            users_btn.setFixedSize(30, 30)
            users_btn.clicked.connect(lambda checked, p=position: self.show_users(p))
            actions_layout.addWidget(users_btn)

            toggle_btn = QPushButton("🔄")
            toggle_btn.setToolTip("Aktivovat/Deaktivovat")
            toggle_btn.setFixedSize(30, 30)
            toggle_btn.clicked.connect(lambda checked, p=position: self.toggle_active(p))
            actions_layout.addWidget(toggle_btn)

            delete_btn = QPushButton("🗑️")
            delete_btn.setToolTip("Smazat")
            delete_btn.setFixedSize(30, 30)
            delete_btn.clicked.connect(lambda checked, p=position: self.delete_position(p))
            actions_layout.addWidget(delete_btn)

            self.table.setCellWidget(row, 6, actions_widget)

        self.count_label.setText(f"Celkem: {len(data)} pozic")

    def on_double_click(self, row, column):
        """Dvojklik na řádek - otevře editaci"""
        id_item = self.table.item(row, 0)
        if id_item:
            position_id = int(id_item.text())
            for position in self.all_data:
                if position["id"] == position_id:
                    self.edit_position(position)
                    break

    def add_position(self):
        """Přidání nové pozice"""
        dialog = PositionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    INSERT INTO codebook_positions
                    (code, name, description, default_hourly_rate, access_level, active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                db.execute_query(query, (
                    data["code"],
                    data["name"],
                    data["description"],
                    data["default_hourly_rate"],
                    data["access_level"],
                    data["active"]
                ))

                QMessageBox.information(self, "Úspěch", f"Pozice '{data['name']}' byla přidána.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    QMessageBox.warning(self, "Chyba", f"Kód '{data['code']}' již existuje.")
                else:
                    QMessageBox.critical(self, "Chyba", f"Nepodařilo se přidat pozici:\n{e}")

    def edit_position(self, position):
        """Úprava pozice"""
        dialog = PositionDialog(self, position)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    UPDATE codebook_positions
                    SET code = ?, name = ?, description = ?, default_hourly_rate = ?,
                        access_level = ?, active = ?
                    WHERE id = ?
                """
                db.execute_query(query, (
                    data["code"],
                    data["name"],
                    data["description"],
                    data["default_hourly_rate"],
                    data["access_level"],
                    data["active"],
                    position["id"]
                ))

                QMessageBox.information(self, "Úspěch", "Pozice byla upravena.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se upravit pozici:\n{e}")

    def delete_position(self, position):
        """Smazání pozice"""
        # Kontrola použití
        query = "SELECT COUNT(*) as count FROM users WHERE role = ?"
        result = db.fetch_one(query, (position["code"],))
        usage_count = result["count"] if result else 0

        if usage_count > 0:
            QMessageBox.warning(
                self,
                "Nelze smazat",
                f"Pozice '{position['name']}' je přiřazena {usage_count} uživatelům.\n\n"
                "Místo smazání ji můžete deaktivovat."
            )
            return

        reply = QMessageBox.question(
            self,
            "Smazat pozici",
            f"Opravdu chcete smazat pozici '{position['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = "DELETE FROM codebook_positions WHERE id = ?"
                db.execute_query(query, (position["id"],))

                QMessageBox.information(self, "Úspěch", "Pozice byla smazána.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat pozici:\n{e}")

    def toggle_active(self, position):
        """Přepnutí aktivního stavu"""
        try:
            new_state = 0 if position["active"] else 1
            query = "UPDATE codebook_positions SET active = ? WHERE id = ?"
            db.execute_query(query, (new_state, position["id"]))

            self.load_data()
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se změnit stav:\n{e}")

    def show_users(self, position):
        """Zobrazení uživatelů s danou pozicí"""
        try:
            query = "SELECT username, full_name FROM users WHERE role = ?"
            users = db.fetch_all(query, (position["code"],))

            if not users:
                QMessageBox.information(
                    self,
                    f"Uživatelé - {position['name']}",
                    "Žádní uživatelé nemají přiřazenu tuto pozici."
                )
                return

            user_list = "\n".join([f"• {u['full_name']} ({u['username']})" for u in users])

            QMessageBox.information(
                self,
                f"Uživatelé - {position['name']}",
                f"Počet uživatelů: {len(users)}\n\n{user_list}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst uživatele:\n{e}")

    # =====================================================
    # IMPORT / EXPORT
    # =====================================================

    def import_csv(self):
        """Import pozic z CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importovat pozice z CSV",
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

                    description = dict(row).get("description", "").strip()
                    default_hourly_rate = float(dict(row).get("default_hourly_rate", 0))
                    access_level = int(dict(row).get("access_level", 1))
                    active = int(dict(row).get("active", 1))

                    # Kontrola existence
                    check_query = "SELECT id FROM codebook_positions WHERE code = ?"
                    existing = db.fetch_one(check_query, (code,))

                    if existing:
                        skipped += 1
                        continue

                    query = """
                        INSERT INTO codebook_positions
                        (code, name, description, default_hourly_rate, access_level, active)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """
                    db.execute_query(query, (code, name, description, default_hourly_rate, access_level, active))
                    imported += 1

            QMessageBox.information(
                self,
                "Import dokončen",
                f"Importováno: {imported} pozic\nPřeskočeno (duplicity): {skipped}"
            )

            self.load_data()
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se importovat CSV:\n{e}")

    def export_csv(self):
        """Export pozic do CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportovat pozice do CSV",
            f"pozice_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV soubory (*.csv)"
        )

        if not file_path:
            return

        try:
            query = """
                SELECT code, name, description, default_hourly_rate, access_level, active
                FROM codebook_positions
                ORDER BY code
            """
            positions = db.fetch_all(query)

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["code", "name", "description", "default_hourly_rate", "access_level", "active"],
                    delimiter=';'
                )
                writer.writeheader()

                for pos in positions:
                    writer.writerow({
                        "code": pos["code"],
                        "name": pos["name"],
                        "description": pos["description"] or "",
                        "default_hourly_rate": pos["default_hourly_rate"],
                        "access_level": pos["access_level"],
                        "active": pos["active"]
                    })

            QMessageBox.information(
                self,
                "Export dokončen",
                f"Exportováno {len(positions)} pozic do:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se exportovat CSV:\n{e}")

    def reset_to_default(self):
        """Obnovení výchozích pozic"""
        reply = QMessageBox.question(
            self,
            "Obnovit výchozí pozice",
            "Opravdu chcete obnovit výchozí pozice?\n\n"
            "Budou přidány chybějící pozice, existující zůstanou.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            default_positions = [
                ("UCEN", "Učeň", "Učeň - asistence při práci", 200, 1),
                ("MECH", "Mechanik", "Mechanik - základní opravy a servis", 800, 2),
                ("SMECH", "Senior mechanik", "Senior mechanik - složité opravy", 1000, 3),
                ("DIAG", "Diagnostik", "Diagnostik - elektronika a diagnostika", 1200, 3),
                ("LAKYR", "Lakýrník", "Lakýrník - lakýrnické práce", 900, 2),
                ("ELEKTR", "Autoelektrikář", "Autoelektrikář - elektroinstalace", 1100, 3),
                ("ADMIN", "Administrativní pracovník", "Administrativní pracovník - fakturace, příjem", 600, 2),
                ("PRIJEM", "Příjemce", "Příjemce zakázek - kontakt se zákazníky", 700, 2),
                ("VEDSERV", "Vedoucí servisu", "Vedoucí servisu - management", 1500, 4),
                ("MAJITEL", "Majitel", "Majitel - plná kontrola", 0, 5),
            ]

            added = 0
            for code, name, description, rate, level in default_positions:
                check_query = "SELECT id FROM codebook_positions WHERE code = ?"
                existing = db.fetch_one(check_query, (code,))

                if not existing:
                    query = """
                        INSERT INTO codebook_positions
                        (code, name, description, default_hourly_rate, access_level, active)
                        VALUES (?, ?, ?, ?, ?, 1)
                    """
                    db.execute_query(query, (code, name, description, rate, level))
                    added += 1

            QMessageBox.information(
                self,
                "Dokončeno",
                f"Přidáno {added} výchozích pozic."
            )

            self.load_data()
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se obnovit výchozí pozice:\n{e}")

    # =====================================================
    # POMOCNÉ METODY
    # =====================================================

    def get_count(self):
        """Vrátí počet položek"""
        try:
            query = "SELECT COUNT(*) as count FROM codebook_positions"
            result = db.fetch_one(query)
            return result["count"] if result else 0
        except:
            return 0

    def export_data(self):
        """Export dat pro zálohu"""
        try:
            query = """
                SELECT code, name, description, default_hourly_rate, access_level, active
                FROM codebook_positions
            """
            return db.fetch_all(query)
        except:
            return []

    def import_data(self, data):
        """Import dat ze zálohy"""
        try:
            for item in data:
                check_query = "SELECT id FROM codebook_positions WHERE code = ?"
                existing = db.fetch_one(check_query, (item["code"],))

                if existing:
                    query = """
                        UPDATE codebook_positions
                        SET name = ?, description = ?, default_hourly_rate = ?,
                            access_level = ?, active = ?
                        WHERE code = ?
                    """
                    db.execute_query(query, (
                        item["name"],
                        item.get("description", ""),
                        item["default_hourly_rate"],
                        item["access_level"],
                        item["active"],
                        item["code"]
                    ))
                else:
                    query = """
                        INSERT INTO codebook_positions
                        (code, name, description, default_hourly_rate, access_level, active)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """
                    db.execute_query(query, (
                        item["code"],
                        item["name"],
                        item.get("description", ""),
                        item["default_hourly_rate"],
                        item["access_level"],
                        item["active"]
                    ))

            self.load_data()

        except Exception as e:
            print(f"Chyba při importu dat: {e}")

    def refresh(self):
        """Obnovení dat"""
        self.load_data()


# =====================================================
# DIALOG PRO POZICI
# =====================================================

class PositionDialog(QDialog):
    """Dialog pro přidání/úpravu pozice"""

    def __init__(self, parent, position=None):
        super().__init__(parent)
        self.position = position
        self.setWindowTitle("Upravit pozici" if position else "Nová pozice")
        self.setMinimumWidth(500)
        self.init_ui()

        if position:
            self.load_position_data()

    def init_ui(self):
        """Inicializace UI"""
        layout = QFormLayout(self)

        # Kód
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Např: MECH, DIAG, ADMIN...")
        self.code_input.setMaxLength(10)
        layout.addRow("Kód:", self.code_input)

        # Název
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Např: Mechanik, Diagnostik...")
        layout.addRow("Název:", self.name_input)

        # Popis
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("Popis pracovní pozice...")
        layout.addRow("Popis:", self.description_input)

        # Hodinová sazba
        rate_group = QGroupBox("Výchozí hodinová sazba")
        rate_layout = QFormLayout(rate_group)

        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(0, 99999)
        self.rate_input.setDecimals(0)
        self.rate_input.setSuffix(" Kč/h")
        self.rate_input.setValue(800)
        rate_layout.addRow("Sazba:", self.rate_input)

        rate_info = QLabel("Tato sazba se použije při přiřazení práce uživateli s touto pozicí.")
        rate_info.setStyleSheet("color: #7f8c8d; font-size: 10pt;")
        rate_info.setWordWrap(True)
        rate_layout.addRow("", rate_info)

        layout.addRow(rate_group)

        # Úroveň přístupu
        access_group = QGroupBox("Úroveň přístupu")
        access_layout = QVBoxLayout(access_group)

        self.access_slider = QSlider(Qt.Orientation.Horizontal)
        self.access_slider.setRange(1, 5)
        self.access_slider.setValue(1)
        self.access_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.access_slider.setTickInterval(1)
        self.access_slider.valueChanged.connect(self.update_access_label)
        access_layout.addWidget(self.access_slider)

        self.access_label = QLabel("⭐ Level 1 - Základní (pouze prohlížení)")
        self.access_label.setStyleSheet("font-weight: bold; text-align: center;")
        self.access_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        access_layout.addWidget(self.access_label)

        access_descriptions = QLabel(
            "Level 1: Základní - pouze prohlížení\n"
            "Level 2: Pokročilý - vytváření a úpravy vlastních dat\n"
            "Level 3: Senior - rozšířené oprávnění\n"
            "Level 4: Vedoucí - správa týmu a reporty\n"
            "Level 5: Admin - plný přístup"
        )
        access_descriptions.setStyleSheet("color: #7f8c8d; font-size: 9pt;")
        access_layout.addWidget(access_descriptions)

        layout.addRow(access_group)

        # Aktivní
        self.active_checkbox = QCheckBox("Aktivní (dostupná pro přiřazení)")
        self.active_checkbox.setChecked(True)
        layout.addRow("", self.active_checkbox)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        if self.position:
            delete_btn = QPushButton("🗑️ Smazat")
            delete_btn.clicked.connect(self.delete_position)
            delete_btn.setStyleSheet(f"background-color: {config.COLOR_DANGER}; color: white; padding: 8px 20px;")
            buttons_layout.addWidget(delete_btn)

        save_btn = QPushButton("💾 Uložit")
        save_btn.clicked.connect(self.save)
        save_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 20px;")
        buttons_layout.addWidget(save_btn)

        layout.addRow(buttons_layout)

    def update_access_label(self):
        """Aktualizace popisku úrovně přístupu"""
        level = self.access_slider.value()
        stars = "⭐" * level

        level_descriptions = {
            1: "Základní (pouze prohlížení)",
            2: "Pokročilý (vytváření a úpravy)",
            3: "Senior (rozšířené oprávnění)",
            4: "Vedoucí (správa týmu)",
            5: "Admin (plný přístup)"
        }

        self.access_label.setText(f"{stars} Level {level} - {level_descriptions[level]}")

    def load_position_data(self):
        """Načtení dat pozice"""
        self.code_input.setText(self.position["code"])
        self.name_input.setText(self.position["name"])
        self.description_input.setPlainText(self.position["description"] or "")
        self.rate_input.setValue(self.position["default_hourly_rate"])
        self.access_slider.setValue(self.position["access_level"])
        self.active_checkbox.setChecked(self.position["active"] == 1)
        self.update_access_label()

    def delete_position(self):
        """Smazání pozice z dialogu"""
        if self.position:
            self.parent().delete_position(self.position)
            self.reject()

    def save(self):
        """Uložení pozice"""
        code = self.code_input.text().strip()
        name = self.name_input.text().strip()

        if not code:
            QMessageBox.warning(self, "Chyba", "Vyplňte kód pozice.")
            return

        if not name:
            QMessageBox.warning(self, "Chyba", "Vyplňte název pozice.")
            return

        self.accept()

    def get_data(self):
        """Vrácení dat"""
        return {
            "code": self.code_input.text().strip().upper(),
            "name": self.name_input.text().strip(),
            "description": self.description_input.toPlainText().strip(),
            "default_hourly_rate": self.rate_input.value(),
            "access_level": self.access_slider.value(),
            "active": 1 if self.active_checkbox.isChecked() else 0
        }
