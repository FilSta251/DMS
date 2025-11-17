# -*- coding: utf-8 -*-
"""
Modul Administrativa - Detail faktury (PRODUKČNÍ VERZE)
Kompletní dialog pro správu faktury se všemi záložkami
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QFrame,
                             QComboBox, QLineEdit, QDateEdit, QHeaderView,
                             QMessageBox, QDialog, QFormLayout, QTextEdit,
                             QSpinBox, QDoubleSpinBox, QFileDialog, QCheckBox,
                             QGroupBox, QTabWidget, QScrollArea, QTreeWidget,
                             QTreeWidgetItem, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QDateTime
from PyQt6.QtGui import QFont, QColor, QIcon
from datetime import datetime, timedelta, date
from pathlib import Path
import config
from database_manager import db


class InvoiceDetailDialog(QDialog):
    """
    Kompletní dialog pro detail a editaci faktury
    Se všemi záložkami a funkcemi
    """

    invoice_saved = pyqtSignal()

    def __init__(self, parent, invoice_id=None, invoice_type="issued"):
        super().__init__(parent)
        self.invoice_id = invoice_id
        self.invoice_type = invoice_type
        self.is_edit = invoice_id is not None
        self.items_data = []
        self.payments_data = []
        self.documents_data = []
        self.history_data = []
        self.original_invoice = None

        self.setWindowTitle("Detail faktury" if self.is_edit else "Nová faktura")
        self.setMinimumSize(1000, 800)

        self.init_ui()

        if self.is_edit:
            self.load_invoice()
        else:
            self.init_new_invoice()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Hlavička s číslem faktury
        self.create_header(layout)

        # Záložky
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)

        # Záložka: Základní údaje
        self.tab_basic = self.create_basic_tab()
        self.tabs.addTab(self.tab_basic, "📋 Základní údaje")

        # Záložka: Položky faktury
        self.tab_items = self.create_items_tab()
        self.tabs.addTab(self.tab_items, "📦 Položky faktury")

        # Záložka: Platby
        self.tab_payments = self.create_payments_tab()
        self.tabs.addTab(self.tab_payments, "💳 Platby")

        # Záložka: Dokumenty
        self.tab_documents = self.create_documents_tab()
        self.tabs.addTab(self.tab_documents, "📎 Dokumenty")

        # Záložka: Historie
        self.tab_history = self.create_history_tab()
        self.tabs.addTab(self.tab_history, "📜 Historie")

        layout.addWidget(self.tabs)

        # Tlačítka
        self.create_buttons(layout)

    def create_header(self, parent_layout):
        """Vytvoření hlavičky"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)

        # Číslo faktury
        self.header_number = QLabel("Nová faktura")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        self.header_number.setFont(header_font)
        header_layout.addWidget(self.header_number)

        header_layout.addStretch()

        # Status
        self.header_status = QLabel("")
        status_font = QFont()
        status_font.setPointSize(12)
        status_font.setBold(True)
        self.header_status.setFont(status_font)
        header_layout.addWidget(self.header_status)

        parent_layout.addWidget(header_frame)

    def create_basic_tab(self):
        """Záložka: Základní údaje"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout(widget)

        # Formulář
        form_layout = QFormLayout()

        # Číslo faktury
        number_layout = QHBoxLayout()
        self.invoice_number_input = QLineEdit()
        number_layout.addWidget(self.invoice_number_input)

        self.auto_number_checkbox = QCheckBox("Automatické číslo")
        self.auto_number_checkbox.setChecked(True)
        self.auto_number_checkbox.stateChanged.connect(self.toggle_auto_number)
        number_layout.addWidget(self.auto_number_checkbox)

        form_layout.addRow("Číslo faktury:", number_layout)

        # Typ faktury (pouze u nové)
        if not self.is_edit:
            self.invoice_type_combo = QComboBox()
            self.invoice_type_combo.addItem("Vydaná faktura", "issued")
            self.invoice_type_combo.addItem("Přijatá faktura", "received")
            self.invoice_type_combo.setCurrentIndex(0 if self.invoice_type == "issued" else 1)
            self.invoice_type_combo.currentIndexChanged.connect(self.on_type_changed)
            form_layout.addRow("Typ faktury:", self.invoice_type_combo)

        # Zákazník/Dodavatel
        customer_layout = QHBoxLayout()
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        self.customer_combo.setMinimumWidth(400)
        self.load_customers()
        customer_layout.addWidget(self.customer_combo)

        add_customer_btn = QPushButton("➕ Nový")
        add_customer_btn.setFixedWidth(80)
        add_customer_btn.clicked.connect(self.quick_add_customer)
        customer_layout.addWidget(add_customer_btn)
        customer_layout.addStretch()

        self.customer_label = QLabel("Zákazník:" if self.invoice_type == "issued" else "Dodavatel:")
        form_layout.addRow(self.customer_label, customer_layout)

        # Data
        dates_group = QGroupBox("Datumy")
        dates_layout = QFormLayout(dates_group)

        self.issue_date = QDateEdit()
        self.issue_date.setDate(QDate.currentDate())
        self.issue_date.setCalendarPopup(True)
        self.issue_date.setDisplayFormat("dd.MM.yyyy")
        self.issue_date.dateChanged.connect(self.update_due_date)
        dates_layout.addRow("Datum vystavení:", self.issue_date)

        self.due_date = QDateEdit()
        self.due_date.setDate(QDate.currentDate().addDays(14))
        self.due_date.setCalendarPopup(True)
        self.due_date.setDisplayFormat("dd.MM.yyyy")
        dates_layout.addRow("Datum splatnosti:", self.due_date)

        self.tax_date = QDateEdit()
        self.tax_date.setDate(QDate.currentDate())
        self.tax_date.setCalendarPopup(True)
        self.tax_date.setDisplayFormat("dd.MM.yyyy")
        dates_layout.addRow("Datum zdanit. plnění:", self.tax_date)

        layout.addWidget(dates_group)

        # Platební údaje
        payment_group = QGroupBox("Platební údaje")
        payment_layout = QFormLayout(payment_group)

        self.payment_method = QComboBox()
        self.payment_method.addItems([
            "Bankovní převod",
            "Hotovost",
            "Karta",
            "Dobírka",
            "Ostatní"
        ])
        payment_layout.addRow("Forma úhrady:", self.payment_method)

        self.variable_symbol = QLineEdit()
        self.variable_symbol.setPlaceholderText("Variabilní symbol")
        payment_layout.addRow("Variabilní symbol:", self.variable_symbol)

        self.constant_symbol = QLineEdit()
        self.constant_symbol.setPlaceholderText("Konstantní symbol")
        payment_layout.addRow("Konstantní symbol:", self.constant_symbol)

        self.specific_symbol = QLineEdit()
        self.specific_symbol.setPlaceholderText("Specifický symbol")
        payment_layout.addRow("Specifický symbol:", self.specific_symbol)

        layout.addWidget(payment_group)

        # Poznámka
        note_group = QGroupBox("Poznámka")
        note_layout = QVBoxLayout(note_group)
        self.note_input = QTextEdit()
        self.note_input.setMaximumHeight(100)
        self.note_input.setPlaceholderText("Interní poznámka k faktuře...")
        note_layout.addWidget(self.note_input)
        layout.addWidget(note_group)

        # Zakázka
        order_layout = QHBoxLayout()
        self.order_combo = QComboBox()
        self.order_combo.addItem("-- Bez zakázky --", None)
        self.order_combo.currentIndexChanged.connect(self.on_order_changed)
        self.load_orders()
        order_layout.addWidget(self.order_combo)

        import_from_order_btn = QPushButton("📥 Import položek ze zakázky")
        import_from_order_btn.clicked.connect(self.import_from_order)
        order_layout.addWidget(import_from_order_btn)

        form_layout.addRow("Zakázka:", order_layout)

        layout.addLayout(form_layout)
        layout.addStretch()

        return scroll

    def create_items_tab(self):
        """Záložka: Položky faktury"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Tlačítka
        buttons_layout = QHBoxLayout()

        add_item_btn = QPushButton("➕ Přidat položku")
        add_item_btn.clicked.connect(self.add_invoice_item)
        add_item_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 15px;")
        buttons_layout.addWidget(add_item_btn)

        add_from_warehouse_btn = QPushButton("📦 Ze skladu")
        add_from_warehouse_btn.clicked.connect(self.add_item_from_warehouse)
        buttons_layout.addWidget(add_from_warehouse_btn)

        edit_item_btn = QPushButton("✏️ Upravit")
        edit_item_btn.clicked.connect(self.edit_invoice_item)
        buttons_layout.addWidget(edit_item_btn)

        remove_item_btn = QPushButton("➖ Odebrat")
        remove_item_btn.clicked.connect(self.remove_invoice_item)
        remove_item_btn.setStyleSheet(f"background-color: {config.COLOR_DANGER}; color: white; padding: 8px 15px;")
        buttons_layout.addWidget(remove_item_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # Tabulka položek
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(8)
        self.items_table.setHorizontalHeaderLabels([
            "Název", "Množství", "Jednotka", "Cena bez DPH", "DPH %", "Cena s DPH", "Celkem bez DPH", "Celkem s DPH"
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.items_table.doubleClicked.connect(self.edit_invoice_item)
        layout.addWidget(self.items_table)

        # Součty
        totals_frame = QFrame()
        totals_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        totals_layout = QHBoxLayout(totals_frame)

        # Rozpis DPH
        vat_breakdown_group = QGroupBox("Rozpis DPH")
        vat_breakdown_layout = QVBoxLayout(vat_breakdown_group)
        self.vat_breakdown_label = QLabel("Žádné položky")
        self.vat_breakdown_label.setStyleSheet("font-size: 11pt;")
        vat_breakdown_layout.addWidget(self.vat_breakdown_label)
        totals_layout.addWidget(vat_breakdown_group)

        totals_layout.addStretch()

        # Celkové součty
        totals_group = QGroupBox("Celkem")
        totals_form = QFormLayout(totals_group)

        self.total_without_vat_label = QLabel("0,00 Kč")
        self.total_without_vat_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        totals_form.addRow("Celkem bez DPH:", self.total_without_vat_label)

        self.total_vat_label = QLabel("0,00 Kč")
        self.total_vat_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        totals_form.addRow("Celkem DPH:", self.total_vat_label)

        self.total_with_vat_label = QLabel("0,00 Kč")
        self.total_with_vat_label.setStyleSheet("font-weight: bold; font-size: 16pt; color: #27ae60;")
        totals_form.addRow("Celkem s DPH:", self.total_with_vat_label)

        totals_layout.addWidget(totals_group)

        layout.addWidget(totals_frame)

        return widget

    def create_payments_tab(self):
        """Záložka: Platby"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Přehled
        overview_frame = QFrame()
        overview_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        overview_layout = QHBoxLayout(overview_frame)

        self.payment_total_label = QLabel("Celková částka: <b>0,00 Kč</b>")
        overview_layout.addWidget(self.payment_total_label)

        self.payment_paid_label = QLabel("Zaplaceno: <b>0,00 Kč</b>")
        overview_layout.addWidget(self.payment_paid_label)

        self.payment_remaining_label = QLabel("Zbývá uhradit: <b>0,00 Kč</b>")
        self.payment_remaining_label.setStyleSheet("color: #e74c3c;")
        overview_layout.addWidget(self.payment_remaining_label)

        overview_layout.addStretch()

        layout.addWidget(overview_frame)

        # Tlačítka
        buttons_layout = QHBoxLayout()

        add_payment_btn = QPushButton("💳 Přidat platbu")
        add_payment_btn.clicked.connect(self.add_payment)
        add_payment_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 15px;")
        buttons_layout.addWidget(add_payment_btn)

        remove_payment_btn = QPushButton("➖ Odebrat platbu")
        remove_payment_btn.clicked.connect(self.remove_payment)
        buttons_layout.addWidget(remove_payment_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # Seznam plateb
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(5)
        self.payments_table.setHorizontalHeaderLabels([
            "Datum", "Částka", "Způsob platby", "Poznámka", "Vytvořil"
        ])
        self.payments_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.payments_table)

        return widget

    def create_documents_tab(self):
        """Záložka: Dokumenty"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Tlačítka
        buttons_layout = QHBoxLayout()

        upload_btn = QPushButton("📎 Nahrát soubor")
        upload_btn.clicked.connect(self.upload_document)
        upload_btn.setStyleSheet(f"background-color: {config.COLOR_SECONDARY}; color: white; padding: 8px 15px;")
        buttons_layout.addWidget(upload_btn)

        generate_pdf_btn = QPushButton("📄 Generovat PDF faktury")
        generate_pdf_btn.clicked.connect(self.generate_invoice_pdf)
        buttons_layout.addWidget(generate_pdf_btn)

        download_btn = QPushButton("⬇️ Stáhnout")
        download_btn.clicked.connect(self.download_document)
        buttons_layout.addWidget(download_btn)

        delete_doc_btn = QPushButton("🗑️ Smazat")
        delete_doc_btn.clicked.connect(self.delete_document)
        buttons_layout.addWidget(delete_doc_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # Seznam dokumentů
        self.documents_list = QListWidget()
        self.documents_list.setIconSize(QIcon().actualSize(QIcon.Mode.Normal))
        layout.addWidget(self.documents_list)

        return widget

    def create_history_tab(self):
        """Záložka: Historie změn"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info_label = QLabel("Historie všech změn a událostí faktury:")
        info_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # Strom historie
        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabels(["Událost", "Datum a čas", "Uživatel", "Detail"])
        self.history_tree.setAlternatingRowColors(True)
        layout.addWidget(self.history_tree)

        return widget

    def create_buttons(self, parent_layout):
        """Vytvoření tlačítek"""
        buttons_frame = QFrame()
        buttons_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 2px solid #e0e0e0;
                padding: 15px;
            }
        """)
        buttons_layout = QHBoxLayout(buttons_frame)

        # Levá strana - akce
        if self.is_edit:
            print_btn = QPushButton("🖨️ Tisk")
            print_btn.clicked.connect(self.print_invoice)
            buttons_layout.addWidget(print_btn)

            email_btn = QPushButton("📧 Odeslat emailem")
            email_btn.clicked.connect(self.send_email)
            buttons_layout.addWidget(email_btn)

            copy_btn = QPushButton("📄 Kopírovat fakturu")
            copy_btn.clicked.connect(self.copy_invoice)
            buttons_layout.addWidget(copy_btn)

            if self.invoice_type == "issued":
                cancel_btn = QPushButton("❌ Storno")
                cancel_btn.clicked.connect(self.cancel_invoice)
                cancel_btn.setStyleSheet(f"background-color: {config.COLOR_DANGER}; color: white;")
                buttons_layout.addWidget(cancel_btn)

                credit_note_btn = QPushButton("📋 Dobropis")
                credit_note_btn.clicked.connect(self.create_credit_note)
                buttons_layout.addWidget(credit_note_btn)

        buttons_layout.addStretch()

        # Pravá strana - uložit/zrušit
        close_btn = QPushButton("Zavřít")
        close_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(close_btn)

        save_btn = QPushButton("💾 Uložit")
        save_btn.clicked.connect(self.save_invoice)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 10px 40px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14pt;
            }}
        """)
        buttons_layout.addWidget(save_btn)

        parent_layout.addWidget(buttons_frame)

    # =====================================================
    # INICIALIZACE A NAČÍTÁNÍ
    # =====================================================

    def init_new_invoice(self):
        """Inicializace nové faktury"""
        # Automatické číslo
        next_number = db.get_next_invoice_number(self.invoice_type)
        self.invoice_number_input.setText(next_number)
        self.invoice_number_input.setEnabled(False)

        self.update_header()

    def load_invoice(self):
        """Načtení existující faktury"""
        try:
            query = """
                SELECT i.*, c.first_name, c.last_name, c.company, u.full_name as created_by_name
                FROM invoices i
                LEFT JOIN customers c ON i.customer_id = c.id
                LEFT JOIN users u ON i.created_by = u.id
                WHERE i.id = ?
            """
            invoice = db.fetch_one(query, (self.invoice_id,))

            if not invoice:
                QMessageBox.critical(self, "Chyba", "Faktura nebyla nalezena.")
                self.reject()
                return

            self.original_invoice = invoice
            self.invoice_type = invoice["invoice_type"]

            # Základní údaje
            self.invoice_number_input.setText(invoice["invoice_number"])
            self.invoice_number_input.setEnabled(False)
            self.auto_number_checkbox.setVisible(False)

            # Zákazník
            if invoice["customer_id"]:
                index = self.customer_combo.findData(invoice["customer_id"])
                if index >= 0:
                    self.customer_combo.setCurrentIndex(index)
            elif invoice["supplier_name"]:
                self.customer_combo.setEditText(invoice["supplier_name"])

            # Data
            self.issue_date.setDate(QDate.fromString(invoice["issue_date"], "yyyy-MM-dd"))
            self.due_date.setDate(QDate.fromString(invoice["due_date"], "yyyy-MM-dd"))
            self.tax_date.setDate(QDate.fromString(invoice["tax_date"], "yyyy-MM-dd"))

            # Platební údaje
            if invoice["payment_method"]:
                index = self.payment_method.findText(invoice["payment_method"])
                if index >= 0:
                    self.payment_method.setCurrentIndex(index)

            if invoice["variable_symbol"]:
                self.variable_symbol.setText(invoice["variable_symbol"])
            if invoice["constant_symbol"]:
                self.constant_symbol.setText(invoice["constant_symbol"])
            if invoice["specific_symbol"]:
                self.specific_symbol.setText(invoice["specific_symbol"])

            if invoice["note"]:
                self.note_input.setPlainText(invoice["note"])

            # Zakázka
            if invoice["order_id"]:
                index = self.order_combo.findData(invoice["order_id"])
                if index >= 0:
                    self.order_combo.setCurrentIndex(index)

            # Načtení položek
            self.load_invoice_items()

            # Načtení plateb
            self.load_payments()

            # Načtení dokumentů
            self.load_documents()

            # Načtení historie
            self.load_history()

            self.update_header()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst fakturu:\n{e}")
            self.reject()

    def load_invoice_items(self):
        """Načtení položek faktury"""
        try:
            query = """
                SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY id
            """
            items = db.fetch_all(query, (self.invoice_id,))

            self.items_data = []
            for item in items:
                self.items_data.append({
                    "id": item["id"],
                    "name": item["item_name"],
                    "quantity": item["quantity"],
                    "unit": item["unit"] or "ks",
                    "price": item["price_per_unit"],
                    "vat_rate": item["vat_rate"],
                    "warehouse_item_id": item["warehouse_item_id"]
                })

            self.refresh_items_table()

        except Exception as e:
            print(f"Chyba při načítání položek faktury: {e}")

    def load_payments(self):
        """Načtení plateb"""
        try:
            query = """
                SELECT p.*, u.full_name as created_by_name
                FROM payments p
                LEFT JOIN users u ON p.created_by = u.id
                WHERE p.invoice_id = ?
                ORDER BY p.payment_date DESC
            """
            payments = db.fetch_all(query, (self.invoice_id,))

            self.payments_data = list(payments)
            self.refresh_payments_table()

        except Exception as e:
            print(f"Chyba při načítání plateb: {e}")

    def load_documents(self):
        """Načtení dokumentů"""
        try:
            query = """
                SELECT * FROM documents
                WHERE linked_entity_type = 'invoice' AND linked_entity_id = ?
                ORDER BY upload_date DESC
            """
            documents = db.fetch_all(query, (self.invoice_id,))

            self.documents_data = list(documents)
            self.refresh_documents_list()

        except Exception as e:
            print(f"Chyba při načítání dokumentů: {e}")

    def load_history(self):
        """Načtení historie"""
        if not self.is_edit:
            return

        self.history_tree.clear()

        # Vytvoření
        if self.original_invoice:
            root = QTreeWidgetItem(self.history_tree)
            root.setText(0, "🆕 Faktura vytvořena")
            root.setText(1, self.format_datetime(self.original_invoice["created_at"]))
            root.setText(2, self.original_invoice["created_by_name"] or "Systém")
            root.setText(3, f"Číslo: {self.original_invoice['invoice_number']}")

        # Platby
        for payment in self.payments_data:
            item = QTreeWidgetItem(self.history_tree)
            item.setText(0, "💳 Platba přijata")
            item.setText(1, self.format_datetime(payment["created_at"]))
            item.setText(2, payment["created_by_name"] or "Systém")
            item.setText(3, f"Částka: {payment['amount']:,.2f} Kč, {payment['payment_method']}".replace(",", " "))

        # Dokumenty
        for doc in self.documents_data:
            item = QTreeWidgetItem(self.history_tree)
            item.setText(0, "📎 Dokument nahrán")
            item.setText(1, self.format_datetime(doc["upload_date"]))
            item.setText(2, "")
            item.setText(3, doc["document_name"])

        # Rozbalit vše
        self.history_tree.expandAll()

    def load_customers(self):
        """Načtení seznamu zákazníků"""
        try:
            query = """
                SELECT id, first_name, last_name, company
                FROM customers
                ORDER BY last_name, first_name
            """
            customers = db.fetch_all(query)

            self.customer_combo.clear()
            self.customer_combo.addItem("-- Vyberte zákazníka --", None)

            for customer in customers:
                if customer["company"]:
                    text = f"{customer['company']} ({customer['first_name']} {customer['last_name']})"
                else:
                    text = f"{customer['first_name']} {customer['last_name']}"
                self.customer_combo.addItem(text, customer["id"])

        except Exception as e:
            print(f"Chyba při načítání zákazníků: {e}")

    def load_orders(self):
        """Načtení seznamu zakázek"""
        try:
            query = """
                SELECT o.id, o.order_number, c.first_name, c.last_name, o.total_price
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                WHERE o.status IN ('V přípravě', 'Otevřená', 'Rozpracovaná')
                ORDER BY o.created_date DESC
                LIMIT 100
            """
            orders = db.fetch_all(query)

            for order in orders:
                text = f"{order['order_number']} - {order['first_name']} {order['last_name']} ({order['total_price']:,.0f} Kč)".replace(",", " ")
                self.order_combo.addItem(text, order["id"])

        except Exception as e:
            print(f"Chyba při načítání zakázek: {e}")

    # =====================================================
    # UDÁLOSTI A AKTUALIZACE
    # =====================================================

    def on_tab_changed(self, index):
        """Změna záložky"""
        # Můžeme zde provést refresh dat při přepnutí
        pass

    def on_type_changed(self):
        """Změna typu faktury"""
        if hasattr(self, 'invoice_type_combo'):
            self.invoice_type = self.invoice_type_combo.currentData()
            label_text = "Zákazník:" if self.invoice_type == "issued" else "Dodavatel:"
            self.customer_label.setText(label_text)

            # Aktualizovat číslo faktury
            next_number = db.get_next_invoice_number(self.invoice_type)
            self.invoice_number_input.setText(next_number)

    def on_order_changed(self):
        """Změna zakázky"""
        # Případně můžeme automaticky načíst data zákazníka
        pass

    def toggle_auto_number(self, state):
        """Přepnutí automatického číslování"""
        auto = (state == Qt.CheckState.Checked.value)
        self.invoice_number_input.setEnabled(not auto)

        if auto and not self.is_edit:
            next_number = db.get_next_invoice_number(self.invoice_type)
            self.invoice_number_input.setText(next_number)

    def update_due_date(self):
        """Aktualizace data splatnosti"""
        if not self.is_edit:
            query = "SELECT setting_value FROM admin_settings WHERE setting_key = 'default_due_days'"
            result = db.fetch_one(query)
            due_days = int(result[0]) if result else 14

            new_due_date = self.issue_date.date().addDays(due_days)
            self.due_date.setDate(new_due_date)

    def update_header(self):
        """Aktualizace hlavičky"""
        if self.is_edit and self.original_invoice:
            self.header_number.setText(f"Faktura {self.original_invoice['invoice_number']}")

            status = self.original_invoice['status']
            status_labels = {
                'paid': ('✅ Zaplaceno', config.COLOR_SUCCESS),
                'unpaid': ('⏳ Nezaplaceno', config.COLOR_WARNING),
                'partial': ('💳 Částečně zaplaceno', '#3498db'),
                'overdue': ('⚠️ Po splatnosti', config.COLOR_DANGER),
                'cancelled': ('❌ Stornováno', '#95a5a6')
            }

            label, color = status_labels.get(status, ('', ''))
            self.header_status.setText(label)
            self.header_status.setStyleSheet(f"color: {color};")
        else:
            self.header_number.setText("Nová faktura")
            self.header_status.setText("")

    # =====================================================
    # POLOŽKY FAKTURY
    # =====================================================

    def add_invoice_item(self):
        """Přidání položky faktury"""
        dialog = InvoiceItemDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            item_data = dialog.get_data()
            self.items_data.append(item_data)
            self.refresh_items_table()
            self.add_history_entry("Přidána položka", f"{item_data['name']}")

    def add_item_from_warehouse(self):
        """Přidání položky ze skladu"""
        dialog = WarehouseItemSelector(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_items = dialog.get_selected_items()
            for item in selected_items:
                self.items_data.append({
                    "name": item["name"],
                    "quantity": 1,
                    "unit": item["unit"],
                    "price": item["price_sale"],
                    "vat_rate": 21,
                    "warehouse_item_id": item["id"]
                })
            self.refresh_items_table()

    def edit_invoice_item(self):
        """Úprava položky faktury"""
        current_row = self.items_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Upozornění", "Vyberte položku k úpravě.")
            return

        item_data = self.items_data[current_row]
        dialog = InvoiceItemDialog(self, item_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_data()
            self.items_data[current_row] = updated_data
            self.refresh_items_table()
            self.add_history_entry("Upravena položka", f"{updated_data['name']}")

    def remove_invoice_item(self):
        """Odebrání položky faktury"""
        current_row = self.items_table.currentRow()
        if current_row >= 0:
            item_name = self.items_data[current_row]["name"]
            reply = QMessageBox.question(
                self,
                "Odebrat položku",
                f"Opravdu chcete odebrat položku '{item_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                del self.items_data[current_row]
                self.refresh_items_table()
                self.add_history_entry("Odebrána položka", item_name)

    def import_from_order(self):
        """Import položek ze zakázky"""
        order_id = self.order_combo.currentData()
        if not order_id:
            QMessageBox.warning(self, "Upozornění", "Vyberte zakázku.")
            return

        try:
            query = """
                SELECT item_name, quantity, unit, unit_price
                FROM order_items
                WHERE order_id = ?
            """
            order_items = db.fetch_all(query, (order_id,))

            if not order_items:
                QMessageBox.information(self, "Info", "Zakázka neobsahuje žádné položky.")
                return

            reply = QMessageBox.question(
                self,
                "Import položek",
                f"Chcete importovat {len(order_items)} položek ze zakázky?\n\nStávající položky budou smazány.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.items_data = []
                for item in order_items:
                    self.items_data.append({
                        "name": item["item_name"],
                        "quantity": item["quantity"],
                        "unit": item["unit"] or "ks",
                        "price": item["unit_price"],
                        "vat_rate": 21,
                        "warehouse_item_id": None
                    })

                self.refresh_items_table()
                self.add_history_entry("Import ze zakázky", f"{len(order_items)} položek")
                QMessageBox.information(self, "Úspěch", f"Importováno {len(order_items)} položek.")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se importovat položky:\n{e}")

    def refresh_items_table(self):
        """Obnovení tabulky položek"""
        self.items_table.setRowCount(len(self.items_data))

        total_without_vat = 0
        total_vat = 0
        total_with_vat = 0

        vat_breakdown = {}  # {vat_rate: {'base': amount, 'vat': amount}}

        for row, item in enumerate(self.items_data):
            # Název
            self.items_table.setItem(row, 0, QTableWidgetItem(item["name"]))

            # Množství
            qty_item = QTableWidgetItem(f"{item['quantity']:.2f}")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.items_table.setItem(row, 1, qty_item)

            # Jednotka
            self.items_table.setItem(row, 2, QTableWidgetItem(item["unit"]))

            # Cena bez DPH
            price_item = QTableWidgetItem(f"{item['price']:,.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.items_table.setItem(row, 3, price_item)

            # DPH %
            vat_item = QTableWidgetItem(f"{item['vat_rate']}%")
            vat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.items_table.setItem(row, 4, vat_item)

            # Cena s DPH
            price_with_vat = item["price"] * (1 + item["vat_rate"] / 100)
            price_vat_item = QTableWidgetItem(f"{price_with_vat:,.2f}")
            price_vat_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.items_table.setItem(row, 5, price_vat_item)

            # Celkem bez DPH
            item_total_without_vat = item["price"] * item["quantity"]
            total_without_item = QTableWidgetItem(f"{item_total_without_vat:,.2f}")
            total_without_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.items_table.setItem(row, 6, total_without_item)

            # Celkem s DPH
            item_vat = item_total_without_vat * item["vat_rate"] / 100
            item_total_with_vat = item_total_without_vat + item_vat
            total_with_item = QTableWidgetItem(f"{item_total_with_vat:,.2f}")
            total_with_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.items_table.setItem(row, 7, total_with_item)

            # Součty
            total_without_vat += item_total_without_vat
            total_vat += item_vat
            total_with_vat += item_total_with_vat

            # Rozpis DPH
            rate = item["vat_rate"]
            if rate not in vat_breakdown:
                vat_breakdown[rate] = {"base": 0, "vat": 0}
            vat_breakdown[rate]["base"] += item_total_without_vat
            vat_breakdown[rate]["vat"] += item_vat

        # Aktualizace labelů
        self.total_without_vat_label.setText(f"{total_without_vat:,.2f} Kč".replace(",", " "))
        self.total_vat_label.setText(f"{total_vat:,.2f} Kč".replace(",", " "))
        self.total_with_vat_label.setText(f"{total_with_vat:,.2f} Kč".replace(",", " "))

        # Rozpis DPH
        if vat_breakdown:
            breakdown_text = ""
            for rate in sorted(vat_breakdown.keys()):
                base = vat_breakdown[rate]["base"]
                vat = vat_breakdown[rate]["vat"]
                breakdown_text += f"DPH {rate}%: {base:,.2f} Kč → {vat:,.2f} Kč\n".replace(",", " ")
            self.vat_breakdown_label.setText(breakdown_text.strip())
        else:
            self.vat_breakdown_label.setText("Žádné položky")

        # Aktualizace přehledu plateb
        if self.is_edit:
            self.update_payment_overview(total_with_vat)

    # =====================================================
    # PLATBY
    # =====================================================

    def add_payment(self):
        """Přidání platby"""
        if not self.is_edit:
            QMessageBox.warning(self, "Upozornění", "Nejprve uložte fakturu.")
            return

        # Vypočítat zbývající částku
        total = float(self.total_with_vat_label.text().replace(" Kč", "").replace(" ", ""))
        paid = sum(p["amount"] for p in self.payments_data)
        remaining = total - paid

        if remaining <= 0:
            QMessageBox.information(self, "Info", "Faktura je již plně zaplacena.")
            return

        dialog = PaymentDialog(
            self,
            self.invoice_id,
            self.original_invoice["invoice_number"],
            remaining
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_payments()
            self.add_history_entry("Přidána platba", f"{dialog.amount_input.value():,.2f} Kč")

    def remove_payment(self):
        """Odebrání platby"""
        current_row = self.payments_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Upozornění", "Vyberte platbu k odebrání.")
            return

        payment = self.payments_data[current_row]

        reply = QMessageBox.question(
            self,
            "Odebrat platbu",
            f"Opravdu chcete odebrat platbu {payment['amount']:,.2f} Kč z {payment['payment_date']}?".replace(",", " "),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Smazat platbu
                query = "DELETE FROM payments WHERE id = ?"
                db.execute_query(query, (payment["id"],))

                # Aktualizovat zaplacené částky na faktuře
                update_query = """
                    UPDATE invoices
                    SET paid_amount = paid_amount - ?,
                        status = CASE
                            WHEN (paid_amount - ?) <= 0 THEN 'unpaid'
                            WHEN (paid_amount - ?) < total_with_vat THEN 'partial'
                            ELSE 'paid'
                        END
                    WHERE id = ?
                """
                db.execute_query(update_query, (payment["amount"], payment["amount"], payment["amount"], self.invoice_id))

                self.load_payments()
                self.add_history_entry("Odebrána platba", f"{payment['amount']:,.2f} Kč")
                QMessageBox.information(self, "Úspěch", "Platba byla odebrána.")

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se odebrat platbu:\n{e}")

    def refresh_payments_table(self):
        """Obnovení tabulky plateb"""
        self.payments_table.setRowCount(len(self.payments_data))

        for row, payment in enumerate(self.payments_data):
            # Datum
            payment_date = datetime.fromisoformat(payment["payment_date"]).strftime("%d.%m.%Y")
            self.payments_table.setItem(row, 0, QTableWidgetItem(payment_date))

            # Částka
            amount_item = QTableWidgetItem(f"{payment['amount']:,.2f} Kč".replace(",", " "))
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.payments_table.setItem(row, 1, amount_item)

            # Způsob platby
            self.payments_table.setItem(row, 2, QTableWidgetItem(payment["payment_method"] or "-"))

            # Poznámka
            self.payments_table.setItem(row, 3, QTableWidgetItem(payment["note"] or "-"))

            # Vytvořil
            self.payments_table.setItem(row, 4, QTableWidgetItem(payment["created_by_name"] or "-"))

        # Aktualizace přehledu
        if self.is_edit:
            total = self.original_invoice["total_with_vat"]
            self.update_payment_overview(total)

    def update_payment_overview(self, total):
        """Aktualizace přehledu plateb"""
        paid = sum(p["amount"] for p in self.payments_data)
        remaining = total - paid

        self.payment_total_label.setText(f"Celková částka: <b>{total:,.2f} Kč</b>".replace(",", " "))
        self.payment_paid_label.setText(f"Zaplaceno: <b>{paid:,.2f} Kč</b>".replace(",", " "))

        if remaining > 0:
            self.payment_remaining_label.setText(f"Zbývá uhradit: <b>{remaining:,.2f} Kč</b>".replace(",", " "))
            self.payment_remaining_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        else:
            self.payment_remaining_label.setText(f"Zbývá uhradit: <b>0,00 Kč</b>")
            self.payment_remaining_label.setStyleSheet("color: #27ae60; font-weight: bold;")

    # =====================================================
    # DOKUMENTY
    # =====================================================

    def upload_document(self):
        """Nahrání dokumentu"""
        if not self.is_edit:
            QMessageBox.warning(self, "Upozornění", "Nejprve uložte fakturu.")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Vyberte soubor",
            "",
            "Všechny soubory (*.*)"
        )

        if not file_path:
            return

        try:
            # Zkopírovat soubor do data/documents
            documents_dir = Path(config.DATA_DIR) / "documents" / "invoices"
            documents_dir.mkdir(parents=True, exist_ok=True)

            file_name = Path(file_path).name
            dest_path = documents_dir / f"{self.invoice_id}_{file_name}"

            import shutil
            shutil.copy2(file_path, dest_path)

            # Uložit do databáze
            file_size = dest_path.stat().st_size
            query = """
                INSERT INTO documents (
                    document_type, document_name, file_path, linked_entity_type,
                    linked_entity_id, file_size, uploaded_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            db.execute_query(query, (
                "invoice_attachment",
                file_name,
                str(dest_path),
                "invoice",
                self.invoice_id,
                file_size,
                1  # TODO: Skutečné ID uživatele
            ))

            self.load_documents()
            self.add_history_entry("Nahrán dokument", file_name)
            QMessageBox.information(self, "Úspěch", "Dokument byl nahrán.")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se nahrát dokument:\n{e}")

    def generate_invoice_pdf(self):
        """Generování PDF faktury"""
        if not self.is_edit:
            QMessageBox.warning(self, "Upozornění", "Nejprve uložte fakturu.")
            return

        # TODO: Implementovat generování PDF
        QMessageBox.information(
            self,
            "Generování PDF",
            "Funkce generování PDF faktury bude implementována.\n\n"
            "Bude zahrnovat:\n"
            "- Profesionální šablonu faktury\n"
            "- Logo firmy\n"
            "- Všechny položky a součty\n"
            "- QR kód pro platbu"
        )

    def download_document(self):
        """Stažení dokumentu"""
        current_item = self.documents_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Upozornění", "Vyberte dokument ke stažení.")
            return

        doc = self.documents_data[self.documents_list.currentRow()]
        source_path = Path(doc["file_path"])

        if not source_path.exists():
            QMessageBox.critical(self, "Chyba", "Soubor nebyl nalezen.")
            return

        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit jako",
            doc["document_name"]
        )

        if dest_path:
            try:
                import shutil
                shutil.copy2(source_path, dest_path)
                QMessageBox.information(self, "Úspěch", "Dokument byl stažen.")
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se stáhnout dokument:\n{e}")

    def delete_document(self):
        """Smazání dokumentu"""
        current_item = self.documents_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Upozornění", "Vyberte dokument ke smazání.")
            return

        doc = self.documents_data[self.documents_list.currentRow()]

        reply = QMessageBox.question(
            self,
            "Smazat dokument",
            f"Opravdu chcete smazat dokument '{doc['document_name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Smazat soubor
                file_path = Path(doc["file_path"])
                if file_path.exists():
                    file_path.unlink()

                # Smazat z databáze
                query = "DELETE FROM documents WHERE id = ?"
                db.execute_query(query, (doc["id"],))

                self.load_documents()
                self.add_history_entry("Smazán dokument", doc["document_name"])
                QMessageBox.information(self, "Úspěch", "Dokument byl smazán.")

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat dokument:\n{e}")

    def refresh_documents_list(self):
        """Obnovení seznamu dokumentů"""
        self.documents_list.clear()

        for doc in self.documents_data:
            item = QListWidgetItem(f"📄 {doc['document_name']}")
            upload_date = datetime.fromisoformat(doc["upload_date"]).strftime("%d.%m.%Y %H:%M")
            size_kb = doc["file_size"] / 1024 if doc["file_size"] else 0
            item.setToolTip(f"Nahráno: {upload_date}\nVelikost: {size_kb:.1f} KB")
            self.documents_list.addItem(item)

    # =====================================================
    # AKCE
    # =====================================================

    def save_invoice(self):
        """Uložení faktury"""
        try:
            # Validace
            if not self.invoice_number_input.text().strip():
                QMessageBox.warning(self, "Chyba", "Vyplňte číslo faktury.")
                return

            if self.customer_combo.currentData() is None and self.invoice_type == "issued":
                QMessageBox.warning(self, "Chyba", "Vyberte zákazníka.")
                return

            if len(self.items_data) == 0:
                QMessageBox.warning(self, "Chyba", "Přidejte alespoň jednu položku faktury.")
                return

            # Výpočet součtů
            total_without_vat = sum(item["price"] * item["quantity"] for item in self.items_data)
            total_vat = sum(item["price"] * item["quantity"] * item["vat_rate"] / 100 for item in self.items_data)
            total_with_vat = total_without_vat + total_vat

            # Data faktury
            invoice_data = {
                "invoice_number": self.invoice_number_input.text().strip(),
                "invoice_type": self.invoice_type,
                "customer_id": self.customer_combo.currentData(),
                "supplier_name": self.customer_combo.currentText() if self.invoice_type == "received" else None,
                "issue_date": self.issue_date.date().toString("yyyy-MM-dd"),
                "due_date": self.due_date.date().toString("yyyy-MM-dd"),
                "tax_date": self.tax_date.date().toString("yyyy-MM-dd"),
                "payment_method": self.payment_method.currentText(),
                "variable_symbol": self.variable_symbol.text().strip() or None,
                "constant_symbol": self.constant_symbol.text().strip() or None,
                "specific_symbol": self.specific_symbol.text().strip() or None,
                "note": self.note_input.toPlainText().strip() or None,
                "total_without_vat": total_without_vat,
                "total_vat": total_vat,
                "total_with_vat": total_with_vat,
                "order_id": self.order_combo.currentData(),
                "created_by": 1  # TODO: Skutečné ID přihlášeného uživatele
            }

            if self.is_edit:
                # Aktualizace
                paid_amount = self.original_invoice["paid_amount"]
                status = self.calculate_status(total_with_vat, paid_amount)

                query = """
                    UPDATE invoices SET
                        invoice_number = ?, invoice_type = ?, customer_id = ?, supplier_name = ?,
                        issue_date = ?, due_date = ?, tax_date = ?, payment_method = ?,
                        variable_symbol = ?, constant_symbol = ?, specific_symbol = ?,
                        note = ?, total_without_vat = ?, total_vat = ?,
                        total_with_vat = ?, order_id = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """
                db.execute_query(query, (
                    invoice_data["invoice_number"], invoice_data["invoice_type"],
                    invoice_data["customer_id"], invoice_data["supplier_name"],
                    invoice_data["issue_date"], invoice_data["due_date"], invoice_data["tax_date"],
                    invoice_data["payment_method"], invoice_data["variable_symbol"],
                    invoice_data["constant_symbol"], invoice_data["specific_symbol"],
                    invoice_data["note"], invoice_data["total_without_vat"],
                    invoice_data["total_vat"], invoice_data["total_with_vat"],
                    invoice_data["order_id"], status, self.invoice_id
                ))

                # Smazat staré položky
                db.execute_query("DELETE FROM invoice_items WHERE invoice_id = ?", (self.invoice_id,))
                invoice_id = self.invoice_id

            else:
                # Vložení nové faktury
                query = """
                    INSERT INTO invoices (
                        invoice_number, invoice_type, customer_id, supplier_name,
                        issue_date, due_date, tax_date, payment_method, variable_symbol,
                        constant_symbol, specific_symbol, note, status, total_without_vat,
                        total_vat, total_with_vat, paid_amount, order_id, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                db.execute_query(query, (
                    invoice_data["invoice_number"], invoice_data["invoice_type"],
                    invoice_data["customer_id"], invoice_data["supplier_name"],
                    invoice_data["issue_date"], invoice_data["due_date"], invoice_data["tax_date"],
                    invoice_data["payment_method"], invoice_data["variable_symbol"],
                    invoice_data["constant_symbol"], invoice_data["specific_symbol"],
                    invoice_data["note"], "unpaid",
                    invoice_data["total_without_vat"], invoice_data["total_vat"],
                    invoice_data["total_with_vat"], 0,
                    invoice_data["order_id"], invoice_data["created_by"]
                ))

                # Získat ID nové faktury
                invoice_id = db.cursor.lastrowid

            # Vložení položek
            for item in self.items_data:
                item_total_without_vat = item["price"] * item["quantity"]
                item_vat = item_total_without_vat * item["vat_rate"] / 100
                item_total_with_vat = item_total_without_vat + item_vat

                query = """
                    INSERT INTO invoice_items (
                        invoice_id, item_name, quantity, unit, price_per_unit,
                        vat_rate, total_without_vat, total_vat, total_with_vat, warehouse_item_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                db.execute_query(query, (
                    invoice_id, item["name"], item["quantity"], item["unit"],
                    item["price"], item["vat_rate"], item_total_without_vat,
                    item_vat, item_total_with_vat, item.get("warehouse_item_id")
                ))

            QMessageBox.information(
                self,
                "Úspěch",
                f"Faktura {invoice_data['invoice_number']} byla {'aktualizována' if self.is_edit else 'vytvořena'}."
            )

            self.invoice_saved.emit()
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit fakturu:\n{e}")

    def calculate_status(self, total, paid):
        """Výpočet statusu faktury"""
        if paid >= total:
            return "paid"
        elif paid > 0:
            return "partial"
        else:
            return "unpaid"

    def print_invoice(self):
        """Tisk faktury"""
        QMessageBox.information(
            self,
            "Tisk",
            "Funkce tisku faktury bude implementována.\n\n"
            "Vygeneruje PDF a odešle na výchozí tiskárnu."
        )

    def send_email(self):
        """Odeslání emailem"""
        QMessageBox.information(
            self,
            "Email",
            "Funkce odeslání emailu bude implementována.\n\n"
            "Bude zahrnovat:\n"
            "- Načtení emailu zákazníka\n"
            "- Generování PDF\n"
            "- Odeslání přes SMTP"
        )

    def copy_invoice(self):
        """Kopírování faktury"""
        reply = QMessageBox.question(
            self,
            "Kopírovat fakturu",
            "Chcete vytvořit kopii této faktury?\n\nPro novou fakturu bude vygenerováno nové číslo.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implementovat kopírování
            QMessageBox.information(self, "Info", "Funkce kopírování bude implementována.")

    def cancel_invoice(self):
        """Storno faktury"""
        reply = QMessageBox.question(
            self,
            "Storno faktury",
            f"Opravdu chcete stornovat fakturu {self.original_invoice['invoice_number']}?\n\n"
            "Tato akce je nevratná!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = "UPDATE invoices SET status = 'cancelled' WHERE id = ?"
                db.execute_query(query, (self.invoice_id,))

                self.add_history_entry("Faktura stornována", "Změna statusu na 'Stornováno'")
                QMessageBox.information(self, "Úspěch", "Faktura byla stornována.")

                self.invoice_saved.emit()
                self.accept()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se stornovat fakturu:\n{e}")

    def create_credit_note(self):
        """Vytvoření dobropisu"""
        QMessageBox.information(
            self,
            "Dobropis",
            "Funkce vytvoření dobropisu bude implementována.\n\n"
            "Bude zahrnovat:\n"
            "- Vytvoření nové faktury se zápornými částkami\n"
            "- Propojení s původní fakturou\n"
            "- Automatické vyplnění všech údajů"
        )

    def quick_add_customer(self):
        """Rychlé přidání zákazníka"""
        # TODO: Dialog pro rychlé přidání zákazníka
        QMessageBox.information(self, "Přidat zákazníka", "Dialog pro přidání zákazníka bude implementován.")

    # =====================================================
    # POMOCNÉ METODY
    # =====================================================

    def add_history_entry(self, event, detail):
        """Přidání záznamu do historie"""
        if not hasattr(self, 'temp_history'):
            self.temp_history = []

        self.temp_history.append({
            "event": event,
            "timestamp": datetime.now(),
            "user": "Aktuální uživatel",
            "detail": detail
        })

    def format_datetime(self, dt_string):
        """Formátování datetime"""
        try:
            dt = datetime.fromisoformat(dt_string)
            return dt.strftime("%d.%m.%Y %H:%M")
        except:
            return dt_string


# =====================================================
# POMOCNÉ DIALOGY
# =====================================================

class InvoiceItemDialog(QDialog):
    """Dialog pro přidání/úpravu položky faktury"""

    def __init__(self, parent, item_data=None):
        super().__init__(parent)
        self.item_data = item_data
        self.is_edit = item_data is not None

        self.setWindowTitle("Upravit položku" if self.is_edit else "Přidat položku")
        self.setMinimumWidth(500)

        self.init_ui()

        if self.is_edit:
            self.load_data()

    def init_ui(self):
        """Inicializace UI"""
        layout = QFormLayout(self)

        # Název
        self.name_input = QLineEdit()
        layout.addRow("Název položky:", self.name_input)

        # Množství
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setDecimals(2)
        self.quantity_input.setMinimum(0.01)
        self.quantity_input.setMaximum(999999)
        self.quantity_input.setValue(1)
        layout.addRow("Množství:", self.quantity_input)

        # Jednotka
        self.unit_input = QComboBox()
        self.unit_input.setEditable(True)
        self.unit_input.addItems(["ks", "hod", "m", "m2", "m3", "kg", "l", "bal", "sada"])
        layout.addRow("Jednotka:", self.unit_input)

        # Cena bez DPH
        self.price_input = QDoubleSpinBox()
        self.price_input.setDecimals(2)
        self.price_input.setMinimum(0)
        self.price_input.setMaximum(999999)
        self.price_input.setSuffix(" Kč")
        layout.addRow("Cena bez DPH:", self.price_input)

        # Sazba DPH
        self.vat_input = QComboBox()
        self.vat_input.addItems(["21", "12", "0"])
        layout.addRow("Sazba DPH (%):", self.vat_input)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("Uložit" if self.is_edit else "Přidat")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 8px 20px;
            }}
        """)
        buttons_layout.addWidget(ok_btn)

        layout.addRow(buttons_layout)

    def load_data(self):
        """Načtení dat pro editaci"""
        self.name_input.setText(self.item_data["name"])
        self.quantity_input.setValue(self.item_data["quantity"])
        self.unit_input.setCurrentText(self.item_data["unit"])
        self.price_input.setValue(self.item_data["price"])
        self.vat_input.setCurrentText(str(self.item_data["vat_rate"]))

    def get_data(self):
        """Vrátí data položky"""
        return {
            "name": self.name_input.text().strip(),
            "quantity": self.quantity_input.value(),
            "unit": self.unit_input.currentText(),
            "price": self.price_input.value(),
            "vat_rate": int(self.vat_input.currentText()),
            "warehouse_item_id": self.item_data.get("warehouse_item_id") if self.item_data else None
        }


class WarehouseItemSelector(QDialog):
    """Dialog pro výběr položek ze skladu"""

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Vybrat položky ze skladu")
        self.setMinimumSize(800, 600)

        self.init_ui()
        self.load_items()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # Vyhledávání
        search_layout = QHBoxLayout()
        search_label = QLabel("Hledat:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Název, kód...")
        self.search_input.textChanged.connect(self.filter_items)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Tabulka
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "✓", "Kód", "Název", "Množství", "Cena prodejní", "Jednotka"
        ])
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("Přidat vybrané")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 20px;")
        buttons_layout.addWidget(ok_btn)

        layout.addLayout(buttons_layout)

    def load_items(self):
        """Načtení položek ze skladu"""
        try:
            query = """
                SELECT id, code, name, quantity, price_sale, unit
                FROM warehouse
                WHERE quantity > 0
                ORDER BY name
            """
            items = db.fetch_all(query)

            self.table.setRowCount(len(items))

            for row, item in enumerate(items):
                # Checkbox
                checkbox = QCheckBox()
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                self.table.setCellWidget(row, 0, checkbox_widget)

                # Kód
                self.table.setItem(row, 1, QTableWidgetItem(item["code"]))

                # Název
                self.table.setItem(row, 2, QTableWidgetItem(item["name"]))

                # Množství
                self.table.setItem(row, 3, QTableWidgetItem(f"{item['quantity']:.2f}"))

                # Cena
                price_item = QTableWidgetItem(f"{item['price_sale']:,.2f} Kč".replace(",", " "))
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 4, price_item)

                # Jednotka
                self.table.setItem(row, 5, QTableWidgetItem(item["unit"] or "ks"))

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst položky ze skladu:\n{e}")

    def filter_items(self):
        """Filtrování položek"""
        search_text = self.search_input.text().lower()

        for row in range(self.table.rowCount()):
            show = True
            if search_text:
                code = self.table.item(row, 1).text().lower()
                name = self.table.item(row, 2).text().lower()
                if search_text not in code and search_text not in name:
                    show = False
            self.table.setRowHidden(row, not show)

    def get_selected_items(self):
        """Vrátí vybrané položky"""
        selected = []
        try:
            query = "SELECT * FROM warehouse WHERE id = ?"

            for row in range(self.table.rowCount()):
                checkbox_widget = self.table.cellWidget(row, 0)
                checkbox = checkbox_widget.findChild(QCheckBox)

                if checkbox and checkbox.isChecked():
                    code = self.table.item(row, 1).text()
                    # Načíst celý záznam
                    item_query = "SELECT * FROM warehouse WHERE code = ?"
                    item = db.fetch_one(item_query, (code,))
                    if item:
                        selected.append(dict(item))

        except Exception as e:
            print(f"Chyba při získávání vybraných položek: {e}")

        return selected


class PaymentDialog(QDialog):
    """Dialog pro zaznamenání platby"""

    def __init__(self, parent, invoice_id, invoice_number, remaining_amount):
        super().__init__(parent)
        self.invoice_id = invoice_id
        self.invoice_number = invoice_number
        self.remaining_amount = remaining_amount

        self.setWindowTitle(f"Zaznamenat platbu - {invoice_number}")
        self.setMinimumWidth(400)

        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QFormLayout(self)

        # Info
        info_label = QLabel(f"Zbývá uhradit: <b>{self.remaining_amount:,.2f} Kč</b>".replace(",", " "))
        layout.addRow(info_label)

        # Datum platby
        self.payment_date = QDateEdit()
        self.payment_date.setDate(QDate.currentDate())
        self.payment_date.setCalendarPopup(True)
        self.payment_date.setDisplayFormat("dd.MM.yyyy")
        layout.addRow("Datum platby:", self.payment_date)

        # Částka
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setDecimals(2)
        self.amount_input.setMinimum(0.01)
        self.amount_input.setMaximum(self.remaining_amount)
        self.amount_input.setValue(self.remaining_amount)
        self.amount_input.setSuffix(" Kč")
        layout.addRow("Částka:", self.amount_input)

        # Způsob platby
        self.payment_method = QComboBox()
        self.payment_method.addItems([
            "Bankovní převod",
            "Hotovost",
            "Karta",
            "Ostatní"
        ])
        layout.addRow("Způsob platby:", self.payment_method)

        # Poznámka
        self.note_input = QTextEdit()
        self.note_input.setMaximumHeight(60)
        layout.addRow("Poznámka:", self.note_input)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Uložit platbu")
        save_btn.clicked.connect(self.save_payment)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 8px 20px;
            }}
        """)
        buttons_layout.addWidget(save_btn)

        layout.addRow(buttons_layout)

    def save_payment(self):
        """Uložení platby"""
        try:
            amount = self.amount_input.value()

            if amount <= 0:
                QMessageBox.warning(self, "Chyba", "Zadejte platnou částku.")
                return

            if amount > self.remaining_amount + 0.01:
                QMessageBox.warning(self, "Chyba", "Částka platby překračuje zbývající dluh.")
                return

            # Vložení platby
            query = """
                INSERT INTO payments (
                    invoice_id, payment_date, amount, payment_method, note, created_by
                ) VALUES (?, ?, ?, ?, ?, ?)
            """
            db.execute_query(query, (
                self.invoice_id,
                self.payment_date.date().toString("yyyy-MM-dd"),
                amount,
                self.payment_method.currentText(),
                self.note_input.toPlainText().strip() or None,
                1  # TODO: Skutečné ID uživatele
            ))

            # Aktualizace zaplacené částky na faktuře
            update_query = """
                UPDATE invoices
                SET paid_amount = paid_amount + ?,
                    status = CASE
                        WHEN (paid_amount + ?) >= total_with_vat THEN 'paid'
                        WHEN (paid_amount + ?) > 0 THEN 'partial'
                        ELSE status
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            db.execute_query(update_query, (amount, amount, amount, self.invoice_id))

            QMessageBox.information(
                self,
                "Úspěch",
                f"Platba {amount:,.2f} Kč byla zaznamenána.".replace(",", " ")
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit platbu:\n{e}")
