# -*- coding: utf-8 -*-
"""
Nastavení firemních údajů
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QComboBox, QDateEdit, QTimeEdit, QLabel,
    QPushButton, QFileDialog, QScrollArea, QFrame, QMessageBox,
    QGridLayout, QCheckBox, QSpinBox
)
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QPixmap, QFont, QColor
from pathlib import Path
import json
import re
from database_manager import db
import config


class CompanySettingsWidget(QWidget):
    """Widget pro nastavení firemních údajů"""

    def __init__(self):
        super().__init__()
        self.logo_path = None
        self.stamp_path = None
        self.signature_path = None
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Inicializace UI"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Základní údaje
        main_layout.addWidget(self.create_basic_info_section())

        # Kontaktní údaje
        main_layout.addWidget(self.create_contact_section())

        # Bankovní spojení
        main_layout.addWidget(self.create_bank_section())

        # Logo a branding
        main_layout.addWidget(self.create_branding_section())

        # Provozní údaje
        main_layout.addWidget(self.create_operation_section())

        main_layout.addStretch()

        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        self.set_styles()

    def create_basic_info_section(self):
        """Sekce základních údajů"""
        group = QGroupBox("🏢 Základní údaje")
        group.setObjectName("settingsGroup")
        layout = QFormLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Název firmy
        self.company_name = QLineEdit()
        self.company_name.setPlaceholderText("Název vaší firmy *")
        layout.addRow("Název firmy *:", self.company_name)

        # IČO
        self.ico = QLineEdit()
        self.ico.setPlaceholderText("12345678")
        self.ico.setMaxLength(8)
        self.ico.textChanged.connect(self.validate_ico)
        layout.addRow("IČO *:", self.ico)

        # DIČ
        self.dic = QLineEdit()
        self.dic.setPlaceholderText("CZ12345678")
        self.dic.setMaxLength(12)
        self.dic.textChanged.connect(self.validate_dic)
        layout.addRow("DIČ:", self.dic)

        # Právní forma
        self.legal_form = QComboBox()
        self.legal_form.addItems([
            "OSVČ",
            "s.r.o.",
            "a.s.",
            "k.s.",
            "v.o.s.",
            "družstvo",
            "spolek",
            "jiná"
        ])
        layout.addRow("Právní forma:", self.legal_form)

        # Datum založení
        self.founded_date = QDateEdit()
        self.founded_date.setCalendarPopup(True)
        self.founded_date.setDate(QDate.currentDate())
        self.founded_date.setDisplayFormat("dd.MM.yyyy")
        layout.addRow("Datum založení:", self.founded_date)

        # Registrace
        self.registration = QLineEdit()
        self.registration.setPlaceholderText("Např. OR u MS Praha, spisová značka C 12345")
        layout.addRow("Registrace:", self.registration)

        return group

    def create_contact_section(self):
        """Sekce kontaktních údajů"""
        group = QGroupBox("📍 Kontaktní údaje")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 20, 15, 15)

        # Adresa sídla
        address_label = QLabel("Adresa sídla:")
        address_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(address_label)

        address_form = QFormLayout()
        address_form.setSpacing(8)

        self.street = QLineEdit()
        self.street.setPlaceholderText("Ulice a číslo popisné *")
        address_form.addRow("Ulice *:", self.street)

        self.city = QLineEdit()
        self.city.setPlaceholderText("Město *")
        address_form.addRow("Město *:", self.city)

        self.zip_code = QLineEdit()
        self.zip_code.setPlaceholderText("12345")
        self.zip_code.setMaxLength(5)
        address_form.addRow("PSČ *:", self.zip_code)

        self.region = QComboBox()
        self.region.addItems([
            "Hlavní město Praha",
            "Středočeský kraj",
            "Jihočeský kraj",
            "Plzeňský kraj",
            "Karlovarský kraj",
            "Ústecký kraj",
            "Liberecký kraj",
            "Královéhradecký kraj",
            "Pardubický kraj",
            "Kraj Vysočina",
            "Jihomoravský kraj",
            "Olomoucký kraj",
            "Zlínský kraj",
            "Moravskoslezský kraj"
        ])
        address_form.addRow("Kraj:", self.region)

        self.country = QLineEdit()
        self.country.setText("Česká republika")
        address_form.addRow("Země:", self.country)

        layout.addLayout(address_form)

        # Provozovna
        self.different_workplace = QCheckBox("Provozovna na jiné adrese")
        self.different_workplace.toggled.connect(self.toggle_workplace_fields)
        layout.addWidget(self.different_workplace)

        self.workplace_frame = QFrame()
        workplace_layout = QFormLayout(self.workplace_frame)
        workplace_layout.setSpacing(8)

        self.workplace_street = QLineEdit()
        self.workplace_street.setPlaceholderText("Ulice a číslo")
        workplace_layout.addRow("Ulice:", self.workplace_street)

        self.workplace_city = QLineEdit()
        self.workplace_city.setPlaceholderText("Město")
        workplace_layout.addRow("Město:", self.workplace_city)

        self.workplace_zip = QLineEdit()
        self.workplace_zip.setPlaceholderText("PSČ")
        self.workplace_zip.setMaxLength(5)
        workplace_layout.addRow("PSČ:", self.workplace_zip)

        self.workplace_frame.setVisible(False)
        layout.addWidget(self.workplace_frame)

        # Kontakty
        contact_label = QLabel("Kontakty:")
        contact_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(contact_label)

        contact_form = QFormLayout()
        contact_form.setSpacing(8)

        self.phone = QLineEdit()
        self.phone.setPlaceholderText("+420 xxx xxx xxx *")
        contact_form.addRow("Telefon *:", self.phone)

        self.email = QLineEdit()
        self.email.setPlaceholderText("info@firma.cz *")
        contact_form.addRow("Email *:", self.email)

        self.web = QLineEdit()
        self.web.setPlaceholderText("www.firma.cz")
        contact_form.addRow("Web:", self.web)

        self.fax = QLineEdit()
        self.fax.setPlaceholderText("+420 xxx xxx xxx")
        contact_form.addRow("Fax:", self.fax)

        layout.addLayout(contact_form)

        return group

    def create_bank_section(self):
        """Sekce bankovního spojení"""
        group = QGroupBox("🏦 Bankovní spojení")
        group.setObjectName("settingsGroup")
        layout = QFormLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        self.bank_account = QLineEdit()
        self.bank_account.setPlaceholderText("123456789/0100 *")
        layout.addRow("Číslo účtu *:", self.bank_account)

        self.bank_code = QLineEdit()
        self.bank_code.setPlaceholderText("0100")
        self.bank_code.setMaxLength(4)
        layout.addRow("Kód banky:", self.bank_code)

        self.iban = QLineEdit()
        self.iban.setPlaceholderText("CZ6508000000192000145399")
        self.iban.setMaxLength(24)
        self.iban.textChanged.connect(self.validate_iban)
        layout.addRow("IBAN:", self.iban)

        self.bic = QLineEdit()
        self.bic.setPlaceholderText("KOMBCZPP")
        self.bic.setMaxLength(11)
        layout.addRow("BIC/SWIFT:", self.bic)

        self.bank_name = QLineEdit()
        self.bank_name.setPlaceholderText("Např. Komerční banka")
        layout.addRow("Název banky:", self.bank_name)

        return group

    def create_branding_section(self):
        """Sekce loga a brandingu"""
        group = QGroupBox("🎨 Logo a branding")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 20, 15, 15)

        # Logo
        logo_layout = QHBoxLayout()

        logo_left = QVBoxLayout()
        logo_label = QLabel("Logo firmy:")
        logo_label.setStyleSheet("font-weight: bold;")
        logo_left.addWidget(logo_label)

        self.logo_preview = QLabel()
        self.logo_preview.setFixedSize(200, 100)
        self.logo_preview.setStyleSheet("""
            border: 2px dashed #bdc3c7;
            border-radius: 4px;
            background-color: white;
        """)
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setText("Bez loga")
        logo_left.addWidget(self.logo_preview)

        logo_info = QLabel("Doporučeno: 400x200 px\nFormáty: PNG, JPG, SVG")
        logo_info.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        logo_left.addWidget(logo_info)

        logo_layout.addLayout(logo_left)

        logo_buttons = QVBoxLayout()
        logo_buttons.setSpacing(5)

        upload_logo_btn = QPushButton("📤 Nahrát logo")
        upload_logo_btn.clicked.connect(self.upload_logo)
        logo_buttons.addWidget(upload_logo_btn)

        remove_logo_btn = QPushButton("🗑️ Odstranit")
        remove_logo_btn.clicked.connect(self.remove_logo)
        logo_buttons.addWidget(remove_logo_btn)

        logo_buttons.addStretch()
        logo_layout.addLayout(logo_buttons)
        logo_layout.addStretch()

        layout.addLayout(logo_layout)

        # Barvy
        colors_label = QLabel("Firemní barvy:")
        colors_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(colors_label)

        colors_layout = QHBoxLayout()

        primary_layout = QVBoxLayout()
        primary_layout.addWidget(QLabel("Primární:"))
        self.primary_color = QLineEdit()
        self.primary_color.setPlaceholderText("#3498db")
        self.primary_color.setMaxLength(7)
        primary_layout.addWidget(self.primary_color)
        colors_layout.addLayout(primary_layout)

        secondary_layout = QVBoxLayout()
        secondary_layout.addWidget(QLabel("Sekundární:"))
        self.secondary_color = QLineEdit()
        self.secondary_color.setPlaceholderText("#2ecc71")
        self.secondary_color.setMaxLength(7)
        secondary_layout.addWidget(self.secondary_color)
        colors_layout.addLayout(secondary_layout)

        colors_layout.addStretch()
        layout.addLayout(colors_layout)

        # Razítko a podpis
        stamp_sig_layout = QHBoxLayout()

        # Razítko
        stamp_layout = QVBoxLayout()
        stamp_label = QLabel("Razítko:")
        stamp_label.setStyleSheet("font-weight: bold;")
        stamp_layout.addWidget(stamp_label)

        self.stamp_preview = QLabel()
        self.stamp_preview.setFixedSize(120, 120)
        self.stamp_preview.setStyleSheet("""
            border: 2px dashed #bdc3c7;
            border-radius: 4px;
            background-color: white;
        """)
        self.stamp_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stamp_preview.setText("Bez razítka")
        stamp_layout.addWidget(self.stamp_preview)

        upload_stamp_btn = QPushButton("📤 Nahrát")
        upload_stamp_btn.clicked.connect(self.upload_stamp)
        stamp_layout.addWidget(upload_stamp_btn)

        stamp_sig_layout.addLayout(stamp_layout)

        # Podpis
        sig_layout = QVBoxLayout()
        sig_label = QLabel("Podpis:")
        sig_label.setStyleSheet("font-weight: bold;")
        sig_layout.addWidget(sig_label)

        self.signature_preview = QLabel()
        self.signature_preview.setFixedSize(120, 60)
        self.signature_preview.setStyleSheet("""
            border: 2px dashed #bdc3c7;
            border-radius: 4px;
            background-color: white;
        """)
        self.signature_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.signature_preview.setText("Bez podpisu")
        sig_layout.addWidget(self.signature_preview)

        upload_sig_btn = QPushButton("📤 Nahrát")
        upload_sig_btn.clicked.connect(self.upload_signature)
        sig_layout.addWidget(upload_sig_btn)

        stamp_sig_layout.addLayout(sig_layout)
        stamp_sig_layout.addStretch()

        layout.addLayout(stamp_sig_layout)

        return group

    def create_operation_section(self):
        """Sekce provozních údajů"""
        group = QGroupBox("⏰ Provozní údaje")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 20, 15, 15)

        # Otevírací doba
        hours_label = QLabel("Otevírací doba:")
        hours_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(hours_label)

        days = ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"]
        self.opening_hours = {}

        hours_grid = QGridLayout()
        hours_grid.setSpacing(10)

        for i, day in enumerate(days):
            hours_grid.addWidget(QLabel(day + ":"), i, 0)

            self.opening_hours[day] = {
                "closed": QCheckBox("Zavřeno"),
                "from": QTimeEdit(),
                "to": QTimeEdit()
            }

            self.opening_hours[day]["from"].setDisplayFormat("HH:mm")
            self.opening_hours[day]["to"].setDisplayFormat("HH:mm")

            if day in ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek"]:
                self.opening_hours[day]["from"].setTime(QTime(7, 0))
                self.opening_hours[day]["to"].setTime(QTime(16, 0))
            elif day == "Sobota":
                self.opening_hours[day]["from"].setTime(QTime(8, 0))
                self.opening_hours[day]["to"].setTime(QTime(12, 0))
            else:
                self.opening_hours[day]["closed"].setChecked(True)

            self.opening_hours[day]["closed"].toggled.connect(
                lambda checked, d=day: self.toggle_day_hours(d, checked)
            )

            hours_grid.addWidget(self.opening_hours[day]["from"], i, 1)
            hours_grid.addWidget(QLabel("-"), i, 2)
            hours_grid.addWidget(self.opening_hours[day]["to"], i, 3)
            hours_grid.addWidget(self.opening_hours[day]["closed"], i, 4)

            if day == "Neděle":
                self.toggle_day_hours(day, True)

        layout.addLayout(hours_grid)

        # Svátky
        holidays_layout = QHBoxLayout()
        self.use_cz_holidays = QCheckBox("Použít české státní svátky")
        self.use_cz_holidays.setChecked(True)
        holidays_layout.addWidget(self.use_cz_holidays)
        holidays_layout.addStretch()
        layout.addLayout(holidays_layout)

        # Kapacita
        capacity_label = QLabel("Kapacita servisu:")
        capacity_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(capacity_label)

        capacity_form = QFormLayout()
        capacity_form.setSpacing(8)

        self.service_stations = QSpinBox()
        self.service_stations.setRange(1, 50)
        self.service_stations.setValue(3)
        capacity_form.addRow("Počet stanovišť:", self.service_stations)

        self.max_orders_per_day = QSpinBox()
        self.max_orders_per_day.setRange(1, 100)
        self.max_orders_per_day.setValue(10)
        capacity_form.addRow("Max. zakázek/den:", self.max_orders_per_day)

        layout.addLayout(capacity_form)

        return group

    def toggle_workplace_fields(self, checked):
        """Přepnutí viditelnosti polí provozovny"""
        self.workplace_frame.setVisible(checked)

    def toggle_day_hours(self, day, closed):
        """Přepnutí dostupnosti hodin pro den"""
        self.opening_hours[day]["from"].setEnabled(not closed)
        self.opening_hours[day]["to"].setEnabled(not closed)

    def validate_ico(self):
        """Validace IČO"""
        ico = self.ico.text()
        if ico and not ico.isdigit():
            self.ico.setStyleSheet("border: 2px solid red;")
        elif ico and len(ico) != 8:
            self.ico.setStyleSheet("border: 2px solid orange;")
        else:
            self.ico.setStyleSheet("")

    def validate_dic(self):
        """Validace DIČ"""
        dic = self.dic.text()
        if dic and not re.match(r'^CZ\d{8,10}$', dic):
            self.dic.setStyleSheet("border: 2px solid orange;")
        else:
            self.dic.setStyleSheet("")

    def validate_iban(self):
        """Validace IBAN"""
        iban = self.iban.text().replace(" ", "")
        if iban and (len(iban) != 24 or not iban[:2].isalpha()):
            self.iban.setStyleSheet("border: 2px solid orange;")
        else:
            self.iban.setStyleSheet("")

    def upload_logo(self):
        """Nahrání loga"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Vyberte logo",
            "",
            "Obrázky (*.png *.jpg *.jpeg *.svg)"
        )
        if file_path:
            self.logo_path = file_path
            pixmap = QPixmap(file_path)
            scaled = pixmap.scaled(
                200, 100,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.logo_preview.setPixmap(scaled)

    def remove_logo(self):
        """Odstranění loga"""
        self.logo_path = None
        self.logo_preview.clear()
        self.logo_preview.setText("Bez loga")

    def upload_stamp(self):
        """Nahrání razítka"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Vyberte razítko",
            "",
            "Obrázky (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.stamp_path = file_path
            pixmap = QPixmap(file_path)
            scaled = pixmap.scaled(
                120, 120,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.stamp_preview.setPixmap(scaled)

    def upload_signature(self):
        """Nahrání podpisu"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Vyberte podpis",
            "",
            "Obrázky (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.signature_path = file_path
            pixmap = QPixmap(file_path)
            scaled = pixmap.scaled(
                120, 60,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.signature_preview.setPixmap(scaled)

    def validate_required_fields(self):
        """Validace povinných polí"""
        errors = []

        if not self.company_name.text().strip():
            errors.append("Název firmy je povinný")
        if not self.ico.text().strip() or len(self.ico.text()) != 8:
            errors.append("IČO musí mít 8 číslic")
        if not self.street.text().strip():
            errors.append("Ulice je povinná")
        if not self.city.text().strip():
            errors.append("Město je povinné")
        if not self.zip_code.text().strip():
            errors.append("PSČ je povinné")
        if not self.phone.text().strip():
            errors.append("Telefon je povinný")
        if not self.email.text().strip():
            errors.append("Email je povinný")
        if not self.bank_account.text().strip():
            errors.append("Číslo účtu je povinné")

        return errors

    def save_settings(self):
        """Uložení nastavení"""
        errors = self.validate_required_fields()
        if errors:
            raise Exception("\n".join(errors))

        settings = self.get_settings()

        # Uložení do databáze
        conn = db.get_connection()
        cursor = conn.cursor()

        for key, value in settings.items():
            if isinstance(value, dict):
                value = json.dumps(value, ensure_ascii=False)
            cursor.execute("""
                INSERT OR REPLACE INTO app_settings (key, value)
                VALUES (?, ?)
            """, (f"company_{key}", str(value)))

        conn.commit()

    def load_settings(self):
        """Načtení nastavení z databáze"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM app_settings WHERE key LIKE 'company_%'")
            rows = cursor.fetchall()

            settings = {}
            for key, value in rows:
                settings[key.replace("company_", "")] = value

            self.set_settings(settings)
        except Exception:
            pass

    def get_settings(self):
        """Získání aktuálních nastavení"""
        opening_hours_data = {}
        for day, widgets in self.opening_hours.items():
            opening_hours_data[day] = {
                "closed": widgets["closed"].isChecked(),
                "from": widgets["from"].time().toString("HH:mm"),
                "to": widgets["to"].time().toString("HH:mm")
            }

        return {
            "name": self.company_name.text(),
            "ico": self.ico.text(),
            "dic": self.dic.text(),
            "legal_form": self.legal_form.currentText(),
            "founded_date": self.founded_date.date().toString("yyyy-MM-dd"),
            "registration": self.registration.text(),
            "street": self.street.text(),
            "city": self.city.text(),
            "zip_code": self.zip_code.text(),
            "region": self.region.currentText(),
            "country": self.country.text(),
            "different_workplace": self.different_workplace.isChecked(),
            "workplace_street": self.workplace_street.text(),
            "workplace_city": self.workplace_city.text(),
            "workplace_zip": self.workplace_zip.text(),
            "phone": self.phone.text(),
            "email": self.email.text(),
            "web": self.web.text(),
            "fax": self.fax.text(),
            "bank_account": self.bank_account.text(),
            "bank_code": self.bank_code.text(),
            "iban": self.iban.text(),
            "bic": self.bic.text(),
            "bank_name": self.bank_name.text(),
            "logo_path": self.logo_path or "",
            "stamp_path": self.stamp_path or "",
            "signature_path": self.signature_path or "",
            "primary_color": self.primary_color.text(),
            "secondary_color": self.secondary_color.text(),
            "opening_hours": opening_hours_data,
            "use_cz_holidays": self.use_cz_holidays.isChecked(),
            "service_stations": self.service_stations.value(),
            "max_orders_per_day": self.max_orders_per_day.value()
        }

    def set_settings(self, settings):
        """Nastavení hodnot z načtených dat"""
        if "name" in settings:
            self.company_name.setText(settings["name"])
        if "ico" in settings:
            self.ico.setText(settings["ico"])
        if "dic" in settings:
            self.dic.setText(settings["dic"])
        if "legal_form" in settings:
            index = self.legal_form.findText(settings["legal_form"])
            if index >= 0:
                self.legal_form.setCurrentIndex(index)
        if "founded_date" in settings:
            self.founded_date.setDate(QDate.fromString(settings["founded_date"], "yyyy-MM-dd"))
        if "registration" in settings:
            self.registration.setText(settings["registration"])
        if "street" in settings:
            self.street.setText(settings["street"])
        if "city" in settings:
            self.city.setText(settings["city"])
        if "zip_code" in settings:
            self.zip_code.setText(settings["zip_code"])
        if "region" in settings:
            index = self.region.findText(settings["region"])
            if index >= 0:
                self.region.setCurrentIndex(index)
        if "country" in settings:
            self.country.setText(settings["country"])
        if "different_workplace" in settings:
            self.different_workplace.setChecked(settings["different_workplace"] == "True")
        if "workplace_street" in settings:
            self.workplace_street.setText(settings["workplace_street"])
        if "workplace_city" in settings:
            self.workplace_city.setText(settings["workplace_city"])
        if "workplace_zip" in settings:
            self.workplace_zip.setText(settings["workplace_zip"])
        if "phone" in settings:
            self.phone.setText(settings["phone"])
        if "email" in settings:
            self.email.setText(settings["email"])
        if "web" in settings:
            self.web.setText(settings["web"])
        if "fax" in settings:
            self.fax.setText(settings["fax"])
        if "bank_account" in settings:
            self.bank_account.setText(settings["bank_account"])
        if "bank_code" in settings:
            self.bank_code.setText(settings["bank_code"])
        if "iban" in settings:
            self.iban.setText(settings["iban"])
        if "bic" in settings:
            self.bic.setText(settings["bic"])
        if "bank_name" in settings:
            self.bank_name.setText(settings["bank_name"])
        if "primary_color" in settings:
            self.primary_color.setText(settings["primary_color"])
        if "secondary_color" in settings:
            self.secondary_color.setText(settings["secondary_color"])
        if "use_cz_holidays" in settings:
            self.use_cz_holidays.setChecked(settings["use_cz_holidays"] == "True")
        if "service_stations" in settings:
            self.service_stations.setValue(int(settings["service_stations"]))
        if "max_orders_per_day" in settings:
            self.max_orders_per_day.setValue(int(settings["max_orders_per_day"]))

        # Logo, razítko, podpis
        if "logo_path" in settings and settings["logo_path"]:
            self.logo_path = settings["logo_path"]
            if Path(self.logo_path).exists():
                pixmap = QPixmap(self.logo_path)
                scaled = pixmap.scaled(200, 100, Qt.AspectRatioMode.KeepAspectRatio)
                self.logo_preview.setPixmap(scaled)

        if "stamp_path" in settings and settings["stamp_path"]:
            self.stamp_path = settings["stamp_path"]
            if Path(self.stamp_path).exists():
                pixmap = QPixmap(self.stamp_path)
                scaled = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio)
                self.stamp_preview.setPixmap(scaled)

        if "signature_path" in settings and settings["signature_path"]:
            self.signature_path = settings["signature_path"]
            if Path(self.signature_path).exists():
                pixmap = QPixmap(self.signature_path)
                scaled = pixmap.scaled(120, 60, Qt.AspectRatioMode.KeepAspectRatio)
                self.signature_preview.setPixmap(scaled)

        # Otevírací doba
        if "opening_hours" in settings:
            try:
                hours_data = json.loads(settings["opening_hours"]) if isinstance(settings["opening_hours"], str) else settings["opening_hours"]
                for day, data in hours_data.items():
                    if day in self.opening_hours:
                        self.opening_hours[day]["closed"].setChecked(data.get("closed", False))
                        self.opening_hours[day]["from"].setTime(QTime.fromString(data.get("from", "07:00"), "HH:mm"))
                        self.opening_hours[day]["to"].setTime(QTime.fromString(data.get("to", "16:00"), "HH:mm"))
            except Exception:
                pass

    def refresh(self):
        """Obnovení dat"""
        self.load_settings()

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet("""
            #settingsGroup {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }

            #settingsGroup::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }

            QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }

            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus, QSpinBox:focus {
                border: 2px solid #3498db;
            }

            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                background-color: #3498db;
                color: white;
                border: none;
            }

            QPushButton:hover {
                background-color: #2980b9;
            }

            QCheckBox {
                spacing: 8px;
            }
        """)
