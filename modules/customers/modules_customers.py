# modules_customers.py
# -*- coding: utf-8 -*-
"""
Modul Zákazníci - Hlavní seznam zákazníků
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMenu, QMessageBox, QApplication,
    QFileDialog, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QBrush, QCursor
import config
from database_manager import db
from datetime import datetime, timedelta


class CustomersModule(QWidget):
    """Hlavní modul pro správu zákazníků"""

    customer_selected = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.current_filters = {}
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Inicializace uživatelského rozhraní"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Hlavička
        self.create_header(layout)

        # Statistiky
        self.create_statistics(layout)

        # Filtry
        self.create_filters(layout)

        # Tabulka
        self.create_table(layout)

        self.set_styles()

    def create_header(self, parent_layout):
        """Vytvoření hlavičky s tlačítky"""
        header = QFrame()
        header.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Titulek
        title = QLabel("👥 Zákazníci")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Tlačítka
        btn_new = QPushButton("➕ Nový zákazník")
        btn_new.setObjectName("btnSuccess")
        btn_new.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_new.clicked.connect(self.add_customer)
        header_layout.addWidget(btn_new)

        btn_import = QPushButton("📥 Import")
        btn_import.setObjectName("btnPrimary")
        btn_import.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_import.clicked.connect(self.import_customers)
        header_layout.addWidget(btn_import)

        btn_export = QPushButton("📤 Export")
        btn_export.setObjectName("btnSecondary")
        btn_export.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_export.clicked.connect(self.export_customers)
        header_layout.addWidget(btn_export)

        btn_email = QPushButton("📧 Hromadný email")
        btn_email.setObjectName("btnSecondary")
        btn_email.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_email.clicked.connect(self.send_bulk_email)
        header_layout.addWidget(btn_email)

        parent_layout.addWidget(header)

    def create_statistics(self, parent_layout):
        """Vytvoření panelu statistik"""
        stats_frame = QFrame()
        stats_frame.setObjectName("statsFrame")
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(15)

        self.stat_labels = {}

        stats_config = [
            ("total", "Celkem", "0"),
            ("company", "Firemní", "0"),
            ("personal", "Soukromé", "0"),
            ("active", "Aktivní", "0"),
            ("vip", "VIP", "0"),
            ("debtors", "Dlužníci", "0")
        ]

        for key, name, default in stats_config:
            stat_widget = self.create_stat_card(name, default)
            self.stat_labels[key] = stat_widget.findChild(QLabel, "statValue")
            stats_layout.addWidget(stat_widget)

        parent_layout.addWidget(stats_frame)

    def create_stat_card(self, name, value):
        """Vytvoření karty statistiky"""
        card = QFrame()
        card.setObjectName("statCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)
        card_layout.setSpacing(5)

        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_label = QLabel(name)
        name_label.setObjectName("statName")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(value_label)
        card_layout.addWidget(name_label)

        return card

    def create_filters(self, parent_layout):
        """Vytvoření panelu filtrů"""
        filters_frame = QFrame()
        filters_frame.setObjectName("filtersFrame")
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setSpacing(10)

        # Vyhledávání
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Hledat (jméno, telefon, email, IČO...)")
        self.search_input.setMinimumWidth(250)
        self.search_input.textChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.search_input)

        # Typ zákazníka
        self.filter_type = QComboBox()
        self.filter_type.addItems(["Vše", "Soukromá osoba", "Firma"])
        self.filter_type.currentTextChanged.connect(self.apply_filters)
        filters_layout.addWidget(QLabel("Typ:"))
        filters_layout.addWidget(self.filter_type)

        # Skupina
        self.filter_group = QComboBox()
        self.filter_group.addItems(["Vše", "Standardní", "VIP", "Firemní", "Pojišťovna"])
        self.filter_group.currentTextChanged.connect(self.apply_filters)
        filters_layout.addWidget(QLabel("Skupina:"))
        filters_layout.addWidget(self.filter_group)

        # Aktivita
        self.filter_activity = QComboBox()
        self.filter_activity.addItems(["Vše", "Aktivní", "Neaktivní"])
        self.filter_activity.currentTextChanged.connect(self.apply_filters)
        filters_layout.addWidget(QLabel("Aktivita:"))
        filters_layout.addWidget(self.filter_activity)

        # Pohledávky
        self.filter_debt = QComboBox()
        self.filter_debt.addItems(["Vše", "Bez dluhů", "S pohledávkami"])
        self.filter_debt.currentTextChanged.connect(self.apply_filters)
        filters_layout.addWidget(QLabel("Pohledávky:"))
        filters_layout.addWidget(self.filter_debt)

        filters_layout.addStretch()

        # Reset filtrů
        btn_reset = QPushButton("🔄 Reset")
        btn_reset.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_reset.clicked.connect(self.reset_filters)
        filters_layout.addWidget(btn_reset)

        parent_layout.addWidget(filters_frame)

    def create_table(self, parent_layout):
        """Vytvoření tabulky zákazníků"""
        self.table = QTableWidget()
        self.table.setObjectName("customersTable")

        # Nastavení sloupců
        columns = [
            "ID", "Jméno / Firma", "Telefon", "Email", "Město",
            "Skupina", "Vozidla", "Zakázky", "Útrata", "Poslední zakázka", "Poznámka"
        ]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)

        # Skrytí ID sloupce
        self.table.setColumnHidden(0, True)

        # Nastavení hlavičky
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.Stretch)

        # Nastavení chování
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Signály
        self.table.doubleClicked.connect(self.open_customer_detail)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        parent_layout.addWidget(self.table)

    def load_data(self):
        """Načtení dat z databáze"""
        try:
            # Načtení zákazníků
            query = """
                SELECT
                    c.id,
                    CASE
                        WHEN c.customer_type = 'company' THEN c.company_name
                        ELSE c.first_name || ' ' || c.last_name
                    END as name,
                    c.phone,
                    c.email,
                    c.city,
                    c.customer_group,
                    (SELECT COUNT(*) FROM vehicles WHERE customer_id = c.id) as vehicle_count,
                    (SELECT COUNT(*) FROM orders WHERE customer_id = c.id) as order_count,
                    (SELECT COALESCE(SUM(total_price), 0) FROM orders WHERE customer_id = c.id) as total_spent,
                    (SELECT MAX(created_at) FROM orders WHERE customer_id = c.id) as last_order,
                    c.notes,
                    c.customer_type,
                    c.has_debt
                FROM customers c
                WHERE c.is_active = 1
                ORDER BY name
            """

            customers = db.fetch_all(query)
            self.populate_table(customers if customers else [])
            self.update_statistics()

        except Exception as e:
            print(f"Chyba při načítání zákazníků: {e}")
            self.populate_table([])

    def populate_table(self, customers):
        """Naplnění tabulky daty"""
        self.table.setRowCount(0)

        for customer in customers:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # ID
            id_item = QTableWidgetItem(str(customer[0]))
            self.table.setItem(row, 0, id_item)

            # Jméno / Firma
            name_item = QTableWidgetItem(str(customer[1] or ""))
            name_font = QFont()
            name_font.setBold(True)
            name_item.setFont(name_font)
            self.table.setItem(row, 1, name_item)

            # Telefon
            self.table.setItem(row, 2, QTableWidgetItem(str(customer[2] or "")))

            # Email
            self.table.setItem(row, 3, QTableWidgetItem(str(customer[3] or "")))

            # Město
            self.table.setItem(row, 4, QTableWidgetItem(str(customer[4] or "")))

            # Skupina (s barvou)
            group_item = QTableWidgetItem(str(customer[5] or "Standardní"))
            group_color = self.get_group_color(customer[5])
            group_item.setBackground(QBrush(QColor(group_color)))
            group_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, group_item)

            # Počet vozidel
            vehicles_item = QTableWidgetItem(str(customer[6] or 0))
            vehicles_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, vehicles_item)

            # Počet zakázek
            orders_item = QTableWidgetItem(str(customer[7] or 0))
            orders_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 7, orders_item)

            # Celková útrata
            spent = customer[8] or 0
            spent_item = QTableWidgetItem(f"{spent:,.0f} Kč".replace(",", " "))
            spent_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 8, spent_item)

            # Poslední zakázka
            last_order = customer[9] or ""
            if last_order:
                try:
                    dt = datetime.fromisoformat(last_order)
                    last_order = dt.strftime("%d.%m.%Y")
                except:
                    pass
            self.table.setItem(row, 9, QTableWidgetItem(last_order))

            # Poznámka
            notes = str(customer[10] or "")
            if len(notes) > 50:
                notes = notes[:50] + "..."
            self.table.setItem(row, 10, QTableWidgetItem(notes))

            # Červené pozadí pro dlužníky
            if customer[12]:  # has_debt
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item and col != 5:  # Nezměnit barvu skupiny
                        item.setBackground(QBrush(QColor("#ffcccc")))

    def get_group_color(self, group):
        """Vrátí barvu pro skupinu zákazníka"""
        colors = {
            "VIP": "#a8e6cf",
            "Firemní": "#87ceeb",
            "Pojišťovna": "#fff3cd",
            "Standardní": "#e0e0e0"
        }
        return colors.get(group, "#e0e0e0")

    def update_statistics(self):
        """Aktualizace statistik"""
        try:
            # Celkem
            total = db.fetch_one("SELECT COUNT(*) FROM customers WHERE is_active = 1")
            self.stat_labels["total"].setText(str(total[0] if total else 0))

            # Firemní
            company = db.fetch_one("SELECT COUNT(*) FROM customers WHERE customer_type = 'company' AND is_active = 1")
            self.stat_labels["company"].setText(str(company[0] if company else 0))

            # Soukromé
            personal = db.fetch_one("SELECT COUNT(*) FROM customers WHERE customer_type = 'personal' AND is_active = 1")
            self.stat_labels["personal"].setText(str(personal[0] if personal else 0))

            # Aktivní (zakázka za poslední rok)
            year_ago = (datetime.now() - timedelta(days=365)).isoformat()
            active = db.fetch_one(f"""
                SELECT COUNT(DISTINCT c.id) FROM customers c
                INNER JOIN orders o ON c.id = o.customer_id
                WHERE o.created_at >= '{year_ago}' AND c.is_active = 1
            """)
            self.stat_labels["active"].setText(str(active[0] if active else 0))

            # VIP
            vip = db.fetch_one("SELECT COUNT(*) FROM customers WHERE customer_group = 'VIP' AND is_active = 1")
            self.stat_labels["vip"].setText(str(vip[0] if vip else 0))

            # Dlužníci
            debtors = db.fetch_one("SELECT COUNT(*) FROM customers WHERE has_debt = 1 AND is_active = 1")
            self.stat_labels["debtors"].setText(str(debtors[0] if debtors else 0))

        except Exception as e:
            print(f"Chyba při aktualizaci statistik: {e}")

    def apply_filters(self):
        """Aplikace filtrů na tabulku"""
        search_text = self.search_input.text().lower()
        filter_type = self.filter_type.currentText()
        filter_group = self.filter_group.currentText()
        filter_activity = self.filter_activity.currentText()
        filter_debt = self.filter_debt.currentText()

        for row in range(self.table.rowCount()):
            show_row = True

            # Vyhledávání
            if search_text:
                row_text = ""
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        row_text += item.text().lower() + " "
                if search_text not in row_text:
                    show_row = False

            # Filtr skupiny
            if filter_group != "Vše" and show_row:
                group_item = self.table.item(row, 5)
                if group_item and group_item.text() != filter_group:
                    show_row = False

            self.table.setRowHidden(row, not show_row)

    def reset_filters(self):
        """Reset všech filtrů"""
        self.search_input.clear()
        self.filter_type.setCurrentIndex(0)
        self.filter_group.setCurrentIndex(0)
        self.filter_activity.setCurrentIndex(0)
        self.filter_debt.setCurrentIndex(0)

        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, False)

    def show_context_menu(self, position):
        """Zobrazení kontextového menu"""
        item = self.table.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        menu.addAction("📖 Otevřít detail", self.open_customer_detail)
        menu.addAction("✏️ Upravit zákazníka", self.edit_customer)
        menu.addSeparator()
        menu.addAction("📋 Kopírovat telefon", self.copy_phone)
        menu.addAction("📋 Kopírovat email", self.copy_email)
        menu.addSeparator()
        menu.addAction("🏍️ Zobrazit vozidla", self.show_vehicles)
        menu.addAction("📋 Zobrazit zakázky", self.show_orders)
        menu.addSeparator()
        menu.addAction("📧 Odeslat email", self.send_email)
        menu.addAction("📱 Odeslat SMS", self.send_sms)
        menu.addSeparator()
        menu.addAction("💰 Finanční přehled", self.show_financial)
        menu.addSeparator()
        menu.addAction("🗑️ Smazat zákazníka", self.delete_customer)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def get_selected_customer_id(self):
        """Získání ID vybraného zákazníka"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            id_item = self.table.item(current_row, 0)
            if id_item:
                return int(id_item.text())
        return None

    def add_customer(self):
        """Přidání nového zákazníka"""
        from .customer_form import CustomerFormDialog
        dialog = CustomerFormDialog(self)
        if dialog.exec():
            self.load_data()

    def edit_customer(self):
        """Úprava zákazníka"""
        customer_id = self.get_selected_customer_id()
        if customer_id:
            from .customer_form import CustomerFormDialog
            dialog = CustomerFormDialog(self, customer_id)
            if dialog.exec():
                self.load_data()

    def open_customer_detail(self):
        """Otevření detailu zákazníka"""
        customer_id = self.get_selected_customer_id()
        if customer_id:
            self.customer_selected.emit(customer_id)
            QMessageBox.information(self, "Detail", f"Otevření detailu zákazníka ID: {customer_id}")

    def copy_phone(self):
        """Kopírování telefonu do schránky"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            phone_item = self.table.item(current_row, 2)
            if phone_item:
                QApplication.clipboard().setText(phone_item.text())
                QMessageBox.information(self, "Zkopírováno", "Telefon zkopírován do schránky")

    def copy_email(self):
        """Kopírování emailu do schránky"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            email_item = self.table.item(current_row, 3)
            if email_item:
                QApplication.clipboard().setText(email_item.text())
                QMessageBox.information(self, "Zkopírováno", "Email zkopírován do schránky")

    def show_vehicles(self):
        """Zobrazení vozidel zákazníka"""
        customer_id = self.get_selected_customer_id()
        if customer_id:
            QMessageBox.information(self, "Vozidla", f"Zobrazení vozidel zákazníka ID: {customer_id}")

    def show_orders(self):
        """Zobrazení zakázek zákazníka"""
        customer_id = self.get_selected_customer_id()
        if customer_id:
            QMessageBox.information(self, "Zakázky", f"Zobrazení zakázek zákazníka ID: {customer_id}")

    def send_email(self):
        """Odeslání emailu"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            email_item = self.table.item(current_row, 3)
            if email_item and email_item.text():
                import webbrowser
                webbrowser.open(f"mailto:{email_item.text()}")

    def send_sms(self):
        """Odeslání SMS"""
        QMessageBox.information(self, "SMS", "Funkce odeslání SMS bude implementována")

    def show_financial(self):
        """Zobrazení finančního přehledu"""
        customer_id = self.get_selected_customer_id()
        if customer_id:
            QMessageBox.information(self, "Finance", f"Finanční přehled zákazníka ID: {customer_id}")

    def delete_customer(self):
        """Smazání zákazníka"""
        customer_id = self.get_selected_customer_id()
        if customer_id:
            reply = QMessageBox.question(
                self,
                "Smazat zákazníka",
                "Opravdu chcete smazat tohoto zákazníka?\nTato akce je nevratná.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    db.execute("UPDATE customers SET is_active = 0 WHERE id = ?", (customer_id,))
                    self.load_data()
                    QMessageBox.information(self, "Smazáno", "Zákazník byl úspěšně smazán")
                except Exception as e:
                    QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat zákazníka: {e}")

    def import_customers(self):
        """Import zákazníků z CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import zákazníků",
            "",
            "CSV soubory (*.csv);;Excel soubory (*.xlsx)"
        )
        if file_path:
            QMessageBox.information(self, "Import", f"Import ze souboru: {file_path}")

    def export_customers(self):
        """Export zákazníků do CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export zákazníků",
            "zakaznici_export.csv",
            "CSV soubory (*.csv);;Excel soubory (*.xlsx)"
        )
        if file_path:
            QMessageBox.information(self, "Export", f"Export do souboru: {file_path}")

    def send_bulk_email(self):
        """Hromadné odeslání emailů"""
        QMessageBox.information(self, "Hromadný email", "Funkce hromadného emailu bude implementována")

    def refresh(self):
        """Obnovení dat modulu"""
        self.load_data()

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet(f"""
            #headerFrame {{
                background-color: white;
                border-radius: 8px;
                padding: 15px;
            }}
            #statsFrame {{
                background-color: transparent;
            }}
            #statCard {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
                min-width: 120px;
            }}
            #statValue {{
                color: {config.COLOR_PRIMARY};
            }}
            #statName {{
                color: #7f8c8d;
                font-size: 12px;
            }}
            #filtersFrame {{
                background-color: white;
                border-radius: 8px;
                padding: 15px;
            }}
            #customersTable {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
                gridline-color: #e0e0e0;
            }}
            #customersTable::item {{
                padding: 8px;
            }}
            QHeaderView::section {{
                background-color: {config.COLOR_PRIMARY};
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
            #btnSuccess {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
            #btnSuccess:hover {{
                background-color: #219a52;
            }}
            #btnPrimary {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
            #btnPrimary:hover {{
                background-color: #2980b9;
            }}
            #btnSecondary {{
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
            #btnSecondary:hover {{
                background-color: #7f8c8d;
            }}
            QLineEdit {{
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 13px;
            }}
            QComboBox {{
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 13px;
                min-width: 120px;
            }}
        """)
