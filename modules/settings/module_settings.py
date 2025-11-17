# -*- coding: utf-8 -*-
"""
Modul Nastavení - Hlavní vstupní bod
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QStackedWidget, QLineEdit, QScrollArea, QMessageBox,
    QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import json
from pathlib import Path
import config

# Import všech sekcí nastavení
from .settings_company import CompanySettingsWidget
from .settings_users import UsersSettingsWidget
from .settings_permissions import PermissionsSettingsWidget
from .settings_orders import OrdersSettingsWidget
from .settings_invoicing import InvoicingSettingsWidget
from .settings_templates import TemplatesSettingsWidget
from .settings_email import EmailSettingsWidget
from .settings_backup import BackupSettingsWidget
from .settings_database import DatabaseSettingsWidget
from .settings_appearance import AppearanceSettingsWidget
from .settings_integrations import IntegrationsSettingsWidget
from .settings_license import LicenseSettingsWidget


class SettingsModule(QWidget):
    """Hlavní modul nastavení"""

    def __init__(self):
        super().__init__()
        self.current_section = None
        self.sections = {}
        self.nav_buttons = {}
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Levý navigační panel
        self.create_nav_panel(main_layout)

        # Pravý obsahový panel
        self.create_content_panel(main_layout)

        self.set_styles()

    def create_nav_panel(self, parent_layout):
        """Vytvoření levého navigačního panelu"""
        nav_widget = QWidget()
        nav_widget.setObjectName("settingsNavPanel")
        nav_widget.setFixedWidth(280)

        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        # Hlavička
        header = QFrame()
        header.setObjectName("settingsNavHeader")
        header.setFixedHeight(60)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(15, 10, 15, 10)

        title = QLabel("⚙️ Nastavení")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(title)
        nav_layout.addWidget(header)

        # Vyhledávání
        search_frame = QFrame()
        search_frame.setObjectName("searchFrame")
        search_layout = QVBoxLayout(search_frame)
        search_layout.setContentsMargins(10, 10, 10, 10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Hledat v nastavení...")
        self.search_input.textChanged.connect(self.filter_sections)
        search_layout.addWidget(self.search_input)

        nav_layout.addWidget(search_frame)

        # Scroll area pro menu
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setObjectName("navScrollArea")

        scroll_content = QWidget()
        self.nav_buttons_layout = QVBoxLayout(scroll_content)
        self.nav_buttons_layout.setContentsMargins(5, 5, 5, 5)
        self.nav_buttons_layout.setSpacing(2)

        # Definice sekcí
        self.section_definitions = [
            {"id": "company", "name": "🏢 Firemní údaje", "keywords": ["firma", "ico", "dic", "adresa", "kontakt", "logo"]},
            {"id": "users", "name": "👥 Uživatelé", "keywords": ["uživatel", "účet", "heslo", "přihlášení", "login"]},
            {"id": "permissions", "name": "🔐 Oprávnění a role", "keywords": ["práva", "role", "přístup", "oprávnění", "permission"]},
            {"id": "orders", "name": "📋 Zakázky", "keywords": ["zakázka", "stav", "číslování", "workflow", "objednávka"]},
            {"id": "invoicing", "name": "🧾 Fakturace", "keywords": ["faktura", "dph", "splatnost", "platba", "daň"]},
            {"id": "templates", "name": "📄 Šablony dokumentů", "keywords": ["šablona", "dokument", "tisk", "pdf", "report"]},
            {"id": "email", "name": "📧 Email a notifikace", "keywords": ["email", "smtp", "notifikace", "upozornění", "mail"]},
            {"id": "backup", "name": "💾 Zálohování", "keywords": ["záloha", "backup", "obnovení", "archiv", "restore"]},
            {"id": "database", "name": "🗄️ Databáze", "keywords": ["databáze", "sql", "údržba", "optimalizace", "sqlite"]},
            {"id": "appearance", "name": "🎨 Vzhled", "keywords": ["vzhled", "téma", "barva", "font", "design"]},
            {"id": "integrations", "name": "🔗 Integrace", "keywords": ["api", "integrace", "propojení", "import", "export"]},
            {"id": "license", "name": "📜 Licence", "keywords": ["licence", "aktivace", "verze", "aktualizace", "update"]},
        ]

        # Vytvoření tlačítek
        for section in self.section_definitions:
            btn = QPushButton(section["name"])
            btn.setObjectName("settingsNavButton")
            btn.setFixedHeight(45)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, s=section["id"]: self.switch_section(s))
            self.nav_buttons[section["id"]] = btn
            self.nav_buttons_layout.addWidget(btn)

        self.nav_buttons_layout.addStretch()

        scroll.setWidget(scroll_content)
        nav_layout.addWidget(scroll)

        # Spodní tlačítka
        bottom_frame = QFrame()
        bottom_frame.setObjectName("settingsBottomFrame")
        bottom_layout = QVBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(10, 10, 10, 10)
        bottom_layout.setSpacing(5)

        help_btn = QPushButton("📖 Nápověda")
        help_btn.setObjectName("settingsActionButton")
        help_btn.clicked.connect(self.show_help)
        help_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        reset_btn = QPushButton("🔄 Obnovit výchozí")
        reset_btn.setObjectName("settingsActionButton")
        reset_btn.clicked.connect(self.reset_to_defaults)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        export_btn = QPushButton("📤 Export nastavení")
        export_btn.setObjectName("settingsActionButton")
        export_btn.clicked.connect(self.export_settings)
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        import_btn = QPushButton("📥 Import nastavení")
        import_btn.setObjectName("settingsActionButton")
        import_btn.clicked.connect(self.import_settings)
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        bottom_layout.addWidget(help_btn)
        bottom_layout.addWidget(reset_btn)
        bottom_layout.addWidget(export_btn)
        bottom_layout.addWidget(import_btn)

        nav_layout.addWidget(bottom_frame)

        parent_layout.addWidget(nav_widget)

    def create_content_panel(self, parent_layout):
        """Vytvoření pravého obsahového panelu"""
        content_widget = QWidget()
        content_widget.setObjectName("settingsContentPanel")

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Horní lišta
        top_bar = QFrame()
        top_bar.setObjectName("settingsTopBar")
        top_bar.setFixedHeight(60)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(20, 10, 20, 10)

        self.section_title = QLabel("Vyberte sekci")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.section_title.setFont(title_font)

        top_bar_layout.addWidget(self.section_title)
        top_bar_layout.addStretch()

        # Tlačítko uložit
        self.save_btn = QPushButton("💾 Uložit změny")
        self.save_btn.setObjectName("saveButton")
        self.save_btn.clicked.connect(self.save_current_settings)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setEnabled(False)

        top_bar_layout.addWidget(self.save_btn)

        content_layout.addWidget(top_bar)

        # Stack pro sekce
        self.section_stack = QStackedWidget()
        self.section_stack.setObjectName("sectionStack")

        # Výchozí placeholder
        placeholder = self.create_placeholder_widget()
        self.section_stack.addWidget(placeholder)
        self.sections["placeholder"] = placeholder

        # Registrace všech sekcí
        self.register_sections()

        content_layout.addWidget(self.section_stack)

        parent_layout.addWidget(content_widget)

    def register_sections(self):
        """Registrace všech sekcí nastavení"""
        # Mapování ID sekce na widget třídu
        section_widgets = {
            "company": CompanySettingsWidget,
            "users": UsersSettingsWidget,
            "permissions": PermissionsSettingsWidget,
            "orders": OrdersSettingsWidget,
            "invoicing": InvoicingSettingsWidget,
            "templates": TemplatesSettingsWidget,
            "email": EmailSettingsWidget,
            "backup": BackupSettingsWidget,
            "database": DatabaseSettingsWidget,
            "appearance": AppearanceSettingsWidget,
            "integrations": IntegrationsSettingsWidget,
            "license": LicenseSettingsWidget,
        }

        # Vytvoření instancí widgetů
        for section_id, widget_class in section_widgets.items():
            try:
                widget = widget_class()
                self.sections[section_id] = widget
                self.section_stack.addWidget(widget)
            except Exception as e:
                print(f"Chyba při vytváření sekce {section_id}: {e}")
                # Vytvoření fallback placeholder
                fallback = self.create_error_placeholder(section_id, str(e))
                self.sections[section_id] = fallback
                self.section_stack.addWidget(fallback)

    def create_placeholder_widget(self):
        """Vytvoření výchozího placeholder widgetu"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel("⚙️")
        icon_label.setStyleSheet("font-size: 64px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel("Vyberte sekci z menu vlevo")
        text_label.setStyleSheet("font-size: 18px; color: #7f8c8d;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(icon_label)
        layout.addWidget(text_label)

        return widget

    def create_error_placeholder(self, section_id, error_msg):
        """Vytvoření placeholder widgetu pro chybu"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel(f"Sekce '{section_id}' se nepodařilo načíst")
        text_label.setStyleSheet("font-size: 16px; color: #e74c3c; font-weight: bold;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        error_label = QLabel(f"Chyba: {error_msg}")
        error_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setWordWrap(True)

        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addWidget(error_label)

        return widget

    def switch_section(self, section_id):
        """Přepnutí na vybranou sekci"""
        if section_id in self.sections:
            # Aktualizace aktivního tlačítka
            for btn_id, btn in self.nav_buttons.items():
                btn.setProperty("active", btn_id == section_id)
                btn.style().unpolish(btn)
                btn.style().polish(btn)

            # Přepnutí stacku
            self.section_stack.setCurrentWidget(self.sections[section_id])
            self.current_section = section_id

            # Aktualizace titulku
            section_name = next(
                (s["name"] for s in self.section_definitions if s["id"] == section_id),
                "Nastavení"
            )
            self.section_title.setText(section_name)

            # Aktivace tlačítka uložit
            self.save_btn.setEnabled(True)

            # Refresh sekce pokud má metodu
            if hasattr(self.sections[section_id], 'refresh'):
                try:
                    self.sections[section_id].refresh()
                except Exception as e:
                    print(f"Chyba při refresh sekce {section_id}: {e}")

    def filter_sections(self, text):
        """Filtrování sekcí podle vyhledávání"""
        search_text = text.lower().strip()

        for section in self.section_definitions:
            btn = self.nav_buttons.get(section["id"])
            if btn:
                if not search_text:
                    btn.setVisible(True)
                else:
                    # Hledání v názvu nebo klíčových slovech
                    matches = (
                        search_text in section["name"].lower() or
                        any(search_text in kw for kw in section["keywords"])
                    )
                    btn.setVisible(matches)

    def save_current_settings(self):
        """Uložení aktuálního nastavení"""
        if self.current_section and self.current_section in self.sections:
            section_widget = self.sections[self.current_section]
            if hasattr(section_widget, 'save_settings'):
                try:
                    section_widget.save_settings()
                    QMessageBox.information(
                        self,
                        "Uloženo",
                        "Nastavení bylo úspěšně uloženo."
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Chyba",
                        f"Nepodařilo se uložit nastavení:\n{str(e)}"
                    )
            else:
                QMessageBox.information(
                    self,
                    "Info",
                    "Tato sekce zatím nepodporuje ukládání."
                )

    def show_help(self):
        """Zobrazení nápovědy"""
        QMessageBox.information(
            self,
            "Nápověda",
            "📖 Nápověda k nastavení\n\n"
            "• Vyberte sekci z menu vlevo\n"
            "• Upravte potřebná nastavení\n"
            "• Klikněte na 'Uložit změny'\n\n"
            "Jednotlivé sekce:\n"
            "🏢 Firemní údaje - IČO, DIČ, adresa, logo\n"
            "👥 Uživatelé - správa uživatelských účtů\n"
            "🔐 Oprávnění - role a přístupová práva\n"
            "📋 Zakázky - nastavení workflow zakázek\n"
            "🧾 Fakturace - DPH, splatnosti, šablony\n"
            "📄 Šablony - dokumenty a tiskové sestavy\n"
            "📧 Email - SMTP a notifikace\n"
            "💾 Zálohování - automatické zálohy\n"
            "🗄️ Databáze - údržba a optimalizace\n"
            "🎨 Vzhled - téma a barvy aplikace\n"
            "🔗 Integrace - API a externí služby\n"
            "📜 Licence - informace o licenci"
        )

    def reset_to_defaults(self):
        """Obnovení výchozího nastavení"""
        reply = QMessageBox.question(
            self,
            "Obnovit výchozí nastavení",
            "Opravdu chcete obnovit výchozí nastavení?\n\n"
            "Tato akce nelze vrátit zpět!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.perform_reset()
                QMessageBox.information(
                    self,
                    "Hotovo",
                    "Výchozí nastavení bylo obnoveno.\n"
                    "Některé změny se projeví až po restartu aplikace."
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Chyba",
                    f"Nepodařilo se obnovit nastavení:\n{str(e)}"
                )

    def perform_reset(self):
        """Provede reset nastavení"""
        # Reset všech sekcí
        for section_id, section_widget in self.sections.items():
            if hasattr(section_widget, 'reset_to_defaults'):
                try:
                    section_widget.reset_to_defaults()
                except Exception as e:
                    print(f"Chyba při reset sekce {section_id}: {e}")

    def export_settings(self):
        """Export nastavení do souboru"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export nastavení",
            str(config.EXPORTS_DIR / "nastaveni_export.json"),
            "JSON soubory (*.json)"
        )

        if file_path:
            try:
                settings_data = self.gather_all_settings()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(settings_data, f, ensure_ascii=False, indent=2)

                QMessageBox.information(
                    self,
                    "Export dokončen",
                    f"Nastavení bylo exportováno do:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Chyba exportu",
                    f"Nepodařilo se exportovat nastavení:\n{str(e)}"
                )

    def import_settings(self):
        """Import nastavení ze souboru"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import nastavení",
            str(config.EXPORTS_DIR),
            "JSON soubory (*.json)"
        )

        if file_path:
            reply = QMessageBox.question(
                self,
                "Import nastavení",
                "Import přepíše aktuální nastavení.\n\n"
                "Chcete pokračovat?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        settings_data = json.load(f)

                    self.apply_imported_settings(settings_data)

                    QMessageBox.information(
                        self,
                        "Import dokončen",
                        "Nastavení bylo úspěšně importováno.\n"
                        "Některé změny se projeví až po restartu aplikace."
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Chyba importu",
                        f"Nepodařilo se importovat nastavení:\n{str(e)}"
                    )

    def gather_all_settings(self):
        """Shromáždění všech nastavení pro export"""
        settings = {
            "app_version": config.APP_VERSION,
            "export_date": str(Path(__file__).stat().st_mtime),
            "sections": {}
        }

        for section_id, section_widget in self.sections.items():
            if section_id != "placeholder" and hasattr(section_widget, 'get_settings'):
                try:
                    settings["sections"][section_id] = section_widget.get_settings()
                except Exception as e:
                    print(f"Chyba při získávání nastavení sekce {section_id}: {e}")

        return settings

    def apply_imported_settings(self, settings_data):
        """Aplikování importovaných nastavení"""
        if "sections" in settings_data:
            for section_id, section_settings in settings_data["sections"].items():
                if section_id in self.sections:
                    section_widget = self.sections[section_id]
                    if hasattr(section_widget, 'set_settings'):
                        try:
                            section_widget.set_settings(section_settings)
                        except Exception as e:
                            print(f"Chyba při aplikování nastavení sekce {section_id}: {e}")

    def refresh(self):
        """Obnovení modulu"""
        # Reset vyhledávání
        self.search_input.clear()

        # Zobrazení výchozího placeholder
        if "placeholder" in self.sections:
            self.section_stack.setCurrentWidget(self.sections["placeholder"])

        self.section_title.setText("Vyberte sekci")
        self.save_btn.setEnabled(False)
        self.current_section = None

        # Reset aktivních tlačítek
        for btn in self.nav_buttons.values():
            btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet(f"""
            #settingsNavPanel {{
                background-color: #ecf0f1;
                border-right: 2px solid #bdc3c7;
            }}

            #settingsNavHeader {{
                background-color: {config.COLOR_PRIMARY};
                color: white;
            }}

            #settingsNavHeader QLabel {{
                color: white;
            }}

            #searchFrame {{
                background-color: white;
                border-bottom: 1px solid #bdc3c7;
            }}

            #searchFrame QLineEdit {{
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 13px;
            }}

            #searchFrame QLineEdit:focus {{
                border: 2px solid {config.COLOR_SECONDARY};
            }}

            #navScrollArea {{
                border: none;
                background-color: transparent;
            }}

            #settingsNavButton {{
                background-color: transparent;
                border: none;
                text-align: left;
                padding: 12px 15px;
                font-size: 13px;
                color: #2c3e50;
                border-radius: 4px;
                margin: 2px 5px;
            }}

            #settingsNavButton:hover {{
                background-color: #d5dbdb;
            }}

            #settingsNavButton[active="true"] {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                font-weight: bold;
            }}

            #settingsBottomFrame {{
                background-color: #d5dbdb;
                border-top: 1px solid #bdc3c7;
            }}

            #settingsActionButton {{
                background-color: white;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
            }}

            #settingsActionButton:hover {{
                background-color: #ecf0f1;
                border-color: {config.COLOR_SECONDARY};
            }}

            #settingsContentPanel {{
                background-color: #f5f5f5;
            }}

            #settingsTopBar {{
                background-color: white;
                border-bottom: 2px solid #e0e0e0;
            }}

            #saveButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }}

            #saveButton:hover {{
                background-color: #229954;
            }}

            #saveButton:disabled {{
                background-color: #95a5a6;
            }}

            #sectionStack {{
                background-color: #f5f5f5;
            }}
        """)
