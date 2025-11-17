# customer_widgets.py
# -*- coding: utf-8 -*-
"""
Pomocné dialogy a komponenty pro modul zákazníků
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTextEdit, QFrame, QFormLayout,
    QMessageBox, QCompleter, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QStringListModel
from PyQt6.QtGui import QFont, QCursor
import config
from database_manager import db
import re


class CustomerSearchDialog(QDialog):
    """Dialog pro vyhledávání zákazníka"""

    customer_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_customer_id = None
        self.init_ui()
        self.load_customers()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("Vyhledat zákazníka")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Vyhledávání
        search_layout = QHBoxLayout()

        self.le_search = QLineEdit()
        self.le_search.setPlaceholderText("🔍 Hledat podle jména, telefonu, emailu, IČO...")
        self.le_search.textChanged.connect(self.filter_customers)
        search_layout.addWidget(self.le_search)

        btn_new = QPushButton("➕ Nový zákazník")
        btn_new.setObjectName("btnSuccess")
        btn_new.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_new.clicked.connect(self.create_new_customer)
        search_layout.addWidget(btn_new)

        layout.addLayout(search_layout)

        # Tabulka výsledků
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Jméno / Firma", "Telefon", "Email", "Skupina"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.doubleClicked.connect(self.select_customer)

        layout.addWidget(self.table)

        # Náhled
        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("previewFrame")
        preview_layout = QVBoxLayout(self.preview_frame)

        self.lbl_preview = QLabel("Vyberte zákazníka pro náhled")
        self.lbl_preview.setStyleSheet("color: #7f8c8d; font-style: italic;")
        preview_layout.addWidget(self.lbl_preview)

        layout.addWidget(self.preview_frame)

        # Tlačítka
        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_select = QPushButton("✓ Vybrat")
        btn_select.setObjectName("btnPrimary")
        btn_select.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_select.clicked.connect(self.select_customer)
        buttons.addWidget(btn_select)

        layout.addLayout(buttons)

        self.table.selectionModel().selectionChanged.connect(self.update_preview)

        self.set_styles()

    def load_customers(self):
        """Načtení zákazníků"""
        try:
            query = """
                SELECT
                    id,
                    CASE
                        WHEN customer_type = 'company' THEN company_name
                        ELSE first_name || ' ' || last_name
                    END as name,
                    phone,
                    email,
                    customer_group
                FROM customers
                WHERE is_active = 1
                ORDER BY name
            """

            self.all_customers = db.fetch_all(query) or []
            self.populate_table(self.all_customers)

        except Exception as e:
            print(f"Chyba při načítání zákazníků: {e}")
            self.all_customers = []

    def populate_table(self, customers):
        """Naplnění tabulky"""
        self.table.setRowCount(len(customers))

        for i, customer in enumerate(customers):
            for j, value in enumerate(customer):
                self.table.setItem(i, j, QTableWidgetItem(str(value or "")))

    def filter_customers(self):
        """Filtrování zákazníků"""
        search_text = self.le_search.text().lower()

        if not search_text:
            self.populate_table(self.all_customers)
            return

        filtered = []
        for customer in self.all_customers:
            row_text = " ".join([str(v or "").lower() for v in customer])
            if search_text in row_text:
                filtered.append(customer)

        self.populate_table(filtered)

    def update_preview(self):
        """Aktualizace náhledu"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            name = self.table.item(current_row, 1).text()
            phone = self.table.item(current_row, 2).text()
            email = self.table.item(current_row, 3).text()
            group = self.table.item(current_row, 4).text()

            self.lbl_preview.setText(
                f"<b>{name}</b><br>"
                f"📞 {phone}<br>"
                f"📧 {email}<br>"
                f"🏷️ {group}"
            )
        else:
            self.lbl_preview.setText("Vyberte zákazníka pro náhled")

    def select_customer(self):
        """Výběr zákazníka"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.selected_customer_id = int(self.table.item(current_row, 0).text())
            self.customer_selected.emit(self.selected_customer_id)
            self.accept()
        else:
            QMessageBox.warning(self, "Chyba", "Vyberte zákazníka ze seznamu")

    def create_new_customer(self):
        """Vytvoření nového zákazníka"""
        from .customer_form import CustomerFormDialog
        dialog = CustomerFormDialog(self)
        if dialog.exec():
            self.load_customers()

    def get_selected_id(self):
        """Získání ID vybraného zákazníka"""
        return self.selected_customer_id

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #f5f5f5;
            }}
            #previewFrame {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 10px;
            }}
            QTableWidget {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }}
            QHeaderView::section {{
                background-color: {config.COLOR_PRIMARY};
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }}
            QLineEdit {{
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }}
            #btnSuccess {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }}
            #btnPrimary {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton {{
                padding: 6px 12px;
                border-radius: 4px;
                border: 1px solid #ddd;
            }}
        """)


class CustomerQuickAddDialog(QDialog):
    """Dialog pro rychlé přidání zákazníka"""

    customer_created = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.created_customer_id = None
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("Rychlé přidání zákazníka")
        self.setMinimumSize(400, 350)

        layout = QVBoxLayout(self)

        info_label = QLabel("💡 Rychlé vytvoření zákazníka s minimálními údaji")
        info_label.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info_label)

        form = QFormLayout()
        form.setSpacing(10)

        self.le_first_name = QLineEdit()
        self.le_first_name.setPlaceholderText("Povinné")
        form.addRow("Jméno *:", self.le_first_name)

        self.le_last_name = QLineEdit()
        self.le_last_name.setPlaceholderText("Povinné")
        form.addRow("Příjmení *:", self.le_last_name)

        self.le_phone = QLineEdit()
        self.le_phone.setPlaceholderText("+420 xxx xxx xxx")
        form.addRow("Telefon *:", self.le_phone)

        self.le_email = QLineEdit()
        self.le_email.setPlaceholderText("email@example.com")
        form.addRow("Email:", self.le_email)

        layout.addLayout(form)
        layout.addStretch()

        # Tlačítka
        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Vytvořit")
        btn_save.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; font-weight: bold; padding: 10px 20px;")
        btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save.clicked.connect(self.create_customer)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

    def create_customer(self):
        """Vytvoření zákazníka"""
        first_name = self.le_first_name.text().strip()
        last_name = self.le_last_name.text().strip()
        phone = self.le_phone.text().strip()
        email = self.le_email.text().strip()

        # Validace
        if not first_name or not last_name:
            QMessageBox.warning(self, "Chyba", "Jméno a příjmení jsou povinné")
            return

        if not phone:
            QMessageBox.warning(self, "Chyba", "Telefon je povinný")
            return

        try:
            cursor = db.execute(
                """INSERT INTO customers
                   (customer_type, first_name, last_name, phone, email, customer_group, is_active, gdpr_consent)
                   VALUES ('personal', ?, ?, ?, ?, 'Standardní', 1, 1)""",
                (first_name, last_name, phone, email)
            )

            self.created_customer_id = cursor.lastrowid
            self.customer_created.emit(self.created_customer_id)

            QMessageBox.information(self, "Vytvořeno", f"Zákazník {first_name} {last_name} byl vytvořen")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se vytvořit zákazníka: {e}")

    def get_created_id(self):
        """Získání ID vytvořeného zákazníka"""
        return self.created_customer_id


class CustomerSelector(QComboBox):
    """ComboBox pro výběr zákazníka s autocomplete"""

    customer_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.customers_data = {}
        self.init_ui()
        self.load_customers()

    def init_ui(self):
        """Inicializace UI"""
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.setMinimumWidth(250)

        # Completer
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.setCompleter(self.completer)

        self.currentIndexChanged.connect(self.on_selection_changed)

    def load_customers(self):
        """Načtení zákazníků"""
        try:
            query = """
                SELECT
                    id,
                    CASE
                        WHEN customer_type = 'company' THEN company_name
                        ELSE first_name || ' ' || last_name
                    END as name
                FROM customers
                WHERE is_active = 1
                ORDER BY name
            """

            customers = db.fetch_all(query) or []

            self.clear()
            self.addItem("-- Vyberte zákazníka --", None)

            names = []
            for customer in customers:
                self.addItem(customer[1], customer[0])
                self.customers_data[customer[1]] = customer[0]
                names.append(customer[1])

            model = QStringListModel(names)
            self.completer.setModel(model)

        except Exception as e:
            print(f"Chyba při načítání zákazníků: {e}")

    def on_selection_changed(self, index):
        """Změna výběru"""
        if index > 0:
            customer_id = self.itemData(index)
            if customer_id:
                self.customer_selected.emit(customer_id)

    def get_selected_id(self):
        """Získání ID vybraného zákazníka"""
        return self.currentData()

    def set_customer(self, customer_id):
        """Nastavení zákazníka podle ID"""
        for i in range(self.count()):
            if self.itemData(i) == customer_id:
                self.setCurrentIndex(i)
                return


class CustomerCard(QFrame):
    """Karta zákazníka pro náhledy"""

    def __init__(self, customer_id=None, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.init_ui()
        if customer_id:
            self.load_customer()

    def init_ui(self):
        """Inicializace UI"""
        self.setObjectName("customerCard")
        self.setFixedHeight(180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)

        # Jméno
        self.lbl_name = QLabel("Zákazník")
        name_font = QFont()
        name_font.setPointSize(14)
        name_font.setBold(True)
        self.lbl_name.setFont(name_font)
        layout.addWidget(self.lbl_name)

        # Skupina badge
        self.lbl_group = QLabel("Standardní")
        self.lbl_group.setObjectName("groupBadge")
        layout.addWidget(self.lbl_group)

        # Kontakty
        self.lbl_phone = QLabel("📞 -")
        layout.addWidget(self.lbl_phone)

        self.lbl_email = QLabel("📧 -")
        layout.addWidget(self.lbl_email)

        # Statistiky
        stats_layout = QHBoxLayout()
        self.lbl_vehicles = QLabel("🏍️ 0 vozidel")
        self.lbl_orders = QLabel("📋 0 zakázek")
        stats_layout.addWidget(self.lbl_vehicles)
        stats_layout.addWidget(self.lbl_orders)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        self.set_styles()

    def load_customer(self):
        """Načtení dat zákazníka"""
        if not self.customer_id:
            return

        try:
            query = """
                SELECT
                    CASE
                        WHEN c.customer_type = 'company' THEN c.company_name
                        ELSE c.first_name || ' ' || c.last_name
                    END as name,
                    c.customer_group,
                    c.phone,
                    c.email,
                    (SELECT COUNT(*) FROM vehicles WHERE customer_id = c.id) as vehicle_count,
                    (SELECT COUNT(*) FROM orders WHERE customer_id = c.id) as order_count
                FROM customers c
                WHERE c.id = ?
            """

            customer = db.fetch_one(query, (self.customer_id,))

            if customer:
                self.lbl_name.setText(customer[0] or "Zákazník")
                self.lbl_group.setText(customer[1] or "Standardní")
                self.lbl_phone.setText(f"📞 {customer[2] or '-'}")
                self.lbl_email.setText(f"📧 {customer[3] or '-'}")
                self.lbl_vehicles.setText(f"🏍️ {customer[4]} vozidel")
                self.lbl_orders.setText(f"📋 {customer[5]} zakázek")

        except Exception as e:
            print(f"Chyba při načítání zákazníka: {e}")

    def set_customer(self, customer_id):
        """Nastavení zákazníka"""
        self.customer_id = customer_id
        self.load_customer()

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet(f"""
            #customerCard {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }}
            #groupBadge {{
                background-color: #e0e0e0;
                padding: 3px 10px;
                border-radius: 10px;
                font-size: 11px;
                max-width: 100px;
            }}
        """)


class AresLookupWidget(QFrame):
    """Widget pro vyhledání v ARES"""

    data_loaded = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setObjectName("aresWidget")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("IČO:"))

        self.le_ico = QLineEdit()
        self.le_ico.setPlaceholderText("8 číslic")
        self.le_ico.setMaxLength(8)
        self.le_ico.setFixedWidth(120)
        layout.addWidget(self.le_ico)

        btn_search = QPushButton("🔍 Načíst z ARES")
        btn_search.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_search.clicked.connect(self.lookup_ares)
        layout.addWidget(btn_search)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.lbl_status)

        layout.addStretch()

    def lookup_ares(self):
        """Vyhledání v ARES"""
        ico = self.le_ico.text().strip()

        if not ico or len(ico) != 8 or not ico.isdigit():
            QMessageBox.warning(self, "Chyba", "Zadejte platné IČO (8 číslic)")
            return

        self.lbl_status.setText("Načítání...")

        # Simulace načtení z ARES
        # V produkci by zde bylo API volání
        data = {
            "company_name": f"Firma s IČO {ico}",
            "ico": ico,
            "dic": f"CZ{ico}",
            "street": "Testovací ulice 123",
            "city": "Praha",
            "zip": "10000"
        }

        self.lbl_status.setText("✅ Načteno")
        self.data_loaded.emit(data)

        QMessageBox.information(
            self,
            "ARES",
            f"Údaje načteny z ARES:\n\n"
            f"Firma: {data['company_name']}\n"
            f"IČO: {data['ico']}\n"
            f"DIČ: {data['dic']}\n"
            f"Adresa: {data['street']}, {data['zip']} {data['city']}"
        )

    def get_ico(self):
        """Získání IČO"""
        return self.le_ico.text().strip()

    def set_ico(self, ico):
        """Nastavení IČO"""
        self.le_ico.setText(ico)


