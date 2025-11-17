# -*- coding: utf-8 -*-
"""
Modul Administrativa - Hlavní vstupní bod (PRODUKČNÍ VERZE)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFrame, QStackedWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import config
from database_manager import db


class AdministrationModule(QWidget):
    """Hlavní modul administrativa"""

    def __init__(self):
        super().__init__()
        self.current_section = None
        self.sections = {}
        self.section_buttons = {}
        self.init_ui()
        self.load_quick_stats()

    def init_ui(self):
        """Inicializace UI"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Levé menu
        self.create_navigation_panel(main_layout)

        # Pravý panel s obsahem
        self.create_content_panel(main_layout)

        # Styly
        self.apply_styles()

        # Výchozí sekce
        self.switch_section("invoices_issued")

    def create_navigation_panel(self, parent_layout):
        """Vytvoření levého navigačního panelu"""
        nav_widget = QWidget()
        nav_widget.setObjectName("adminNavPanel")
        nav_widget.setFixedWidth(280)

        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        # Hlavička
        header = QFrame()
        header.setObjectName("adminNavHeader")
        header.setFixedHeight(80)
        header_layout = QVBoxLayout(header)

        title = QLabel("📊 Administrativa")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel("Správa faktur a účetnictví")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(9)
        subtitle.setFont(subtitle_font)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        nav_layout.addWidget(header)

        # Sekce navigace
        sections = [
            {"id": "invoices_issued", "name": "📄 Faktury vydané"},
            {"id": "invoices_received", "name": "📥 Faktury přijaté"},
            {"id": "payments", "name": "💳 Platby"},
            {"id": "documents", "name": "📋 Dokumenty"},
            {"id": "accounting", "name": "💰 Účetnictví"},
            {"id": "tax", "name": "📊 DPH a daně"},
            {"id": "reports", "name": "📈 Reporty"},
            {"id": "settings", "name": "⚙️ Nastavení"},
        ]

        for section in sections:
            btn = QPushButton(section["name"])
            btn.setObjectName("adminNavButton")
            btn.setFixedHeight(55)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, s=section["id"]: self.switch_section(s))
            self.section_buttons[section["id"]] = btn
            nav_layout.addWidget(btn)

        nav_layout.addStretch()

        # Info panel
        info_panel = QFrame()
        info_panel.setObjectName("adminInfoPanel")
        info_panel.setFixedHeight(100)
        info_layout = QVBoxLayout(info_panel)

        stats_label = QLabel("📊 Rychlý přehled")
        stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_font = QFont()
        stats_font.setBold(True)
        stats_label.setFont(stats_font)

        self.quick_stats = QLabel("Načítání...")
        self.quick_stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quick_stats.setWordWrap(True)
        self.quick_stats.setStyleSheet("font-size: 11px; padding: 5px;")

        info_layout.addWidget(stats_label)
        info_layout.addWidget(self.quick_stats)

        nav_layout.addWidget(info_panel)

        parent_layout.addWidget(nav_widget)

    def create_content_panel(self, parent_layout):
        """Vytvoření pravého panelu s obsahem"""
        content_widget = QWidget()
        content_widget.setObjectName("adminContentPanel")

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Horní lišta
        top_bar = QFrame()
        top_bar.setObjectName("adminTopBar")
        top_bar.setFixedHeight(70)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(20, 10, 20, 10)

        # Název sekce
        self.section_title = QLabel("Faktury vydané")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.section_title.setFont(title_font)

        top_bar_layout.addWidget(self.section_title)
        top_bar_layout.addStretch()

        # Rychlé akce
        self.quick_new_invoice_btn = QPushButton("➕ Nová faktura")
        self.quick_new_invoice_btn.setObjectName("adminQuickActionButton")
        self.quick_new_invoice_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.quick_new_invoice_btn.clicked.connect(self.quick_new_invoice)

        self.quick_new_payment_btn = QPushButton("💳 Platba")
        self.quick_new_payment_btn.setObjectName("adminQuickActionButton")
        self.quick_new_payment_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.quick_new_payment_btn.clicked.connect(self.quick_new_payment)

        self.quick_report_btn = QPushButton("📊 Report")
        self.quick_report_btn.setObjectName("adminQuickActionButton")
        self.quick_report_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.quick_report_btn.clicked.connect(self.quick_report)

        top_bar_layout.addWidget(self.quick_new_invoice_btn)
        top_bar_layout.addWidget(self.quick_new_payment_btn)
        top_bar_layout.addWidget(self.quick_report_btn)

        content_layout.addWidget(top_bar)

        # Stack pro sekce
        self.section_stack = QStackedWidget()
        self.section_stack.setObjectName("adminSectionStack")

        # Vytvoření sekcí
        self.create_section_widgets()

        content_layout.addWidget(self.section_stack)

        parent_layout.addWidget(content_widget)

    def create_section_widgets(self):
        """Vytvoření widgetů pro jednotlivé sekce"""
        # Import skutečných modulů
        from .admin_invoices import InvoicesWidget
        from .admin_payments import PaymentsWidget
        from .admin_documents import DocumentsWidget
        from .admin_accounting import AccountingWidget
        from .admin_tax import TaxWidget
        from .admin_reports import ReportsWidget
        from .admin_settings import SettingsWidget

        # Faktury vydané
        self.sections["invoices_issued"] = InvoicesWidget(invoice_type="issued")
        self.section_stack.addWidget(self.sections["invoices_issued"])

        # Faktury přijaté
        self.sections["invoices_received"] = InvoicesWidget(invoice_type="received")
        self.section_stack.addWidget(self.sections["invoices_received"])

        # Platby
        self.sections["payments"] = PaymentsWidget()
        self.section_stack.addWidget(self.sections["payments"])

        # Dokumenty
        self.sections["documents"] = DocumentsWidget()
        self.section_stack.addWidget(self.sections["documents"])

        # Účetnictví
        self.sections["accounting"] = AccountingWidget()
        self.section_stack.addWidget(self.sections["accounting"])

        # DPH a daně
        self.sections["tax"] = TaxWidget()
        self.section_stack.addWidget(self.sections["tax"])

        # Reporty
        self.sections["reports"] = ReportsWidget()
        self.section_stack.addWidget(self.sections["reports"])

        # Nastavení
        self.sections["settings"] = SettingsWidget()
        self.section_stack.addWidget(self.sections["settings"])

    def create_placeholder_widget(self, title, description):
        """Vytvoření placeholder widgetu pro sekci"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel("🚧")
        icon_font = QFont()
        icon_font.setPointSize(72)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc_label = QLabel(description)
        desc_font = QFont()
        desc_font.setPointSize(14)
        desc_label.setFont(desc_font)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("color: #7f8c8d;")

        status_label = QLabel("Modul v přípravě")
        status_font = QFont()
        status_font.setPointSize(12)
        status_font.setItalic(True)
        status_label.setFont(status_font)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setStyleSheet("color: #95a5a6; margin-top: 20px;")

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addWidget(status_label)

        return widget

    def switch_section(self, section_id):
        """Přepnutí na jinou sekci"""
        if section_id in self.sections:
            # Zvýraznění aktivního tlačítka
            for btn_id, btn in self.section_buttons.items():
                btn.setProperty("active", btn_id == section_id)
                btn.style().unpolish(btn)
                btn.style().polish(btn)

            # Přepnutí stacku
            self.section_stack.setCurrentWidget(self.sections[section_id])
            self.current_section = section_id

            # Aktualizace titulku
            section_titles = {
                "invoices_issued": "📄 Faktury vydané",
                "invoices_received": "📥 Faktury přijaté",
                "payments": "💳 Platby",
                "documents": "📋 Dokumenty",
                "accounting": "💰 Účetnictví",
                "tax": "📊 DPH a daně",
                "reports": "📈 Reporty",
                "settings": "⚙️ Nastavení",
            }
            self.section_title.setText(section_titles.get(section_id, ""))

            # Refresh sekce
            if hasattr(self.sections[section_id], 'refresh'):
                self.sections[section_id].refresh()

    def quick_new_invoice(self):
        """Rychlé vytvoření nové faktury"""
        if self.current_section in ["invoices_issued", "invoices_received"]:
            self.sections[self.current_section].new_invoice()

    def quick_new_payment(self):
        """Rychlý záznam platby"""
        if self.current_section in ["invoices_issued", "invoices_received"]:
            self.sections[self.current_section].record_payment()

    def quick_report(self):
        """Rychlé vytvoření reportu"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Report", "Sekce reportů bude implementována v dalším kroku.")

    def load_quick_stats(self):
        """Načtení rychlých statistik z databáze"""
        try:
            # Nezaplacené faktury
            query_unpaid = """
                SELECT COUNT(*), COALESCE(SUM(total_with_vat - paid_amount), 0)
                FROM invoices
                WHERE status IN ('unpaid', 'partial', 'overdue')
                AND invoice_type = 'issued'
            """
            result = db.fetch_one(query_unpaid)
            unpaid_count = result[0] if result else 0
            unpaid_amount = result[1] if result else 0

            # Po splatnosti
            query_overdue = """
                SELECT COUNT(*), COALESCE(SUM(total_with_vat - paid_amount), 0)
                FROM invoices
                WHERE status = 'overdue'
                AND invoice_type = 'issued'
            """
            result = db.fetch_one(query_overdue)
            overdue_count = result[0] if result else 0
            overdue_amount = result[1] if result else 0

            # Dnes splatné
            from datetime import date
            today = date.today().isoformat()
            query_today = """
                SELECT COUNT(*)
                FROM invoices
                WHERE due_date = ?
                AND status IN ('unpaid', 'partial')
                AND invoice_type = 'issued'
            """
            result = db.fetch_one(query_today, (today,))
            today_count = result[0] if result else 0

            stats_text = f"""Nezaplaceno: {unpaid_count} ({unpaid_amount:,.0f} Kč)
Po splatnosti: {overdue_count} ({overdue_amount:,.0f} Kč)
Dnes splatné: {today_count}""".replace(",", " ")

            self.quick_stats.setText(stats_text)

        except Exception as e:
            self.quick_stats.setText(f"Chyba načítání: {e}")

    def refresh(self):
        """Obnovení dat modulu"""
        self.load_quick_stats()
        if self.current_section and hasattr(self.sections.get(self.current_section), 'refresh'):
            self.sections[self.current_section].refresh()

    def apply_styles(self):
        """Aplikace stylů"""
        self.setStyleSheet(f"""
            #adminNavPanel {{
                background-color: {config.COLOR_PRIMARY};
                border-right: 2px solid #1a252f;
            }}
            #adminNavHeader {{
                background-color: #1a252f;
                color: white;
            }}
            #adminNavButton {{
                background-color: transparent;
                border: none;
                color: white;
                text-align: left;
                padding: 15px 20px;
                font-size: 14px;
                border-left: 4px solid transparent;
            }}
            #adminNavButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            #adminNavButton[active="true"] {{
                background-color: {config.COLOR_SECONDARY};
                border-left: 4px solid {config.COLOR_SUCCESS};
            }}
            #adminInfoPanel {{
                background-color: #1a252f;
                color: white;
                padding: 10px;
            }}
            #adminTopBar {{
                background-color: white;
                border-bottom: 2px solid #e0e0e0;
            }}
            #adminContentPanel {{
                background-color: #f5f5f5;
            }}
            #adminSectionStack {{
                background-color: #f5f5f5;
            }}
            #adminQuickActionButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 13px;
                margin-left: 5px;
            }}
            #adminQuickActionButton:hover {{
                background-color: #2980b9;
            }}
            #adminQuickActionButton:pressed {{
                background-color: #21618c;
            }}
        """)
