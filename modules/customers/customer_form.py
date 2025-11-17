# customer_form.py
# -*- coding: utf-8 -*-
"""
Dialog pro vytvoření/editaci zákazníka
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QWidget, QLabel, QLineEdit, QComboBox, QTextEdit, QCheckBox,
    QPushButton, QRadioButton, QButtonGroup, QGroupBox, QSpinBox,
    QDoubleSpinBox, QDateEdit, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QDate, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator, QFont, QCursor
import config
from database_manager import db
import re


class CustomerFormDialog(QDialog):
    """Dialog pro vytvoření/editaci zákazníka"""

    def __init__(self, parent=None, customer_id=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.is_edit_mode = customer_id is not None
        self.init_ui()
        if self.is_edit_mode:
            self.load_customer_data()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("Nový zákazník" if not self.is_edit_mode else "Upravit zákazníka")
        self.setMinimumSize(800, 700)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Záložky
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_basic_tab(), "📋 Základní údaje")
        self.tabs.addTab(self.create_contact_tab(), "📞 Kontaktní údaje")
        self.tabs.addTab(self.create_address_tab(), "🏠 Adresa")
        self.tabs.addTab(self.create_billing_tab(), "💰 Fakturační údaje")
        self.tabs.addTab(self.create_group_tab(), "👥 Zákaznická skupina")
        self.tabs.addTab(self.create_notes_tab(), "📝 Poznámky")

        layout.addWidget(self.tabs)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Uložit")
        btn_save.setObjectName("btnSave")
        btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save.clicked.connect(self.save_customer)
        buttons_layout.addWidget(btn_save)

        btn_save_open = QPushButton("💾 Uložit a otevřít detail")
        btn_save_open.setObjectName("btnSaveOpen")
        btn_save_open.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save_open.clicked.connect(self.save_and_open)
        buttons_layout.addWidget(btn_save_open)

        layout.addLayout(buttons_layout)

        self.set_styles()

    def create_basic_tab(self):
        """Záložka základních údajů"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # Typ zákazníka
        type_group = QGroupBox("Typ zákazníka")
        type_layout = QHBoxLayout(type_group)

        self.type_group = QButtonGroup()
        self.rb_personal = QRadioButton("Soukromá osoba")
        self.rb_company = QRadioButton("Firma")
        self.type_group.addButton(self.rb_personal)
        self.type_group.addButton(self.rb_company)
        self.rb_personal.setChecked(True)

        self.rb_personal.toggled.connect(self.toggle_customer_type)

        type_layout.addWidget(self.rb_personal)
        type_layout.addWidget(self.rb_company)
        type_layout.addStretch()

        layout.addWidget(type_group)

        # Osobní údaje
        self.personal_group = QGroupBox("Osobní údaje")
        personal_layout = QFormLayout(self.personal_group)

        self.cb_salutation = QComboBox()
        self.cb_salutation.addItems(["", "Pan", "Paní", "Slečna"])
        personal_layout.addRow("Oslovení:", self.cb_salutation)

        self.le_first_name = QLineEdit()
        self.le_first_name.setPlaceholderText("Povinné pole")
        personal_layout.addRow("Jméno *:", self.le_first_name)

        self.le_last_name = QLineEdit()
        self.le_last_name.setPlaceholderText("Povinné pole")
        personal_layout.addRow("Příjmení *:", self.le_last_name)

        self.de_birth_date = QDateEdit()
        self.de_birth_date.setCalendarPopup(True)
        self.de_birth_date.setDate(QDate.currentDate())
        self.de_birth_date.setDisplayFormat("dd.MM.yyyy")
        personal_layout.addRow("Datum narození:", self.de_birth_date)

        self.le_birth_number = QLineEdit()
        self.le_birth_number.setPlaceholderText("Volitelné, chráněný údaj")
        personal_layout.addRow("Rodné číslo:", self.le_birth_number)

        layout.addWidget(self.personal_group)

        # Firemní údaje
        self.company_group = QGroupBox("Firemní údaje")
        company_layout = QFormLayout(self.company_group)

        self.le_company_name = QLineEdit()
        self.le_company_name.setPlaceholderText("Povinné pole")
        company_layout.addRow("Název firmy *:", self.le_company_name)

        ico_layout = QHBoxLayout()
        self.le_ico = QLineEdit()
        self.le_ico.setPlaceholderText("8 číslic")
        self.le_ico.setMaxLength(8)
        ico_layout.addWidget(self.le_ico)

        btn_ares = QPushButton("🔍 ARES")
        btn_ares.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_ares.clicked.connect(self.load_from_ares)
        ico_layout.addWidget(btn_ares)

        company_layout.addRow("IČO *:", ico_layout)

        self.le_dic = QLineEdit()
        self.le_dic.setPlaceholderText("CZxxxxxxxx")
        company_layout.addRow("DIČ:", self.le_dic)

        self.le_contact_person = QLineEdit()
        company_layout.addRow("Kontaktní osoba:", self.le_contact_person)

        self.le_contact_position = QLineEdit()
        company_layout.addRow("Pozice:", self.le_contact_position)

        layout.addWidget(self.company_group)
        self.company_group.hide()

        layout.addStretch()
        return tab

    def create_contact_tab(self):
        """Záložka kontaktních údajů"""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setSpacing(10)

        self.le_phone = QLineEdit()
        self.le_phone.setPlaceholderText("+420 xxx xxx xxx")
        layout.addRow("Telefon *:", self.le_phone)

        self.le_phone2 = QLineEdit()
        self.le_phone2.setPlaceholderText("Záložní telefon")
        layout.addRow("Telefon 2:", self.le_phone2)

        self.le_email = QLineEdit()
        self.le_email.setPlaceholderText("email@example.com")
        layout.addRow("Email *:", self.le_email)

        self.le_email2 = QLineEdit()
        self.le_email2.setPlaceholderText("Záložní email")
        layout.addRow("Email 2:", self.le_email2)

        self.le_web = QLineEdit()
        self.le_web.setPlaceholderText("https://www.example.com")
        layout.addRow("Web:", self.le_web)

        return tab

    def create_address_tab(self):
        """Záložka adresy"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Hlavní adresa
        main_group = QGroupBox("Hlavní adresa")
        main_layout = QFormLayout(main_group)

        self.le_street = QLineEdit()
        self.le_street.setPlaceholderText("Ulice a číslo popisné")
        main_layout.addRow("Ulice *:", self.le_street)

        self.le_city = QLineEdit()
        self.le_city.setPlaceholderText("Město")
        main_layout.addRow("Město *:", self.le_city)

        self.le_zip = QLineEdit()
        self.le_zip.setPlaceholderText("12345")
        self.le_zip.setMaxLength(5)
        main_layout.addRow("PSČ *:", self.le_zip)

        self.le_region = QLineEdit()
        main_layout.addRow("Kraj:", self.le_region)

        self.cb_country = QComboBox()
        self.cb_country.addItems(["Česká republika", "Slovensko", "Polsko", "Německo", "Rakousko"])
        main_layout.addRow("Země:", self.cb_country)

        layout.addWidget(main_group)

        # Fakturační adresa
        billing_group = QGroupBox("Fakturační adresa")
        billing_layout = QVBoxLayout(billing_group)

        self.chk_same_address = QCheckBox("Stejná jako hlavní adresa")
        self.chk_same_address.setChecked(True)
        self.chk_same_address.toggled.connect(self.toggle_billing_address)
        billing_layout.addWidget(self.chk_same_address)

        self.billing_form = QWidget()
        billing_form_layout = QFormLayout(self.billing_form)

        self.le_billing_street = QLineEdit()
        billing_form_layout.addRow("Ulice:", self.le_billing_street)

        self.le_billing_city = QLineEdit()
        billing_form_layout.addRow("Město:", self.le_billing_city)

        self.le_billing_zip = QLineEdit()
        self.le_billing_zip.setMaxLength(5)
        billing_form_layout.addRow("PSČ:", self.le_billing_zip)

        self.cb_billing_country = QComboBox()
        self.cb_billing_country.addItems(["Česká republika", "Slovensko", "Polsko", "Německo", "Rakousko"])
        billing_form_layout.addRow("Země:", self.cb_billing_country)

        self.billing_form.hide()
        billing_layout.addWidget(self.billing_form)

        layout.addWidget(billing_group)
        layout.addStretch()

        return tab

    def create_billing_tab(self):
        """Záložka fakturačních údajů"""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setSpacing(10)

        self.le_billing_ico = QLineEdit()
        self.le_billing_ico.setReadOnly(True)
        self.le_billing_ico.setStyleSheet("background-color: #f0f0f0;")
        layout.addRow("IČO:", self.le_billing_ico)

        self.le_billing_dic = QLineEdit()
        self.le_billing_dic.setReadOnly(True)
        self.le_billing_dic.setStyleSheet("background-color: #f0f0f0;")
        layout.addRow("DIČ:", self.le_billing_dic)

        self.le_bank_account = QLineEdit()
        self.le_bank_account.setPlaceholderText("IBAN nebo číslo účtu/kód banky")
        layout.addRow("Číslo účtu:", self.le_bank_account)

        self.le_bank_name = QLineEdit()
        layout.addRow("Banka:", self.le_bank_name)

        self.sb_payment_days = QSpinBox()
        self.sb_payment_days.setRange(1, 90)
        self.sb_payment_days.setValue(14)
        self.sb_payment_days.setSuffix(" dní")
        layout.addRow("Splatnost faktur:", self.sb_payment_days)

        self.cb_payment_method = QComboBox()
        self.cb_payment_method.addItems(["Bankovní převod", "Hotovost", "Platební karta", "Dobírka"])
        layout.addRow("Platební metoda:", self.cb_payment_method)

        self.dsb_credit_limit = QDoubleSpinBox()
        self.dsb_credit_limit.setRange(0, 1000000)
        self.dsb_credit_limit.setValue(0)
        self.dsb_credit_limit.setSuffix(" Kč")
        self.dsb_credit_limit.setDecimals(0)
        layout.addRow("Kreditní limit:", self.dsb_credit_limit)

        return tab

    def create_group_tab(self):
        """Záložka zákaznické skupiny"""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setSpacing(10)

        self.cb_customer_group = QComboBox()
        self.cb_customer_group.addItems(["Standardní", "VIP", "Firemní", "Pojišťovna"])
        layout.addRow("Skupina *:", self.cb_customer_group)

        self.dsb_work_discount = QDoubleSpinBox()
        self.dsb_work_discount.setRange(0, 100)
        self.dsb_work_discount.setValue(0)
        self.dsb_work_discount.setSuffix(" %")
        layout.addRow("Sleva na práci:", self.dsb_work_discount)

        self.dsb_material_discount = QDoubleSpinBox()
        self.dsb_material_discount.setRange(0, 100)
        self.dsb_material_discount.setValue(0)
        self.dsb_material_discount.setSuffix(" %")
        layout.addRow("Sleva na materiál:", self.dsb_material_discount)

        self.sb_priority = QSpinBox()
        self.sb_priority.setRange(1, 5)
        self.sb_priority.setValue(3)
        layout.addRow("Priorita (1-5):", self.sb_priority)

        self.chk_vip = QCheckBox("VIP zákazník")
        layout.addRow("", self.chk_vip)

        return tab

    def create_notes_tab(self):
        """Záložka poznámek"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addWidget(QLabel("Poznámky k zákazníkovi:"))
        self.te_notes = QTextEdit()
        self.te_notes.setPlaceholderText("Interní poznámky o zákazníkovi...")
        layout.addWidget(self.te_notes)

        layout.addWidget(QLabel("Speciální požadavky:"))
        self.te_special = QTextEdit()
        self.te_special.setPlaceholderText("Speciální požadavky zákazníka...")
        self.te_special.setMaximumHeight(100)
        layout.addWidget(self.te_special)

        self.cb_communication = QComboBox()
        self.cb_communication.addItems(["Email", "Telefon", "SMS"])
        comm_layout = QHBoxLayout()
        comm_layout.addWidget(QLabel("Preferovaná komunikace:"))
        comm_layout.addWidget(self.cb_communication)
        comm_layout.addStretch()
        layout.addLayout(comm_layout)

        self.chk_marketing = QCheckBox("Souhlas s marketingem")
        layout.addWidget(self.chk_marketing)

        self.chk_gdpr = QCheckBox("GDPR souhlas (povinný)")
        self.chk_gdpr.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.chk_gdpr)

        return tab

    def toggle_customer_type(self):
        """Přepnutí typu zákazníka"""
        if self.rb_personal.isChecked():
            self.personal_group.show()
            self.company_group.hide()
        else:
            self.personal_group.hide()
            self.company_group.show()

    def toggle_billing_address(self, checked):
        """Přepnutí fakturační adresy"""
        self.billing_form.setVisible(not checked)

    def load_from_ares(self):
        """Načtení údajů z ARES"""
        ico = self.le_ico.text().strip()
        if not self.validate_ico(ico):
            QMessageBox.warning(self, "Chyba", "Zadejte platné IČO (8 číslic)")
            return

        QMessageBox.information(
            self,
            "ARES",
            f"Načítání údajů z ARES pro IČO: {ico}\n\nTato funkce bude implementována."
        )

    def validate_ico(self, ico):
        """Validace IČO"""
        if not ico:
            return False
        return len(ico) == 8 and ico.isdigit()

    def validate_dic(self, dic):
        """Validace DIČ"""
        if not dic:
            return True
        pattern = r'^CZ\d{8,10}$'
        return bool(re.match(pattern, dic))

    def validate_email(self, email):
        """Validace emailu"""
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def validate_phone(self, phone):
        """Validace telefonu"""
        if not phone:
            return False
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)
        return len(cleaned) >= 9 and cleaned.replace('+', '').isdigit()

    def validate_zip(self, zip_code):
        """Validace PSČ"""
        if not zip_code:
            return False
        return len(zip_code) == 5 and zip_code.isdigit()

    def validate_form(self):
        """Validace celého formuláře"""
        errors = []

        # Kontrola typu zákazníka
        if self.rb_personal.isChecked():
            if not self.le_first_name.text().strip():
                errors.append("Jméno je povinné")
            if not self.le_last_name.text().strip():
                errors.append("Příjmení je povinné")
        else:
            if not self.le_company_name.text().strip():
                errors.append("Název firmy je povinný")
            if not self.validate_ico(self.le_ico.text().strip()):
                errors.append("IČO musí mít 8 číslic")
            if self.le_dic.text().strip() and not self.validate_dic(self.le_dic.text().strip()):
                errors.append("DIČ má neplatný formát (CZxxxxxxxx)")

        # Kontaktní údaje
        if not self.validate_phone(self.le_phone.text().strip()):
            errors.append("Telefon má neplatný formát")

        if not self.validate_email(self.le_email.text().strip()):
            errors.append("Email má neplatný formát")

        # Adresa
        if not self.le_street.text().strip():
            errors.append("Ulice je povinná")
        if not self.le_city.text().strip():
            errors.append("Město je povinné")
        if not self.validate_zip(self.le_zip.text().strip()):
            errors.append("PSČ musí mít 5 číslic")

        # GDPR
        if not self.chk_gdpr.isChecked():
            errors.append("GDPR souhlas je povinný")

        if errors:
            QMessageBox.warning(
                self,
                "Chyby ve formuláři",
                "Opravte následující chyby:\n\n• " + "\n• ".join(errors)
            )
            return False

        return True

    def save_customer(self):
        """Uložení zákazníka"""
        if not self.validate_form():
            return

        try:
            customer_type = "personal" if self.rb_personal.isChecked() else "company"

            data = {
                "customer_type": customer_type,
                "first_name": self.le_first_name.text().strip() if customer_type == "personal" else "",
                "last_name": self.le_last_name.text().strip() if customer_type == "personal" else "",
                "company_name": self.le_company_name.text().strip() if customer_type == "company" else "",
                "ico": self.le_ico.text().strip() if customer_type == "company" else "",
                "dic": self.le_dic.text().strip() if customer_type == "company" else "",
                "phone": self.le_phone.text().strip(),
                "phone2": self.le_phone2.text().strip(),
                "email": self.le_email.text().strip(),
                "email2": self.le_email2.text().strip(),
                "web": self.le_web.text().strip(),
                "street": self.le_street.text().strip(),
                "city": self.le_city.text().strip(),
                "zip": self.le_zip.text().strip(),
                "region": self.le_region.text().strip(),
                "country": self.cb_country.currentText(),
                "customer_group": self.cb_customer_group.currentText(),
                "work_discount": self.dsb_work_discount.value(),
                "material_discount": self.dsb_material_discount.value(),
                "priority": self.sb_priority.value(),
                "is_vip": 1 if self.chk_vip.isChecked() else 0,
                "notes": self.te_notes.toPlainText(),
                "special_requirements": self.te_special.toPlainText(),
                "preferred_communication": self.cb_communication.currentText(),
                "marketing_consent": 1 if self.chk_marketing.isChecked() else 0,
                "gdpr_consent": 1 if self.chk_gdpr.isChecked() else 0,
                "payment_days": self.sb_payment_days.value(),
                "payment_method": self.cb_payment_method.currentText(),
                "credit_limit": self.dsb_credit_limit.value(),
                "bank_account": self.le_bank_account.text().strip(),
                "bank_name": self.le_bank_name.text().strip(),
                "is_active": 1,
                "has_debt": 0
            }

            if self.is_edit_mode:
                # UPDATE
                set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
                values = list(data.values()) + [self.customer_id]
                db.execute(f"UPDATE customers SET {set_clause} WHERE id = ?", values)
                QMessageBox.information(self, "Uloženo", "Zákazník byl úspěšně upraven")
            else:
                # INSERT
                columns = ", ".join(data.keys())
                placeholders = ", ".join(["?" for _ in data])
                db.execute(f"INSERT INTO customers ({columns}) VALUES ({placeholders})", list(data.values()))
                QMessageBox.information(self, "Uloženo", "Zákazník byl úspěšně vytvořen")

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit zákazníka:\n{e}")

    def save_and_open(self):
        """Uložení a otevření detailu"""
        self.save_customer()

    def load_customer_data(self):
        """Načtení dat zákazníka pro editaci"""
        try:
            customer = db.fetch_one(f"SELECT * FROM customers WHERE id = ?", (self.customer_id,))
            if customer:
                # Implementace načtení dat do formuláře
                pass
        except Exception as e:
            print(f"Chyba při načítání zákazníka: {e}")

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #f5f5f5;
            }}
            QTabWidget::pane {{
                border: 1px solid #ddd;
                background-color: white;
                border-radius: 5px;
            }}
            QTabBar::tab {{
                background-color: #e0e0e0;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }}
            QTabBar::tab:selected {{
                background-color: white;
                font-weight: bold;
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 13px;
            }}
            QTextEdit {{
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            #btnSave {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                border: none;
                padding: 10px 25px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }}
            #btnSave:hover {{
                background-color: #219a52;
            }}
            #btnSaveOpen {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                padding: 10px 25px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }}
            #btnSaveOpen:hover {{
                background-color: #2980b9;
            }}
            QPushButton {{
                padding: 8px 16px;
                border-radius: 4px;
            }}
        """)
