# -*- coding: utf-8 -*-
"""
Nastavení vzhledu a přizpůsobení
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QLabel,
    QPushButton, QScrollArea, QRadioButton, QButtonGroup,
    QColorDialog, QSlider
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from database_manager import db
import config
import json


class AppearanceSettingsWidget(QWidget):
    """Widget pro nastavení vzhledu"""

    def __init__(self):
        super().__init__()
        self.colors = {
            "primary": config.COLOR_PRIMARY,
            "secondary": config.COLOR_SECONDARY,
            "success": config.COLOR_SUCCESS,
            "warning": config.COLOR_WARNING,
            "danger": config.COLOR_DANGER
        }
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

        main_layout.addWidget(self.create_theme_section())
        main_layout.addWidget(self.create_colors_section())
        main_layout.addWidget(self.create_font_section())
        main_layout.addWidget(self.create_layout_section())
        main_layout.addWidget(self.create_dashboard_section())
        main_layout.addWidget(self.create_tables_section())
        main_layout.addWidget(self.create_language_section())

        main_layout.addStretch()

        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        self.set_styles()

    def create_theme_section(self):
        """Sekce tématu"""
        group = QGroupBox("🎨 Téma aplikace")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        self.theme_group = QButtonGroup(self)

        self.theme_light = QRadioButton("☀️ Světlé téma")
        self.theme_light.setChecked(True)
        self.theme_group.addButton(self.theme_light)
        layout.addWidget(self.theme_light)

        self.theme_dark = QRadioButton("🌙 Tmavé téma")
        self.theme_group.addButton(self.theme_dark)
        layout.addWidget(self.theme_dark)

        self.theme_auto = QRadioButton("🔄 Automaticky podle systému")
        self.theme_group.addButton(self.theme_auto)
        layout.addWidget(self.theme_auto)

        self.theme_custom = QRadioButton("🎨 Vlastní barvy")
        self.theme_group.addButton(self.theme_custom)
        layout.addWidget(self.theme_custom)

        info_label = QLabel("💡 Změna tématu se projeví po restartu aplikace.")
        info_label.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-top: 5px;")
        layout.addWidget(info_label)

        return group

    def create_colors_section(self):
        """Sekce barev"""
        group = QGroupBox("🌈 Barvy aplikace")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        primary_layout = QHBoxLayout()
        primary_layout.addWidget(QLabel("Primární barva:"))

        self.primary_color_preview = QLabel()
        self.primary_color_preview.setFixedSize(60, 30)
        self.primary_color_preview.setStyleSheet(f"background-color: {self.colors['primary']}; border-radius: 4px;")
        primary_layout.addWidget(self.primary_color_preview)

        self.primary_color_input = QLineEdit(self.colors['primary'])
        self.primary_color_input.setMaxLength(7)
        self.primary_color_input.textChanged.connect(lambda t: self.update_color_preview("primary", t))
        primary_layout.addWidget(self.primary_color_input)

        primary_btn = QPushButton("🎨")
        primary_btn.setFixedWidth(40)
        primary_btn.clicked.connect(lambda: self.choose_color("primary"))
        primary_layout.addWidget(primary_btn)
        primary_layout.addStretch()

        layout.addLayout(primary_layout)

        secondary_layout = QHBoxLayout()
        secondary_layout.addWidget(QLabel("Sekundární barva:"))

        self.secondary_color_preview = QLabel()
        self.secondary_color_preview.setFixedSize(60, 30)
        self.secondary_color_preview.setStyleSheet(f"background-color: {self.colors['secondary']}; border-radius: 4px;")
        secondary_layout.addWidget(self.secondary_color_preview)

        self.secondary_color_input = QLineEdit(self.colors['secondary'])
        self.secondary_color_input.setMaxLength(7)
        self.secondary_color_input.textChanged.connect(lambda t: self.update_color_preview("secondary", t))
        secondary_layout.addWidget(self.secondary_color_input)

        secondary_btn = QPushButton("🎨")
        secondary_btn.setFixedWidth(40)
        secondary_btn.clicked.connect(lambda: self.choose_color("secondary"))
        secondary_layout.addWidget(secondary_btn)
        secondary_layout.addStretch()

        layout.addLayout(secondary_layout)

        success_layout = QHBoxLayout()
        success_layout.addWidget(QLabel("Barva úspěchu:"))

        self.success_color_preview = QLabel()
        self.success_color_preview.setFixedSize(60, 30)
        self.success_color_preview.setStyleSheet(f"background-color: {self.colors['success']}; border-radius: 4px;")
        success_layout.addWidget(self.success_color_preview)

        self.success_color_input = QLineEdit(self.colors['success'])
        self.success_color_input.setMaxLength(7)
        self.success_color_input.textChanged.connect(lambda t: self.update_color_preview("success", t))
        success_layout.addWidget(self.success_color_input)

        success_btn = QPushButton("🎨")
        success_btn.setFixedWidth(40)
        success_btn.clicked.connect(lambda: self.choose_color("success"))
        success_layout.addWidget(success_btn)
        success_layout.addStretch()

        layout.addLayout(success_layout)

        warning_layout = QHBoxLayout()
        warning_layout.addWidget(QLabel("Barva varování:"))

        self.warning_color_preview = QLabel()
        self.warning_color_preview.setFixedSize(60, 30)
        self.warning_color_preview.setStyleSheet(f"background-color: {self.colors['warning']}; border-radius: 4px;")
        warning_layout.addWidget(self.warning_color_preview)

        self.warning_color_input = QLineEdit(self.colors['warning'])
        self.warning_color_input.setMaxLength(7)
        self.warning_color_input.textChanged.connect(lambda t: self.update_color_preview("warning", t))
        warning_layout.addWidget(self.warning_color_input)

        warning_btn = QPushButton("🎨")
        warning_btn.setFixedWidth(40)
        warning_btn.clicked.connect(lambda: self.choose_color("warning"))
        warning_layout.addWidget(warning_btn)
        warning_layout.addStretch()

        layout.addLayout(warning_layout)

        danger_layout = QHBoxLayout()
        danger_layout.addWidget(QLabel("Barva chyby:"))

        self.danger_color_preview = QLabel()
        self.danger_color_preview.setFixedSize(60, 30)
        self.danger_color_preview.setStyleSheet(f"background-color: {self.colors['danger']}; border-radius: 4px;")
        danger_layout.addWidget(self.danger_color_preview)

        self.danger_color_input = QLineEdit(self.colors['danger'])
        self.danger_color_input.setMaxLength(7)
        self.danger_color_input.textChanged.connect(lambda t: self.update_color_preview("danger", t))
        danger_layout.addWidget(self.danger_color_input)

        danger_btn = QPushButton("🎨")
        danger_btn.setFixedWidth(40)
        danger_btn.clicked.connect(lambda: self.choose_color("danger"))
        danger_layout.addWidget(danger_btn)
        danger_layout.addStretch()

        layout.addLayout(danger_layout)

        reset_colors_btn = QPushButton("🔄 Obnovit výchozí barvy")
        reset_colors_btn.clicked.connect(self.reset_colors)
        reset_colors_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(reset_colors_btn)

        return group

    def update_color_preview(self, color_type, hex_color):
        """Aktualizace náhledu barvy"""
        if not hex_color.startswith("#"):
            hex_color = "#" + hex_color

        if len(hex_color) == 7:
            preview = getattr(self, f"{color_type}_color_preview", None)
            if preview:
                preview.setStyleSheet(f"background-color: {hex_color}; border-radius: 4px;")
                self.colors[color_type] = hex_color

    def choose_color(self, color_type):
        """Výběr barvy"""
        current_color = QColor(self.colors.get(color_type, "#3498db"))
        color = QColorDialog.getColor(current_color, self)

        if color.isValid():
            hex_color = color.name()
            self.colors[color_type] = hex_color

            input_field = getattr(self, f"{color_type}_color_input", None)
            if input_field:
                input_field.setText(hex_color)

            preview = getattr(self, f"{color_type}_color_preview", None)
            if preview:
                preview.setStyleSheet(f"background-color: {hex_color}; border-radius: 4px;")

    def reset_colors(self):
        """Obnovení výchozích barev"""
        default_colors = {
            "primary": "#2c3e50",
            "secondary": "#3498db",
            "success": "#27ae60",
            "warning": "#f39c12",
            "danger": "#e74c3c"
        }

        for color_type, color_value in default_colors.items():
            self.colors[color_type] = color_value

            input_field = getattr(self, f"{color_type}_color_input", None)
            if input_field:
                input_field.setText(color_value)

            preview = getattr(self, f"{color_type}_color_preview", None)
            if preview:
                preview.setStyleSheet(f"background-color: {color_value}; border-radius: 4px;")

    def create_font_section(self):
        """Sekce písma"""
        group = QGroupBox("🔤 Písmo")
        group.setObjectName("settingsGroup")
        layout = QFormLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        self.app_font = QComboBox()
        self.app_font.addItems([
            "Segoe UI",
            "Roboto",
            "Arial",
            "Helvetica",
            "Open Sans",
            "Noto Sans",
            "Ubuntu"
        ])
        layout.addRow("Font aplikace:", self.app_font)

        self.font_size = QComboBox()
        self.font_size.addItems(["Malé (9)", "Střední (10)", "Velké (12)", "Extra velké (14)"])
        self.font_size.setCurrentIndex(1)
        layout.addRow("Velikost písma:", self.font_size)

        self.bold_headers = QCheckBox("Tučné nadpisy")
        self.bold_headers.setChecked(True)
        layout.addRow("", self.bold_headers)

        return group

    def create_layout_section(self):
        """Sekce layoutu"""
        group = QGroupBox("📐 Rozložení")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        self.compact_mode = QCheckBox("Kompaktní režim (menší mezery)")
        layout.addWidget(self.compact_mode)

        self.show_icons = QCheckBox("Zobrazit ikony v menu")
        self.show_icons.setChecked(True)
        layout.addWidget(self.show_icons)

        self.show_button_labels = QCheckBox("Zobrazit popisky tlačítek")
        self.show_button_labels.setChecked(True)
        layout.addWidget(self.show_button_labels)

        menu_width_layout = QHBoxLayout()
        menu_width_layout.addWidget(QLabel("Šířka postranního menu:"))

        self.menu_width = QSlider(Qt.Orientation.Horizontal)
        self.menu_width.setRange(200, 350)
        self.menu_width.setValue(250)
        self.menu_width.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.menu_width.setTickInterval(25)
        menu_width_layout.addWidget(self.menu_width)

        self.menu_width_label = QLabel("250 px")
        self.menu_width.valueChanged.connect(lambda v: self.menu_width_label.setText(f"{v} px"))
        menu_width_layout.addWidget(self.menu_width_label)

        layout.addLayout(menu_width_layout)

        default_module_layout = QHBoxLayout()
        default_module_layout.addWidget(QLabel("Výchozí modul po přihlášení:"))

        self.default_module = QComboBox()
        for module in config.MODULES:
            self.default_module.addItem(f"{module['icon']} {module['name']}", module['id'])
        default_module_layout.addWidget(self.default_module)
        default_module_layout.addStretch()

        layout.addLayout(default_module_layout)

        return group

    def create_dashboard_section(self):
        """Sekce dashboardu"""
        group = QGroupBox("📊 Dashboard")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        widgets_label = QLabel("Zobrazit widgety:")
        widgets_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(widgets_label)

        self.widget_today_orders = QCheckBox("📋 Dnešní zakázky")
        self.widget_today_orders.setChecked(True)
        layout.addWidget(self.widget_today_orders)

        self.widget_statistics = QCheckBox("📊 Statistiky")
        self.widget_statistics.setChecked(True)
        layout.addWidget(self.widget_statistics)

        self.widget_utilization = QCheckBox("👷 Vytíženost mechaniků")
        self.widget_utilization.setChecked(True)
        layout.addWidget(self.widget_utilization)

        self.widget_alerts = QCheckBox("⚠️ Upozornění")
        self.widget_alerts.setChecked(True)
        layout.addWidget(self.widget_alerts)

        self.widget_quick_actions = QCheckBox("⚡ Rychlé akce")
        self.widget_quick_actions.setChecked(True)
        layout.addWidget(self.widget_quick_actions)

        self.widget_calendar = QCheckBox("📅 Dnešní události")
        layout.addWidget(self.widget_calendar)

        columns_layout = QHBoxLayout()
        columns_layout.addWidget(QLabel("Počet sloupců:"))

        self.dashboard_columns = QSpinBox()
        self.dashboard_columns.setRange(1, 4)
        self.dashboard_columns.setValue(3)
        columns_layout.addWidget(self.dashboard_columns)
        columns_layout.addStretch()

        layout.addLayout(columns_layout)

        refresh_layout = QHBoxLayout()
        self.auto_refresh = QCheckBox("Automatické obnovování každých")
        refresh_layout.addWidget(self.auto_refresh)

        self.refresh_interval = QSpinBox()
        self.refresh_interval.setRange(30, 600)
        self.refresh_interval.setValue(60)
        self.refresh_interval.setSuffix(" sekund")
        refresh_layout.addWidget(self.refresh_interval)
        refresh_layout.addStretch()

        layout.addLayout(refresh_layout)

        return group

    def create_tables_section(self):
        """Sekce tabulek"""
        group = QGroupBox("📋 Tabulky")
        group.setObjectName("settingsGroup")
        layout = QFormLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        self.rows_per_page = QComboBox()
        self.rows_per_page.addItems(["10", "25", "50", "100", "Vše"])
        self.rows_per_page.setCurrentIndex(1)
        layout.addRow("Řádků na stránku:", self.rows_per_page)

        self.alternating_rows = QCheckBox("Alternující barvy řádků")
        self.alternating_rows.setChecked(True)
        layout.addRow("", self.alternating_rows)

        self.highlight_hover = QCheckBox("Zvýrazňovat při najetí myší")
        self.highlight_hover.setChecked(True)
        layout.addRow("", self.highlight_hover)

        self.compact_rows = QCheckBox("Kompaktní řádky")
        layout.addRow("", self.compact_rows)

        return group

    def create_language_section(self):
        """Sekce jazyka a formátů"""
        group = QGroupBox("🌍 Jazyk a formáty")
        group.setObjectName("settingsGroup")
        layout = QFormLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        self.language = QComboBox()
        self.language.addItems([
            "🇨🇿 Čeština",
            "🇬🇧 English",
            "🇩🇪 Deutsch",
            "🇸🇰 Slovenčina"
        ])
        layout.addRow("Jazyk aplikace:", self.language)

        self.date_format = QComboBox()
        self.date_format.addItems([
            "DD.MM.YYYY (31.12.2025)",
            "YYYY-MM-DD (2025-12-31)",
            "MM/DD/YYYY (12/31/2025)",
            "DD/MM/YYYY (31/12/2025)"
        ])
        layout.addRow("Formát data:", self.date_format)

        self.time_format = QComboBox()
        self.time_format.addItems([
            "24 hodin (14:30)",
            "12 hodin AM/PM (2:30 PM)"
        ])
        layout.addRow("Formát času:", self.time_format)

        self.thousands_separator = QComboBox()
        self.thousands_separator.addItems([
            "Mezera (1 234 567)",
            "Tečka (1.234.567)",
            "Čárka (1,234,567)",
            "Bez oddělovače (1234567)"
        ])
        layout.addRow("Oddělovač tisíců:", self.thousands_separator)

        self.decimal_separator = QComboBox()
        self.decimal_separator.addItems([
            "Čárka (123,45)",
            "Tečka (123.45)"
        ])
        layout.addRow("Desetinný oddělovač:", self.decimal_separator)

        self.currency = QComboBox()
        self.currency.addItems([
            "CZK (Kč)",
            "EUR (€)",
            "USD ($)",
            "GBP (£)"
        ])
        layout.addRow("Měna:", self.currency)

        return group

    def load_settings(self):
        """Načtení nastavení"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT key, value FROM app_settings WHERE key LIKE 'appearance_%'")
            rows = cursor.fetchall()

            settings = {}
            for key, value in rows:
                settings[key.replace("appearance_", "")] = value

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
                """, (f"appearance_{key}", str(value)))

            conn.commit()

        except Exception as e:
            raise Exception(f"Chyba při ukládání: {str(e)}")

    def get_settings(self):
        """Získání nastavení"""
        theme = "light"
        if self.theme_dark.isChecked():
            theme = "dark"
        elif self.theme_auto.isChecked():
            theme = "auto"
        elif self.theme_custom.isChecked():
            theme = "custom"

        return {
            "theme": theme,
            "colors": self.colors,
            "app_font": self.app_font.currentText(),
            "font_size": self.font_size.currentText(),
            "bold_headers": self.bold_headers.isChecked(),
            "compact_mode": self.compact_mode.isChecked(),
            "show_icons": self.show_icons.isChecked(),
            "show_button_labels": self.show_button_labels.isChecked(),
            "menu_width": self.menu_width.value(),
            "default_module": self.default_module.currentData(),
            "widget_today_orders": self.widget_today_orders.isChecked(),
            "widget_statistics": self.widget_statistics.isChecked(),
            "widget_utilization": self.widget_utilization.isChecked(),
            "widget_alerts": self.widget_alerts.isChecked(),
            "widget_quick_actions": self.widget_quick_actions.isChecked(),
            "widget_calendar": self.widget_calendar.isChecked(),
            "dashboard_columns": self.dashboard_columns.value(),
            "auto_refresh": self.auto_refresh.isChecked(),
            "refresh_interval": self.refresh_interval.value(),
            "rows_per_page": self.rows_per_page.currentText(),
            "alternating_rows": self.alternating_rows.isChecked(),
            "highlight_hover": self.highlight_hover.isChecked(),
            "compact_rows": self.compact_rows.isChecked(),
            "language": self.language.currentText(),
            "date_format": self.date_format.currentText(),
            "time_format": self.time_format.currentText(),
            "thousands_separator": self.thousands_separator.currentText(),
            "decimal_separator": self.decimal_separator.currentText(),
            "currency": self.currency.currentText()
        }

    def set_settings(self, settings):
        """Nastavení hodnot"""
        if "theme" in settings:
            theme = settings["theme"]
            if theme == "dark":
                self.theme_dark.setChecked(True)
            elif theme == "auto":
                self.theme_auto.setChecked(True)
            elif theme == "custom":
                self.theme_custom.setChecked(True)
            else:
                self.theme_light.setChecked(True)

        if "app_font" in settings:
            index = self.app_font.findText(settings["app_font"])
            if index >= 0:
                self.app_font.setCurrentIndex(index)

        if "font_size" in settings:
            index = self.font_size.findText(settings["font_size"])
            if index >= 0:
                self.font_size.setCurrentIndex(index)

        if "menu_width" in settings:
            self.menu_width.setValue(int(settings["menu_width"]))

        if "dashboard_columns" in settings:
            self.dashboard_columns.setValue(int(settings["dashboard_columns"]))

        if "refresh_interval" in settings:
            self.refresh_interval.setValue(int(settings["refresh_interval"]))

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

            QCheckBox, QRadioButton {
                spacing: 8px;
            }

            QSlider::groove:horizontal {
                border: 1px solid #bdc3c7;
                height: 8px;
                background: #ecf0f1;
                border-radius: 4px;
            }

            QSlider::handle:horizontal {
                background: #3498db;
                border: 1px solid #2980b9;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)
