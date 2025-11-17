# -*- coding: utf-8 -*-
"""
Editor zakázkového listu - možnost vyplnit všechny údaje před tiskem
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QPushButton,
    QLabel, QLineEdit, QTextEdit, QDateEdit, QMessageBox, QGroupBox,
    QScrollArea, QWidget, QCheckBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
import config
from database_manager import db
from datetime import datetime


class WorkOrderEditorDialog(QDialog):
    """Dialog pro editaci a tisk zakázkového listu"""

    def __init__(self, order_id, parent=None):
        super().__init__(parent)
        self.order_id = order_id
        self.order_data = None

        self.setWindowTitle("Editor zakázkového listu")
        self.setModal(True)
        self.setMinimumSize(900, 700)

        self.init_ui()
        self.load_order_data()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # === HLAVIČKA ===
        header = QLabel("📄 Zakázkový list - úprava před tiskem")
        header.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {config.COLOR_PRIMARY};
            padding: 15px;
            background-color: #ecf0f1;
            border-radius: 5px;
        """)
        layout.addWidget(header)

        # === SCROLL AREA ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # === ZÁKLADNÍ ÚDAJE O ZAKÁZCE ===
        basic_group = QGroupBox("📋 Základní údaje")
        basic_layout = QFormLayout(basic_group)

        self.lbl_order_number = QLabel()
        self.lbl_order_number.setStyleSheet("font-weight: bold;")
        basic_layout.addRow("Číslo zakázky:", self.lbl_order_number)

        self.lbl_customer = QLabel()
        basic_layout.addRow("Zákazník:", self.lbl_customer)

        self.lbl_vehicle = QLabel()
        basic_layout.addRow("Vozidlo:", self.lbl_vehicle)

        scroll_layout.addWidget(basic_group)

        # === DATUM PŘÍJMU ===
        dates_group = QGroupBox("📅 Termíny")
        dates_layout = QFormLayout(dates_group)

        self.date_received = QDateEdit()
        self.date_received.setCalendarPopup(True)
        self.date_received.setDate(QDate.currentDate())
        dates_layout.addRow("Datum příjmu:", self.date_received)

        self.date_estimated = QDateEdit()
        self.date_estimated.setCalendarPopup(True)
        self.date_estimated.setDate(QDate.currentDate().addDays(7))
        dates_layout.addRow("Předběžný termín dokončení:", self.date_estimated)

        scroll_layout.addWidget(dates_group)

        # === STAV VOZIDLA ===
        vehicle_state_group = QGroupBox("🚗 Stav vozidla při příjmu")
        vehicle_state_layout = QVBoxLayout(vehicle_state_group)

        # Stav PHM
        phm_layout = QFormLayout()

        self.input_fuel_level = QLineEdit()
        self.input_fuel_level.setPlaceholderText("např. 1/2, 3/4, plná...")
        phm_layout.addRow("Stav PHM:", self.input_fuel_level)

        self.input_mileage = QLineEdit()
        self.input_mileage.setPlaceholderText("Stav tachometru...")
        phm_layout.addRow("Stav km:", self.input_mileage)

        vehicle_state_layout.addLayout(phm_layout)

        # Výbava vozidla
        equipment_label = QLabel("Výbava vozidla / viditelná poškození:")
        equipment_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        vehicle_state_layout.addWidget(equipment_label)

        self.text_equipment = QTextEdit()
        self.text_equipment.setMaximumHeight(80)
        self.text_equipment.setPlaceholderText("Např.: Lékárnička, trojúhelník, klíče, poškození pravého blatníku...")
        vehicle_state_layout.addWidget(self.text_equipment)

        scroll_layout.addWidget(vehicle_state_group)

        # === POPIS PRACÍ ===
        work_group = QGroupBox("🔧 Popis prací / požadavky zákazníka")
        work_layout = QVBoxLayout(work_group)

        self.text_work_description = QTextEdit()
        self.text_work_description.setMinimumHeight(150)
        self.text_work_description.setPlaceholderText(
            "Popište požadované práce...\n\n"
            "Toto pole se automaticky vyplní položkami z zakázky, "
            "ale můžete je upravit před tiskem."
        )
        work_layout.addWidget(self.text_work_description)

        scroll_layout.addWidget(work_group)

        # === ROZŠÍŘENÍ ZAKÁZKY ===
        extension_group = QGroupBox("📝 Prostor pro rozšíření zakázky / vyjádření opravny")
        extension_layout = QVBoxLayout(extension_group)

        info = QLabel("💡 Tento prostor slouží pro dodatečné práce nebo zjištění během opravy")
        info.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        extension_layout.addWidget(info)

        self.text_extension = QTextEdit()
        self.text_extension.setMinimumHeight(120)
        self.text_extension.setPlaceholderText(
            "Prostor pro doplnění dalších zjištěných závad, "
            "nutných prací nebo poznámek opravny..."
        )
        extension_layout.addWidget(self.text_extension)

        scroll_layout.addWidget(extension_group)

        # === PŘEDBĚŽNÁ CENA ===
        price_group = QGroupBox("💰 Předběžná cena")
        price_layout = QFormLayout(price_group)

        self.input_estimated_price = QLineEdit()
        self.input_estimated_price.setPlaceholderText("Odhad ceny včetně DPH...")
        price_layout.addRow("Odhad ceny vč. DPH:", self.input_estimated_price)

        self.check_price_from_order = QCheckBox("Použít cenu ze zakázky")
        self.check_price_from_order.setChecked(True)
        self.check_price_from_order.stateChanged.connect(self.toggle_price_input)
        price_layout.addRow("", self.check_price_from_order)

        scroll_layout.addWidget(price_group)

        # === POZNÁMKY ===
        notes_group = QGroupBox("📌 Dodatečné poznámky")
        notes_layout = QVBoxLayout(notes_group)

        self.text_notes = QTextEdit()
        self.text_notes.setMaximumHeight(80)
        self.text_notes.setPlaceholderText("Jakékoliv další poznámky k zakázce...")
        notes_layout.addWidget(self.text_notes)

        scroll_layout.addWidget(notes_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # === TLAČÍTKA ===
        buttons = QHBoxLayout()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 13px;
            }
        """)

        btn_preview = QPushButton("👁️ Náhled")
        btn_preview.clicked.connect(self.preview_document)
        btn_preview.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }}
        """)

        btn_print = QPushButton("🖨️ Vytisknout / Uložit PDF")
        btn_print.clicked.connect(self.print_document)
        btn_print.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }}
        """)

        buttons.addWidget(btn_cancel)
        buttons.addStretch()
        buttons.addWidget(btn_preview)
        buttons.addWidget(btn_print)

        layout.addLayout(buttons)

    def load_order_data(self):
        """Načtení dat zakázky"""
        try:
            # Načtení základních dat
            order = db.execute_query(
                """SELECT
                    o.order_number, o.total_price, o.created_date,
                    c.first_name || ' ' || c.last_name as customer_name,
                    v.brand || ' ' || v.model || ' (' || v.license_plate || ')' as vehicle_info,
                    v.mileage
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                LEFT JOIN vehicles v ON o.vehicle_id = v.id
                WHERE o.id = ?""",
                [self.order_id]
            )

            if order and len(order) > 0:
                self.order_data = order[0]

                # Vyplnění polí
                self.lbl_order_number.setText(self.order_data[0])
                self.lbl_customer.setText(self.order_data[3] or "---")
                self.lbl_vehicle.setText(self.order_data[4] or "---")

                # Předvyplnění ceny
                if self.order_data[1]:
                    self.input_estimated_price.setText(f"{self.order_data[1]:.2f}")

                # Stav km
                if self.order_data[5]:
                    self.input_mileage.setText(str(self.order_data[5]))

                # Načtení položek zakázky
                self.load_work_items()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při načítání:\n{str(e)}")

    def load_work_items(self):
        """Načtení položek zakázky do popisu prací"""
        try:
            items = db.execute_query(
                """SELECT item_type, name, quantity, unit
                   FROM order_items WHERE order_id = ?
                   ORDER BY item_type, id""",
                [self.order_id]
            )

            if items:
                work_text = "POŽADOVANÉ PRÁCE A MATERIÁL:\n\n"

                current_type = None
                for item in items:
                    item_type = item[0]

                    # Nadpis pro každý typ
                    if item_type != current_type:
                        if current_type is not None:
                            work_text += "\n"
                        work_text += f"=== {item_type.upper()} ===\n"
                        current_type = item_type

                    # Položka
                    work_text += f"• {item[1]}"
                    if item[2] and item[2] != 1:
                        work_text += f" ({item[2]:.2f} {item[3]})"
                    work_text += "\n"

                self.text_work_description.setPlainText(work_text)

        except Exception as e:
            print(f"Chyba při načítání položek: {e}")

    def toggle_price_input(self, state):
        """Přepínání možnosti editace ceny"""
        if state == Qt.CheckState.Checked.value:
            # Použít cenu ze zakázky
            if self.order_data and self.order_data[1]:
                self.input_estimated_price.setText(f"{self.order_data[1]:.2f}")
            self.input_estimated_price.setEnabled(False)
        else:
            # Ruční zadání
            self.input_estimated_price.setEnabled(True)
            self.input_estimated_price.setFocus()

    def preview_document(self):
        """Náhled dokumentu"""
        try:
            from .order_work_order_preview import WorkOrderPreviewDialog

            # Sestavení dat pro náhled
            preview_data = self.get_form_data()

            dialog = WorkOrderPreviewDialog(preview_data, self)
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při náhledu:\n{str(e)}")

    def print_document(self):
        """Tisk nebo uložení PDF"""
        try:
            from .order_export import exporter

            # Sestavení dat
            form_data = self.get_form_data()

            # Export pomocí order_export
            success = exporter.export_work_order_with_data(self.order_id, form_data, self)

            if success:
                QMessageBox.information(self, "Úspěch", "Zakázkový list byl vytištěn/uložen")
                self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při tisku:\n{str(e)}")

    def get_form_data(self):
        """Získání dat z formuláře"""
        return {
            'order_number': self.lbl_order_number.text(),
            'customer': self.lbl_customer.text(),
            'vehicle': self.lbl_vehicle.text(),
            'date_received': self.date_received.date().toString("dd.MM.yyyy"),
            'date_estimated': self.date_estimated.date().toString("dd.MM.yyyy"),
            'fuel_level': self.input_fuel_level.text(),
            'mileage': self.input_mileage.text(),
            'equipment': self.text_equipment.toPlainText(),
            'work_description': self.text_work_description.toPlainText(),
            'extension': self.text_extension.toPlainText(),
            'estimated_price': self.input_estimated_price.text(),
            'notes': self.text_notes.toPlainText()
        }
