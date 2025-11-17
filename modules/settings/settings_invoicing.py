# -*- coding: utf-8 -*-
"""
Nastavení fakturace
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QLabel,
    QPushButton, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QDoubleSpinBox, QFrame, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database_manager import db
import config
import json


class InvoicingSettingsWidget(QWidget):
    """Widget pro nastavení fakturace"""

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

        # Číselné řady
        main_layout.addWidget(self.create_numbering_section())

        # Splatnost
        main_layout.addWidget(self.create_due_date_section())

        # DPH
        main_layout.addWidget(self.create_vat_section())

        # Platební metody
        main_layout.addWidget(self.create_payment_methods_section())

        # Zaokrouhlování
        main_layout.addWidget(self.create_rounding_section())

        # Upomínky
        main_layout.addWidget(self.create_reminders_section())

        main_layout.addStretch()

        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        self.set_styles()

    def create_numbering_section(self):
        """Sekce číselných řad"""
        group = QGroupBox("🔢 Číselné řady")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 20, 15, 15)

        # Záložky pro různé typy dokladů
        tabs = QTabWidget()

        # Faktury vydané
        tabs.addTab(self.create_invoice_numbering("issued"), "📤 Faktury vydané")

        # Faktury přijaté
        tabs.addTab(self.create_invoice_numbering("received"), "📥 Faktury přijaté")

        # Dobropisy
        tabs.addTab(self.create_invoice_numbering("credit"), "💳 Dobropisy")

        # Zálohové faktury
        tabs.addTab(self.create_invoice_numbering("advance"), "💰 Zálohové faktury")

        layout.addWidget(tabs)

        return group

    def create_invoice_numbering(self, doc_type):
        """Vytvoření sekce číslování pro typ dokladu"""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 15, 10, 10)

        prefixes = {
            "issued": "FV-",
            "received": "FP-",
            "credit": "DOP-",
            "advance": "ZAL-"
        }

        # Formát
        format_combo = QComboBox()
        format_combo.addItems([
            "PREFIX-RRRR-####",
            "PREFIX####",
            "RRRR-PREFIX-####",
            "Vlastní"
        ])
        setattr(self, f"{doc_type}_format", format_combo)
        layout.addRow("Formát:", format_combo)

        # Prefix
        prefix_input = QLineEdit()
        prefix_input.setText(prefixes.get(doc_type, "DOK-"))
        prefix_input.setMaxLength(10)
        setattr(self, f"{doc_type}_prefix", prefix_input)
        layout.addRow("Prefix:", prefix_input)

        # Počáteční číslo
        start_number = QSpinBox()
        start_number.setRange(1, 999999)
        start_number.setValue(1)
        setattr(self, f"{doc_type}_start", start_number)
        layout.addRow("Počáteční číslo:", start_number)

        # Počet číslic
        digits = QSpinBox()
        digits.setRange(3, 8)
        digits.setValue(4)
        setattr(self, f"{doc_type}_digits", digits)
        layout.addRow("Počet číslic:", digits)

        # Reset ročně
        reset = QCheckBox("Resetovat číslování každý rok")
        reset.setChecked(True)
        setattr(self, f"{doc_type}_reset", reset)
        layout.addRow("", reset)

        # Náhled
        preview = QLabel(f"{prefixes.get(doc_type, 'DOK-')}2025-0001")
        preview.setStyleSheet("""
            background-color: #ecf0f1;
            padding: 8px 15px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 13px;
            font-weight: bold;
        """)
        setattr(self, f"{doc_type}_preview", preview)

        # Propojení signálů pro aktualizaci náhledu
        format_combo.currentTextChanged.connect(lambda: self.update_invoice_preview(doc_type))
        prefix_input.textChanged.connect(lambda: self.update_invoice_preview(doc_type))
        start_number.valueChanged.connect(lambda: self.update_invoice_preview(doc_type))
        digits.valueChanged.connect(lambda: self.update_invoice_preview(doc_type))

        preview_layout = QHBoxLayout()
        preview_layout.addWidget(QLabel("Náhled:"))
        preview_layout.addWidget(preview)
        preview_layout.addStretch()
        layout.addRow("", preview_layout)

        return widget

    def update_invoice_preview(self, doc_type):
        """Aktualizace náhledu čísla dokladu"""
        format_combo = getattr(self, f"{doc_type}_format")
        prefix_input = getattr(self, f"{doc_type}_prefix")
        start_number = getattr(self, f"{doc_type}_start")
        digits = getattr(self, f"{doc_type}_digits")
        preview = getattr(self, f"{doc_type}_preview")

        fmt = format_combo.currentText()
        prefix = prefix_input.text()
        number = str(start_number.value()).zfill(digits.value())
        year = "2025"

        if fmt == "PREFIX-RRRR-####":
            result = f"{prefix}{year}-{number}"
        elif fmt == "PREFIX####":
            result = f"{prefix}{number}"
        elif fmt == "RRRR-PREFIX-####":
            result = f"{year}-{prefix}{number}"
        else:
            result = f"{prefix}{number}"

        preview.setText(result)

    def create_due_date_section(self):
        """Sekce splatnosti"""
        group = QGroupBox("📅 Splatnost")
        group.setObjectName("settingsGroup")
        layout = QFormLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Výchozí splatnost
        self.default_due_days = QComboBox()
        self.default_due_days.addItems(["7 dní", "14 dní", "21 dní", "30 dní", "45 dní", "60 dní", "90 dní"])
        self.default_due_days.setCurrentIndex(1)  # 14 dní
        layout.addRow("Výchozí splatnost:", self.default_due_days)

        # Různá splatnost podle skupiny
        self.custom_due_by_group = QCheckBox("Různá splatnost podle skupiny zákazníka")
        self.custom_due_by_group.setChecked(True)
        layout.addRow("", self.custom_due_by_group)

        # Penále z prodlení
        penalty_layout = QHBoxLayout()
        self.late_penalty = QDoubleSpinBox()
        self.late_penalty.setRange(0, 1)
        self.late_penalty.setValue(0.05)
        self.late_penalty.setSuffix(" % denně")
        self.late_penalty.setDecimals(3)
        penalty_layout.addWidget(self.late_penalty)
        penalty_layout.addStretch()
        layout.addRow("Penále z prodlení:", penalty_layout)

        # Úrok z prodlení
        interest_layout = QHBoxLayout()
        self.late_interest = QDoubleSpinBox()
        self.late_interest.setRange(0, 50)
        self.late_interest.setValue(8.5)
        self.late_interest.setSuffix(" % ročně")
        self.late_interest.setDecimals(2)
        interest_layout.addWidget(self.late_interest)
        interest_layout.addStretch()
        layout.addRow("Úrok z prodlení:", interest_layout)

        # Tolerance
        tolerance_layout = QHBoxLayout()
        self.payment_tolerance = QSpinBox()
        self.payment_tolerance.setRange(0, 30)
        self.payment_tolerance.setValue(3)
        self.payment_tolerance.setSuffix(" dní")
        tolerance_layout.addWidget(self.payment_tolerance)
        tolerance_layout.addStretch()
        layout.addRow("Tolerance platby:", tolerance_layout)

        return group

    def create_vat_section(self):
        """Sekce DPH"""
        group = QGroupBox("📊 DPH")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Plátce DPH
        self.is_vat_payer = QCheckBox("Jsme plátce DPH")
        self.is_vat_payer.setChecked(True)
        self.is_vat_payer.toggled.connect(self.toggle_vat_options)
        layout.addWidget(self.is_vat_payer)

        # DIČ
        dic_layout = QHBoxLayout()
        dic_layout.addWidget(QLabel("DIČ firmy:"))
        self.company_dic = QLineEdit()
        self.company_dic.setPlaceholderText("CZ12345678")
        self.company_dic.setMaxLength(12)
        dic_layout.addWidget(self.company_dic)
        dic_layout.addStretch()
        layout.addLayout(dic_layout)

        # Sazby DPH
        vat_rates_label = QLabel("Sazby DPH:")
        vat_rates_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(vat_rates_label)

        self.vat_rates_table = QTableWidget()
        self.vat_rates_table.setColumnCount(3)
        self.vat_rates_table.setHorizontalHeaderLabels(["Název", "Sazba (%)", "Výchozí"])

        header = self.vat_rates_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)

        self.vat_rates_table.setColumnWidth(1, 100)
        self.vat_rates_table.setColumnWidth(2, 80)
        self.vat_rates_table.setMaximumHeight(150)

        # Výchozí sazby
        default_rates = [
            ("Základní sazba", "21", True),
            ("První snížená sazba", "12", False),
            ("Nulová sazba", "0", False)
        ]

        self.vat_rates_table.setRowCount(len(default_rates))
        for i, (name, rate, is_default) in enumerate(default_rates):
            self.vat_rates_table.setItem(i, 0, QTableWidgetItem(name))
            self.vat_rates_table.setItem(i, 1, QTableWidgetItem(rate))

            default_item = QTableWidgetItem()
            default_item.setFlags(default_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            default_item.setCheckState(Qt.CheckState.Checked if is_default else Qt.CheckState.Unchecked)
            self.vat_rates_table.setItem(i, 2, default_item)

        layout.addWidget(self.vat_rates_table)

        # Režim přenesení daňové povinnosti
        self.reverse_charge = QCheckBox("Podporovat režim přenesení daňové povinnosti")
        layout.addWidget(self.reverse_charge)

        return group

    def toggle_vat_options(self, checked):
        """Přepnutí možností DPH"""
        self.company_dic.setEnabled(checked)
        self.vat_rates_table.setEnabled(checked)
        self.reverse_charge.setEnabled(checked)

    def create_payment_methods_section(self):
        """Sekce platebních metod"""
        group = QGroupBox("💳 Platební metody")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Tabulka metod
        self.payment_methods_table = QTableWidget()
        self.payment_methods_table.setColumnCount(4)
        self.payment_methods_table.setHorizontalHeaderLabels(["Metoda", "Poplatek (%)", "Aktivní", "Výchozí"])

        header = self.payment_methods_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)

        self.payment_methods_table.setColumnWidth(1, 100)
        self.payment_methods_table.setColumnWidth(2, 80)
        self.payment_methods_table.setColumnWidth(3, 80)
        self.payment_methods_table.setMaximumHeight(180)

        # Výchozí metody
        default_methods = [
            ("Bankovní převod", "0", True, True),
            ("Hotovost", "0", True, False),
            ("Platební karta", "1.5", True, False),
            ("Dobírka", "2", False, False)
        ]

        self.payment_methods_table.setRowCount(len(default_methods))
        for i, (name, fee, active, is_default) in enumerate(default_methods):
            self.payment_methods_table.setItem(i, 0, QTableWidgetItem(name))
            self.payment_methods_table.setItem(i, 1, QTableWidgetItem(fee))

            active_item = QTableWidgetItem()
            active_item.setFlags(active_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            active_item.setCheckState(Qt.CheckState.Checked if active else Qt.CheckState.Unchecked)
            self.payment_methods_table.setItem(i, 2, active_item)

            default_item = QTableWidgetItem()
            default_item.setFlags(default_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            default_item.setCheckState(Qt.CheckState.Checked if is_default else Qt.CheckState.Unchecked)
            self.payment_methods_table.setItem(i, 3, default_item)

        layout.addWidget(self.payment_methods_table)

        # Tlačítka
        buttons_layout = QHBoxLayout()

        add_btn = QPushButton("➕ Přidat metodu")
        add_btn.clicked.connect(self.add_payment_method)

        remove_btn = QPushButton("➖ Odebrat")
        remove_btn.clicked.connect(self.remove_payment_method)

        buttons_layout.addWidget(add_btn)
        buttons_layout.addWidget(remove_btn)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        return group

    def add_payment_method(self):
        """Přidání platební metody"""
        row = self.payment_methods_table.rowCount()
        self.payment_methods_table.insertRow(row)

        self.payment_methods_table.setItem(row, 0, QTableWidgetItem("Nová metoda"))
        self.payment_methods_table.setItem(row, 1, QTableWidgetItem("0"))

        active_item = QTableWidgetItem()
        active_item.setFlags(active_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        active_item.setCheckState(Qt.CheckState.Checked)
        self.payment_methods_table.setItem(row, 2, active_item)

        default_item = QTableWidgetItem()
        default_item.setFlags(default_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        default_item.setCheckState(Qt.CheckState.Unchecked)
        self.payment_methods_table.setItem(row, 3, default_item)

    def remove_payment_method(self):
        """Odebrání platební metody"""
        current_row = self.payment_methods_table.currentRow()
        if current_row >= 0:
            self.payment_methods_table.removeRow(current_row)

    def create_rounding_section(self):
        """Sekce zaokrouhlování"""
        group = QGroupBox("🔄 Zaokrouhlování")
        group.setObjectName("settingsGroup")
        layout = QFormLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Zaokrouhlování faktur
        self.invoice_rounding = QComboBox()
        self.invoice_rounding.addItems([
            "Na koruny",
            "Na 10 haléřů",
            "Na 50 haléřů",
            "Bez zaokrouhlení"
        ])
        layout.addRow("Zaokrouhlování faktur:", self.invoice_rounding)

        # Zaokrouhlování DPH
        self.vat_rounding = QComboBox()
        self.vat_rounding.addItems([
            "Na haléře",
            "Na koruny",
            "Bez zaokrouhlení"
        ])
        layout.addRow("Zaokrouhlování DPH:", self.vat_rounding)

        # Způsob zaokrouhlení
        self.rounding_method = QComboBox()
        self.rounding_method.addItems([
            "Matematicky",
            "Vždy nahoru",
            "Vždy dolů"
        ])
        layout.addRow("Způsob zaokrouhlení:", self.rounding_method)

        return group

    def create_reminders_section(self):
        """Sekce upomínek"""
        group = QGroupBox("📧 Upomínky")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Automatické upomínky
        self.auto_reminders = QCheckBox("Automaticky odesílat upomínky")
        self.auto_reminders.toggled.connect(self.toggle_reminder_options)
        layout.addWidget(self.auto_reminders)

        # Nastavení upomínek
        reminders_frame = QFrame()
        reminders_frame.setObjectName("remindersFrame")
        reminders_layout = QFormLayout(reminders_frame)
        reminders_layout.setSpacing(8)

        # 1. upomínka
        first_layout = QHBoxLayout()
        self.reminder_1_days = QSpinBox()
        self.reminder_1_days.setRange(1, 90)
        self.reminder_1_days.setValue(7)
        self.reminder_1_days.setSuffix(" dní po splatnosti")
        first_layout.addWidget(self.reminder_1_days)
        first_layout.addStretch()
        reminders_layout.addRow("1. upomínka:", first_layout)

        # 2. upomínka
        second_layout = QHBoxLayout()
        self.reminder_2_days = QSpinBox()
        self.reminder_2_days.setRange(1, 120)
        self.reminder_2_days.setValue(14)
        self.reminder_2_days.setSuffix(" dní po splatnosti")
        second_layout.addWidget(self.reminder_2_days)
        second_layout.addStretch()
        reminders_layout.addRow("2. upomínka:", second_layout)

        # 3. upomínka
        third_layout = QHBoxLayout()
        self.reminder_3_days = QSpinBox()
        self.reminder_3_days.setRange(1, 180)
        self.reminder_3_days.setValue(30)
        self.reminder_3_days.setSuffix(" dní po splatnosti")
        third_layout.addWidget(self.reminder_3_days)
        third_layout.addStretch()
        reminders_layout.addRow("3. upomínka:", third_layout)

        self.reminders_frame = reminders_frame
        layout.addWidget(reminders_frame)

        # Upozornění
        info_label = QLabel("💡 Šablony upomínek můžete upravit v sekci 'Šablony dokumentů'")
        info_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(info_label)

        self.toggle_reminder_options(False)

        return group

    def toggle_reminder_options(self, checked):
        """Přepnutí možností upomínek"""
        self.reminders_frame.setEnabled(checked)

    def load_settings(self):
        """Načtení nastavení"""
        # Aktualizace náhledů
        for doc_type in ["issued", "received", "credit", "advance"]:
            self.update_invoice_preview(doc_type)

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
                """, (f"invoicing_{key}", str(value)))

            conn.commit()

        except Exception as e:
            raise Exception(f"Chyba při ukládání: {str(e)}")

    def get_settings(self):
        """Získání nastavení"""
        # Číselné řady
        numbering = {}
        for doc_type in ["issued", "received", "credit", "advance"]:
            numbering[doc_type] = {
                "format": getattr(self, f"{doc_type}_format").currentText(),
                "prefix": getattr(self, f"{doc_type}_prefix").text(),
                "start": getattr(self, f"{doc_type}_start").value(),
                "digits": getattr(self, f"{doc_type}_digits").value(),
                "reset_yearly": getattr(self, f"{doc_type}_reset").isChecked()
            }

        # DPH sazby
        vat_rates = []
        for row in range(self.vat_rates_table.rowCount()):
            name_item = self.vat_rates_table.item(row, 0)
            rate_item = self.vat_rates_table.item(row, 1)
            default_item = self.vat_rates_table.item(row, 2)

            if name_item and rate_item:
                vat_rates.append({
                    "name": name_item.text(),
                    "rate": float(rate_item.text()),
                    "is_default": default_item.checkState() == Qt.CheckState.Checked if default_item else False
                })

        # Platební metody
        payment_methods = []
        for row in range(self.payment_methods_table.rowCount()):
            name_item = self.payment_methods_table.item(row, 0)
            fee_item = self.payment_methods_table.item(row, 1)
            active_item = self.payment_methods_table.item(row, 2)
            default_item = self.payment_methods_table.item(row, 3)

            if name_item:
                payment_methods.append({
                    "name": name_item.text(),
                    "fee": float(fee_item.text()) if fee_item else 0,
                    "active": active_item.checkState() == Qt.CheckState.Checked if active_item else True,
                    "is_default": default_item.checkState() == Qt.CheckState.Checked if default_item else False
                })

        return {
            "numbering": numbering,
            "default_due_days": self.default_due_days.currentText(),
            "custom_due_by_group": self.custom_due_by_group.isChecked(),
            "late_penalty": self.late_penalty.value(),
            "late_interest": self.late_interest.value(),
            "payment_tolerance": self.payment_tolerance.value(),
            "is_vat_payer": self.is_vat_payer.isChecked(),
            "company_dic": self.company_dic.text(),
            "vat_rates": vat_rates,
            "reverse_charge": self.reverse_charge.isChecked(),
            "payment_methods": payment_methods,
            "invoice_rounding": self.invoice_rounding.currentText(),
            "vat_rounding": self.vat_rounding.currentText(),
            "rounding_method": self.rounding_method.currentText(),
            "auto_reminders": self.auto_reminders.isChecked(),
            "reminder_1_days": self.reminder_1_days.value(),
            "reminder_2_days": self.reminder_2_days.value(),
            "reminder_3_days": self.reminder_3_days.value()
        }

    def set_settings(self, settings):
        """Nastavení hodnot"""
        if "is_vat_payer" in settings:
            self.is_vat_payer.setChecked(settings["is_vat_payer"] == "True")

        if "company_dic" in settings:
            self.company_dic.setText(settings["company_dic"])

        if "auto_reminders" in settings:
            self.auto_reminders.setChecked(settings["auto_reminders"] == "True")

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

            #remindersFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
            }

            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }

            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }

            QTabBar::tab:selected {
                background-color: white;
                font-weight: bold;
            }
        """)
