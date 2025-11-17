# -*- coding: utf-8 -*-
"""
Modul Administrativa - Účetní přehledy (PRODUKČNÍ VERZE)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QFrame,
                             QComboBox, QLineEdit, QDateEdit, QHeaderView,
                             QMessageBox, QDialog, QFormLayout, QTextEdit,
                             QSpinBox, QDoubleSpinBox, QFileDialog, QCheckBox,
                             QGroupBox, QTabWidget, QScrollArea, QProgressBar,
                             QSplitter)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QPen
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QLineSeries, QBarSeries, QBarSet, QValueAxis, QBarCategoryAxis
from datetime import datetime, timedelta, date
from pathlib import Path
import config
from database_manager import db


class AccountingWidget(QWidget):
    """Widget pro účetní přehledy"""

    def __init__(self):
        super().__init__()
        self.current_period = {"from": None, "to": None}
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Výběr období
        self.create_period_selector(layout)

        # Statistiky
        self.create_stats_panel(layout)

        # Záložky
        tabs = QTabWidget()

        # Záložka: Přehled účetnictví
        self.tab_overview = self.create_overview_tab()
        tabs.addTab(self.tab_overview, "💰 Přehled účetnictví")

        # Záložka: Peněžní toky
        self.tab_cashflow = self.create_cashflow_tab()
        tabs.addTab(self.tab_cashflow, "💵 Peněžní toky")

        # Záložka: Nákladové středisko
        self.tab_costs = self.create_costs_tab()
        tabs.addTab(self.tab_costs, "📊 Nákladové středisko")

        # Záložka: Přehledy pro účetní
        self.tab_reports = self.create_reports_tab()
        tabs.addTab(self.tab_reports, "📋 Přehledy pro účetní")

        layout.addWidget(tabs)

    def create_period_selector(self, parent_layout):
        """Výběr období"""
        period_frame = QFrame()
        period_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        period_layout = QHBoxLayout(period_frame)

        # Předvolené období
        period_label = QLabel("Období:")
        period_label_font = QFont()
        period_label_font.setBold(True)
        period_label.setFont(period_label_font)
        period_layout.addWidget(period_label)

        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "Tento měsíc",
            "Minulý měsíc",
            "Tento rok",
            "Minulý rok",
            "Poslední 3 měsíce",
            "Poslední 6 měsíců",
            "Poslední 12 měsíců",
            "Vlastní období"
        ])
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        period_layout.addWidget(self.period_combo)

        # Datum od
        period_layout.addWidget(QLabel("Od:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd.MM.yyyy")
        self.date_from.dateChanged.connect(self.load_data)
        period_layout.addWidget(self.date_from)

        # Datum do
        period_layout.addWidget(QLabel("Do:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd.MM.yyyy")
        self.date_to.dateChanged.connect(self.load_data)
        period_layout.addWidget(self.date_to)

        # Tlačítko refresh
        refresh_btn = QPushButton("🔄 Aktualizovat")
        refresh_btn.clicked.connect(self.load_data)
        period_layout.addWidget(refresh_btn)

        period_layout.addStretch()

        parent_layout.addWidget(period_frame)

    def create_stats_panel(self, parent_layout):
        """Panel s rychlými statistikami"""
        stats_frame = QFrame()
        stats_frame.setObjectName("statsFrame")
        stats_layout = QHBoxLayout(stats_frame)

        stats = [
            ("💰 Celkové příjmy", "0 Kč", "income", config.COLOR_SUCCESS),
            ("💸 Celkové výdaje", "0 Kč", "expenses", config.COLOR_DANGER),
            ("📊 Zisk/Ztráta", "0 Kč", "profit", config.COLOR_SECONDARY),
            ("📈 Marže", "0%", "margin", config.COLOR_WARNING),
        ]

        self.stat_labels = {}

        for title, value, key, color in stats:
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(15, 10, 15, 10)

            title_label = QLabel(title)
            title_font = QFont()
            title_font.setPointSize(10)
            title_label.setFont(title_font)
            title_label.setStyleSheet("color: #7f8c8d;")

            value_label = QLabel(value)
            value_font = QFont()
            value_font.setPointSize(16)
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

    def create_overview_tab(self):
        """Záložka: Přehled účetnictví"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Rozdělení na sloupce
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Levý panel - Příjmy
        income_group = QGroupBox("💰 Příjmy")
        income_layout = QVBoxLayout(income_group)

        self.income_table = QTableWidget()
        self.income_table.setColumnCount(2)
        self.income_table.setHorizontalHeaderLabels(["Kategorie", "Částka"])
        self.income_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.income_table.setMaximumHeight(300)
        income_layout.addWidget(self.income_table)

        self.total_income_label = QLabel("Celkem: 0 Kč")
        income_font = QFont()
        income_font.setBold(True)
        income_font.setPointSize(12)
        self.total_income_label.setFont(income_font)
        self.total_income_label.setStyleSheet(f"color: {config.COLOR_SUCCESS}; padding: 10px;")
        income_layout.addWidget(self.total_income_label)

        splitter.addWidget(income_group)

        # Pravý panel - Výdaje
        expenses_group = QGroupBox("💸 Výdaje")
        expenses_layout = QVBoxLayout(expenses_group)

        self.expenses_table = QTableWidget()
        self.expenses_table.setColumnCount(2)
        self.expenses_table.setHorizontalHeaderLabels(["Kategorie", "Částka"])
        self.expenses_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.expenses_table.setMaximumHeight(300)
        expenses_layout.addWidget(self.expenses_table)

        self.total_expenses_label = QLabel("Celkem: 0 Kč")
        expenses_font = QFont()
        expenses_font.setBold(True)
        expenses_font.setPointSize(12)
        self.total_expenses_label.setFont(expenses_font)
        self.total_expenses_label.setStyleSheet(f"color: {config.COLOR_DANGER}; padding: 10px;")
        expenses_layout.addWidget(self.total_expenses_label)

        splitter.addWidget(expenses_group)

        layout.addWidget(splitter)

        # Graf vývoje
        chart_group = QGroupBox("📈 Vývoj příjmů a výdajů v čase")
        chart_layout = QVBoxLayout(chart_group)

        self.overview_chart = QChartView()
        self.overview_chart.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.overview_chart.setMinimumHeight(300)
        chart_layout.addWidget(self.overview_chart)

        layout.addWidget(chart_group)

        # Tlačítka exportu
        export_layout = QHBoxLayout()
        export_layout.addStretch()

        export_excel_btn = QPushButton("📊 Export do Excel")
        export_excel_btn.clicked.connect(self.export_overview_excel)
        export_layout.addWidget(export_excel_btn)

        export_pdf_btn = QPushButton("📄 Export do PDF")
        export_pdf_btn.clicked.connect(self.export_overview_pdf)
        export_layout.addWidget(export_pdf_btn)

        layout.addLayout(export_layout)

        return widget

    def create_cashflow_tab(self):
        """Záložka: Peněžní toky"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Přehled cash flow
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

        # Začátek období
        start_group = QGroupBox("💰 Stav na začátku")
        start_layout = QVBoxLayout(start_group)
        self.cashflow_start_label = QLabel("0 Kč")
        self.cashflow_start_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        start_layout.addWidget(self.cashflow_start_label)
        overview_layout.addWidget(start_group)

        # Příjmy
        income_group = QGroupBox("💵 Příjmy celkem")
        income_layout = QVBoxLayout(income_group)
        self.cashflow_income_label = QLabel("0 Kč")
        self.cashflow_income_label.setStyleSheet(f"font-size: 16pt; font-weight: bold; color: {config.COLOR_SUCCESS};")
        income_layout.addWidget(self.cashflow_income_label)
        overview_layout.addWidget(income_group)

        # Výdaje
        expense_group = QGroupBox("💸 Výdaje celkem")
        expense_layout = QVBoxLayout(expense_group)
        self.cashflow_expense_label = QLabel("0 Kč")
        self.cashflow_expense_label.setStyleSheet(f"font-size: 16pt; font-weight: bold; color: {config.COLOR_DANGER};")
        expense_layout.addWidget(self.cashflow_expense_label)
        overview_layout.addWidget(expense_group)

        # Konec období
        end_group = QGroupBox("💰 Stav na konci")
        end_layout = QVBoxLayout(end_group)
        self.cashflow_end_label = QLabel("0 Kč")
        self.cashflow_end_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #3498db;")
        end_layout.addWidget(self.cashflow_end_label)
        overview_layout.addWidget(end_group)

        layout.addWidget(overview_frame)

        # Detailní tabulka
        detail_group = QGroupBox("Detailní přehled peněžních toků")
        detail_layout = QVBoxLayout(detail_group)

        self.cashflow_table = QTableWidget()
        self.cashflow_table.setColumnCount(5)
        self.cashflow_table.setHorizontalHeaderLabels([
            "Datum",
            "Popis",
            "Kategorie",
            "Příjem",
            "Výdaj"
        ])
        self.cashflow_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        detail_layout.addWidget(self.cashflow_table)

        layout.addWidget(detail_group)

        return widget

    def create_costs_tab(self):
        """Záložka: Nákladové středisko"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Graf nákladů
        chart_group = QGroupBox("📊 Rozdělení nákladů podle kategorií")
        chart_layout = QVBoxLayout(chart_group)

        self.costs_chart = QChartView()
        self.costs_chart.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.costs_chart.setMinimumHeight(400)
        chart_layout.addWidget(self.costs_chart)

        layout.addWidget(chart_group)

        # Tabulka nákladů
        table_group = QGroupBox("Detailní přehled nákladů")
        table_layout = QVBoxLayout(table_group)

        self.costs_table = QTableWidget()
        self.costs_table.setColumnCount(4)
        self.costs_table.setHorizontalHeaderLabels([
            "Kategorie",
            "Částka",
            "Procento",
            "Počet položek"
        ])
        self.costs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_layout.addWidget(self.costs_table)

        layout.addWidget(table_group)

        return widget

    def create_reports_tab(self):
        """Záložka: Přehledy pro účetní"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Tlačítka pro různé přehledy
        buttons_layout = QHBoxLayout()

        receivables_btn = QPushButton("📊 Výpis pohledávek")
        receivables_btn.clicked.connect(self.generate_receivables_report)
        receivables_btn.setStyleSheet(f"background-color: {config.COLOR_SECONDARY}; color: white; padding: 10px 20px;")
        buttons_layout.addWidget(receivables_btn)

        payables_btn = QPushButton("📉 Výpis závazků")
        payables_btn.clicked.connect(self.generate_payables_report)
        payables_btn.setStyleSheet(f"background-color: {config.COLOR_SECONDARY}; color: white; padding: 10px 20px;")
        buttons_layout.addWidget(payables_btn)

        inventory_btn = QPushButton("📦 Hodnota skladu")
        inventory_btn.clicked.connect(self.generate_inventory_report)
        inventory_btn.setStyleSheet(f"background-color: {config.COLOR_SECONDARY}; color: white; padding: 10px 20px;")
        buttons_layout.addWidget(inventory_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # Přehledy
        tabs = QTabWidget()

        # Pohledávky
        receivables_widget = QWidget()
        receivables_layout = QVBoxLayout(receivables_widget)
        self.receivables_table = QTableWidget()
        self.receivables_table.setColumnCount(6)
        self.receivables_table.setHorizontalHeaderLabels([
            "Číslo faktury",
            "Zákazník",
            "Datum splatnosti",
            "Částka celkem",
            "Zaplaceno",
            "Zbývá"
        ])
        self.receivables_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        receivables_layout.addWidget(self.receivables_table)
        tabs.addTab(receivables_widget, "📊 Pohledávky")

        # Závazky
        payables_widget = QWidget()
        payables_layout = QVBoxLayout(payables_widget)
        self.payables_table = QTableWidget()
        self.payables_table.setColumnCount(6)
        self.payables_table.setHorizontalHeaderLabels([
            "Číslo faktury",
            "Dodavatel",
            "Datum splatnosti",
            "Částka celkem",
            "Zaplaceno",
            "Zbývá"
        ])
        self.payables_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        payables_layout.addWidget(self.payables_table)
        tabs.addTab(payables_widget, "📉 Závazky")

        # Sklad
        inventory_widget = QWidget()
        inventory_layout = QVBoxLayout(inventory_widget)

        inventory_stats = QFrame()
        inventory_stats.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        inventory_stats_layout = QHBoxLayout(inventory_stats)

        self.inventory_count_label = QLabel("Počet položek: 0")
        inventory_stats_layout.addWidget(self.inventory_count_label)

        self.inventory_purchase_value_label = QLabel("Nákupní hodnota: 0 Kč")
        inventory_stats_layout.addWidget(self.inventory_purchase_value_label)

        self.inventory_sale_value_label = QLabel("Prodejní hodnota: 0 Kč")
        inventory_stats_layout.addWidget(self.inventory_sale_value_label)

        inventory_stats_layout.addStretch()
        inventory_layout.addWidget(inventory_stats)

        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(5)
        self.inventory_table.setHorizontalHeaderLabels([
            "Kód",
            "Název",
            "Množství",
            "Nákupní cena",
            "Celková hodnota"
        ])
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        inventory_layout.addWidget(self.inventory_table)
        tabs.addTab(inventory_widget, "📦 Sklad")

        layout.addWidget(tabs)

        # Export tlačítka
        export_layout = QHBoxLayout()
        export_layout.addStretch()

        export_csv_btn = QPushButton("📄 Export do CSV (pro účetní SW)")
        export_csv_btn.clicked.connect(self.export_for_accounting)
        export_layout.addWidget(export_csv_btn)

        export_excel_btn = QPushButton("📊 Export do Excel")
        export_excel_btn.clicked.connect(self.export_reports_excel)
        export_layout.addWidget(export_excel_btn)

        layout.addLayout(export_layout)

        return widget

    # =====================================================
    # NAČÍTÁNÍ DAT
    # =====================================================

    def on_period_changed(self, period_text):
        """Změna předvoleného období"""
        today = QDate.currentDate()

        if period_text == "Tento měsíc":
            self.date_from.setDate(QDate(today.year(), today.month(), 1))
            self.date_to.setDate(today)
        elif period_text == "Minulý měsíc":
            last_month = today.addMonths(-1)
            first_day = QDate(last_month.year(), last_month.month(), 1)
            last_day = QDate(last_month.year(), last_month.month(), last_month.daysInMonth())
            self.date_from.setDate(first_day)
            self.date_to.setDate(last_day)
        elif period_text == "Tento rok":
            self.date_from.setDate(QDate(today.year(), 1, 1))
            self.date_to.setDate(today)
        elif period_text == "Minulý rok":
            self.date_from.setDate(QDate(today.year() - 1, 1, 1))
            self.date_to.setDate(QDate(today.year() - 1, 12, 31))
        elif period_text == "Poslední 3 měsíce":
            self.date_from.setDate(today.addMonths(-3))
            self.date_to.setDate(today)
        elif period_text == "Poslední 6 měsíců":
            self.date_from.setDate(today.addMonths(-6))
            self.date_to.setDate(today)
        elif period_text == "Poslední 12 měsíců":
            self.date_from.setDate(today.addMonths(-12))
            self.date_to.setDate(today)

        self.load_data()

    def load_data(self):
        """Načtení všech dat"""
        self.current_period["from"] = self.date_from.date().toString("yyyy-MM-dd")
        self.current_period["to"] = self.date_to.date().toString("yyyy-MM-dd")

        self.load_statistics()
        self.load_overview()
        self.load_cashflow()
        self.load_costs()
        self.load_reports()

    def load_statistics(self):
        """Načtení hlavních statistik"""
        try:
            date_from = self.current_period["from"]
            date_to = self.current_period["to"]

            # Příjmy z faktur
            query_income = """
                SELECT COALESCE(SUM(total_with_vat), 0) as total
                FROM invoices
                WHERE invoice_type = 'issued'
                  AND status IN ('paid', 'partial')
                  AND issue_date BETWEEN ? AND ?
            """
            result = db.fetch_one(query_income, (date_from, date_to))
            income = result["total"] if result else 0

            # Výdaje z faktur
            query_expenses = """
                SELECT COALESCE(SUM(total_with_vat), 0) as total
                FROM invoices
                WHERE invoice_type = 'received'
                  AND status IN ('paid', 'partial')
                  AND issue_date BETWEEN ? AND ?
            """
            result = db.fetch_one(query_expenses, (date_from, date_to))
            expenses = result["total"] if result else 0

            # Zisk/Ztráta
            profit = income - expenses

            # Marže
            margin = (profit / income * 100) if income > 0 else 0

            # Aktualizace labelů
            self.stat_labels["income"].setText(f"{income:,.2f} Kč".replace(",", " "))
            self.stat_labels["expenses"].setText(f"{expenses:,.2f} Kč".replace(",", " "))

            profit_label = self.stat_labels["profit"]
            profit_label.setText(f"{profit:,.2f} Kč".replace(",", " "))
            if profit > 0:
                profit_label.setStyleSheet(f"color: {config.COLOR_SUCCESS}; font-weight: bold; font-size: 16pt;")
            elif profit < 0:
                profit_label.setStyleSheet(f"color: {config.COLOR_DANGER}; font-weight: bold; font-size: 16pt;")
            else:
                profit_label.setStyleSheet(f"color: {config.COLOR_SECONDARY}; font-weight: bold; font-size: 16pt;")

            self.stat_labels["margin"].setText(f"{margin:.1f}%")

        except Exception as e:
            print(f"Chyba při načítání statistik: {e}")

    def load_overview(self):
        """Načtení přehledu účetnictví"""
        try:
            date_from = self.current_period["from"]
            date_to = self.current_period["to"]

            # Příjmy podle kategorií
            income_data = [
                ("Faktury zákazníkům", self.get_issued_invoices_total(date_from, date_to)),
                ("Hotovostní prodej", 0),  # TODO: Implementovat
                ("Ostatní příjmy", 0),  # TODO: Implementovat
            ]

            self.income_table.setRowCount(len(income_data))
            total_income = 0

            for row, (category, amount) in enumerate(income_data):
                self.income_table.setItem(row, 0, QTableWidgetItem(category))
                amount_item = QTableWidgetItem(f"{amount:,.2f} Kč".replace(",", " "))
                amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.income_table.setItem(row, 1, amount_item)
                total_income += amount

            self.total_income_label.setText(f"Celkem: {total_income:,.2f} Kč".replace(",", " "))

            # Výdaje podle kategorií
            expenses_data = [
                ("Nákup materiálu", self.get_received_invoices_total(date_from, date_to)),
                ("Mzdy", 0),  # TODO: Implementovat
                ("Provoz", 0),  # TODO: Implementovat
                ("Ostatní výdaje", 0),  # TODO: Implementovat
            ]

            self.expenses_table.setRowCount(len(expenses_data))
            total_expenses = 0

            for row, (category, amount) in enumerate(expenses_data):
                self.expenses_table.setItem(row, 0, QTableWidgetItem(category))
                amount_item = QTableWidgetItem(f"{amount:,.2f} Kč".replace(",", " "))
                amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.expenses_table.setItem(row, 1, amount_item)
                total_expenses += amount

            self.total_expenses_label.setText(f"Celkem: {total_expenses:,.2f} Kč".replace(",", " "))

            # Graf vývoje
            self.create_overview_chart(date_from, date_to)

        except Exception as e:
            print(f"Chyba při načítání přehledu: {e}")

    def create_overview_chart(self, date_from, date_to):
        """Vytvoření grafu vývoje příjmů a výdajů"""
        try:
            # Získat měsíční data
            query = """
                SELECT
                    strftime('%Y-%m', issue_date) as month,
                    invoice_type,
                    SUM(total_with_vat) as total
                FROM invoices
                WHERE issue_date BETWEEN ? AND ?
                  AND status IN ('paid', 'partial')
                GROUP BY month, invoice_type
                ORDER BY month
            """
            data = db.fetch_all(query, (date_from, date_to))

            # Připravit data pro graf
            months = set()
            income_by_month = {}
            expenses_by_month = {}

            for row in data:
                month = row["month"]
                months.add(month)

                if row["invoice_type"] == "issued":
                    income_by_month[month] = row["total"]
                else:
                    expenses_by_month[month] = row["total"]

            months = sorted(list(months))

            # Vytvořit série
            income_series = QLineSeries()
            income_series.setName("Příjmy")

            expenses_series = QLineSeries()
            expenses_series.setName("Výdaje")

            for i, month in enumerate(months):
                income_series.append(i, income_by_month.get(month, 0))
                expenses_series.append(i, expenses_by_month.get(month, 0))

            # Vytvořit graf
            chart = QChart()
            chart.addSeries(income_series)
            chart.addSeries(expenses_series)
            chart.setTitle("Vývoj příjmů a výdajů")
            chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

            # Formátování měsíců
            categories = [datetime.strptime(m, "%Y-%m").strftime("%m/%Y") for m in months]

            axis_x = QBarCategoryAxis()
            axis_x.append(categories)
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            income_series.attachAxis(axis_x)
            expenses_series.attachAxis(axis_x)

            axis_y = QValueAxis()
            axis_y.setTitleText("Částka (Kč)")
            chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
            income_series.attachAxis(axis_y)
            expenses_series.attachAxis(axis_y)

            self.overview_chart.setChart(chart)

        except Exception as e:
            print(f"Chyba při vytváření grafu: {e}")

    def load_cashflow(self):
        """Načtení peněžních toků"""
        try:
            date_from = self.current_period["from"]
            date_to = self.current_period["to"]

            # Příjmy
            income = self.get_issued_invoices_total(date_from, date_to)

            # Výdaje
            expenses = self.get_received_invoices_total(date_from, date_to)

            # Aktualizace labelů
            self.cashflow_start_label.setText("0 Kč")  # TODO: Skutečný stav
            self.cashflow_income_label.setText(f"{income:,.2f} Kč".replace(",", " "))
            self.cashflow_expense_label.setText(f"{expenses:,.2f} Kč".replace(",", " "))
            self.cashflow_end_label.setText(f"{income - expenses:,.2f} Kč".replace(",", " "))

            # Detailní tabulka
            self.load_cashflow_details(date_from, date_to)

        except Exception as e:
            print(f"Chyba při načítání cash flow: {e}")

    def load_cashflow_details(self, date_from, date_to):
        """Načtení detailů peněžních toků"""
        try:
            query = """
                SELECT
                    p.payment_date,
                    i.invoice_number,
                    i.invoice_type,
                    p.amount,
                    CASE
                        WHEN i.invoice_type = 'issued' THEN 'Příjem z faktury'
                        ELSE 'Platba faktury'
                    END as category
                FROM payments p
                JOIN invoices i ON p.invoice_id = i.id
                WHERE p.payment_date BETWEEN ? AND ?
                ORDER BY p.payment_date DESC
            """
            payments = db.fetch_all(query, (date_from, date_to))

            self.cashflow_table.setRowCount(len(payments))

            for row, payment in enumerate(payments):
                # Datum
                payment_date = datetime.fromisoformat(payment["payment_date"]).strftime("%d.%m.%Y")
                self.cashflow_table.setItem(row, 0, QTableWidgetItem(payment_date))

                # Popis
                desc = f"Faktura {payment['invoice_number']}"
                self.cashflow_table.setItem(row, 1, QTableWidgetItem(desc))

                # Kategorie
                self.cashflow_table.setItem(row, 2, QTableWidgetItem(payment["category"]))

                # Příjem/Výdaj
                if payment["invoice_type"] == "issued":
                    income_item = QTableWidgetItem(f"{payment['amount']:,.2f} Kč".replace(",", " "))
                    income_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    income_item.setForeground(QColor(config.COLOR_SUCCESS))
                    self.cashflow_table.setItem(row, 3, income_item)
                    self.cashflow_table.setItem(row, 4, QTableWidgetItem(""))
                else:
                    self.cashflow_table.setItem(row, 3, QTableWidgetItem(""))
                    expense_item = QTableWidgetItem(f"{payment['amount']:,.2f} Kč".replace(",", " "))
                    expense_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    expense_item.setForeground(QColor(config.COLOR_DANGER))
                    self.cashflow_table.setItem(row, 4, expense_item)

        except Exception as e:
            print(f"Chyba při načítání detailů cash flow: {e}")

    def load_costs(self):
        """Načtení nákladového střediska"""
        try:
            date_from = self.current_period["from"]
            date_to = self.current_period["to"]

            # Získat náklady podle kategorií
            expenses = self.get_received_invoices_total(date_from, date_to)

            # Pro demonstraci - rozdělení nákladů
            costs_data = [
                ("Nákup materiálu", expenses * 0.6),
                ("Mzdy", expenses * 0.25),
                ("Provoz", expenses * 0.10),
                ("Ostatní", expenses * 0.05),
            ]

            # Koláčový graf
            series = QPieSeries()
            for category, amount in costs_data:
                series.append(f"{category}\n{amount:,.0f} Kč".replace(",", " "), amount)

            chart = QChart()
            chart.addSeries(series)
            chart.setTitle("Rozdělení nákladů")
            chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

            self.costs_chart.setChart(chart)

            # Tabulka
            self.costs_table.setRowCount(len(costs_data))
            total = sum(amount for _, amount in costs_data)

            for row, (category, amount) in enumerate(costs_data):
                self.costs_table.setItem(row, 0, QTableWidgetItem(category))

                amount_item = QTableWidgetItem(f"{amount:,.2f} Kč".replace(",", " "))
                amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.costs_table.setItem(row, 1, amount_item)

                percent = (amount / total * 100) if total > 0 else 0
                percent_item = QTableWidgetItem(f"{percent:.1f}%")
                percent_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.costs_table.setItem(row, 2, percent_item)

                self.costs_table.setItem(row, 3, QTableWidgetItem("-"))

        except Exception as e:
            print(f"Chyba při načítání nákladů: {e}")

    def load_reports(self):
        """Načtení přehledů pro účetní"""
        try:
            date_from = self.current_period["from"]
            date_to = self.current_period["to"]

            # Pohledávky
            self.load_receivables_report()

            # Závazky
            self.load_payables_report()

            # Sklad
            self.load_inventory_report()

        except Exception as e:
            print(f"Chyba při načítání přehledů: {e}")

    def load_receivables_report(self):
        """Načtení přehledu pohledávek"""
        try:
            query = """
                SELECT
                    i.invoice_number,
                    COALESCE(c.first_name || ' ' || c.last_name, c.company, 'Neznámý') as customer_name,
                    i.due_date,
                    i.total_with_vat,
                    i.paid_amount,
                    (i.total_with_vat - i.paid_amount) as remaining
                FROM invoices i
                LEFT JOIN customers c ON i.customer_id = c.id
                WHERE i.invoice_type = 'issued'
                  AND i.status IN ('unpaid', 'partial', 'overdue')
                  AND (i.total_with_vat - i.paid_amount) > 0
                ORDER BY i.due_date
            """
            receivables = db.fetch_all(query)

            self.receivables_table.setRowCount(len(receivables))

            for row, rec in enumerate(receivables):
                self.receivables_table.setItem(row, 0, QTableWidgetItem(rec["invoice_number"]))
                self.receivables_table.setItem(row, 1, QTableWidgetItem(rec["customer_name"]))

                due_date = datetime.fromisoformat(rec["due_date"]).strftime("%d.%m.%Y")
                self.receivables_table.setItem(row, 2, QTableWidgetItem(due_date))

                total_item = QTableWidgetItem(f"{rec['total_with_vat']:,.2f} Kč".replace(",", " "))
                total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.receivables_table.setItem(row, 3, total_item)

                paid_item = QTableWidgetItem(f"{rec['paid_amount']:,.2f} Kč".replace(",", " "))
                paid_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.receivables_table.setItem(row, 4, paid_item)

                remaining_item = QTableWidgetItem(f"{rec['remaining']:,.2f} Kč".replace(",", " "))
                remaining_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                remaining_item.setForeground(QColor(config.COLOR_DANGER))
                self.receivables_table.setItem(row, 5, remaining_item)

        except Exception as e:
            print(f"Chyba při načítání pohledávek: {e}")

    def load_payables_report(self):
        """Načtení přehledu závazků"""
        try:
            query = """
                SELECT
                    i.invoice_number,
                    COALESCE(i.supplier_name, 'Neznámý dodavatel') as supplier_name,
                    i.due_date,
                    i.total_with_vat,
                    i.paid_amount,
                    (i.total_with_vat - i.paid_amount) as remaining
                FROM invoices i
                WHERE i.invoice_type = 'received'
                  AND i.status IN ('unpaid', 'partial', 'overdue')
                  AND (i.total_with_vat - i.paid_amount) > 0
                ORDER BY i.due_date
            """
            payables = db.fetch_all(query)

            self.payables_table.setRowCount(len(payables))

            for row, pay in enumerate(payables):
                self.payables_table.setItem(row, 0, QTableWidgetItem(pay["invoice_number"]))
                self.payables_table.setItem(row, 1, QTableWidgetItem(pay["supplier_name"]))

                due_date = datetime.fromisoformat(pay["due_date"]).strftime("%d.%m.%Y")
                self.payables_table.setItem(row, 2, QTableWidgetItem(due_date))

                total_item = QTableWidgetItem(f"{pay['total_with_vat']:,.2f} Kč".replace(",", " "))
                total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.payables_table.setItem(row, 3, total_item)

                paid_item = QTableWidgetItem(f"{pay['paid_amount']:,.2f} Kč".replace(",", " "))
                paid_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.payables_table.setItem(row, 4, paid_item)

                remaining_item = QTableWidgetItem(f"{pay['remaining']:,.2f} Kč".replace(",", " "))
                remaining_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.payables_table.setItem(row, 5, remaining_item)

        except Exception as e:
            print(f"Chyba při načítání závazků: {e}")

    def load_inventory_report(self):
        """Načtení přehledu skladu"""
        try:
            query = """
                SELECT
                    code,
                    name,
                    quantity,
                    price_purchase,
                    (quantity * price_purchase) as total_value
                FROM warehouse
                WHERE quantity > 0
                ORDER BY total_value DESC
            """
            items = db.fetch_all(query)

            self.inventory_table.setRowCount(len(items))

            total_purchase_value = 0
            total_sale_value = 0

            for row, item in enumerate(items):
                self.inventory_table.setItem(row, 0, QTableWidgetItem(item["code"]))
                self.inventory_table.setItem(row, 1, QTableWidgetItem(item["name"]))

                qty_item = QTableWidgetItem(f"{item['quantity']:.2f}")
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.inventory_table.setItem(row, 2, qty_item)

                price_item = QTableWidgetItem(f"{item['price_purchase']:,.2f} Kč".replace(",", " "))
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.inventory_table.setItem(row, 3, price_item)

                value_item = QTableWidgetItem(f"{item['total_value']:,.2f} Kč".replace(",", " "))
                value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.inventory_table.setItem(row, 4, value_item)

                total_purchase_value += item['total_value']

            # Aktualizace statistik
            self.inventory_count_label.setText(f"Počet položek: {len(items)}")
            self.inventory_purchase_value_label.setText(f"Nákupní hodnota: {total_purchase_value:,.2f} Kč".replace(",", " "))
            self.inventory_sale_value_label.setText(f"Prodejní hodnota: N/A")  # TODO: Vypočítat

        except Exception as e:
            print(f"Chyba při načítání skladu: {e}")

    # =====================================================
    # POMOCNÉ METODY
    # =====================================================

    def get_issued_invoices_total(self, date_from, date_to):
        """Celkový součet vydaných faktur"""
        query = """
            SELECT COALESCE(SUM(total_with_vat), 0) as total
            FROM invoices
            WHERE invoice_type = 'issued'
              AND status IN ('paid', 'partial')
              AND issue_date BETWEEN ? AND ?
        """
        result = db.fetch_one(query, (date_from, date_to))
        return result["total"] if result else 0

    def get_received_invoices_total(self, date_from, date_to):
        """Celkový součet přijatých faktur"""
        query = """
            SELECT COALESCE(SUM(total_with_vat), 0) as total
            FROM invoices
            WHERE invoice_type = 'received'
              AND status IN ('paid', 'partial')
              AND issue_date BETWEEN ? AND ?
        """
        result = db.fetch_one(query, (date_from, date_to))
        return result["total"] if result else 0

    # =====================================================
    # AKCE
    # =====================================================

    def generate_receivables_report(self):
        """Generování přehledu pohledávek"""
        QMessageBox.information(
            self,
            "Přehled pohledávek",
            "Export přehledu pohledávek do PDF bude implementován."
        )

    def generate_payables_report(self):
        """Generování přehledu závazků"""
        QMessageBox.information(
            self,
            "Přehled závazků",
            "Export přehledu závazků do PDF bude implementován."
        )

    def generate_inventory_report(self):
        """Generování přehledu skladu"""
        QMessageBox.information(
            self,
            "Přehled skladu",
            "Export přehledu skladu do PDF bude implementován."
        )

    def export_overview_excel(self):
        """Export přehledu do Excel"""
        QMessageBox.information(
            self,
            "Export",
            "Export účetního přehledu do Excel bude implementován."
        )

    def export_overview_pdf(self):
        """Export přehledu do PDF"""
        QMessageBox.information(
            self,
            "Export",
            "Export účetního přehledu do PDF bude implementován."
        )

    def export_for_accounting(self):
        """Export pro účetní software"""
        QMessageBox.information(
            self,
            "Export",
            "Export do CSV formátu pro účetní software bude implementován.\n\n"
            "Podporované formáty:\n"
            "- Pohoda\n"
            "- Money S3\n"
            "- ABRA Flexi"
        )

    def export_reports_excel(self):
        """Export přehledů do Excel"""
        QMessageBox.information(
            self,
            "Export",
            "Export přehledů do Excel bude implementován."
        )

    def refresh(self):
        """Obnovení dat"""
        self.load_data()
