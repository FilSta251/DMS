# -*- coding: utf-8 -*-
"""
Modul Číselníky - Měny (PRODUKČNÍ VERZE)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QFrame,
                             QComboBox, QLineEdit, QHeaderView, QMessageBox,
                             QDialog, QFormLayout, QCheckBox, QFileDialog,
                             QDoubleSpinBox, QSpinBox, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
import csv
import config
from database_manager import db


class CurrenciesWidget(QWidget):
    """Widget pro správu měn"""

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

        # Tabulka
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "ISO kód", "Název", "Symbol", "Pozice", "Des. místa",
            "Kurz k CZK", "Výchozí", "Aktivní"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 80)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 70)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 70)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 80)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 100)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(7, 70)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(8, 70)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self.on_double_click)
        layout.addWidget(self.table)

        # Kalkulátor měn
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
        add_btn = QPushButton("➕ Přidat měnu")
        add_btn.clicked.connect(self.add_currency)
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

        update_rates_btn = QPushButton("🔄 Aktualizovat kurzy (ČNB)")
        update_rates_btn.clicked.connect(self.update_rates_from_cnb)
        update_rates_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_WARNING};
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
            }}
        """)
        layout.addWidget(update_rates_btn)

        reset_btn = QPushButton("🔄 Obnovit výchozí")
        reset_btn.clicked.connect(self.reset_to_default)
        layout.addWidget(reset_btn)

        layout.addStretch()

        # Vyhledávání
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Vyhledat měnu...")
        self.search_input.setFixedWidth(200)
        self.search_input.textChanged.connect(self.filter_data)
        layout.addWidget(self.search_input)

        return frame

    def create_info_panel(self):
        """Vytvoření informačního panelu"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #d5f5e3;
                border-radius: 4px;
                padding: 10px;
                border: 1px solid #27ae60;
            }
        """)
        layout = QHBoxLayout(frame)

        info_icon = QLabel("💡")
        info_icon.setStyleSheet("font-size: 20pt;")
        layout.addWidget(info_icon)

        info_text = QLabel(
            "Kurzy měn lze aktualizovat ručně nebo automaticky z ČNB.\n"
            "Výchozí měna (CZK) má vždy kurz 1.00 a nelze ji změnit."
        )
        info_text.setStyleSheet("font-size: 11pt;")
        layout.addWidget(info_text)

        layout.addStretch()

        self.last_update_cnb = QLabel("Poslední aktualizace: -")
        self.last_update_cnb.setStyleSheet("color: #27ae60; font-weight: bold;")
        layout.addWidget(self.last_update_cnb)

        return frame

    def create_calculator_panel(self):
        """Vytvoření kalkulátoru měn"""
        group = QGroupBox("💱 Kalkulátor měn")
        layout = QHBoxLayout(group)

        # Částka
        layout.addWidget(QLabel("Částka:"))
        self.calc_amount = QDoubleSpinBox()
        self.calc_amount.setRange(0, 999999999)
        self.calc_amount.setDecimals(2)
        self.calc_amount.setValue(1000)
        self.calc_amount.valueChanged.connect(self.calculate_conversion)
        layout.addWidget(self.calc_amount)

        # Z měny
        layout.addWidget(QLabel("Z:"))
        self.calc_from = QComboBox()
        self.calc_from.currentIndexChanged.connect(self.calculate_conversion)
        layout.addWidget(self.calc_from)

        # Do měny
        layout.addWidget(QLabel("Do:"))
        self.calc_to = QComboBox()
        self.calc_to.currentIndexChanged.connect(self.calculate_conversion)
        layout.addWidget(self.calc_to)

        # Výsledek
        layout.addWidget(QLabel("="))
        self.calc_result = QLabel("0.00")
        self.calc_result.setStyleSheet("font-weight: bold; font-size: 14pt; color: #27ae60;")
        layout.addWidget(self.calc_result)

        # Swap tlačítko
        swap_btn = QPushButton("⇄")
        swap_btn.setToolTip("Prohodit měny")
        swap_btn.setFixedSize(40, 30)
        swap_btn.clicked.connect(self.swap_currencies)
        layout.addWidget(swap_btn)

        layout.addStretch()

        return group

    def create_bottom_panel(self):
        """Vytvoření spodního panelu"""
        frame = QFrame()
        layout = QHBoxLayout(frame)

        self.count_label = QLabel("Celkem: 0 měn")
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
            query = """
                SELECT id, iso_code, name, symbol, symbol_position, decimal_places,
                       exchange_rate, is_default, active
                FROM codebook_currencies
                ORDER BY is_default DESC, iso_code ASC
            """
            currencies = db.fetch_all(query)

            self.all_data = currencies
            self.filter_data()
            self.update_calculator_combos()

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
            filtered = [c for c in filtered if
                       search_text in c["name"].lower() or
                       search_text in c["iso_code"].lower() or
                       search_text in c["symbol"].lower()]

        self.display_data(filtered)

    def display_data(self, data):
        """Zobrazení dat v tabulce"""
        self.table.setRowCount(len(data))

        for row, currency in enumerate(data):
            # ID
            id_item = QTableWidgetItem(str(currency["id"]))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, id_item)

            # ISO kód
            code_item = QTableWidgetItem(currency["iso_code"])
            code_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            code_item.setFlags(code_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            code_font = QFont()
            code_font.setBold(True)
            code_item.setFont(code_font)
            if currency["is_default"]:
                code_item.setForeground(QColor("#27ae60"))
            self.table.setItem(row, 1, code_item)

            # Název
            name_item = QTableWidgetItem(currency["name"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, name_item)

            # Symbol
            symbol_item = QTableWidgetItem(currency["symbol"])
            symbol_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            symbol_item.setFlags(symbol_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            symbol_font = QFont()
            symbol_font.setPointSize(12)
            symbol_item.setFont(symbol_font)
            self.table.setItem(row, 3, symbol_item)

            # Pozice symbolu
            position_text = "Za" if currency["symbol_position"] == "after" else "Před"
            position_item = QTableWidgetItem(position_text)
            position_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            position_item.setFlags(position_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, position_item)

            # Desetinná místa
            decimal_item = QTableWidgetItem(str(currency["decimal_places"]))
            decimal_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            decimal_item.setFlags(decimal_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 5, decimal_item)

            # Kurz
            rate_item = QTableWidgetItem(f"{currency['exchange_rate']:.4f}")
            rate_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            rate_item.setFlags(rate_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 6, rate_item)

            # Výchozí
            default_item = QTableWidgetItem("⭐" if currency["is_default"] else "")
            default_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            default_item.setFlags(default_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 7, default_item)

            # Aktivní
            active_item = QTableWidgetItem("✅" if currency["active"] else "❌")
            active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            active_item.setFlags(active_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if not currency["active"]:
                active_item.setForeground(QColor("#e74c3c"))
            self.table.setItem(row, 8, active_item)

        self.count_label.setText(f"Celkem: {len(data)} měn")

    def on_double_click(self, row, column):
        """Dvojklik na řádek - otevře editaci"""
        id_item = self.table.item(row, 0)
        if id_item:
            currency_id = int(id_item.text())
            for currency in self.all_data:
                if currency["id"] == currency_id:
                    self.edit_currency(currency)
                    break

    def add_currency(self):
        """Přidání nové měny"""
        dialog = CurrencyDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    INSERT INTO codebook_currencies
                    (iso_code, name, symbol, symbol_position, decimal_places,
                     exchange_rate, is_default, active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                db.execute_query(query, (
                    data["iso_code"],
                    data["name"],
                    data["symbol"],
                    data["symbol_position"],
                    data["decimal_places"],
                    data["exchange_rate"],
                    data["is_default"],
                    data["active"]
                ))

                QMessageBox.information(self, "Úspěch", f"Měna '{data['name']}' byla přidána.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    QMessageBox.warning(self, "Chyba", f"Měna s kódem '{data['iso_code']}' již existuje.")
                else:
                    QMessageBox.critical(self, "Chyba", f"Nepodařilo se přidat měnu:\n{e}")

    def edit_currency(self, currency):
        """Úprava měny"""
        dialog = CurrencyDialog(self, currency)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    UPDATE codebook_currencies
                    SET iso_code = ?, name = ?, symbol = ?, symbol_position = ?,
                        decimal_places = ?, exchange_rate = ?, is_default = ?, active = ?
                    WHERE id = ?
                """
                db.execute_query(query, (
                    data["iso_code"],
                    data["name"],
                    data["symbol"],
                    data["symbol_position"],
                    data["decimal_places"],
                    data["exchange_rate"],
                    data["is_default"],
                    data["active"],
                    currency["id"]
                ))

                # Pokud je nastavena jako výchozí, zrušit u ostatních
                if data["is_default"]:
                    query = "UPDATE codebook_currencies SET is_default = 0 WHERE id != ?"
                    db.execute_query(query, (currency["id"],))

                QMessageBox.information(self, "Úspěch", "Měna byla upravena.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se upravit měnu:\n{e}")

    def delete_currency(self, currency):
        """Smazání měny"""
        if currency["is_default"]:
            QMessageBox.warning(self, "Nelze smazat", "Nelze smazat výchozí měnu.")
            return

        reply = QMessageBox.question(
            self,
            "Smazat měnu",
            f"Opravdu chcete smazat měnu '{currency['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = "DELETE FROM codebook_currencies WHERE id = ?"
                db.execute_query(query, (currency["id"],))

                QMessageBox.information(self, "Úspěch", "Měna byla smazána.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat měnu:\n{e}")

    # =====================================================
    # KURZY A KALKULACE
    # =====================================================

    def update_rates_from_cnb(self):
        """Aktualizace kurzů z ČNB API"""
        try:
            import urllib.request
            import ssl

            # ČNB kurzovní lístek
            url = "https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt"

            # Ignorovat SSL certifikát (pro jednoduchost)
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(url, context=context, timeout=10) as response:
                data = response.read().decode('utf-8')

            # Parsování dat
            lines = data.strip().split('\n')
            if len(lines) < 3:
                raise ValueError("Neplatná data z ČNB")

            # První řádek obsahuje datum
            date_line = lines[0]

            # Kurzy začínají od řádku 3
            updated_count = 0
            for line in lines[2:]:
                parts = line.split('|')
                if len(parts) >= 5:
                    country = parts[0].strip()
                    currency_name = parts[1].strip()
                    amount = int(parts[2].strip())
                    iso_code = parts[3].strip()
                    rate_str = parts[4].strip().replace(',', '.')
                    rate = float(rate_str) / amount

                    # Aktualizovat kurz v databázi
                    query = "UPDATE codebook_currencies SET exchange_rate = ? WHERE iso_code = ?"
                    result = db.execute_query(query, (rate, iso_code))
                    if result:
                        updated_count += 1

            self.last_update_cnb.setText(f"Poslední aktualizace: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

            QMessageBox.information(
                self,
                "Kurzy aktualizovány",
                f"Aktualizováno {updated_count} kurzů z ČNB.\n\n"
                f"Datum kurzovního lístku: {date_line}"
            )

            self.load_data()

        except Exception as e:
            QMessageBox.warning(
                self,
                "Chyba aktualizace",
                f"Nepodařilo se stáhnout kurzy z ČNB:\n{e}\n\n"
                "Kurzy můžete aktualizovat ručně."
            )

    def update_calculator_combos(self):
        """Aktualizace comboboxů kalkulátoru"""
        if not hasattr(self, 'calc_from'):
            return

        current_from = self.calc_from.currentData()
        current_to = self.calc_to.currentData()

        self.calc_from.clear()
        self.calc_to.clear()

        for currency in self.all_data:
            if currency["active"]:
                text = f"{currency['iso_code']} - {currency['name']}"
                self.calc_from.addItem(text, currency)
                self.calc_to.addItem(text, currency)

        # Obnovit výběr
        if current_from:
            for i in range(self.calc_from.count()):
                if self.calc_from.itemData(i) and self.calc_from.itemData(i)["iso_code"] == current_from["iso_code"]:
                    self.calc_from.setCurrentIndex(i)
                    break

        if current_to:
            for i in range(self.calc_to.count()):
                if self.calc_to.itemData(i) and self.calc_to.itemData(i)["iso_code"] == current_to["iso_code"]:
                    self.calc_to.setCurrentIndex(i)
                    break

        self.calculate_conversion()

    def calculate_conversion(self):
        """Výpočet převodu měn"""
        if not hasattr(self, 'calc_from') or self.calc_from.count() == 0:
            return

        from_currency = self.calc_from.currentData()
        to_currency = self.calc_to.currentData()

        if not from_currency or not to_currency:
            return

        amount = self.calc_amount.value()

        # Převod přes CZK
        # amount * from_rate = CZK
        # CZK / to_rate = amount in to_currency
        czk_amount = amount * from_currency["exchange_rate"]
        result = czk_amount / to_currency["exchange_rate"]

        decimals = to_currency["decimal_places"]
        symbol = to_currency["symbol"]
        position = to_currency["symbol_position"]

        if position == "before":
            result_text = f"{symbol}{result:,.{decimals}f}".replace(",", " ")
        else:
            result_text = f"{result:,.{decimals}f} {symbol}".replace(",", " ")

        self.calc_result.setText(result_text)

    def swap_currencies(self):
        """Prohodit měny v kalkulátoru"""
        from_index = self.calc_from.currentIndex()
        to_index = self.calc_to.currentIndex()

        self.calc_from.setCurrentIndex(to_index)
        self.calc_to.setCurrentIndex(from_index)

    # =====================================================
    # VÝCHOZÍ DATA
    # =====================================================

    def reset_to_default(self):
        """Obnovení výchozích měn"""
        reply = QMessageBox.question(
            self,
            "Obnovit výchozí měny",
            "Opravdu chcete obnovit výchozí měny?\n\n"
            "Budou přidány chybějící měny, existující zůstanou.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            default_currencies = [
                ("CZK", "Česká koruna", "Kč", "after", 2, 1.0, 1),
                ("EUR", "Euro", "€", "before", 2, 25.0, 0),
                ("USD", "Americký dolar", "$", "before", 2, 23.0, 0),
                ("GBP", "Britská libra", "£", "before", 2, 29.0, 0),
                ("PLN", "Polský zlotý", "zł", "after", 2, 5.8, 0),
                ("CHF", "Švýcarský frank", "CHF", "before", 2, 26.0, 0),
            ]

            added = 0
            for iso_code, name, symbol, position, decimals, rate, is_default in default_currencies:
                check_query = "SELECT id FROM codebook_currencies WHERE iso_code = ?"
                existing = db.fetch_one(check_query, (iso_code,))

                if not existing:
                    query = """
                        INSERT INTO codebook_currencies
                        (iso_code, name, symbol, symbol_position, decimal_places,
                         exchange_rate, is_default, active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    """
                    db.execute_query(query, (iso_code, name, symbol, position, decimals, rate, is_default))
                    added += 1

            QMessageBox.information(
                self,
                "Dokončeno",
                f"Přidáno {added} výchozích měn."
            )

            self.load_data()
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se obnovit výchozí měny:\n{e}")

    # =====================================================
    # POMOCNÉ METODY
    # =====================================================

    def get_count(self):
        """Vrátí počet položek"""
        try:
            query = "SELECT COUNT(*) as count FROM codebook_currencies"
            result = db.fetch_one(query)
            return result["count"] if result else 0
        except:
            return 0

    def export_data(self):
        """Export dat pro zálohu"""
        try:
            query = """
                SELECT iso_code, name, symbol, symbol_position, decimal_places,
                       exchange_rate, is_default, active
                FROM codebook_currencies
            """
            return db.fetch_all(query)
        except:
            return []

    def import_data(self, data):
        """Import dat ze zálohy"""
        try:
            for item in data:
                check_query = "SELECT id FROM codebook_currencies WHERE iso_code = ?"
                existing = db.fetch_one(check_query, (item["iso_code"],))

                if existing:
                    query = """
                        UPDATE codebook_currencies
                        SET name = ?, symbol = ?, symbol_position = ?, decimal_places = ?,
                            exchange_rate = ?, is_default = ?, active = ?
                        WHERE iso_code = ?
                    """
                    db.execute_query(query, (
                        item["name"],
                        item["symbol"],
                        item["symbol_position"],
                        item["decimal_places"],
                        item["exchange_rate"],
                        item["is_default"],
                        item["active"],
                        item["iso_code"]
                    ))
                else:
                    query = """
                        INSERT INTO codebook_currencies
                        (iso_code, name, symbol, symbol_position, decimal_places,
                         exchange_rate, is_default, active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    db.execute_query(query, (
                        item["iso_code"],
                        item["name"],
                        item["symbol"],
                        item["symbol_position"],
                        item["decimal_places"],
                        item["exchange_rate"],
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
# DIALOG PRO MĚNU
# =====================================================

class CurrencyDialog(QDialog):
    """Dialog pro přidání/úpravu měny"""

    def __init__(self, parent, currency=None):
        super().__init__(parent)
        self.currency = currency
        self.setWindowTitle("Upravit měnu" if currency else "Nová měna")
        self.setMinimumWidth(450)
        self.init_ui()

        if currency:
            self.load_currency_data()

    def init_ui(self):
        """Inicializace UI"""
        layout = QFormLayout(self)

        # ISO kód
        self.iso_code_input = QLineEdit()
        self.iso_code_input.setPlaceholderText("Např: CZK, EUR, USD...")
        self.iso_code_input.setMaxLength(3)
        layout.addRow("ISO kód:", self.iso_code_input)

        # Název
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Např: Česká koruna, Euro...")
        layout.addRow("Název:", self.name_input)

        # Symbol
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Např: Kč, €, $...")
        self.symbol_input.setMaxLength(5)
        layout.addRow("Symbol:", self.symbol_input)

        # Pozice symbolu
        self.position_combo = QComboBox()
        self.position_combo.addItem("Za částkou (100 Kč)", "after")
        self.position_combo.addItem("Před částkou (€100)", "before")
        layout.addRow("Pozice symbolu:", self.position_combo)

        # Desetinná místa
        self.decimal_input = QSpinBox()
        self.decimal_input.setRange(0, 4)
        self.decimal_input.setValue(2)
        layout.addRow("Desetinná místa:", self.decimal_input)

        # Kurz
        rate_group = QGroupBox("Kurz k CZK")
        rate_layout = QFormLayout(rate_group)

        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(0.0001, 999999)
        self.rate_input.setDecimals(4)
        self.rate_input.setValue(1.0)
        rate_layout.addRow("1 jednotka této měny =", self.rate_input)

        rate_info = QLabel("Kč")
        rate_info.setStyleSheet("font-weight: bold;")
        rate_layout.addRow("", rate_info)

        layout.addRow(rate_group)

        # Výchozí měna
        self.default_checkbox = QCheckBox("Nastavit jako výchozí měnu")
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

        if self.currency and not self.currency["is_default"]:
            delete_btn = QPushButton("🗑️ Smazat")
            delete_btn.clicked.connect(self.delete_currency)
            delete_btn.setStyleSheet(f"background-color: {config.COLOR_DANGER}; color: white; padding: 8px 20px;")
            buttons_layout.addWidget(delete_btn)

        save_btn = QPushButton("💾 Uložit")
        save_btn.clicked.connect(self.save)
        save_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 20px;")
        buttons_layout.addWidget(save_btn)

        layout.addRow(buttons_layout)

    def load_currency_data(self):
        """Načtení dat měny"""
        self.iso_code_input.setText(self.currency["iso_code"])
        self.name_input.setText(self.currency["name"])
        self.symbol_input.setText(self.currency["symbol"])

        index = self.position_combo.findData(self.currency["symbol_position"])
        if index >= 0:
            self.position_combo.setCurrentIndex(index)

        self.decimal_input.setValue(self.currency["decimal_places"])
        self.rate_input.setValue(self.currency["exchange_rate"])
        self.default_checkbox.setChecked(self.currency["is_default"] == 1)
        self.active_checkbox.setChecked(self.currency["active"] == 1)

        # Výchozí měnu nelze upravovat některé vlastnosti
        if self.currency["is_default"]:
            self.rate_input.setEnabled(False)
            self.default_checkbox.setEnabled(False)
            self.active_checkbox.setEnabled(False)

    def delete_currency(self):
        """Smazání měny z dialogu"""
        if self.currency:
            self.parent().delete_currency(self.currency)
            self.reject()

    def save(self):
        """Uložení měny"""
        iso_code = self.iso_code_input.text().strip().upper()
        name = self.name_input.text().strip()
        symbol = self.symbol_input.text().strip()

        if not iso_code or len(iso_code) != 3:
            QMessageBox.warning(self, "Chyba", "ISO kód musí mít přesně 3 znaky.")
            return

        if not name:
            QMessageBox.warning(self, "Chyba", "Vyplňte název měny.")
            return

        if not symbol:
            QMessageBox.warning(self, "Chyba", "Vyplňte symbol měny.")
            return

        self.accept()

    def get_data(self):
        """Vrácení dat"""
        return {
            "iso_code": self.iso_code_input.text().strip().upper(),
            "name": self.name_input.text().strip(),
            "symbol": self.symbol_input.text().strip(),
            "symbol_position": self.position_combo.currentData(),
            "decimal_places": self.decimal_input.value(),
            "exchange_rate": self.rate_input.value(),
            "is_default": 1 if self.default_checkbox.isChecked() else 0,
            "active": 1 if self.active_checkbox.isChecked() else 0
        }
