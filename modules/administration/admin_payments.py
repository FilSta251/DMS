# -*- coding: utf-8 -*-
"""
Modul Administrativa - Správa plateb a pohledávek (PRODUKČNÍ VERZE)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QFrame,
                             QComboBox, QLineEdit, QDateEdit, QHeaderView,
                             QMessageBox, QDialog, QFormLayout, QTextEdit,
                             QSpinBox, QDoubleSpinBox, QFileDialog, QCheckBox,
                             QGroupBox, QTabWidget, QScrollArea, QProgressBar)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, timedelta, date
from pathlib import Path
import config
from database_manager import db


class PaymentsWidget(QWidget):
    """Widget pro správu plateb a pohledávek"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Statistiky nahoře
        self.create_stats_panel(layout)

        # Záložky
        tabs = QTabWidget()

        # Záložka: Přehled plateb
        self.tab_payments = self.create_payments_tab()
        tabs.addTab(self.tab_payments, "💳 Přehled plateb")

        # Záložka: Pohledávky
        self.tab_receivables = self.create_receivables_tab()
        tabs.addTab(self.tab_receivables, "📊 Pohledávky")

        # Záložka: Závazky
        self.tab_payables = self.create_payables_tab()
        tabs.addTab(self.tab_payables, "📉 Závazky")

        # Záložka: Cash flow predikce
        self.tab_cashflow = self.create_cashflow_tab()
        tabs.addTab(self.tab_cashflow, "💰 Cash Flow")

        layout.addWidget(tabs)

    def create_stats_panel(self, parent_layout):
        """Panel s rychlými statistikami"""
        stats_frame = QFrame()
        stats_frame.setObjectName("statsFrame")
        stats_layout = QHBoxLayout(stats_frame)

        # Definice statistik
        stats = [
            ("📊 Celkové pohledávky", "0 Kč", "receivables", config.COLOR_WARNING),
            ("📉 Celkové závazky", "0 Kč", "payables", config.COLOR_DANGER),
            ("⏱️ Průměrná doba inkasa", "0 dní", "avg_collection", config.COLOR_SECONDARY),
            ("⚠️ Po splatnosti", "0%", "overdue_percent", config.COLOR_DANGER),
            ("💰 Cash flow (30 dní)", "0 Kč", "cashflow_30", config.COLOR_SUCCESS),
        ]

        self.stat_labels = {}

        for title, value, key, color in stats:
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(15, 10, 15, 10)

            title_label = QLabel(title)
            title_font = QFont()
            title_font.setPointSize(9)
            title_label.setFont(title_font)
            title_label.setStyleSheet("color: #7f8c8d;")

            value_label = QLabel(value)
            value_font = QFont()
            value_font.setPointSize(14)
            value_font.setBold(True)
            value_label.setFont(value_font)
            value_label.setStyleSheet(f"color: {color};")

            self.stat_labels[key] = value_label

            stat_layout.addWidget(title_label)
            stat_layout.addWidget(value_label)

            stat_widget.setStyleSheet("""
                QWidget {
                    background-color: white;
                    border-radius: 8px;
                    border: 1px solid #e0e0e0;
                }
            """)

            stats_layout.addWidget(stat_widget)

        parent_layout.addWidget(stats_frame)

    def create_payments_tab(self):
        """Záložka: Přehled plateb"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filtry
        filters_frame = QFrame()
        filters_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        filters_layout = QHBoxLayout(filters_frame)

        # Období
        period_label = QLabel("Období:")
        self.payments_period_combo = QComboBox()
        self.payments_period_combo.addItems([
            "Tento měsíc",
            "Poslední 3 měsíce",
            "Tento rok",
            "Vlastní"
        ])
        self.payments_period_combo.currentTextChanged.connect(self.filter_payments)
        filters_layout.addWidget(period_label)
        filters_layout.addWidget(self.payments_period_combo)

        # Datum od/do
        self.payments_date_from = QDateEdit()
        self.payments_date_from.setDate(QDate.currentDate().addMonths(-1))
        self.payments_date_from.setCalendarPopup(True)
        self.payments_date_from.setDisplayFormat("dd.MM.yyyy")
        self.payments_date_from.dateChanged.connect(self.filter_payments)
        filters_layout.addWidget(QLabel("Od:"))
        filters_layout.addWidget(self.payments_date_from)

        self.payments_date_to = QDateEdit()
        self.payments_date_to.setDate(QDate.currentDate())
        self.payments_date_to.setCalendarPopup(True)
        self.payments_date_to.setDisplayFormat("dd.MM.yyyy")
        self.payments_date_to.dateChanged.connect(self.filter_payments)
        filters_layout.addWidget(QLabel("Do:"))
        filters_layout.addWidget(self.payments_date_to)

        # Typ faktury
        type_label = QLabel("Typ:")
        self.payments_type_combo = QComboBox()
        self.payments_type_combo.addItems([
            "Všechny",
            "Příchozí platby (vydané faktury)",
            "Odchozí platby (přijaté faktury)"
        ])
        self.payments_type_combo.currentTextChanged.connect(self.filter_payments)
        filters_layout.addWidget(type_label)
        filters_layout.addWidget(self.payments_type_combo)

        # Vyhledávání
        search_label = QLabel("Hledat:")
        self.payments_search = QLineEdit()
        self.payments_search.setPlaceholderText("Číslo faktury, zákazník...")
        self.payments_search.textChanged.connect(self.filter_payments)
        filters_layout.addWidget(search_label)
        filters_layout.addWidget(self.payments_search)

        filters_layout.addStretch()
        layout.addWidget(filters_frame)

        # Tlačítka akcí
        buttons_layout = QHBoxLayout()

        import_btn = QPushButton("📥 Import bankovního výpisu")
        import_btn.clicked.connect(self.import_bank_statement)
        import_btn.setStyleSheet(f"background-color: {config.COLOR_SECONDARY}; color: white; padding: 8px 15px;")
        buttons_layout.addWidget(import_btn)

        pair_btn = QPushButton("🔗 Spárovat platby")
        pair_btn.clicked.connect(self.pair_payments)
        buttons_layout.addWidget(pair_btn)

        export_btn = QPushButton("📤 Export")
        export_btn.clicked.connect(self.export_payments)
        buttons_layout.addWidget(export_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # Tabulka plateb
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(8)
        self.payments_table.setHorizontalHeaderLabels([
            "Datum platby",
            "Číslo faktury",
            "Partner",
            "Částka",
            "Způsob platby",
            "Typ",
            "Spárováno",
            "Poznámka"
        ])
        self.payments_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.payments_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.payments_table.setAlternatingRowColors(True)
        layout.addWidget(self.payments_table)

        return widget

    def create_receivables_tab(self):
        """Záložka: Pohledávky"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filtry
        filters_layout = QHBoxLayout()

        status_label = QLabel("Stav:")
        self.receivables_status_combo = QComboBox()
        self.receivables_status_combo.addItems([
            "Všechny",
            "V termínu",
            "Po splatnosti (1-30 dní)",
            "Po splatnosti (31-60 dní)",
            "Po splatnosti (60+ dní)"
        ])
        self.receivables_status_combo.currentTextChanged.connect(self.filter_receivables)
        filters_layout.addWidget(status_label)
        filters_layout.addWidget(self.receivables_status_combo)

        search_label = QLabel("Hledat:")
        self.receivables_search = QLineEdit()
        self.receivables_search.setPlaceholderText("Zákazník, číslo faktury...")
        self.receivables_search.textChanged.connect(self.filter_receivables)
        filters_layout.addWidget(search_label)
        filters_layout.addWidget(self.receivables_search)

        filters_layout.addStretch()
        layout.addLayout(filters_layout)

        # Tlačítka akcí
        buttons_layout = QHBoxLayout()

        reminder_1_btn = QPushButton("📧 Odeslat 1. upomínku")
        reminder_1_btn.clicked.connect(lambda: self.send_reminder(1))
        buttons_layout.addWidget(reminder_1_btn)

        reminder_2_btn = QPushButton("📧 Odeslat 2. upomínku")
        reminder_2_btn.clicked.connect(lambda: self.send_reminder(2))
        buttons_layout.addWidget(reminder_2_btn)

        reminder_3_btn = QPushButton("📧 Odeslat 3. upomínku")
        reminder_3_btn.clicked.connect(lambda: self.send_reminder(3))
        reminder_3_btn.setStyleSheet(f"background-color: {config.COLOR_DANGER}; color: white;")
        buttons_layout.addWidget(reminder_3_btn)

        export_btn = QPushButton("📤 Export pohledávek")
        export_btn.clicked.connect(self.export_receivables)
        buttons_layout.addWidget(export_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # Tabulka pohledávek
        self.receivables_table = QTableWidget()
        self.receivables_table.setColumnCount(9)
        self.receivables_table.setHorizontalHeaderLabels([
            "Číslo faktury",
            "Zákazník",
            "Datum vystavení",
            "Datum splatnosti",
            "Dní po splatnosti",
            "Částka celkem",
            "Nezaplaceno",
            "Upomínka",
            "Akce"
        ])
        self.receivables_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.receivables_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.receivables_table.setAlternatingRowColors(True)
        layout.addWidget(self.receivables_table)

        return widget

    def create_payables_tab(self):
        """Záložka: Závazky"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filtry
        filters_layout = QHBoxLayout()

        status_label = QLabel("Stav:")
        self.payables_status_combo = QComboBox()
        self.payables_status_combo.addItems([
            "Všechny",
            "V termínu",
            "Po splatnosti",
            "Zaplacené"
        ])
        self.payables_status_combo.currentTextChanged.connect(self.filter_payables)
        filters_layout.addWidget(status_label)
        filters_layout.addWidget(self.payables_status_combo)

        priority_label = QLabel("Priorita:")
        self.payables_priority_combo = QComboBox()
        self.payables_priority_combo.addItems([
            "Všechny",
            "Vysoká",
            "Střední",
            "Nízká"
        ])
        self.payables_priority_combo.currentTextChanged.connect(self.filter_payables)
        filters_layout.addWidget(priority_label)
        filters_layout.addWidget(self.payables_priority_combo)

        search_label = QLabel("Hledat:")
        self.payables_search = QLineEdit()
        self.payables_search.setPlaceholderText("Dodavatel, číslo faktury...")
        self.payables_search.textChanged.connect(self.filter_payables)
        filters_layout.addWidget(search_label)
        filters_layout.addWidget(self.payables_search)

        filters_layout.addStretch()
        layout.addLayout(filters_layout)

        # Tlačítka akcí
        buttons_layout = QHBoxLayout()

        pay_btn = QPushButton("💳 Zaznamenat platbu")
        pay_btn.clicked.connect(self.record_payable_payment)
        pay_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 15px;")
        buttons_layout.addWidget(pay_btn)

        set_priority_btn = QPushButton("⚠️ Nastavit prioritu")
        set_priority_btn.clicked.connect(self.set_payment_priority)
        buttons_layout.addWidget(set_priority_btn)

        export_btn = QPushButton("📤 Export závazků")
        export_btn.clicked.connect(self.export_payables)
        buttons_layout.addWidget(export_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # Tabulka závazků
        self.payables_table = QTableWidget()
        self.payables_table.setColumnCount(8)
        self.payables_table.setHorizontalHeaderLabels([
            "Číslo faktury",
            "Dodavatel",
            "Datum vystavení",
            "Datum splatnosti",
            "Zbývá dní",
            "Částka celkem",
            "Nezaplaceno",
            "Priorita"
        ])
        self.payables_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.payables_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.payables_table.setAlternatingRowColors(True)
        layout.addWidget(self.payables_table)

        return widget

    def create_cashflow_tab(self):
        """Záložka: Cash flow predikce"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info
        info_label = QLabel("Predikce cash flow na základě splatných faktur")
        info_label.setStyleSheet("font-size: 12pt; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # Období predikce
        period_layout = QHBoxLayout()
        period_label = QLabel("Období predikce:")
        self.cashflow_period = QComboBox()
        self.cashflow_period.addItems([
            "7 dní",
            "14 dní",
            "30 dní",
            "60 dní",
            "90 dní"
        ])
        self.cashflow_period.setCurrentIndex(2)  # 30 dní
        self.cashflow_period.currentTextChanged.connect(self.update_cashflow)
        period_layout.addWidget(period_label)
        period_layout.addWidget(self.cashflow_period)
        period_layout.addStretch()
        layout.addLayout(period_layout)

        # Přehled
        overview_frame = QFrame()
        overview_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        overview_layout = QHBoxLayout(overview_frame)

        # Příjmy
        income_group = QGroupBox("💰 Očekávané příjmy")
        income_layout = QVBoxLayout(income_group)
        self.cashflow_income_label = QLabel("0,00 Kč")
        self.cashflow_income_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #27ae60;")
        income_layout.addWidget(self.cashflow_income_label)
        self.cashflow_income_count = QLabel("0 faktur")
        income_layout.addWidget(self.cashflow_income_count)
        overview_layout.addWidget(income_group)

        # Výdaje
        expense_group = QGroupBox("💸 Očekávané výdaje")
        expense_layout = QVBoxLayout(expense_group)
        self.cashflow_expense_label = QLabel("0,00 Kč")
        self.cashflow_expense_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #e74c3c;")
        expense_layout.addWidget(self.cashflow_expense_label)
        self.cashflow_expense_count = QLabel("0 faktur")
        expense_layout.addWidget(self.cashflow_expense_count)
        overview_layout.addWidget(expense_group)

        # Rozdíl
        balance_group = QGroupBox("📊 Rozdíl (Cash Flow)")
        balance_layout = QVBoxLayout(balance_group)
        self.cashflow_balance_label = QLabel("0,00 Kč")
        self.cashflow_balance_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #3498db;")
        balance_layout.addWidget(self.cashflow_balance_label)
        self.cashflow_balance_trend = QLabel("")
        balance_layout.addWidget(self.cashflow_balance_trend)
        overview_layout.addWidget(balance_group)

        layout.addWidget(overview_frame)

        # Tabulka detailů
        detail_label = QLabel("Detail podle týdnů:")
        detail_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        layout.addWidget(detail_label)

        self.cashflow_table = QTableWidget()
        self.cashflow_table.setColumnCount(5)
        self.cashflow_table.setHorizontalHeaderLabels([
            "Období",
            "Příjmy",
            "Výdaje",
            "Rozdíl",
            "Kumulativní"
        ])
        self.cashflow_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.cashflow_table)

        return widget

    # =====================================================
    # NAČÍTÁNÍ DAT
    # =====================================================

    def load_data(self):
        """Načtení všech dat"""
        self.load_statistics()
        self.load_payments()
        self.load_receivables()
        self.load_payables()
        self.update_cashflow()

    def load_statistics(self):
        """Načtení statistik"""
        try:
            # Celkové pohledávky
            query_receivables = """
                SELECT COALESCE(SUM(total_with_vat - paid_amount), 0) as total
                FROM invoices
                WHERE invoice_type = 'issued'
                  AND status IN ('unpaid', 'partial', 'overdue')
            """
            result = db.fetch_one(query_receivables)
            receivables = result["total"] if result else 0

            # Celkové závazky
            query_payables = """
                SELECT COALESCE(SUM(total_with_vat - paid_amount), 0) as total
                FROM invoices
                WHERE invoice_type = 'received'
                  AND status IN ('unpaid', 'partial', 'overdue')
            """
            result = db.fetch_one(query_payables)
            payables = result["total"] if result else 0

            # Průměrná doba inkasa (dny mezi vystavením a zaplacením)
            query_avg = """
                SELECT AVG(
                    JULIANDAY(
                        COALESCE(
                            (SELECT MAX(payment_date) FROM payments WHERE invoice_id = i.id),
                            DATE('now')
                        )
                    ) - JULIANDAY(i.issue_date)
                ) as avg_days
                FROM invoices i
                WHERE i.invoice_type = 'issued'
                  AND i.status IN ('paid', 'partial')
                  AND i.issue_date >= DATE('now', '-365 days')
            """
            result = db.fetch_one(query_avg)
            avg_collection = int(result["avg_days"]) if result and result["avg_days"] else 0

            # Procento po splatnosti
            query_overdue = """
                SELECT
                    COUNT(*) as total_count,
                    SUM(CASE WHEN due_date < DATE('now') THEN 1 ELSE 0 END) as overdue_count
                FROM invoices
                WHERE invoice_type = 'issued'
                  AND status IN ('unpaid', 'partial', 'overdue')
            """
            result = db.fetch_one(query_overdue)
            if result and result["total_count"] > 0:
                overdue_percent = (result["overdue_count"] / result["total_count"]) * 100
            else:
                overdue_percent = 0

            # Cash flow 30 dní
            query_cashflow = """
                SELECT
                    COALESCE(SUM(CASE WHEN invoice_type = 'issued' THEN (total_with_vat - paid_amount) ELSE 0 END), 0) as income,
                    COALESCE(SUM(CASE WHEN invoice_type = 'received' THEN (total_with_vat - paid_amount) ELSE 0 END), 0) as expense
                FROM invoices
                WHERE status IN ('unpaid', 'partial', 'overdue')
                  AND due_date BETWEEN DATE('now') AND DATE('now', '+30 days')
            """
            result = db.fetch_one(query_cashflow)
            if result:
                cashflow = result["income"] - result["expense"]
            else:
                cashflow = 0

            # Aktualizace labelů
            self.stat_labels["receivables"].setText(f"{receivables:,.2f} Kč".replace(",", " "))
            self.stat_labels["payables"].setText(f"{payables:,.2f} Kč".replace(",", " "))
            self.stat_labels["avg_collection"].setText(f"{avg_collection} dní")
            self.stat_labels["overdue_percent"].setText(f"{overdue_percent:.1f}%")
            self.stat_labels["cashflow_30"].setText(f"{cashflow:,.2f} Kč".replace(",", " "))

        except Exception as e:
            print(f"Chyba při načítání statistik: {e}")

    def load_payments(self):
        """Načtení přehledu plateb"""
        try:
            query = """
                SELECT
                    p.payment_date,
                    i.invoice_number,
                    CASE
                        WHEN i.invoice_type = 'issued' THEN
                            COALESCE(c.first_name || ' ' || c.last_name, c.company, 'Neznámý')
                        ELSE
                            COALESCE(i.supplier_name, 'Neznámý dodavatel')
                    END as partner_name,
                    p.amount,
                    p.payment_method,
                    i.invoice_type,
                    p.note
                FROM payments p
                JOIN invoices i ON p.invoice_id = i.id
                LEFT JOIN customers c ON i.customer_id = c.id
                ORDER BY p.payment_date DESC
                LIMIT 500
            """
            payments = db.fetch_all(query)

            self.payments_table.setRowCount(len(payments))

            for row, payment in enumerate(payments):
                # Datum
                payment_date = datetime.fromisoformat(payment["payment_date"]).strftime("%d.%m.%Y")
                self.payments_table.setItem(row, 0, QTableWidgetItem(payment_date))

                # Číslo faktury
                self.payments_table.setItem(row, 1, QTableWidgetItem(payment["invoice_number"]))

                # Partner
                self.payments_table.setItem(row, 2, QTableWidgetItem(payment["partner_name"]))

                # Částka
                amount_item = QTableWidgetItem(f"{payment['amount']:,.2f} Kč".replace(",", " "))
                amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.payments_table.setItem(row, 3, amount_item)

                # Způsob platby
                self.payments_table.setItem(row, 4, QTableWidgetItem(payment["payment_method"] or "-"))

                # Typ
                type_text = "Příjem" if payment["invoice_type"] == "issued" else "Výdaj"
                type_item = QTableWidgetItem(type_text)
                if payment["invoice_type"] == "issued":
                    type_item.setForeground(QColor(config.COLOR_SUCCESS))
                else:
                    type_item.setForeground(QColor(config.COLOR_DANGER))
                self.payments_table.setItem(row, 5, type_item)

                # Spárováno
                paired_item = QTableWidgetItem("✓ Ano")
                paired_item.setForeground(QColor(config.COLOR_SUCCESS))
                self.payments_table.setItem(row, 6, paired_item)

                # Poznámka
                self.payments_table.setItem(row, 7, QTableWidgetItem(payment["note"] or "-"))

        except Exception as e:
            print(f"Chyba při načítání plateb: {e}")

    def load_receivables(self):
        """Načtení pohledávek"""
        try:
            query = """
                SELECT
                    i.id,
                    i.invoice_number,
                    COALESCE(c.first_name || ' ' || c.last_name, c.company, 'Neznámý') as customer_name,
                    i.issue_date,
                    i.due_date,
                    i.total_with_vat,
                    i.paid_amount,
                    (i.total_with_vat - i.paid_amount) as remaining,
                    JULIANDAY(DATE('now')) - JULIANDAY(i.due_date) as days_overdue,
                    c.email
                FROM invoices i
                LEFT JOIN customers c ON i.customer_id = c.id
                WHERE i.invoice_type = 'issued'
                  AND i.status IN ('unpaid', 'partial', 'overdue')
                  AND (i.total_with_vat - i.paid_amount) > 0
                ORDER BY i.due_date ASC
            """
            receivables = db.fetch_all(query)

            self.receivables_table.setRowCount(len(receivables))

            for row, rec in enumerate(receivables):
                # Číslo faktury
                self.receivables_table.setItem(row, 0, QTableWidgetItem(rec["invoice_number"]))

                # Zákazník
                self.receivables_table.setItem(row, 1, QTableWidgetItem(rec["customer_name"]))

                # Datum vystavení
                issue_date = datetime.fromisoformat(rec["issue_date"]).strftime("%d.%m.%Y")
                self.receivables_table.setItem(row, 2, QTableWidgetItem(issue_date))

                # Datum splatnosti
                due_date = datetime.fromisoformat(rec["due_date"]).strftime("%d.%m.%Y")
                due_item = QTableWidgetItem(due_date)
                if rec["days_overdue"] > 0:
                    due_item.setForeground(QColor(config.COLOR_DANGER))
                self.receivables_table.setItem(row, 3, due_item)

                # Dní po splatnosti
                days_overdue = max(0, int(rec["days_overdue"]))
                days_item = QTableWidgetItem(str(days_overdue) if days_overdue > 0 else "-")
                days_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if days_overdue > 60:
                    days_item.setBackground(QColor(config.COLOR_DANGER))
                    days_item.setForeground(QColor("white"))
                elif days_overdue > 30:
                    days_item.setBackground(QColor(config.COLOR_WARNING))
                    days_item.setForeground(QColor("white"))
                self.receivables_table.setItem(row, 4, days_item)

                # Částka celkem
                total_item = QTableWidgetItem(f"{rec['total_with_vat']:,.2f} Kč".replace(",", " "))
                total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.receivables_table.setItem(row, 5, total_item)

                # Nezaplaceno
                remaining_item = QTableWidgetItem(f"{rec['remaining']:,.2f} Kč".replace(",", " "))
                remaining_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                remaining_item.setForeground(QColor(config.COLOR_DANGER))
                self.receivables_table.setItem(row, 6, remaining_item)

                # Upomínka
                reminder_level = self.calculate_reminder_level(days_overdue)
                reminder_item = QTableWidgetItem(reminder_level)
                reminder_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.receivables_table.setItem(row, 7, reminder_item)

                # Tlačítko akce
                action_btn = QPushButton("📧 Upomínka")
                action_btn.clicked.connect(lambda checked, r=rec: self.send_reminder_for_invoice(r))
                self.receivables_table.setCellWidget(row, 8, action_btn)

        except Exception as e:
            print(f"Chyba při načítání pohledávek: {e}")

    def load_payables(self):
        """Načtení závazků"""
        try:
            query = """
                SELECT
                    i.id,
                    i.invoice_number,
                    COALESCE(i.supplier_name, 'Neznámý dodavatel') as supplier_name,
                    i.issue_date,
                    i.due_date,
                    i.total_with_vat,
                    i.paid_amount,
                    (i.total_with_vat - i.paid_amount) as remaining,
                    JULIANDAY(i.due_date) - JULIANDAY(DATE('now')) as days_remaining
                FROM invoices i
                WHERE i.invoice_type = 'received'
                  AND i.status IN ('unpaid', 'partial', 'overdue')
                  AND (i.total_with_vat - i.paid_amount) > 0
                ORDER BY i.due_date ASC
            """
            payables = db.fetch_all(query)

            self.payables_table.setRowCount(len(payables))

            for row, pay in enumerate(payables):
                # Číslo faktury
                self.payables_table.setItem(row, 0, QTableWidgetItem(pay["invoice_number"]))

                # Dodavatel
                self.payables_table.setItem(row, 1, QTableWidgetItem(pay["supplier_name"]))

                # Datum vystavení
                issue_date = datetime.fromisoformat(pay["issue_date"]).strftime("%d.%m.%Y")
                self.payables_table.setItem(row, 2, QTableWidgetItem(issue_date))

                # Datum splatnosti
                due_date = datetime.fromisoformat(pay["due_date"]).strftime("%d.%m.%Y")
                due_item = QTableWidgetItem(due_date)
                if pay["days_remaining"] < 0:
                    due_item.setForeground(QColor(config.COLOR_DANGER))
                self.payables_table.setItem(row, 3, due_item)

                # Zbývá dní
                days_remaining = int(pay["days_remaining"])
                if days_remaining < 0:
                    days_text = f"Po splatnosti ({abs(days_remaining)} dní)"
                    days_item = QTableWidgetItem(days_text)
                    days_item.setForeground(QColor(config.COLOR_DANGER))
                else:
                    days_item = QTableWidgetItem(str(days_remaining))
                days_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.payables_table.setItem(row, 4, days_item)

                # Částka celkem
                total_item = QTableWidgetItem(f"{pay['total_with_vat']:,.2f} Kč".replace(",", " "))
                total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.payables_table.setItem(row, 5, total_item)

                # Nezaplaceno
                remaining_item = QTableWidgetItem(f"{pay['remaining']:,.2f} Kč".replace(",", " "))
                remaining_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.payables_table.setItem(row, 6, remaining_item)

                # Priorita
                priority = self.calculate_priority(days_remaining, pay['remaining'])
                priority_item = QTableWidgetItem(priority)
                priority_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if priority == "Vysoká":
                    priority_item.setBackground(QColor(config.COLOR_DANGER))
                    priority_item.setForeground(QColor("white"))
                elif priority == "Střední":
                    priority_item.setBackground(QColor(config.COLOR_WARNING))
                self.payables_table.setItem(row, 7, priority_item)

        except Exception as e:
            print(f"Chyba při načítání závazků: {e}")

    def update_cashflow(self):
        """Aktualizace cash flow predikce"""
        try:
            # Získat období
            period_text = self.cashflow_period.currentText()
            days = int(period_text.split()[0])

            # Příjmy (splatné vydané faktury)
            query_income = """
                SELECT
                    COALESCE(SUM(total_with_vat - paid_amount), 0) as total,
                    COUNT(*) as count
                FROM invoices
                WHERE invoice_type = 'issued'
                  AND status IN ('unpaid', 'partial', 'overdue')
                  AND due_date BETWEEN DATE('now') AND DATE('now', '+' || ? || ' days')
            """
            result = db.fetch_one(query_income, (days,))
            income = result["total"] if result else 0
            income_count = result["count"] if result else 0

            # Výdaje (splatné přijaté faktury)
            query_expense = """
                SELECT
                    COALESCE(SUM(total_with_vat - paid_amount), 0) as total,
                    COUNT(*) as count
                FROM invoices
                WHERE invoice_type = 'received'
                  AND status IN ('unpaid', 'partial', 'overdue')
                  AND due_date BETWEEN DATE('now') AND DATE('now', '+' || ? || ' days')
            """
            result = db.fetch_one(query_expense, (days,))
            expense = result["total"] if result else 0
            expense_count = result["count"] if result else 0

            # Rozdíl
            balance = income - expense

            # Aktualizace labelů
            self.cashflow_income_label.setText(f"{income:,.2f} Kč".replace(",", " "))
            self.cashflow_income_count.setText(f"{income_count} faktur")

            self.cashflow_expense_label.setText(f"{expense:,.2f} Kč".replace(",", " "))
            self.cashflow_expense_count.setText(f"{expense_count} faktur")

            self.cashflow_balance_label.setText(f"{balance:,.2f} Kč".replace(",", " "))
            if balance > 0:
                self.cashflow_balance_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #27ae60;")
                self.cashflow_balance_trend.setText("↗ Pozitivní")
                self.cashflow_balance_trend.setStyleSheet("color: #27ae60;")
            elif balance < 0:
                self.cashflow_balance_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #e74c3c;")
                self.cashflow_balance_trend.setText("↘ Negativní")
                self.cashflow_balance_trend.setStyleSheet("color: #e74c3c;")
            else:
                self.cashflow_balance_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #95a5a6;")
                self.cashflow_balance_trend.setText("→ Vyrovnaný")
                self.cashflow_balance_trend.setStyleSheet("color: #95a5a6;")

            # Detailní tabulka po týdnech
            self.load_cashflow_details(days)

        except Exception as e:
            print(f"Chyba při aktualizaci cash flow: {e}")

    def load_cashflow_details(self, total_days):
        """Načtení detailů cash flow po týdnech"""
        try:
            weeks = (total_days + 6) // 7  # Zaokrouhlení nahoru
            self.cashflow_table.setRowCount(weeks)

            cumulative = 0

            for week in range(weeks):
                start_day = week * 7
                end_day = min((week + 1) * 7, total_days)

                # Příjmy v tomto týdnu
                query_income = """
                    SELECT COALESCE(SUM(total_with_vat - paid_amount), 0) as total
                    FROM invoices
                    WHERE invoice_type = 'issued'
                      AND status IN ('unpaid', 'partial', 'overdue')
                      AND due_date BETWEEN DATE('now', '+' || ? || ' days')
                                       AND DATE('now', '+' || ? || ' days')
                """
                result = db.fetch_one(query_income, (start_day, end_day))
                income = result["total"] if result else 0

                # Výdaje v tomto týdnu
                query_expense = """
                    SELECT COALESCE(SUM(total_with_vat - paid_amount), 0) as total
                    FROM invoices
                    WHERE invoice_type = 'received'
                      AND status IN ('unpaid', 'partial', 'overdue')
                      AND due_date BETWEEN DATE('now', '+' || ? || ' days')
                                       AND DATE('now', '+' || ? || ' days')
                """
                result = db.fetch_one(query_expense, (start_day, end_day))
                expense = result["total"] if result else 0

                difference = income - expense
                cumulative += difference

                # Období
                start_date = (date.today() + timedelta(days=start_day)).strftime("%d.%m")
                end_date = (date.today() + timedelta(days=end_day-1)).strftime("%d.%m")
                period_item = QTableWidgetItem(f"Týden {week+1} ({start_date} - {end_date})")
                self.cashflow_table.setItem(week, 0, period_item)

                # Příjmy
                income_item = QTableWidgetItem(f"{income:,.2f} Kč".replace(",", " "))
                income_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                income_item.setForeground(QColor(config.COLOR_SUCCESS))
                self.cashflow_table.setItem(week, 1, income_item)

                # Výdaje
                expense_item = QTableWidgetItem(f"{expense:,.2f} Kč".replace(",", " "))
                expense_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                expense_item.setForeground(QColor(config.COLOR_DANGER))
                self.cashflow_table.setItem(week, 2, expense_item)

                # Rozdíl
                diff_item = QTableWidgetItem(f"{difference:,.2f} Kč".replace(",", " "))
                diff_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if difference > 0:
                    diff_item.setForeground(QColor(config.COLOR_SUCCESS))
                elif difference < 0:
                    diff_item.setForeground(QColor(config.COLOR_DANGER))
                self.cashflow_table.setItem(week, 3, diff_item)

                # Kumulativní
                cumul_item = QTableWidgetItem(f"{cumulative:,.2f} Kč".replace(",", " "))
                cumul_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                cumul_font = QFont()
                cumul_font.setBold(True)
                cumul_item.setFont(cumul_font)
                if cumulative > 0:
                    cumul_item.setForeground(QColor(config.COLOR_SUCCESS))
                elif cumulative < 0:
                    cumul_item.setForeground(QColor(config.COLOR_DANGER))
                self.cashflow_table.setItem(week, 4, cumul_item)

        except Exception as e:
            print(f"Chyba při načítání detailů cash flow: {e}")

    # =====================================================
    # FILTRY
    # =====================================================

    def filter_payments(self):
        """Filtrování plateb"""
        # TODO: Implementovat filtrování podle období a typu
        pass

    def filter_receivables(self):
        """Filtrování pohledávek"""
        search_text = self.receivables_search.text().lower()
        status_filter = self.receivables_status_combo.currentText()

        for row in range(self.receivables_table.rowCount()):
            show = True

            # Filtr vyhledávání
            if search_text:
                invoice_number = self.receivables_table.item(row, 0).text().lower()
                customer = self.receivables_table.item(row, 1).text().lower()
                if search_text not in invoice_number and search_text not in customer:
                    show = False

            # Filtr stavu (podle dní po splatnosti)
            if status_filter != "Všechny":
                days_item = self.receivables_table.item(row, 4)
                if days_item:
                    days_text = days_item.text()
                    if days_text != "-":
                        days = int(days_text)
                        if status_filter == "V termínu" and days > 0:
                            show = False
                        elif status_filter == "Po splatnosti (1-30 dní)" and not (1 <= days <= 30):
                            show = False
                        elif status_filter == "Po splatnosti (31-60 dní)" and not (31 <= days <= 60):
                            show = False
                        elif status_filter == "Po splatnosti (60+ dní)" and days <= 60:
                            show = False

            self.receivables_table.setRowHidden(row, not show)

    def filter_payables(self):
        """Filtrování závazků"""
        search_text = self.payables_search.text().lower()

        for row in range(self.payables_table.rowCount()):
            show = True

            if search_text:
                invoice_number = self.payables_table.item(row, 0).text().lower()
                supplier = self.payables_table.item(row, 1).text().lower()
                if search_text not in invoice_number and search_text not in supplier:
                    show = False

            self.payables_table.setRowHidden(row, not show)

    # =====================================================
    # AKCE
    # =====================================================

    def import_bank_statement(self):
        """Import bankovního výpisu"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Vyberte bankovní výpis",
            "",
            "CSV soubory (*.csv);;PDF soubory (*.pdf);;Všechny soubory (*.*)"
        )

        if not file_path:
            return

        # TODO: Implementovat parser bankovních výpisů
        QMessageBox.information(
            self,
            "Import výpisu",
            "Funkce importu bankovního výpisu bude implementována.\n\n"
            "Bude podporovat:\n"
            "- CSV výpisy (různé formáty bank)\n"
            "- PDF výpisy (s OCR)\n"
            "- Automatické rozpoznání plateb\n"
            "- Párování s fakturami podle VS"
        )

    def pair_payments(self):
        """Automatické párování plateb s fakturami"""
        QMessageBox.information(
            self,
            "Párování plateb",
            "Funkce automatického párování plateb bude implementována.\n\n"
            "Algoritmus:\n"
            "1. Porovnání částek\n"
            "2. Shoda variabilního symbolu\n"
            "3. Shoda data splatnosti ±5 dní\n"
            "4. Návrh možných párování"
        )

    def send_reminder(self, level):
        """Odeslání upomínek vybraného stupně"""
        selected_rows = set()
        for item in self.receivables_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            QMessageBox.warning(self, "Upozornění", "Vyberte faktury pro odeslání upomínek.")
            return

        count = len(selected_rows)
        reply = QMessageBox.question(
            self,
            "Odeslat upomínky",
            f"Chcete odeslat {level}. upomínku pro {count} faktur?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implementovat skutečné odesílání upomínek
            QMessageBox.information(
                self,
                "Upomínky",
                f"Bylo by odesláno {count} upomínek {level}. stupně.\n\n"
                "Funkce bude zahrnovat:\n"
                "- Generování PDF upomínky\n"
                "- Odeslání emailem\n"
                "- Záznam do historie"
            )

    def send_reminder_for_invoice(self, invoice):
        """Odeslání upomínky pro konkrétní fakturu"""
        QMessageBox.information(
            self,
            "Upomínka",
            f"Odeslání upomínky pro fakturu {invoice['invoice_number']} bude implementováno."
        )

    def record_payable_payment(self):
        """Zaznamenání platby závazku"""
        current_row = self.payables_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Upozornění", "Vyberte fakturu pro zaznamenání platby.")
            return

        invoice_number = self.payables_table.item(current_row, 0).text()
        remaining_text = self.payables_table.item(current_row, 6).text()
        remaining = float(remaining_text.replace(" Kč", "").replace(" ", ""))

        # TODO: Otevřít dialog pro zaznamenání platby
        QMessageBox.information(
            self,
            "Platba",
            f"Dialog pro zaznamenání platby faktury {invoice_number} bude implementován.\n\n"
            f"Zbývá uhradit: {remaining:,.2f} Kč".replace(",", " ")
        )

    def set_payment_priority(self):
        """Nastavení priority platby"""
        current_row = self.payables_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Upozornění", "Vyberte fakturu.")
            return

        # Dialog pro výběr priority
        dialog = QDialog(self)
        dialog.setWindowTitle("Nastavit prioritu")
        layout = QVBoxLayout(dialog)

        combo = QComboBox()
        combo.addItems(["Vysoká", "Střední", "Nízká"])
        layout.addWidget(combo)

        buttons_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(dialog.reject)
        buttons_layout.addWidget(ok_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            priority = combo.currentText()
            # TODO: Uložit prioritu do databáze
            self.payables_table.item(current_row, 7).setText(priority)

    def export_payments(self):
        """Export plateb"""
        QMessageBox.information(self, "Export", "Export plateb do Excel bude implementován.")

    def export_receivables(self):
        """Export pohledávek"""
        QMessageBox.information(self, "Export", "Export pohledávek do Excel bude implementován.")

    def export_payables(self):
        """Export závazků"""
        QMessageBox.information(self, "Export", "Export závazků do Excel bude implementován.")

    # =====================================================
    # POMOCNÉ METODY
    # =====================================================

    def calculate_reminder_level(self, days_overdue):
        """Výpočet stupně upomínky"""
        if days_overdue <= 0:
            return "-"
        elif days_overdue <= 14:
            return "1. upomínka"
        elif days_overdue <= 30:
            return "2. upomínka"
        else:
            return "3. upomínka"

    def calculate_priority(self, days_remaining, amount):
        """Výpočet priority platby"""
        if days_remaining < 0:
            return "Vysoká"  # Po splatnosti
        elif days_remaining <= 7 or amount > 50000:
            return "Vysoká"  # Brzy splatné nebo vysoká částka
        elif days_remaining <= 14:
            return "Střední"
        else:
            return "Nízká"

    def refresh(self):
        """Obnovení dat"""
        self.load_data()
