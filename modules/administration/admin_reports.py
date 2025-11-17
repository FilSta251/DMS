# -*- coding: utf-8 -*-
"""
Modul Administrativa - Finanční reporty a analýzy (PRODUKČNÍ VERZE)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QFrame,
                             QComboBox, QLineEdit, QDateEdit, QHeaderView,
                             QMessageBox, QDialog, QFormLayout, QTextEdit,
                             QSpinBox, QDoubleSpinBox, QFileDialog, QCheckBox,
                             QGroupBox, QTabWidget, QScrollArea, QProgressBar,
                             QSplitter, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor, QTextDocument, QTextCursor
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QLineSeries, QBarSeries, QBarSet, QValueAxis, QBarCategoryAxis
from PyQt6.QtPrintSupport import QPrinter
from datetime import datetime, timedelta, date
from pathlib import Path
import config
from database_manager import db


class ReportsWidget(QWidget):
    """Widget pro finanční reporty"""

    def __init__(self):
        super().__init__()
        self.current_report_data = None
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Hlavička
        header_label = QLabel("📈 Finanční reporty a analýzy")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)

        # Hlavní splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Levý panel - výběr reportu
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # Pravý panel - náhled reportu
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

    def create_left_panel(self):
        """Levý panel s výběrem reportu"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Typ reportu
        type_group = QGroupBox("Typ reportu")
        type_layout = QVBoxLayout(type_group)

        self.report_types = QListWidget()
        report_types_data = [
            ("📊 Měsíční report", "monthly"),
            ("📅 Čtvrtletní report", "quarterly"),
            ("📆 Roční report", "yearly"),
            ("📈 Vlastní období", "custom"),
        ]

        for label, value in report_types_data:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, value)
            self.report_types.addItem(item)

        self.report_types.setCurrentRow(0)
        self.report_types.currentRowChanged.connect(self.on_report_type_changed)
        type_layout.addWidget(self.report_types)

        layout.addWidget(type_group)

        # Období
        period_group = QGroupBox("Období")
        period_layout = QVBoxLayout(period_group)

        # Předvolené období (pro měsíční/čtvrtletní/roční)
        self.period_combo = QComboBox()
        self.period_combo.currentTextChanged.connect(self.update_period_dates)
        period_layout.addWidget(self.period_combo)

        # Vlastní období
        custom_widget = QWidget()
        custom_layout = QFormLayout(custom_widget)
        custom_layout.setContentsMargins(0, 0, 0, 0)

        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd.MM.yyyy")
        custom_layout.addRow("Od:", self.date_from)

        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd.MM.yyyy")
        custom_layout.addRow("Do:", self.date_to)

        self.custom_widget = custom_widget
        self.custom_widget.setVisible(False)
        period_layout.addWidget(self.custom_widget)

        layout.addWidget(period_group)

        # Šablona reportu
        template_group = QGroupBox("Šablona reportu")
        template_layout = QVBoxLayout(template_group)

        self.template_combo = QComboBox()
        self.template_combo.addItem("Pro majitele (high-level)", "owner")
        self.template_combo.addItem("Pro management (detailní)", "management")
        self.template_combo.addItem("Pro účetní (technický)", "accounting")
        template_layout.addWidget(self.template_combo)

        layout.addWidget(template_group)

        # Porovnání
        comparison_group = QGroupBox("Porovnání")
        comparison_layout = QVBoxLayout(comparison_group)

        self.comparison_checkbox = QCheckBox("Porovnat s předchozím obdobím")
        self.comparison_checkbox.setChecked(True)
        comparison_layout.addWidget(self.comparison_checkbox)

        self.trend_checkbox = QCheckBox("Zobrazit trendy")
        self.trend_checkbox.setChecked(True)
        comparison_layout.addWidget(self.trend_checkbox)

        self.prediction_checkbox = QCheckBox("Predikce dalšího období")
        comparison_layout.addWidget(self.prediction_checkbox)

        layout.addWidget(comparison_group)

        # Tlačítko generovat
        generate_btn = QPushButton("📊 Vygenerovat report")
        generate_btn.clicked.connect(self.generate_report)
        generate_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 12px 20px;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 4px;
            }}
        """)
        layout.addWidget(generate_btn)

        layout.addStretch()

        return widget

    def create_right_panel(self):
        """Pravý panel s náhledem reportu"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tlačítka akcí
        actions_layout = QHBoxLayout()

        export_pdf_btn = QPushButton("📄 Export PDF")
        export_pdf_btn.clicked.connect(self.export_pdf)
        actions_layout.addWidget(export_pdf_btn)

        export_excel_btn = QPushButton("📊 Export Excel")
        export_excel_btn.clicked.connect(self.export_excel)
        actions_layout.addWidget(export_excel_btn)

        export_pptx_btn = QPushButton("📽️ Export PowerPoint")
        export_pptx_btn.clicked.connect(self.export_powerpoint)
        actions_layout.addWidget(export_pptx_btn)

        send_email_btn = QPushButton("📧 Odeslat emailem")
        send_email_btn.clicked.connect(self.send_email)
        actions_layout.addWidget(send_email_btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        # Náhled reportu
        preview_group = QGroupBox("Náhled reportu")
        preview_layout = QVBoxLayout(preview_group)

        # Scroll area pro report
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.report_widget = QWidget()
        self.report_layout = QVBoxLayout(self.report_widget)
        self.report_layout.setContentsMargins(20, 20, 20, 20)

        # Placeholder
        placeholder = QLabel("Vyberte parametry a klikněte na 'Vygenerovat report'")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #95a5a6; font-size: 12pt; padding: 50px;")
        self.report_layout.addWidget(placeholder)

        scroll.setWidget(self.report_widget)
        preview_layout.addWidget(scroll)

        layout.addWidget(preview_group)

        return widget

    # =====================================================
    # UDÁLOSTI
    # =====================================================

    def on_report_type_changed(self, row):
        """Změna typu reportu"""
        if row < 0:
            return

        item = self.report_types.item(row)
        report_type = item.data(Qt.ItemDataRole.UserRole)

        # Aktualizovat seznam období
        self.period_combo.clear()

        if report_type == "monthly":
            # Měsíční - posledních 12 měsíců
            for i in range(12):
                date = QDate.currentDate().addMonths(-i)
                month_name = self.get_month_name(date.month())
                self.period_combo.addItem(f"{month_name} {date.year()}", date)
            self.period_combo.setVisible(True)
            self.custom_widget.setVisible(False)

        elif report_type == "quarterly":
            # Čtvrtletní - posledních 8 čtvrtletí
            for i in range(8):
                quarter_start = QDate.currentDate().addMonths(-i * 3)
                quarter_num = (quarter_start.month() - 1) // 3 + 1
                self.period_combo.addItem(f"Q{quarter_num} {quarter_start.year()}", quarter_start)
            self.period_combo.setVisible(True)
            self.custom_widget.setVisible(False)

        elif report_type == "yearly":
            # Roční - posledních 5 let
            current_year = QDate.currentDate().year()
            for year in range(current_year, current_year - 5, -1):
                self.period_combo.addItem(str(year), QDate(year, 1, 1))
            self.period_combo.setVisible(True)
            self.custom_widget.setVisible(False)

        elif report_type == "custom":
            self.period_combo.setVisible(False)
            self.custom_widget.setVisible(True)

    def update_period_dates(self):
        """Aktualizace dat podle vybraného období"""
        current_item = self.report_types.currentItem()
        if not current_item:
            return

        report_type = current_item.data(Qt.ItemDataRole.UserRole)
        selected_date = self.period_combo.currentData()

        if not selected_date or report_type == "custom":
            return

        if report_type == "monthly":
            first_day = QDate(selected_date.year(), selected_date.month(), 1)
            last_day = QDate(selected_date.year(), selected_date.month(), selected_date.daysInMonth())
            self.date_from.setDate(first_day)
            self.date_to.setDate(last_day)

        elif report_type == "quarterly":
            quarter_num = (selected_date.month() - 1) // 3 + 1
            first_month = (quarter_num - 1) * 3 + 1
            first_day = QDate(selected_date.year(), first_month, 1)
            last_month = quarter_num * 3
            last_day = QDate(selected_date.year(), last_month, QDate(selected_date.year(), last_month, 1).daysInMonth())
            self.date_from.setDate(first_day)
            self.date_to.setDate(last_day)

        elif report_type == "yearly":
            self.date_from.setDate(QDate(selected_date.year(), 1, 1))
            self.date_to.setDate(QDate(selected_date.year(), 12, 31))

    # =====================================================
    # GENEROVÁNÍ REPORTU
    # =====================================================

    def generate_report(self):
        """Generování reportu"""
        try:
            # Získat parametry
            date_from = self.date_from.date().toString("yyyy-MM-dd")
            date_to = self.date_to.date().toString("yyyy-MM-dd")
            template = self.template_combo.currentData()
            compare = self.comparison_checkbox.isChecked()
            show_trends = self.trend_checkbox.isChecked()
            show_prediction = self.prediction_checkbox.isChecked()

            # Načíst data
            report_data = self.load_report_data(date_from, date_to, compare)
            self.current_report_data = report_data

            # Vymazat starý obsah
            while self.report_layout.count():
                child = self.report_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            # Vygenerovat report podle šablony
            if template == "owner":
                self.generate_owner_report(report_data, compare, show_trends, show_prediction)
            elif template == "management":
                self.generate_management_report(report_data, compare, show_trends, show_prediction)
            elif template == "accounting":
                self.generate_accounting_report(report_data, compare, show_trends, show_prediction)

            QMessageBox.information(self, "Úspěch", "Report byl vygenerován.")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se vygenerovat report:\n{e}")

    def load_report_data(self, date_from, date_to, compare=False):
        """Načtení dat pro report"""
        try:
            data = {
                "period": {
                    "from": date_from,
                    "to": date_to
                },
                "current": {},
                "previous": {}
            }

            # Aktuální období
            data["current"] = self.load_period_data(date_from, date_to)

            # Předchozí období (pokud porovnáváme)
            if compare:
                # Vypočítat předchozí období stejné délky
                from_date = datetime.fromisoformat(date_from)
                to_date = datetime.fromisoformat(date_to)
                period_length = (to_date - from_date).days

                prev_to = from_date - timedelta(days=1)
                prev_from = prev_to - timedelta(days=period_length)

                data["previous"] = self.load_period_data(
                    prev_from.strftime("%Y-%m-%d"),
                    prev_to.strftime("%Y-%m-%d")
                )

            return data

        except Exception as e:
            print(f"Chyba při načítání dat reportu: {e}")
            return {}

    def load_period_data(self, date_from, date_to):
        """Načtení dat pro období"""
        try:
            data = {}

            # Obrat (z vydaných faktur)
            query_revenue = """
                SELECT COALESCE(SUM(total_with_vat), 0) as revenue
                FROM invoices
                WHERE invoice_type = 'issued'
                  AND status IN ('paid', 'partial')
                  AND issue_date BETWEEN ? AND ?
            """
            result = db.fetch_one(query_revenue, (date_from, date_to))
            data["revenue"] = result["revenue"] if result else 0

            # Náklady (z přijatých faktur)
            query_costs = """
                SELECT COALESCE(SUM(total_with_vat), 0) as costs
                FROM invoices
                WHERE invoice_type = 'received'
                  AND status IN ('paid', 'partial')
                  AND issue_date BETWEEN ? AND ?
            """
            result = db.fetch_one(query_costs, (date_from, date_to))
            data["costs"] = result["costs"] if result else 0

            # Zisk
            data["profit"] = data["revenue"] - data["costs"]

            # Marže
            data["margin"] = (data["profit"] / data["revenue"] * 100) if data["revenue"] > 0 else 0

            # Počet faktur
            query_invoices_count = """
                SELECT COUNT(*) as count
                FROM invoices
                WHERE invoice_type = 'issued'
                  AND issue_date BETWEEN ? AND ?
            """
            result = db.fetch_one(query_invoices_count, (date_from, date_to))
            data["invoices_count"] = result["count"] if result else 0

            # Počet zákazníků
            query_customers = """
                SELECT COUNT(DISTINCT customer_id) as count
                FROM invoices
                WHERE invoice_type = 'issued'
                  AND issue_date BETWEEN ? AND ?
            """
            result = db.fetch_one(query_customers, (date_from, date_to))
            data["customers_count"] = result["count"] if result else 0

            # Průměrná hodnota faktury
            data["avg_invoice_value"] = (data["revenue"] / data["invoices_count"]) if data["invoices_count"] > 0 else 0

            # Top zákazníci
            query_top_customers = """
                SELECT
                    c.first_name || ' ' || c.last_name as customer_name,
                    COALESCE(c.company, '') as company,
                    SUM(i.total_with_vat) as total
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                WHERE i.invoice_type = 'issued'
                  AND i.status IN ('paid', 'partial')
                  AND i.issue_date BETWEEN ? AND ?
                GROUP BY i.customer_id
                ORDER BY total DESC
                LIMIT 10
            """
            data["top_customers"] = db.fetch_all(query_top_customers, (date_from, date_to))

            # Top zakázky podle marže
            query_top_orders = """
                SELECT
                    o.order_number,
                    c.first_name || ' ' || c.last_name as customer_name,
                    o.total_price,
                    o.profit_margin
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                WHERE o.created_date BETWEEN ? AND ?
                  AND o.status = 'Dokončená'
                ORDER BY o.profit_margin DESC
                LIMIT 10
            """
            data["top_orders"] = db.fetch_all(query_top_orders, (date_from, date_to))

            return data

        except Exception as e:
            print(f"Chyba při načítání dat období: {e}")
            return {}

    # =====================================================
    # GENEROVÁNÍ ŠABLON
    # =====================================================

    def generate_owner_report(self, data, compare, show_trends, show_prediction):
        """Report pro majitele (high-level)"""
        # Hlavička
        header = QLabel("📊 FINANČNÍ REPORT PRO MAJITELE")
        header_font = QFont()
        header_font.setPointSize(18)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.report_layout.addWidget(header)

        # Období
        period_label = QLabel(
            f"Období: {datetime.fromisoformat(data['period']['from']).strftime('%d.%m.%Y')} - "
            f"{datetime.fromisoformat(data['period']['to']).strftime('%d.%m.%Y')}"
        )
        period_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        period_label.setStyleSheet("font-size: 11pt; color: #7f8c8d; margin-bottom: 20px;")
        self.report_layout.addWidget(period_label)

        # Executive Summary
        self.add_section_header("📋 Executive Summary")

        current = data["current"]

        summary_frame = self.create_metrics_frame([
            ("💰 Obrat", f"{current['revenue']:,.2f} Kč", config.COLOR_SUCCESS),
            ("💸 Náklady", f"{current['costs']:,.2f} Kč", config.COLOR_DANGER),
            ("📊 Zisk", f"{current['profit']:,.2f} Kč", config.COLOR_SUCCESS if current['profit'] > 0 else config.COLOR_DANGER),
            ("📈 Marže", f"{current['margin']:.1f}%", config.COLOR_WARNING),
        ])
        self.report_layout.addWidget(summary_frame)

        # Porovnání s předchozím obdobím
        if compare and data.get("previous"):
            self.add_section_header("📊 Porovnání s předchozím obdobím")
            self.add_comparison_table(data["current"], data["previous"])

        # Top zákazníci
        self.add_section_header("👥 Top 5 zákazníků podle obratu")
        self.add_top_customers_table(current["top_customers"][:5])

        # Doporučení
        self.add_section_header("💡 Doporučení")
        self.add_recommendations(current)

    def generate_management_report(self, data, compare, show_trends, show_prediction):
        """Report pro management (detailní)"""
        # Hlavička
        header = QLabel("📊 FINANČNÍ REPORT PRO MANAGEMENT")
        header_font = QFont()
        header_font.setPointSize(18)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.report_layout.addWidget(header)

        # Období
        period_label = QLabel(
            f"Období: {datetime.fromisoformat(data['period']['from']).strftime('%d.%m.%Y')} - "
            f"{datetime.fromisoformat(data['period']['to']).strftime('%d.%m.%Y')}"
        )
        period_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        period_label.setStyleSheet("font-size: 11pt; color: #7f8c8d; margin-bottom: 20px;")
        self.report_layout.addWidget(period_label)

        current = data["current"]

        # Klíčové metriky
        self.add_section_header("📈 Klíčové metriky")
        metrics_frame = self.create_metrics_frame([
            ("💰 Obrat", f"{current['revenue']:,.2f} Kč", config.COLOR_SUCCESS),
            ("💸 Náklady", f"{current['costs']:,.2f} Kč", config.COLOR_DANGER),
            ("📊 Zisk", f"{current['profit']:,.2f} Kč", config.COLOR_SUCCESS if current['profit'] > 0 else config.COLOR_DANGER),
            ("📈 Marže", f"{current['margin']:.1f}%", config.COLOR_WARNING),
            ("📄 Počet faktur", str(current['invoices_count']), config.COLOR_SECONDARY),
            ("👥 Počet zákazníků", str(current['customers_count']), config.COLOR_SECONDARY),
            ("💵 Průměrná faktura", f"{current['avg_invoice_value']:,.0f} Kč", config.COLOR_SECONDARY),
        ])
        self.report_layout.addWidget(metrics_frame)

        # Porovnání
        if compare and data.get("previous"):
            self.add_section_header("📊 Porovnání s předchozím obdobím")
            self.add_comparison_table(data["current"], data["previous"])

        # Top zákazníci
        self.add_section_header("👥 Top 10 zákazníků podle obratu")
        self.add_top_customers_table(current["top_customers"])

        # Top zakázky
        self.add_section_header("📦 Top 10 zakázek podle marže")
        self.add_top_orders_table(current["top_orders"])

        # Analýza
        self.add_section_header("📊 Analýza")
        self.add_analysis(current)

    def generate_accounting_report(self, data, compare, show_trends, show_prediction):
        """Report pro účetní (technický)"""
        # Hlavička
        header = QLabel("📊 TECHNICKÝ ÚČETNÍ REPORT")
        header_font = QFont()
        header_font.setPointSize(18)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.report_layout.addWidget(header)

        # Období
        period_label = QLabel(
            f"Období: {datetime.fromisoformat(data['period']['from']).strftime('%d.%m.%Y')} - "
            f"{datetime.fromisoformat(data['period']['to']).strftime('%d.%m.%Y')}"
        )
        period_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        period_label.setStyleSheet("font-size: 11pt; color: #7f8c8d; margin-bottom: 20px;")
        self.report_layout.addWidget(period_label)

        current = data["current"]

        # Přehled
        self.add_section_header("💰 Finanční přehled")

        accounting_table = QTableWidget()
        accounting_table.setColumnCount(2)
        accounting_table.setHorizontalHeaderLabels(["Položka", "Částka"])
        accounting_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        items = [
            ("Tržby celkem", f"{current['revenue']:,.2f} Kč"),
            ("Náklady celkem", f"{current['costs']:,.2f} Kč"),
            ("Hrubý zisk", f"{current['profit']:,.2f} Kč"),
            ("Marže (%)", f"{current['margin']:.2f}%"),
            ("Počet vydaných faktur", str(current['invoices_count'])),
            ("Průměrná hodnota faktury", f"{current['avg_invoice_value']:,.2f} Kč"),
        ]

        accounting_table.setRowCount(len(items))
        for row, (label, value) in enumerate(items):
            accounting_table.setItem(row, 0, QTableWidgetItem(label))
            value_item = QTableWidgetItem(value)
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            accounting_table.setItem(row, 1, value_item)

        self.report_layout.addWidget(accounting_table)

        # Poznámka pro účetní
        note_frame = QFrame()
        note_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        note_layout = QVBoxLayout(note_frame)

        note_title = QLabel("📝 Poznámka:")
        note_font = QFont()
        note_font.setBold(True)
        note_title.setFont(note_font)
        note_layout.addWidget(note_title)

        note_text = QLabel(
            "Tento report obsahuje základní finanční údaje. "
            "Pro detailní účetní analýzu použijte exporty do účetního systému."
        )
        note_text.setWordWrap(True)
        note_layout.addWidget(note_text)

        self.report_layout.addWidget(note_frame)

    # =====================================================
    # POMOCNÉ METODY PRO GENEROVÁNÍ
    # =====================================================

    def add_section_header(self, text):
        """Přidat nadpis sekce"""
        header = QLabel(text)
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setStyleSheet("margin-top: 20px; margin-bottom: 10px;")
        self.report_layout.addWidget(header)

    def create_metrics_frame(self, metrics):
        """Vytvoření rámce s metrikami"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        layout = QHBoxLayout(frame)

        for label, value, color in metrics:
            metric_widget = QWidget()
            metric_layout = QVBoxLayout(metric_widget)
            metric_layout.setContentsMargins(10, 10, 10, 10)

            label_widget = QLabel(label)
            label_widget.setStyleSheet("color: #7f8c8d; font-size: 10pt;")
            metric_layout.addWidget(label_widget)

            value_widget = QLabel(value)
            value_font = QFont()
            value_font.setPointSize(14)
            value_font.setBold(True)
            value_widget.setFont(value_font)
            value_widget.setStyleSheet(f"color: {color};")
            metric_layout.addWidget(value_widget)

            layout.addWidget(metric_widget)

        return frame

    def add_comparison_table(self, current, previous):
        """Přidat tabulku porovnání"""
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Metrika", "Aktuální", "Předchozí", "Změna"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        comparisons = [
            ("Obrat", current["revenue"], previous["revenue"]),
            ("Náklady", current["costs"], previous["costs"]),
            ("Zisk", current["profit"], previous["profit"]),
            ("Marže", current["margin"], previous["margin"]),
        ]

        table.setRowCount(len(comparisons))

        for row, (label, curr, prev) in enumerate(comparisons):
            table.setItem(row, 0, QTableWidgetItem(label))

            if label == "Marže":
                curr_text = f"{curr:.1f}%"
                prev_text = f"{prev:.1f}%"
            else:
                curr_text = f"{curr:,.2f} Kč".replace(",", " ")
                prev_text = f"{prev:,.2f} Kč".replace(",", " ")

            table.setItem(row, 1, QTableWidgetItem(curr_text))
            table.setItem(row, 2, QTableWidgetItem(prev_text))

            # Změna
            if prev != 0:
                change = ((curr - prev) / prev) * 100
                change_text = f"{change:+.1f}%"
                change_item = QTableWidgetItem(change_text)
                change_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if change > 0:
                    change_item.setForeground(QColor(config.COLOR_SUCCESS))
                elif change < 0:
                    change_item.setForeground(QColor(config.COLOR_DANGER))

                table.setItem(row, 3, change_item)
            else:
                table.setItem(row, 3, QTableWidgetItem("N/A"))

        self.report_layout.addWidget(table)

    def add_top_customers_table(self, customers):
        """Přidat tabulku top zákazníků"""
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["#", "Zákazník", "Obrat"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        table.setRowCount(len(customers))

        for row, customer in enumerate(customers):
            # Pořadí
            rank_item = QTableWidgetItem(str(row + 1))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 0, rank_item)

            # Zákazník
            name = customer["customer_name"]
            if customer.get("company"):
                name += f" ({customer['company']})"
            table.setItem(row, 1, QTableWidgetItem(name))

            # Obrat
            total_item = QTableWidgetItem(f"{customer['total']:,.2f} Kč".replace(",", " "))
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 2, total_item)

        self.report_layout.addWidget(table)

    def add_top_orders_table(self, orders):
        """Přidat tabulku top zakázek"""
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["#", "Číslo zakázky", "Zákazník", "Marže"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        table.setRowCount(len(orders))

        for row, order in enumerate(orders):
            # Pořadí
            rank_item = QTableWidgetItem(str(row + 1))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 0, rank_item)

            # Číslo zakázky
            table.setItem(row, 1, QTableWidgetItem(order["order_number"]))

            # Zákazník
            table.setItem(row, 2, QTableWidgetItem(order["customer_name"]))

            # Marže
            margin_item = QTableWidgetItem(f"{order['profit_margin']:.1f}%")
            margin_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 3, margin_item)

        self.report_layout.addWidget(table)

    def add_recommendations(self, data):
        """Přidat doporučení"""
        recommendations = []

        # Na základě marže
        if data["margin"] < 10:
            recommendations.append("⚠️ Nízká marže - zvažte optimalizaci nákladů nebo zvýšení cen")
        elif data["margin"] > 30:
            recommendations.append("✅ Vynikající marže - udržujte stávající strategii")

        # Na základě průměrné faktury
        if data["avg_invoice_value"] < 5000:
            recommendations.append("💡 Nízká průměrná hodnota faktury - zaměřte se na upselling")

        # Obecné
        recommendations.append("📊 Pravidelně monitorujte klíčové metriky")
        recommendations.append("👥 Pečujte o top zákazníky - generují většinu obratu")

        rec_text = QLabel("\n".join(recommendations))
        rec_text.setWordWrap(True)
        rec_text.setStyleSheet("padding: 15px; background-color: #e8f5e9; border-radius: 8px;")
        self.report_layout.addWidget(rec_text)

    def add_analysis(self, data):
        """Přidat analýzu"""
        analysis_text = f"""
        <p><b>Finanční zdraví:</b></p>
        <p>{'✅ Velmi dobré' if data['profit'] > 0 and data['margin'] > 20 else '⚠️ Vyžaduje pozornost'}</p>

        <p><b>Klíčové závěry:</b></p>
        <ul>
        <li>Celkový obrat dosáhl {data['revenue']:,.0f} Kč</li>
        <li>Marže je na úrovni {data['margin']:.1f}%</li>
        <li>Průměrná hodnota faktury: {data['avg_invoice_value']:,.0f} Kč</li>
        <li>Bylo obsluženo {data['customers_count']} zákazníků</li>
        </ul>

        <p><b>Oblasti ke zlepšení:</b></p>
        <ul>
        <li>Optimalizace nákladů</li>
        <li>Zvýšení průměrné hodnoty objednávky</li>
        <li>Retention zákazníků</li>
        </ul>
        """.replace(",", " ")

        analysis_label = QLabel(analysis_text)
        analysis_label.setWordWrap(True)
        analysis_label.setStyleSheet("padding: 15px; background-color: #f8f9fa; border-radius: 8px;")
        self.report_layout.addWidget(analysis_label)

    # =====================================================
    # EXPORT
    # =====================================================

    def export_pdf(self):
        """Export do PDF"""
        if not self.current_report_data:
            QMessageBox.warning(self, "Upozornění", "Nejprve vygenerujte report.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit report jako PDF",
            f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF soubory (*.pdf)"
        )

        if not file_path:
            return

        try:
            # TODO: Implementovat export do PDF
            QMessageBox.information(
                self,
                "Export PDF",
                f"Export reportu do PDF bude implementován.\n\n"
                f"Soubor: {file_path}\n\n"
                "PDF bude obsahovat:\n"
                "- Profesionální vzhled\n"
                "- Grafy a tabulky\n"
                "- Barevné zvýraznění"
            )

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se exportovat PDF:\n{e}")

    def export_excel(self):
        """Export do Excel"""
        if not self.current_report_data:
            QMessageBox.warning(self, "Upozornění", "Nejprve vygenerujte report.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit report jako Excel",
            f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel soubory (*.xlsx)"
        )

        if not file_path:
            return

        try:
            # TODO: Implementovat export do Excel
            QMessageBox.information(
                self,
                "Export Excel",
                f"Export reportu do Excel bude implementován.\n\n"
                f"Soubor: {file_path}\n\n"
                "Excel bude obsahovat:\n"
                "- Detailní data\n"
                "- Pivot tabulky\n"
                "- Grafy"
            )

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se exportovat Excel:\n{e}")

    def export_powerpoint(self):
        """Export do PowerPoint"""
        if not self.current_report_data:
            QMessageBox.warning(self, "Upozornění", "Nejprve vygenerujte report.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit report jako PowerPoint",
            f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx",
            "PowerPoint soubory (*.pptx)"
        )

        if not file_path:
            return

        try:
            # TODO: Implementovat export do PowerPoint
            QMessageBox.information(
                self,
                "Export PowerPoint",
                f"Export reportu do PowerPoint bude implementován.\n\n"
                f"Soubor: {file_path}\n\n"
                "Prezentace bude obsahovat:\n"
                "- Executive summary\n"
                "- Klíčové metriky na slidech\n"
                "- Grafy a vizualizace"
            )

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se exportovat PowerPoint:\n{e}")

    def send_email(self):
        """Odeslání emailem"""
        if not self.current_report_data:
            QMessageBox.warning(self, "Upozornění", "Nejprve vygenerujte report.")
            return

        # Dialog pro email
        dialog = EmailReportDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(
                self,
                "Email",
                "Funkce odeslání reportu emailem bude implementována.\n\n"
                "Report bude odeslán jako PDF příloha."
            )

    # =====================================================
    # POMOCNÉ METODY
    # =====================================================

    def get_month_name(self, month):
        """Vrátí název měsíce"""
        months = {
            1: "Leden", 2: "Únor", 3: "Březen", 4: "Duben",
            5: "Květen", 6: "Červen", 7: "Červenec", 8: "Srpen",
            9: "Září", 10: "Říjen", 11: "Listopad", 12: "Prosinec"
        }
        return months.get(month, "")

    def refresh(self):
        """Obnovení"""
        pass


# =====================================================
# DIALOGY
# =====================================================

class EmailReportDialog(QDialog):
    """Dialog pro odeslání reportu emailem"""

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Odeslat report emailem")
        self.setMinimumWidth(500)

        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QFormLayout(self)

        # Email příjemce
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("prijemce@email.cz")
        layout.addRow("Email příjemce:", self.email_input)

        # Předmět
        self.subject_input = QLineEdit()
        self.subject_input.setText(f"Finanční report - {datetime.now().strftime('%d.%m.%Y')}")
        layout.addRow("Předmět:", self.subject_input)

        # Zpráva
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(150)
        self.message_input.setPlainText(
            "Dobrý den,\n\n"
            "v příloze zasíláme finanční report.\n\n"
            "S pozdravem"
        )
        layout.addRow("Zpráva:", self.message_input)

        # Formát
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PDF", "Excel", "Oba"])
        layout.addRow("Formát přílohy:", self.format_combo)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        send_btn = QPushButton("📧 Odeslat")
        send_btn.clicked.connect(self.accept)
        send_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 20px;")
        buttons_layout.addWidget(send_btn)

        layout.addRow(buttons_layout)
