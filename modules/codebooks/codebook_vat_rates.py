# -*- coding: utf-8 -*-
"""
Modul Číselníky - Sazby DPH (PRODUKČNÍ VERZE)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QFrame,
                             QComboBox, QLineEdit, QHeaderView, QMessageBox,
                             QDialog, QFormLayout, QCheckBox, QFileDialog,
                             QDoubleSpinBox, QTextEdit, QGroupBox, QDateEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, date
import csv
import config
from database_manager import db


class VatRatesWidget(QWidget):
    """Widget pro správu sazeb DPH"""

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

        # Informační panel
        info_panel = self.create_info_panel()
        layout.addWidget(info_panel)

        # Filtr
        filter_panel = self.create_filter_panel()
        layout.addWidget(filter_panel)

        # Tabulka
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Název", "Sazba %", "Popis", "Platná od", "Platná do",
            "Výchozí", "Stav", "Akce"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 80)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 100)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 100)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 70)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(7, 100)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(8, 120)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self.on_double_click)
        layout.addWidget(self.table)

        # Kalkulátor DPH
        calculator_panel = self.create_calculator_panel()
        layout.addWidget(calculator_panel)

        # Spodní panel
        bottom_panel = self.create_bottom_panel()
        layout.addWidget(bottom_panel)

    def create_top_panel(self):
        """Vytvoření horního panelu"""
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tlačítka
        add_btn = QPushButton("➕ Přidat sazbu DPH")
        add_btn.clicked.connect(self.add_rate)
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
        self.search_input.setPlaceholderText("🔍 Vyhledat sazbu...")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self.filter_data)
        layout.addWidget(self.search_input)

        return frame

    def create_info_panel(self):
        """Vytvoření informačního panelu"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #fef9e7;
                border-radius: 4px;
                padding: 10px;
                border: 1px solid #f39c12;
            }
        """)
        layout = QHBoxLayout(frame)

        info_icon = QLabel("⚠️")
        info_icon.setStyleSheet("font-size: 20pt;")
        layout.addWidget(info_icon)

        info_text = QLabel(
            "Sazby DPH se používají při fakturaci. Při změně legislativy\n"
            "vytvořte novou sazbu s datem platnosti, starou sazbu ponechte pro historii."
        )
        info_text.setStyleSheet("font-size: 11pt;")
        layout.addWidget(info_text)

        layout.addStretch()

        # Aktuální sazby
        self.current_rates_label = QLabel("")
        self.current_rates_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 11pt;")
        layout.addWidget(self.current_rates_label)

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

        # Filtr stavu
        layout.addWidget(QLabel("Stav:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("Všechny", "all")
        self.status_filter.addItem("✅ Aktivní (platné)", "active")
        self.status_filter.addItem("📅 Budoucí", "future")
        self.status_filter.addItem("⏰ Prošlé", "expired")
        self.status_filter.addItem("❌ Neaktivní", "inactive")
        self.status_filter.currentIndexChanged.connect(self.filter_data)
        layout.addWidget(self.status_filter)

        layout.addStretch()

        # Řazení
        layout.addWidget(QLabel("Řadit:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Podle sazby", "rate")
        self.sort_combo.addItem("Podle názvu", "name")
        self.sort_combo.addItem("Podle platnosti", "valid_from")
        self.sort_combo.addItem("Výchozí první", "default")
        self.sort_combo.currentIndexChanged.connect(self.load_data)
        layout.addWidget(self.sort_combo)

        return frame

    def create_calculator_panel(self):
        """Vytvoření kalkulátoru DPH"""
        group = QGroupBox("🧮 Kalkulátor DPH")
        layout = QHBoxLayout(group)

        # Částka
        layout.addWidget(QLabel("Částka bez DPH:"))
        self.calc_amount = QDoubleSpinBox()
        self.calc_amount.setRange(0, 999999999)
        self.calc_amount.setDecimals(2)
        self.calc_amount.setSuffix(" Kč")
        self.calc_amount.setValue(1000)
        self.calc_amount.valueChanged.connect(self.calculate_vat)
        layout.addWidget(self.calc_amount)

        # Sazba
        layout.addWidget(QLabel("Sazba DPH:"))
        self.calc_rate = QComboBox()
        self.calc_rate.currentIndexChanged.connect(self.calculate_vat)
        layout.addWidget(self.calc_rate)

        # Výsledky
        layout.addWidget(QLabel("DPH:"))
        self.calc_vat_amount = QLabel("0 Kč")
        self.calc_vat_amount.setStyleSheet("font-weight: bold; color: #e74c3c;")
        layout.addWidget(self.calc_vat_amount)

        layout.addWidget(QLabel("Celkem s DPH:"))
        self.calc_total = QLabel("0 Kč")
        self.calc_total.setStyleSheet("font-weight: bold; font-size: 12pt; color: #27ae60;")
        layout.addWidget(self.calc_total)

        layout.addStretch()

        return group

    def create_bottom_panel(self):
        """Vytvoření spodního panelu"""
        frame = QFrame()
        layout = QHBoxLayout(frame)

        self.count_label = QLabel("Celkem: 0 sazeb")
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
            sort_option = self.sort_combo.currentData() if hasattr(self, 'sort_combo') else "rate"

            order_by = "rate DESC"
            if sort_option == "name":
                order_by = "name ASC"
            elif sort_option == "valid_from":
                order_by = "valid_from DESC"
            elif sort_option == "default":
                order_by = "is_default DESC, rate DESC"

            query = f"""
                SELECT id, name, rate, description, valid_from, valid_to, is_default, active
                FROM codebook_vat_rates
                ORDER BY {order_by}
            """
            rates = db.fetch_all(query)

            self.all_data = rates
            self.filter_data()
            self.update_calculator_rates()
            self.update_current_rates_label()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst data:\n{e}")

    def filter_data(self):
        """Filtrování dat podle kritérií"""
        if not hasattr(self, 'all_data'):
            return

        filtered = self.all_data
        today = date.today().isoformat()

        # Filtr podle textu
        search_text = self.search_input.text().lower().strip()
        if search_text:
            filtered = [r for r in filtered if
                       search_text in r["name"].lower() or
                       search_text in (r["description"] or "").lower() or
                       search_text in str(r["rate"])]

        # Filtr podle stavu
        status_filter = self.status_filter.currentData()
        if status_filter == "active":
            filtered = [r for r in filtered if
                       r["active"] == 1 and
                       (r["valid_from"] is None or r["valid_from"] <= today) and
                       (r["valid_to"] is None or r["valid_to"] >= today)]
        elif status_filter == "future":
            filtered = [r for r in filtered if
                       r["valid_from"] is not None and r["valid_from"] > today]
        elif status_filter == "expired":
            filtered = [r for r in filtered if
                       r["valid_to"] is not None and r["valid_to"] < today]
        elif status_filter == "inactive":
            filtered = [r for r in filtered if r["active"] == 0]

        self.display_data(filtered)

    def display_data(self, data):
        """Zobrazení dat v tabulce"""
        self.table.setRowCount(len(data))
        today = date.today().isoformat()

        for row, rate in enumerate(data):
            # ID
            id_item = QTableWidgetItem(str(rate["id"]))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, id_item)

            # Název
            name_item = QTableWidgetItem(rate["name"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_font = QFont()
            name_font.setBold(True)
            name_item.setFont(name_font)
            self.table.setItem(row, 1, name_item)

            # Sazba
            rate_text = f"{rate['rate']:.0f}%"
            rate_item = QTableWidgetItem(rate_text)
            rate_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            rate_item.setFlags(rate_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            rate_font = QFont()
            rate_font.setPointSize(12)
            rate_font.setBold(True)
            rate_item.setFont(rate_font)
            if rate["rate"] == 0:
                rate_item.setForeground(QColor("#27ae60"))
            elif rate["rate"] == 21:
                rate_item.setForeground(QColor("#e74c3c"))
            else:
                rate_item.setForeground(QColor("#f39c12"))
            self.table.setItem(row, 2, rate_item)

            # Popis
            desc_item = QTableWidgetItem(rate["description"] or "")
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, desc_item)

            # Platná od
            valid_from_text = self.format_date(rate["valid_from"]) if rate["valid_from"] else "∞"
            valid_from_item = QTableWidgetItem(valid_from_text)
            valid_from_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            valid_from_item.setFlags(valid_from_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, valid_from_item)

            # Platná do
            valid_to_text = self.format_date(rate["valid_to"]) if rate["valid_to"] else "∞"
            valid_to_item = QTableWidgetItem(valid_to_text)
            valid_to_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            valid_to_item.setFlags(valid_to_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 5, valid_to_item)

            # Výchozí
            default_item = QTableWidgetItem("⭐" if rate["is_default"] else "")
            default_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            default_item.setFlags(default_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 6, default_item)

            # Stav
            if rate["active"] == 0:
                status_text = "❌ Neaktivní"
                status_color = QColor("#e74c3c")
            elif rate["valid_from"] and rate["valid_from"] > today:
                status_text = "📅 Budoucí"
                status_color = QColor("#3498db")
            elif rate["valid_to"] and rate["valid_to"] < today:
                status_text = "⏰ Prošlá"
                status_color = QColor("#95a5a6")
            else:
                status_text = "✅ Aktivní"
                status_color = QColor("#27ae60")

            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            status_item.setForeground(status_color)
            self.table.setItem(row, 7, status_item)

            # Akce
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.setSpacing(5)

            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Upravit")
            edit_btn.setFixedSize(30, 30)
            edit_btn.clicked.connect(lambda checked, r=rate: self.edit_rate(r))
            actions_layout.addWidget(edit_btn)

            if not rate["is_default"]:
                default_btn = QPushButton("⭐")
                default_btn.setToolTip("Nastavit jako výchozí")
                default_btn.setFixedSize(30, 30)
                default_btn.clicked.connect(lambda checked, r=rate: self.set_as_default(r))
                actions_layout.addWidget(default_btn)

            delete_btn = QPushButton("🗑️")
            delete_btn.setToolTip("Smazat")
            delete_btn.setFixedSize(30, 30)
            delete_btn.clicked.connect(lambda checked, r=rate: self.delete_rate(r))
            actions_layout.addWidget(delete_btn)

            self.table.setCellWidget(row, 8, actions_widget)

        self.count_label.setText(f"Celkem: {len(data)} sazeb")

    def format_date(self, date_str):
        """Formátování data do českého formátu"""
        if not date_str:
            return ""
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
            return d.strftime("%d.%m.%Y")
        except:
            return date_str

    def on_double_click(self, row, column):
        """Dvojklik na řádek - otevře editaci"""
        id_item = self.table.item(row, 0)
        if id_item:
            rate_id = int(id_item.text())
            for rate in self.all_data:
                if rate["id"] == rate_id:
                    self.edit_rate(rate)
                    break

    def add_rate(self):
        """Přidání nové sazby DPH"""
        dialog = VatRateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    INSERT INTO codebook_vat_rates
                    (name, rate, description, valid_from, valid_to, is_default, active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                db.execute_query(query, (
                    data["name"],
                    data["rate"],
                    data["description"],
                    data["valid_from"],
                    data["valid_to"],
                    data["is_default"],
                    data["active"]
                ))

                # Pokud je nastaven jako výchozí, zrušit u ostatních
                if data["is_default"]:
                    last_id = db.fetch_one("SELECT last_insert_rowid() as id")["id"]
                    query = "UPDATE codebook_vat_rates SET is_default = 0 WHERE id != ?"
                    db.execute_query(query, (last_id,))

                QMessageBox.information(self, "Úspěch", f"Sazba DPH '{data['name']}' byla přidána.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se přidat sazbu DPH:\n{e}")

    def edit_rate(self, rate):
        """Úprava sazby DPH"""
        dialog = VatRateDialog(self, rate)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    UPDATE codebook_vat_rates
                    SET name = ?, rate = ?, description = ?, valid_from = ?,
                        valid_to = ?, is_default = ?, active = ?
                    WHERE id = ?
                """
                db.execute_query(query, (
                    data["name"],
                    data["rate"],
                    data["description"],
                    data["valid_from"],
                    data["valid_to"],
                    data["is_default"],
                    data["active"],
                    rate["id"]
                ))

                # Pokud je nastaven jako výchozí, zrušit u ostatních
                if data["is_default"]:
                    query = "UPDATE codebook_vat_rates SET is_default = 0 WHERE id != ?"
                    db.execute_query(query, (rate["id"],))

                QMessageBox.information(self, "Úspěch", "Sazba DPH byla upravena.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se upravit sazbu DPH:\n{e}")

    def delete_rate(self, rate):
        """Smazání sazby DPH"""
        if rate["is_default"]:
            QMessageBox.warning(self, "Nelze smazat", "Nelze smazat výchozí sazbu DPH.")
            return

        reply = QMessageBox.question(
            self,
            "Smazat sazbu DPH",
            f"Opravdu chcete smazat sazbu '{rate['name']}'?\n\n"
            "Pro zachování historie je lepší sazbu deaktivovat.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = "DELETE FROM codebook_vat_rates WHERE id = ?"
                db.execute_query(query, (rate["id"],))

                QMessageBox.information(self, "Úspěch", "Sazba DPH byla smazána.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat sazbu DPH:\n{e}")

    def set_as_default(self, rate):
        """Nastavení jako výchozí"""
        try:
            # Zrušit výchozí u všech
            db.execute_query("UPDATE codebook_vat_rates SET is_default = 0")

            # Nastavit nový výchozí
            query = "UPDATE codebook_vat_rates SET is_default = 1, active = 1 WHERE id = ?"
            db.execute_query(query, (rate["id"],))

            QMessageBox.information(self, "Úspěch", f"'{rate['name']}' je nyní výchozí sazba DPH.")
            self.load_data()
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se nastavit výchozí:\n{e}")

    # =====================================================
    # KALKULÁTOR
    # =====================================================

    def update_calculator_rates(self):
        """Aktualizace sazeb v kalkulátoru"""
        if not hasattr(self, 'calc_rate'):
            return

        current_data = self.calc_rate.currentData()
        self.calc_rate.clear()

        today = date.today().isoformat()

        for rate in self.all_data:
            if rate["active"] == 1:
                # Kontrola platnosti
                if rate["valid_from"] and rate["valid_from"] > today:
                    continue
                if rate["valid_to"] and rate["valid_to"] < today:
                    continue

                text = f"{rate['name']} ({rate['rate']:.0f}%)"
                self.calc_rate.addItem(text, rate)

        # Obnovit výběr
        if current_data:
            for i in range(self.calc_rate.count()):
                if self.calc_rate.itemData(i) and self.calc_rate.itemData(i)["id"] == current_data["id"]:
                    self.calc_rate.setCurrentIndex(i)
                    break

        self.calculate_vat()

    def update_current_rates_label(self):
        """Aktualizace popisku aktuálních sazeb"""
        today = date.today().isoformat()
        current_rates = []

        for rate in self.all_data:
            if rate["active"] == 1:
                if rate["valid_from"] and rate["valid_from"] > today:
                    continue
                if rate["valid_to"] and rate["valid_to"] < today:
                    continue
                current_rates.append(f"{rate['rate']:.0f}%")

        if current_rates:
            self.current_rates_label.setText(f"Aktuální sazby: {', '.join(current_rates)}")
        else:
            self.current_rates_label.setText("Žádné aktivní sazby")

    def calculate_vat(self):
        """Výpočet DPH"""
        if not hasattr(self, 'calc_rate') or self.calc_rate.count() == 0:
            return

        rate_data = self.calc_rate.currentData()
        if not rate_data:
            return

        amount = self.calc_amount.value()
        rate = rate_data["rate"]

        vat_amount = amount * (rate / 100)
        total = amount + vat_amount

        self.calc_vat_amount.setText(f"{vat_amount:,.2f} Kč".replace(",", " "))
        self.calc_total.setText(f"{total:,.2f} Kč".replace(",", " "))

    # =====================================================
    # VÝCHOZÍ DATA
    # =====================================================

    def reset_to_default(self):
        """Obnovení výchozích sazeb DPH"""
        reply = QMessageBox.question(
            self,
            "Obnovit výchozí sazby DPH",
            "Opravdu chcete obnovit výchozí sazby DPH?\n\n"
            "Budou přidány chybějící sazby, existující zůstanou.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            default_rates = [
                ("Základní sazba", 21, "Základní sazba DPH 21%", 1),
                ("Snížená sazba", 12, "První snížená sazba DPH 12%", 0),
                ("Nulová sazba", 0, "Osvobozeno od DPH / přenesená daňová povinnost", 0),
            ]

            added = 0
            for name, rate, desc, is_default in default_rates:
                # Kontrola existence podle sazby
                check_query = "SELECT id FROM codebook_vat_rates WHERE rate = ? AND active = 1"
                existing = db.fetch_one(check_query, (rate,))

                if not existing:
                    query = """
                        INSERT INTO codebook_vat_rates
                        (name, rate, description, valid_from, valid_to, is_default, active)
                        VALUES (?, ?, ?, NULL, NULL, ?, 1)
                    """
                    db.execute_query(query, (name, rate, desc, is_default))
                    added += 1

            QMessageBox.information(
                self,
                "Dokončeno",
                f"Přidáno {added} výchozích sazeb DPH."
            )

            self.load_data()
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se obnovit výchozí sazby DPH:\n{e}")

    # =====================================================
    # IMPORT / EXPORT
    # =====================================================

    def import_csv(self):
        """Import sazeb DPH z CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importovat sazby DPH z CSV",
            "",
            "CSV soubory (*.csv)"
        )

        if not file_path:
            return

        try:
            imported = 0

            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')

                for row in reader:
                    name = dict(row).get("name", "").strip()
                    if not name:
                        continue

                    rate = float(dict(row).get("rate", 0))
                    description = dict(row).get("description", "").strip()
                    valid_from = dict(row).get("valid_from", "").strip() or None
                    valid_to = dict(row).get("valid_to", "").strip() or None
                    is_default = int(dict(row).get("is_default", 0))
                    active = int(dict(row).get("active", 1))

                    query = """
                        INSERT INTO codebook_vat_rates
                        (name, rate, description, valid_from, valid_to, is_default, active)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """
                    db.execute_query(query, (name, rate, description, valid_from, valid_to, is_default, active))
                    imported += 1

            QMessageBox.information(
                self,
                "Import dokončen",
                f"Importováno: {imported} sazeb DPH"
            )

            self.load_data()
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se importovat CSV:\n{e}")

    def export_csv(self):
        """Export sazeb DPH do CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportovat sazby DPH do CSV",
            f"sazby_dph_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV soubory (*.csv)"
        )

        if not file_path:
            return

        try:
            query = """
                SELECT name, rate, description, valid_from, valid_to, is_default, active
                FROM codebook_vat_rates
                ORDER BY rate DESC
            """
            rates = db.fetch_all(query)

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["name", "rate", "description", "valid_from", "valid_to",
                               "is_default", "active"],
                    delimiter=';'
                )
                writer.writeheader()

                for rate in rates:
                    writer.writerow({
                        "name": rate["name"],
                        "rate": rate["rate"],
                        "description": rate["description"] or "",
                        "valid_from": rate["valid_from"] or "",
                        "valid_to": rate["valid_to"] or "",
                        "is_default": rate["is_default"],
                        "active": rate["active"]
                    })

            QMessageBox.information(
                self,
                "Export dokončen",
                f"Exportováno {len(rates)} sazeb DPH do:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se exportovat CSV:\n{e}")

    # =====================================================
    # POMOCNÉ METODY
    # =====================================================

    def get_count(self):
        """Vrátí počet položek"""
        try:
            query = "SELECT COUNT(*) as count FROM codebook_vat_rates"
            result = db.fetch_one(query)
            return result["count"] if result else 0
        except:
            return 0

    def export_data(self):
        """Export dat pro zálohu"""
        try:
            query = """
                SELECT name, rate, description, valid_from, valid_to, is_default, active
                FROM codebook_vat_rates
            """
            return db.fetch_all(query)
        except:
            return []

    def import_data(self, data):
        """Import dat ze zálohy"""
        try:
            for item in data:
                query = """
                    INSERT INTO codebook_vat_rates
                    (name, rate, description, valid_from, valid_to, is_default, active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                db.execute_query(query, (
                    item["name"],
                    item["rate"],
                    item.get("description", ""),
                    item.get("valid_from"),
                    item.get("valid_to"),
                    item["is_default"],
                    item["active"]
                ))

            self.load_data()

        except Exception as e:
            print(f"Chyba při importu dat: {e}")

    def refresh(self):
        """Obnovení dat"""
        self.load_data()


# =====================================================
# DIALOG PRO SAZBU DPH
# =====================================================

class VatRateDialog(QDialog):
    """Dialog pro přidání/úpravu sazby DPH"""

    def __init__(self, parent, rate=None):
        super().__init__(parent)
        self.rate = rate
        self.setWindowTitle("Upravit sazbu DPH" if rate else "Nová sazba DPH")
        self.setMinimumWidth(500)
        self.init_ui()

        if rate:
            self.load_rate_data()

    def init_ui(self):
        """Inicializace UI"""
        layout = QFormLayout(self)

        # Název
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Např: Základní sazba, Snížená sazba...")
        layout.addRow("Název:", self.name_input)

        # Sazba
        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(0, 100)
        self.rate_input.setDecimals(1)
        self.rate_input.setSuffix(" %")
        self.rate_input.setValue(21)
        layout.addRow("Sazba DPH:", self.rate_input)

        # Rychlé nastavení
        quick_group = QGroupBox("Rychlé nastavení")
        quick_layout = QHBoxLayout(quick_group)

        btn_0 = QPushButton("0%")
        btn_0.clicked.connect(lambda: self.rate_input.setValue(0))
        quick_layout.addWidget(btn_0)

        btn_12 = QPushButton("12%")
        btn_12.clicked.connect(lambda: self.rate_input.setValue(12))
        quick_layout.addWidget(btn_12)

        btn_21 = QPushButton("21%")
        btn_21.clicked.connect(lambda: self.rate_input.setValue(21))
        quick_layout.addWidget(btn_21)

        layout.addRow(quick_group)

        # Popis
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("Popis použití sazby...")
        layout.addRow("Popis:", self.description_input)

        # Platnost
        validity_group = QGroupBox("Platnost sazby (volitelné)")
        validity_layout = QFormLayout(validity_group)

        self.has_valid_from = QCheckBox("Platná od konkrétního data")
        self.has_valid_from.stateChanged.connect(self.toggle_valid_from)
        validity_layout.addRow("", self.has_valid_from)

        self.valid_from_input = QDateEdit()
        self.valid_from_input.setCalendarPopup(True)
        self.valid_from_input.setDate(QDate.currentDate())
        self.valid_from_input.setDisplayFormat("dd.MM.yyyy")
        self.valid_from_input.setEnabled(False)
        validity_layout.addRow("Platná od:", self.valid_from_input)

        self.has_valid_to = QCheckBox("Platná do konkrétního data")
        self.has_valid_to.stateChanged.connect(self.toggle_valid_to)
        validity_layout.addRow("", self.has_valid_to)

        self.valid_to_input = QDateEdit()
        self.valid_to_input.setCalendarPopup(True)
        self.valid_to_input.setDate(QDate.currentDate().addYears(1))
        self.valid_to_input.setDisplayFormat("dd.MM.yyyy")
        self.valid_to_input.setEnabled(False)
        validity_layout.addRow("Platná do:", self.valid_to_input)

        validity_info = QLabel(
            "Ponechte prázdné pro sazbu bez časového omezení.\n"
            "Při změně legislativy vytvořte novou sazbu s novou platností."
        )
        validity_info.setStyleSheet("color: #7f8c8d; font-size: 9pt;")
        validity_layout.addRow("", validity_info)

        layout.addRow(validity_group)

        # Výchozí
        self.default_checkbox = QCheckBox("Nastavit jako výchozí sazbu DPH")
        layout.addRow("", self.default_checkbox)

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

        if self.rate and not self.rate["is_default"]:
            delete_btn = QPushButton("🗑️ Smazat")
            delete_btn.clicked.connect(self.delete_rate)
            delete_btn.setStyleSheet(f"background-color: {config.COLOR_DANGER}; color: white; padding: 8px 20px;")
            buttons_layout.addWidget(delete_btn)

        save_btn = QPushButton("💾 Uložit")
        save_btn.clicked.connect(self.save)
        save_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 20px;")
        buttons_layout.addWidget(save_btn)

        layout.addRow(buttons_layout)

    def toggle_valid_from(self):
        """Přepnutí pole platná od"""
        self.valid_from_input.setEnabled(self.has_valid_from.isChecked())

    def toggle_valid_to(self):
        """Přepnutí pole platná do"""
        self.valid_to_input.setEnabled(self.has_valid_to.isChecked())

    def load_rate_data(self):
        """Načtení dat sazby"""
        self.name_input.setText(self.rate["name"])
        self.rate_input.setValue(self.rate["rate"])
        self.description_input.setPlainText(self.rate["description"] or "")

        # Platnost od
        if self.rate["valid_from"]:
            self.has_valid_from.setChecked(True)
            try:
                d = datetime.strptime(self.rate["valid_from"], "%Y-%m-%d")
                self.valid_from_input.setDate(QDate(d.year, d.month, d.day))
            except:
                pass

        # Platnost do
        if self.rate["valid_to"]:
            self.has_valid_to.setChecked(True)
            try:
                d = datetime.strptime(self.rate["valid_to"], "%Y-%m-%d")
                self.valid_to_input.setDate(QDate(d.year, d.month, d.day))
            except:
                pass

        self.default_checkbox.setChecked(self.rate["is_default"] == 1)
        self.active_checkbox.setChecked(self.rate["active"] == 1)

    def delete_rate(self):
        """Smazání sazby z dialogu"""
        if self.rate:
            self.parent().delete_rate(self.rate)
            self.reject()

    def save(self):
        """Uložení sazby"""
        name = self.name_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Chyba", "Vyplňte název sazby.")
            return

        if self.has_valid_from.isChecked() and self.has_valid_to.isChecked():
            if self.valid_to_input.date() < self.valid_from_input.date():
                QMessageBox.warning(self, "Chyba", "Datum 'Platná do' musí být později než 'Platná od'.")
                return

        self.accept()

    def get_data(self):
        """Vrácení dat"""
        valid_from = None
        valid_to = None

        if self.has_valid_from.isChecked():
            valid_from = self.valid_from_input.date().toString("yyyy-MM-dd")

        if self.has_valid_to.isChecked():
            valid_to = self.valid_to_input.date().toString("yyyy-MM-dd")

        return {
            "name": self.name_input.text().strip(),
            "rate": self.rate_input.value(),
            "description": self.description_input.toPlainText().strip(),
            "valid_from": valid_from,
            "valid_to": valid_to,
            "is_default": 1 if self.default_checkbox.isChecked() else 0,
            "active": 1 if self.active_checkbox.isChecked() else 0
        }
