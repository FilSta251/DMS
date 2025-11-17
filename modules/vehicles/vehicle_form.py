# -*- coding: utf-8 -*-
"""
Dialog pro přidání/editaci vozidla
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QTextEdit, QComboBox, QPushButton, QLabel, QMessageBox, QFrame,
    QGroupBox, QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QGridLayout, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime
import config
from database_manager import db


class VehicleFormDialog(QDialog):
    """Dialog pro přidání nebo editaci vozidla"""

    def __init__(self, parent=None, vehicle_id=None):
        super().__init__(parent)
        self.vehicle_id = vehicle_id
        self.selected_customer_id = None
        self.init_ui()

        if vehicle_id:
            self.load_vehicle_data()

    def init_ui(self):
        """Inicializace uživatelského rozhraní"""
        if self.vehicle_id:
            self.setWindowTitle("✏️ Upravit vozidlo")
        else:
            self.setWindowTitle("➕ Nové vozidlo")

        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit, QSpinBox, QComboBox, QDateEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QDateEdit:focus {
                border-color: #3498db;
            }
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QTextEdit:focus {
                border-color: #3498db;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Tabs
        tabs = QTabWidget()

        # Tab 1: Základní údaje
        tab_basic = QWidget()
        tab_basic_layout = QVBoxLayout(tab_basic)

        # Skupina: Údaje o vozidle
        vehicle_group = QGroupBox("🏍️ Údaje o vozidle")
        vehicle_layout = QGridLayout(vehicle_group)
        vehicle_layout.setSpacing(10)

        # SPZ
        vehicle_layout.addWidget(QLabel("SPZ *:"), 0, 0)
        self.spz_input = QLineEdit()
        self.spz_input.setPlaceholderText("např. 1A2 3456")
        self.spz_input.setMaxLength(20)
        vehicle_layout.addWidget(self.spz_input, 0, 1)

        # Značka
        vehicle_layout.addWidget(QLabel("Značka *:"), 0, 2)
        self.brand_input = QComboBox()
        self.brand_input.setEditable(True)
        self.brand_input.addItems([
            "", "Honda", "Yamaha", "Suzuki", "Kawasaki", "BMW", "Harley-Davidson",
            "Ducati", "KTM", "Triumph", "Aprilia", "Indian", "Husqvarna",
            "Royal Enfield", "Moto Guzzi", "MV Agusta", "Benelli", "CFMoto"
        ])
        vehicle_layout.addWidget(self.brand_input, 0, 3)

        # Model
        vehicle_layout.addWidget(QLabel("Model *:"), 1, 0)
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("např. CB500X")
        vehicle_layout.addWidget(self.model_input, 1, 1)

        # Rok výroby
        vehicle_layout.addWidget(QLabel("Rok výroby:"), 1, 2)
        self.year_input = QSpinBox()
        self.year_input.setRange(1900, datetime.now().year + 1)
        self.year_input.setValue(datetime.now().year)
        self.year_input.setSpecialValueText("Neuvedeno")
        vehicle_layout.addWidget(self.year_input, 1, 3)

        # VIN
        vehicle_layout.addWidget(QLabel("VIN:"), 2, 0)
        self.vin_input = QLineEdit()
        self.vin_input.setPlaceholderText("17 znaků")
        self.vin_input.setMaxLength(17)
        vehicle_layout.addWidget(self.vin_input, 2, 1)

        # Barva
        vehicle_layout.addWidget(QLabel("Barva:"), 2, 2)
        self.color_input = QComboBox()
        self.color_input.setEditable(True)
        self.color_input.addItems([
            "", "Černá", "Bílá", "Červená", "Modrá", "Zelená", "Žlutá",
            "Oranžová", "Šedá", "Stříbrná", "Zlatá", "Hnědá", "Fialová"
        ])
        vehicle_layout.addWidget(self.color_input, 2, 3)

        # Typ motoru
        vehicle_layout.addWidget(QLabel("Typ motoru:"), 3, 0)
        self.engine_input = QLineEdit()
        self.engine_input.setPlaceholderText("např. 500cc, V-Twin")
        vehicle_layout.addWidget(self.engine_input, 3, 1)

        # Typ paliva
        vehicle_layout.addWidget(QLabel("Palivo:"), 3, 2)
        self.fuel_input = QComboBox()
        self.fuel_input.addItems(["", "Benzín", "Diesel", "Elektro", "Hybrid"])
        vehicle_layout.addWidget(self.fuel_input, 3, 3)

        # Stav km
        vehicle_layout.addWidget(QLabel("Stav km:"), 4, 0)
        self.mileage_input = QSpinBox()
        self.mileage_input.setRange(0, 999999)
        self.mileage_input.setSuffix(" km")
        self.mileage_input.setSpecialValueText("Neuvedeno")
        vehicle_layout.addWidget(self.mileage_input, 4, 1)

        # STK platná do
        vehicle_layout.addWidget(QLabel("STK platná do:"), 4, 2)
        self.stk_input = QDateEdit()
        self.stk_input.setCalendarPopup(True)
        self.stk_input.setDate(QDate.currentDate().addYears(2))
        self.stk_input.setDisplayFormat("dd.MM.yyyy")
        self.stk_input.setSpecialValueText("Neuvedeno")
        vehicle_layout.addWidget(self.stk_input, 4, 3)

        tab_basic_layout.addWidget(vehicle_group)

        # Skupina: Zákazník
        customer_group = QGroupBox("👤 Majitel vozidla")
        customer_layout = QVBoxLayout(customer_group)

        # Vybraný zákazník
        customer_info_layout = QHBoxLayout()

        self.customer_label = QLabel("Není vybrán zákazník")
        self.customer_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
                font-size: 13px;
            }
        """)
        customer_info_layout.addWidget(self.customer_label)

        btn_select_customer = QPushButton("🔍 Vybrat zákazníka")
        btn_select_customer.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: #2980b9;
            }}
        """)
        btn_select_customer.clicked.connect(self.select_customer)
        customer_info_layout.addWidget(btn_select_customer)

        btn_new_customer = QPushButton("➕ Nový zákazník")
        btn_new_customer.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: #219a52;
            }}
        """)
        btn_new_customer.clicked.connect(self.add_new_customer)
        customer_info_layout.addWidget(btn_new_customer)

        btn_clear_customer = QPushButton("❌ Zrušit výběr")
        btn_clear_customer.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        btn_clear_customer.clicked.connect(self.clear_customer)
        customer_info_layout.addWidget(btn_clear_customer)

        customer_layout.addLayout(customer_info_layout)
        tab_basic_layout.addWidget(customer_group)

        # Poznámky
        notes_group = QGroupBox("📝 Poznámky")
        notes_layout = QVBoxLayout(notes_group)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Poznámky k vozidlu...")
        self.notes_input.setMaximumHeight(100)
        notes_layout.addWidget(self.notes_input)

        tab_basic_layout.addWidget(notes_group)
        tab_basic_layout.addStretch()

        tabs.addTab(tab_basic, "Základní údaje")

        # Tab 2: Technické údaje (pro budoucí rozšíření)
        tab_technical = QWidget()
        tab_technical_layout = QVBoxLayout(tab_technical)

        tech_label = QLabel("Technické údaje budou k dispozici v příští verzi.")
        tech_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tech_label.setStyleSheet("color: #7f8c8d; padding: 50px; font-size: 14px;")
        tab_technical_layout.addWidget(tech_label)

        tabs.addTab(tab_technical, "Technické údaje")

        layout.addWidget(tabs)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 12px 25px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Uložit")
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 12px 25px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #219a52;
            }}
        """)
        btn_save.clicked.connect(self.save_vehicle)
        buttons_layout.addWidget(btn_save)

        layout.addLayout(buttons_layout)

    def load_vehicle_data(self):
        """Načtení dat vozidla pro editaci"""
        try:
            vehicle = db.fetch_one("""
                SELECT v.*,
                       c.first_name || ' ' || c.last_name as customer_name,
                       c.phone as customer_phone
                FROM vehicles v
                LEFT JOIN customers c ON v.customer_id = c.id
                WHERE v.id = ?
            """, (self.vehicle_id,))

            if vehicle:
                self.spz_input.setText(vehicle['license_plate'] or '')
                self.brand_input.setCurrentText(vehicle['brand'] or '')
                self.model_input.setText(vehicle['model'] or '')

                if vehicle['year']:
                    self.year_input.setValue(vehicle['year'])
                else:
                    self.year_input.setValue(self.year_input.minimum())

                self.vin_input.setText(vehicle['vin'] or '')
                self.color_input.setCurrentText(vehicle['color'] or '')
                self.engine_input.setText(vehicle['engine_type'] or '')
                self.fuel_input.setCurrentText(vehicle['fuel_type'] or '')

                if vehicle['mileage']:
                    self.mileage_input.setValue(vehicle['mileage'])
                else:
                    self.mileage_input.setValue(0)

                if vehicle['stk_valid_until']:
                    try:
                        stk_date = datetime.strptime(str(vehicle['stk_valid_until']), "%Y-%m-%d")
                        self.stk_input.setDate(QDate(stk_date.year, stk_date.month, stk_date.day))
                    except:
                        pass

                self.notes_input.setPlainText(vehicle['notes'] or '')

                if vehicle['customer_id']:
                    self.selected_customer_id = vehicle['customer_id']
                    customer_text = vehicle['customer_name'] or 'Neznámý'
                    if vehicle['customer_phone']:
                        customer_text += f" ({vehicle['customer_phone']})"
                    self.customer_label.setText(f"✅ {customer_text}")
                    self.customer_label.setStyleSheet("""
                        QLabel {
                            padding: 10px;
                            background-color: #d5f5e3;
                            border-radius: 5px;
                            font-size: 13px;
                            color: #27ae60;
                        }
                    """)
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst data vozidla:\n{e}")

    def select_customer(self):
        """Výběr existujícího zákazníka"""
        dialog = CustomerSelectDialog(self)
        if dialog.exec():
            customer = dialog.get_selected_customer()
            if customer:
                self.selected_customer_id = customer['id']
                self.customer_label.setText(f"✅ {customer['name']}")
                self.customer_label.setStyleSheet("""
                    QLabel {
                        padding: 10px;
                        background-color: #d5f5e3;
                        border-radius: 5px;
                        font-size: 13px;
                        color: #27ae60;
                    }
                """)

    def add_new_customer(self):
        """Přidání nového zákazníka"""
        dialog = QuickCustomerDialog(self)
        if dialog.exec():
            customer = dialog.get_customer_data()
            if customer:
                self.selected_customer_id = customer['id']
                self.customer_label.setText(f"✅ {customer['name']}")
                self.customer_label.setStyleSheet("""
                    QLabel {
                        padding: 10px;
                        background-color: #d5f5e3;
                        border-radius: 5px;
                        font-size: 13px;
                        color: #27ae60;
                    }
                """)

    def clear_customer(self):
        """Zrušení výběru zákazníka"""
        self.selected_customer_id = None
        self.customer_label.setText("Není vybrán zákazník")
        self.customer_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
                font-size: 13px;
            }
        """)

    def validate_form(self):
        """Validace formuláře"""
        errors = []

        if not self.spz_input.text().strip():
            errors.append("SPZ je povinný údaj")

        if not self.brand_input.currentText().strip():
            errors.append("Značka je povinný údaj")

        if not self.model_input.text().strip():
            errors.append("Model je povinný údaj")

        # Kontrola unikátnosti SPZ
        spz = self.spz_input.text().strip().upper()
        if self.vehicle_id:
            existing = db.fetch_one(
                "SELECT id FROM vehicles WHERE license_plate = ? AND id != ?",
                (spz, self.vehicle_id)
            )
        else:
            existing = db.fetch_one(
                "SELECT id FROM vehicles WHERE license_plate = ?",
                (spz,)
            )

        if existing:
            errors.append(f"Vozidlo s SPZ '{spz}' již existuje")

        return errors

    def save_vehicle(self):
        """Uložení vozidla"""
        errors = self.validate_form()

        if errors:
            QMessageBox.warning(
                self,
                "Chyba validace",
                "Opravte následující chyby:\n\n• " + "\n• ".join(errors)
            )
            return

        try:
            # Příprava dat
            spz = self.spz_input.text().strip().upper()
            brand = self.brand_input.currentText().strip()
            model = self.model_input.text().strip()
            year = self.year_input.value() if self.year_input.value() > self.year_input.minimum() else None
            vin = self.vin_input.text().strip().upper() or None
            color = self.color_input.currentText().strip() or None
            engine = self.engine_input.text().strip() or None
            fuel = self.fuel_input.currentText() or None
            mileage = self.mileage_input.value() if self.mileage_input.value() > 0 else None
            stk_date = self.stk_input.date().toString("yyyy-MM-dd") if self.stk_input.date() > self.stk_input.minimumDate() else None
            notes = self.notes_input.toPlainText().strip() or None
            customer_id = self.selected_customer_id

            if self.vehicle_id:
                # Aktualizace
                db.execute_query("""
                    UPDATE vehicles SET
                        license_plate = ?,
                        brand = ?,
                        model = ?,
                        year = ?,
                        vin = ?,
                        color = ?,
                        engine_type = ?,
                        fuel_type = ?,
                        mileage = ?,
                        stk_valid_until = ?,
                        notes = ?,
                        customer_id = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (spz, brand, model, year, vin, color, engine, fuel, mileage,
                      stk_date, notes, customer_id, self.vehicle_id))
            else:
                # Nové vozidlo
                db.execute_query("""
                    INSERT INTO vehicles (
                        license_plate, brand, model, year, vin, color,
                        engine_type, fuel_type, mileage, stk_valid_until,
                        notes, customer_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (spz, brand, model, year, vin, color, engine, fuel, mileage,
                      stk_date, notes, customer_id))

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit vozidlo:\n{e}")


class CustomerSelectDialog(QDialog):
    """Dialog pro výběr existujícího zákazníka"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_customer = None
        self.init_ui()
        self.load_customers()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("🔍 Vybrat zákazníka")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Vyhledávání
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 Hledat:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Jméno, telefon, email, IČO...")
        self.search_input.textChanged.connect(self.filter_customers)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Tabulka
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Jméno", "Příjmení", "Firma", "Telefon", "Email"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setColumnHidden(0, True)
        self.table.doubleClicked.connect(self.select_and_close)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        btn_select = QPushButton("✅ Vybrat")
        btn_select.setStyleSheet(f"background-color: {config.COLOR_SUCCESS};")
        btn_select.clicked.connect(self.select_and_close)
        buttons_layout.addWidget(btn_select)

        layout.addLayout(buttons_layout)

    def load_customers(self):
        """Načtení zákazníků"""
        try:
            customers = db.fetch_all("""
                SELECT id, first_name, last_name, company, phone, email
                FROM customers
                ORDER BY last_name, first_name
            """)

            self.table.setRowCount(0)
            for customer in customers:
                row = self.table.rowCount()
                self.table.insertRow(row)

                self.table.setItem(row, 0, QTableWidgetItem(str(customer['id'])))
                self.table.setItem(row, 1, QTableWidgetItem(customer['first_name'] or ''))
                self.table.setItem(row, 2, QTableWidgetItem(customer['last_name'] or ''))
                self.table.setItem(row, 3, QTableWidgetItem(customer['company'] or ''))
                self.table.setItem(row, 4, QTableWidgetItem(customer['phone'] or ''))
                self.table.setItem(row, 5, QTableWidgetItem(customer['email'] or ''))
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst zákazníky:\n{e}")

    def filter_customers(self):
        """Filtrování zákazníků"""
        search_text = self.search_input.text().lower()

        for row in range(self.table.rowCount()):
            show_row = False
            for col in range(1, self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    show_row = True
                    break
            self.table.setRowHidden(row, not show_row)

    def select_and_close(self):
        """Výběr zákazníka a zavření"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Upozornění", "Vyberte zákazníka.")
            return

        customer_id = int(self.table.item(selected_row, 0).text())
        first_name = self.table.item(selected_row, 1).text()
        last_name = self.table.item(selected_row, 2).text()
        phone = self.table.item(selected_row, 4).text()

        name = f"{first_name} {last_name}"
        if phone:
            name += f" ({phone})"

        self.selected_customer = {
            'id': customer_id,
            'name': name
        }

        self.accept()

    def get_selected_customer(self):
        """Získání vybraného zákazníka"""
        return self.selected_customer


class QuickCustomerDialog(QDialog):
    """Dialog pro rychlé vytvoření zákazníka"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.customer_data = None
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("➕ Nový zákazník")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("Povinný údaj")
        form_layout.addRow("Jméno *:", self.first_name_input)

        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Povinný údaj")
        form_layout.addRow("Příjmení *:", self.last_name_input)

        self.company_input = QLineEdit()
        form_layout.addRow("Firma:", self.company_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+420 123 456 789")
        form_layout.addRow("Telefon:", self.phone_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@example.com")
        form_layout.addRow("Email:", self.email_input)

        self.address_input = QLineEdit()
        form_layout.addRow("Adresa:", self.address_input)

        self.city_input = QLineEdit()
        form_layout.addRow("Město:", self.city_input)

        self.postal_code_input = QLineEdit()
        self.postal_code_input.setMaxLength(10)
        form_layout.addRow("PSČ:", self.postal_code_input)

        self.ico_input = QLineEdit()
        self.ico_input.setMaxLength(20)
        form_layout.addRow("IČO:", self.ico_input)

        self.dic_input = QLineEdit()
        self.dic_input.setMaxLength(20)
        form_layout.addRow("DIČ:", self.dic_input)

        layout.addLayout(form_layout)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Vytvořit zákazníka")
        btn_save.setStyleSheet(f"background-color: {config.COLOR_SUCCESS};")
        btn_save.clicked.connect(self.save_customer)
        buttons_layout.addWidget(btn_save)

        layout.addLayout(buttons_layout)

    def save_customer(self):
        """Uložení zákazníka"""
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()

        if not first_name or not last_name:
            QMessageBox.warning(self, "Chyba", "Jméno a příjmení jsou povinné údaje.")
            return

        try:
            db.execute_query("""
                INSERT INTO customers (
                    first_name, last_name, company, phone, email,
                    address, city, postal_code, ico, dic
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                first_name,
                last_name,
                self.company_input.text().strip() or None,
                self.phone_input.text().strip() or None,
                self.email_input.text().strip() or None,
                self.address_input.text().strip() or None,
                self.city_input.text().strip() or None,
                self.postal_code_input.text().strip() or None,
                self.ico_input.text().strip() or None,
                self.dic_input.text().strip() or None
            ))

            # Získání ID nového zákazníka
            new_customer = db.fetch_one(
                "SELECT id FROM customers ORDER BY id DESC LIMIT 1"
            )

            if new_customer:
                name = f"{first_name} {last_name}"
                phone = self.phone_input.text().strip()
                if phone:
                    name += f" ({phone})"

                self.customer_data = {
                    'id': new_customer['id'],
                    'name': name
                }

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se vytvořit zákazníka:\n{e}")

    def get_customer_data(self):
        """Získání dat zákazníka"""
        return self.customer_data
