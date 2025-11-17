# -*- coding: utf-8 -*-
"""
Správa šablon dokumentů
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QTextEdit, QSplitter, QGroupBox,
    QMessageBox, QFileDialog, QDialog, QFormLayout, QLineEdit,
    QComboBox, QScrollArea, QFrame, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from database_manager import db
import config
import json
from pathlib import Path


class TemplatesSettingsWidget(QWidget):
    """Widget pro správu šablon dokumentů"""

    def __init__(self):
        super().__init__()
        self.current_template = None
        self.templates_data = {}
        self.init_ui()
        self.load_templates()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Horní panel
        top_panel = QHBoxLayout()

        import_btn = QPushButton("📥 Importovat šablonu")
        import_btn.clicked.connect(self.import_template)
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        export_btn = QPushButton("📤 Exportovat šablonu")
        export_btn.clicked.connect(self.export_template)
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        reset_btn = QPushButton("🔄 Obnovit výchozí")
        reset_btn.clicked.connect(self.reset_to_default)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        top_panel.addWidget(import_btn)
        top_panel.addWidget(export_btn)
        top_panel.addWidget(reset_btn)
        top_panel.addStretch()

        layout.addLayout(top_panel)

        # Hlavní splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Levý panel - seznam šablon
        left_panel = self.create_templates_list()
        splitter.addWidget(left_panel)

        # Pravý panel - editor
        right_panel = self.create_template_editor()
        splitter.addWidget(right_panel)

        splitter.setSizes([300, 700])

        layout.addWidget(splitter)

        self.set_styles()

    def create_templates_list(self):
        """Vytvoření seznamu šablon"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        label = QLabel("📋 Dostupné šablony:")
        label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(label)

        self.templates_list = QListWidget()
        self.templates_list.setAlternatingRowColors(True)
        self.templates_list.currentItemChanged.connect(self.on_template_selected)

        layout.addWidget(self.templates_list)

        # Tlačítka
        buttons_layout = QHBoxLayout()

        duplicate_btn = QPushButton("📋 Duplikovat")
        duplicate_btn.clicked.connect(self.duplicate_template)
        duplicate_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        buttons_layout.addWidget(duplicate_btn)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        return widget

    def create_template_editor(self):
        """Vytvoření editoru šablony"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Záložky
        tabs = QTabWidget()

        # Záložka: Editor
        tabs.addTab(self.create_editor_tab(), "✏️ Editor")

        # Záložka: Proměnné
        tabs.addTab(self.create_variables_tab(), "🔧 Proměnné")

        # Záložka: Náhled
        tabs.addTab(self.create_preview_tab(), "👁️ Náhled")

        layout.addWidget(tabs)

        # Tlačítka pro uložení
        buttons_layout = QHBoxLayout()

        save_btn = QPushButton("💾 Uložit šablonu")
        save_btn.clicked.connect(self.save_template)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setObjectName("saveButton")

        preview_btn = QPushButton("🖨️ Tisk testovací")
        preview_btn.clicked.connect(self.print_test)
        preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        buttons_layout.addStretch()
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(preview_btn)

        layout.addLayout(buttons_layout)

        return widget

    def create_editor_tab(self):
        """Záložka editoru"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Název šablony
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Název šablony:"))
        self.template_name = QLineEdit()
        self.template_name.setReadOnly(True)
        self.template_name.setStyleSheet("background-color: #ecf0f1;")
        name_layout.addWidget(self.template_name)
        layout.addLayout(name_layout)

        # Předmět (pro emaily)
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("Předmět:"))
        self.template_subject = QLineEdit()
        self.template_subject.setPlaceholderText("Předmět emailu (pouze pro emailové šablony)")
        subject_layout.addWidget(self.template_subject)
        layout.addLayout(subject_layout)

        # Hlavní editor
        editor_label = QLabel("Obsah šablony:")
        editor_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(editor_label)

        self.template_editor = QTextEdit()
        self.template_editor.setPlaceholderText("Zde upravte obsah šablony...\n\nPoužijte proměnné ve formátu {{nazev_promenne}}")
        self.template_editor.setMinimumHeight(300)

        layout.addWidget(self.template_editor)

        # Formátovací tlačítka
        format_layout = QHBoxLayout()

        bold_btn = QPushButton("B")
        bold_btn.setStyleSheet("font-weight: bold;")
        bold_btn.setFixedWidth(30)
        bold_btn.clicked.connect(lambda: self.insert_formatting("**", "**"))

        italic_btn = QPushButton("I")
        italic_btn.setStyleSheet("font-style: italic;")
        italic_btn.setFixedWidth(30)
        italic_btn.clicked.connect(lambda: self.insert_formatting("*", "*"))

        underline_btn = QPushButton("U")
        underline_btn.setStyleSheet("text-decoration: underline;")
        underline_btn.setFixedWidth(30)
        underline_btn.clicked.connect(lambda: self.insert_formatting("<u>", "</u>"))

        table_btn = QPushButton("📊 Tabulka")
        table_btn.clicked.connect(self.insert_table)

        format_layout.addWidget(bold_btn)
        format_layout.addWidget(italic_btn)
        format_layout.addWidget(underline_btn)
        format_layout.addWidget(table_btn)
        format_layout.addStretch()

        layout.addLayout(format_layout)

        return widget

    def create_variables_tab(self):
        """Záložka proměnných"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)

        # Firemní údaje
        content_layout.addWidget(self.create_variables_group("🏢 Firemní údaje", [
            ("{{firma_nazev}}", "Název firmy"),
            ("{{firma_ico}}", "IČO"),
            ("{{firma_dic}}", "DIČ"),
            ("{{firma_adresa}}", "Adresa firmy"),
            ("{{firma_telefon}}", "Telefon firmy"),
            ("{{firma_email}}", "Email firmy"),
            ("{{firma_ucet}}", "Bankovní účet"),
            ("{{firma_iban}}", "IBAN"),
            ("{{firma_logo}}", "Logo firmy (obrázek)")
        ]))

        # Zákazník
        content_layout.addWidget(self.create_variables_group("👤 Zákazník", [
            ("{{zakaznik_jmeno}}", "Jméno zákazníka"),
            ("{{zakaznik_prijmeni}}", "Příjmení zákazníka"),
            ("{{zakaznik_adresa}}", "Adresa zákazníka"),
            ("{{zakaznik_telefon}}", "Telefon zákazníka"),
            ("{{zakaznik_email}}", "Email zákazníka"),
            ("{{zakaznik_ico}}", "IČO zákazníka"),
            ("{{zakaznik_dic}}", "DIČ zákazníka")
        ]))

        # Vozidlo
        content_layout.addWidget(self.create_variables_group("🏍️ Vozidlo", [
            ("{{vozidlo_spz}}", "SPZ vozidla"),
            ("{{vozidlo_znacka}}", "Značka vozidla"),
            ("{{vozidlo_model}}", "Model vozidla"),
            ("{{vozidlo_vin}}", "VIN kód"),
            ("{{vozidlo_rok}}", "Rok výroby"),
            ("{{vozidlo_barva}}", "Barva vozidla")
        ]))

        # Zakázka
        content_layout.addWidget(self.create_variables_group("📋 Zakázka", [
            ("{{zakazka_cislo}}", "Číslo zakázky"),
            ("{{zakazka_datum}}", "Datum zakázky"),
            ("{{zakazka_popis}}", "Popis zakázky"),
            ("{{zakazka_polozky}}", "Seznam položek (tabulka)"),
            ("{{zakazka_cena_bez_dph}}", "Cena bez DPH"),
            ("{{zakazka_dph}}", "DPH"),
            ("{{zakazka_cena_s_dph}}", "Cena s DPH"),
            ("{{zakazka_stav}}", "Stav zakázky"),
            ("{{zakazka_mechanik}}", "Přiřazený mechanik")
        ]))

        # Faktura
        content_layout.addWidget(self.create_variables_group("🧾 Faktura", [
            ("{{faktura_cislo}}", "Číslo faktury"),
            ("{{faktura_datum_vystaveni}}", "Datum vystavení"),
            ("{{faktura_datum_splatnosti}}", "Datum splatnosti"),
            ("{{faktura_datum_zdp}}", "Datum zdan. plnění"),
            ("{{faktura_vs}}", "Variabilní symbol"),
            ("{{faktura_ks}}", "Konstantní symbol"),
            ("{{faktura_forma_uhrady}}", "Forma úhrady")
        ]))

        # Systémové
        content_layout.addWidget(self.create_variables_group("⚙️ Systémové", [
            ("{{dnes}}", "Dnešní datum"),
            ("{{cas}}", "Aktuální čas"),
            ("{{rok}}", "Aktuální rok"),
            ("{{uzivatel}}", "Přihlášený uživatel")
        ]))

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        return widget

    def create_variables_group(self, title, variables):
        """Vytvoření skupiny proměnných"""
        group = QGroupBox(title)
        group.setObjectName("variablesGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(5)

        for var, desc in variables:
            var_layout = QHBoxLayout()

            var_label = QLabel(var)
            var_label.setStyleSheet("""
                font-family: monospace;
                background-color: #f8f9fa;
                padding: 4px 8px;
                border-radius: 3px;
                color: #e74c3c;
            """)
            var_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

            desc_label = QLabel(f"- {desc}")
            desc_label.setStyleSheet("color: #7f8c8d;")

            insert_btn = QPushButton("➕")
            insert_btn.setFixedSize(25, 25)
            insert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            insert_btn.clicked.connect(lambda checked, v=var: self.insert_variable(v))
            insert_btn.setToolTip("Vložit do editoru")

            var_layout.addWidget(var_label)
            var_layout.addWidget(desc_label)
            var_layout.addStretch()
            var_layout.addWidget(insert_btn)

            layout.addLayout(var_layout)

        return group

    def create_preview_tab(self):
        """Záložka náhledu"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        info_label = QLabel("👁️ Náhled šablony s ukázkovými daty:")
        info_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(info_label)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("background-color: white;")

        layout.addWidget(self.preview_text)

        refresh_btn = QPushButton("🔄 Obnovit náhled")
        refresh_btn.clicked.connect(self.update_preview)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(refresh_btn)

        return widget

    def load_templates(self):
        """Načtení šablon"""
        default_templates = [
            {"id": "order_sheet", "name": "📋 Zakázkový list", "type": "document"},
            {"id": "proforma", "name": "📊 Proforma", "type": "document"},
            {"id": "invoice", "name": "🧾 Faktura", "type": "document"},
            {"id": "offer", "name": "📝 Nabídka", "type": "document"},
            {"id": "service_contract", "name": "📄 Smlouva servisní", "type": "document"},
            {"id": "handover_protocol", "name": "📋 Předávací protokol", "type": "document"},
            {"id": "email_order_confirm", "name": "📧 Email - potvrzení zakázky", "type": "email"},
            {"id": "email_reminder", "name": "📧 Email - upomínka", "type": "email"},
            {"id": "email_complete", "name": "📧 Email - dokončení", "type": "email"},
            {"id": "sms_confirm", "name": "📱 SMS - potvrzení", "type": "sms"},
            {"id": "sms_ready", "name": "📱 SMS - vozidlo připraveno", "type": "sms"}
        ]

        self.templates_list.clear()

        for template in default_templates:
            item = QListWidgetItem(template["name"])
            item.setData(Qt.ItemDataRole.UserRole, template["id"])
            self.templates_list.addItem(item)

            # Výchozí obsah šablony
            if template["id"] not in self.templates_data:
                self.templates_data[template["id"]] = {
                    "name": template["name"],
                    "type": template["type"],
                    "subject": "",
                    "content": self.get_default_template_content(template["id"])
                }

    def get_default_template_content(self, template_id):
        """Získání výchozího obsahu šablony"""
        templates = {
            "order_sheet": """ZAKÁZKOVÝ LIST č. {{zakazka_cislo}}

Datum: {{zakazka_datum}}
Zákazník: {{zakaznik_jmeno}} {{zakaznik_prijmeni}}
Telefon: {{zakaznik_telefon}}

VOZIDLO:
SPZ: {{vozidlo_spz}}
Značka: {{vozidlo_znacka}} {{vozidlo_model}}
VIN: {{vozidlo_vin}}

POŽADOVANÉ PRÁCE:
{{zakazka_popis}}

POLOŽKY:
{{zakazka_polozky}}

CELKOVÁ CENA: {{zakazka_cena_s_dph}} Kč

Podpis zákazníka: _________________
Podpis servisu: _________________
""",
            "email_order_confirm": """Dobrý den,

potvrzujeme přijetí Vaší zakázky č. {{zakazka_cislo}}.

Vozidlo: {{vozidlo_znacka}} {{vozidlo_model}} ({{vozidlo_spz}})
Požadované práce: {{zakazka_popis}}

O průběhu zakázky Vás budeme informovat.

S pozdravem,
{{firma_nazev}}
Tel: {{firma_telefon}}
Email: {{firma_email}}
""",
            "email_complete": """Dobrý den,

Vaše zakázka č. {{zakazka_cislo}} byla dokončena.

Vozidlo {{vozidlo_znacka}} {{vozidlo_model}} ({{vozidlo_spz}}) je připraveno k vyzvednutí.

Celková cena: {{zakazka_cena_s_dph}} Kč

Otevírací doba: Po-Pá 7:00-16:00

S pozdravem,
{{firma_nazev}}
""",
            "sms_ready": "Dobry den, Vase vozidlo {{vozidlo_spz}} je pripraveno k vyzvednuti. {{firma_nazev}}"
        }

        return templates.get(template_id, f"Šablona pro {template_id}\n\nVložte obsah šablony...")

    def on_template_selected(self, current, previous):
        """Při výběru šablony"""
        if not current:
            return

        template_id = current.data(Qt.ItemDataRole.UserRole)
        self.current_template = template_id

        if template_id in self.templates_data:
            data = self.templates_data[template_id]
            self.template_name.setText(data["name"])
            self.template_subject.setText(data.get("subject", ""))
            self.template_editor.setPlainText(data.get("content", ""))
            self.update_preview()

    def insert_variable(self, variable):
        """Vložení proměnné do editoru"""
        cursor = self.template_editor.textCursor()
        cursor.insertText(variable)
        self.template_editor.setFocus()

    def insert_formatting(self, prefix, suffix):
        """Vložení formátování"""
        cursor = self.template_editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(f"{prefix}{text}{suffix}")
        else:
            cursor.insertText(f"{prefix}{suffix}")
        self.template_editor.setFocus()

    def insert_table(self):
        """Vložení tabulky"""
        table_template = """
| Položka | Množství | Cena |
|---------|----------|------|
|         |          |      |
"""
        cursor = self.template_editor.textCursor()
        cursor.insertText(table_template)
        self.template_editor.setFocus()

    def update_preview(self):
        """Aktualizace náhledu"""
        content = self.template_editor.toPlainText()

        # Ukázková data
        sample_data = {
            "{{firma_nazev}}": "Motoservis ABC s.r.o.",
            "{{firma_ico}}": "12345678",
            "{{firma_dic}}": "CZ12345678",
            "{{firma_adresa}}": "Hlavní 123, 602 00 Brno",
            "{{firma_telefon}}": "+420 123 456 789",
            "{{firma_email}}": "info@motoservis.cz",
            "{{firma_ucet}}": "123456789/0100",
            "{{zakaznik_jmeno}}": "Jan",
            "{{zakaznik_prijmeni}}": "Novák",
            "{{zakaznik_adresa}}": "Vedlejší 456, 615 00 Brno",
            "{{zakaznik_telefon}}": "+420 987 654 321",
            "{{zakaznik_email}}": "jan.novak@email.cz",
            "{{vozidlo_spz}}": "1B2 3456",
            "{{vozidlo_znacka}}": "Honda",
            "{{vozidlo_model}}": "CB500F",
            "{{vozidlo_vin}}": "JH2PC4507DM123456",
            "{{zakazka_cislo}}": "ZAK-2025-0042",
            "{{zakazka_datum}}": "15.11.2025",
            "{{zakazka_popis}}": "Pravidelný servis - výměna oleje a filtru",
            "{{zakazka_cena_s_dph}}": "2 450",
            "{{dnes}}": "15.11.2025",
            "{{cas}}": "14:30",
            "{{rok}}": "2025"
        }

        for key, value in sample_data.items():
            content = content.replace(key, value)

        self.preview_text.setPlainText(content)

    def save_template(self):
        """Uložení šablony"""
        if not self.current_template:
            QMessageBox.warning(self, "Upozornění", "Vyberte šablonu pro uložení.")
            return

        self.templates_data[self.current_template]["subject"] = self.template_subject.text()
        self.templates_data[self.current_template]["content"] = self.template_editor.toPlainText()

        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO app_settings (key, value)
                VALUES (?, ?)
            """, (
                f"template_{self.current_template}",
                json.dumps(self.templates_data[self.current_template], ensure_ascii=False)
            ))

            conn.commit()

            QMessageBox.information(self, "Uloženo", "Šablona byla uložena.")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit šablonu:\n{str(e)}")

    def duplicate_template(self):
        """Duplikace šablony"""
        if not self.current_template:
            QMessageBox.warning(self, "Upozornění", "Vyberte šablonu pro duplikaci.")
            return

        QMessageBox.information(
            self,
            "Duplikace",
            "Funkce duplikace bude implementována v další verzi."
        )

    def import_template(self):
        """Import šablony"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importovat šablonu",
            str(config.EXPORTS_DIR),
            "JSON soubory (*.json);;Textové soubory (*.txt)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    if file_path.endswith('.json'):
                        data = json.load(f)
                    else:
                        data = {"content": f.read()}

                if self.current_template and "content" in data:
                    self.template_editor.setPlainText(data["content"])
                    if "subject" in data:
                        self.template_subject.setText(data["subject"])

                    QMessageBox.information(self, "Hotovo", "Šablona byla importována.")

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se importovat šablonu:\n{str(e)}")

    def export_template(self):
        """Export šablony"""
        if not self.current_template:
            QMessageBox.warning(self, "Upozornění", "Vyberte šablonu pro export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportovat šablonu",
            str(config.EXPORTS_DIR / f"{self.current_template}.json"),
            "JSON soubory (*.json)"
        )

        if file_path:
            try:
                data = {
                    "id": self.current_template,
                    "name": self.template_name.text(),
                    "subject": self.template_subject.text(),
                    "content": self.template_editor.toPlainText()
                }

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                QMessageBox.information(self, "Hotovo", f"Šablona byla exportována do:\n{file_path}")

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se exportovat šablonu:\n{str(e)}")

    def reset_to_default(self):
        """Obnovení výchozí šablony"""
        if not self.current_template:
            QMessageBox.warning(self, "Upozornění", "Vyberte šablonu pro obnovení.")
            return

        reply = QMessageBox.question(
            self,
            "Obnovit výchozí",
            "Opravdu chcete obnovit výchozí obsah této šablony?\n\n"
            "Aktuální obsah bude ztracen!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            default_content = self.get_default_template_content(self.current_template)
            self.template_editor.setPlainText(default_content)
            self.update_preview()

    def print_test(self):
        """Testovací tisk"""
        QMessageBox.information(
            self,
            "Testovací tisk",
            "Funkce testovacího tisku bude implementována v další verzi.\n\n"
            "Zatím můžete použít 'Náhled' pro kontrolu šablony."
        )

    def save_settings(self):
        """Uložení všech nastavení"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            for template_id, data in self.templates_data.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO app_settings (key, value)
                    VALUES (?, ?)
                """, (
                    f"template_{template_id}",
                    json.dumps(data, ensure_ascii=False)
                ))

            conn.commit()

        except Exception as e:
            raise Exception(f"Chyba při ukládání šablon: {str(e)}")

    def get_settings(self):
        """Získání nastavení"""
        return self.templates_data

    def set_settings(self, settings):
        """Nastavení hodnot"""
        if isinstance(settings, dict):
            self.templates_data.update(settings)

    def refresh(self):
        """Obnovení"""
        self.load_templates()

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet(f"""
            QListWidget {{
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }}

            QListWidget::item {{
                padding: 10px;
                border-bottom: 1px solid #ecf0f1;
            }}

            QListWidget::item:selected {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
            }}

            QListWidget::item:hover {{
                background-color: #ecf0f1;
            }}

            QTextEdit {{
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 10px;
                font-family: monospace;
                font-size: 12px;
            }}

            QTextEdit:focus {{
                border: 2px solid {config.COLOR_SECONDARY};
            }}

            QLineEdit {{
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
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

            #saveButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                border: none;
                font-weight: bold;
            }}

            #saveButton:hover {{
                background-color: #229954;
            }}

            #variablesGroup {{
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin-top: 8px;
            }}

            QTabWidget::pane {{
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }}

            QTabBar::tab {{
                background-color: #ecf0f1;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}

            QTabBar::tab:selected {{
                background-color: white;
                font-weight: bold;
            }}

            QGroupBox {{
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }}
        """)
