# -*- coding: utf-8 -*-
"""
Dialog pro vytvoření/editaci zakázky - ZJEDNODUŠENÝ
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLineEdit, QComboBox, QTextEdit,
    QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
import config
from database_manager import db
from datetime import datetime


class OrderFormDialog(QDialog):
    """Dialog pro vytvoření/editaci zakázky - ZJEDNODUŠENÝ"""

    def __init__(self, order_type=None, order_id=None, vehicle_id=None, parent=None):
        super().__init__(parent)
        self.order_type = order_type
        self.order_id = order_id
        self.vehicle_id = vehicle_id
        self.is_edit_mode = order_id is not None
        self.customer_id = None
        self.selected_vehicle_id = vehicle_id

        self.setWindowTitle("Upravit zakázku" if self.is_edit_mode else f"Nová {order_type}")
        self.setModal(True)
        self.setMinimumWidth(600)

        self.init_ui()

        if self.is_edit_mode:
            self.load_order_data()
        elif self.vehicle_id:
            self.load_vehicle_by_id(self.vehicle_id)

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Nadpis
        title = QLabel("📋 " + ("Upravit zakázku" if self.is_edit_mode else f"Nová {self.order_type}"))
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: {config.COLOR_PRIMARY};
            padding: 10px;
        """)
        layout.addWidget(title)

        # Formulář
        form = QFormLayout()
        form.setSpacing(10)

        # Typ zakázky
        self.combo_type = QComboBox()
        self.combo_type.addItems(config.ORDER_TYPES)
        if self.order_type:
            self.combo_type.setCurrentText(self.order_type)
        form.addRow("Typ zakázky:", self.combo_type)

        # Stav
        self.combo_status = QComboBox()
        self.combo_status.addItems(config.ORDER_STATUSES)
        if not self.is_edit_mode:
            self.combo_status.setCurrentText("V přípravě")
        form.addRow("Stav:", self.combo_status)

        # SPZ - hlavní input
        spz_layout = QHBoxLayout()
        self.input_spz = QLineEdit()
        self.input_spz.setPlaceholderText("Zadejte SPZ motorky...")
        self.input_spz.textChanged.connect(self.on_spz_changed)
        spz_layout.addWidget(self.input_spz)

        btn_search = QPushButton("🔍 Vyhledat")
        btn_search.clicked.connect(self.search_vehicle)
        btn_search.setStyleSheet(f"background-color: {config.COLOR_SECONDARY}; padding: 8px;")
        spz_layout.addWidget(btn_search)

        form.addRow("SPZ motorky *:", spz_layout)

        # Info o motorce (read-only)
        self.lbl_vehicle_info = QLabel("-- Zadejte SPZ --")
        self.lbl_vehicle_info.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
        """)
        form.addRow("Motorka:", self.lbl_vehicle_info)

        # Info o zákazníkovi (read-only)
        self.lbl_customer_info = QLabel("-- Načte se automaticky --")
        self.lbl_customer_info.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
        """)
        form.addRow("Zákazník:", self.lbl_customer_info)

        # Poznámka
        self.text_note = QTextEdit()
        self.text_note.setMaximumHeight(100)
        self.text_note.setPlaceholderText("Poznámka k zakázce...")
        form.addRow("Poznámka:", self.text_note)

        layout.addLayout(form)

        # Info text
        info = QLabel("ℹ️ Datum vytvoření a dokončení se zadává až při tvorbě zakázkového listu")
        info.setStyleSheet("color: #7f8c8d; font-size: 11px; padding: 10px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Tlačítka
        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setStyleSheet(self.get_button_style("#95a5a6"))

        btn_save = QPushButton("Uložit")
        btn_save.clicked.connect(self.save_order)
        btn_save.setStyleSheet(self.get_button_style(config.COLOR_SUCCESS))

        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

    def get_button_style(self, color):
        """Styl pro tlačítka"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 30px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
        """

    def darken_color(self, hex_color, factor=0.2):
        """Ztmavení barvy"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = int(r * (1 - factor))
        g = int(g * (1 - factor))
        b = int(b * (1 - factor))
        return f'#{r:02x}{g:02x}{b:02x}'

    def on_spz_changed(self, text):
        """Při změně SPZ"""
        # Automaticky převeď na velká písmena
        self.input_spz.blockSignals(True)
        self.input_spz.setText(text.upper())
        self.input_spz.blockSignals(False)

    def search_vehicle(self):
        """Vyhledání motorky podle SPZ"""
        spz = self.input_spz.text().strip().upper()

        if not spz:
            QMessageBox.warning(self, "Varování", "Zadejte SPZ motorky!")
            return

        try:
            vehicle = db.execute_query(
                """SELECT v.id, v.brand, v.model, v.license_plate, v.customer_id,
                          c.first_name, c.last_name, c.phone
                   FROM vehicles v
                   LEFT JOIN customers c ON v.customer_id = c.id
                   WHERE v.license_plate = ?""",
                [spz]
            )

            if not vehicle or len(vehicle) == 0:
                # Motorka neexistuje
                reply = QMessageBox.question(
                    self,
                    "Motorka nenalezena",
                    f"Motorka s SPZ '{spz}' nebyla nalezena.\n\n"
                    "Chcete ji založit?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.create_new_vehicle(spz)
                return

            # Motorka nalezena
            vehicle = vehicle[0]
            self.selected_vehicle_id = vehicle[0]
            self.customer_id = vehicle[4]

            # Zobraz info
            vehicle_info = f"{vehicle[1]} {vehicle[2]} ({vehicle[3]})"
            self.lbl_vehicle_info.setText(vehicle_info)
            self.lbl_vehicle_info.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 4px;
                    color: #155724;
                }
            """)

            if self.customer_id:
                customer_info = f"{vehicle[5]} {vehicle[6]}"
                if vehicle[7]:
                    customer_info += f" ({vehicle[7]})"
                self.lbl_customer_info.setText(customer_info)
                self.lbl_customer_info.setStyleSheet("""
                    QLabel {
                        padding: 8px;
                        background-color: #d4edda;
                        border: 1px solid #c3e6cb;
                        border-radius: 4px;
                        color: #155724;
                    }
                """)
            else:
                self.lbl_customer_info.setText("⚠️ Motorka nemá přiřazeného zákazníka!")
                self.lbl_customer_info.setStyleSheet("""
                    QLabel {
                        padding: 8px;
                        background-color: #fff3cd;
                        border: 1px solid #ffeaa7;
                        border-radius: 4px;
                        color: #856404;
                    }
                """)

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při vyhledávání motorky:\n{str(e)}")

    def load_vehicle_by_id(self, vehicle_id):
        """Načtení motorky podle ID (když se otevírá z detailu motorky)"""
        try:
            vehicle = db.execute_query(
                """SELECT v.id, v.brand, v.model, v.license_plate, v.customer_id,
                          c.first_name, c.last_name, c.phone
                   FROM vehicles v
                   LEFT JOIN customers c ON v.customer_id = c.id
                   WHERE v.id = ?""",
                [vehicle_id]
            )

            if vehicle and len(vehicle) > 0:
                vehicle = vehicle[0]
                self.selected_vehicle_id = vehicle[0]
                self.customer_id = vehicle[4]

                # Nastav SPZ
                self.input_spz.setText(vehicle[3])

                # Zobraz info
                vehicle_info = f"{vehicle[1]} {vehicle[2]} ({vehicle[3]})"
                self.lbl_vehicle_info.setText(vehicle_info)
                self.lbl_vehicle_info.setStyleSheet("""
                    QLabel {
                        padding: 8px;
                        background-color: #d4edda;
                        border: 1px solid #c3e6cb;
                        border-radius: 4px;
                        color: #155724;
                    }
                """)

                if self.customer_id:
                    customer_info = f"{vehicle[5]} {vehicle[6]}"
                    if vehicle[7]:
                        customer_info += f" ({vehicle[7]})"
                    self.lbl_customer_info.setText(customer_info)
                    self.lbl_customer_info.setStyleSheet("""
                        QLabel {
                            padding: 8px;
                            background-color: #d4edda;
                            border: 1px solid #c3e6cb;
                            border-radius: 4px;
                            color: #155724;
                        }
                    """)

        except Exception as e:
            print(f"Chyba při načítání motorky: {e}")

    def create_new_vehicle(self, spz):
        """Vytvoření nové motorky"""
        from module_vehicles import VehicleDialog

        dialog = VehicleDialog(self)
        dialog.input_license_plate.setText(spz)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            vehicle_data = dialog.get_data()

            try:
                db.execute_query("""
                    INSERT INTO vehicles (customer_id, brand, model, license_plate, vin,
                                        year, color, engine_type, fuel_type, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    vehicle_data['customer_id'],
                    vehicle_data['brand'],
                    vehicle_data['model'],
                    vehicle_data['license_plate'],
                    vehicle_data['vin'],
                    vehicle_data['year'],
                    vehicle_data['color'],
                    vehicle_data['engine_type'],
                    vehicle_data['fuel_type'],
                    vehicle_data['notes']
                ))

                QMessageBox.information(self, "Úspěch", "Motorka byla vytvořena!")

                # Načti znovu podle SPZ
                self.search_vehicle()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se vytvořit motorku:\n{str(e)}")

    def load_order_data(self):
        """Načtení dat zakázky pro editaci"""
        try:
            order = db.execute_query(
                "SELECT order_type, status, vehicle_id, note FROM orders WHERE id = ?",
                [self.order_id]
            )

            if order and len(order) > 0:
                order = order[0]

                self.combo_type.setCurrentText(order[0])
                self.combo_status.setCurrentText(order[1])

                if order[2]:
                    self.selected_vehicle_id = order[2]
                    self.load_vehicle_by_id(order[2])

                if order[3]:
                    self.text_note.setPlainText(order[3])

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při načítání zakázky:\n{str(e)}")

    def save_order(self):
        """Uložení zakázky"""
        # Validace
        if not self.selected_vehicle_id:
            QMessageBox.warning(self, "Varování", "Vyhledejte motorku podle SPZ!")
            return

        if not self.customer_id:
            QMessageBox.warning(self, "Varování", "Motorka musí mít přiřazeného zákazníka!")
            return

        try:
            order_type = self.combo_type.currentText()
            status = self.combo_status.currentText()
            note = self.text_note.toPlainText()

            if self.is_edit_mode:
                # Aktualizace
                db.execute_query(
                    """UPDATE orders SET
                       order_type = ?, status = ?, vehicle_id = ?, note = ?
                       WHERE id = ?""",
                    [order_type, status, self.selected_vehicle_id, note, self.order_id]
                )
            else:
                # Vytvoření čísla zakázky
                order_number = self.generate_order_number()
                created_date = datetime.now().strftime("%Y-%m-%d")

                # Vložení
                db.execute_query(
                    """INSERT INTO orders
                       (order_number, order_type, status, customer_id, vehicle_id,
                        created_date, note, total_price)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 0)""",
                    [order_number, order_type, status, self.customer_id,
                     self.selected_vehicle_id, created_date, note]
                )

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při ukládání:\n{str(e)}")

    def generate_order_number(self):
        # Bezpečné generování z DB (atomické, bez kolizí)
        return db.get_next_order_number()


        # Počet zakázek v aktuálním roce
        count = db.execute_query(
            "SELECT COUNT(*) FROM orders WHERE order_number LIKE ?",
            [f"{year}%"]
        )

        next_num = count[0][0] + 1 if count and len(count) > 0 else 1
        return f"{year}{next_num:04d}"

