# -*- coding: utf-8 -*-
"""
Modul Číselníky - Hodinové sazby (PRODUKČNÍ VERZE)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QFrame,
                             QComboBox, QLineEdit, QHeaderView, QMessageBox,
                             QDialog, QFormLayout, QCheckBox, QFileDialog,
                             QDoubleSpinBox, QGroupBox, QDateEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, date
import csv
import config
from database_manager import db


class HourlyRatesWidget(QWidget):
    """Widget pro správu hodinových sazeb"""

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
            "ID", "Název", "Pozice", "Sazba bez DPH", "DPH %", "Sazba s DPH",
            "Platná od", "Platná do", "Stav"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 120)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 70)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 120)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 100)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(7, 100)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(8, 100)
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
        add_btn = QPushButton("➕ Přidat sazbu")
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

        info_icon = QLabel("💡")
        info_icon.setStyleSheet("font-size: 20pt;")
        layout.addWidget(info_icon)

        info_text = QLabel(
            "Hodinové sazby umožňují definovat různé ceny práce podle typu úkonu.\n"
            "Každá sazba může mít platnost od-do pro zachování historie změn."
        )
        info_text.setStyleSheet("font-size: 11pt;")
        layout.addWidget(info_text)

        layout.addStretch()

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

        # Filtr pozice
        layout.addWidget(QLabel("Pozice:"))
        self.position_filter = QComboBox()
        self.position_filter.addItem("Všechny pozice", "")
        self.load_positions_filter()
        self.position_filter.currentIndexChanged.connect(self.filter_data)
        layout.addWidget(self.position_filter)

        layout.addStretch()

        # Řazení
        layout.addWidget(QLabel("Řadit:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Podle názvu", "name")
        self.sort_combo.addItem("Podle sazby", "rate")
        self.sort_combo.addItem("Podle platnosti", "valid_from")
        self.sort_combo.addItem("Podle pozice", "position")
        self.sort_combo.currentIndexChanged.connect(self.load_data)
        layout.addWidget(self.sort_combo)

        return frame

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

    def load_positions_filter(self):
        """Načtení pozic do filtru"""
        try:
            query = "SELECT code, name FROM codebook_positions WHERE active = 1 ORDER BY name"
            positions = db.fetch_all(query)

            for pos in positions:
                self.position_filter.addItem(pos["name"], pos["code"])
        except:
            pass

    # =====================================================
    # CRUD OPERACE
    # =====================================================

    def load_data(self):
        """Načtení dat z databáze"""
        try:
            # Sestavení dotazu s řazením
            sort_option = self.sort_combo.currentData() if hasattr(self, 'sort_combo') else "name"

            order_by = "hr.name ASC"
            if sort_option == "rate":
                order_by = "hr.rate_without_vat DESC"
            elif sort_option == "valid_from":
                order_by = "hr.valid_from DESC"
            elif sort_option == "position":
                order_by = "p.name ASC, hr.name ASC"

            query = f"""
                SELECT hr.id, hr.name, hr.position_id, hr.rate_without_vat, hr.rate_with_vat,
                       hr.vat_rate, hr.valid_from, hr.valid_to, hr.active,
                       COALESCE(p.name, 'Všechny pozice') as position_name,
                       COALESCE(p.code, '') as position_code
                FROM codebook_hourly_rates hr
                LEFT JOIN codebook_positions p ON hr.position_id = p.id
                ORDER BY {order_by}
            """
            rates = db.fetch_all(query)

            self.all_data = rates
            self.filter_data()

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
                       search_text in r["position_name"].lower()]

        # Filtr podle stavu
        status_filter = self.status_filter.currentData()
        if status_filter == "active":
            # Aktivní a platné dnes
            filtered = [r for r in filtered if
                       r["active"] == 1 and
                       r["valid_from"] <= today and
                       (r["valid_to"] is None or r["valid_to"] >= today)]
        elif status_filter == "future":
            # Budoucí sazby
            filtered = [r for r in filtered if r["valid_from"] > today]
        elif status_filter == "expired":
            # Prošlé sazby
            filtered = [r for r in filtered if
                       r["valid_to"] is not None and r["valid_to"] < today]
        elif status_filter == "inactive":
            filtered = [r for r in filtered if r["active"] == 0]

        # Filtr podle pozice
        position_code = self.position_filter.currentData()
        if position_code:
            filtered = [r for r in filtered if r["position_code"] == position_code]

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

            # Pozice
            position_item = QTableWidgetItem(rate["position_name"])
            position_item.setFlags(position_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, position_item)

            # Sazba bez DPH
            rate_text = f"{rate['rate_without_vat']:,.0f} Kč/h".replace(",", " ")
            rate_item = QTableWidgetItem(rate_text)
            rate_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            rate_item.setFlags(rate_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, rate_item)

            # DPH %
            vat_item = QTableWidgetItem(f"{rate['vat_rate']:.0f}%")
            vat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            vat_item.setFlags(vat_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, vat_item)

            # Sazba s DPH
            rate_vat_text = f"{rate['rate_with_vat']:,.0f} Kč/h".replace(",", " ")
            rate_vat_item = QTableWidgetItem(rate_vat_text)
            rate_vat_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            rate_vat_item.setFlags(rate_vat_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 5, rate_vat_item)

            # Platná od
            valid_from_text = self.format_date(rate["valid_from"])
            valid_from_item = QTableWidgetItem(valid_from_text)
            valid_from_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            valid_from_item.setFlags(valid_from_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 6, valid_from_item)

            # Platná do
            valid_to_text = self.format_date(rate["valid_to"]) if rate["valid_to"] else "∞"
            valid_to_item = QTableWidgetItem(valid_to_text)
            valid_to_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            valid_to_item.setFlags(valid_to_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 7, valid_to_item)

            # Stav
            if rate["active"] == 0:
                status_text = "❌ Neaktivní"
                status_color = QColor("#e74c3c")
            elif rate["valid_from"] > today:
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
            self.table.setItem(row, 8, status_item)

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
        """Přidání nové sazby"""
        dialog = HourlyRateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    INSERT INTO codebook_hourly_rates
                    (name, position_id, rate_without_vat, rate_with_vat, vat_rate,
                     valid_from, valid_to, active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                db.execute_query(query, (
                    data["name"],
                    data["position_id"],
                    data["rate_without_vat"],
                    data["rate_with_vat"],
                    data["vat_rate"],
                    data["valid_from"],
                    data["valid_to"],
                    data["active"]
                ))

                QMessageBox.information(self, "Úspěch", f"Sazba '{data['name']}' byla přidána.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se přidat sazbu:\n{e}")

    def edit_rate(self, rate):
        """Úprava sazby"""
        dialog = HourlyRateDialog(self, rate)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    UPDATE codebook_hourly_rates
                    SET name = ?, position_id = ?, rate_without_vat = ?, rate_with_vat = ?,
                        vat_rate = ?, valid_from = ?, valid_to = ?, active = ?
                    WHERE id = ?
                """
                db.execute_query(query, (
                    data["name"],
                    data["position_id"],
                    data["rate_without_vat"],
                    data["rate_with_vat"],
                    data["vat_rate"],
                    data["valid_from"],
                    data["valid_to"],
                    data["active"],
                    rate["id"]
                ))

                QMessageBox.information(self, "Úspěch", "Sazba byla upravena.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se upravit sazbu:\n{e}")

    def delete_rate(self, rate):
        """Smazání sazby"""
        reply = QMessageBox.question(
            self,
            "Smazat sazbu",
            f"Opravdu chcete smazat sazbu '{rate['name']}'?\n\n"
            "Pro zachování historie je lepší sazbu deaktivovat.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = "DELETE FROM codebook_hourly_rates WHERE id = ?"
                db.execute_query(query, (rate["id"],))

                QMessageBox.information(self, "Úspěch", "Sazba byla smazána.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat sazbu:\n{e}")

    # =====================================================
    # IMPORT / EXPORT
    # =====================================================

    def import_csv(self):
        """Import sazeb z CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importovat sazby z CSV",
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

                    position_code = dict(row).get("position_code", "").strip()
                    rate_without_vat = float(dict(row).get("rate_without_vat", 0))
                    vat_rate = float(dict(row).get("vat_rate", 21))
                    rate_with_vat = rate_without_vat * (1 + vat_rate / 100)
                    valid_from = dict(row).get("valid_from", date.today().isoformat())
                    valid_to = dict(row).get("valid_to", "").strip() or None
                    active = int(dict(row).get("active", 1))

                    # Najít position_id
                    position_id = None
                    if position_code:
                        pos_query = "SELECT id FROM codebook_positions WHERE code = ?"
                        pos_result = db.fetch_one(pos_query, (position_code,))
                        if pos_result:
                            position_id = pos_result["id"]

                    query = """
                        INSERT INTO codebook_hourly_rates
                        (name, position_id, rate_without_vat, rate_with_vat, vat_rate,
                         valid_from, valid_to, active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    db.execute_query(query, (
                        name, position_id, rate_without_vat, rate_with_vat,
                        vat_rate, valid_from, valid_to, active
                    ))
                    imported += 1

            QMessageBox.information(
                self,
                "Import dokončen",
                f"Importováno: {imported} sazeb"
            )

            self.load_data()
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se importovat CSV:\n{e}")

    def export_csv(self):
        """Export sazeb do CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportovat sazby do CSV",
            f"hodinove_sazby_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV soubory (*.csv)"
        )

        if not file_path:
            return

        try:
            query = """
                SELECT hr.name, COALESCE(p.code, '') as position_code,
                       hr.rate_without_vat, hr.vat_rate, hr.rate_with_vat,
                       hr.valid_from, hr.valid_to, hr.active
                FROM codebook_hourly_rates hr
                LEFT JOIN codebook_positions p ON hr.position_id = p.id
                ORDER BY hr.name
            """
            rates = db.fetch_all(query)

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["name", "position_code", "rate_without_vat", "vat_rate",
                               "rate_with_vat", "valid_from", "valid_to", "active"],
                    delimiter=';'
                )
                writer.writeheader()

                for rate in rates:
                    writer.writerow({
                        "name": rate["name"],
                        "position_code": rate["position_code"],
                        "rate_without_vat": rate["rate_without_vat"],
                        "vat_rate": rate["vat_rate"],
                        "rate_with_vat": rate["rate_with_vat"],
                        "valid_from": rate["valid_from"],
                        "valid_to": rate["valid_to"] or "",
                        "active": rate["active"]
                    })

            QMessageBox.information(
                self,
                "Export dokončen",
                f"Exportováno {len(rates)} sazeb do:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se exportovat CSV:\n{e}")

    def reset_to_default(self):
        """Obnovení výchozích sazeb"""
        reply = QMessageBox.question(
            self,
            "Obnovit výchozí sazby",
            "Opravdu chcete přidat výchozí sazby?\n\n"
            "Existující sazby zůstanou zachovány.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            today = date.today().isoformat()

            default_rates = [
                ("Mechanik - standardní", None, 800, 21),
                ("Mechanik - víkend/svátky", None, 1200, 21),
                ("Mechanik - noční", None, 1000, 21),
                ("Diagnostika", None, 1000, 21),
                ("Lakýrnictví", None, 900, 21),
                ("Elektrikář", None, 1100, 21),
                ("Pneuservis", None, 600, 21),
                ("Karosářské práce", None, 950, 21),
                ("Montáž příslušenství", None, 700, 21),
            ]

            added = 0
            for name, position_id, rate, vat in default_rates:
                rate_with_vat = rate * (1 + vat / 100)

                query = """
                    INSERT INTO codebook_hourly_rates
                    (name, position_id, rate_without_vat, rate_with_vat, vat_rate,
                     valid_from, valid_to, active)
                    VALUES (?, ?, ?, ?, ?, ?, NULL, 1)
                """
                db.execute_query(query, (name, position_id, rate, rate_with_vat, vat, today))
                added += 1

            QMessageBox.information(
                self,
                "Dokončeno",
                f"Přidáno {added} výchozích sazeb."
            )

            self.load_data()
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se obnovit výchozí sazby:\n{e}")

    # =====================================================
    # POMOCNÉ METODY
    # =====================================================

    def get_count(self):
        """Vrátí počet položek"""
        try:
            query = "SELECT COUNT(*) as count FROM codebook_hourly_rates"
            result = db.fetch_one(query)
            return result["count"] if result else 0
        except:
            return 0

    def export_data(self):
        """Export dat pro zálohu"""
        try:
            query = """
                SELECT hr.name, COALESCE(p.code, '') as position_code,
                       hr.rate_without_vat, hr.vat_rate, hr.rate_with_vat,
                       hr.valid_from, hr.valid_to, hr.active
                FROM codebook_hourly_rates hr
                LEFT JOIN codebook_positions p ON hr.position_id = p.id
            """
            return db.fetch_all(query)
        except:
            return []

    def import_data(self, data):
        """Import dat ze zálohy"""
        try:
            for item in data:
                position_id = None
                if item.get("position_code"):
                    pos_query = "SELECT id FROM codebook_positions WHERE code = ?"
                    pos_result = db.fetch_one(pos_query, (item["position_code"],))
                    if pos_result:
                        position_id = pos_result["id"]

                query = """
                    INSERT INTO codebook_hourly_rates
                    (name, position_id, rate_without_vat, rate_with_vat, vat_rate,
                     valid_from, valid_to, active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                db.execute_query(query, (
                    item["name"],
                    position_id,
                    item["rate_without_vat"],
                    item["rate_with_vat"],
                    item["vat_rate"],
                    item["valid_from"],
                    item.get("valid_to"),
                    item["active"]
                ))

            self.load_data()

        except Exception as e:
            print(f"Chyba při importu dat: {e}")

    def refresh(self):
        """Obnovení dat"""
        self.load_positions_filter()
        self.load_data()


# =====================================================
# DIALOG PRO HODINOVOU SAZBU
# =====================================================

class HourlyRateDialog(QDialog):
    """Dialog pro přidání/úpravu hodinové sazby"""

    def __init__(self, parent, rate=None):
        super().__init__(parent)
        self.rate = rate
        self.setWindowTitle("Upravit sazbu" if rate else "Nová hodinová sazba")
        self.setMinimumWidth(500)
        self.init_ui()

        if rate:
            self.load_rate_data()

    def init_ui(self):
        """Inicializace UI"""
        layout = QFormLayout(self)

        # Název
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Např: Mechanik - standardní, Diagnostika...")
        layout.addRow("Název sazby:", self.name_input)

        # Pozice
        self.position_combo = QComboBox()
        self.position_combo.addItem("Všechny pozice (obecná sazba)", None)
        self.load_positions()
        layout.addRow("Pozice:", self.position_combo)

        # Sazby
        rates_group = QGroupBox("Hodinová sazba")
        rates_layout = QFormLayout(rates_group)

        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(0, 99999)
        self.rate_input.setDecimals(0)
        self.rate_input.setSuffix(" Kč/h")
        self.rate_input.setValue(800)
        self.rate_input.valueChanged.connect(self.calculate_vat)
        rates_layout.addRow("Sazba bez DPH:", self.rate_input)

        self.vat_input = QDoubleSpinBox()
        self.vat_input.setRange(0, 100)
        self.vat_input.setDecimals(0)
        self.vat_input.setSuffix(" %")
        self.vat_input.setValue(21)
        self.vat_input.valueChanged.connect(self.calculate_vat)
        rates_layout.addRow("DPH:", self.vat_input)

        self.rate_with_vat_label = QLabel("968 Kč/h")
        self.rate_with_vat_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: #27ae60;")
        rates_layout.addRow("Sazba s DPH:", self.rate_with_vat_label)

        layout.addRow(rates_group)

        # Platnost
        validity_group = QGroupBox("Platnost sazby")
        validity_layout = QFormLayout(validity_group)

        self.valid_from_input = QDateEdit()
        self.valid_from_input.setCalendarPopup(True)
        self.valid_from_input.setDate(QDate.currentDate())
        self.valid_from_input.setDisplayFormat("dd.MM.yyyy")
        validity_layout.addRow("Platná od:", self.valid_from_input)

        self.has_valid_to = QCheckBox("Omezená platnost")
        self.has_valid_to.stateChanged.connect(self.toggle_valid_to)
        validity_layout.addRow("", self.has_valid_to)

        self.valid_to_input = QDateEdit()
        self.valid_to_input.setCalendarPopup(True)
        self.valid_to_input.setDate(QDate.currentDate().addYears(1))
        self.valid_to_input.setDisplayFormat("dd.MM.yyyy")
        self.valid_to_input.setEnabled(False)
        validity_layout.addRow("Platná do:", self.valid_to_input)

        validity_info = QLabel(
            "Neomezená platnost znamená, že sazba bude platit do doby,\n"
            "než ji ručně ukončíte nebo nahradíte novou."
        )
        validity_info.setStyleSheet("color: #7f8c8d; font-size: 9pt;")
        validity_layout.addRow("", validity_info)

        layout.addRow(validity_group)

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

        if self.rate:
            delete_btn = QPushButton("🗑️ Smazat")
            delete_btn.clicked.connect(self.delete_rate)
            delete_btn.setStyleSheet(f"background-color: {config.COLOR_DANGER}; color: white; padding: 8px 20px;")
            buttons_layout.addWidget(delete_btn)

        save_btn = QPushButton("💾 Uložit")
        save_btn.clicked.connect(self.save)
        save_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 20px;")
        buttons_layout.addWidget(save_btn)

        layout.addRow(buttons_layout)

        # Inicializovat výpočet
        self.calculate_vat()

    def load_positions(self):
        """Načtení pozic do comboboxu"""
        try:
            query = "SELECT id, code, name FROM codebook_positions WHERE active = 1 ORDER BY name"
            positions = db.fetch_all(query)

            for pos in positions:
                self.position_combo.addItem(f"{pos['name']} ({pos['code']})", pos["id"])
        except:
            pass

    def calculate_vat(self):
        """Výpočet sazby s DPH"""
        rate = self.rate_input.value()
        vat = self.vat_input.value()
        rate_with_vat = rate * (1 + vat / 100)
        self.rate_with_vat_label.setText(f"{rate_with_vat:,.0f} Kč/h".replace(",", " "))

    def toggle_valid_to(self):
        """Přepnutí pole platná do"""
        self.valid_to_input.setEnabled(self.has_valid_to.isChecked())

    def load_rate_data(self):
        """Načtení dat sazby"""
        self.name_input.setText(self.rate["name"])

        # Pozice
        if self.rate["position_id"]:
            for i in range(self.position_combo.count()):
                if self.position_combo.itemData(i) == self.rate["position_id"]:
                    self.position_combo.setCurrentIndex(i)
                    break

        self.rate_input.setValue(self.rate["rate_without_vat"])
        self.vat_input.setValue(self.rate["vat_rate"])

        # Platnost od
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

        self.active_checkbox.setChecked(self.rate["active"] == 1)
        self.calculate_vat()

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

        if self.has_valid_to.isChecked():
            if self.valid_to_input.date() < self.valid_from_input.date():
                QMessageBox.warning(self, "Chyba", "Datum 'Platná do' musí být později než 'Platná od'.")
                return

        self.accept()

    def get_data(self):
        """Vrácení dat"""
        rate_without_vat = self.rate_input.value()
        vat_rate = self.vat_input.value()
        rate_with_vat = rate_without_vat * (1 + vat_rate / 100)

        valid_to = None
        if self.has_valid_to.isChecked():
            valid_to = self.valid_to_input.date().toString("yyyy-MM-dd")

        return {
            "name": self.name_input.text().strip(),
            "position_id": self.position_combo.currentData(),
            "rate_without_vat": rate_without_vat,
            "rate_with_vat": rate_with_vat,
            "vat_rate": vat_rate,
            "valid_from": self.valid_from_input.date().toString("yyyy-MM-dd"),
            "valid_to": valid_to,
            "active": 1 if self.active_checkbox.isChecked() else 0
        }
