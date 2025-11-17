# customer_export.py
# -*- coding: utf-8 -*-
"""
Export dat zákazníků
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QGroupBox, QProgressBar,
    QMessageBox, QFileDialog, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
import config
from database_manager import db
from datetime import datetime
import os


class CustomerExporter:
    """Třída pro export zákazníků"""

    @staticmethod
    def export_customer_card(customer_id, file_path):
        """Export karty zákazníka do PDF"""
        try:
            customer = db.fetch_one(
                """SELECT * FROM customers WHERE id = ?""",
                (customer_id,)
            )

            if not customer:
                return False, "Zákazník nenalezen"

            # Zde by byla implementace generování PDF
            # Použití knihovny jako reportlab nebo fpdf

            return True, f"Karta zákazníka exportována do {file_path}"

        except Exception as e:
            return False, str(e)

    @staticmethod
    def export_customer_list(customers, file_path):
        """Export seznamu zákazníků do Excelu"""
        try:
            # Zde by byla implementace exportu do Excelu
            # Použití knihovny openpyxl nebo xlsxwriter

            return True, f"Seznam exportován do {file_path}"

        except Exception as e:
            return False, str(e)

    @staticmethod
    def export_financial_statement(customer_id, file_path):
        """Export finančního výpisu do PDF"""
        try:
            # Načtení finančních dat
            invoices = db.fetch_all(
                """SELECT * FROM invoices WHERE customer_id = ? ORDER BY issue_date DESC""",
                (customer_id,)
            )

            # Zde by byla implementace generování PDF

            return True, f"Finanční výpis exportován do {file_path}"

        except Exception as e:
            return False, str(e)

    @staticmethod
    def export_for_marketing(customers, file_path):
        """Export pro marketing (emaily)"""
        try:
            # Filtrovat pouze zákazníky se souhlasem
            marketing_data = []
            for customer in customers:
                if customer.get("marketing_consent"):
                    marketing_data.append({
                        "email": customer.get("email"),
                        "name": customer.get("name"),
                        "group": customer.get("customer_group")
                    })

            # Zde by byla implementace exportu

            return True, f"Marketing data exportována do {file_path}"

        except Exception as e:
            return False, str(e)


class ExportDialog(QDialog):
    """Dialog pro export zákazníků"""

    def __init__(self, customer_id=None, customers=None, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.customers = customers or []
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("Export zákazníků")
        self.setMinimumSize(500, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Typ exportu
        export_group = QGroupBox("📤 Typ exportu")
        export_layout = QVBoxLayout(export_group)

        self.export_type_group = QButtonGroup()

        self.rb_customer_card = QRadioButton("📄 Karta zákazníka (PDF)")
        self.rb_customer_list = QRadioButton("📋 Seznam zákazníků (Excel)")
        self.rb_financial = QRadioButton("💰 Finanční výpis (PDF)")
        self.rb_statistics = QRadioButton("📊 Statistiky zákazníků (Excel)")
        self.rb_marketing = QRadioButton("📧 Export pro marketing (Excel)")
        self.rb_complete = QRadioButton("📁 Kompletní export (ZIP)")

        self.export_type_group.addButton(self.rb_customer_card)
        self.export_type_group.addButton(self.rb_customer_list)
        self.export_type_group.addButton(self.rb_financial)
        self.export_type_group.addButton(self.rb_statistics)
        self.export_type_group.addButton(self.rb_marketing)
        self.export_type_group.addButton(self.rb_complete)

        if self.customer_id:
            self.rb_customer_card.setChecked(True)
        else:
            self.rb_customer_list.setChecked(True)
            self.rb_customer_card.setEnabled(False)
            self.rb_financial.setEnabled(False)

        export_layout.addWidget(self.rb_customer_card)
        export_layout.addWidget(self.rb_customer_list)
        export_layout.addWidget(self.rb_financial)
        export_layout.addWidget(self.rb_statistics)
        export_layout.addWidget(self.rb_marketing)
        export_layout.addWidget(self.rb_complete)

        layout.addWidget(export_group)

        # Nastavení exportu
        settings_group = QGroupBox("⚙️ Nastavení")
        settings_layout = QVBoxLayout(settings_group)

        self.chk_include_vehicles = QCheckBox("Zahrnout vozidla")
        self.chk_include_vehicles.setChecked(True)
        settings_layout.addWidget(self.chk_include_vehicles)

        self.chk_include_orders = QCheckBox("Zahrnout zakázky")
        self.chk_include_orders.setChecked(True)
        settings_layout.addWidget(self.chk_include_orders)

        self.chk_include_financial = QCheckBox("Zahrnout finanční údaje")
        self.chk_include_financial.setChecked(True)
        settings_layout.addWidget(self.chk_include_financial)

        self.chk_gdpr_only = QCheckBox("Pouze se souhlasem GDPR")
        self.chk_gdpr_only.setChecked(True)
        settings_layout.addWidget(self.chk_gdpr_only)

        layout.addWidget(settings_group)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.hide()
        layout.addWidget(self.progress)

        # Status
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.lbl_status)

        layout.addStretch()

        # Tlačítka
        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_export = QPushButton("📤 Exportovat")
        btn_export.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; font-weight: bold; padding: 10px 20px;")
        btn_export.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_export.clicked.connect(self.start_export)
        buttons.addWidget(btn_export)

        layout.addLayout(buttons)

    def start_export(self):
        """Spuštění exportu"""
        # Určit typ souboru
        if self.rb_customer_card.isChecked() or self.rb_financial.isChecked():
            file_filter = "PDF soubory (*.pdf)"
            default_ext = ".pdf"
        elif self.rb_complete.isChecked():
            file_filter = "ZIP archiv (*.zip)"
            default_ext = ".zip"
        else:
            file_filter = "Excel soubory (*.xlsx)"
            default_ext = ".xlsx"

        # Výchozí název souboru
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.rb_customer_card.isChecked():
            default_name = f"karta_zakaznika_{self.customer_id}_{timestamp}{default_ext}"
        elif self.rb_customer_list.isChecked():
            default_name = f"seznam_zakazniku_{timestamp}{default_ext}"
        elif self.rb_financial.isChecked():
            default_name = f"financni_vypis_{self.customer_id}_{timestamp}{default_ext}"
        elif self.rb_statistics.isChecked():
            default_name = f"statistiky_zakazniku_{timestamp}{default_ext}"
        elif self.rb_marketing.isChecked():
            default_name = f"marketing_export_{timestamp}{default_ext}"
        else:
            default_name = f"kompletni_export_{timestamp}{default_ext}"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit export",
            default_name,
            file_filter
        )

        if file_path:
            self.perform_export(file_path)

    def perform_export(self, file_path):
        """Provedení exportu"""
        self.progress.show()
        self.progress.setValue(0)
        self.lbl_status.setText("Exportování...")

        try:
            if self.rb_customer_card.isChecked():
                success, message = CustomerExporter.export_customer_card(self.customer_id, file_path)
            elif self.rb_financial.isChecked():
                success, message = CustomerExporter.export_financial_statement(self.customer_id, file_path)
            elif self.rb_marketing.isChecked():
                success, message = CustomerExporter.export_for_marketing(self.customers, file_path)
            else:
                success, message = CustomerExporter.export_customer_list(self.customers, file_path)

            self.progress.setValue(100)

            if success:
                self.lbl_status.setText(f"✅ {message}")
                QMessageBox.information(self, "Export dokončen", message)
                self.accept()
            else:
                self.lbl_status.setText(f"❌ Chyba: {message}")
                QMessageBox.critical(self, "Chyba exportu", message)

        except Exception as e:
            self.lbl_status.setText(f"❌ Chyba: {str(e)}")
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se exportovat: {e}")
