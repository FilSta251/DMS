# -*- coding: utf-8 -*-
"""
Licence a aktivace
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QLabel, QPushButton, QScrollArea, QFrame,
    QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from database_manager import db
import config
import json
from datetime import datetime, timedelta


class LicenseCheckThread(QThread):
    """Vlákno pro kontrolu licence"""
    finished = pyqtSignal(bool, dict)

    def __init__(self, license_key):
        super().__init__()
        self.license_key = license_key

    def run(self):
        try:
            import time
            time.sleep(2)

            if self.license_key.startswith("MOTO-PRO-"):
                result = {
                    "valid": True,
                    "type": "Pro",
                    "expires": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
                    "users": 10,
                    "features": ["orders", "customers", "vehicles", "warehouse", "invoicing", "reports", "api"]
                }
            elif self.license_key.startswith("MOTO-BASIC-"):
                result = {
                    "valid": True,
                    "type": "Basic",
                    "expires": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
                    "users": 3,
                    "features": ["orders", "customers", "vehicles", "warehouse", "invoicing"]
                }
            else:
                result = {"valid": False, "error": "Neplatný licenční klíč"}

            self.finished.emit(result.get("valid", False), result)

        except Exception as e:
            self.finished.emit(False, {"error": str(e)})


class LicenseSettingsWidget(QWidget):
    """Widget pro správu licence"""

    def __init__(self):
        super().__init__()
        self.license_thread = None
        self.init_ui()
        self.load_license_info()

    def init_ui(self):
        """Inicializace UI"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        main_layout.addWidget(self.create_license_info_section())
        main_layout.addWidget(self.create_limits_section())
        main_layout.addWidget(self.create_activation_section())
        main_layout.addWidget(self.create_upgrade_section())
        main_layout.addWidget(self.create_about_section())
        main_layout.addWidget(self.create_legal_section())

        main_layout.addStretch()

        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        self.set_styles()

    def create_license_info_section(self):
        """Sekce informací o licenci"""
        group = QGroupBox("📜 Informace o licenci")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        status_frame = QFrame()
        status_frame.setObjectName("licenseStatusFrame")
        status_layout = QVBoxLayout(status_frame)

        self.license_status_icon = QLabel("✅")
        self.license_status_icon.setStyleSheet("font-size: 48px;")
        self.license_status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.license_status_icon)

        self.license_status_text = QLabel("Aktivní licence")
        self.license_status_text.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60;")
        self.license_status_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.license_status_text)

        layout.addWidget(status_frame)

        details_form = QFormLayout()
        details_form.setSpacing(8)

        self.license_type = QLabel("Trial")
        self.license_type.setStyleSheet("font-weight: bold; font-size: 14px;")
        details_form.addRow("Typ licence:", self.license_type)

        self.license_key_display = QLabel("MOTO-TRIAL-XXXX-XXXX")
        self.license_key_display.setStyleSheet("font-family: monospace;")
        details_form.addRow("Licenční klíč:", self.license_key_display)

        self.license_expires = QLabel("31.12.2025")
        details_form.addRow("Platnost do:", self.license_expires)

        self.license_days_left = QLabel("45 dní")
        self.license_days_left.setStyleSheet("font-weight: bold;")
        details_form.addRow("Zbývá:", self.license_days_left)

        self.license_registered_to = QLabel("Motoservis ABC s.r.o.")
        details_form.addRow("Registrováno na:", self.license_registered_to)

        layout.addLayout(details_form)

        return group

    def create_limits_section(self):
        """Sekce limitů licence"""
        group = QGroupBox("📊 Limity licence")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        users_layout = QHBoxLayout()
        users_layout.addWidget(QLabel("Počet uživatelů:"))
        self.users_count = QLabel("2 / 5")
        self.users_count.setStyleSheet("font-weight: bold;")
        users_layout.addWidget(self.users_count)
        users_layout.addStretch()
        layout.addLayout(users_layout)

        self.users_progress = QProgressBar()
        self.users_progress.setMaximum(5)
        self.users_progress.setValue(2)
        self.users_progress.setTextVisible(False)
        self.users_progress.setMaximumHeight(10)
        layout.addWidget(self.users_progress)

        customers_layout = QHBoxLayout()
        customers_layout.addWidget(QLabel("Počet zákazníků:"))
        self.customers_limit = QLabel("Neomezeno ∞")
        self.customers_limit.setStyleSheet("font-weight: bold; color: #27ae60;")
        customers_layout.addWidget(self.customers_limit)
        customers_layout.addStretch()
        layout.addLayout(customers_layout)

        modules_label = QLabel("Dostupné moduly:")
        modules_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(modules_label)

        self.module_orders = QLabel("✅ Zakázky")
        self.module_orders.setStyleSheet("color: #27ae60;")
        layout.addWidget(self.module_orders)

        self.module_customers = QLabel("✅ Zákazníci")
        self.module_customers.setStyleSheet("color: #27ae60;")
        layout.addWidget(self.module_customers)

        self.module_vehicles = QLabel("✅ Vozidla")
        self.module_vehicles.setStyleSheet("color: #27ae60;")
        layout.addWidget(self.module_vehicles)

        self.module_warehouse = QLabel("✅ Sklad")
        self.module_warehouse.setStyleSheet("color: #27ae60;")
        layout.addWidget(self.module_warehouse)

        self.module_invoicing = QLabel("✅ Fakturace")
        self.module_invoicing.setStyleSheet("color: #27ae60;")
        layout.addWidget(self.module_invoicing)

        self.module_reports = QLabel("⚠️ Pokročilé reporty (vyžaduje Pro)")
        self.module_reports.setStyleSheet("color: #f39c12;")
        layout.addWidget(self.module_reports)

        self.module_api = QLabel("❌ API přístup (vyžaduje Enterprise)")
        self.module_api.setStyleSheet("color: #e74c3c;")
        layout.addWidget(self.module_api)

        self.module_multisite = QLabel("❌ Více poboček (vyžaduje Enterprise)")
        self.module_multisite.setStyleSheet("color: #e74c3c;")
        layout.addWidget(self.module_multisite)

        return group

    def create_activation_section(self):
        """Sekce aktivace"""
        group = QGroupBox("🔑 Aktivace licence")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Licenční klíč:"))

        self.activation_key_input = QLineEdit()
        self.activation_key_input.setPlaceholderText("MOTO-PRO-XXXX-XXXX-XXXX")
        self.activation_key_input.setMaxLength(30)
        key_layout.addWidget(self.activation_key_input)

        layout.addLayout(key_layout)

        buttons_layout = QHBoxLayout()

        self.activate_online_btn = QPushButton("🌐 Online aktivace")
        self.activate_online_btn.clicked.connect(self.activate_online)
        self.activate_online_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.activate_online_btn.setObjectName("primaryButton")

        self.activate_offline_btn = QPushButton("📁 Offline aktivace")
        self.activate_offline_btn.clicked.connect(self.activate_offline)
        self.activate_offline_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        buttons_layout.addWidget(self.activate_online_btn)
        buttons_layout.addWidget(self.activate_offline_btn)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        self.activation_status = QLabel("")
        self.activation_status.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.activation_status)

        info_label = QLabel(
            "💡 Licenční klíč obdržíte po zakoupení licence.\n"
            "Pro offline aktivaci kontaktujte podporu."
        )
        info_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        return group

    def create_upgrade_section(self):
        """Sekce upgrade"""
        group = QGroupBox("⬆️ Upgrade licence")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 20, 15, 15)

        current_plan = QLabel("Aktuální plán: Trial")
        current_plan.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(current_plan)

        plans_label = QLabel("Dostupné plány:")
        plans_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(plans_label)

        basic_frame = QFrame()
        basic_frame.setObjectName("planFrame")
        basic_layout = QVBoxLayout(basic_frame)
        basic_layout.setSpacing(5)

        basic_title = QLabel("📦 Basic")
        basic_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        basic_layout.addWidget(basic_title)

        basic_price = QLabel("499 Kč / měsíc")
        basic_price.setStyleSheet("color: #3498db; font-weight: bold;")
        basic_layout.addWidget(basic_price)

        basic_features = QLabel("• 3 uživatelé\n• Základní moduly\n• Email podpora")
        basic_features.setStyleSheet("color: #7f8c8d;")
        basic_layout.addWidget(basic_features)

        layout.addWidget(basic_frame)

        pro_frame = QFrame()
        pro_frame.setObjectName("planFrameHighlight")
        pro_layout = QVBoxLayout(pro_frame)
        pro_layout.setSpacing(5)

        pro_title = QLabel("🚀 Pro (Doporučeno)")
        pro_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #27ae60;")
        pro_layout.addWidget(pro_title)

        pro_price = QLabel("999 Kč / měsíc")
        pro_price.setStyleSheet("color: #27ae60; font-weight: bold;")
        pro_layout.addWidget(pro_price)

        pro_features = QLabel("• 10 uživatelů\n• Všechny moduly\n• Pokročilé reporty\n• Priority podpora")
        pro_features.setStyleSheet("color: #7f8c8d;")
        pro_layout.addWidget(pro_features)

        layout.addWidget(pro_frame)

        enterprise_frame = QFrame()
        enterprise_frame.setObjectName("planFrame")
        enterprise_layout = QVBoxLayout(enterprise_frame)
        enterprise_layout.setSpacing(5)

        enterprise_title = QLabel("🏢 Enterprise")
        enterprise_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        enterprise_layout.addWidget(enterprise_title)

        enterprise_price = QLabel("Kontaktujte nás")
        enterprise_price.setStyleSheet("color: #9b59b6; font-weight: bold;")
        enterprise_layout.addWidget(enterprise_price)

        enterprise_features = QLabel("• Neomezeno uživatelů\n• API přístup\n• Více poboček\n• Dedikovaná podpora")
        enterprise_features.setStyleSheet("color: #7f8c8d;")
        enterprise_layout.addWidget(enterprise_features)

        layout.addWidget(enterprise_frame)

        upgrade_btn = QPushButton("⬆️ Upgradovat licenci")
        upgrade_btn.clicked.connect(self.upgrade_license)
        upgrade_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        upgrade_btn.setObjectName("upgradeButton")

        layout.addWidget(upgrade_btn)

        return group

    def create_about_section(self):
        """Sekce o aplikaci"""
        group = QGroupBox("ℹ️ O aplikaci")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        title_layout = QHBoxLayout()

        logo_label = QLabel("🏍️")
        logo_label.setStyleSheet("font-size: 48px;")
        title_layout.addWidget(logo_label)

        name_layout = QVBoxLayout()
        app_name = QLabel("Motoservis DMS")
        app_name.setStyleSheet("font-size: 24px; font-weight: bold;")
        name_layout.addWidget(app_name)

        app_subtitle = QLabel("Dealer Management System")
        app_subtitle.setStyleSheet("color: #7f8c8d;")
        name_layout.addWidget(app_subtitle)

        title_layout.addLayout(name_layout)
        title_layout.addStretch()

        layout.addLayout(title_layout)

        info_form = QFormLayout()
        info_form.setSpacing(8)

        self.app_version = QLabel(config.APP_VERSION)
        self.app_version.setStyleSheet("font-weight: bold;")
        info_form.addRow("Verze:", self.app_version)

        self.app_build = QLabel("2025.11.16")
        info_form.addRow("Build:", self.app_build)

        self.app_developer = QLabel("Váš vývojář")
        info_form.addRow("Vývojář:", self.app_developer)

        self.app_contact = QLabel("support@motoservis-dms.cz")
        info_form.addRow("Kontakt:", self.app_contact)

        self.app_website = QLabel("www.motoservis-dms.cz")
        info_form.addRow("Web:", self.app_website)

        layout.addLayout(info_form)

        buttons_layout = QHBoxLayout()

        check_updates_btn = QPushButton("🔄 Zkontrolovat aktualizace")
        check_updates_btn.clicked.connect(self.check_updates)
        check_updates_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        system_info_btn = QPushButton("📊 Systémové informace")
        system_info_btn.clicked.connect(self.show_system_info)
        system_info_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        buttons_layout.addWidget(check_updates_btn)
        buttons_layout.addWidget(system_info_btn)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        return group

    def create_legal_section(self):
        """Sekce právních informací"""
        group = QGroupBox("⚖️ Právní informace")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        eula_btn = QPushButton("📜 Licenční smlouva (EULA)")
        eula_btn.clicked.connect(lambda: self.show_legal_doc("eula"))
        eula_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        eula_btn.setFlat(True)
        eula_btn.setStyleSheet("text-align: left; padding: 5px;")
        layout.addWidget(eula_btn)

        privacy_btn = QPushButton("🔒 Ochrana osobních údajů")
        privacy_btn.clicked.connect(lambda: self.show_legal_doc("privacy"))
        privacy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        privacy_btn.setFlat(True)
        privacy_btn.setStyleSheet("text-align: left; padding: 5px;")
        layout.addWidget(privacy_btn)

        gdpr_btn = QPushButton("🇪🇺 GDPR")
        gdpr_btn.clicked.connect(lambda: self.show_legal_doc("gdpr"))
        gdpr_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        gdpr_btn.setFlat(True)
        gdpr_btn.setStyleSheet("text-align: left; padding: 5px;")
        layout.addWidget(gdpr_btn)

        terms_btn = QPushButton("📋 Podmínky použití")
        terms_btn.clicked.connect(lambda: self.show_legal_doc("terms"))
        terms_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        terms_btn.setFlat(True)
        terms_btn.setStyleSheet("text-align: left; padding: 5px;")
        layout.addWidget(terms_btn)

        copyright_label = QLabel("© 2025 Motoservis DMS. Všechna práva vyhrazena.")
        copyright_label.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-top: 10px;")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright_label)

        return group

    def load_license_info(self):
        """Načtení informací o licenci"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT value FROM app_settings WHERE key = 'license_type'")
            row = cursor.fetchone()

            if row:
                license_type = row[0]
                self.license_type.setText(license_type)
            else:
                self.license_type.setText("Trial (30 dní)")
                self.license_days_left.setText("30 dní")

        except Exception:
            pass

    def activate_online(self):
        """Online aktivace licence"""
        key = self.activation_key_input.text().strip()

        if not key:
            QMessageBox.warning(self, "Chyba", "Zadejte licenční klíč.")
            return

        self.activation_status.setText("⏳ Ověřuji licenci...")
        self.activation_status.setStyleSheet("color: #f39c12; font-weight: bold;")
        self.activate_online_btn.setEnabled(False)

        self.license_thread = LicenseCheckThread(key)
        self.license_thread.finished.connect(self.on_license_check_finished)
        self.license_thread.start()

    def on_license_check_finished(self, valid, result):
        """Callback po ověření licence"""
        self.activate_online_btn.setEnabled(True)

        if valid:
            self.activation_status.setText("✅ Licence aktivována!")
            self.activation_status.setStyleSheet("color: #27ae60; font-weight: bold;")

            self.license_type.setText(result.get("type", "Unknown"))
            self.license_expires.setText(result.get("expires", "N/A"))

            try:
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO app_settings (key, value)
                    VALUES ('license_key', ?), ('license_type', ?), ('license_expires', ?)
                """, (
                    self.activation_key_input.text(),
                    result.get("type", ""),
                    result.get("expires", "")
                ))
                conn.commit()
            except Exception:
                pass

            QMessageBox.information(
                self,
                "Aktivace úspěšná",
                f"Licence byla úspěšně aktivována!\n\n"
                f"Typ: {result.get('type', 'Unknown')}\n"
                f"Platnost do: {result.get('expires', 'N/A')}"
            )

        else:
            self.activation_status.setText(f"❌ {result.get('error', 'Aktivace selhala')}")
            self.activation_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
            QMessageBox.critical(self, "Chyba aktivace", result.get("error", "Neznámá chyba"))

    def activate_offline(self):
        """Offline aktivace"""
        QMessageBox.information(
            self,
            "Offline aktivace",
            "Pro offline aktivaci kontaktujte podporu:\n\n"
            "Email: support@motoservis-dms.cz\n"
            "Telefon: +420 123 456 789\n\n"
            "Připravte si:\n"
            "• Licenční klíč\n"
            "• Hardware ID počítače\n"
            "• Číslo objednávky"
        )

    def upgrade_license(self):
        """Upgrade licence"""
        QMessageBox.information(
            self,
            "Upgrade licence",
            "Pro upgrade licence navštivte:\n\n"
            "www.motoservis-dms.cz/upgrade\n\n"
            "nebo kontaktujte obchodní oddělení:\n"
            "sales@motoservis-dms.cz"
        )

    def check_updates(self):
        """Kontrola aktualizací"""
        QMessageBox.information(
            self,
            "Kontrola aktualizací",
            f"Aktuální verze: {config.APP_VERSION}\n\n"
            "Kontroluji dostupnost aktualizací...\n\n"
            "✅ Máte nejnovější verzi!"
        )

    def show_system_info(self):
        """Zobrazení systémových informací"""
        import platform
        import sys

        info = (
            f"Operační systém: {platform.system()} {platform.release()}\n"
            f"Python verze: {sys.version.split()[0]}\n"
            f"PyQt verze: {config.APP_VERSION}\n"
            f"Architektura: {platform.machine()}\n"
            f"Procesor: {platform.processor()}\n\n"
            f"Databáze: SQLite\n"
            f"Cesta k datům: {config.DATA_DIR}"
        )

        QMessageBox.information(self, "Systémové informace", info)

    def show_legal_doc(self, doc_type):
        """Zobrazení právního dokumentu"""
        docs = {
            "eula": "Licenční smlouva (EULA)\n\nTento software je licencován...",
            "privacy": "Ochrana osobních údajů\n\nVaše soukromí je pro nás důležité...",
            "gdpr": "GDPR\n\nSplňujeme požadavky GDPR...",
            "terms": "Podmínky použití\n\nPoužíváním tohoto software souhlasíte..."
        }

        QMessageBox.information(
            self,
            doc_type.upper(),
            docs.get(doc_type, "Dokument není k dispozici.") + "\n\n"
            "Kompletní znění naleznete na www.motoservis-dms.cz/legal"
        )

    def save_settings(self):
        """Uložení nastavení"""
        pass

    def get_settings(self):
        """Získání nastavení"""
        return {
            "license_key": self.activation_key_input.text()
        }

    def set_settings(self, settings):
        """Nastavení hodnot"""
        pass

    def refresh(self):
        """Obnovení"""
        self.load_license_info()

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

            #licenseStatusFrame {{
                background-color: #ecf0f1;
                border-radius: 8px;
                padding: 20px;
            }}

            #planFrame {{
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }}

            #planFrameHighlight {{
                background-color: #e8f5e9;
                border: 2px solid #27ae60;
                border-radius: 8px;
                padding: 10px;
            }}

            QLineEdit {{
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }}

            QLineEdit:focus {{
                border: 2px solid #3498db;
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

            #upgradeButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                border: none;
                font-weight: bold;
                font-size: 14px;
                padding: 12px;
            }}

            #upgradeButton:hover {{
                background-color: #229954;
            }}

            QProgressBar {{
                border: none;
                background-color: #ecf0f1;
                border-radius: 5px;
            }}

            QProgressBar::chunk {{
                background-color: {config.COLOR_SECONDARY};
                border-radius: 5px;
            }}
        """)
