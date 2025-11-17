# -*- coding: utf-8 -*-
"""
Manažerský modul - Hlavní vstupní bod
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFrame, QStackedWidget, QScrollArea, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from .management_widgets import DateRangeFilter, MetricCard
from database_manager import db


class ManagementModule(QWidget):
    """Hlavní modul pro manažerské analýzy"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_section = None
        self.sections = {}
        self.section_buttons = {}
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Levé postranní menu
        self.create_sidebar(main_layout)

        # Pravý panel s obsahem
        self.create_content_panel(main_layout)

        # Výchozí sekce
        self.switch_section("dashboard")

    def create_sidebar(self, parent_layout):
        """Vytvoření postranního menu"""
        sidebar = QFrame()
        sidebar.setObjectName("managementSidebar")
        sidebar.setFixedWidth(280)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Hlavička
        header = QFrame()
        header.setObjectName("sidebarHeader")
        header.setFixedHeight(80)
        header_layout = QVBoxLayout(header)

        title = QLabel("📊 Management")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel("Analýzy a přehledy")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(9)
        subtitle.setFont(subtitle_font)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        sidebar_layout.addWidget(header)

        # Menu sekce
        menu_sections = [
            ("dashboard", "📊 Dashboard", "Hlavní přehled"),
            ("orders", "📋 Analýza zakázek", "Detailní analýzy zakázek"),
            ("mechanics", "👨‍🔧 Výkon mechaniků", "Produktivita mechaniků"),
            ("warehouse", "📦 Přehled skladu", "Stav a obratovost skladu"),
            ("financial", "💰 Finance", "Příjmy, náklady, zisk"),
            ("trends", "📈 Trendy & Predikce", "Časové analýzy a predikce"),
            ("kpi", "🎯 KPI Monitoring", "Klíčové ukazatele výkonu"),
            ("reports", "📄 Reporty", "Generování reportů"),
        ]

        for section_id, section_name, section_desc in menu_sections:
            btn = QPushButton(section_name)
            btn.setObjectName("sidebarButton")
            btn.setFixedHeight(70)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, sid=section_id: self.switch_section(sid))

            # Popis pod tlačítkem
            btn.setToolTip(section_desc)

            self.section_buttons[section_id] = btn
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # Stylování
        sidebar.setStyleSheet("""
            QFrame#managementSidebar {
                background-color: #34495e;
                border-right: 2px solid #2c3e50;
            }
            QFrame#sidebarHeader {
                background-color: #2c3e50;
                color: white;
            }
            QPushButton#sidebarButton {
                background-color: transparent;
                border: none;
                color: white;
                text-align: left;
                padding: 15px 20px;
                font-size: 13px;
                border-left: 4px solid transparent;
            }
            QPushButton#sidebarButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton#sidebarButton[active="true"] {
                background-color: #2c3e50;
                border-left: 4px solid #3498db;
                font-weight: bold;
            }
        """)

        parent_layout.addWidget(sidebar)

    def create_content_panel(self, parent_layout):
        """Vytvoření pravého panelu s obsahem"""
        content_widget = QWidget()
        content_widget.setObjectName("contentPanel")

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Horní lišta s filtrem období
        self.create_top_bar(content_layout)

        # Stack pro jednotlivé sekce
        self.section_stack = QStackedWidget()
        self.section_stack.setObjectName("sectionStack")

        # Vytvoření všech sekcí
        self.create_sections()

        content_layout.addWidget(self.section_stack)

        content_widget.setStyleSheet("""
            QWidget#contentPanel {
                background-color: #ecf0f1;
            }
            QStackedWidget#sectionStack {
                background-color: #ecf0f1;
            }
        """)

        parent_layout.addWidget(content_widget)

    def create_top_bar(self, parent_layout):
        """Vytvoření horní lišty s filtrem"""
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(70)

        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(20, 10, 20, 10)

        # Titulek sekce
        self.section_title = QLabel("Dashboard")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.section_title.setFont(title_font)
        top_bar_layout.addWidget(self.section_title)

        top_bar_layout.addStretch()

        # Filtr období
        self.date_filter = DateRangeFilter()
        self.date_filter.date_changed.connect(self.on_date_range_changed)
        top_bar_layout.addWidget(self.date_filter)

        top_bar.setStyleSheet("""
            QFrame#topBar {
                background-color: white;
                border-bottom: 2px solid #bdc3c7;
            }
        """)

        parent_layout.addWidget(top_bar)

    def create_sections(self):
        """Vytvoření všech sekcí"""
        # Importy sekcí (zatím používáme placeholder, později je nahradíme skutečnými moduly)
        try:
            from .management_dashboard import ManagementDashboard
            dashboard = ManagementDashboard(self)
        except ImportError:
            dashboard = self.create_placeholder_section("Dashboard", "📊")

        try:
            from .management_orders_analysis import ManagementOrdersAnalysis
            orders = ManagementOrdersAnalysis(self)
        except ImportError:
            orders = self.create_placeholder_section("Analýza zakázek", "📋")

        try:
            from .management_mechanic_performance import ManagementMechanicPerformance
            mechanics = ManagementMechanicPerformance(self)
        except ImportError:
            mechanics = self.create_placeholder_section("Výkon mechaniků", "👨‍🔧")

        try:
            from .management_warehouse_overview import ManagementWarehouseOverview
            warehouse = ManagementWarehouseOverview(self)
        except ImportError:
            warehouse = self.create_placeholder_section("Přehled skladu", "📦")

        try:
            from .management_financial import ManagementFinancial
            financial = ManagementFinancial(self)
        except ImportError:
            financial = self.create_placeholder_section("Finance", "💰")

        try:
            from .management_trends import ManagementTrends
            trends = ManagementTrends(self)
        except ImportError:
            trends = self.create_placeholder_section("Trendy & Predikce", "📈")

        try:
            from .management_kpi import ManagementKPI
            kpi = ManagementKPI(self)
        except ImportError:
            kpi = self.create_placeholder_section("KPI Monitoring", "🎯")

        try:
            from .management_reports import ManagementReports
            reports = ManagementReports(self)
        except ImportError:
            reports = self.create_placeholder_section("Reporty", "📄")

        # Registrace sekcí
        self.sections["dashboard"] = dashboard
        self.sections["orders"] = orders
        self.sections["mechanics"] = mechanics
        self.sections["warehouse"] = warehouse
        self.sections["financial"] = financial
        self.sections["trends"] = trends
        self.sections["kpi"] = kpi
        self.sections["reports"] = reports

        # Přidání do stacku
        for section in self.sections.values():
            self.section_stack.addWidget(section)

    def create_placeholder_section(self, title, icon):
        """Vytvoření placeholder sekce (dokud nevytvoříme skutečný modul)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 72px;")

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)

        desc_label = QLabel("Tato sekce bude brzy k dispozici")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #7f8c8d; font-size: 14px;")

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)

        return widget

    def switch_section(self, section_id):
        """Přepnutí mezi sekcemi"""
        if section_id in self.sections:
            # Aktualizace aktivního tlačítka
            for btn_id, btn in self.section_buttons.items():
                btn.setProperty("active", btn_id == section_id)
                btn.style().unpolish(btn)
                btn.style().polish(btn)

            # Přepnutí stacku
            self.section_stack.setCurrentWidget(self.sections[section_id])
            self.current_section = section_id

            # Aktualizace titulku
            section_names = {
                "dashboard": "📊 Dashboard",
                "orders": "📋 Analýza zakázek",
                "mechanics": "👨‍🔧 Výkon mechaniků",
                "warehouse": "📦 Přehled skladu",
                "financial": "💰 Finance",
                "trends": "📈 Trendy & Predikce",
                "kpi": "🎯 KPI Monitoring",
                "reports": "📄 Reporty"
            }
            self.section_title.setText(section_names.get(section_id, "Management"))

            # Refresh dat sekce (pokud má metodu refresh)
            if hasattr(self.sections[section_id], 'refresh'):
                self.sections[section_id].refresh()

    def on_date_range_changed(self, date_from, date_to):
        """Změna filtru období"""
        # Aktualizace aktivní sekce s novým obdobím
        if self.current_section in self.sections:
            section = self.sections[self.current_section]
            if hasattr(section, 'set_date_range'):
                section.set_date_range(date_from, date_to)
            if hasattr(section, 'refresh'):
                section.refresh()

    def refresh(self):
        """Refresh celého modulu"""
        # Refresh aktivní sekce
        if self.current_section in self.sections:
            if hasattr(self.sections[self.current_section], 'refresh'):
                self.sections[self.current_section].refresh()

    def get_date_range(self):
        """Získání aktuálně vybraného období"""
        return self.date_filter.get_date_range()
