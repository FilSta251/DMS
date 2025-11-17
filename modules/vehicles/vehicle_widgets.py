# -*- coding: utf-8 -*-
"""
Pomocné widgety a dialogy pro modul vozidel
Používané z jiných modulů (zakázky, zákazníci, kalendář)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QDialog, QFormLayout, QLineEdit,
    QComboBox, QSpinBox, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame, QCompleter, QDateEdit, QTextEdit,
    QGroupBox
)
from PyQt6.QtCore import Qt, QDate, QStringListModel, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QBrush, QPixmap
from datetime import datetime, date, timedelta
from pathlib import Path
import config
from database_manager import db


class VehicleDialog(QDialog):
    """Jednoduchý dialog pro rychlou editaci vozidla"""

    def __init__(self, parent=None, vehicle_id=None):
        super().__init__(parent)
        self.vehicle_id = vehicle_id
        self.init_ui()

        if vehicle_id:
            self.load_data()

    def init_ui(self):
        """Inicializace UI"""
        if self.vehicle_id:
            self.setWindowTitle("✏️ Rychlá editace vozidla")
        else:
            self.setWindowTitle("➕ Rychlé přidání vozidla")

        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # SPZ
        self.spz_input = QLineEdit()
        self.spz_input.setPlaceholderText("1A2 3456")
        form_layout.addRow("SPZ *:", self.spz_input)

        # Značka
        self.brand_input = QComboBox()
        self.brand_input.setEditable(True)
        self.brand_input.addItems([
            "", "Honda", "Yamaha", "Suzuki", "Kawasaki", "BMW",
            "Harley-Davidson", "Ducati", "KTM", "Triumph"
        ])
        form_layout.addRow("Značka *:", self.brand_input)

        # Model
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("např. CB500X")
        form_layout.addRow("Model *:", self.model_input)

        # Rok
        self.year_input = QSpinBox()
        self.year_input.setRange(1900, datetime.now().year + 1)
        self.year_input.setValue(datetime.now().year)
        form_layout.addRow("Rok výroby:", self.year_input)

        # Zákazník
        customer_layout = QHBoxLayout()
        self.customer_label = QLabel("Nevybrán")
        self.customer_label.setStyleSheet("padding: 5px; background-color: #ecf0f1; border-radius: 3px;")
        customer_layout.addWidget(self.customer_label)

        btn_select = QPushButton("🔍")
        btn_select.setFixedWidth(40)
        btn_select.clicked.connect(self.select_customer)
        customer_layout.addWidget(btn_select)

        form_layout.addRow("Zákazník:", customer_layout)

        layout.addLayout(form_layout)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Uložit")
        btn_save.setStyleSheet(f"background-color: {config.COLOR_SUCCESS};")
        btn_save.clicked.connect(self.save)
        buttons_layout.addWidget(btn_save)

        layout.addLayout(buttons_layout)

        self.selected_customer_id = None

    def load_data(self):
        """Načtení dat vozidla"""
        try:
            vehicle = db.fetch_one("""
                SELECT v.*, c.first_name || ' ' || c.last_name as customer_name
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

                if vehicle['customer_id']:
                    self.selected_customer_id = vehicle['customer_id']
                    self.customer_label.setText(vehicle['customer_name'] or 'Neznámý')
                    self.customer_label.setStyleSheet("padding: 5px; background-color: #d5f5e3; border-radius: 3px; color: #27ae60;")
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst data:\n{e}")

    def select_customer(self):
        """Výběr zákazníka"""
        dialog = VehicleSearchDialog(self, search_type='customer')
        if dialog.exec():
            customer = dialog.get_selected()
            if customer:
                self.selected_customer_id = customer['id']
                self.customer_label.setText(customer['name'])
                self.customer_label.setStyleSheet("padding: 5px; background-color: #d5f5e3; border-radius: 3px; color: #27ae60;")

    def save(self):
        """Uložení vozidla"""
        spz = self.spz_input.text().strip().upper()
        brand = self.brand_input.currentText().strip()
        model = self.model_input.text().strip()

        if not spz or not brand or not model:
            QMessageBox.warning(self, "Chyba", "SPZ, značka a model jsou povinné údaje.")
            return

        try:
            if self.vehicle_id:
                db.execute_query("""
                    UPDATE vehicles SET
                        license_plate = ?, brand = ?, model = ?, year = ?, customer_id = ?
                    WHERE id = ?
                """, (spz, brand, model, self.year_input.value(), self.selected_customer_id, self.vehicle_id))
            else:
                db.execute_query("""
                    INSERT INTO vehicles (license_plate, brand, model, year, customer_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (spz, brand, model, self.year_input.value(), self.selected_customer_id))

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit:\n{e}")


class VehicleSearchDialog(QDialog):
    """Dialog pro vyhledávání vozidla nebo zákazníka"""

    def __init__(self, parent=None, search_type='vehicle'):
        super().__init__(parent)
        self.search_type = search_type
        self.selected_item = None
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Inicializace UI"""
        if self.search_type == 'vehicle':
            self.setWindowTitle("🔍 Vyhledat vozidlo")
        else:
            self.setWindowTitle("🔍 Vyhledat zákazníka")

        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Vyhledávání
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍")
        self.search_input = QLineEdit()

        if self.search_type == 'vehicle':
            self.search_input.setPlaceholderText("SPZ, VIN, značka, model, zákazník...")
        else:
            self.search_input.setPlaceholderText("Jméno, telefon, email, IČO...")

        self.search_input.textChanged.connect(self.filter_data)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Tabulka
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.select_and_close)

        if self.search_type == 'vehicle':
            self.table.setColumnCount(6)
            self.table.setHorizontalHeaderLabels(["ID", "SPZ", "Značka", "Model", "Rok", "Zákazník"])
            self.table.setColumnHidden(0, True)

            header = self.table.horizontalHeader()
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        else:
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["ID", "Jméno", "Příjmení", "Telefon", "Email"])
            self.table.setColumnHidden(0, True)

            header = self.table.horizontalHeader()
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

        # Náhled
        self.preview_label = QLabel("Vyberte položku pro náhled")
        self.preview_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
                color: #7f8c8d;
            }
        """)
        self.table.itemSelectionChanged.connect(self.update_preview)
        layout.addWidget(self.preview_label)

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

    def load_data(self):
        """Načtení dat"""
        try:
            if self.search_type == 'vehicle':
                data = db.fetch_all("""
                    SELECT v.id, v.license_plate, v.brand, v.model, v.year,
                           c.first_name || ' ' || c.last_name as customer_name
                    FROM vehicles v
                    LEFT JOIN customers c ON v.customer_id = c.id
                    ORDER BY v.license_plate
                """)

                self.table.setRowCount(0)
                for item in data:
                    row = self.table.rowCount()
                    self.table.insertRow(row)

                    self.table.setItem(row, 0, QTableWidgetItem(str(item['id'])))
                    self.table.setItem(row, 1, QTableWidgetItem(item['license_plate'] or ''))
                    self.table.setItem(row, 2, QTableWidgetItem(item['brand'] or ''))
                    self.table.setItem(row, 3, QTableWidgetItem(item['model'] or ''))
                    self.table.setItem(row, 4, QTableWidgetItem(str(item['year']) if item['year'] else ''))
                    self.table.setItem(row, 5, QTableWidgetItem(item['customer_name'] or 'Bez zákazníka'))
            else:
                data = db.fetch_all("""
                    SELECT id, first_name, last_name, phone, email
                    FROM customers
                    ORDER BY last_name, first_name
                """)

                self.table.setRowCount(0)
                for item in data:
                    row = self.table.rowCount()
                    self.table.insertRow(row)

                    self.table.setItem(row, 0, QTableWidgetItem(str(item['id'])))
                    self.table.setItem(row, 1, QTableWidgetItem(item['first_name'] or ''))
                    self.table.setItem(row, 2, QTableWidgetItem(item['last_name'] or ''))
                    self.table.setItem(row, 3, QTableWidgetItem(item['phone'] or ''))
                    self.table.setItem(row, 4, QTableWidgetItem(item['email'] or ''))
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst data:\n{e}")

    def filter_data(self):
        """Filtrování dat"""
        search_text = self.search_input.text().lower()

        for row in range(self.table.rowCount()):
            show_row = False
            for col in range(1, self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    show_row = True
                    break
            self.table.setRowHidden(row, not show_row)

    def update_preview(self):
        """Aktualizace náhledu"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return

        if self.search_type == 'vehicle':
            spz = self.table.item(selected_row, 1).text()
            brand = self.table.item(selected_row, 2).text()
            model = self.table.item(selected_row, 3).text()
            year = self.table.item(selected_row, 4).text()
            customer = self.table.item(selected_row, 5).text()

            self.preview_label.setText(
                f"<b>🏍️ {spz}</b><br>"
                f"{brand} {model} ({year})<br>"
                f"Zákazník: {customer}"
            )
        else:
            first = self.table.item(selected_row, 1).text()
            last = self.table.item(selected_row, 2).text()
            phone = self.table.item(selected_row, 3).text()
            email = self.table.item(selected_row, 4).text()

            self.preview_label.setText(
                f"<b>👤 {first} {last}</b><br>"
                f"Tel: {phone}<br>"
                f"Email: {email}"
            )

        self.preview_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #d5f5e3;
                border-radius: 5px;
                color: #27ae60;
            }
        """)

    def select_and_close(self):
        """Výběr a zavření"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Upozornění", "Vyberte položku.")
            return

        item_id = int(self.table.item(selected_row, 0).text())

        if self.search_type == 'vehicle':
            spz = self.table.item(selected_row, 1).text()
            brand = self.table.item(selected_row, 2).text()
            model = self.table.item(selected_row, 3).text()

            self.selected_item = {
                'id': item_id,
                'name': f"{spz} - {brand} {model}"
            }
        else:
            first = self.table.item(selected_row, 1).text()
            last = self.table.item(selected_row, 2).text()
            phone = self.table.item(selected_row, 3).text()

            name = f"{first} {last}"
            if phone:
                name += f" ({phone})"

            self.selected_item = {
                'id': item_id,
                'name': name
            }

        self.accept()

    def get_selected(self):
        """Získání vybraného"""
        return self.selected_item


class VehicleQuickAddDialog(QDialog):
    """Dialog pro rychlé přidání vozidla s minimálními údaji"""

    vehicle_created = pyqtSignal(int)  # Signal s ID nového vozidla

    def __init__(self, parent=None, customer_id=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.new_vehicle_id = None
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("➕ Rychlé přidání vozidla")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        info_label = QLabel("Zadejte základní údaje o vozidle:")
        info_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(info_label)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # SPZ
        self.spz_input = QLineEdit()
        self.spz_input.setPlaceholderText("Povinné")
        form_layout.addRow("SPZ *:", self.spz_input)

        # Značka
        self.brand_input = QComboBox()
        self.brand_input.setEditable(True)
        self.brand_input.addItems([
            "Honda", "Yamaha", "Suzuki", "Kawasaki", "BMW",
            "Harley-Davidson", "Ducati", "KTM", "Triumph"
        ])
        form_layout.addRow("Značka *:", self.brand_input)

        # Model
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Povinné")
        form_layout.addRow("Model *:", self.model_input)

        # Zákazník (pokud není předvybrán)
        if not self.customer_id:
            customer_layout = QHBoxLayout()
            self.customer_label = QLabel("Nevybrán")
            customer_layout.addWidget(self.customer_label)

            btn_select = QPushButton("🔍 Vybrat")
            btn_select.clicked.connect(self.select_customer)
            customer_layout.addWidget(btn_select)

            form_layout.addRow("Zákazník:", customer_layout)

        layout.addLayout(form_layout)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Vytvořit")
        btn_save.setStyleSheet(f"background-color: {config.COLOR_SUCCESS};")
        btn_save.clicked.connect(self.save)
        buttons_layout.addWidget(btn_save)

        layout.addLayout(buttons_layout)

    def select_customer(self):
        """Výběr zákazníka"""
        dialog = VehicleSearchDialog(self, search_type='customer')
        if dialog.exec():
            customer = dialog.get_selected()
            if customer:
                self.customer_id = customer['id']
                self.customer_label.setText(customer['name'])

    def save(self):
        """Uložení vozidla"""
        spz = self.spz_input.text().strip().upper()
        brand = self.brand_input.currentText().strip()
        model = self.model_input.text().strip()

        if not spz or not brand or not model:
            QMessageBox.warning(self, "Chyba", "SPZ, značka a model jsou povinné.")
            return

        try:
            db.execute_query("""
                INSERT INTO vehicles (license_plate, brand, model, customer_id)
                VALUES (?, ?, ?, ?)
            """, (spz, brand, model, self.customer_id))

            # Získání ID
            result = db.fetch_one("SELECT id FROM vehicles ORDER BY id DESC LIMIT 1")
            if result:
                self.new_vehicle_id = result['id']
                self.vehicle_created.emit(self.new_vehicle_id)

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se vytvořit vozidlo:\n{e}")

    def get_vehicle_id(self):
        """Získání ID nového vozidla"""
        return self.new_vehicle_id


class STKReminderWidget(QFrame):
    """Widget pro zobrazení stavu STK"""

    def __init__(self, vehicle_id, parent=None):
        super().__init__(parent)
        self.vehicle_id = vehicle_id
        self.init_ui()
        self.load_stk_status()

    def init_ui(self):
        """Inicializace UI"""
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Titulek
        title = QLabel("🔧 Stav STK")
        title_font = QFont()
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Stav
        self.status_label = QLabel("Načítání...")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Zbývající dny
        self.days_label = QLabel("")
        self.days_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.days_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.days_label)

        # Tlačítko
        self.btn_schedule = QPushButton("🗓️ Naplánovat STK")
        self.btn_schedule.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                padding: 8px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: #2980b9;
            }}
        """)
        self.btn_schedule.clicked.connect(self.schedule_stk)
        layout.addWidget(self.btn_schedule)

    def load_stk_status(self):
        """Načtení stavu STK"""
        try:
            vehicle = db.fetch_one(
                "SELECT stk_valid_until FROM vehicles WHERE id = ?",
                (self.vehicle_id,)
            )

            if vehicle and vehicle['stk_valid_until']:
                stk_date = datetime.strptime(str(vehicle['stk_valid_until']), "%Y-%m-%d").date()
                today = date.today()
                days_left = (stk_date - today).days

                if days_left < 0:
                    self.status_label.setText(f"⚠️ NEPLATNÁ - vypršela {stk_date.strftime('%d.%m.%Y')}")
                    self.days_label.setText(f"{abs(days_left)} dní po expiraci")
                    self.days_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #e74c3c;")
                    self.setStyleSheet("""
                        QFrame {
                            background-color: #fadbd8;
                            border: 2px solid #e74c3c;
                            border-radius: 8px;
                            padding: 10px;
                        }
                    """)
                elif days_left <= 30:
                    self.status_label.setText(f"⚠️ Expiruje brzy - {stk_date.strftime('%d.%m.%Y')}")
                    self.days_label.setText(f"{days_left} dní do expirace")
                    self.days_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #f39c12;")
                    self.setStyleSheet("""
                        QFrame {
                            background-color: #fef9e7;
                            border: 2px solid #f39c12;
                            border-radius: 8px;
                            padding: 10px;
                        }
                    """)
                else:
                    self.status_label.setText(f"✅ Platná do {stk_date.strftime('%d.%m.%Y')}")
                    self.days_label.setText(f"{days_left} dní")
                    self.days_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60;")
                    self.setStyleSheet("""
                        QFrame {
                            background-color: #d5f5e3;
                            border: 2px solid #27ae60;
                            border-radius: 8px;
                            padding: 10px;
                        }
                    """)
            else:
                self.status_label.setText("ℹ️ STK není zadána")
                self.days_label.setText("-")
                self.days_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #95a5a6;")
        except Exception as e:
            self.status_label.setText(f"Chyba: {e}")

    def schedule_stk(self):
        """Naplánování STK"""
        QMessageBox.information(
            self,
            "Naplánovat STK",
            "Funkce bude implementována v modulu Kalendář."
        )


class VehicleCard(QFrame):
    """Karta vozidla pro náhledy"""

    clicked = pyqtSignal(int)  # Signal s ID vozidla

    def __init__(self, vehicle_id, parent=None):
        super().__init__(parent)
        self.vehicle_id = vehicle_id
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Inicializace UI"""
        self.setFixedSize(250, 180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 10px;
                padding: 10px;
            }
            QFrame:hover {
                border-color: #3498db;
                background-color: #ecf0f1;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Fotka
        self.photo_label = QLabel()
        self.photo_label.setFixedSize(80, 60)
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_label.setStyleSheet("""
            QLabel {
                background-color: #ecf0f1;
                border-radius: 5px;
            }
        """)
        self.photo_label.setText("🏍️")
        layout.addWidget(self.photo_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # SPZ
        self.spz_label = QLabel()
        spz_font = QFont()
        spz_font.setPointSize(16)
        spz_font.setBold(True)
        self.spz_label.setFont(spz_font)
        self.spz_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.spz_label)

        # Značka/Model
        self.brand_model_label = QLabel()
        self.brand_model_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.brand_model_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.brand_model_label)

        # Zákazník
        self.customer_label = QLabel()
        self.customer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.customer_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.customer_label)

        # STK badge
        self.stk_badge = QLabel()
        self.stk_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stk_badge.setStyleSheet("""
            QLabel {
                padding: 3px 8px;
                border-radius: 10px;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.stk_badge)

    def load_data(self):
        """Načtení dat"""
        try:
            vehicle = db.fetch_one("""
                SELECT v.*, c.first_name || ' ' || c.last_name as customer_name
                FROM vehicles v
                LEFT JOIN customers c ON v.customer_id = c.id
                WHERE v.id = ?
            """, (self.vehicle_id,))

            if vehicle:
                self.spz_label.setText(vehicle['license_plate'] or '')
                self.brand_model_label.setText(f"{vehicle['brand']} {vehicle['model']}")
                self.customer_label.setText(vehicle['customer_name'] or 'Bez zákazníka')

                # STK badge
                if vehicle['stk_valid_until']:
                    stk_date = datetime.strptime(str(vehicle['stk_valid_until']), "%Y-%m-%d").date()
                    today = date.today()
                    days_left = (stk_date - today).days

                    if days_left < 0:
                        self.stk_badge.setText("❌ NEPLATNÁ STK")
                        self.stk_badge.setStyleSheet("""
                            QLabel {
                                padding: 3px 8px;
                                border-radius: 10px;
                                font-size: 10px;
                                font-weight: bold;
                                background-color: #e74c3c;
                                color: white;
                            }
                        """)
                    elif days_left <= 30:
                        self.stk_badge.setText(f"⚠️ STK za {days_left} dní")
                        self.stk_badge.setStyleSheet("""
                            QLabel {
                                padding: 3px 8px;
                                border-radius: 10px;
                                font-size: 10px;
                                font-weight: bold;
                                background-color: #f39c12;
                                color: white;
                            }
                        """)
                    else:
                        self.stk_badge.setText("✅ STK v pořádku")
                        self.stk_badge.setStyleSheet("""
                            QLabel {
                                padding: 3px 8px;
                                border-radius: 10px;
                                font-size: 10px;
                                font-weight: bold;
                                background-color: #27ae60;
                                color: white;
                            }
                        """)
                else:
                    self.stk_badge.setText("ℹ️ STK neuvedena")
                    self.stk_badge.setStyleSheet("""
                        QLabel {
                            padding: 3px 8px;
                            border-radius: 10px;
                            font-size: 10px;
                            font-weight: bold;
                            background-color: #95a5a6;
                            color: white;
                        }
                    """)

                # Načtení hlavní fotky pokud existuje
                main_photo = db.fetch_one("""
                    SELECT thumbnail_path FROM vehicle_photos
                    WHERE vehicle_id = ? AND is_main = 1
                    LIMIT 1
                """, (self.vehicle_id,))

                if main_photo and main_photo['thumbnail_path']:
                    path = Path(main_photo['thumbnail_path'])
                    if path.exists():
                        pixmap = QPixmap(str(path))
                        if not pixmap.isNull():
                            scaled = pixmap.scaled(80, 60, Qt.AspectRatioMode.KeepAspectRatio)
                            self.photo_label.setPixmap(scaled)
        except Exception as e:
            print(f"Chyba při načítání karty vozidla: {e}")

    def mousePressEvent(self, event):
        """Kliknutí na kartu"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.vehicle_id)


class VehicleSelector(QComboBox):
    """ComboBox pro výběr vozidla s autocomplete"""

    vehicle_selected = pyqtSignal(int)  # Signal s ID vozidla

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vehicles_data = []
        self.init_ui()
        self.load_vehicles()

    def init_ui(self):
        """Inicializace UI"""
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.setMinimumWidth(300)
        self.setPlaceholderText("Vyberte nebo vyhledejte vozidlo...")

        # Autocomplete
        self.completer = QCompleter(self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.setCompleter(self.completer)

        self.currentIndexChanged.connect(self.on_selection_changed)

    def load_vehicles(self):
        """Načtení vozidel"""
        try:
            self.vehicles_data = db.fetch_all("""
                SELECT v.id, v.license_plate, v.brand, v.model,
                       c.first_name || ' ' || c.last_name as customer_name
                FROM vehicles v
                LEFT JOIN customers c ON v.customer_id = c.id
                ORDER BY v.license_plate
            """)

            self.clear()
            self.addItem("", None)  # Prázdná položka

            items = []
            for v in self.vehicles_data:
                text = f"{v['license_plate']} - {v['brand']} {v['model']}"
                if v['customer_name']:
                    text += f" ({v['customer_name']})"
                items.append(text)
                self.addItem(text, v['id'])

            # Nastavení completeru
            model = QStringListModel(items)
            self.completer.setModel(model)

        except Exception as e:
            print(f"Chyba při načítání vozidel: {e}")

    def on_selection_changed(self, index):
        """Změna výběru"""
        vehicle_id = self.currentData()
        if vehicle_id:
            self.vehicle_selected.emit(vehicle_id)

    def get_selected_id(self):
        """Získání ID vybraného vozidla"""
        return self.currentData()

    def set_vehicle(self, vehicle_id):
        """Nastavení vozidla podle ID"""
        for i in range(self.count()):
            if self.itemData(i) == vehicle_id:
                self.setCurrentIndex(i)
                break


class MileageUpdateDialog(QDialog):
    """Dialog pro aktualizaci stavu km"""

    def __init__(self, vehicle_id, parent=None):
        super().__init__(parent)
        self.vehicle_id = vehicle_id
        self.current_mileage = 0
        self.init_ui()
        self.load_current_mileage()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("🔄 Aktualizace stavu km")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Info
        info_label = QLabel("Aktualizace stavu tachometru vozidla")
        info_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(info_label)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Aktuální stav
        self.current_label = QLabel("Načítání...")
        self.current_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #ecf0f1;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        form_layout.addRow("Poslední stav:", self.current_label)

        # Nový stav
        self.new_mileage = QSpinBox()
        self.new_mileage.setRange(0, 9999999)
        self.new_mileage.setSuffix(" km")
        form_layout.addRow("Nový stav *:", self.new_mileage)

        # Datum
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("dd.MM.yyyy")
        form_layout.addRow("Datum aktualizace:", self.date_input)

        # Poznámka
        self.note_input = QTextEdit()
        self.note_input.setPlaceholderText("Poznámka k aktualizaci...")
        self.note_input.setMaximumHeight(60)
        form_layout.addRow("Poznámka:", self.note_input)

        layout.addLayout(form_layout)

        # Varování
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        self.warning_label.hide()
        layout.addWidget(self.warning_label)

        self.new_mileage.valueChanged.connect(self.validate_mileage)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Uložit")
        btn_save.setStyleSheet(f"background-color: {config.COLOR_SUCCESS};")
        btn_save.clicked.connect(self.save)
        buttons_layout.addWidget(btn_save)

        layout.addLayout(buttons_layout)

    def load_current_mileage(self):
        """Načtení aktuálního stavu km"""
        try:
            vehicle = db.fetch_one(
                "SELECT mileage, license_plate FROM vehicles WHERE id = ?",
                (self.vehicle_id,)
            )

            if vehicle:
                self.current_mileage = vehicle['mileage'] or 0
                self.current_label.setText(f"{self.current_mileage:,} km".replace(",", " "))
                self.new_mileage.setValue(self.current_mileage)
                self.setWindowTitle(f"🔄 Aktualizace km - {vehicle['license_plate']}")
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst data:\n{e}")

    def validate_mileage(self):
        """Validace nového stavu km"""
        new_value = self.new_mileage.value()

        if new_value < self.current_mileage:
            self.warning_label.setText(
                f"⚠️ Nový stav ({new_value:,} km) je menší než aktuální ({self.current_mileage:,} km)!"
            )
            self.warning_label.show()
        else:
            self.warning_label.hide()

    def save(self):
        """Uložení nového stavu"""
        new_value = self.new_mileage.value()

        if new_value < self.current_mileage:
            reply = QMessageBox.question(
                self,
                "Varování",
                f"Nový stav km ({new_value:,}) je menší než aktuální ({self.current_mileage:,}).\n\n"
                "Opravdu chcete pokračovat?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        try:
            # Aktualizace vozidla
            db.execute_query(
                "UPDATE vehicles SET mileage = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_value, self.vehicle_id)
            )

            # Záznam do historie (pokud existuje tabulka)
            try:
                db.execute_query("""
                    INSERT INTO mileage_history (vehicle_id, mileage, recorded_date, note)
                    VALUES (?, ?, ?, ?)
                """, (
                    self.vehicle_id,
                    new_value,
                    self.date_input.date().toString("yyyy-MM-dd"),
                    self.note_input.toPlainText().strip()
                ))
            except:
                pass  # Tabulka neexistuje

            self.accept()
            QMessageBox.information(
                self,
                "Úspěch",
                f"Stav km byl aktualizován na {new_value:,} km.".replace(",", " ")
            )

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit:\n{e}")
