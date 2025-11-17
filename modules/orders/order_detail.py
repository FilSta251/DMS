# -*- coding: utf-8 -*-
"""
Detail zakázky - PROFESIONÁLNÍ VERZE - OPRAVENO
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QLineEdit, QDoubleSpinBox, QComboBox, QDialog,
    QTextEdit, QTabWidget, QGroupBox, QSplitter, QScrollArea,
    QCheckBox, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
import config
from database_manager import db


class OrderDetailWindow(QMainWindow):
    """Okno s detailem zakázky - PROFESIONÁLNÍ"""

    order_updated = pyqtSignal()

    def __init__(self, order_id, parent=None):
        super().__init__(parent)
        self.order_id = order_id
        self.order_data = None
        self.customer_id = None
        self.vehicle_id = None

        self.setWindowTitle(f"Detail zakázky")
        self.setMinimumSize(1400, 800)

        self.init_ui()
        self.load_order_data()

    def init_ui(self):
        """Inicializace UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === HORNÍ LIŠTA - DECENTNÍ ===
        self.create_action_bar(main_layout)

        # === HLAVNÍ OBSAH - SPLIT VIEW ===
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Levá strana - záložky
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # Pravá strana - náhled dokumentů
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # Poměr rozdělení 70:30
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)

    def create_action_bar(self, parent_layout):
        """Horní lišta - MALÁ A KOMPAKTNÍ"""
        action_bar = QWidget()
        action_bar.setFixedHeight(45)  # ⬅️ PEVNÁ VÝŠKA
        action_bar.setStyleSheet("""
            QWidget {
                background-color: #ecf0f1;
                border-bottom: 2px solid #bdc3c7;
            }
        """)
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(10, 5, 10, 5)  # ⬅️ MENŠÍ OKRAJE
        action_layout.setSpacing(10)

        # Číslo zakázky
        self.lbl_order_number = QLabel("Zakázka č. XXX")
        self.lbl_order_number.setStyleSheet("color: #2c3e50; font-size: 13px; font-weight: bold;")
        action_layout.addWidget(self.lbl_order_number)

        # Stav
        self.lbl_status_badge = QLabel("V přípravě")
        self.lbl_status_badge.setStyleSheet("""
            background-color: #95a5a6;
            color: white;
            padding: 2px 8px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 10px;
        """)
        action_layout.addWidget(self.lbl_status_badge)

        action_layout.addStretch()

        # AKTUÁLNÍ CENA
        lbl_price_title = QLabel("Cena:")
        lbl_price_title.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        action_layout.addWidget(lbl_price_title)

        self.lbl_current_price = QLabel("0.00 Kč")
        self.lbl_current_price.setStyleSheet("""
            color: #27ae60;
            font-size: 14px;
            font-weight: bold;
            padding: 0 8px;
        """)
        action_layout.addWidget(self.lbl_current_price)

        # Tlačítko změny stavu
        btn_change_status = QPushButton("Změnit stav")
        btn_change_status.setFixedHeight(28)  # ⬅️ MENŠÍ TLAČÍTKO
        btn_change_status.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 4px 10px;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_change_status.clicked.connect(self.change_status)
        action_layout.addWidget(btn_change_status)

        # ZELENÁ FAJVKA
        btn_save_close = QPushButton("✓ Uložit")
        btn_save_close.setFixedHeight(28)  # ⬅️ MENŠÍ TLAČÍTKO
        btn_save_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                border: none;
                padding: 4px 10px;
                border-radius: 3px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: #229954;
            }}
        """)
        btn_save_close.clicked.connect(self.save_and_close)
        action_layout.addWidget(btn_save_close)

        # ČERVENÝ KŘÍŽEK
        btn_delete = QPushButton("✕ Smazat")
        btn_delete.setFixedHeight(28)  # ⬅️ MENŠÍ TLAČÍTKO
        btn_delete.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_DANGER};
                color: white;
                border: none;
                padding: 4px 10px;
                border-radius: 3px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: #c0392b;
            }}
        """)
        btn_delete.clicked.connect(self.delete_order)
        action_layout.addWidget(btn_delete)

        parent_layout.addWidget(action_bar)

    def create_left_panel(self):
        """Levý panel se záložkami"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Záložky
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

        # ZÁLOŽKA 1: Základní informace
        self.tab_basic = self.create_tab_basic_info()
        self.tabs.addTab(self.tab_basic, "📋 Základní informace")

        # ZÁLOŽKA 2: Položky
        self.tab_items = self.create_tab_items()
        self.tabs.addTab(self.tab_items, "📦 Položky zakázky")

        # ZÁLOŽKA 3: Dokumenty
        self.tab_documents = self.create_tab_documents()
        self.tabs.addTab(self.tab_documents, "📁 Dokumenty a fotky")

        layout.addWidget(self.tabs)

        return widget

    def create_tab_basic_info(self):
        """ZÁLOŽKA 1: Základní informace"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # === ZÁKAZNÍK ===
        customer_group = QGroupBox("👤 Zákazník")
        customer_layout = QFormLayout(customer_group)

        self.lbl_customer = QLabel()
        self.lbl_customer.setStyleSheet("font-weight: bold; font-size: 14px;")
        customer_layout.addRow("Jméno:", self.lbl_customer)

        self.lbl_customer_phone = QLabel()
        customer_layout.addRow("Telefon:", self.lbl_customer_phone)

        self.lbl_customer_email = QLabel()
        customer_layout.addRow("Email:", self.lbl_customer_email)

        # Tlačítko prokliku - OPRAVENO
        self.btn_goto_customer = QPushButton("→ Otevřít zákazníka")
        self.btn_goto_customer.clicked.connect(self.goto_customer)
        customer_layout.addRow("", self.btn_goto_customer)

        scroll_layout.addWidget(customer_group)

        # === MOTORKA ===
        vehicle_group = QGroupBox("🏍️ Motorka")
        vehicle_layout = QFormLayout(vehicle_group)

        self.lbl_vehicle = QLabel()
        self.lbl_vehicle.setStyleSheet("font-weight: bold; font-size: 14px;")
        vehicle_layout.addRow("Info:", self.lbl_vehicle)

        self.lbl_vehicle_vin = QLabel()
        vehicle_layout.addRow("VIN:", self.lbl_vehicle_vin)

        # Tlačítko prokliku - OPRAVENO
        self.btn_goto_vehicle = QPushButton("→ Otevřít motorku")
        self.btn_goto_vehicle.clicked.connect(self.goto_vehicle)
        vehicle_layout.addRow("", self.btn_goto_vehicle)

        scroll_layout.addWidget(vehicle_group)

        # === OBCHODNÍ PODMÍNKY ===
        business_group = QGroupBox("💰 Obchodní podmínky")
        business_layout = QFormLayout(business_group)

        self.combo_customer_group = QComboBox()
        self.combo_customer_group.addItems(["Standardní", "VIP", "Velkoobchod", "Servisní partner"])
        business_layout.addRow("Zák. skupina:", self.combo_customer_group)

        self.spin_labor_discount = QSpinBox()
        self.spin_labor_discount.setRange(0, 100)
        self.spin_labor_discount.setSuffix(" %")
        business_layout.addRow("Sleva na práci:", self.spin_labor_discount)

        self.spin_material_discount = QSpinBox()
        self.spin_material_discount.setRange(0, 100)
        self.spin_material_discount.setSuffix(" %")
        business_layout.addRow("Sleva na materiál:", self.spin_material_discount)

        scroll_layout.addWidget(business_group)

        # === POZNÁMKA ===
        note_group = QGroupBox("📝 Poznámka k zakázce")
        note_layout = QVBoxLayout(note_group)

        self.text_order_note = QTextEdit()
        self.text_order_note.setMaximumHeight(100)
        self.text_order_note.setPlaceholderText("Interní poznámka...")
        note_layout.addWidget(self.text_order_note)

        scroll_layout.addWidget(note_group)

        # === FAKTURAČNÍ ÚDAJE ===
        invoice_group = QGroupBox("🧾 Fakturační údaje")
        invoice_layout = QFormLayout(invoice_group)

        self.check_different_invoice = QCheckBox("Odlišné fakturační údaje")
        self.check_different_invoice.stateChanged.connect(self.toggle_invoice_fields)
        invoice_layout.addRow(self.check_different_invoice)

        self.input_invoice_name = QLineEdit()
        self.input_invoice_name.setEnabled(False)
        invoice_layout.addRow("Název firmy:", self.input_invoice_name)

        self.input_invoice_ico = QLineEdit()
        self.input_invoice_ico.setEnabled(False)
        invoice_layout.addRow("IČO:", self.input_invoice_ico)

        self.input_invoice_address = QLineEdit()
        self.input_invoice_address.setEnabled(False)
        invoice_layout.addRow("Adresa:", self.input_invoice_address)

        scroll_layout.addWidget(invoice_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return widget

    def create_tab_items(self):
        """ZÁLOŽKA 2: Položky"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        items_tabs = QTabWidget()

        # === MATERIÁL ===
        self.tab_materials = self.create_items_table("Materiál")
        items_tabs.addTab(self.tab_materials, "📦 Materiál")

        # === PRÁCE ===
        self.tab_labor = self.create_items_table("Práce")
        items_tabs.addTab(self.tab_labor, "🔧 Práce")

        # === CIZÍ VÝKONY ===
        self.tab_external = self.create_items_table("Cizí výkon")
        items_tabs.addTab(self.tab_external, "🏢 Cizí výkony")

        layout.addWidget(items_tabs)

        return widget

    def create_items_table(self, item_type):
        """Vytvoření tabulky pro položky"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Tlačítka
        btn_layout = QHBoxLayout()
        btn_add = QPushButton(f"+ Přidat")
        btn_add.setStyleSheet(self.get_button_style(config.COLOR_SUCCESS))
        btn_add.clicked.connect(lambda: self.add_item(item_type))

        btn_delete = QPushButton("🗑️ Smazat")
        btn_delete.setStyleSheet(self.get_button_style(config.COLOR_DANGER))
        btn_delete.clicked.connect(lambda: self.delete_item(item_type))

        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_delete)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # Tabulka
        table = QTableWidget()
        table.setObjectName(f"table_{item_type}")
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "Název", "Množství", "Jednotka", "Cena/jedn.", "Sleva %", "Cena celkem", "ID"
        ])
        table.setColumnHidden(6, True)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.horizontalHeader().setStretchLastSection(True)
        table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                font-weight: bold;
            }
        """)

        table.doubleClicked.connect(lambda: self.edit_item(item_type))

        layout.addWidget(table)

        return widget

    def create_tab_documents(self):
        """ZÁLOŽKA 3: Dokumenty"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        btn_layout = QHBoxLayout()

        btn_add_doc = QPushButton("📄 Přidat dokument")
        btn_add_doc.setStyleSheet(self.get_button_style(config.COLOR_SECONDARY))
        btn_add_doc.clicked.connect(self.import_document)

        btn_add_photo = QPushButton("📷 Přidat fotku")
        btn_add_photo.setStyleSheet(self.get_button_style(config.COLOR_SUCCESS))
        btn_add_photo.clicked.connect(self.import_photo)

        btn_layout.addWidget(btn_add_doc)
        btn_layout.addWidget(btn_add_photo)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        self.list_documents = QTableWidget()
        self.list_documents.setColumnCount(4)
        self.list_documents.setHorizontalHeaderLabels(["Název", "Typ", "Datum", "Velikost"])
        self.list_documents.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.list_documents)

        info = QLabel("ℹ️ Dokumenty budou uloženy v databázi")
        info.setStyleSheet("color: #7f8c8d; padding: 10px;")
        layout.addWidget(info)

        return widget

    def create_right_panel(self):
        """Pravý panel"""
        widget = QWidget()
        widget.setStyleSheet("background-color: #f8f9fa;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("📄 Akce")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        layout.addWidget(title)

        # === POZNÁMKY ===
        notes_group = QGroupBox("📝 Poznámky")
        notes_layout = QVBoxLayout(notes_group)

        self.lbl_vehicle_notes = QLabel("...")
        self.lbl_vehicle_notes.setWordWrap(True)
        self.lbl_vehicle_notes.setStyleSheet("padding: 5px; background: white; border-radius: 3px;")
        notes_layout.addWidget(self.lbl_vehicle_notes)

        self.lbl_customer_notes = QLabel("...")
        self.lbl_customer_notes.setWordWrap(True)
        self.lbl_customer_notes.setStyleSheet("padding: 5px; background: white; border-radius: 3px;")
        notes_layout.addWidget(self.lbl_customer_notes)

        layout.addWidget(notes_group)

        # === TLAČÍTKA ===
        btn_work_order = QPushButton("📄 Zakázkový list")
        btn_work_order.setStyleSheet(self.get_button_style(config.COLOR_PRIMARY))
        btn_work_order.clicked.connect(self.open_work_order_editor)
        layout.addWidget(btn_work_order)

        btn_proforma = QPushButton("📋 Proforma")
        btn_proforma.setStyleSheet(self.get_button_style(config.COLOR_SECONDARY))
        btn_proforma.clicked.connect(self.preview_proforma)
        layout.addWidget(btn_proforma)

        btn_invoice = QPushButton("🧾 Faktura")
        btn_invoice.setStyleSheet(self.get_button_style(config.COLOR_SUCCESS))
        btn_invoice.clicked.connect(self.create_invoice)
        layout.addWidget(btn_invoice)

        layout.addStretch()

        return widget

    def get_button_style(self, color):
        """Styl tlačítek"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """

    # === NAČÍTÁNÍ DAT ===

    def load_order_data(self):
        """Načtení dat"""
        try:
            order = db.execute_query(
                """SELECT
                    o.order_number, o.status, o.note, o.total_price,
                    o.customer_id, o.vehicle_id,
                    c.first_name || ' ' || c.last_name as customer_name,
                    c.phone, c.email,
                    v.brand || ' ' || v.model || ' (' || v.license_plate || ')' as vehicle_info,
                    v.vin, v.notes as vehicle_notes,
                    c.notes as customer_notes
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                LEFT JOIN vehicles v ON o.vehicle_id = v.id
                WHERE o.id = ?""",
                [self.order_id]
            )

            if order:
                self.order_data = order[0]
                self.customer_id = order[0][4]
                self.vehicle_id = order[0][5]
                self.update_ui_with_data()
                self.load_all_items()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba:\n{str(e)}")

    def update_ui_with_data(self):
        """Aktualizace UI"""
        d = self.order_data

        self.lbl_order_number.setText(f"Zakázka č. {d[0]}")
        self.lbl_status_badge.setText(d[1])
        status_color = config.ORDER_STATUS_COLORS.get(d[1], "#95a5a6")
        self.lbl_status_badge.setStyleSheet(f"""
            background-color: {status_color};
            color: white;
            padding: 3px 10px;
            border-radius: 10px;
            font-weight: bold;
            font-size: 11px;
        """)

        self.lbl_current_price.setText(f"{d[3]:.2f} Kč" if d[3] else "0.00 Kč")

        self.lbl_customer.setText(d[6] or "---")
        self.lbl_customer_phone.setText(d[7] or "---")
        self.lbl_customer_email.setText(d[8] or "---")

        self.lbl_vehicle.setText(d[9] or "---")
        self.lbl_vehicle_vin.setText(d[10] or "---")

        self.text_order_note.setPlainText(d[2] or "")
        self.lbl_vehicle_notes.setText(f"Motorka: {d[11] or 'Žádné poznámky'}")
        self.lbl_customer_notes.setText(f"Zákazník: {d[12] or 'Žádné poznámky'}")

    def load_all_items(self):
        """Načtení položek"""
        try:
            items = db.execute_query(
                """SELECT id, item_type, name, quantity, unit, unit_price, total_price
                   FROM order_items WHERE order_id = ?
                   ORDER BY item_type, id""",
                [self.order_id]
            )

            for item in items:
                item_type = item[1]
                table = None

                if item_type == "Materiál":
                    table = self.tab_materials.findChild(QTableWidget, "table_Materiál")
                elif item_type == "Práce":
                    table = self.tab_labor.findChild(QTableWidget, "table_Práce")
                elif item_type == "Cizí výkon":
                    table = self.tab_external.findChild(QTableWidget, "table_Cizí výkon")

                if table:
                    self.add_item_to_table(table, item)

        except Exception as e:
            print(f"Chyba: {e}")

    def add_item_to_table(self, table, item):
        """Přidání do tabulky"""
        row = table.rowCount()
        table.insertRow(row)

        table.setItem(row, 0, QTableWidgetItem(item[2]))
        table.setItem(row, 1, QTableWidgetItem(str(item[3])))
        table.setItem(row, 2, QTableWidgetItem(item[4]))
        table.setItem(row, 3, QTableWidgetItem(f"{item[5]:.2f} Kč"))
        table.setItem(row, 4, QTableWidgetItem("0%"))
        table.setItem(row, 5, QTableWidgetItem(f"{item[6]:.2f} Kč"))
        table.setItem(row, 6, QTableWidgetItem(str(item[0])))

    # === AKCE ===

    def toggle_invoice_fields(self, state):
        """Zapnutí fakturačních údajů"""
        enabled = (state == Qt.CheckState.Checked.value)
        self.input_invoice_name.setEnabled(enabled)
        self.input_invoice_ico.setEnabled(enabled)
        self.input_invoice_address.setEnabled(enabled)

    def save_and_close(self):
        """Uložit a zavřít"""
        self.save_order()
        self.order_updated.emit()
        self.close()

    def save_order(self):
        """Uložení"""
        try:
            note = self.text_order_note.toPlainText()
            db.execute_query("UPDATE orders SET note = ? WHERE id = ?", [note, self.order_id])
            QMessageBox.information(self, "Uloženo", "Zakázka uložena")
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba:\n{str(e)}")

    def delete_order(self):
        """Smazání"""
        reply = QMessageBox.question(
            self,
            "Smazat?",
            f"Opravdu smazat zakázku č. {self.order_data[0]}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                db.execute_query("DELETE FROM order_items WHERE order_id = ?", [self.order_id])
                db.execute_query("DELETE FROM orders WHERE id = ?", [self.order_id])
                QMessageBox.information(self, "Smazáno", "Zakázka smazána")
                self.order_updated.emit()
                self.close()
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Chyba:\n{str(e)}")

    def change_status(self):
        """Změna stavu"""
        from .order_widgets import ChangeStatusDialog
        dialog = ChangeStatusDialog(self.order_id, self.order_data[1], self)
        dialog.status_changed.connect(lambda: self.load_order_data())
        dialog.exec()

    def goto_customer(self):
        """PROKLIK NA ZÁKAZNÍKA - OPRAVENO"""
        if not self.customer_id:
            QMessageBox.warning(self, "Chyba", "Zakázka nemá přiřazeného zákazníka")
            return

        try:
            from module_customers import CustomerDialog
            dialog = CustomerDialog(self.customer_id, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.information(self, "Info", f"Zákazník ID: {self.customer_id}\n(Modul zákazníků zatím není implementován)")

    def goto_vehicle(self):
        """PROKLIK NA MOTORKU - OPRAVENO"""
        if not self.vehicle_id:
            QMessageBox.warning(self, "Chyba", "Zakázka nemá přiřazené vozidlo")
            return

        try:
            from module_vehicles import VehicleDialog
            dialog = VehicleDialog(self.vehicle_id, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.information(self, "Info", f"Vozidlo ID: {self.vehicle_id}\n(Modul vozidel zatím není implementován)")

    def add_item(self, item_type):
        """Přidání položky"""
        from .order_widgets import OrderItemDialog
        dialog = OrderItemDialog(self.order_id, item_type=item_type, parent=self)
        if dialog.exec():
            self.load_order_data()

    def edit_item(self, item_type):
        """Editace"""
        table_name = f"table_{item_type}"

        if item_type == "Materiál":
            table = self.tab_materials.findChild(QTableWidget, table_name)
        elif item_type == "Práce":
            table = self.tab_labor.findChild(QTableWidget, table_name)
        elif item_type == "Cizí výkon":
            table = self.tab_external.findChild(QTableWidget, table_name)
        else:
            return

        if not table or table.currentRow() < 0:
            QMessageBox.warning(self, "Varování", "Vyberte položku!")
            return

        item_id = int(table.item(table.currentRow(), 6).text())

        from .order_widgets import OrderItemDialog
        dialog = OrderItemDialog(self.order_id, item_type=item_type, item_id=item_id, parent=self)
        if dialog.exec():
            self.load_order_data()

    def delete_item(self, item_type):
        """Smazání"""
        table_name = f"table_{item_type}"

        if item_type == "Materiál":
            table = self.tab_materials.findChild(QTableWidget, table_name)
        elif item_type == "Práce":
            table = self.tab_labor.findChild(QTableWidget, table_name)
        elif item_type == "Cizí výkon":
            table = self.tab_external.findChild(QTableWidget, table_name)
        else:
            return

        if not table or table.currentRow() < 0:
            QMessageBox.warning(self, "Varování", "Vyberte položku!")
            return

        item_name = table.item(table.currentRow(), 0).text()
        item_id = int(table.item(table.currentRow(), 6).text())

        reply = QMessageBox.question(
            self,
            "Smazat?",
            f"Opravdu smazat '{item_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                db.execute_query("DELETE FROM order_items WHERE id = ?", [item_id])
                self.load_order_data()
                self.order_updated.emit()
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Chyba:\n{str(e)}")

    def import_document(self):
        """Import dokumentu"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Vyberte dokument", "", "Dokumenty (*.pdf *.doc *.docx *.xls *.xlsx)")
        if file_path:
            QMessageBox.information(self, "Info", f"Dokument '{file_path}' bude uložen")

    def import_photo(self):
        """Import fotky"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Vyberte fotku", "", "Obrázky (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            QMessageBox.information(self, "Info", f"Fotka '{file_path}' bude uložena")

    def open_work_order_editor(self):
        """EDITOR ZAKÁZKOVÉHO LISTU - NOVÝ"""
        from .order_work_order_editor import WorkOrderEditorDialog
        dialog = WorkOrderEditorDialog(self.order_id, self)
        dialog.exec()

    def preview_proforma(self):
        """NÁHLED PROFORMY - OPRAVENO"""
        from .order_preview import ProformaPreviewDialog
        dialog = ProformaPreviewDialog(self.order_id, self)
        dialog.exec()

    def create_invoice(self):
        """Faktura"""
        from .order_export import exporter
        exporter.export_invoice(self.order_id, self)
