# -*- coding: utf-8 -*-
"""
Nastavení emailu a notifikací
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QLabel,
    QPushButton, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextEdit, QMessageBox, QTabWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from database_manager import db
import config
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailTestThread(QThread):
    """Vlákno pro testování SMTP připojení"""
    finished = pyqtSignal(bool, str)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings

    def run(self):
        try:
            if self.settings["encryption"] == "SSL":
                server = smtplib.SMTP_SSL(
                    self.settings["server"],
                    self.settings["port"],
                    timeout=10
                )
            else:
                server = smtplib.SMTP(
                    self.settings["server"],
                    self.settings["port"],
                    timeout=10
                )
                if self.settings["encryption"] == "TLS":
                    server.starttls()

            server.login(self.settings["username"], self.settings["password"])
            server.quit()

            self.finished.emit(True, "Připojení úspěšné!")

        except Exception as e:
            self.finished.emit(False, str(e))


class EmailSettingsWidget(QWidget):
    """Widget pro nastavení emailu"""

    def __init__(self):
        super().__init__()
        self.test_thread = None
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

        # SMTP nastavení
        main_layout.addWidget(self.create_smtp_section())

        # Automatické emaily
        main_layout.addWidget(self.create_auto_emails_section())

        # Podpis emailu
        main_layout.addWidget(self.create_signature_section())

        # SMS brána
        main_layout.addWidget(self.create_sms_section())

        # Push notifikace
        main_layout.addWidget(self.create_notifications_section())

        # Log emailů
        main_layout.addWidget(self.create_email_log_section())

        main_layout.addStretch()

        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        self.set_styles()

    def create_smtp_section(self):
        """Sekce SMTP nastavení"""
        group = QGroupBox("📧 SMTP nastavení")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Přednastavené profily
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Přednastavený profil:"))

        self.smtp_preset = QComboBox()
        self.smtp_preset.addItems([
            "Vlastní",
            "Gmail",
            "Outlook / Office 365",
            "Seznam.cz",
            "Centrum.cz"
        ])
        self.smtp_preset.currentTextChanged.connect(self.apply_smtp_preset)
        preset_layout.addWidget(self.smtp_preset)
        preset_layout.addStretch()

        layout.addLayout(preset_layout)

        # Formulář SMTP
        form = QFormLayout()
        form.setSpacing(10)

        self.smtp_server = QLineEdit()
        self.smtp_server.setPlaceholderText("smtp.example.com")
        form.addRow("SMTP server *:", self.smtp_server)

        port_layout = QHBoxLayout()
        self.smtp_port = QSpinBox()
        self.smtp_port.setRange(1, 65535)
        self.smtp_port.setValue(587)
        port_layout.addWidget(self.smtp_port)

        self.smtp_encryption = QComboBox()
        self.smtp_encryption.addItems(["TLS", "SSL", "Žádné"])
        port_layout.addWidget(QLabel("Šifrování:"))
        port_layout.addWidget(self.smtp_encryption)
        port_layout.addStretch()

        form.addRow("Port *:", port_layout)

        self.smtp_username = QLineEdit()
        self.smtp_username.setPlaceholderText("vas@email.cz")
        form.addRow("Uživatelské jméno *:", self.smtp_username)

        self.smtp_password = QLineEdit()
        self.smtp_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.smtp_password.setPlaceholderText("••••••••")
        form.addRow("Heslo *:", self.smtp_password)

        self.smtp_from = QLineEdit()
        self.smtp_from.setPlaceholderText("servis@vasefirma.cz")
        form.addRow("Odesílatel (From) *:", self.smtp_from)

        self.smtp_reply_to = QLineEdit()
        self.smtp_reply_to.setPlaceholderText("info@vasefirma.cz (volitelné)")
        form.addRow("Reply-To:", self.smtp_reply_to)

        self.smtp_from_name = QLineEdit()
        self.smtp_from_name.setPlaceholderText("Motoservis ABC")
        form.addRow("Jméno odesílatele:", self.smtp_from_name)

        layout.addLayout(form)

        # Test připojení
        test_layout = QHBoxLayout()

        self.test_smtp_btn = QPushButton("🧪 Test připojení")
        self.test_smtp_btn.clicked.connect(self.test_smtp_connection)
        self.test_smtp_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.test_smtp_btn.setObjectName("primaryButton")

        self.smtp_status = QLabel("")
        self.smtp_status.setStyleSheet("font-weight: bold;")

        test_layout.addWidget(self.test_smtp_btn)
        test_layout.addWidget(self.smtp_status)
        test_layout.addStretch()

        layout.addLayout(test_layout)

        return group

    def apply_smtp_preset(self, preset):
        """Aplikování přednastavených SMTP profilů"""
        presets = {
            "Gmail": {
                "server": "smtp.gmail.com",
                "port": 587,
                "encryption": "TLS"
            },
            "Outlook / Office 365": {
                "server": "smtp.office365.com",
                "port": 587,
                "encryption": "TLS"
            },
            "Seznam.cz": {
                "server": "smtp.seznam.cz",
                "port": 465,
                "encryption": "SSL"
            },
            "Centrum.cz": {
                "server": "smtp.centrum.cz",
                "port": 587,
                "encryption": "TLS"
            }
        }

        if preset in presets:
            data = presets[preset]
            self.smtp_server.setText(data["server"])
            self.smtp_port.setValue(data["port"])
            index = self.smtp_encryption.findText(data["encryption"])
            if index >= 0:
                self.smtp_encryption.setCurrentIndex(index)

    def test_smtp_connection(self):
        """Test SMTP připojení"""
        if not self.smtp_server.text() or not self.smtp_username.text() or not self.smtp_password.text():
            QMessageBox.warning(self, "Chyba", "Vyplňte všechny povinné údaje SMTP.")
            return

        self.test_smtp_btn.setEnabled(False)
        self.smtp_status.setText("⏳ Testování...")
        self.smtp_status.setStyleSheet("color: #f39c12; font-weight: bold;")

        settings = {
            "server": self.smtp_server.text(),
            "port": self.smtp_port.value(),
            "encryption": self.smtp_encryption.currentText(),
            "username": self.smtp_username.text(),
            "password": self.smtp_password.text()
        }

        self.test_thread = EmailTestThread(settings)
        self.test_thread.finished.connect(self.on_smtp_test_finished)
        self.test_thread.start()

    def on_smtp_test_finished(self, success, message):
        """Callback po testu SMTP"""
        self.test_smtp_btn.setEnabled(True)

        if success:
            self.smtp_status.setText("✅ " + message)
            self.smtp_status.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.smtp_status.setText("❌ Chyba: " + message)
            self.smtp_status.setStyleSheet("color: #e74c3c; font-weight: bold;")

    def create_auto_emails_section(self):
        """Sekce automatických emailů"""
        group = QGroupBox("🤖 Automatické emaily")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 20, 15, 15)

        self.auto_email_order_confirm = QCheckBox("Potvrzení zakázky")
        self.auto_email_order_confirm.setChecked(True)
        layout.addWidget(self.auto_email_order_confirm)

        self.auto_email_status_change = QCheckBox("Změna stavu zakázky")
        layout.addWidget(self.auto_email_status_change)

        self.auto_email_order_complete = QCheckBox("Dokončení zakázky")
        self.auto_email_order_complete.setChecked(True)
        layout.addWidget(self.auto_email_order_complete)

        self.auto_email_invoice = QCheckBox("Odeslání faktury")
        self.auto_email_invoice.setChecked(True)
        layout.addWidget(self.auto_email_invoice)

        self.auto_email_stk_reminder = QCheckBox("Upomínka před STK (30 dní předem)")
        layout.addWidget(self.auto_email_stk_reminder)

        self.auto_email_payment_reminder = QCheckBox("Upomínka platby")
        self.auto_email_payment_reminder.setChecked(True)
        layout.addWidget(self.auto_email_payment_reminder)

        self.auto_email_service_reminder = QCheckBox("Připomínka pravidelného servisu")
        layout.addWidget(self.auto_email_service_reminder)

        info_label = QLabel("💡 Šablony emailů upravíte v sekci 'Šablony dokumentů'")
        info_label.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-top: 5px;")
        layout.addWidget(info_label)

        return group

    def create_signature_section(self):
        """Sekce podpisu emailu"""
        group = QGroupBox("✍️ Podpis emailu")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Povolit podpis
        self.enable_signature = QCheckBox("Použít podpis v emailech")
        self.enable_signature.setChecked(True)
        self.enable_signature.toggled.connect(self.toggle_signature)
        layout.addWidget(self.enable_signature)

        # Editor podpisu
        self.signature_editor = QTextEdit()
        self.signature_editor.setPlaceholderText(
            "S pozdravem,\n\n"
            "{{firma_nazev}}\n"
            "Tel: {{firma_telefon}}\n"
            "Email: {{firma_email}}\n"
            "Web: www.vasefirma.cz"
        )
        self.signature_editor.setMaximumHeight(150)
        layout.addWidget(self.signature_editor)

        # Volby
        options_layout = QHBoxLayout()

        self.signature_logo = QCheckBox("Vložit logo firmy")
        options_layout.addWidget(self.signature_logo)

        self.signature_social = QCheckBox("Sociální sítě")
        options_layout.addWidget(self.signature_social)

        options_layout.addStretch()
        layout.addLayout(options_layout)

        # Sociální sítě
        social_form = QFormLayout()
        social_form.setSpacing(8)

        self.social_facebook = QLineEdit()
        self.social_facebook.setPlaceholderText("facebook.com/vasefirma")
        social_form.addRow("Facebook:", self.social_facebook)

        self.social_instagram = QLineEdit()
        self.social_instagram.setPlaceholderText("instagram.com/vasefirma")
        social_form.addRow("Instagram:", self.social_instagram)

        layout.addLayout(social_form)

        return group

    def toggle_signature(self, checked):
        """Přepnutí podpisu"""
        self.signature_editor.setEnabled(checked)
        self.signature_logo.setEnabled(checked)
        self.signature_social.setEnabled(checked)

    def create_sms_section(self):
        """Sekce SMS brány"""
        group = QGroupBox("📱 SMS brána (volitelně)")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Povolit SMS
        self.enable_sms = QCheckBox("Povolit odesílání SMS")
        self.enable_sms.toggled.connect(self.toggle_sms)
        layout.addWidget(self.enable_sms)

        # Nastavení SMS
        sms_form = QFormLayout()
        sms_form.setSpacing(8)

        self.sms_provider = QComboBox()
        self.sms_provider.addItems([
            "SMSOperator.cz",
            "GoSMS.cz",
            "BulkGate",
            "Vlastní API"
        ])
        sms_form.addRow("Poskytovatel:", self.sms_provider)

        self.sms_api_key = QLineEdit()
        self.sms_api_key.setPlaceholderText("Váš API klíč")
        self.sms_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        sms_form.addRow("API klíč:", self.sms_api_key)

        self.sms_sender = QLineEdit()
        self.sms_sender.setPlaceholderText("Motoservis")
        self.sms_sender.setMaxLength(11)
        sms_form.addRow("Odesílatel:", self.sms_sender)

        self.sms_frame = QWidget()
        self.sms_frame.setLayout(sms_form)
        self.sms_frame.setEnabled(False)
        layout.addWidget(self.sms_frame)

        # Kredit a test
        credit_layout = QHBoxLayout()

        self.sms_credit = QLabel("Kredit: --")
        self.sms_credit.setStyleSheet("font-weight: bold;")
        credit_layout.addWidget(self.sms_credit)

        check_credit_btn = QPushButton("🔄 Zjistit kredit")
        check_credit_btn.clicked.connect(self.check_sms_credit)
        credit_layout.addWidget(check_credit_btn)

        test_sms_btn = QPushButton("🧪 Test SMS")
        test_sms_btn.clicked.connect(self.test_sms)
        credit_layout.addWidget(test_sms_btn)

        credit_layout.addStretch()
        layout.addLayout(credit_layout)

        return group

    def toggle_sms(self, checked):
        """Přepnutí SMS"""
        self.sms_frame.setEnabled(checked)

    def check_sms_credit(self):
        """Zjištění kreditu SMS"""
        QMessageBox.information(
            self,
            "SMS kredit",
            "Funkce zjištění kreditu bude implementována v další verzi."
        )

    def test_sms(self):
        """Test SMS"""
        QMessageBox.information(
            self,
            "Test SMS",
            "Funkce testovací SMS bude implementována v další verzi."
        )

    def create_notifications_section(self):
        """Sekce push notifikací"""
        group = QGroupBox("🔔 Notifikace v aplikaci")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 20, 15, 15)

        self.enable_app_notifications = QCheckBox("Povolit notifikace v aplikaci")
        self.enable_app_notifications.setChecked(True)
        layout.addWidget(self.enable_app_notifications)

        self.enable_sound = QCheckBox("Zvuk notifikace")
        self.enable_sound.setChecked(True)
        layout.addWidget(self.enable_sound)

        self.enable_desktop_notifications = QCheckBox("Desktop notifikace (systémové)")
        layout.addWidget(self.enable_desktop_notifications)

        # Typy notifikací
        notif_label = QLabel("Notifikovat při:")
        notif_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(notif_label)

        self.notif_new_order = QCheckBox("Nová zakázka")
        self.notif_new_order.setChecked(True)
        layout.addWidget(self.notif_new_order)

        self.notif_low_stock = QCheckBox("Nízký stav skladu")
        self.notif_low_stock.setChecked(True)
        layout.addWidget(self.notif_low_stock)

        self.notif_payment_received = QCheckBox("Přijatá platba")
        layout.addWidget(self.notif_payment_received)

        self.notif_calendar_reminder = QCheckBox("Připomínka z kalendáře")
        self.notif_calendar_reminder.setChecked(True)
        layout.addWidget(self.notif_calendar_reminder)

        return group

    def create_email_log_section(self):
        """Sekce logu odeslaných emailů"""
        group = QGroupBox("📋 Log odeslaných emailů")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        self.email_log_table = QTableWidget()
        self.email_log_table.setColumnCount(5)
        self.email_log_table.setHorizontalHeaderLabels([
            "Datum a čas", "Příjemce", "Předmět", "Stav", "Detail"
        ])

        header = self.email_log_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        self.email_log_table.setColumnWidth(0, 140)
        self.email_log_table.setColumnWidth(3, 80)
        self.email_log_table.setMaximumHeight(200)
        self.email_log_table.setAlternatingRowColors(True)

        layout.addWidget(self.email_log_table)

        # Tlačítka
        buttons_layout = QHBoxLayout()

        refresh_btn = QPushButton("🔄 Obnovit")
        refresh_btn.clicked.connect(self.load_email_log)

        clear_btn = QPushButton("🗑️ Vyčistit log")
        clear_btn.clicked.connect(self.clear_email_log)

        buttons_layout.addWidget(refresh_btn)
        buttons_layout.addWidget(clear_btn)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        return group

    def load_email_log(self):
        """Načtení logu emailů"""
        # TODO: Načíst z databáze
        self.email_log_table.setRowCount(0)

    def clear_email_log(self):
        """Vyčištění logu"""
        reply = QMessageBox.question(
            self,
            "Vyčistit log",
            "Opravdu chcete vyčistit log odeslaných emailů?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.email_log_table.setRowCount(0)

    def load_settings(self):
        """Načtení nastavení"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT key, value FROM app_settings WHERE key LIKE 'email_%'")
            rows = cursor.fetchall()

            settings = {}
            for key, value in rows:
                settings[key.replace("email_", "")] = value

            self.set_settings(settings)

        except Exception:
            pass

    def save_settings(self):
        """Uložení nastavení"""
        settings = self.get_settings()

        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            for key, value in settings.items():
                if isinstance(value, (dict, list, bool)):
                    value = json.dumps(value, ensure_ascii=False)
                cursor.execute("""
                    INSERT OR REPLACE INTO app_settings (key, value)
                    VALUES (?, ?)
                """, (f"email_{key}", str(value)))

            conn.commit()

        except Exception as e:
            raise Exception(f"Chyba při ukládání: {str(e)}")

    def get_settings(self):
        """Získání nastavení"""
        return {
            "smtp_server": self.smtp_server.text(),
            "smtp_port": self.smtp_port.value(),
            "smtp_encryption": self.smtp_encryption.currentText(),
            "smtp_username": self.smtp_username.text(),
            "smtp_password": self.smtp_password.text(),
            "smtp_from": self.smtp_from.text(),
            "smtp_reply_to": self.smtp_reply_to.text(),
            "smtp_from_name": self.smtp_from_name.text(),
            "auto_email_order_confirm": self.auto_email_order_confirm.isChecked(),
            "auto_email_status_change": self.auto_email_status_change.isChecked(),
            "auto_email_order_complete": self.auto_email_order_complete.isChecked(),
            "auto_email_invoice": self.auto_email_invoice.isChecked(),
            "auto_email_stk_reminder": self.auto_email_stk_reminder.isChecked(),
            "auto_email_payment_reminder": self.auto_email_payment_reminder.isChecked(),
            "auto_email_service_reminder": self.auto_email_service_reminder.isChecked(),
            "enable_signature": self.enable_signature.isChecked(),
            "signature_content": self.signature_editor.toPlainText(),
            "signature_logo": self.signature_logo.isChecked(),
            "signature_social": self.signature_social.isChecked(),
            "social_facebook": self.social_facebook.text(),
            "social_instagram": self.social_instagram.text(),
            "enable_sms": self.enable_sms.isChecked(),
            "sms_provider": self.sms_provider.currentText(),
            "sms_api_key": self.sms_api_key.text(),
            "sms_sender": self.sms_sender.text(),
            "enable_app_notifications": self.enable_app_notifications.isChecked(),
            "enable_sound": self.enable_sound.isChecked(),
            "enable_desktop_notifications": self.enable_desktop_notifications.isChecked(),
            "notif_new_order": self.notif_new_order.isChecked(),
            "notif_low_stock": self.notif_low_stock.isChecked(),
            "notif_payment_received": self.notif_payment_received.isChecked(),
            "notif_calendar_reminder": self.notif_calendar_reminder.isChecked()
        }

    def set_settings(self, settings):
        """Nastavení hodnot"""
        if "smtp_server" in settings:
            self.smtp_server.setText(settings["smtp_server"])
        if "smtp_port" in settings:
            self.smtp_port.setValue(int(settings["smtp_port"]))
        if "smtp_encryption" in settings:
            index = self.smtp_encryption.findText(settings["smtp_encryption"])
            if index >= 0:
                self.smtp_encryption.setCurrentIndex(index)
        if "smtp_username" in settings:
            self.smtp_username.setText(settings["smtp_username"])
        if "smtp_password" in settings:
            self.smtp_password.setText(settings["smtp_password"])
        if "smtp_from" in settings:
            self.smtp_from.setText(settings["smtp_from"])
        if "smtp_reply_to" in settings:
            self.smtp_reply_to.setText(settings["smtp_reply_to"])
        if "smtp_from_name" in settings:
            self.smtp_from_name.setText(settings["smtp_from_name"])
        if "signature_content" in settings:
            self.signature_editor.setPlainText(settings["signature_content"])
        if "social_facebook" in settings:
            self.social_facebook.setText(settings["social_facebook"])
        if "social_instagram" in settings:
            self.social_instagram.setText(settings["social_instagram"])
        if "sms_api_key" in settings:
            self.sms_api_key.setText(settings["sms_api_key"])
        if "sms_sender" in settings:
            self.sms_sender.setText(settings["sms_sender"])

    def refresh(self):
        """Obnovení"""
        self.load_settings()
        self.load_email_log()

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet(f"""
            #settingsGroup {{
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }}

            #settingsGroup::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}

            QLineEdit, QComboBox, QSpinBox {{
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }}

            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
                border: 2px solid #3498db;
            }}

            QTextEdit {{
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
            }}

            QTextEdit:focus {{
                border: 2px solid #3498db;
            }}

            QTableWidget {{
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }}

            QHeaderView::section {{
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
            }}

            QPushButton {{
                padding: 8px 16px;
                border-radius: 4px;
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
            }}

            QPushButton:hover {{
                background-color: #d5dbdb;
            }}

            #primaryButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
            }}

            #primaryButton:hover {{
                background-color: #2980b9;
            }}

            QCheckBox {{
                spacing: 8px;
            }}
        """)
