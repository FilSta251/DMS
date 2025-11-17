# -*- coding: utf-8 -*-
"""
Detail položky skladu - PROFESIONÁLNÍ
Editace všech údajů, historie, fotky, statistiky
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QDoubleSpinBox, QComboBox,
    QTextEdit, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QGroupBox, QScrollArea, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QPixmap, QColor
import config
from database_manager import db
from datetime import datetime
import os


class WarehouseDetailWindow(QMainWindow):
    """Okno s detailem položky skladu"""

    item_updated = pyqtSignal()

    def __init__(self, item_id=None, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.is_new = item_id is None
        self.item_data = None

        self.setWindowTitle("Detail položky skladu" if not self.is_new else "Nová položka")
        self.setMinimumSize(1200, 800)

        self.init_ui()

        if not self.is_new:
            self.load_item_data()

    def init_ui(self):
        """Inicializace UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === HORNÍ LIŠTA ===
        self.create_action_bar(main_layout)

        # === ZÁLOŽKY ===
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                background: white;
            }
            QTabBar::tab {
                background: #ecf0f1;
                padding: 10px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 3px solid #3498db;
            }
        """)

        # ZÁLOŽKA 1: Základní info
        self.tab_basic = self.create_tab_basic_info()
        self.tabs.addTab(self.tab_basic, "📋 Základní info")

        # ZÁLOŽKA 2: Ceny a marže
        self.tab_prices = self.create_tab_prices()
        self.tabs.addTab(self.tab_prices, "💰 Ceny a marže")

        # ZÁLOŽKA 3: Skladové údaje
        self.tab_stock = self.create_tab_stock()
        self.tabs.addTab(self.tab_stock, "📦 Skladové údaje")

        # ZÁLOŽKA 4: Historie pohybů
        self.tab_history = self.create_tab_history()
        self.tabs.addTab(self.tab_history, "📊 Historie pohybů")

        # ZÁLOŽKA 5: Fotky
        self.tab_photos = self.create_tab_photos()
        self.tabs.addTab(self.tab_photos, "📷 Fotky")

        # ZÁLOŽKA 6: Statistiky
        self.tab_stats = self.create_tab_statistics()
        self.tabs.addTab(self.tab_stats, "📈 Statistiky")

        main_layout.addWidget(self.tabs)

    def create_action_bar(self, parent_layout):
        """Horní lišta s akcemi"""
        action_bar = QWidget()
        action_bar.setFixedHeight(55)
        action_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {config.COLOR_PRIMARY};
                border-bottom: 2px solid #2c3e50;
            }}
        """)
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(15, 10, 15, 10)

        # Nadpis
        self.lbl_title = QLabel("Nová položka skladu")
        self.lbl_title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        action_layout.addWidget(self.lbl_title)

        # Badge stavu
        self.lbl_status = QLabel("✓ Na skladě")
        self.lbl_status.setStyleSheet("""
            background-color: #27ae60;
            color: white;
            padding: 4px 12px;
            border-radius: 10px;
            font-weight: bold;
            font-size: 11px;
        """)
        action_layout.addWidget(self.lbl_status)

        action_layout.addStretch()

        # Tlačítka akcí (jen pokud není nová položka)
        if not self.is_new:
            btn_receive = QPushButton("➕ Příjem")
            btn_receive.setStyleSheet(self.get_button_style(config.COLOR_SUCCESS))
            btn_receive.clicked.connect(self.receive_stock)
            action_layout.addWidget(btn_receive)

            btn_issue = QPushButton("➖ Výdej")
            btn_issue.setStyleSheet(self.get_button_style("#e67e22"))
            btn_issue.clicked.connect(self.issue_stock)
            action_layout.addWidget(btn_issue)

            btn_label = QPushButton("🏷️ Štítek")
            btn_label.setStyleSheet(self.get_button_style(config.COLOR_SECONDARY))
            btn_label.clicked.connect(self.print_label)
            action_layout.addWidget(btn_label)

        # Uložit
        btn_save = QPushButton("✓ Uložit")
        btn_save.setStyleSheet(self.get_button_style(config.COLOR_SUCCESS))
        btn_save.clicked.connect(self.save_item)
        action_layout.addWidget(btn_save)

        # Smazat (jen pokud není nová)
        if not self.is_new:
            btn_delete = QPushButton("✕ Smazat")
            btn_delete.setStyleSheet(self.get_button_style(config.COLOR_DANGER))
            btn_delete.clicked.connect(self.delete_item)
            action_layout.addWidget(btn_delete)

        parent_layout.addWidget(action_bar)

    def create_tab_basic_info(self):
        """ZÁLOŽKA 1: Základní informace"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # === ZÁKLADNÍ ÚDAJE ===
        basic_group = QGroupBox("📋 Základní údaje")
        basic_form = QFormLayout(basic_group)

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Název položky...")
        basic_form.addRow("Název *:", self.input_name)

        self.input_code = QLineEdit()
        self.input_code.setPlaceholderText("Interní kód...")
        basic_form.addRow("Kód:", self.input_code)

        self.input_ean = QLineEdit()
        self.input_ean.setPlaceholderText("EAN čárový kód...")
        basic_form.addRow("EAN:", self.input_ean)

        self.combo_category = QComboBox()
        self.load_categories()
        basic_form.addRow("Kategorie *:", self.combo_category)

        self.combo_supplier = QComboBox()
        self.load_suppliers()
        basic_form.addRow("Dodavatel:", self.combo_supplier)

        scroll_layout.addWidget(basic_group)

        # === POPIS ===
        desc_group = QGroupBox("📝 Popis")
        desc_layout = QVBoxLayout(desc_group)

        self.text_description = QTextEdit()
        self.text_description.setMaximumHeight(100)
        self.text_description.setPlaceholderText("Podrobný popis položky...")
        desc_layout.addWidget(self.text_description)

        scroll_layout.addWidget(desc_group)

        # === POZNÁMKY ===
        notes_group = QGroupBox("💬 Interní poznámky")
        notes_layout = QVBoxLayout(notes_group)

        self.text_notes = QTextEdit()
        self.text_notes.setMaximumHeight(80)
        self.text_notes.setPlaceholderText("Interní poznámky...")
        notes_layout.addWidget(self.text_notes)

        scroll_layout.addWidget(notes_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return widget

    def create_tab_prices(self):
        """ZÁLOŽKA 2: Ceny a marže"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # === NÁKUPNÍ CENA ===
        purchase_group = QGroupBox("💵 Nákupní cena")
        purchase_form = QFormLayout(purchase_group)

        self.spin_price_purchase = QDoubleSpinBox()
        self.spin_price_purchase.setRange(0, 999999.99)
        self.spin_price_purchase.setDecimals(2)
        self.spin_price_purchase.setSuffix(" Kč")
        self.spin_price_purchase.valueChanged.connect(self.calculate_margin)
        purchase_form.addRow("Nákupní cena *:", self.spin_price_purchase)

        scroll_layout.addWidget(purchase_group)

        # === PRODEJNÍ CENA ===
        sale_group = QGroupBox("💰 Prodejní cena")
        sale_form = QFormLayout(sale_group)

        self.spin_price_sale = QDoubleSpinBox()
        self.spin_price_sale.setRange(0, 999999.99)
        self.spin_price_sale.setDecimals(2)
        self.spin_price_sale.setSuffix(" Kč")
        self.spin_price_sale.valueChanged.connect(self.calculate_margin)
        sale_form.addRow("Prodejní cena *:", self.spin_price_sale)

        self.combo_vat = QComboBox()
        self.combo_vat.addItems(["21%", "15%", "12%", "0%"])
        sale_form.addRow("DPH:", self.combo_vat)

        scroll_layout.addWidget(sale_group)

        # === MARŽE ===
        margin_group = QGroupBox("📊 Marže")
        margin_layout = QVBoxLayout(margin_group)

        self.lbl_margin_amount = QLabel("Marže: 0.00 Kč")
        self.lbl_margin_amount.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60;")
        margin_layout.addWidget(self.lbl_margin_amount)

        self.lbl_margin_percent = QLabel("Marže: 0.0%")
        self.lbl_margin_percent.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        margin_layout.addWidget(self.lbl_margin_percent)

        # Rychlé tlačítka pro nastavení marže
        quick_margin = QHBoxLayout()
        quick_margin.addWidget(QLabel("Rychlá marže:"))

        for percent in [10, 20, 30, 50, 100]:
            btn = QPushButton(f"+{percent}%")
            btn.clicked.connect(lambda checked, p=percent: self.apply_quick_margin(p))
            quick_margin.addWidget(btn)

        quick_margin.addStretch()
        margin_layout.addLayout(quick_margin)

        scroll_layout.addWidget(margin_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return widget

    def create_tab_stock(self):
        """ZÁLOŽKA 3: Skladové údaje"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # === MNOŽSTVÍ ===
        quantity_group = QGroupBox("📦 Množství")
        quantity_form = QFormLayout(quantity_group)

        self.spin_quantity = QDoubleSpinBox()
        self.spin_quantity.setRange(0, 999999.99)
        self.spin_quantity.setDecimals(2)
        self.spin_quantity.valueChanged.connect(self.update_stock_status)
        quantity_form.addRow("Množství *:", self.spin_quantity)

        self.combo_unit = QComboBox()
        self.combo_unit.addItems(["ks", "m", "l", "kg", "m²", "m³", "bal", "sad"])
        self.combo_unit.setEditable(True)
        quantity_form.addRow("Jednotka *:", self.combo_unit)

        scroll_layout.addWidget(quantity_group)

        # === MINIMÁLNÍ STAV ===
        minimum_group = QGroupBox("⚠️ Minimální stav")
        minimum_form = QFormLayout(minimum_group)

        self.spin_min_quantity = QDoubleSpinBox()
        self.spin_min_quantity.setRange(0, 999999.99)
        self.spin_min_quantity.setDecimals(2)
        self.spin_min_quantity.valueChanged.connect(self.update_stock_status)
        minimum_form.addRow("Min. množství:", self.spin_min_quantity)

        info = QLabel("💡 Upozornění se zobrazí, když množství klesne pod tuto hodnotu")
        info.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        info.setWordWrap(True)
        minimum_form.addRow("", info)

        scroll_layout.addWidget(minimum_group)

        # === UMÍSTĚNÍ ===
        location_group = QGroupBox("📍 Umístění")
        location_form = QFormLayout(location_group)

        self.input_location = QLineEdit()
        self.input_location.setPlaceholderText("Např.: Regál A3, Police 2...")
        location_form.addRow("Umístění:", self.input_location)

        scroll_layout.addWidget(location_group)

        # === STATUS BOX ===
        self.status_box = QGroupBox("📊 Aktuální stav")
        status_layout = QVBoxLayout(self.status_box)

        self.lbl_stock_status = QLabel("Stav: ---")
        self.lbl_stock_status.setStyleSheet("font-size: 16px; font-weight: bold;")
        status_layout.addWidget(self.lbl_stock_status)

        self.lbl_stock_value = QLabel("Hodnota: 0.00 Kč")
        self.lbl_stock_value.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        status_layout.addWidget(self.lbl_stock_value)

        scroll_layout.addWidget(self.status_box)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return widget

    def create_tab_history(self):
        """ZÁLOŽKA 4: Historie pohybů"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info
        info = QLabel("📊 Historie všech pohybů této položky")
        info.setStyleSheet("padding: 10px; background-color: #ecf0f1; font-weight: bold;")
        layout.addWidget(info)

        # Tabulka
        self.table_history = QTableWidget()
        self.table_history.setColumnCount(7)
        self.table_history.setHorizontalHeaderLabels([
            "Datum", "Typ", "Množství", "Cena", "Celkem", "Poznámka", "ID"
        ])
        self.table_history.setColumnHidden(6, True)
        self.table_history.setAlternatingRowColors(True)
        self.table_history.horizontalHeader().setStretchLastSection(True)
        self.table_history.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                font-weight: bold;
            }
        """)

        layout.addWidget(self.table_history)

        return widget

    def create_tab_photos(self):
        """ZÁLOŽKA 5: Fotky"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Tlačítka
        btn_layout = QHBoxLayout()

        btn_add_photo = QPushButton("➕ Přidat fotku")
        btn_add_photo.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px;")
        btn_add_photo.clicked.connect(self.add_photo)
        btn_layout.addWidget(btn_add_photo)

        btn_delete_photo = QPushButton("🗑️ Smazat")
        btn_delete_photo.setStyleSheet(f"background-color: {config.COLOR_DANGER}; color: white; padding: 8px;")
        btn_delete_photo.clicked.connect(self.delete_photo)
        btn_layout.addWidget(btn_delete_photo)

        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # Seznam fotek (zatím placeholder)
        info = QLabel("📷 Funkce správy fotek bude doplněna v další verzi\n\n"
                     "Fotky budou uloženy jako BLOB v databázi")
        info.setStyleSheet("color: #7f8c8d; padding: 20px;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        return widget

    def create_tab_statistics(self):
        """ZÁLOŽKA 6: Statistiky"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # === SOUHRNNÉ STATISTIKY ===
        stats_group = QGroupBox("📊 Souhrnné statistiky")
        stats_layout = QFormLayout(stats_group)

        self.lbl_total_received = QLabel("0")
        stats_layout.addRow("Celkem přijato:", self.lbl_total_received)

        self.lbl_total_issued = QLabel("0")
        stats_layout.addRow("Celkem vydáno:", self.lbl_total_issued)

        self.lbl_avg_purchase_price = QLabel("0.00 Kč")
        stats_layout.addRow("Průměrná nákupní cena:", self.lbl_avg_purchase_price)

        self.lbl_last_movement = QLabel("---")
        stats_layout.addRow("Poslední pohyb:", self.lbl_last_movement)

        scroll_layout.addWidget(stats_group)

        # === GRAF ===
        graph_info = QLabel("📈 Graf prodeje/spotřeby bude doplněn v další verzi\n\n"
                           "Použijeme knihovnu matplotlib pro zobrazení grafů")
        graph_info.setStyleSheet("color: #7f8c8d; padding: 20px; background-color: #f8f9fa; border-radius: 5px;")
        graph_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(graph_info)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return widget

    def get_button_style(self, color):
        """Styl tlačítek"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 6px 14px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """

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
            print(f"Chyba při načítání kategorií: {e}")

    def load_suppliers(self):
        """Načtení dodavatelů"""
        try:
            self.combo_supplier.clear()
            self.combo_supplier.addItem("-- Bez dodavatele --", None)

            suppliers = db.execute_query("SELECT id, name FROM warehouse_suppliers ORDER BY name")
            if suppliers:
                for sup in suppliers:
                    self.combo_supplier.addItem(sup[1], sup[0])
        except Exception as e:
            print(f"Chyba při načítání dodavatelů: {e}")

    def load_item_data(self):
        """Načtení dat položky"""
        try:
            item = db.execute_query(
                """SELECT
                    name, code, ean, category_id, supplier_id, description, notes,
                    quantity, unit, min_quantity, location,
                    price_purchase, price_sale
                FROM warehouse WHERE id = ?""",
                [self.item_id]
            )

            if not item:
                QMessageBox.warning(self, "Chyba", "Položka nenalezena!")
                self.close()
                return

            self.item_data = item[0]

            # Aktualizace nadpisu
            self.lbl_title.setText(f"📦 {self.item_data[0]}")

            # ZÁKLADNÍ INFO
            self.input_name.setText(self.item_data[0] or "")
            self.input_code.setText(self.item_data[1] or "")
            self.input_ean.setText(self.item_data[2] or "")

            if self.item_data[3]:
                index = self.combo_category.findData(self.item_data[3])
                if index >= 0:
                    self.combo_category.setCurrentIndex(index)

            if self.item_data[4]:
                index = self.combo_supplier.findData(self.item_data[4])
                if index >= 0:
                    self.combo_supplier.setCurrentIndex(index)

            self.text_description.setPlainText(self.item_data[5] or "")
            self.text_notes.setPlainText(self.item_data[6] or "")

            # SKLADOVÉ ÚDAJE
            self.spin_quantity.setValue(self.item_data[7] or 0)
            self.combo_unit.setCurrentText(self.item_data[8] or "ks")
            self.spin_min_quantity.setValue(self.item_data[9] or 0)
            self.input_location.setText(self.item_data[10] or "")

            # CENY
            self.spin_price_purchase.setValue(self.item_data[11] or 0)
            self.spin_price_sale.setValue(self.item_data[12] or 0)

            # Přepočet marže a stavu
            self.calculate_margin()
            self.update_stock_status()

            # Načtení historie
            self.load_history()

            # Načtení statistik
            self.load_statistics()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při načítání:\n{str(e)}")

    def calculate_margin(self):
        """Výpočet marže"""
        purchase = self.spin_price_purchase.value()
        sale = self.spin_price_sale.value()

        if purchase > 0:
            margin_amount = sale - purchase
            margin_percent = (margin_amount / purchase) * 100

            self.lbl_margin_amount.setText(f"Marže: {margin_amount:.2f} Kč")
            self.lbl_margin_percent.setText(f"Marže: {margin_percent:.1f}%")

            # Barevné zvýraznění
            if margin_amount >= 0:
                self.lbl_margin_amount.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60;")
            else:
                self.lbl_margin_amount.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c;")
        else:
            self.lbl_margin_amount.setText("Marže: ---")
            self.lbl_margin_percent.setText("Marže: ---")

    def apply_quick_margin(self, percent):
        """Rychlé nastavení marže"""
        purchase = self.spin_price_purchase.value()
        if purchase > 0:
            sale = purchase * (1 + percent / 100)
            self.spin_price_sale.setValue(sale)

    def update_stock_status(self):
        """Aktualizace stavu skladu"""
        quantity = self.spin_quantity.value()
        min_qty = self.spin_min_quantity.value()
        purchase = self.spin_price_purchase.value()

        # Hodnota
        value = quantity * purchase
        self.lbl_stock_value.setText(f"Hodnota: {value:,.2f} Kč")

        # Status
        if quantity == 0:
            status = "❌ Nulový stav"
            color = config.STOCK_ZERO
        elif quantity < min_qty:
            status = f"⚠️ Pod minimem ({quantity:.2f} / {min_qty:.2f})"
            color = config.STOCK_CRITICAL
        elif quantity < min_qty * 1.5:
            status = f"⚡ Blíží se minimu ({quantity:.2f} / {min_qty:.2f})"
            color = config.STOCK_WARNING
        else:
            status = f"✓ V pořádku ({quantity:.2f})"
            color = config.STOCK_OK

        self.lbl_stock_status.setText(f"Stav: {status}")
        self.lbl_stock_status.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")

        # Aktualizace badge ve hlavičce
        self.lbl_status.setText(status)
        self.lbl_status.setStyleSheet(f"""
            background-color: {color};
            color: white;
            padding: 4px 12px;
            border-radius: 10px;
            font-weight: bold;
            font-size: 11px;
        """)

    def load_history(self):
        """Načtení historie pohybů"""
        try:
            movements = db.execute_query(
                """SELECT id, date, movement_type, quantity, unit_price, note
                   FROM warehouse_movements
                   WHERE item_id = ?
                   ORDER BY date DESC, id DESC
                   LIMIT 100""",
                [self.item_id]
            )

            self.table_history.setRowCount(0)

            if not movements:
                return

            for mov in movements:
                row = self.table_history.rowCount()
                self.table_history.insertRow(row)

                mov_id = mov[0]
                date = mov[1]
                mov_type = mov[2]
                quantity = mov[3]
                price = mov[4] or 0
                note = mov[5] or ""

                total = quantity * price

                # Typ pohybu s ikonou
                if mov_type == "Příjem":
                    type_text = "➕ Příjem"
                    qty_text = f"+{quantity:.2f}"
                elif mov_type == "Výdej":
                    type_text = "➖ Výdej"
                    qty_text = f"-{quantity:.2f}"
                else:
                    type_text = f"📊 {mov_type}"
                    qty_text = f"{quantity:.2f}"

                self.table_history.setItem(row, 0, QTableWidgetItem(date))
                self.table_history.setItem(row, 1, QTableWidgetItem(type_text))
                self.table_history.setItem(row, 2, QTableWidgetItem(qty_text))
                self.table_history.setItem(row, 3, QTableWidgetItem(f"{price:.2f} Kč"))
                self.table_history.setItem(row, 4, QTableWidgetItem(f"{total:.2f} Kč"))
                self.table_history.setItem(row, 5, QTableWidgetItem(note))
                self.table_history.setItem(row, 6, QTableWidgetItem(str(mov_id)))

        except Exception as e:
            print(f"Chyba při načítání historie: {e}")

    def load_statistics(self):
        """Načtení statistik"""
        try:
            # Celkem přijato
            received = db.execute_query(
                """SELECT SUM(quantity) FROM warehouse_movements
                   WHERE item_id = ? AND movement_type = 'Příjem'""",
                [self.item_id]
            )
            self.lbl_total_received.setText(f"{received[0][0] or 0:.2f}")

            # Celkem vydáno
            issued = db.execute_query(
                """SELECT SUM(quantity) FROM warehouse_movements
                   WHERE item_id = ? AND movement_type = 'Výdej'""",
                [self.item_id]
            )
            self.lbl_total_issued.setText(f"{issued[0][0] or 0:.2f}")

            # Průměrná nákupní cena
            avg_price = db.execute_query(
                """SELECT AVG(unit_price) FROM warehouse_movements
                   WHERE item_id = ? AND movement_type = 'Příjem' AND unit_price > 0""",
                [self.item_id]
            )
            if avg_price and avg_price[0][0]:
                self.lbl_avg_purchase_price.setText(f"{avg_price[0][0]:.2f} Kč")

            # Poslední pohyb
            last = db.execute_query(
                """SELECT date, movement_type FROM warehouse_movements
                   WHERE item_id = ?
                   ORDER BY date DESC, id DESC
                   LIMIT 1""",
                [self.item_id]
            )
            if last:
                self.lbl_last_movement.setText(f"{last[0][1]} - {last[0][0]}")

        except Exception as e:
            print(f"Chyba při načítání statistik: {e}")

    def save_item(self):
        """Uložení položky"""
        # Validace
        if not self.input_name.text():
            QMessageBox.warning(self, "Chyba", "Vyplňte název položky!")
            self.tabs.setCurrentIndex(0)
            self.input_name.setFocus()
            return

        if self.combo_category.currentData() is None:
            QMessageBox.warning(self, "Chyba", "Vyberte kategorii!")
            self.tabs.setCurrentIndex(0)
            return

        try:
            # Sběr dat
            data = {
                'name': self.input_name.text(),
                'code': self.input_code.text(),
                'ean': self.input_ean.text(),
                'category_id': self.combo_category.currentData(),
                'supplier_id': self.combo_supplier.currentData(),
                'description': self.text_description.toPlainText(),
                'notes': self.text_notes.toPlainText(),
                'quantity': self.spin_quantity.value(),
                'unit': self.combo_unit.currentText(),
                'min_quantity': self.spin_min_quantity.value(),
                'location': self.input_location.text(),
                'price_purchase': self.spin_price_purchase.value(),
                'price_sale': self.spin_price_sale.value()
            }

            if self.is_new:
                # Nová položka
                db.execute_query(
                    """INSERT INTO warehouse
                       (name, code, ean, category_id, supplier_id, description, notes,
                        quantity, unit, min_quantity, location, price_purchase, price_sale)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    list(data.values())
                )
                QMessageBox.information(self, "Úspěch", "Položka byla přidána do skladu")
            else:
                # Aktualizace
                db.execute_query(
                    """UPDATE warehouse SET
                       name=?, code=?, ean=?, category_id=?, supplier_id=?, description=?, notes=?,
                       quantity=?, unit=?, min_quantity=?, location=?, price_purchase=?, price_sale=?
                       WHERE id=?""",
                    list(data.values()) + [self.item_id]
                )
                QMessageBox.information(self, "Úspěch", "Položka byla aktualizována")

            self.item_updated.emit()
            self.close()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při ukládání:\n{str(e)}")

    def delete_item(self):
        """Smazání položky"""
        reply = QMessageBox.question(
            self,
            "Smazat položku?",
            f"Opravdu smazat '{self.input_name.text()}' ze skladu?\n\n⚠️ Tato akce je NEVRATNÁ!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                db.execute_query("DELETE FROM warehouse WHERE id = ?", [self.item_id])
                QMessageBox.information(self, "Smazáno", "Položka byla smazána")
                self.item_updated.emit()
                self.close()
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Chyba:\n{str(e)}")

    def receive_stock(self):
        """Příjem na sklad"""
        QMessageBox.information(self, "Info", "Dialog příjmu bude implementován v warehouse_widgets.py")

    def issue_stock(self):
        """Výdej ze skladu"""
        QMessageBox.information(self, "Info", "Dialog výdeje bude implementován v warehouse_widgets.py")

    def print_label(self):
        """Tisk štítku"""
        QMessageBox.information(self, "Info", "Tisk štítku bude implementován v warehouse_labels.py")

    def add_photo(self):
        """Přidání fotky"""
        QMessageBox.information(self, "Info", "Správa fotek bude doplněna v další verzi")

    def delete_photo(self):
        """Smazání fotky"""
        QMessageBox.information(self, "Info", "Správa fotek bude doplněna v další verzi")
