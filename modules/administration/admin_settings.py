# -*- coding: utf-8 -*-
"""
Modul Administrativa - Nastavení (PRODUKČNÍ VERZE)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QFrame,
                             QComboBox, QLineEdit, QDateEdit, QHeaderView,
                             QMessageBox, QDialog, QFormLayout, QTextEdit,
                             QSpinBox, QDoubleSpinBox, QFileDialog, QCheckBox,
                             QGroupBox, QTabWidget, QScrollArea, QProgressBar)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPixmap
from datetime import datetime, timedelta, date
from pathlib import Path
import json
import config
from database_manager import db


class SettingsWidget(QWidget):
    """Widget pro nastavení administrativy"""

    settings_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Hlavička
        header_label = QLabel("⚙️ Nastavení administrativy")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)

        # Záložky
        tabs = QTabWidget()

        # Záložka: Firemní údaje
        self.tab_company = self.create_company_tab()
        tabs.addTab(self.tab_company, "🏢 Firemní údaje")

        # Záložka: Číselné řady
        self.tab_numbering = self.create_numbering_tab()
        tabs.addTab(self.tab_numbering, "🔢 Číselné řady")

        # Záložka: Splatnosti
        self.tab_payments = self.create_payments_tab()
        tabs.addTab(self.tab_payments, "💳 Splatnosti")

        # Záložka: DPH
        self.tab_vat = self.create_vat_tab()
        tabs.addTab(self.tab_vat, "📊 DPH")

        # Záložka: Emaily
        self.tab_emails = self.create_emails_tab()
        tabs.addTab(self.tab_emails, "📧 Emaily")

        # Záložka: Notifikace
        self.tab_notifications = self.create_notifications_tab()
        tabs.addTab(self.tab_notifications, "🔔 Notifikace")

        layout.addWidget(tabs)

        # Tlačítko uložit
        save_layout = QHBoxLayout()
        save_layout.addStretch()

        save_btn = QPushButton("💾 Uložit všechna nastavení")
        save_btn.clicked.connect(self.save_all_settings)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 12px 40px;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 4px;
            }}
        """)
        save_layout.addWidget(save_btn)

        layout.addLayout(save_layout)

    def create_company_tab(self):
        """Záložka: Firemní údaje"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout(widget)

        # Základní údaje
        basic_group = QGroupBox("Základní údaje")
        basic_layout = QFormLayout(basic_group)

        self.company_name = QLineEdit()
        self.company_name.setPlaceholderText("Název firmy nebo jméno OSVČ")
        basic_layout.addRow("Název firmy:", self.company_name)

        self.ico = QLineEdit()
        self.ico.setPlaceholderText("12345678")
        self.ico.setMaxLength(8)
        basic_layout.addRow("IČO:", self.ico)

        self.dic = QLineEdit()
        self.dic.setPlaceholderText("CZ12345678")
        basic_layout.addRow("DIČ:", self.dic)

        layout.addWidget(basic_group)

        # Adresa
        address_group = QGroupBox("Adresa")
        address_layout = QFormLayout(address_group)

        self.street = QLineEdit()
        address_layout.addRow("Ulice a číslo:", self.street)

        self.city = QLineEdit()
        address_layout.addRow("Město:", self.city)

        self.zip_code = QLineEdit()
        self.zip_code.setPlaceholderText("12345")
        self.zip_code.setMaxLength(5)
        address_layout.addRow("PSČ:", self.zip_code)

        layout.addWidget(address_group)

        # Kontakty
        contact_group = QGroupBox("Kontaktní údaje")
        contact_layout = QFormLayout(contact_group)

        self.phone = QLineEdit()
        self.phone.setPlaceholderText("+420 123 456 789")
        contact_layout.addRow("Telefon:", self.phone)

        self.email = QLineEdit()
        self.email.setPlaceholderText("firma@email.cz")
        contact_layout.addRow("Email:", self.email)

        self.website = QLineEdit()
        self.website.setPlaceholderText("www.firma.cz")
        contact_layout.addRow("Web:", self.website)

        layout.addWidget(contact_group)

        # Bankovní spojení
        bank_group = QGroupBox("Bankovní spojení")
        bank_layout = QFormLayout(bank_group)

        self.account_number = QLineEdit()
        self.account_number.setPlaceholderText("123456789/0100")
        bank_layout.addRow("Číslo účtu:", self.account_number)

        self.iban = QLineEdit()
        self.iban.setPlaceholderText("CZ65 0800 0000 1920 0014 5399")
        bank_layout.addRow("IBAN:", self.iban)

        self.swift = QLineEdit()
        self.swift.setPlaceholderText("GIBACZPX")
        bank_layout.addRow("SWIFT/BIC:", self.swift)

        layout.addWidget(bank_group)

        # Registrace
        registration_group = QGroupBox("Registrace")
        registration_layout = QFormLayout(registration_group)

        self.court_registration = QLineEdit()
        self.court_registration.setPlaceholderText("Městský soud v Praze, oddíl C, vložka 12345")
        registration_layout.addRow("Zápis v OR:", self.court_registration)

        self.vat_registered = QCheckBox("Jsme plátci DPH")
        registration_layout.addRow("", self.vat_registered)

        layout.addWidget(registration_group)

        # Logo firmy
        logo_group = QGroupBox("Logo firmy")
        logo_layout = QVBoxLayout(logo_group)

        self.logo_preview = QLabel("Žádné logo")
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setMinimumHeight(150)
        self.logo_preview.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 8px;
            }
        """)
        logo_layout.addWidget(self.logo_preview)

        logo_buttons = QHBoxLayout()

        upload_logo_btn = QPushButton("📁 Nahrát logo")
        upload_logo_btn.clicked.connect(self.upload_logo)
        logo_buttons.addWidget(upload_logo_btn)

        remove_logo_btn = QPushButton("🗑️ Odebrat logo")
        remove_logo_btn.clicked.connect(self.remove_logo)
        logo_buttons.addWidget(remove_logo_btn)

        logo_buttons.addStretch()
        logo_layout.addLayout(logo_buttons)

        layout.addWidget(logo_group)

        layout.addStretch()

        return scroll

    def create_numbering_tab(self):
        """Záložka: Číselné řady"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout(widget)

        # Info
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)

        info_title = QLabel("💡 Informace o číselných řadách")
        info_font = QFont()
        info_font.setBold(True)
        info_title.setFont(info_font)
        info_layout.addWidget(info_title)

        info_text = QLabel(
            "Číselné řady slouží pro automatické generování čísel dokladů.\n"
            "Můžete použít proměnné:\n"
            "• {YYYY} - rok 4 číslice (2025)\n"
            "• {YY} - rok 2 číslice (25)\n"
            "• {MM} - měsíc (01-12)\n"
            "• {NUMBER} - pořadové číslo s automatickým doplněním nul"
        )
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)

        layout.addWidget(info_frame)

        # Vydané faktury
        issued_group = QGroupBox("📤 Vydané faktury")
        issued_layout = QFormLayout(issued_group)

        self.issued_prefix = QLineEdit()
        self.issued_prefix.setPlaceholderText("FV")
        issued_layout.addRow("Prefix:", self.issued_prefix)

        self.issued_format = QLineEdit()
        self.issued_format.setText("{PREFIX}{YYYY}{NUMBER:05d}")
        self.issued_format.setPlaceholderText("{PREFIX}{YYYY}{NUMBER:05d}")
        issued_layout.addRow("Formát:", self.issued_format)

        self.issued_start_number = QSpinBox()
        self.issued_start_number.setRange(1, 999999)
        self.issued_start_number.setValue(1)
        issued_layout.addRow("Počáteční číslo:", self.issued_start_number)

        self.issued_reset_yearly = QCheckBox("Resetovat každý rok")
        self.issued_reset_yearly.setChecked(True)
        issued_layout.addRow("", self.issued_reset_yearly)

        # Ukázka
        issued_example = QLabel()
        issued_example.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.issued_example_label = issued_example
        issued_layout.addRow("Ukázka:", issued_example)

        layout.addWidget(issued_group)

        # Přijaté faktury
        received_group = QGroupBox("📥 Přijaté faktury")
        received_layout = QFormLayout(received_group)

        self.received_prefix = QLineEdit()
        self.received_prefix.setPlaceholderText("FP")
        received_layout.addRow("Prefix:", self.received_prefix)

        self.received_format = QLineEdit()
        self.received_format.setText("{PREFIX}{YYYY}{NUMBER:05d}")
        received_layout.addRow("Formát:", self.received_format)

        self.received_start_number = QSpinBox()
        self.received_start_number.setRange(1, 999999)
        self.received_start_number.setValue(1)
        received_layout.addRow("Počáteční číslo:", self.received_start_number)

        self.received_reset_yearly = QCheckBox("Resetovat každý rok")
        self.received_reset_yearly.setChecked(True)
        received_layout.addRow("", self.received_reset_yearly)

        # Ukázka
        received_example = QLabel()
        received_example.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.received_example_label = received_example
        received_layout.addRow("Ukázka:", received_example)

        layout.addWidget(received_group)

        # Dobropisy
        credit_group = QGroupBox("📋 Dobropisy")
        credit_layout = QFormLayout(credit_group)

        self.credit_prefix = QLineEdit()
        self.credit_prefix.setPlaceholderText("DB")
        credit_layout.addRow("Prefix:", self.credit_prefix)

        self.credit_format = QLineEdit()
        self.credit_format.setText("{PREFIX}{YYYY}{NUMBER:05d}")
        credit_layout.addRow("Formát:", self.credit_format)

        layout.addWidget(credit_group)

        # Propojení pro aktualizaci ukázek
        self.issued_prefix.textChanged.connect(self.update_numbering_examples)
        self.issued_format.textChanged.connect(self.update_numbering_examples)
        self.received_prefix.textChanged.connect(self.update_numbering_examples)
        self.received_format.textChanged.connect(self.update_numbering_examples)

        layout.addStretch()

        return scroll

    def create_payments_tab(self):
        """Záložka: Splatnosti"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout(widget)

        # Výchozí splatnost
        due_group = QGroupBox("⏱️ Výchozí splatnost")
        due_layout = QFormLayout(due_group)

        self.default_due_days = QSpinBox()
        self.default_due_days.setRange(0, 365)
        self.default_due_days.setValue(14)
        self.default_due_days.setSuffix(" dní")
        due_layout.addRow("Splatnost faktur:", self.default_due_days)

        layout.addWidget(due_group)

        # Výchozí forma úhrady
        payment_group = QGroupBox("💳 Forma úhrady")
        payment_layout = QFormLayout(payment_group)

        self.default_payment_method = QComboBox()
        self.default_payment_method.addItems([
            "Bankovní převod",
            "Hotovost",
            "Karta",
            "Dobírka"
        ])
        payment_layout.addRow("Výchozí forma:", self.default_payment_method)

        layout.addWidget(payment_group)

        # Penále
        penalty_group = QGroupBox("⚠️ Penále z prodlení")
        penalty_layout = QFormLayout(penalty_group)

        self.penalty_enabled = QCheckBox("Účtovat penále z prodlení")
        penalty_layout.addRow("", self.penalty_enabled)

        self.penalty_rate = QDoubleSpinBox()
        self.penalty_rate.setRange(0, 10)
        self.penalty_rate.setValue(0.05)
        self.penalty_rate.setSuffix(" % denně")
        self.penalty_rate.setDecimals(2)
        self.penalty_rate.setEnabled(False)
        self.penalty_enabled.stateChanged.connect(
            lambda state: self.penalty_rate.setEnabled(state == Qt.CheckState.Checked.value)
        )
        penalty_layout.addRow("Sazba penále:", self.penalty_rate)

        penalty_info = QLabel("Zákonná sazba je 0,05% denně z dlužné částky (repo sazba ČNB + 8 p.b.)")
        penalty_info.setStyleSheet("color: #7f8c8d; font-size: 9pt;")
        penalty_info.setWordWrap(True)
        penalty_layout.addRow("", penalty_info)

        layout.addWidget(penalty_group)

        # Upomínky
        reminder_group = QGroupBox("📧 Upomínky")
        reminder_layout = QFormLayout(reminder_group)

        self.reminder_1_days = QSpinBox()
        self.reminder_1_days.setRange(1, 30)
        self.reminder_1_days.setValue(7)
        self.reminder_1_days.setSuffix(" dní po splatnosti")
        reminder_layout.addRow("1. upomínka:", self.reminder_1_days)

        self.reminder_2_days = QSpinBox()
        self.reminder_2_days.setRange(1, 60)
        self.reminder_2_days.setValue(14)
        self.reminder_2_days.setSuffix(" dní po splatnosti")
        reminder_layout.addRow("2. upomínka:", self.reminder_2_days)

        self.reminder_3_days = QSpinBox()
        self.reminder_3_days.setRange(1, 90)
        self.reminder_3_days.setValue(30)
        self.reminder_3_days.setSuffix(" dní po splatnosti")
        reminder_layout.addRow("3. upomínka:", self.reminder_3_days)

        self.reminder_fee = QDoubleSpinBox()
        self.reminder_fee.setRange(0, 10000)
        self.reminder_fee.setValue(200)
        self.reminder_fee.setSuffix(" Kč")
        reminder_layout.addRow("Poplatek za upomínku:", self.reminder_fee)

        layout.addWidget(reminder_group)

        layout.addStretch()

        return scroll

    def create_vat_tab(self):
        """Záložka: DPH"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout(widget)

        # Plátce DPH
        vat_payer_group = QGroupBox("📊 Plátce DPH")
        vat_payer_layout = QVBoxLayout(vat_payer_group)

        self.vat_payer = QCheckBox("Jsme plátci DPH")
        self.vat_payer.setChecked(True)
        vat_payer_layout.addWidget(self.vat_payer)

        vat_info = QLabel(
            "Pokud nejste plátci DPH, nebudou se u faktur zobrazovat řádky s DPH."
        )
        vat_info.setWordWrap(True)
        vat_info.setStyleSheet("color: #7f8c8d; margin-top: 10px;")
        vat_payer_layout.addWidget(vat_info)

        layout.addWidget(vat_payer_group)

        # Sazby DPH
        rates_group = QGroupBox("💰 Sazby DPH")
        rates_layout = QFormLayout(rates_group)

        self.vat_rate_standard = QDoubleSpinBox()
        self.vat_rate_standard.setRange(0, 100)
        self.vat_rate_standard.setValue(21)
        self.vat_rate_standard.setSuffix(" %")
        rates_layout.addRow("Základní sazba:", self.vat_rate_standard)

        self.vat_rate_reduced = QDoubleSpinBox()
        self.vat_rate_reduced.setRange(0, 100)
        self.vat_rate_reduced.setValue(12)
        self.vat_rate_reduced.setSuffix(" %")
        rates_layout.addRow("Snížená sazba:", self.vat_rate_reduced)

        layout.addWidget(rates_group)

        # Výchozí sazba
        default_group = QGroupBox("⚙️ Výchozí nastavení")
        default_layout = QFormLayout(default_group)

        self.default_vat_rate = QComboBox()
        self.default_vat_rate.addItem("Základní (21%)", 21)
        self.default_vat_rate.addItem("Snížená (12%)", 12)
        self.default_vat_rate.addItem("Osvobozeno (0%)", 0)
        default_layout.addRow("Výchozí sazba:", self.default_vat_rate)

        layout.addWidget(default_group)

        # Způsob evidence
        evidence_group = QGroupBox("📋 Způsob evidence DPH")
        evidence_layout = QVBoxLayout(evidence_group)

        self.vat_frequency = QComboBox()
        self.vat_frequency.addItem("Měsíční", "monthly")
        self.vat_frequency.addItem("Čtvrtletní", "quarterly")
        self.vat_frequency.addItem("Roční", "yearly")
        evidence_layout.addWidget(QLabel("Frekvence podání:"))
        evidence_layout.addWidget(self.vat_frequency)

        layout.addWidget(evidence_group)

        # Kontrolní hlášení
        control_group = QGroupBox("📊 Kontrolní hlášení")
        control_layout = QVBoxLayout(control_group)

        self.control_report = QCheckBox("Podávám kontrolní hlášení")
        control_layout.addWidget(self.control_report)

        control_info = QLabel(
            "Kontrolní hlášení podávají plátci s obratem nad 10 mil. Kč ročně."
        )
        control_info.setWordWrap(True)
        control_info.setStyleSheet("color: #7f8c8d;")
        control_layout.addWidget(control_info)

        layout.addWidget(control_group)

        layout.addStretch()

        return scroll

    def create_emails_tab(self):
        """Záložka: Emaily"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout(widget)

        # Automatické zasílání
        auto_group = QGroupBox("📧 Automatické zasílání")
        auto_layout = QVBoxLayout(auto_group)

        self.auto_send_invoices = QCheckBox("Automaticky odesílat faktury emailem po vytvoření")
        auto_layout.addWidget(self.auto_send_invoices)

        self.auto_send_reminders = QCheckBox("Automaticky odesílat upomínky")
        auto_layout.addWidget(self.auto_send_reminders)

        layout.addWidget(auto_group)

        # Kopie
        copies_group = QGroupBox("📋 Kopie emailů")
        copies_layout = QFormLayout(copies_group)

        self.email_cc = QLineEdit()
        self.email_cc.setPlaceholderText("kopie@firma.cz")
        copies_layout.addRow("CC (kopie):", self.email_cc)

        self.email_bcc = QLineEdit()
        self.email_bcc.setPlaceholderText("skryta-kopie@firma.cz")
        copies_layout.addRow("BCC (skrytá kopie):", self.email_bcc)

        layout.addWidget(copies_group)

        # Šablony
        templates_group = QGroupBox("📝 Šablony emailů")
        templates_layout = QVBoxLayout(templates_group)

        # Faktura
        invoice_template_label = QLabel("<b>Šablona pro fakturu:</b>")
        templates_layout.addWidget(invoice_template_label)

        self.invoice_email_subject = QLineEdit()
        self.invoice_email_subject.setPlaceholderText("Faktura {{invoice_number}}")
        templates_layout.addWidget(QLabel("Předmět:"))
        templates_layout.addWidget(self.invoice_email_subject)

        self.invoice_email_body = QTextEdit()
        self.invoice_email_body.setMaximumHeight(100)
        self.invoice_email_body.setPlaceholderText(
            "Dobrý den,\n\n"
            "zasíláme fakturu č. {{invoice_number}}.\n\n"
            "S pozdravem"
        )
        templates_layout.addWidget(QLabel("Text:"))
        templates_layout.addWidget(self.invoice_email_body)

        # Upomínka
        reminder_template_label = QLabel("<b>Šablona pro upomínku:</b>")
        reminder_template_label.setStyleSheet("margin-top: 15px;")
        templates_layout.addWidget(reminder_template_label)

        self.reminder_email_subject = QLineEdit()
        self.reminder_email_subject.setPlaceholderText("Upomínka - {{invoice_number}}")
        templates_layout.addWidget(QLabel("Předmět:"))
        templates_layout.addWidget(self.reminder_email_subject)

        self.reminder_email_body = QTextEdit()
        self.reminder_email_body.setMaximumHeight(100)
        self.reminder_email_body.setPlaceholderText(
            "Vážený zákazníku,\n\n"
            "upozorňujeme na po splatnosti faktury {{invoice_number}}.\n\n"
            "S pozdravem"
        )
        templates_layout.addWidget(QLabel("Text:"))
        templates_layout.addWidget(self.reminder_email_body)

        layout.addWidget(templates_group)

        # Info o proměnných
        vars_info = QLabel(
            "💡 Můžete použít proměnné: {{invoice_number}}, {{customer_name}}, "
            "{{total_with_vat}}, {{due_date}}"
        )
        vars_info.setWordWrap(True)
        vars_info.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                padding: 10px;
                border-radius: 4px;
                margin-top: 10px;
            }
        """)
        layout.addWidget(vars_info)

        layout.addStretch()

        return scroll

    def create_notifications_tab(self):
        """Záložka: Notifikace"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout(widget)

        # Upozornění na splatnosti
        due_group = QGroupBox("⏰ Upozornění na blížící se splatnost")
        due_layout = QVBoxLayout(due_group)

        self.notify_before_due = QCheckBox("Upozornit před splatností")
        self.notify_before_due.setChecked(True)
        due_layout.addWidget(self.notify_before_due)

        before_layout = QHBoxLayout()
        before_layout.addWidget(QLabel("Upozornit"))
        self.notify_before_days = QSpinBox()
        self.notify_before_days.setRange(1, 30)
        self.notify_before_days.setValue(3)
        self.notify_before_days.setSuffix(" dní před")
        before_layout.addWidget(self.notify_before_days)
        before_layout.addWidget(QLabel("splatností"))
        before_layout.addStretch()
        due_layout.addLayout(before_layout)

        layout.addWidget(due_group)

        # Upozornění po splatnosti
        overdue_group = QGroupBox("⚠️ Upozornění po splatnosti")
        overdue_layout = QVBoxLayout(overdue_group)

        self.notify_overdue = QCheckBox("Upozornit na faktury po splatnosti")
        self.notify_overdue.setChecked(True)
        overdue_layout.addWidget(self.notify_overdue)

        self.notify_overdue_daily = QCheckBox("Denní upozornění")
        overdue_layout.addWidget(self.notify_overdue_daily)

        layout.addWidget(overdue_group)

        # Souhrny
        summary_group = QGroupBox("📊 Pravidelné souhrny")
        summary_layout = QVBoxLayout(summary_group)

        self.daily_summary = QCheckBox("Denní souhrn (každé ráno)")
        summary_layout.addWidget(self.daily_summary)

        daily_time_layout = QHBoxLayout()
        daily_time_layout.addWidget(QLabel("Čas odeslání:"))
        self.daily_summary_time = QComboBox()
        for hour in range(24):
            self.daily_summary_time.addItem(f"{hour:02d}:00")
        self.daily_summary_time.setCurrentIndex(8)  # 8:00
        daily_time_layout.addWidget(self.daily_summary_time)
        daily_time_layout.addStretch()
        summary_layout.addLayout(daily_time_layout)

        self.weekly_summary = QCheckBox("Týdenní souhrn (každé pondělí)")
        summary_layout.addWidget(self.weekly_summary)

        self.monthly_summary = QCheckBox("Měsíční souhrn (první den v měsíci)")
        summary_layout.addWidget(self.monthly_summary)

        layout.addWidget(summary_group)

        # Způsob upozornění
        method_group = QGroupBox("📱 Způsob upozornění")
        method_layout = QVBoxLayout(method_group)

        self.notify_email = QCheckBox("Email")
        self.notify_email.setChecked(True)
        method_layout.addWidget(self.notify_email)

        email_address_layout = QHBoxLayout()
        email_address_layout.addWidget(QLabel("Email pro notifikace:"))
        self.notify_email_address = QLineEdit()
        self.notify_email_address.setPlaceholderText("notifikace@firma.cz")
        email_address_layout.addWidget(self.notify_email_address)
        method_layout.addLayout(email_address_layout)

        self.notify_system = QCheckBox("Systémové notifikace v aplikaci")
        self.notify_system.setChecked(True)
        method_layout.addWidget(self.notify_system)

        layout.addWidget(method_group)

        layout.addStretch()

        return scroll

    # =====================================================
    # NAČÍTÁNÍ A UKLÁDÁNÍ NASTAVENÍ
    # =====================================================

    def load_settings(self):
        """Načtení všech nastavení"""
        try:
            query = "SELECT setting_key, setting_value FROM admin_settings"
            settings = db.fetch_all(query)

            settings_dict = {s["setting_key"]: s["setting_value"] for s in settings}

            # Firemní údaje
            self.company_name.setText(settings_dict.get("company_name", ""))
            self.ico.setText(settings_dict.get("ico", ""))
            self.dic.setText(settings_dict.get("dic", ""))
            self.street.setText(settings_dict.get("street", ""))
            self.city.setText(settings_dict.get("city", ""))
            self.zip_code.setText(settings_dict.get("zip_code", ""))
            self.phone.setText(settings_dict.get("phone", ""))
            self.email.setText(settings_dict.get("email", ""))
            self.website.setText(settings_dict.get("website", ""))
            self.account_number.setText(settings_dict.get("account_number", ""))
            self.iban.setText(settings_dict.get("iban", ""))
            self.swift.setText(settings_dict.get("swift", ""))
            self.court_registration.setText(settings_dict.get("court_registration", ""))
            self.vat_registered.setChecked(settings_dict.get("vat_registered", "0") == "1")

            # Logo
            logo_path = settings_dict.get("logo_path", "")
            if logo_path and Path(logo_path).exists():
                pixmap = QPixmap(logo_path)
                scaled_pixmap = pixmap.scaled(
                    300, 150,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.logo_preview.setPixmap(scaled_pixmap)
            else:
                self.logo_preview.setText("Žádné logo")

            # Číselné řady
            self.issued_prefix.setText(settings_dict.get("issued_invoice_prefix", "FV"))
            self.issued_format.setText(settings_dict.get("issued_invoice_format", "{PREFIX}{YYYY}{NUMBER:05d}"))
            self.issued_start_number.setValue(int(settings_dict.get("issued_invoice_start", "1")))
            self.issued_reset_yearly.setChecked(settings_dict.get("issued_invoice_reset_yearly", "1") == "1")

            self.received_prefix.setText(settings_dict.get("received_invoice_prefix", "FP"))
            self.received_format.setText(settings_dict.get("received_invoice_format", "{PREFIX}{YYYY}{NUMBER:05d}"))
            self.received_start_number.setValue(int(settings_dict.get("received_invoice_start", "1")))
            self.received_reset_yearly.setChecked(settings_dict.get("received_invoice_reset_yearly", "1") == "1")

            self.credit_prefix.setText(settings_dict.get("credit_note_prefix", "DB"))
            self.credit_format.setText(settings_dict.get("credit_note_format", "{PREFIX}{YYYY}{NUMBER:05d}"))

            # Splatnosti
            self.default_due_days.setValue(int(settings_dict.get("default_due_days", "14")))
            index = self.default_payment_method.findText(settings_dict.get("default_payment_method", "Bankovní převod"))
            if index >= 0:
                self.default_payment_method.setCurrentIndex(index)

            self.penalty_enabled.setChecked(settings_dict.get("penalty_enabled", "0") == "1")
            self.penalty_rate.setValue(float(settings_dict.get("penalty_rate", "0.05")))
            self.reminder_1_days.setValue(int(settings_dict.get("reminder_1_days", "7")))
            self.reminder_2_days.setValue(int(settings_dict.get("reminder_2_days", "14")))
            self.reminder_3_days.setValue(int(settings_dict.get("reminder_3_days", "30")))
            self.reminder_fee.setValue(float(settings_dict.get("reminder_fee", "200")))

            # DPH
            self.vat_payer.setChecked(settings_dict.get("vat_payer", "1") == "1")
            self.vat_rate_standard.setValue(float(settings_dict.get("vat_rate_standard", "21")))
            self.vat_rate_reduced.setValue(float(settings_dict.get("vat_rate_reduced", "12")))

            default_vat = int(settings_dict.get("default_vat_rate", "21"))
            index = self.default_vat_rate.findData(default_vat)
            if index >= 0:
                self.default_vat_rate.setCurrentIndex(index)

            vat_freq = settings_dict.get("vat_frequency", "monthly")
            index = self.vat_frequency.findData(vat_freq)
            if index >= 0:
                self.vat_frequency.setCurrentIndex(index)

            self.control_report.setChecked(settings_dict.get("control_report", "0") == "1")

            # Emaily
            self.auto_send_invoices.setChecked(settings_dict.get("auto_send_invoices", "0") == "1")
            self.auto_send_reminders.setChecked(settings_dict.get("auto_send_reminders", "0") == "1")
            self.email_cc.setText(settings_dict.get("email_cc", ""))
            self.email_bcc.setText(settings_dict.get("email_bcc", ""))

            self.invoice_email_subject.setText(settings_dict.get("invoice_email_subject", "Faktura {{invoice_number}}"))
            self.invoice_email_body.setPlainText(settings_dict.get("invoice_email_body", ""))

            self.reminder_email_subject.setText(settings_dict.get("reminder_email_subject", "Upomínka - {{invoice_number}}"))
            self.reminder_email_body.setPlainText(settings_dict.get("reminder_email_body", ""))

            # Notifikace
            self.notify_before_due.setChecked(settings_dict.get("notify_before_due", "1") == "1")
            self.notify_before_days.setValue(int(settings_dict.get("notify_before_days", "3")))
            self.notify_overdue.setChecked(settings_dict.get("notify_overdue", "1") == "1")
            self.notify_overdue_daily.setChecked(settings_dict.get("notify_overdue_daily", "0") == "1")

            self.daily_summary.setChecked(settings_dict.get("daily_summary", "0") == "1")
            summary_time = settings_dict.get("daily_summary_time", "8")
            index = self.daily_summary_time.findText(f"{int(summary_time):02d}:00")
            if index >= 0:
                self.daily_summary_time.setCurrentIndex(index)

            self.weekly_summary.setChecked(settings_dict.get("weekly_summary", "0") == "1")
            self.monthly_summary.setChecked(settings_dict.get("monthly_summary", "0") == "1")

            self.notify_email.setChecked(settings_dict.get("notify_email", "1") == "1")
            self.notify_email_address.setText(settings_dict.get("notify_email_address", ""))
            self.notify_system.setChecked(settings_dict.get("notify_system", "1") == "1")

            # Aktualizovat ukázky
            self.update_numbering_examples()

        except Exception as e:
            print(f"Chyba při načítání nastavení: {e}")

    def save_all_settings(self):
        """Uložení všech nastavení"""
        try:
            settings = {
                # Firemní údaje
                "company_name": self.company_name.text().strip(),
                "ico": self.ico.text().strip(),
                "dic": self.dic.text().strip(),
                "street": self.street.text().strip(),
                "city": self.city.text().strip(),
                "zip_code": self.zip_code.text().strip(),
                "phone": self.phone.text().strip(),
                "email": self.email.text().strip(),
                "website": self.website.text().strip(),
                "account_number": self.account_number.text().strip(),
                "iban": self.iban.text().strip(),
                "swift": self.swift.text().strip(),
                "court_registration": self.court_registration.text().strip(),
                "vat_registered": "1" if self.vat_registered.isChecked() else "0",

                # Číselné řady
                "issued_invoice_prefix": self.issued_prefix.text().strip(),
                "issued_invoice_format": self.issued_format.text().strip(),
                "issued_invoice_start": str(self.issued_start_number.value()),
                "issued_invoice_reset_yearly": "1" if self.issued_reset_yearly.isChecked() else "0",

                "received_invoice_prefix": self.received_prefix.text().strip(),
                "received_invoice_format": self.received_format.text().strip(),
                "received_invoice_start": str(self.received_start_number.value()),
                "received_invoice_reset_yearly": "1" if self.received_reset_yearly.isChecked() else "0",

                "credit_note_prefix": self.credit_prefix.text().strip(),
                "credit_note_format": self.credit_format.text().strip(),

                # Splatnosti
                "default_due_days": str(self.default_due_days.value()),
                "default_payment_method": self.default_payment_method.currentText(),
                "penalty_enabled": "1" if self.penalty_enabled.isChecked() else "0",
                "penalty_rate": str(self.penalty_rate.value()),
                "reminder_1_days": str(self.reminder_1_days.value()),
                "reminder_2_days": str(self.reminder_2_days.value()),
                "reminder_3_days": str(self.reminder_3_days.value()),
                "reminder_fee": str(self.reminder_fee.value()),

                # DPH
                "vat_payer": "1" if self.vat_payer.isChecked() else "0",
                "vat_rate_standard": str(self.vat_rate_standard.value()),
                "vat_rate_reduced": str(self.vat_rate_reduced.value()),
                "default_vat_rate": str(self.default_vat_rate.currentData()),
                "vat_frequency": self.vat_frequency.currentData(),
                "control_report": "1" if self.control_report.isChecked() else "0",

                # Emaily
                "auto_send_invoices": "1" if self.auto_send_invoices.isChecked() else "0",
                "auto_send_reminders": "1" if self.auto_send_reminders.isChecked() else "0",
                "email_cc": self.email_cc.text().strip(),
                "email_bcc": self.email_bcc.text().strip(),
                "invoice_email_subject": self.invoice_email_subject.text().strip(),
                "invoice_email_body": self.invoice_email_body.toPlainText().strip(),
                "reminder_email_subject": self.reminder_email_subject.text().strip(),
                "reminder_email_body": self.reminder_email_body.toPlainText().strip(),

                # Notifikace
                "notify_before_due": "1" if self.notify_before_due.isChecked() else "0",
                "notify_before_days": str(self.notify_before_days.value()),
                "notify_overdue": "1" if self.notify_overdue.isChecked() else "0",
                "notify_overdue_daily": "1" if self.notify_overdue_daily.isChecked() else "0",
                "daily_summary": "1" if self.daily_summary.isChecked() else "0",
                "daily_summary_time": str(self.daily_summary_time.currentIndex()),
                "weekly_summary": "1" if self.weekly_summary.isChecked() else "0",
                "monthly_summary": "1" if self.monthly_summary.isChecked() else "0",
                "notify_email": "1" if self.notify_email.isChecked() else "0",
                "notify_email_address": self.notify_email_address.text().strip(),
                "notify_system": "1" if self.notify_system.isChecked() else "0",
            }

            # Uložit do databáze
            for key, value in settings.items():
                query = """
                    INSERT INTO admin_settings (setting_key, setting_value)
                    VALUES (?, ?)
                    ON CONFLICT(setting_key) DO UPDATE SET setting_value = ?
                """
                db.execute_query(query, (key, value, value))

            QMessageBox.information(self, "Úspěch", "Všechna nastavení byla uložena.")
            self.settings_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit nastavení:\n{e}")

    # =====================================================
    # POMOCNÉ METODY
    # =====================================================

    def update_numbering_examples(self):
        """Aktualizace ukázek číslování"""
        try:
            # Vydané faktury
            prefix = self.issued_prefix.text() or "FV"
            format_str = self.issued_format.text() or "{PREFIX}{YYYY}{NUMBER:05d}"

            example = format_str.replace("{PREFIX}", prefix)
            example = example.replace("{YYYY}", "2025")
            example = example.replace("{YY}", "25")
            example = example.replace("{MM}", "01")

            # Najít a nahradit {NUMBER:XXd}
            import re
            number_match = re.search(r'\{NUMBER:(\d+)d\}', example)
            if number_match:
                width = int(number_match.group(1))
                example = re.sub(r'\{NUMBER:\d+d\}', str(1).zfill(width), example)
            else:
                example = example.replace("{NUMBER}", "1")

            self.issued_example_label.setText(f"Příklad: {example}")

            # Přijaté faktury
            prefix = self.received_prefix.text() or "FP"
            format_str = self.received_format.text() or "{PREFIX}{YYYY}{NUMBER:05d}"

            example = format_str.replace("{PREFIX}", prefix)
            example = example.replace("{YYYY}", "2025")
            example = example.replace("{YY}", "25")
            example = example.replace("{MM}", "01")

            number_match = re.search(r'\{NUMBER:(\d+)d\}', example)
            if number_match:
                width = int(number_match.group(1))
                example = re.sub(r'\{NUMBER:\d+d\}', str(1).zfill(width), example)
            else:
                example = example.replace("{NUMBER}", "1")

            self.received_example_label.setText(f"Příklad: {example}")

        except Exception as e:
            print(f"Chyba při aktualizaci ukázek: {e}")

    def upload_logo(self):
        """Nahrání loga"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Vyberte logo",
            "",
            "Obrázky (*.png *.jpg *.jpeg)"
        )

        if not file_path:
            return

        try:
            # Zkopírovat do data/logos
            logos_dir = Path(config.DATA_DIR) / "logos"
            logos_dir.mkdir(parents=True, exist_ok=True)

            source_path = Path(file_path)
            dest_filename = f"company_logo{source_path.suffix}"
            dest_path = logos_dir / dest_filename

            import shutil
            shutil.copy2(source_path, dest_path)

            # Uložit cestu do nastavení
            query = """
                INSERT INTO admin_settings (setting_key, setting_value)
                VALUES ('logo_path', ?)
                ON CONFLICT(setting_key) DO UPDATE SET setting_value = ?
            """
            db.execute_query(query, (str(dest_path), str(dest_path)))

            # Zobrazit náhled
            pixmap = QPixmap(str(dest_path))
            scaled_pixmap = pixmap.scaled(
                300, 150,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.logo_preview.setPixmap(scaled_pixmap)

            QMessageBox.information(self, "Úspěch", "Logo bylo nahráno.")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se nahrát logo:\n{e}")

    def remove_logo(self):
        """Odebrání loga"""
        try:
            query = "DELETE FROM admin_settings WHERE setting_key = 'logo_path'"
            db.execute_query(query)

            self.logo_preview.clear()
            self.logo_preview.setText("Žádné logo")

            QMessageBox.information(self, "Úspěch", "Logo bylo odebráno.")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se odebrat logo:\n{e}")

    def refresh(self):
        """Obnovení nastavení"""
        self.load_settings()
