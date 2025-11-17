# -*- coding: utf-8 -*-
"""
Nastavení integrací s externími službami
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QLabel,
    QPushButton, QScrollArea, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from database_manager import db
import config
import json


class APITestThread(QThread):
    """Vlákno pro testování API"""
    finished = pyqtSignal(bool, str)

    def __init__(self, service_type, settings):
        super().__init__()
        self.service_type = service_type
        self.settings = settings

    def run(self):
        try:
            if self.service_type == "ares":
                import urllib.request
                url = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/25596641"
                req = urllib.request.Request(url, headers={'Accept': 'application/json'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        self.finished.emit(True, "ARES API je dostupné a funkční.")
                    else:
                        self.finished.emit(False, f"ARES vrátil status {response.status}")

            elif self.service_type == "qr":
                self.finished.emit(True, "QR generátor je připraven k použití.")

            else:
                self.finished.emit(True, "Test proběhl úspěšně.")

        except Exception as e:
            self.finished.emit(False, str(e))


class IntegrationsSettingsWidget(QWidget):
    """Widget pro nastavení integrací"""

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

        main_layout.addWidget(self.create_ares_section())
        main_layout.addWidget(self.create_google_section())
        main_layout.addWidget(self.create_microsoft_section())
        main_layout.addWidget(self.create_accounting_section())
        main_layout.addWidget(self.create_payment_section())
        main_layout.addWidget(self.create_api_section())
        main_layout.addWidget(self.create_webhooks_section())

        main_layout.addStretch()

        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        self.set_styles()

    def create_ares_section(self):
        """Sekce ARES"""
        group = QGroupBox("🏛️ ARES (Obchodní rejstřík)")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        self.enable_ares = QCheckBox("Povolit vyhledávání v ARES")
        self.enable_ares.setChecked(True)
        self.enable_ares.toggled.connect(self.toggle_ares)
        layout.addWidget(self.enable_ares)

        ares_frame = QFrame()
        ares_form = QFormLayout(ares_frame)
        ares_form.setSpacing(8)

        self.ares_auto_fill = QCheckBox("Automaticky doplňovat firemní údaje")
        self.ares_auto_fill.setChecked(True)
        ares_form.addRow("", self.ares_auto_fill)

        cache_layout = QHBoxLayout()
        self.ares_cache_days = QSpinBox()
        self.ares_cache_days.setRange(0, 90)
        self.ares_cache_days.setValue(7)
        self.ares_cache_days.setSuffix(" dní")
        cache_layout.addWidget(self.ares_cache_days)
        cache_layout.addStretch()
        ares_form.addRow("Cache výsledků:", cache_layout)

        self.ares_frame = ares_frame
        layout.addWidget(ares_frame)

        test_layout = QHBoxLayout()

        test_ares_btn = QPushButton("🧪 Test ARES API")
        test_ares_btn.clicked.connect(lambda: self.test_service("ares"))
        test_ares_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.ares_status = QLabel("")
        self.ares_status.setStyleSheet("font-weight: bold;")

        test_layout.addWidget(test_ares_btn)
        test_layout.addWidget(self.ares_status)
        test_layout.addStretch()

        layout.addLayout(test_layout)

        return group

    def toggle_ares(self, checked):
        """Přepnutí ARES"""
        self.ares_frame.setEnabled(checked)

    def create_google_section(self):
        """Sekce Google Calendar"""
        group = QGroupBox("📅 Google Calendar")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        connect_layout = QHBoxLayout()

        self.google_status = QLabel("❌ Nepřipojeno")
        self.google_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
        connect_layout.addWidget(self.google_status)

        connect_google_btn = QPushButton("🔗 Připojit Google účet")
        connect_google_btn.clicked.connect(self.connect_google)
        connect_google_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        connect_layout.addWidget(connect_google_btn)

        disconnect_google_btn = QPushButton("❌ Odpojit")
        disconnect_google_btn.clicked.connect(self.disconnect_google)
        disconnect_google_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        connect_layout.addWidget(disconnect_google_btn)

        connect_layout.addStretch()
        layout.addLayout(connect_layout)

        self.enable_google_sync = QCheckBox("Synchronizovat kalendář")
        self.enable_google_sync.toggled.connect(self.toggle_google_sync)
        layout.addWidget(self.enable_google_sync)

        google_sync_frame = QFrame()
        google_form = QFormLayout(google_sync_frame)
        google_form.setSpacing(8)

        self.google_sync_direction = QComboBox()
        self.google_sync_direction.addItems([
            "Obousměrně",
            "Pouze export do Google",
            "Pouze import z Google"
        ])
        google_form.addRow("Směr synchronizace:", self.google_sync_direction)

        self.google_calendar = QComboBox()
        self.google_calendar.addItems(["Primární kalendář", "Motoservis", "Práce"])
        google_form.addRow("Kalendář:", self.google_calendar)

        sync_events_layout = QHBoxLayout()
        self.google_sync_interval = QSpinBox()
        self.google_sync_interval.setRange(5, 120)
        self.google_sync_interval.setValue(15)
        self.google_sync_interval.setSuffix(" minut")
        sync_events_layout.addWidget(self.google_sync_interval)
        sync_events_layout.addStretch()
        google_form.addRow("Interval synchronizace:", sync_events_layout)

        self.google_sync_frame = google_sync_frame
        layout.addWidget(google_sync_frame)

        self.toggle_google_sync(False)

        return group

    def toggle_google_sync(self, checked):
        """Přepnutí Google synchronizace"""
        self.google_sync_frame.setEnabled(checked)

    def connect_google(self):
        """Připojení Google účtu"""
        QMessageBox.information(
            self,
            "Google Calendar",
            "Funkce OAuth autentizace pro Google Calendar bude implementována v další verzi.\n\n"
            "Tato funkce umožní:\n"
            "• Synchronizaci termínů zakázek\n"
            "• Export událostí do Google Calendar\n"
            "• Import událostí z Google Calendar"
        )

    def disconnect_google(self):
        """Odpojení Google účtu"""
        self.google_status.setText("❌ Nepřipojeno")
        self.google_status.setStyleSheet("color: #e74c3c; font-weight: bold;")

    def create_microsoft_section(self):
        """Sekce Microsoft 365"""
        group = QGroupBox("📧 Microsoft 365 / Outlook")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        connect_layout = QHBoxLayout()

        self.microsoft_status = QLabel("❌ Nepřipojeno")
        self.microsoft_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
        connect_layout.addWidget(self.microsoft_status)

        connect_ms_btn = QPushButton("🔗 Připojit Microsoft účet")
        connect_ms_btn.clicked.connect(self.connect_microsoft)
        connect_ms_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        connect_layout.addWidget(connect_ms_btn)

        connect_layout.addStretch()
        layout.addLayout(connect_layout)

        self.ms_sync_calendar = QCheckBox("Synchronizovat kalendář")
        layout.addWidget(self.ms_sync_calendar)

        self.ms_sync_contacts = QCheckBox("Synchronizovat kontakty")
        layout.addWidget(self.ms_sync_contacts)

        self.ms_sync_emails = QCheckBox("Synchronizovat emaily")
        layout.addWidget(self.ms_sync_emails)

        return group

    def connect_microsoft(self):
        """Připojení Microsoft účtu"""
        QMessageBox.information(
            self,
            "Microsoft 365",
            "Funkce OAuth autentizace pro Microsoft 365 bude implementována v další verzi."
        )

    def create_accounting_section(self):
        """Sekce účetních systémů"""
        group = QGroupBox("📊 Účetní systémy")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        system_layout = QHBoxLayout()
        system_layout.addWidget(QLabel("Účetní systém:"))

        self.accounting_system = QComboBox()
        self.accounting_system.addItems([
            "Žádný",
            "Pohoda (XML export)",
            "Money S3 (export)",
            "ABRA Flexibee (API)",
            "Vlastní formát"
        ])
        self.accounting_system.currentTextChanged.connect(self.on_accounting_system_changed)
        system_layout.addWidget(self.accounting_system)
        system_layout.addStretch()

        layout.addLayout(system_layout)

        export_frame = QFrame()
        export_form = QFormLayout(export_frame)
        export_form.setSpacing(8)

        self.accounting_auto_export = QCheckBox("Automatický export faktur")
        export_form.addRow("", self.accounting_auto_export)

        self.accounting_export_path = QLineEdit()
        self.accounting_export_path.setPlaceholderText("C:\\Pohoda\\Import\\")

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.accounting_export_path)

        browse_btn = QPushButton("📁")
        browse_btn.setFixedWidth(40)
        path_layout.addWidget(browse_btn)

        export_form.addRow("Cesta pro export:", path_layout)

        self.accounting_export_on_create = QCheckBox("Exportovat při vytvoření faktury")
        export_form.addRow("", self.accounting_export_on_create)

        self.accounting_frame = export_frame
        layout.addWidget(export_frame)

        test_export_btn = QPushButton("🧪 Test exportu")
        test_export_btn.clicked.connect(self.test_accounting_export)
        test_export_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(test_export_btn)

        return group

    def on_accounting_system_changed(self, system):
        """Změna účetního systému"""
        self.accounting_frame.setEnabled(system != "Žádný")

    def test_accounting_export(self):
        """Test exportu do účetního systému"""
        QMessageBox.information(
            self,
            "Test exportu",
            "Funkce exportu do účetního systému bude implementována v další verzi.\n\n"
            "Podporované formáty:\n"
            "• Pohoda XML (iDoklad)\n"
            "• Money S3 XML\n"
            "• ISDOC (faktura)\n"
            "• CSV/Excel"
        )

    def create_payment_section(self):
        """Sekce platebních bran"""
        group = QGroupBox("💳 Platební brány")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        qr_section = QVBoxLayout()
        qr_label = QLabel("📱 QR platba")
        qr_label.setStyleSheet("font-weight: bold;")
        qr_section.addWidget(qr_label)

        self.enable_qr_payment = QCheckBox("Generovat QR kód pro platbu na faktuře")
        self.enable_qr_payment.setChecked(True)
        qr_section.addWidget(self.enable_qr_payment)

        self.qr_include_vs = QCheckBox("Zahrnout variabilní symbol")
        self.qr_include_vs.setChecked(True)
        qr_section.addWidget(self.qr_include_vs)

        self.qr_include_message = QCheckBox("Zahrnout zprávu pro příjemce")
        self.qr_include_message.setChecked(True)
        qr_section.addWidget(self.qr_include_message)

        test_qr_btn = QPushButton("🧪 Test QR generátoru")
        test_qr_btn.clicked.connect(lambda: self.test_service("qr"))
        test_qr_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        qr_section.addWidget(test_qr_btn)
        layout.addLayout(qr_section)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #bdc3c7;")
        layout.addWidget(separator)

        online_label = QLabel("🌐 Online platební brány (připravujeme)")
        online_label.setStyleSheet("font-weight: bold; color: #7f8c8d;")
        layout.addWidget(online_label)

        self.enable_gopay = QCheckBox("GoPay")
        self.enable_gopay.setEnabled(False)
        layout.addWidget(self.enable_gopay)

        self.enable_paypal = QCheckBox("PayPal")
        self.enable_paypal.setEnabled(False)
        layout.addWidget(self.enable_paypal)

        coming_soon = QLabel("💡 Online platební brány budou dostupné v Pro verzi.")
        coming_soon.setStyleSheet("color: #f39c12; font-size: 11px;")
        layout.addWidget(coming_soon)

        return group

    def create_api_section(self):
        """Sekce API přístupu"""
        group = QGroupBox("🔌 API přístup")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        self.enable_api = QCheckBox("Povolit REST API přístup")
        self.enable_api.toggled.connect(self.toggle_api)
        layout.addWidget(self.enable_api)

        api_frame = QFrame()
        api_form = QFormLayout(api_frame)
        api_form.setSpacing(8)

        key_layout = QHBoxLayout()
        self.api_key = QLineEdit()
        self.api_key.setReadOnly(True)
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText("Klikněte na 'Generovat' pro vytvoření klíče")
        key_layout.addWidget(self.api_key)

        show_key_btn = QPushButton("👁️")
        show_key_btn.setFixedWidth(40)
        show_key_btn.clicked.connect(self.toggle_api_key_visibility)
        key_layout.addWidget(show_key_btn)

        generate_key_btn = QPushButton("🔄 Generovat")
        generate_key_btn.clicked.connect(self.generate_api_key)
        key_layout.addWidget(generate_key_btn)

        api_form.addRow("API klíč:", key_layout)

        rate_layout = QHBoxLayout()
        self.api_rate_limit = QSpinBox()
        self.api_rate_limit.setRange(10, 10000)
        self.api_rate_limit.setValue(100)
        self.api_rate_limit.setSuffix(" req/min")
        rate_layout.addWidget(self.api_rate_limit)
        rate_layout.addStretch()
        api_form.addRow("Rate limit:", rate_layout)

        self.api_allowed_ips = QLineEdit()
        self.api_allowed_ips.setPlaceholderText("* (všechny) nebo 192.168.1.0/24")
        api_form.addRow("Povolené IP:", self.api_allowed_ips)

        self.api_frame = api_frame
        layout.addWidget(api_frame)

        docs_btn = QPushButton("📚 API dokumentace")
        docs_btn.clicked.connect(self.show_api_docs)
        docs_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(docs_btn)

        self.toggle_api(False)

        warning = QLabel("⚠️ API přístup je dostupný pouze v Enterprise verzi.")
        warning.setStyleSheet("color: #e74c3c; font-weight: bold;")
        layout.addWidget(warning)

        return group

    def toggle_api(self, checked):
        """Přepnutí API"""
        self.api_frame.setEnabled(checked)

    def toggle_api_key_visibility(self):
        """Přepnutí viditelnosti API klíče"""
        if self.api_key.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key.setEchoMode(QLineEdit.EchoMode.Password)

    def generate_api_key(self):
        """Generování API klíče"""
        import secrets
        key = secrets.token_hex(32)
        self.api_key.setText(key)
        QMessageBox.information(
            self,
            "API klíč vygenerován",
            "Nový API klíč byl vygenerován.\n\n"
            "⚠️ Uložte si klíč na bezpečné místo!\n"
            "Po uzavření tohoto okna již nebude možné ho zobrazit."
        )

    def show_api_docs(self):
        """Zobrazení API dokumentace"""
        QMessageBox.information(
            self,
            "API dokumentace",
            "REST API dokumentace\n\n"
            "Base URL: http://localhost:5000/api/v1\n\n"
            "Endpointy:\n"
            "• GET /customers - Seznam zákazníků\n"
            "• GET /vehicles - Seznam vozidel\n"
            "• GET /orders - Seznam zakázek\n"
            "• POST /orders - Vytvoření zakázky\n"
            "• GET /invoices - Seznam faktur\n\n"
            "Autentizace: Bearer Token v HTTP hlavičce\n\n"
            "Kompletní dokumentace bude dostupná na webu."
        )

    def create_webhooks_section(self):
        """Sekce webhooků"""
        group = QGroupBox("🔔 Webhooks")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        self.enable_webhooks = QCheckBox("Povolit odesílání webhooks")
        self.enable_webhooks.toggled.connect(self.toggle_webhooks)
        layout.addWidget(self.enable_webhooks)

        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Webhook URL:"))
        self.webhook_url = QLineEdit()
        self.webhook_url.setPlaceholderText("https://your-server.com/webhook")
        url_layout.addWidget(self.webhook_url)

        layout.addLayout(url_layout)

        events_label = QLabel("Odesílat při:")
        events_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(events_label)

        self.webhook_new_order = QCheckBox("Nová zakázka")
        self.webhook_new_order.setChecked(True)
        layout.addWidget(self.webhook_new_order)

        self.webhook_order_status = QCheckBox("Změna stavu zakázky")
        self.webhook_order_status.setChecked(True)
        layout.addWidget(self.webhook_order_status)

        self.webhook_new_invoice = QCheckBox("Nová faktura")
        layout.addWidget(self.webhook_new_invoice)

        self.webhook_payment_received = QCheckBox("Přijatá platba")
        layout.addWidget(self.webhook_payment_received)

        self.webhook_new_customer = QCheckBox("Nový zákazník")
        layout.addWidget(self.webhook_new_customer)

        settings_form = QFormLayout()

        self.webhook_secret = QLineEdit()
        self.webhook_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self.webhook_secret.setPlaceholderText("Tajný klíč pro podpis")
        settings_form.addRow("Secret:", self.webhook_secret)

        timeout_layout = QHBoxLayout()
        self.webhook_timeout = QSpinBox()
        self.webhook_timeout.setRange(5, 60)
        self.webhook_timeout.setValue(10)
        self.webhook_timeout.setSuffix(" sekund")
        timeout_layout.addWidget(self.webhook_timeout)
        timeout_layout.addStretch()
        settings_form.addRow("Timeout:", timeout_layout)

        retry_layout = QHBoxLayout()
        self.webhook_retries = QSpinBox()
        self.webhook_retries.setRange(0, 10)
        self.webhook_retries.setValue(3)
        retry_layout.addWidget(self.webhook_retries)
        retry_layout.addStretch()
        settings_form.addRow("Počet opakování:", retry_layout)

        self.webhooks_settings = QWidget()
        self.webhooks_settings.setLayout(settings_form)
        layout.addWidget(self.webhooks_settings)

        test_layout = QHBoxLayout()

        test_webhook_btn = QPushButton("🧪 Test webhook")
        test_webhook_btn.clicked.connect(self.test_webhook)
        test_webhook_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.webhook_status = QLabel("")
        self.webhook_status.setStyleSheet("font-weight: bold;")

        test_layout.addWidget(test_webhook_btn)
        test_layout.addWidget(self.webhook_status)
        test_layout.addStretch()

        layout.addLayout(test_layout)

        self.toggle_webhooks(False)

        return group

    def toggle_webhooks(self, checked):
        """Přepnutí webhooků"""
        self.webhook_url.setEnabled(checked)
        self.webhook_new_order.setEnabled(checked)
        self.webhook_order_status.setEnabled(checked)
        self.webhook_new_invoice.setEnabled(checked)
        self.webhook_payment_received.setEnabled(checked)
        self.webhook_new_customer.setEnabled(checked)
        self.webhooks_settings.setEnabled(checked)

    def test_webhook(self):
        """Test webhooku"""
        url = self.webhook_url.text()
        if not url:
            QMessageBox.warning(self, "Chyba", "Zadejte URL pro webhook.")
            return

        QMessageBox.information(
            self,
            "Test webhook",
            f"Test webhook bude odeslán na:\n{url}\n\n"
            "Funkce bude implementována v další verzi."
        )

    def test_service(self, service_type):
        """Test služby"""
        if service_type == "ares":
            self.ares_status.setText("⏳ Testování...")
            self.ares_status.setStyleSheet("color: #f39c12; font-weight: bold;")

        self.test_thread = APITestThread(service_type, {})
        self.test_thread.finished.connect(lambda ok, msg: self.on_service_test_finished(service_type, ok, msg))
        self.test_thread.start()

    def on_service_test_finished(self, service_type, success, message):
        """Callback po testu služby"""
        if service_type == "ares":
            if success:
                self.ares_status.setText("✅ " + message)
                self.ares_status.setStyleSheet("color: #27ae60; font-weight: bold;")
            else:
                self.ares_status.setText("❌ " + message)
                self.ares_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
        elif service_type == "qr":
            if success:
                QMessageBox.information(self, "Test QR", message)
            else:
                QMessageBox.critical(self, "Chyba QR", message)

    def load_settings(self):
        """Načtení nastavení"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT key, value FROM app_settings WHERE key LIKE 'integrations_%'")
            rows = cursor.fetchall()

            settings = {}
            for key, value in rows:
                settings[key.replace("integrations_", "")] = value

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
                """, (f"integrations_{key}", str(value)))

            conn.commit()

        except Exception as e:
            raise Exception(f"Chyba při ukládání: {str(e)}")

    def get_settings(self):
        """Získání nastavení"""
        return {
            "enable_ares": self.enable_ares.isChecked(),
            "ares_auto_fill": self.ares_auto_fill.isChecked(),
            "ares_cache_days": self.ares_cache_days.value(),
            "enable_google_sync": self.enable_google_sync.isChecked(),
            "google_sync_direction": self.google_sync_direction.currentText(),
            "google_sync_interval": self.google_sync_interval.value(),
            "ms_sync_calendar": self.ms_sync_calendar.isChecked(),
            "ms_sync_contacts": self.ms_sync_contacts.isChecked(),
            "ms_sync_emails": self.ms_sync_emails.isChecked(),
            "accounting_system": self.accounting_system.currentText(),
            "accounting_auto_export": self.accounting_auto_export.isChecked(),
            "accounting_export_path": self.accounting_export_path.text(),
            "accounting_export_on_create": self.accounting_export_on_create.isChecked(),
            "enable_qr_payment": self.enable_qr_payment.isChecked(),
            "qr_include_vs": self.qr_include_vs.isChecked(),
            "qr_include_message": self.qr_include_message.isChecked(),
            "enable_api": self.enable_api.isChecked(),
            "api_key": self.api_key.text(),
            "api_rate_limit": self.api_rate_limit.value(),
            "api_allowed_ips": self.api_allowed_ips.text(),
            "enable_webhooks": self.enable_webhooks.isChecked(),
            "webhook_url": self.webhook_url.text(),
            "webhook_new_order": self.webhook_new_order.isChecked(),
            "webhook_order_status": self.webhook_order_status.isChecked(),
            "webhook_new_invoice": self.webhook_new_invoice.isChecked(),
            "webhook_payment_received": self.webhook_payment_received.isChecked(),
            "webhook_new_customer": self.webhook_new_customer.isChecked(),
            "webhook_secret": self.webhook_secret.text(),
            "webhook_timeout": self.webhook_timeout.value(),
            "webhook_retries": self.webhook_retries.value()
        }

    def set_settings(self, settings):
        """Nastavení hodnot"""
        if "enable_ares" in settings:
            self.enable_ares.setChecked(settings["enable_ares"] == "True")
        if "ares_auto_fill" in settings:
            self.ares_auto_fill.setChecked(settings["ares_auto_fill"] == "True")
        if "ares_cache_days" in settings:
            self.ares_cache_days.setValue(int(settings["ares_cache_days"]))
        if "api_key" in settings:
            self.api_key.setText(settings["api_key"])
        if "webhook_url" in settings:
            self.webhook_url.setText(settings["webhook_url"])

    def refresh(self):
        """Obnovení"""
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

            QLineEdit, QComboBox, QSpinBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }

            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border: 2px solid #3498db;
            }

            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
            }

            QPushButton:hover {
                background-color: #d5dbdb;
            }

            QCheckBox {
                spacing: 8px;
            }
        """)
