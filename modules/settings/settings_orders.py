# -*- coding: utf-8 -*-
"""
Nastavení zakázek
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QLabel,
    QPushButton, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QColorDialog, QMessageBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QBrush
from database_manager import db
import config
import json


class OrdersSettingsWidget(QWidget):
    """Widget pro nastavení zakázek"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Inicializace UI"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Číslování zakázek
        main_layout.addWidget(self.create_numbering_section())

        # Typy zakázek
        main_layout.addWidget(self.create_types_section())

        # Stavy zakázek
        main_layout.addWidget(self.create_statuses_section())

        # Výchozí hodnoty
        main_layout.addWidget(self.create_defaults_section())

        # Položky zakázky
        main_layout.addWidget(self.create_items_section())

        # Automatizace
        main_layout.addWidget(self.create_automation_section())

        main_layout.addStretch()

        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        self.set_styles()

    def create_numbering_section(self):
        """Sekce číslování zakázek"""
        group = QGroupBox("🔢 Číslování zakázek")
        group.setObjectName("settingsGroup")
        layout = QFormLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Formát čísla
        self.number_format = QComboBox()
        self.number_format.addItems([
            "RRRR####",
            "ZAK-RRRR-####",
            "####/RRRR",
            "Vlastní"
        ])
        self.number_format.currentTextChanged.connect(self.update_preview)
        layout.addRow("Formát:", self.number_format)

        # Prefix
        self.number_prefix = QLineEdit()
        self.number_prefix.setPlaceholderText("ZAK-")
        self.number_prefix.setMaxLength(10)
        self.number_prefix.textChanged.connect(self.update_preview)
        layout.addRow("Prefix:", self.number_prefix)

        # Počáteční číslo
        self.start_number = QSpinBox()
        self.start_number.setRange(1, 999999)
        self.start_number.setValue(1)
        self.start_number.valueChanged.connect(self.update_preview)
        layout.addRow("Počáteční číslo:", self.start_number)

        # Počet číslic
        self.number_digits = QSpinBox()
        self.number_digits.setRange(3, 8)
        self.number_digits.setValue(4)
        self.number_digits.valueChanged.connect(self.update_preview)
        layout.addRow("Počet číslic:", self.number_digits)

        # Reset každý rok
        self.reset_yearly = QCheckBox("Resetovat číslování každý rok")
        self.reset_yearly.setChecked(True)
        layout.addRow("", self.reset_yearly)

        # Náhled
        preview_layout = QHBoxLayout()
        preview_label = QLabel("Náhled:")
        preview_label.setStyleSheet("font-weight: bold;")
        self.number_preview = QLabel("ZAK-2025-0001")
        self.number_preview.setStyleSheet("""
            background-color: #ecf0f1;
            padding: 8px 15px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 14px;
            font-weight: bold;
        """)
        preview_layout.addWidget(preview_label)
        preview_layout.addWidget(self.number_preview)
        preview_layout.addStretch()
        layout.addRow("", preview_layout)

        return group

    def create_types_section(self):
        """Sekce typů zakázek"""
        group = QGroupBox("📁 Typy zakázek")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Tabulka typů
        self.types_table = QTableWidget()
        self.types_table.setColumnCount(3)
        self.types_table.setHorizontalHeaderLabels(["Název", "Barva", "Aktivní"])

        header = self.types_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)

        self.types_table.setColumnWidth(1, 80)
        self.types_table.setColumnWidth(2, 80)

        self.types_table.setAlternatingRowColors(True)
        self.types_table.setMaximumHeight(200)

        layout.addWidget(self.types_table)

        # Tlačítka
        buttons_layout = QHBoxLayout()

        add_type_btn = QPushButton("➕ Přidat typ")
        add_type_btn.clicked.connect(self.add_order_type)

        remove_type_btn = QPushButton("➖ Odebrat")
        remove_type_btn.clicked.connect(self.remove_order_type)

        buttons_layout.addWidget(add_type_btn)
        buttons_layout.addWidget(remove_type_btn)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        return group

    def create_statuses_section(self):
        """Sekce stavů zakázek"""
        group = QGroupBox("📊 Stavy zakázek")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Tabulka stavů
        self.statuses_table = QTableWidget()
        self.statuses_table.setColumnCount(4)
        self.statuses_table.setHorizontalHeaderLabels(["Název", "Barva", "Ikona", "Pořadí"])

        header = self.statuses_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)

        self.statuses_table.setColumnWidth(1, 80)
        self.statuses_table.setColumnWidth(2, 80)
        self.statuses_table.setColumnWidth(3, 80)

        self.statuses_table.setAlternatingRowColors(True)
        self.statuses_table.setMaximumHeight(250)

        layout.addWidget(self.statuses_table)

        # Tlačítka
        buttons_layout = QHBoxLayout()

        add_status_btn = QPushButton("➕ Přidat stav")
        add_status_btn.clicked.connect(self.add_order_status)

        remove_status_btn = QPushButton("➖ Odebrat")
        remove_status_btn.clicked.connect(self.remove_order_status)

        up_btn = QPushButton("⬆️")
        up_btn.clicked.connect(self.move_status_up)

        down_btn = QPushButton("⬇️")
        down_btn.clicked.connect(self.move_status_down)

        buttons_layout.addWidget(add_status_btn)
        buttons_layout.addWidget(remove_status_btn)
        buttons_layout.addWidget(up_btn)
        buttons_layout.addWidget(down_btn)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        return group

    def create_defaults_section(self):
        """Sekce výchozích hodnot"""
        group = QGroupBox("⚙️ Výchozí hodnoty")
        group.setObjectName("settingsGroup")
        layout = QFormLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Výchozí typ
        self.default_type = QComboBox()
        layout.addRow("Výchozí typ zakázky:", self.default_type)

        # Výchozí stav
        self.default_status = QComboBox()
        layout.addRow("Výchozí stav nové zakázky:", self.default_status)

        # Automatické přiřazení
        self.auto_assign_mechanic = QCheckBox("Automaticky přiřadit výchozího mechanika")
        layout.addRow("", self.auto_assign_mechanic)

        self.auto_assign_customer = QCheckBox("Automaticky přiřadit zákazníka k vozidlu")
        self.auto_assign_customer.setChecked(True)
        layout.addRow("", self.auto_assign_customer)

        self.auto_calculate_price = QCheckBox("Automaticky vypočítat cenu")
        self.auto_calculate_price.setChecked(True)
        layout.addRow("", self.auto_calculate_price)

        return group

    def create_items_section(self):
        """Sekce položek zakázky"""
        group = QGroupBox("📝 Položky zakázky")
        group.setObjectName("settingsGroup")
        layout = QFormLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Výchozí DPH
        self.default_vat = QComboBox()
        self.default_vat.addItems(["21%", "15%", "12%", "0%"])
        layout.addRow("Výchozí DPH sazba:", self.default_vat)

        # Zaokrouhlování
        self.price_rounding = QComboBox()
        self.price_rounding.addItems([
            "Na koruny",
            "Na 10 haléřů",
            "Na 50 haléřů",
            "Bez zaokrouhlení"
        ])
        layout.addRow("Zaokrouhlování cen:", self.price_rounding)

        # Minimální marže
        min_margin_layout = QHBoxLayout()
        self.min_margin = QDoubleSpinBox()
        self.min_margin.setRange(0, 100)
        self.min_margin.setValue(20)
        self.min_margin.setSuffix(" %")
        min_margin_layout.addWidget(self.min_margin)

        self.warn_low_margin = QCheckBox("Varovat při nízké marži")
        self.warn_low_margin.setChecked(True)
        min_margin_layout.addWidget(self.warn_low_margin)
        min_margin_layout.addStretch()

        layout.addRow("Minimální marže:", min_margin_layout)

        return group

    def create_automation_section(self):
        """Sekce automatizace"""
        group = QGroupBox("🤖 Automatizace")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Email automatizace
        email_label = QLabel("Automatické odeslání emailu zákazníkovi při:")
        email_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(email_label)

        self.email_on_create = QCheckBox("Vytvoření zakázky")
        layout.addWidget(self.email_on_create)

        self.email_on_status_change = QCheckBox("Změně stavu zakázky")
        layout.addWidget(self.email_on_status_change)

        self.email_on_complete = QCheckBox("Dokončení zakázky")
        self.email_on_complete.setChecked(True)
        layout.addWidget(self.email_on_complete)

        # Tisk
        print_label = QLabel("Automatický tisk:")
        print_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(print_label)

        self.auto_print_order = QCheckBox("Vytisknout zakázkový list při vytvoření")
        layout.addWidget(self.auto_print_order)

        # Archivace
        archive_label = QLabel("Archivace:")
        archive_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(archive_label)

        archive_layout = QHBoxLayout()
        self.auto_archive = QCheckBox("Automatická archivace po")
        archive_layout.addWidget(self.auto_archive)

        self.archive_days = QSpinBox()
        self.archive_days.setRange(1, 365)
        self.archive_days.setValue(90)
        self.archive_days.setSuffix(" dnech")
        archive_layout.addWidget(self.archive_days)
        archive_layout.addStretch()

        layout.addLayout(archive_layout)

        return group

    def update_preview(self):
        """Aktualizace náhledu čísla zakázky"""
        format_type = self.number_format.currentText()
        prefix = self.number_prefix.text()
        start = self.start_number.value()
        digits = self.number_digits.value()

        year = "2025"
        number = str(start).zfill(digits)

        if format_type == "RRRR####":
            preview = f"{year}{number}"
        elif format_type == "ZAK-RRRR-####":
            preview = f"{prefix}{year}-{number}"
        elif format_type == "####/RRRR":
            preview = f"{number}/{year}"
        else:
            preview = f"{prefix}{number}"

        self.number_preview.setText(preview)

    def add_order_type(self):
        """Přidání typu zakázky"""
        row = self.types_table.rowCount()
        self.types_table.insertRow(row)

        self.types_table.setItem(row, 0, QTableWidgetItem("Nový typ"))

        color_item = QTableWidgetItem()
        color_item.setBackground(QBrush(QColor("#3498db")))
        self.types_table.setItem(row, 1, color_item)

        active_item = QTableWidgetItem()
        active_item.setFlags(active_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        active_item.setCheckState(Qt.CheckState.Checked)
        self.types_table.setItem(row, 2, active_item)

    def remove_order_type(self):
        """Odebrání typu zakázky"""
        current_row = self.types_table.currentRow()
        if current_row >= 0:
            self.types_table.removeRow(current_row)

    def add_order_status(self):
        """Přidání stavu zakázky"""
        row = self.statuses_table.rowCount()
        self.statuses_table.insertRow(row)

        self.statuses_table.setItem(row, 0, QTableWidgetItem("Nový stav"))

        color_item = QTableWidgetItem()
        color_item.setBackground(QBrush(QColor("#95a5a6")))
        self.statuses_table.setItem(row, 1, color_item)

        self.statuses_table.setItem(row, 2, QTableWidgetItem("📋"))
        self.statuses_table.setItem(row, 3, QTableWidgetItem(str(row + 1)))

        self.update_default_combos()

    def remove_order_status(self):
        """Odebrání stavu zakázky"""
        current_row = self.statuses_table.currentRow()
        if current_row >= 0:
            self.statuses_table.removeRow(current_row)
            self.update_default_combos()

    def move_status_up(self):
        """Posun stavu nahoru"""
        current_row = self.statuses_table.currentRow()
        if current_row > 0:
            self.swap_rows(self.statuses_table, current_row, current_row - 1)
            self.statuses_table.selectRow(current_row - 1)

    def move_status_down(self):
        """Posun stavu dolů"""
        current_row = self.statuses_table.currentRow()
        if current_row < self.statuses_table.rowCount() - 1:
            self.swap_rows(self.statuses_table, current_row, current_row + 1)
            self.statuses_table.selectRow(current_row + 1)

    def swap_rows(self, table, row1, row2):
        """Prohození řádků v tabulce"""
        for col in range(table.columnCount()):
            item1 = table.takeItem(row1, col)
            item2 = table.takeItem(row2, col)
            table.setItem(row1, col, item2)
            table.setItem(row2, col, item1)

    def update_default_combos(self):
        """Aktualizace výchozích comboboxů"""
        # Typy
        current_type = self.default_type.currentText()
        self.default_type.clear()
        for row in range(self.types_table.rowCount()):
            item = self.types_table.item(row, 0)
            if item:
                self.default_type.addItem(item.text())
        index = self.default_type.findText(current_type)
        if index >= 0:
            self.default_type.setCurrentIndex(index)

        # Stavy
        current_status = self.default_status.currentText()
        self.default_status.clear()
        for row in range(self.statuses_table.rowCount()):
            item = self.statuses_table.item(row, 0)
            if item:
                self.default_status.addItem(item.text())
        index = self.default_status.findText(current_status)
        if index >= 0:
            self.default_status.setCurrentIndex(index)

    def load_settings(self):
        """Načtení nastavení"""
        # Načtení typů zakázek
        default_types = [
            ("Zakázka", "#3498db", True),
            ("Volný prodej", "#27ae60", True),
            ("Interní zakázka", "#f39c12", True),
            ("Reklamace", "#e74c3c", True),
            ("Nabídka", "#9b59b6", True)
        ]

        self.types_table.setRowCount(len(default_types))
        for i, (name, color, active) in enumerate(default_types):
            self.types_table.setItem(i, 0, QTableWidgetItem(name))

            color_item = QTableWidgetItem()
            color_item.setBackground(QBrush(QColor(color)))
            self.types_table.setItem(i, 1, color_item)

            active_item = QTableWidgetItem()
            active_item.setFlags(active_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            active_item.setCheckState(Qt.CheckState.Checked if active else Qt.CheckState.Unchecked)
            self.types_table.setItem(i, 2, active_item)

        # Načtení stavů zakázek
        default_statuses = [
            ("V přípravě", "#95a5a6", "📝", 1),
            ("Otevřená", "#3498db", "📂", 2),
            ("Rozpracovaná", "#f39c12", "🔧", 3),
            ("Čeká na díly", "#f1c40f", "⏳", 4),
            ("Hotová", "#27ae60", "✅", 5),
            ("Fakturováno", "#9b59b6", "🧾", 6),
            ("Archiv", "#7f8c8d", "📦", 7)
        ]

        self.statuses_table.setRowCount(len(default_statuses))
        for i, (name, color, icon, order) in enumerate(default_statuses):
            self.statuses_table.setItem(i, 0, QTableWidgetItem(name))

            color_item = QTableWidgetItem()
            color_item.setBackground(QBrush(QColor(color)))
            self.statuses_table.setItem(i, 1, color_item)

            self.statuses_table.setItem(i, 2, QTableWidgetItem(icon))
            self.statuses_table.setItem(i, 3, QTableWidgetItem(str(order)))

        self.update_default_combos()
        self.update_preview()

    def save_settings(self):
        """Uložení nastavení"""
        settings = self.get_settings()

        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            for key, value in settings.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                cursor.execute("""
                    INSERT OR REPLACE INTO app_settings (key, value)
                    VALUES (?, ?)
                """, (f"orders_{key}", str(value)))

            conn.commit()

        except Exception as e:
            raise Exception(f"Chyba při ukládání: {str(e)}")

    def get_settings(self):
        """Získání nastavení"""
        # Typy zakázek
        types = []
        for row in range(self.types_table.rowCount()):
            name_item = self.types_table.item(row, 0)
            color_item = self.types_table.item(row, 1)
            active_item = self.types_table.item(row, 2)

            if name_item:
                types.append({
                    "name": name_item.text(),
                    "color": color_item.background().color().name() if color_item else "#3498db",
                    "active": active_item.checkState() == Qt.CheckState.Checked if active_item else True
                })

        # Stavy zakázek
        statuses = []
        for row in range(self.statuses_table.rowCount()):
            name_item = self.statuses_table.item(row, 0)
            color_item = self.statuses_table.item(row, 1)
            icon_item = self.statuses_table.item(row, 2)
            order_item = self.statuses_table.item(row, 3)

            if name_item:
                statuses.append({
                    "name": name_item.text(),
                    "color": color_item.background().color().name() if color_item else "#95a5a6",
                    "icon": icon_item.text() if icon_item else "📋",
                    "order": int(order_item.text()) if order_item else row + 1
                })

        return {
            "number_format": self.number_format.currentText(),
            "number_prefix": self.number_prefix.text(),
            "start_number": self.start_number.value(),
            "number_digits": self.number_digits.value(),
            "reset_yearly": self.reset_yearly.isChecked(),
            "types": types,
            "statuses": statuses,
            "default_type": self.default_type.currentText(),
            "default_status": self.default_status.currentText(),
            "auto_assign_mechanic": self.auto_assign_mechanic.isChecked(),
            "auto_assign_customer": self.auto_assign_customer.isChecked(),
            "auto_calculate_price": self.auto_calculate_price.isChecked(),
            "default_vat": self.default_vat.currentText(),
            "price_rounding": self.price_rounding.currentText(),
            "min_margin": self.min_margin.value(),
            "warn_low_margin": self.warn_low_margin.isChecked(),
            "email_on_create": self.email_on_create.isChecked(),
            "email_on_status_change": self.email_on_status_change.isChecked(),
            "email_on_complete": self.email_on_complete.isChecked(),
            "auto_print_order": self.auto_print_order.isChecked(),
            "auto_archive": self.auto_archive.isChecked(),
            "archive_days": self.archive_days.value()
        }

    def set_settings(self, settings):
        """Nastavení hodnot"""
        if "number_format" in settings:
            index = self.number_format.findText(settings["number_format"])
            if index >= 0:
                self.number_format.setCurrentIndex(index)

        if "number_prefix" in settings:
            self.number_prefix.setText(settings["number_prefix"])

        if "start_number" in settings:
            self.start_number.setValue(int(settings["start_number"]))

        if "number_digits" in settings:
            self.number_digits.setValue(int(settings["number_digits"]))

        if "reset_yearly" in settings:
            self.reset_yearly.setChecked(settings["reset_yearly"] == "True")

        self.update_preview()

    def refresh(self):
        """Obnovení"""
        self.load_settings()

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet("""
            #settingsGroup {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }

            #settingsGroup::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }

            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }

            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #3498db;
            }

            QTableWidget {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }

            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
            }

            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                background-color: #3498db;
                color: white;
                border: none;
            }

            QPushButton:hover {
                background-color: #2980b9;
            }

            QCheckBox {
                spacing: 8px;
            }
        """)
