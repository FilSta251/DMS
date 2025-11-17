# -*- coding: utf-8 -*-
"""
Modul Administrativa - Šablony faktur a dokumentů (PRODUKČNÍ VERZE)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QFrame,
                             QComboBox, QLineEdit, QDateEdit, QHeaderView,
                             QMessageBox, QDialog, QFormLayout, QTextEdit,
                             QSpinBox, QDoubleSpinBox, QFileDialog, QCheckBox,
                             QGroupBox, QTabWidget, QScrollArea, QProgressBar,
                             QSplitter, QListWidget, QListWidgetItem, QColorDialog,
                             QFontDialog, QPlainTextEdit)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon, QTextDocument, QTextCursor
from datetime import datetime, timedelta, date
from pathlib import Path
import json
import config
from database_manager import db


class TemplatesWidget(QWidget):
    """Widget pro správu šablon"""

    def __init__(self):
        super().__init__()
        self.current_template = None
        self.init_ui()
        self.load_templates()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Hlavička
        header_label = QLabel("🎨 Šablony faktur a dokumentů")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)

        # Hlavní splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Levý panel - seznam šablon
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # Pravý panel - editor
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

    def create_left_panel(self):
        """Levý panel se seznamem šablon"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tlačítka akcí
        buttons_layout = QHBoxLayout()

        new_btn = QPushButton("➕ Nová šablona")
        new_btn.clicked.connect(self.new_template)
        new_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 15px;")
        buttons_layout.addWidget(new_btn)

        import_btn = QPushButton("📥 Import")
        import_btn.clicked.connect(self.import_template)
        buttons_layout.addWidget(import_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # Filtry
        filters_layout = QHBoxLayout()

        type_label = QLabel("Typ:")
        filters_layout.addWidget(type_label)

        self.type_filter = QComboBox()
        self.type_filter.addItems([
            "Všechny typy",
            "Faktury",
            "Smlouvy",
            "Protokoly",
            "Upomínky",
            "Ostatní"
        ])
        self.type_filter.currentTextChanged.connect(self.filter_templates)
        filters_layout.addWidget(self.type_filter)

        filters_layout.addStretch()
        layout.addLayout(filters_layout)

        # Seznam šablon
        self.templates_table = QTableWidget()
        self.templates_table.setColumnCount(4)
        self.templates_table.setHorizontalHeaderLabels([
            "Název",
            "Typ",
            "Výchozí",
            "Datum úpravy"
        ])
        self.templates_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.templates_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.templates_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.templates_table.currentItemChanged.connect(self.on_template_selected)
        layout.addWidget(self.templates_table)

        return widget

    def create_right_panel(self):
        """Pravý panel s editorem"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tlačítka akcí
        actions_layout = QHBoxLayout()

        save_btn = QPushButton("💾 Uložit")
        save_btn.clicked.connect(self.save_template)
        save_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 15px;")
        actions_layout.addWidget(save_btn)

        preview_btn = QPushButton("👁️ Náhled")
        preview_btn.clicked.connect(self.preview_template)
        actions_layout.addWidget(preview_btn)

        test_btn = QPushButton("🧪 Test s daty")
        test_btn.clicked.connect(self.test_template)
        actions_layout.addWidget(test_btn)

        export_btn = QPushButton("📤 Export")
        export_btn.clicked.connect(self.export_template)
        actions_layout.addWidget(export_btn)

        duplicate_btn = QPushButton("📋 Duplikovat")
        duplicate_btn.clicked.connect(self.duplicate_template)
        actions_layout.addWidget(duplicate_btn)

        delete_btn = QPushButton("🗑️ Smazat")
        delete_btn.clicked.connect(self.delete_template)
        delete_btn.setStyleSheet(f"background-color: {config.COLOR_DANGER}; color: white; padding: 8px 15px;")
        actions_layout.addWidget(delete_btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        # Záložky
        tabs = QTabWidget()

        # Záložka: Základní údaje
        self.tab_basic = self.create_basic_tab()
        tabs.addTab(self.tab_basic, "📋 Základní údaje")

        # Záložka: Editor
        self.tab_editor = self.create_editor_tab()
        tabs.addTab(self.tab_editor, "✏️ Editor")

        # Záložka: Styly
        self.tab_styles = self.create_styles_tab()
        tabs.addTab(self.tab_styles, "🎨 Styly")

        # Záložka: Proměnné
        self.tab_variables = self.create_variables_tab()
        tabs.addTab(self.tab_variables, "📝 Proměnné")

        layout.addWidget(tabs)

        return widget

    def create_basic_tab(self):
        """Záložka: Základní údaje"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout(widget)

        # Formulář
        form_layout = QFormLayout()

        # Název šablony
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Např: Standardní faktura")
        form_layout.addRow("Název šablony:", self.name_input)

        # Typ šablony
        self.type_combo = QComboBox()
        self.type_combo.addItem("Faktura", "invoice")
        self.type_combo.addItem("Smlouva", "contract")
        self.type_combo.addItem("Protokol", "protocol")
        self.type_combo.addItem("Upomínka", "reminder")
        self.type_combo.addItem("Ostatní", "other")
        form_layout.addRow("Typ:", self.type_combo)

        # Popis
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("Popis šablony...")
        form_layout.addRow("Popis:", self.description_input)

        # Výchozí šablona
        self.default_checkbox = QCheckBox("Nastavit jako výchozí šablonu")
        form_layout.addRow("", self.default_checkbox)

        # Aktivní
        self.active_checkbox = QCheckBox("Aktivní (dostupná pro použití)")
        self.active_checkbox.setChecked(True)
        form_layout.addRow("", self.active_checkbox)

        layout.addLayout(form_layout)

        # Logo firmy
        logo_group = QGroupBox("Logo firmy")
        logo_layout = QVBoxLayout(logo_group)

        self.logo_preview = QLabel("Žádné logo")
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setMinimumHeight(100)
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

    def create_editor_tab(self):
        """Záložka: Editor"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info
        info_label = QLabel("💡 Používejte proměnné ve formátu: {{nazev_promenne}}")
        info_label.setStyleSheet("background-color: #e3f2fd; padding: 10px; border-radius: 4px;")
        layout.addWidget(info_label)

        # Části šablony
        parts_tabs = QTabWidget()

        # Hlavička
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        self.header_editor = QPlainTextEdit()
        self.header_editor.setPlaceholderText("HTML kód pro hlavičku dokumentu...")
        header_layout.addWidget(self.header_editor)
        parts_tabs.addTab(header_widget, "📄 Hlavička")

        # Tělo
        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        self.body_editor = QPlainTextEdit()
        self.body_editor.setPlaceholderText("HTML kód pro tělo dokumentu...")
        body_layout.addWidget(self.body_editor)
        parts_tabs.addTab(body_widget, "📝 Tělo")

        # Patička
        footer_widget = QWidget()
        footer_layout = QVBoxLayout(footer_widget)
        self.footer_editor = QPlainTextEdit()
        self.footer_editor.setPlaceholderText("HTML kód pro patičku dokumentu...")
        footer_layout.addWidget(self.footer_editor)
        parts_tabs.addTab(footer_widget, "📋 Patička")

        layout.addWidget(parts_tabs)

        # Tlačítka pro vložení proměnných
        variables_layout = QHBoxLayout()
        variables_label = QLabel("Rychlé vložení:")
        variables_layout.addWidget(variables_label)

        common_vars = [
            ("Název firmy", "{{company_name}}"),
            ("IČO", "{{ico}}"),
            ("DIČ", "{{dic}}"),
            ("Dnešní datum", "{{current_date}}"),
            ("Číslo faktury", "{{invoice_number}}"),
        ]

        for label, var in common_vars:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, v=var: self.insert_variable(v))
            variables_layout.addWidget(btn)

        variables_layout.addStretch()
        layout.addLayout(variables_layout)

        return widget

    def create_styles_tab(self):
        """Záložka: Styly"""
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)

        layout = QVBoxLayout(widget)

        # Barvy
        colors_group = QGroupBox("🎨 Barvy")
        colors_layout = QFormLayout(colors_group)

        # Primární barva
        primary_color_layout = QHBoxLayout()
        self.primary_color_input = QLineEdit("#2c3e50")
        primary_color_layout.addWidget(self.primary_color_input)
        primary_color_btn = QPushButton("🎨")
        primary_color_btn.clicked.connect(lambda: self.choose_color(self.primary_color_input))
        primary_color_layout.addWidget(primary_color_btn)
        colors_layout.addRow("Primární barva:", primary_color_layout)

        # Sekundární barva
        secondary_color_layout = QHBoxLayout()
        self.secondary_color_input = QLineEdit("#3498db")
        secondary_color_layout.addWidget(self.secondary_color_input)
        secondary_color_btn = QPushButton("🎨")
        secondary_color_btn.clicked.connect(lambda: self.choose_color(self.secondary_color_input))
        secondary_color_layout.addWidget(secondary_color_btn)
        colors_layout.addRow("Sekundární barva:", secondary_color_layout)

        # Barva textu
        text_color_layout = QHBoxLayout()
        self.text_color_input = QLineEdit("#333333")
        text_color_layout.addWidget(self.text_color_input)
        text_color_btn = QPushButton("🎨")
        text_color_btn.clicked.connect(lambda: self.choose_color(self.text_color_input))
        text_color_layout.addWidget(text_color_btn)
        colors_layout.addRow("Barva textu:", text_color_layout)

        layout.addWidget(colors_group)

        # Fonty
        fonts_group = QGroupBox("🔤 Fonty")
        fonts_layout = QFormLayout(fonts_group)

        # Font nadpisů
        self.heading_font_combo = QComboBox()
        self.heading_font_combo.addItems([
            "Arial",
            "Helvetica",
            "Times New Roman",
            "Georgia",
            "Verdana",
            "Calibri"
        ])
        fonts_layout.addRow("Font nadpisů:", self.heading_font_combo)

        # Font textu
        self.body_font_combo = QComboBox()
        self.body_font_combo.addItems([
            "Arial",
            "Helvetica",
            "Times New Roman",
            "Georgia",
            "Verdana",
            "Calibri"
        ])
        fonts_layout.addRow("Font textu:", self.body_font_combo)

        # Velikost základního fontu
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setValue(11)
        self.font_size_spin.setSuffix(" pt")
        fonts_layout.addRow("Velikost základního fontu:", self.font_size_spin)

        layout.addWidget(fonts_group)

        # Rozměry
        dimensions_group = QGroupBox("📏 Rozměry")
        dimensions_layout = QFormLayout(dimensions_group)

        # Formát papíru
        self.paper_format_combo = QComboBox()
        self.paper_format_combo.addItems(["A4", "Letter"])
        dimensions_layout.addRow("Formát papíru:", self.paper_format_combo)

        # Okraje
        margins_layout = QHBoxLayout()
        self.margin_top = QSpinBox()
        self.margin_top.setRange(0, 50)
        self.margin_top.setValue(20)
        self.margin_top.setSuffix(" mm")
        margins_layout.addWidget(QLabel("Horní:"))
        margins_layout.addWidget(self.margin_top)

        self.margin_bottom = QSpinBox()
        self.margin_bottom.setRange(0, 50)
        self.margin_bottom.setValue(20)
        self.margin_bottom.setSuffix(" mm")
        margins_layout.addWidget(QLabel("Dolní:"))
        margins_layout.addWidget(self.margin_bottom)

        self.margin_left = QSpinBox()
        self.margin_left.setRange(0, 50)
        self.margin_left.setValue(15)
        self.margin_left.setSuffix(" mm")
        margins_layout.addWidget(QLabel("Levý:"))
        margins_layout.addWidget(self.margin_left)

        self.margin_right = QSpinBox()
        self.margin_right.setRange(0, 50)
        self.margin_right.setValue(15)
        self.margin_right.setSuffix(" mm")
        margins_layout.addWidget(QLabel("Pravý:"))
        margins_layout.addWidget(self.margin_right)

        dimensions_layout.addRow("Okraje:", margins_layout)

        layout.addWidget(dimensions_group)

        layout.addStretch()

        return scroll

    def create_variables_tab(self):
        """Záložka: Proměnné"""
        widget = QWidget()
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

        info_title = QLabel("💡 Dostupné proměnné")
        info_font = QFont()
        info_font.setBold(True)
        info_title.setFont(info_font)
        info_layout.addWidget(info_title)

        info_text = QLabel(
            "Proměnné se používají ve formátu: {{nazev_promenne}}\n"
            "Při generování dokumentu budou automaticky nahrazeny skutečnými hodnotami."
        )
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)

        layout.addWidget(info_frame)

        # Kategorie proměnných
        categories_tabs = QTabWidget()

        # Firemní údaje
        company_vars = self.create_variables_list([
            ("{{company_name}}", "Název firmy"),
            ("{{company_address}}", "Adresa firmy"),
            ("{{company_city}}", "Město"),
            ("{{company_zip}}", "PSČ"),
            ("{{ico}}", "IČO"),
            ("{{dic}}", "DIČ"),
            ("{{phone}}", "Telefon"),
            ("{{email}}", "Email"),
            ("{{website}}", "Web"),
            ("{{bank_account}}", "Číslo účtu"),
            ("{{bank_code}}", "Kód banky"),
            ("{{iban}}", "IBAN"),
        ])
        categories_tabs.addTab(company_vars, "🏢 Firemní údaje")

        # Zákazník
        customer_vars = self.create_variables_list([
            ("{{customer_name}}", "Jméno zákazníka"),
            ("{{customer_company}}", "Firma zákazníka"),
            ("{{customer_address}}", "Adresa zákazníka"),
            ("{{customer_city}}", "Město"),
            ("{{customer_zip}}", "PSČ"),
            ("{{customer_ico}}", "IČO zákazníka"),
            ("{{customer_dic}}", "DIČ zákazníka"),
            ("{{customer_email}}", "Email"),
            ("{{customer_phone}}", "Telefon"),
        ])
        categories_tabs.addTab(customer_vars, "👤 Zákazník")

        # Faktura
        invoice_vars = self.create_variables_list([
            ("{{invoice_number}}", "Číslo faktury"),
            ("{{issue_date}}", "Datum vystavení"),
            ("{{due_date}}", "Datum splatnosti"),
            ("{{tax_date}}", "Datum zdanit. plnění"),
            ("{{variable_symbol}}", "Variabilní symbol"),
            ("{{constant_symbol}}", "Konstantní symbol"),
            ("{{payment_method}}", "Způsob úhrady"),
            ("{{total_without_vat}}", "Celkem bez DPH"),
            ("{{total_vat}}", "Celkem DPH"),
            ("{{total_with_vat}}", "Celkem s DPH"),
            ("{{items_table}}", "Tabulka položek"),
        ])
        categories_tabs.addTab(invoice_vars, "💰 Faktura")

        # Vozidlo
        vehicle_vars = self.create_variables_list([
            ("{{vehicle_license_plate}}", "SPZ"),
            ("{{vehicle_brand}}", "Značka"),
            ("{{vehicle_model}}", "Model"),
            ("{{vehicle_year}}", "Rok výroby"),
            ("{{vehicle_vin}}", "VIN"),
        ])
        categories_tabs.addTab(vehicle_vars, "🚗 Vozidlo")

        # Zakázka
        order_vars = self.create_variables_list([
            ("{{order_number}}", "Číslo zakázky"),
            ("{{order_description}}", "Popis zakázky"),
            ("{{order_date}}", "Datum zakázky"),
            ("{{order_status}}", "Stav zakázky"),
        ])
        categories_tabs.addTab(order_vars, "📦 Zakázka")

        # Ostatní
        other_vars = self.create_variables_list([
            ("{{current_date}}", "Dnešní datum"),
            ("{{current_time}}", "Aktuální čas"),
            ("{{current_year}}", "Aktuální rok"),
            ("{{page_number}}", "Číslo stránky"),
            ("{{total_pages}}", "Celkem stránek"),
        ])
        categories_tabs.addTab(other_vars, "📝 Ostatní")

        layout.addWidget(categories_tabs)

        # Vlastní proměnné
        custom_group = QGroupBox("➕ Vlastní proměnné")
        custom_layout = QVBoxLayout(custom_group)

        custom_info = QLabel("Zde můžete definovat vlastní proměnné pro podmíněné texty.")
        custom_layout.addWidget(custom_info)

        # TODO: Implementovat správu vlastních proměnných

        layout.addWidget(custom_group)

        return widget

    def create_variables_list(self, variables):
        """Vytvoření seznamu proměnných"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Proměnná", "Popis"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setRowCount(len(variables))

        for row, (var, desc) in enumerate(variables):
            var_item = QTableWidgetItem(var)
            var_item.setFont(QFont("Courier New", 10))
            table.setItem(row, 0, var_item)
            table.setItem(row, 1, QTableWidgetItem(desc))

        layout.addWidget(table)

        return widget

    # =====================================================
    # NAČÍTÁNÍ DAT
    # =====================================================

    def load_templates(self):
        """Načtení šablon"""
        try:
            query = """
                SELECT * FROM document_templates
                ORDER BY is_default DESC, name
            """
            templates = db.fetch_all(query)

            self.templates_table.setRowCount(len(templates))

            for row, template in enumerate(templates):
                # Název
                name_item = QTableWidgetItem(template["name"])
                name_item.setData(Qt.ItemDataRole.UserRole, template["id"])
                self.templates_table.setItem(row, 0, name_item)

                # Typ
                type_label = self.get_type_label(template["template_type"])
                self.templates_table.setItem(row, 1, QTableWidgetItem(type_label))

                # Výchozí
                default_item = QTableWidgetItem("✓" if template["is_default"] else "")
                default_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if template["is_default"]:
                    default_item.setForeground(QColor(config.COLOR_SUCCESS))
                self.templates_table.setItem(row, 2, default_item)

                # Datum úpravy
                updated = datetime.fromisoformat(template["updated_at"]).strftime("%d.%m.%Y")
                self.templates_table.setItem(row, 3, QTableWidgetItem(updated))

        except Exception as e:
            print(f"Chyba při načítání šablon: {e}")

    def on_template_selected(self):
        """Vybraná šablona"""
        current_row = self.templates_table.currentRow()
        if current_row < 0:
            return

        try:
            template_id = self.templates_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)

            query = "SELECT * FROM document_templates WHERE id = ?"
            template = db.fetch_one(query, (template_id,))

            if not template:
                return

            self.current_template = template

            # Načíst data do formuláře
            self.name_input.setText(template["name"])

            index = self.type_combo.findData(template["template_type"])
            if index >= 0:
                self.type_combo.setCurrentIndex(index)

            self.description_input.setPlainText(template["description"] or "")
            self.default_checkbox.setChecked(template["is_default"] == 1)
            self.active_checkbox.setChecked(template["is_active"] == 1)

            # Načíst content (JSON)
            if template["content"]:
                content = json.loads(template["content"])

                # Editor
                self.header_editor.setPlainText(content.get("header", ""))
                self.body_editor.setPlainText(content.get("body", ""))
                self.footer_editor.setPlainText(content.get("footer", ""))

                # Styly
                styles = content.get("styles", {})
                self.primary_color_input.setText(styles.get("primary_color", "#2c3e50"))
                self.secondary_color_input.setText(styles.get("secondary_color", "#3498db"))
                self.text_color_input.setText(styles.get("text_color", "#333333"))

                heading_font = styles.get("heading_font", "Arial")
                index = self.heading_font_combo.findText(heading_font)
                if index >= 0:
                    self.heading_font_combo.setCurrentIndex(index)

                body_font = styles.get("body_font", "Arial")
                index = self.body_font_combo.findText(body_font)
                if index >= 0:
                    self.body_font_combo.setCurrentIndex(index)

                self.font_size_spin.setValue(styles.get("font_size", 11))

                paper_format = styles.get("paper_format", "A4")
                index = self.paper_format_combo.findText(paper_format)
                if index >= 0:
                    self.paper_format_combo.setCurrentIndex(index)

                margins = styles.get("margins", {})
                self.margin_top.setValue(margins.get("top", 20))
                self.margin_bottom.setValue(margins.get("bottom", 20))
                self.margin_left.setValue(margins.get("left", 15))
                self.margin_right.setValue(margins.get("right", 15))

            # Logo
            if template["logo_path"]:
                logo_path = Path(template["logo_path"])
                if logo_path.exists():
                    pixmap = QPixmap(str(logo_path))
                    scaled_pixmap = pixmap.scaled(
                        200, 100,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.logo_preview.setPixmap(scaled_pixmap)
                else:
                    self.logo_preview.setText("Logo nenalezeno")
            else:
                self.logo_preview.clear()
                self.logo_preview.setText("Žádné logo")

        except Exception as e:
            print(f"Chyba při načítání šablony: {e}")

    # =====================================================
    # AKCE
    # =====================================================

    def new_template(self):
        """Nová šablona"""
        self.current_template = None

        # Vyčistit formulář
        self.name_input.clear()
        self.type_combo.setCurrentIndex(0)
        self.description_input.clear()
        self.default_checkbox.setChecked(False)
        self.active_checkbox.setChecked(True)

        self.header_editor.clear()
        self.body_editor.clear()
        self.footer_editor.clear()

        self.primary_color_input.setText("#2c3e50")
        self.secondary_color_input.setText("#3498db")
        self.text_color_input.setText("#333333")

        self.logo_preview.clear()
        self.logo_preview.setText("Žádné logo")

    def save_template(self):
        """Uložení šablony"""
        try:
            # Validace
            if not self.name_input.text().strip():
                QMessageBox.warning(self, "Chyba", "Vyplňte název šablony.")
                return

            # Připravit content (JSON)
            content = {
                "header": self.header_editor.toPlainText(),
                "body": self.body_editor.toPlainText(),
                "footer": self.footer_editor.toPlainText(),
                "styles": {
                    "primary_color": self.primary_color_input.text(),
                    "secondary_color": self.secondary_color_input.text(),
                    "text_color": self.text_color_input.text(),
                    "heading_font": self.heading_font_combo.currentText(),
                    "body_font": self.body_font_combo.currentText(),
                    "font_size": self.font_size_spin.value(),
                    "paper_format": self.paper_format_combo.currentText(),
                    "margins": {
                        "top": self.margin_top.value(),
                        "bottom": self.margin_bottom.value(),
                        "left": self.margin_left.value(),
                        "right": self.margin_right.value()
                    }
                }
            }

            content_json = json.dumps(content, ensure_ascii=False)

            # Pokud je výchozí, zrušit ostatní výchozí šablony stejného typu
            if self.default_checkbox.isChecked():
                template_type = self.type_combo.currentData()
                query = "UPDATE document_templates SET is_default = 0 WHERE template_type = ?"
                db.execute_query(query, (template_type,))

            if self.current_template:
                # Aktualizace
                query = """
                    UPDATE document_templates SET
                        name = ?,
                        template_type = ?,
                        description = ?,
                        content = ?,
                        is_default = ?,
                        is_active = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """
                db.execute_query(query, (
                    self.name_input.text().strip(),
                    self.type_combo.currentData(),
                    self.description_input.toPlainText().strip() or None,
                    content_json,
                    1 if self.default_checkbox.isChecked() else 0,
                    1 if self.active_checkbox.isChecked() else 0,
                    self.current_template["id"]
                ))
            else:
                # Vložení
                query = """
                    INSERT INTO document_templates (
                        name, template_type, description, content,
                        is_default, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """
                db.execute_query(query, (
                    self.name_input.text().strip(),
                    self.type_combo.currentData(),
                    self.description_input.toPlainText().strip() or None,
                    content_json,
                    1 if self.default_checkbox.isChecked() else 0,
                    1 if self.active_checkbox.isChecked() else 0
                ))

            QMessageBox.information(self, "Úspěch", "Šablona byla uložena.")
            self.load_templates()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit šablonu:\n{e}")

    def preview_template(self):
        """Náhled šablony"""
        if not self.current_template and not self.name_input.text():
            QMessageBox.warning(self, "Upozornění", "Nejprve vytvořte nebo vyberte šablonu.")
            return

        # TODO: Implementovat náhled s ukázkovými daty
        QMessageBox.information(
            self,
            "Náhled",
            "Funkce náhledu šablony bude implementována.\n\n"
            "Zobrazí se PDF dokument s ukázkovými daty."
        )

    def test_template(self):
        """Test šablony s reálnými daty"""
        if not self.current_template and not self.name_input.text():
            QMessageBox.warning(self, "Upozornění", "Nejprve vytvořte nebo vyberte šablonu.")
            return

        # Dialog pro výběr dat
        dialog = TestDataDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # TODO: Generovat dokument s vybranými daty
            QMessageBox.information(
                self,
                "Test",
                "Funkce testu šablony s reálnými daty bude implementována."
            )

    def export_template(self):
        """Export šablony"""
        if not self.current_template:
            QMessageBox.warning(self, "Upozornění", "Vyberte šablonu k exportu.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportovat šablonu",
            f"{self.current_template['name']}.json",
            "JSON soubory (*.json)"
        )

        if not file_path:
            return

        try:
            # Připravit data pro export
            export_data = {
                "name": self.current_template["name"],
                "type": self.current_template["template_type"],
                "description": self.current_template["description"],
                "content": json.loads(self.current_template["content"]),
                "version": "1.0"
            }

            # Uložit do souboru
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            QMessageBox.information(self, "Úspěch", f"Šablona byla exportována do:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se exportovat šablonu:\n{e}")

    def import_template(self):
        """Import šablony"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importovat šablonu",
            "",
            "JSON soubory (*.json)"
        )

        if not file_path:
            return

        try:
            # Načíst ze souboru
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            # Validace
            required_fields = ["name", "type", "content"]
            if not all(field in import_data for field in required_fields):
                raise ValueError("Neplatný formát šablony")

            # Vložit do databáze
            content_json = json.dumps(import_data["content"], ensure_ascii=False)

            query = """
                INSERT INTO document_templates (
                    name, template_type, description, content, is_default, is_active
                ) VALUES (?, ?, ?, ?, 0, 1)
            """
            db.execute_query(query, (
                import_data["name"],
                import_data["type"],
                import_data.get("description", ""),
                content_json
            ))

            QMessageBox.information(self, "Úspěch", "Šablona byla importována.")
            self.load_templates()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se importovat šablonu:\n{e}")

    def duplicate_template(self):
        """Duplikovat šablonu"""
        if not self.current_template:
            QMessageBox.warning(self, "Upozornění", "Vyberte šablonu k duplikování.")
            return

        try:
            new_name = f"{self.current_template['name']} (kopie)"

            query = """
                INSERT INTO document_templates (
                    name, template_type, description, content, logo_path,
                    is_default, is_active
                ) VALUES (?, ?, ?, ?, ?, 0, ?)
            """
            db.execute_query(query, (
                new_name,
                self.current_template["template_type"],
                self.current_template["description"],
                self.current_template["content"],
                self.current_template["logo_path"],
                self.current_template["is_active"]
            ))

            QMessageBox.information(self, "Úspěch", "Šablona byla zduplikována.")
            self.load_templates()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se duplikovat šablonu:\n{e}")

    def delete_template(self):
        """Smazat šablonu"""
        if not self.current_template:
            QMessageBox.warning(self, "Upozornění", "Vyberte šablonu ke smazání.")
            return

        reply = QMessageBox.question(
            self,
            "Smazat šablonu",
            f"Opravdu chcete smazat šablonu '{self.current_template['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = "DELETE FROM document_templates WHERE id = ?"
                db.execute_query(query, (self.current_template["id"],))

                QMessageBox.information(self, "Úspěch", "Šablona byla smazána.")
                self.current_template = None
                self.load_templates()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat šablonu:\n{e}")

    def upload_logo(self):
        """Nahrát logo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Vyberte logo",
            "",
            "Obrázky (*.png *.jpg *.jpeg)"
        )

        if not file_path:
            return

        try:
            # Zkopírovat do data/templates/logos
            logos_dir = Path(config.DATA_DIR) / "templates" / "logos"
            logos_dir.mkdir(parents=True, exist_ok=True)

            source_path = Path(file_path)
            dest_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{source_path.name}"
            dest_path = logos_dir / dest_filename

            import shutil
            shutil.copy2(source_path, dest_path)

            # Aktualizovat v databázi (pokud máme ID šablony)
            if self.current_template:
                query = "UPDATE document_templates SET logo_path = ? WHERE id = ?"
                db.execute_query(query, (str(dest_path), self.current_template["id"]))
                self.current_template["logo_path"] = str(dest_path)

            # Zobrazit náhled
            pixmap = QPixmap(str(dest_path))
            scaled_pixmap = pixmap.scaled(
                200, 100,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.logo_preview.setPixmap(scaled_pixmap)

            QMessageBox.information(self, "Úspěch", "Logo bylo nahráno.")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se nahrát logo:\n{e}")

    def remove_logo(self):
        """Odebrat logo"""
        if self.current_template and self.current_template["logo_path"]:
            try:
                query = "UPDATE document_templates SET logo_path = NULL WHERE id = ?"
                db.execute_query(query, (self.current_template["id"],))
                self.current_template["logo_path"] = None

                self.logo_preview.clear()
                self.logo_preview.setText("Žádné logo")

                QMessageBox.information(self, "Úspěch", "Logo bylo odebráno.")

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se odebrat logo:\n{e}")

    def choose_color(self, line_edit):
        """Výběr barvy"""
        current_color = QColor(line_edit.text())
        color = QColorDialog.getColor(current_color, self, "Vyberte barvu")

        if color.isValid():
            line_edit.setText(color.name())

    def insert_variable(self, variable):
        """Vložit proměnnou do aktivního editoru"""
        # Zjistit, který editor je aktivní
        focused = self.focusWidget()

        if isinstance(focused, QPlainTextEdit):
            cursor = focused.textCursor()
            cursor.insertText(variable)
            focused.setFocus()

    # =====================================================
    # POMOCNÉ METODY
    # =====================================================

    def get_type_label(self, template_type):
        """Vrátí popisek pro typ šablony"""
        labels = {
            "invoice": "Faktura",
            "contract": "Smlouva",
            "protocol": "Protokol",
            "reminder": "Upomínka",
            "other": "Ostatní"
        }
        return labels.get(template_type, "Neznámý")

    def filter_templates(self):
        """Filtrování šablon"""
        # TODO: Implementovat filtrování
        pass

    def refresh(self):
        """Obnovení"""
        self.load_templates()


# =====================================================
# DIALOGY
# =====================================================

class TestDataDialog(QDialog):
    """Dialog pro výběr testovacích dat"""

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Vybrat testovací data")
        self.setMinimumWidth(400)

        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QFormLayout(self)

        # Faktura
        self.invoice_combo = QComboBox()
        self.load_invoices()
        layout.addRow("Faktura:", self.invoice_combo)

        # Zákazník
        self.customer_combo = QComboBox()
        self.load_customers()
        layout.addRow("Zákazník:", self.customer_combo)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("Generovat")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 20px;")
        buttons_layout.addWidget(ok_btn)

        layout.addRow(buttons_layout)

    def load_invoices(self):
        """Načtení faktur"""
        try:
            query = """
                SELECT id, invoice_number FROM invoices
                ORDER BY created_at DESC
                LIMIT 20
            """
            invoices = db.fetch_all(query)

            for inv in invoices:
                self.invoice_combo.addItem(inv["invoice_number"], inv["id"])

        except Exception as e:
            print(f"Chyba při načítání faktur: {e}")

    def load_customers(self):
        """Načtení zákazníků"""
        try:
            query = """
                SELECT id, first_name, last_name, company FROM customers
                ORDER BY last_name, first_name
                LIMIT 50
            """
            customers = db.fetch_all(query)

            for cust in customers:
                text = f"{cust['first_name']} {cust['last_name']}"
                if cust['company']:
                    text += f" ({cust['company']})"
                self.customer_combo.addItem(text, cust["id"])

        except Exception as e:
            print(f"Chyba při načítání zákazníků: {e}")
