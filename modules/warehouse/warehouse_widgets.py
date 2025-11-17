# -*- coding: utf-8 -*-
"""
Dialogy pro sklad - PROFESIONÁLNÍ
Příjem, výdej, inventura, quick add, hromadné úpravy
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QPushButton,
    QLabel, QLineEdit, QDoubleSpinBox, QComboBox, QTextEdit,
    QMessageBox, QDateEdit, QSpinBox, QCheckBox, QGroupBox,
    QTableWidget, QTableWidgetItem, QWidget
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
import config
from database_manager import db
from datetime import datetime

class ReceiveStockDialog(QDialog):
    """Dialog pro příjem na sklad"""

    stock_received = pyqtSignal()

    def __init__(self, item_id=None, parent=None):
        super().__init__(parent)
        self.item_id = item_id

        self.setWindowTitle("➕ Příjem na sklad")
        self.setModal(True)
        self.setMinimumWidth(600)

        self.init_ui()

        if item_id:
            self.set_item(item_id)

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # Hlavička
        header = QLabel("➕ PŘÍJEM NA SKLAD")
        header.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {config.COLOR_SUCCESS};
            padding: 15px;
            background-color: #ecf0f1;
            border-radius: 5px;
        """)
        layout.addWidget(header)

        # === ZÁKLADNÍ ÚDAJE ===
        basic_group = QGroupBox("📋 Základní údaje")
        basic_form = QFormLayout(basic_group)

        # Položka
        item_layout = QHBoxLayout()
        self.combo_item = QComboBox()
        self.combo_item.setMinimumWidth(400)
        self.load_items()
        self.combo_item.currentIndexChanged.connect(self.on_item_selected)
        item_layout.addWidget(self.combo_item)

        btn_new_item = QPushButton("➕")
        btn_new_item.setMaximumWidth(40)
        btn_new_item.setToolTip("Rychlé přidání položky")
        btn_new_item.clicked.connect(self.quick_add_item)
        item_layout.addWidget(btn_new_item)

        basic_form.addRow("Položka *:", item_layout)

        # Množství
        self.spin_quantity = QDoubleSpinBox()
        self.spin_quantity.setRange(0.01, 999999.99)
        self.spin_quantity.setDecimals(2)
        self.spin_quantity.setValue(1.0)
        self.spin_quantity.valueChanged.connect(self.calculate_total)
        basic_form.addRow("Množství *:", self.spin_quantity)

        # Jednotka (readonly - z položky)
        self.lbl_unit = QLabel("---")
        basic_form.addRow("Jednotka:", self.lbl_unit)

        layout.addWidget(basic_group)

        # === CENA ===
        price_group = QGroupBox("💰 Cena")
        price_form = QFormLayout(price_group)

        # Nákupní cena
        self.spin_purchase_price = QDoubleSpinBox()
        self.spin_purchase_price.setRange(0, 999999.99)
        self.spin_purchase_price.setDecimals(2)
        self.spin_purchase_price.setSuffix(" Kč")
        self.spin_purchase_price.valueChanged.connect(self.calculate_total)
        price_form.addRow("Nákupní cena *:", self.spin_purchase_price)

        # Celková částka
        self.lbl_total = QLabel("Celkem: 0.00 Kč")
        self.lbl_total.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60;")
        price_form.addRow("", self.lbl_total)

        layout.addWidget(price_group)

        # === DODAVATEL A DOKLAD ===
        supplier_group = QGroupBox("🚚 Dodavatel a doklad")
        supplier_form = QFormLayout(supplier_group)

        # Dodavatel
        supplier_layout = QHBoxLayout()
        self.combo_supplier = QComboBox()
        self.load_suppliers()
        supplier_layout.addWidget(self.combo_supplier)

        btn_new_supplier = QPushButton("➕")
        btn_new_supplier.setMaximumWidth(40)
        btn_new_supplier.setToolTip("Nový dodavatel")
        btn_new_supplier.clicked.connect(self.add_supplier)
        supplier_layout.addWidget(btn_new_supplier)

        supplier_form.addRow("Dodavatel:", supplier_layout)

        # Číslo dokladu
        self.input_document = QLineEdit()
        self.input_document.setPlaceholderText("Číslo faktury, dodacího listu...")
        supplier_form.addRow("Číslo dokladu:", self.input_document)

        # Datum přijetí
        self.date_received = QDateEdit()
        self.date_received.setCalendarPopup(True)
        self.date_received.setDate(QDate.currentDate())
        supplier_form.addRow("Datum přijetí:", self.date_received)

        layout.addWidget(supplier_group)

        # === POZNÁMKA ===
        notes_group = QGroupBox("📝 Poznámka")
        notes_layout = QVBoxLayout(notes_group)

        self.text_note = QTextEdit()
        self.text_note.setMaximumHeight(80)
        self.text_note.setPlaceholderText("Volitelná poznámka k příjmu...")
        notes_layout.addWidget(self.text_note)

        layout.addWidget(notes_group)

        # === TLAČÍTKA ===
        buttons = QHBoxLayout()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾 Přijmout na sklad")
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 12px 30px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }}
        """)
        btn_save.clicked.connect(self.save)

        buttons.addStretch()
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

    def load_items(self):
        """Načtení položek"""
        try:
            self.combo_item.clear()
            self.combo_item.addItem("-- Vyberte položku --", None)

            items = db.execute_query(
                "SELECT id, name, code, unit, price_purchase FROM warehouse ORDER BY name"
            )

            if items:
                for item in items:
                    display = f"{item[1]} ({item[2]})" if item[2] else item[1]
                    self.combo_item.addItem(display, item[0])

        except Exception as e:
            print(f"Chyba: {e}")

    def load_suppliers(self):
        """Načtení dodavatelů"""
        try:
            self.combo_supplier.clear()
            self.combo_supplier.addItem("-- Bez dodavatele --", None)

            suppliers = db.execute_query(
                "SELECT id, name FROM warehouse_suppliers ORDER BY name"
            )

            if suppliers:
                for sup in suppliers:
                    self.combo_supplier.addItem(sup[1], sup[0])

        except Exception as e:
            print(f"Chyba: {e}")

    def set_item(self, item_id):
        """Nastavení položky"""
        index = self.combo_item.findData(item_id)
        if index >= 0:
            self.combo_item.setCurrentIndex(index)

    def on_item_selected(self):
        """Při výběru položky"""
        item_id = self.combo_item.currentData()

        if not item_id:
            self.lbl_unit.setText("---")
            self.spin_purchase_price.setValue(0)
            return

        try:
            item = db.execute_query(
                "SELECT unit, price_purchase FROM warehouse WHERE id = ?",
                [item_id]
            )

            if item:
                self.lbl_unit.setText(item[0][0])
                self.spin_purchase_price.setValue(item[0][1] or 0)
                self.calculate_total()

        except Exception as e:
            print(f"Chyba: {e}")

    def calculate_total(self):
        """Výpočet celkové částky"""
        quantity = self.spin_quantity.value()
        price = self.spin_purchase_price.value()
        total = quantity * price

        self.lbl_total.setText(f"Celkem: {total:,.2f} Kč")

    def quick_add_item(self):
        """Rychlé přidání položky"""
        from .warehouse_widgets import QuickAddItemDialog
        dialog = QuickAddItemDialog(self)
        if dialog.exec():
            self.load_items()
            # Nastavit nově přidanou položku
            if hasattr(dialog, 'new_item_id'):
                self.set_item(dialog.new_item_id)

    def add_supplier(self):
        """Přidání dodavatele"""
        from .warehouse_suppliers import SupplierDetailDialog
        dialog = SupplierDetailDialog(parent=self)
        if dialog.exec():
            self.load_suppliers()

    def save(self):
        """Uložení příjmu"""
        item_id = self.combo_item.currentData()

        if not item_id:
            QMessageBox.warning(self, "Chyba", "Vyberte položku!")
            return

        quantity = self.spin_quantity.value()
        price = self.spin_purchase_price.value()

        if quantity <= 0:
            QMessageBox.warning(self, "Chyba", "Množství musí být větší než 0!")
            return

        try:
            supplier_id = self.combo_supplier.currentData()
            document = self.input_document.text()
            date = self.date_received.date().toString("yyyy-MM-dd")
            note = self.text_note.toPlainText()

            # Záznam pohybu
            db.execute_query(
                """INSERT INTO warehouse_movements
                   (item_id, movement_type, quantity, unit_price, supplier_id,
                    document_number, date, note, created_by)
                   VALUES (?, 'Příjem', ?, ?, ?, ?, ?, ?, ?)""",
                [item_id, quantity, price, supplier_id, document,
                 f"{date} {datetime.now().strftime('%H:%M:%S')}", note, "admin"]
            )

            # Aktualizace množství na skladě
            db.execute_query(
                "UPDATE warehouse SET quantity = quantity + ? WHERE id = ?",
                [quantity, item_id]
            )

            # Aktualizace nákupní ceny (průměr)
            db.execute_query(
                "UPDATE warehouse SET price_purchase = ? WHERE id = ?",
                [price, item_id]
            )

            QMessageBox.information(
                self,
                "Úspěch",
                f"Přijato na sklad:\n{self.combo_item.currentText()}\n"
                f"Množství: {quantity:.2f} {self.lbl_unit.text()}"
            )

            self.stock_received.emit()
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při příjmu:\n{str(e)}")


class IssueStockDialog(QDialog):
    """Dialog pro výdej ze skladu"""

    stock_issued = pyqtSignal()

    def __init__(self, item_id=None, parent=None):
        super().__init__(parent)
        self.item_id = item_id

        self.setWindowTitle("➖ Výdej ze skladu")
        self.setModal(True)
        self.setMinimumWidth(600)

        self.init_ui()

        if item_id:
            self.set_item(item_id)

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # Hlavička
        header = QLabel("➖ VÝDEJ ZE SKLADU")
        header.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: #e67e22;
            padding: 15px;
            background-color: #ecf0f1;
            border-radius: 5px;
        """)
        layout.addWidget(header)

        # === ZÁKLADNÍ ÚDAJE ===
        basic_group = QGroupBox("📋 Základní údaje")
        basic_form = QFormLayout(basic_group)

        # Položka
        self.combo_item = QComboBox()
        self.combo_item.setMinimumWidth(450)
        self.load_items()
        self.combo_item.currentIndexChanged.connect(self.on_item_selected)
        basic_form.addRow("Položka *:", self.combo_item)

        # Dostupné množství
        self.lbl_available = QLabel("Dostupné: ---")
        self.lbl_available.setStyleSheet("font-weight: bold; color: #27ae60;")
        basic_form.addRow("", self.lbl_available)

        # Množství k výdeji
        self.spin_quantity = QDoubleSpinBox()
        self.spin_quantity.setRange(0.01, 999999.99)
        self.spin_quantity.setDecimals(2)
        self.spin_quantity.setValue(1.0)
        self.spin_quantity.valueChanged.connect(self.check_availability)
        basic_form.addRow("Množství k výdeji *:", self.spin_quantity)

        # Jednotka
        self.lbl_unit = QLabel("---")
        basic_form.addRow("Jednotka:", self.lbl_unit)

        layout.addWidget(basic_group)

        # === DŮVOD VÝDEJE ===
        reason_group = QGroupBox("📝 Důvod výdeje")
        reason_form = QFormLayout(reason_group)

        # Typ výdeje
        self.combo_reason = QComboBox()
        self.combo_reason.addItems([
            "Zakázka / oprava",
            "Spotřeba",
            "Šrot / znehodnocení",
            "Vnitřní potřeba",
            "Převod na jiné místo",
            "Jiný důvod"
        ])
        reason_form.addRow("Typ výdeje:", self.combo_reason)

        # Poznámka
        self.text_note = QTextEdit()
        self.text_note.setMaximumHeight(80)
        self.text_note.setPlaceholderText("Upřesnění důvodu výdeje, číslo zakázky...")
        reason_form.addRow("Poznámka:", self.text_note)

        # Datum výdeje
        self.date_issued = QDateEdit()
        self.date_issued.setCalendarPopup(True)
        self.date_issued.setDate(QDate.currentDate())
        reason_form.addRow("Datum výdeje:", self.date_issued)

        layout.addWidget(reason_group)

        # === VAROVÁNÍ ===
        self.lbl_warning = QLabel("")
        self.lbl_warning.setStyleSheet("""
            background-color: #fff3cd;
            color: #856404;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #ffc107;
        """)
        self.lbl_warning.setWordWrap(True)
        self.lbl_warning.hide()
        layout.addWidget(self.lbl_warning)

        # === TLAČÍTKA ===
        buttons = QHBoxLayout()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("📤 Vydat ze skladu")
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: #e67e22;
                color: white;
                padding: 12px 30px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }}
        """)
        btn_save.clicked.connect(self.save)

        buttons.addStretch()
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

    def load_items(self):
        """Načtení položek (jen ty na skladě)"""
        try:
            self.combo_item.clear()
            self.combo_item.addItem("-- Vyberte položku --", None)

            items = db.execute_query(
                """SELECT id, name, code, unit, quantity
                   FROM warehouse
                   WHERE quantity > 0
                   ORDER BY name"""
            )

            if items:
                for item in items:
                    display = f"{item[1]} ({item[2]}) - Na skladě: {item[4]:.2f} {item[3]}" if item[2] else f"{item[1]} - Na skladě: {item[4]:.2f} {item[3]}"
                    self.combo_item.addItem(display, item[0])

        except Exception as e:
            print(f"Chyba: {e}")

    def set_item(self, item_id):
        """Nastavení položky"""
        index = self.combo_item.findData(item_id)
        if index >= 0:
            self.combo_item.setCurrentIndex(index)

    def on_item_selected(self):
        """Při výběru položky"""
        item_id = self.combo_item.currentData()

        if not item_id:
            self.lbl_available.setText("Dostupné: ---")
            self.lbl_unit.setText("---")
            return

        try:
            item = db.execute_query(
                "SELECT unit, quantity, min_quantity FROM warehouse WHERE id = ?",
                [item_id]
            )

            if item:
                unit = item[0][0]
                quantity = item[0][1]
                min_qty = item[0][2]

                self.lbl_unit.setText(unit)
                self.lbl_available.setText(f"Dostupné: {quantity:.2f} {unit}")

                # Varování pokud je pod minimem
                if quantity < min_qty:
                    self.lbl_available.setStyleSheet("font-weight: bold; color: #e74c3c;")
                else:
                    self.lbl_available.setStyleSheet("font-weight: bold; color: #27ae60;")

                self.check_availability()

        except Exception as e:
            print(f"Chyba: {e}")

    def check_availability(self):
        """Kontrola dostupnosti"""
        item_id = self.combo_item.currentData()

        if not item_id:
            return

        try:
            item = db.execute_query(
                "SELECT quantity, min_quantity FROM warehouse WHERE id = ?",
                [item_id]
            )

            if not item:
                return

            available = item[0][0]
            min_qty = item[0][1]
            requested = self.spin_quantity.value()

            # Kontrola dostupnosti
            if requested > available:
                self.lbl_warning.setText(
                    f"⚠️ VAROVÁNÍ: Požadované množství ({requested:.2f}) je větší než dostupné ({available:.2f})!"
                )
                self.lbl_warning.show()
            elif available - requested < min_qty:
                self.lbl_warning.setText(
                    f"⚠️ UPOZORNĚNÍ: Po výdeji klesne stav pod minimum ({min_qty:.2f})!"
                )
                self.lbl_warning.show()
            else:
                self.lbl_warning.hide()

        except Exception as e:
            print(f"Chyba: {e}")

    def save(self):
        """Uložení výdeje"""
        item_id = self.combo_item.currentData()

        if not item_id:
            QMessageBox.warning(self, "Chyba", "Vyberte položku!")
            return

        quantity = self.spin_quantity.value()

        if quantity <= 0:
            QMessageBox.warning(self, "Chyba", "Množství musí být větší než 0!")
            return

        # Kontrola dostupnosti
        try:
            item = db.execute_query(
                "SELECT quantity FROM warehouse WHERE id = ?",
                [item_id]
            )

            available = item[0][0]

            if quantity > available:
                reply = QMessageBox.question(
                    self,
                    "Nedostatečné množství",
                    f"Na skladě je jen {available:.2f} {self.lbl_unit.text()}.\n\n"
                    "Chcete přesto pokračovat?\n(Stav skladu bude záporný)",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    return

            # Uložení
            reason = self.combo_reason.currentText()
            note = self.text_note.toPlainText()
            full_note = f"[{reason}] {note}" if note else f"[{reason}]"

            date = self.date_issued.date().toString("yyyy-MM-dd")

            # Záznam pohybu
            db.execute_query(
                """INSERT INTO warehouse_movements
                   (item_id, movement_type, quantity, unit_price, date, note, created_by)
                   VALUES (?, 'Výdej', ?, 0, ?, ?, ?)""",
                [item_id, quantity, f"{date} {datetime.now().strftime('%H:%M:%S')}",
                 full_note, "admin"]
            )

            # Aktualizace množství
            db.execute_query(
                "UPDATE warehouse SET quantity = quantity - ? WHERE id = ?",
                [quantity, item_id]
            )

            QMessageBox.information(
                self,
                "Úspěch",
                f"Vydáno ze skladu:\n{self.combo_item.currentText()}\n"
                f"Množství: {quantity:.2f} {self.lbl_unit.text()}"
            )

            self.stock_issued.emit()
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při výdeji:\n{str(e)}")


class InventoryDialog(QDialog):
    """Dialog pro inventuru"""

    inventory_done = pyqtSignal()

    def __init__(self, item_id=None, parent=None):
        super().__init__(parent)
        self.item_id = item_id

        self.setWindowTitle("📊 Inventura")
        self.setModal(True)
        self.setMinimumWidth(600)

        self.init_ui()

        if item_id:
            self.set_item(item_id)

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # Hlavička
        header = QLabel("📊 INVENTURA SKLADU")
        header.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {config.COLOR_SECONDARY};
            padding: 15px;
            background-color: #ecf0f1;
            border-radius: 5px;
        """)
        layout.addWidget(header)

        # === POLOŽKA ===
        item_group = QGroupBox("📋 Položka")
        item_form = QFormLayout(item_group)

        self.combo_item = QComboBox()
        self.combo_item.setMinimumWidth(450)
        self.load_items()
        self.combo_item.currentIndexChanged.connect(self.on_item_selected)
        item_form.addRow("Položka *:", self.combo_item)

        # Jednotka
        self.lbl_unit = QLabel("---")
        item_form.addRow("Jednotka:", self.lbl_unit)

        layout.addWidget(item_group)

        # === STAVY ===
        states_group = QGroupBox("📊 Stavy")
        states_form = QFormLayout(states_group)

        # Očekávaný stav (z databáze)
        self.lbl_expected = QLabel("0.00")
        self.lbl_expected.setStyleSheet("font-size: 16px; font-weight: bold; color: #3498db;")
        states_form.addRow("Očekávaný stav:", self.lbl_expected)

        # Skutečný stav (zadá uživatel)
        self.spin_actual = QDoubleSpinBox()
        self.spin_actual.setRange(-999999.99, 999999.99)
        self.spin_actual.setDecimals(2)
        self.spin_actual.valueChanged.connect(self.calculate_difference)
        states_form.addRow("Skutečný stav *:", self.spin_actual)

        # Rozdíl
        self.lbl_difference = QLabel("Rozdíl: 0.00")
        self.lbl_difference.setStyleSheet("font-size: 16px; font-weight: bold;")
        states_form.addRow("", self.lbl_difference)

        layout.addWidget(states_group)

        # === POZNÁMKA ===
        note_group = QGroupBox("📝 Poznámka k inventuře")
        note_layout = QVBoxLayout(note_group)

        self.text_note = QTextEdit()
        self.text_note.setMaximumHeight(80)
        self.text_note.setPlaceholderText("Důvod rozdílu, poznámky...")
        note_layout.addWidget(self.text_note)

        layout.addWidget(note_group)

        # === DATUM ===
        date_form = QFormLayout()

        self.date_inventory = QDateEdit()
        self.date_inventory.setCalendarPopup(True)
        self.date_inventory.setDate(QDate.currentDate())
        date_form.addRow("Datum inventury:", self.date_inventory)

        layout.addLayout(date_form)

        # === TLAČÍTKA ===
        buttons = QHBoxLayout()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾 Uložit inventuru")
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                padding: 12px 30px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }}
        """)
        btn_save.clicked.connect(self.save)

        buttons.addStretch()
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

    def load_items(self):
        """Načtení položek"""
        try:
            self.combo_item.clear()
            self.combo_item.addItem("-- Vyberte položku --", None)

            items = db.execute_query(
                "SELECT id, name, code, unit FROM warehouse ORDER BY name"
            )

            if items:
                for item in items:
                    display = f"{item[1]} ({item[2]})" if item[2] else item[1]
                    self.combo_item.addItem(display, item[0])

        except Exception as e:
            print(f"Chyba: {e}")

    def set_item(self, item_id):
        """Nastavení položky"""
        index = self.combo_item.findData(item_id)
        if index >= 0:
            self.combo_item.setCurrentIndex(index)

    def on_item_selected(self):
        """Při výběru položky"""
        item_id = self.combo_item.currentData()

        if not item_id:
            self.lbl_expected.setText("0.00")
            self.lbl_unit.setText("---")
            return

        try:
            item = db.execute_query(
                "SELECT unit, quantity FROM warehouse WHERE id = ?",
                [item_id]
            )

            if item:
                self.lbl_unit.setText(item[0][0])
                expected = item[0][1]
                self.lbl_expected.setText(f"{expected:.2f}")
                self.spin_actual.setValue(expected)
                self.calculate_difference()

        except Exception as e:
            print(f"Chyba: {e}")

    def calculate_difference(self):
        """Výpočet rozdílu"""
        try:
            expected = float(self.lbl_expected.text())
            actual = self.spin_actual.value()
            difference = actual - expected

            if difference > 0:
                self.lbl_difference.setText(f"Rozdíl: +{difference:.2f} (přebytek)")
                self.lbl_difference.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60;")
            elif difference < 0:
                self.lbl_difference.setText(f"Rozdíl: {difference:.2f} (manko)")
                self.lbl_difference.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c;")
            else:
                self.lbl_difference.setText(f"Rozdíl: 0.00 (souhlasí)")
                self.lbl_difference.setStyleSheet("font-size: 16px; font-weight: bold; color: #7f8c8d;")

        except:
            pass

    def save(self):
        """Uložení inventury"""
        item_id = self.combo_item.currentData()

        if not item_id:
            QMessageBox.warning(self, "Chyba", "Vyberte položku!")
            return

        try:
            expected = float(self.lbl_expected.text())
            actual = self.spin_actual.value()
            difference = actual - expected

            if difference == 0:
                reply = QMessageBox.question(
                    self,
                    "Bez rozdílu",
                    "Skutečný stav souhlasí s očekávaným.\n\nChcete přesto zaznamenat inventuru?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.No:
                    return

            note = self.text_note.toPlainText()
            full_note = f"Inventura - Očekáváno: {expected:.2f}, Skutečnost: {actual:.2f}, Rozdíl: {difference:+.2f}. {note}"

            date = self.date_inventory.date().toString("yyyy-MM-dd")

            # Záznam pohybu
            db.execute_query(
                """INSERT INTO warehouse_movements
                   (item_id, movement_type, quantity, unit_price, date, note, created_by)
                   VALUES (?, 'Inventura', ?, 0, ?, ?, ?)""",
                [item_id, difference, f"{date} {datetime.now().strftime('%H:%M:%S')}",
                 full_note, "admin"]
            )

            # Aktualizace skutečného stavu
            db.execute_query(
                "UPDATE warehouse SET quantity = ? WHERE id = ?",
                [actual, item_id]
            )

            QMessageBox.information(
                self,
                "Úspěch",
                f"Inventura uložena:\n\n"
                f"Položka: {self.combo_item.currentText()}\n"
                f"Očekáváno: {expected:.2f}\n"
                f"Skutečnost: {actual:.2f}\n"
                f"Rozdíl: {difference:+.2f}"
            )

            self.inventory_done.emit()
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při inventuře:\n{str(e)}")


class QuickAddItemDialog(QDialog):
    """Quick add - rychlé přidání položky"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.new_item_id = None

        self.setWindowTitle("⚡ Rychlé přidání položky")
        self.setModal(True)
        self.setMinimumWidth(500)

        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # Hlavička
        header = QLabel("⚡ RYCHLÉ PŘIDÁNÍ POLOŽKY")
        header.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #8e44ad;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 5px;
        """)
        layout.addWidget(header)

        # Formulář
        form = QFormLayout()

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Název položky...")
        form.addRow("Název *:", self.input_name)

        self.input_code = QLineEdit()
        self.input_code.setPlaceholderText("Interní kód...")
        form.addRow("Kód:", self.input_code)

        self.combo_category = QComboBox()
        self.load_categories()
        form.addRow("Kategorie *:", self.combo_category)

        self.combo_unit = QComboBox()
        self.combo_unit.addItems(["ks", "m", "l", "kg", "m²", "m³", "bal", "sad"])
        self.combo_unit.setEditable(True)
        form.addRow("Jednotka *:", self.combo_unit)

        self.spin_price = QDoubleSpinBox()
        self.spin_price.setRange(0, 999999.99)
        self.spin_price.setDecimals(2)
        self.spin_price.setSuffix(" Kč")
        form.addRow("Nákupní cena:", self.spin_price)

        layout.addLayout(form)

        # Tlačítka
        buttons = QHBoxLayout()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾 Přidat")
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 10px 25px;
                border-radius: 5px;
                font-weight: bold;
            }}
        """)
        btn_save.clicked.connect(self.save)

        buttons.addStretch()
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

    def load_categories(self):
        """Načtení kategorií"""
        try:
            self.combo_category.clear()
            self.combo_category.addItem("-- Vyberte kategorii --", None)

            categories = db.execute_query("SELECT id, name FROM warehouse_categories ORDER BY name")
            if categories:
                for cat in categories:
                    self.combo_category.addItem(cat[1], cat[0])
        except Exception as e:
            print(f"Chyba: {e}")

    def save(self):
        """Uložení"""
        if not self.input_name.text():
            QMessageBox.warning(self, "Chyba", "Vyplňte název!")
            self.input_name.setFocus()
            return

        if not self.combo_category.currentData():
            QMessageBox.warning(self, "Chyba", "Vyberte kategorii!")
            return

        try:
            # Vložení
            cursor = db.execute_query(
                """INSERT INTO warehouse
                   (name, code, category_id, unit, quantity, min_quantity, price_purchase, price_sale)
                   VALUES (?, ?, ?, ?, 0, 0, ?, ?)""",
                [self.input_name.text(), self.input_code.text(),
                 self.combo_category.currentData(), self.combo_unit.currentText(),
                 self.spin_price.value(), self.spin_price.value() * 1.3]
            )

            # Získání ID nové položky
            self.new_item_id = cursor.lastrowid if hasattr(cursor, 'lastrowid') else None

            QMessageBox.information(self, "Úspěch", f"Položka '{self.input_name.text()}' byla přidána")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba:\n{str(e)}")


class BulkEditDialog(QDialog):
    """Dialog pro hromadnou úpravu"""

    items_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("🔧 Hromadná úprava")
        self.setModal(True)
        self.setMinimumSize(800, 600)

        self.init_ui()
        self.load_items()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # Hlavička
        header = QLabel("🔧 HROMADNÁ ÚPRAVA POLOŽEK")
        header.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {config.COLOR_PRIMARY};
            padding: 15px;
            background-color: #ecf0f1;
            border-radius: 5px;
        """)
        layout.addWidget(header)

        # === VÝBĚR POLOŽEK ===
        items_group = QGroupBox("📋 Výběr položek")
        items_layout = QVBoxLayout(items_group)

        # Tabulka s checkboxy
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "✓", "Název", "Kód", "Kategorie", "ID"
        ])
        self.table.setColumnHidden(4, True)
        self.table.setColumnWidth(0, 30)
        self.table.horizontalHeader().setStretchLastSection(True)

        items_layout.addWidget(self.table)

        # Tlačítka výběru
        select_buttons = QHBoxLayout()
        btn_select_all = QPushButton("Vybrat vše")
        btn_select_all.clicked.connect(self.select_all)

        btn_deselect_all = QPushButton("Zrušit výběr")
        btn_deselect_all.clicked.connect(self.deselect_all)

        select_buttons.addWidget(btn_select_all)
        select_buttons.addWidget(btn_deselect_all)
        select_buttons.addStretch()

        items_layout.addLayout(select_buttons)

        layout.addWidget(items_group)

        # === AKCE ===
        actions_group = QGroupBox("⚙️ Akce")
        actions_layout = QVBoxLayout(actions_group)

        # Výběr akce
        action_form = QFormLayout()

        self.combo_action = QComboBox()
        self.combo_action.addItems([
            "Změnit kategorii",
            "Upravit ceny (navýšení %)",
            "Upravit ceny (snížení %)",
            "Nastavit minimální stav",
            "Změnit dodavatele"
        ])
        self.combo_action.currentIndexChanged.connect(self.on_action_changed)
        action_form.addRow("Akce:", self.combo_action)

        actions_layout.addLayout(action_form)

        # === PARAMETRY AKCE ===
        self.params_widget = QWidget()
        self.params_layout = QFormLayout(self.params_widget)
        actions_layout.addWidget(self.params_widget)

        layout.addWidget(actions_group)

        # Inicializace parametrů
        self.on_action_changed()

        # === TLAČÍTKA ===
        buttons = QHBoxLayout()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.clicked.connect(self.reject)

        btn_apply = QPushButton("✓ Provést hromadnou úpravu")
        btn_apply.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 12px 30px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }}
        """)
        btn_apply.clicked.connect(self.apply_changes)

        buttons.addStretch()
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_apply)

        layout.addLayout(buttons)

    def load_items(self):
        """Načtení položek"""
        try:
            items = db.execute_query(
                """SELECT w.id, w.name, w.code, c.name as category
                   FROM warehouse w
                   LEFT JOIN warehouse_categories c ON w.category_id = c.id
                   ORDER BY w.name"""
            )

            self.table.setRowCount(0)

            if not items:
                return

            for item in items:
                row = self.table.rowCount()
                self.table.insertRow(row)

                # Checkbox
                check = QCheckBox()
                self.table.setCellWidget(row, 0, check)

                self.table.setItem(row, 1, QTableWidgetItem(item[1]))
                self.table.setItem(row, 2, QTableWidgetItem(item[2] or ""))
                self.table.setItem(row, 3, QTableWidgetItem(item[3] or "---"))
                self.table.setItem(row, 4, QTableWidgetItem(str(item[0])))

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba:\n{str(e)}")

    def select_all(self):
        """Vybrat vše"""
        for row in range(self.table.rowCount()):
            check = self.table.cellWidget(row, 0)
            if check:
                check.setChecked(True)

    def deselect_all(self):
        """Zrušit výběr"""
        for row in range(self.table.rowCount()):
            check = self.table.cellWidget(row, 0)
            if check:
                check.setChecked(False)

    def on_action_changed(self):
        """Změna akce"""
        # Vyčistit parametry
        while self.params_layout.count():
            child = self.params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        action = self.combo_action.currentText()

        if action == "Změnit kategorii":
            self.combo_category = QComboBox()
            categories = db.execute_query("SELECT id, name FROM warehouse_categories ORDER BY name")
            for cat in categories:
                self.combo_category.addItem(cat[1], cat[0])
            self.params_layout.addRow("Nová kategorie:", self.combo_category)

        elif "Upravit ceny" in action:
            self.spin_percent = QSpinBox()
            self.spin_percent.setRange(1, 100)
            self.spin_percent.setSuffix(" %")
            self.spin_percent.setValue(10)
            self.params_layout.addRow("Procento:", self.spin_percent)

        elif action == "Nastavit minimální stav":
            self.spin_min = QDoubleSpinBox()
            self.spin_min.setRange(0, 999999.99)
            self.spin_min.setDecimals(2)
            self.params_layout.addRow("Min. stav:", self.spin_min)

        elif action == "Změnit dodavatele":
            self.combo_supplier = QComboBox()
            suppliers = db.execute_query("SELECT id, name FROM warehouse_suppliers ORDER BY name")
            for sup in suppliers:
                self.combo_supplier.addItem(sup[1], sup[0])
            self.params_layout.addRow("Dodavatel:", self.combo_supplier)

    def get_selected_items(self):
        """Získání vybraných položek"""
        selected = []
        for row in range(self.table.rowCount()):
            check = self.table.cellWidget(row, 0)
            if check and check.isChecked():
                item_id = int(self.table.item(row, 4).text())
                selected.append(item_id)
        return selected

    def apply_changes(self):
        """Provedení změn"""
        selected = self.get_selected_items()

        if not selected:
            QMessageBox.warning(self, "Chyba", "Nevybrali jste žádné položky!")
            return

        action = self.combo_action.currentText()

        try:
            if action == "Změnit kategorii":
                category_id = self.combo_category.currentData()
                for item_id in selected:
                    db.execute_query(
                        "UPDATE warehouse SET category_id = ? WHERE id = ?",
                        [category_id, item_id]
                    )

            elif action == "Upravit ceny (navýšení %)":
                percent = self.spin_percent.value()
                for item_id in selected:
                    db.execute_query(
                        """UPDATE warehouse
                           SET price_purchase = price_purchase * (1 + ?/100),
                               price_sale = price_sale * (1 + ?/100)
                           WHERE id = ?""",
                        [percent, percent, item_id]
                    )

            elif action == "Upravit ceny (snížení %)":
                percent = self.spin_percent.value()
                for item_id in selected:
                    db.execute_query(
                        """UPDATE warehouse
                           SET price_purchase = price_purchase * (1 - ?/100),
                               price_sale = price_sale * (1 - ?/100)
                           WHERE id = ?""",
                        [percent, percent, item_id]
                    )

            elif action == "Nastavit minimální stav":
                min_qty = self.spin_min.value()
                for item_id in selected:
                    db.execute_query(
                        "UPDATE warehouse SET min_quantity = ? WHERE id = ?",
                        [min_qty, item_id]
                    )

            elif action == "Změnit dodavatele":
                supplier_id = self.combo_supplier.currentData()
                for item_id in selected:
                    db.execute_query(
                        "UPDATE warehouse SET supplier_id = ? WHERE id = ?",
                        [supplier_id, item_id]
                    )

            QMessageBox.information(
                self,
                "Úspěch",
                f"Hromadná úprava dokončena!\n\n"
                f"Upraveno položek: {len(selected)}\n"
                f"Akce: {action}"
            )

            self.items_updated.emit()
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při úpravě:\n{str(e)}")
