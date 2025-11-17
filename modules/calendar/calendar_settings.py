# -*- coding: utf-8 -*-
"""
Nastavení modulu kalendář
Používá key-value strukturu v databázi (setting_key, setting_value)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QGroupBox, QFormLayout, QSpinBox, QComboBox,
    QCheckBox, QTimeEdit, QTabWidget, QMessageBox,
    QLineEdit, QListWidget, QListWidgetItem, QScrollArea,
    QFileDialog
)
from PyQt6.QtCore import Qt, QTime, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime
from database_manager import db
import config
import json


class CalendarSettings(QWidget):
    """Widget pro nastavení modulu kalendář"""

    settings_saved = pyqtSignal()
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings_data = {}

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        top_panel = self.create_top_panel()
        main_layout.addWidget(top_panel)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("settingsScroll")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(15)

        tabs = QTabWidget()
        tabs.addTab(self.create_work_hours_tab(), "⏰ Pracovní doba")
        tabs.addTab(self.create_defaults_tab(), "📋 Výchozí hodnoty")
        tabs.addTab(self.create_display_tab(), "👁️ Zobrazení")
        tabs.addTab(self.create_notifications_tab(), "🔔 Notifikace")
        tabs.addTab(self.create_integrations_tab(), "🔗 Integrace")
        tabs.addTab(self.create_permissions_tab(), "🔒 Přístupová práva")

        scroll_layout.addWidget(tabs)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        buttons_panel = self.create_buttons_panel()
        main_layout.addWidget(buttons_panel)

        scroll.setStyleSheet("""
            #settingsScroll {
                background: transparent;
                border: none;
            }
        """)

    def create_top_panel(self):
        panel = QFrame()
        panel.setObjectName("topPanel")
        panel.setFixedHeight(60)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(15, 10, 15, 10)

        title = QLabel("⚙️ Nastavení kalendáře")
        title.setObjectName("panelTitle")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        layout.addStretch()

        self.lbl_status = QLabel("Nastavení načteno")
        self.lbl_status.setObjectName("statusLabel")
        layout.addWidget(self.lbl_status)

        panel.setStyleSheet(f"""
            #topPanel {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}
            #panelTitle {{
                color: {config.COLOR_PRIMARY};
            }}
            #statusLabel {{
                color: #666;
                font-style: italic;
            }}
        """)

        return panel

    def create_work_hours_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        hours_group = QGroupBox("Otevírací hodiny servisu")
        hours_layout = QVBoxLayout(hours_group)

        self.day_widgets = {}
        days = [
            ("Pondělí", "monday"),
            ("Úterý", "tuesday"),
            ("Středa", "wednesday"),
            ("Čtvrtek", "thursday"),
            ("Pátek", "friday"),
            ("Sobota", "saturday"),
            ("Neděle", "sunday")
        ]

        for day_name, day_key in days:
            day_layout = QHBoxLayout()

            chk = QCheckBox(day_name)
            chk.setFixedWidth(120)
            chk.stateChanged.connect(self.on_setting_changed)
            day_layout.addWidget(chk)

            time_from = QTimeEdit()
            time_from.setDisplayFormat("HH:mm")
            time_from.setTime(QTime(8, 0))
            time_from.timeChanged.connect(self.on_setting_changed)
            day_layout.addWidget(time_from)

            day_layout.addWidget(QLabel("-"))

            time_to = QTimeEdit()
            time_to.setDisplayFormat("HH:mm")
            time_to.setTime(QTime(17, 0))
            time_to.timeChanged.connect(self.on_setting_changed)
            day_layout.addWidget(time_to)

            day_layout.addStretch()

            self.day_widgets[day_key] = {
                'checkbox': chk,
                'from': time_from,
                'to': time_to
            }

            hours_layout.addLayout(day_layout)

        layout.addWidget(hours_group)

        breaks_group = QGroupBox("Přestávky")
        breaks_layout = QFormLayout(breaks_group)
        breaks_layout.setSpacing(10)

        self.chk_lunch_break = QCheckBox("Polední přestávka")
        self.chk_lunch_break.setChecked(True)
        self.chk_lunch_break.stateChanged.connect(self.on_setting_changed)
        breaks_layout.addRow("", self.chk_lunch_break)

        lunch_layout = QHBoxLayout()
        self.time_lunch_from = QTimeEdit()
        self.time_lunch_from.setDisplayFormat("HH:mm")
        self.time_lunch_from.setTime(QTime(12, 0))
        self.time_lunch_from.timeChanged.connect(self.on_setting_changed)
        lunch_layout.addWidget(self.time_lunch_from)

        lunch_layout.addWidget(QLabel("-"))

        self.time_lunch_to = QTimeEdit()
        self.time_lunch_to.setDisplayFormat("HH:mm")
        self.time_lunch_to.setTime(QTime(13, 0))
        self.time_lunch_to.timeChanged.connect(self.on_setting_changed)
        lunch_layout.addWidget(self.time_lunch_to)

        lunch_layout.addStretch()
        breaks_layout.addRow("Čas:", lunch_layout)

        layout.addWidget(breaks_group)

        holidays_group = QGroupBox("Svátky a speciální dny")
        holidays_layout = QVBoxLayout(holidays_group)

        self.chk_auto_holidays = QCheckBox("Automaticky importovat české státní svátky")
        self.chk_auto_holidays.setChecked(True)
        self.chk_auto_holidays.stateChanged.connect(self.on_setting_changed)
        holidays_layout.addWidget(self.chk_auto_holidays)

        self.chk_close_holidays = QCheckBox("Zavřít servis ve státní svátky")
        self.chk_close_holidays.setChecked(True)
        self.chk_close_holidays.stateChanged.connect(self.on_setting_changed)
        holidays_layout.addWidget(self.chk_close_holidays)

        btn_manage_holidays = QPushButton("📅 Spravovat svátky")
        btn_manage_holidays.clicked.connect(self.manage_holidays)
        holidays_layout.addWidget(btn_manage_holidays)

        layout.addWidget(holidays_group)

        layout.addStretch()

        return tab

    def create_defaults_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        event_defaults = QGroupBox("Výchozí hodnoty události")
        event_layout = QFormLayout(event_defaults)
        event_layout.setSpacing(12)

        duration_layout = QHBoxLayout()
        self.spin_default_duration = QSpinBox()
        self.spin_default_duration.setRange(15, 480)
        self.spin_default_duration.setValue(60)
        self.spin_default_duration.setSingleStep(15)
        self.spin_default_duration.setSuffix(" minut")
        self.spin_default_duration.valueChanged.connect(self.on_setting_changed)
        duration_layout.addWidget(self.spin_default_duration)

        self.cmb_duration_preset = QComboBox()
        self.cmb_duration_preset.addItem("Vlastní", None)
        self.cmb_duration_preset.addItem("15 min", 15)
        self.cmb_duration_preset.addItem("30 min", 30)
        self.cmb_duration_preset.addItem("1 hodina", 60)
        self.cmb_duration_preset.addItem("2 hodiny", 120)
        self.cmb_duration_preset.addItem("Půl dne", 240)
        self.cmb_duration_preset.currentIndexChanged.connect(self.on_duration_preset_changed)
        duration_layout.addWidget(self.cmb_duration_preset)

        duration_layout.addStretch()
        event_layout.addRow("Délka události:", duration_layout)

        self.cmb_default_type = QComboBox()
        self.cmb_default_type.addItem("🔧 Servisní termín", "service")
        self.cmb_default_type.addItem("📞 Schůzka se zákazníkem", "meeting")
        self.cmb_default_type.addItem("📦 Příjem dílu", "delivery")
        self.cmb_default_type.addItem("🚗 Předání vozidla", "handover")
        self.cmb_default_type.addItem("⏰ Připomínka", "reminder")
        self.cmb_default_type.addItem("📅 Jiné", "other")
        self.cmb_default_type.currentIndexChanged.connect(self.on_setting_changed)
        event_layout.addRow("Typ události:", self.cmb_default_type)

        self.cmb_default_priority = QComboBox()
        self.cmb_default_priority.addItem("🟢 Nízká", 1)
        self.cmb_default_priority.addItem("🟡 Střední", 2)
        self.cmb_default_priority.addItem("🔴 Vysoká", 3)
        self.cmb_default_priority.setCurrentIndex(1)
        self.cmb_default_priority.currentIndexChanged.connect(self.on_setting_changed)
        event_layout.addRow("Priorita:", self.cmb_default_priority)

        self.cmb_default_mechanic = QComboBox()
        self.cmb_default_mechanic.addItem("-- Nepřiřazovat --", None)
        self.cmb_default_mechanic.addItem("🔄 Automaticky (nejméně vytížený)", "auto")
        self.load_mechanics_combo()
        self.cmb_default_mechanic.currentIndexChanged.connect(self.on_setting_changed)
        event_layout.addRow("Mechanik:", self.cmb_default_mechanic)

        layout.addWidget(event_defaults)

        reminder_defaults = QGroupBox("Výchozí připomínky")
        reminder_layout = QFormLayout(reminder_defaults)
        reminder_layout.setSpacing(12)

        self.chk_default_reminder = QCheckBox("Automaticky přidávat připomínku")
        self.chk_default_reminder.setChecked(True)
        self.chk_default_reminder.stateChanged.connect(self.on_setting_changed)
        reminder_layout.addRow("", self.chk_default_reminder)

        self.cmb_reminder_time = QComboBox()
        self.cmb_reminder_time.addItem("15 minut před", 15)
        self.cmb_reminder_time.addItem("30 minut před", 30)
        self.cmb_reminder_time.addItem("1 hodina před", 60)
        self.cmb_reminder_time.addItem("2 hodiny před", 120)
        self.cmb_reminder_time.addItem("1 den před", 1440)
        self.cmb_reminder_time.setCurrentIndex(2)
        self.cmb_reminder_time.currentIndexChanged.connect(self.on_setting_changed)
        reminder_layout.addRow("Čas připomínky:", self.cmb_reminder_time)

        layout.addWidget(reminder_defaults)

        auto_actions = QGroupBox("Automatické akce")
        auto_layout = QVBoxLayout(auto_actions)

        self.chk_auto_create_order = QCheckBox("Automaticky vytvořit zakázku z události")
        self.chk_auto_create_order.stateChanged.connect(self.on_setting_changed)
        auto_layout.addWidget(self.chk_auto_create_order)

        self.chk_auto_confirm = QCheckBox("Automaticky potvrdit online rezervace")
        self.chk_auto_confirm.stateChanged.connect(self.on_setting_changed)
        auto_layout.addWidget(self.chk_auto_confirm)

        self.chk_auto_complete = QCheckBox("Automaticky dokončit události po čase")
        self.chk_auto_complete.stateChanged.connect(self.on_setting_changed)
        auto_layout.addWidget(self.chk_auto_complete)

        layout.addWidget(auto_actions)

        layout.addStretch()

        return tab

    def create_display_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        calendar_display = QGroupBox("Zobrazení kalendáře")
        calendar_layout = QFormLayout(calendar_display)
        calendar_layout.setSpacing(12)

        self.cmb_first_day = QComboBox()
        self.cmb_first_day.addItem("Pondělí", 1)
        self.cmb_first_day.addItem("Neděle", 0)
        self.cmb_first_day.currentIndexChanged.connect(self.on_setting_changed)
        calendar_layout.addRow("První den týdne:", self.cmb_first_day)

        self.cmb_time_format = QComboBox()
        self.cmb_time_format.addItem("24 hodin (14:30)", "24h")
        self.cmb_time_format.addItem("12 hodin (2:30 PM)", "12h")
        self.cmb_time_format.currentIndexChanged.connect(self.on_setting_changed)
        calendar_layout.addRow("Formát času:", self.cmb_time_format)

        self.cmb_default_view = QComboBox()
        self.cmb_default_view.addItem("📅 Měsíční", "month")
        self.cmb_default_view.addItem("📆 Týdenní", "week")
        self.cmb_default_view.addItem("📋 Denní", "day")
        self.cmb_default_view.addItem("📑 Seznam", "list")
        self.cmb_default_view.currentIndexChanged.connect(self.on_setting_changed)
        calendar_layout.addRow("Výchozí zobrazení:", self.cmb_default_view)

        zoom_layout = QHBoxLayout()
        self.spin_zoom = QSpinBox()
        self.spin_zoom.setRange(50, 200)
        self.spin_zoom.setValue(100)
        self.spin_zoom.setSingleStep(10)
        self.spin_zoom.setSuffix(" %")
        self.spin_zoom.valueChanged.connect(self.on_setting_changed)
        zoom_layout.addWidget(self.spin_zoom)

        btn_reset_zoom = QPushButton("Reset")
        btn_reset_zoom.clicked.connect(lambda: self.spin_zoom.setValue(100))
        zoom_layout.addWidget(btn_reset_zoom)

        zoom_layout.addStretch()
        calendar_layout.addRow("Zoom úroveň:", zoom_layout)

        layout.addWidget(calendar_display)

        appearance = QGroupBox("Vzhled")
        appearance_layout = QVBoxLayout(appearance)

        self.chk_show_weekends = QCheckBox("Zobrazovat víkendy")
        self.chk_show_weekends.setChecked(True)
        self.chk_show_weekends.stateChanged.connect(self.on_setting_changed)
        appearance_layout.addWidget(self.chk_show_weekends)

        self.chk_show_week_numbers = QCheckBox("Zobrazovat čísla týdnů")
        self.chk_show_week_numbers.setChecked(True)
        self.chk_show_week_numbers.stateChanged.connect(self.on_setting_changed)
        appearance_layout.addWidget(self.chk_show_week_numbers)

        self.chk_highlight_today = QCheckBox("Zvýraznit dnešní den")
        self.chk_highlight_today.setChecked(True)
        self.chk_highlight_today.stateChanged.connect(self.on_setting_changed)
        appearance_layout.addWidget(self.chk_highlight_today)

        self.chk_show_time_grid = QCheckBox("Zobrazovat časovou mřížku")
        self.chk_show_time_grid.setChecked(True)
        self.chk_show_time_grid.stateChanged.connect(self.on_setting_changed)
        appearance_layout.addWidget(self.chk_show_time_grid)

        self.chk_compact_view = QCheckBox("Kompaktní zobrazení událostí")
        self.chk_compact_view.stateChanged.connect(self.on_setting_changed)
        appearance_layout.addWidget(self.chk_compact_view)

        layout.addWidget(appearance)

        colors = QGroupBox("Barevné schéma")
        colors_layout = QFormLayout(colors)
        colors_layout.setSpacing(10)

        self.cmb_color_scheme = QComboBox()
        self.cmb_color_scheme.addItem("🔵 Modrá (výchozí)", "blue")
        self.cmb_color_scheme.addItem("🟢 Zelená", "green")
        self.cmb_color_scheme.addItem("🟣 Fialová", "purple")
        self.cmb_color_scheme.addItem("🟠 Oranžová", "orange")
        self.cmb_color_scheme.addItem("⚫ Tmavá", "dark")
        self.cmb_color_scheme.currentIndexChanged.connect(self.on_setting_changed)
        colors_layout.addRow("Schéma:", self.cmb_color_scheme)

        self.chk_color_by_type = QCheckBox("Barvy podle typu události")
        self.chk_color_by_type.setChecked(True)
        self.chk_color_by_type.stateChanged.connect(self.on_setting_changed)
        colors_layout.addRow("", self.chk_color_by_type)

        self.chk_color_by_priority = QCheckBox("Barvy podle priority")
        self.chk_color_by_priority.stateChanged.connect(self.on_setting_changed)
        colors_layout.addRow("", self.chk_color_by_priority)

        layout.addWidget(colors)

        layout.addStretch()

        return tab

    def create_notifications_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        email_group = QGroupBox("Email notifikace")
        email_layout = QVBoxLayout(email_group)

        self.chk_email_enabled = QCheckBox("Povolit email notifikace")
        self.chk_email_enabled.setChecked(True)
        self.chk_email_enabled.stateChanged.connect(self.on_setting_changed)
        email_layout.addWidget(self.chk_email_enabled)

        self.chk_email_reminder = QCheckBox("Email připomínka před událostí")
        self.chk_email_reminder.setChecked(True)
        self.chk_email_reminder.stateChanged.connect(self.on_setting_changed)
        email_layout.addWidget(self.chk_email_reminder)

        self.chk_email_confirmation = QCheckBox("Email potvrzení rezervace")
        self.chk_email_confirmation.setChecked(True)
        self.chk_email_confirmation.stateChanged.connect(self.on_setting_changed)
        email_layout.addWidget(self.chk_email_confirmation)

        self.chk_email_cancellation = QCheckBox("Email při zrušení")
        self.chk_email_cancellation.setChecked(True)
        self.chk_email_cancellation.stateChanged.connect(self.on_setting_changed)
        email_layout.addWidget(self.chk_email_cancellation)

        layout.addWidget(email_group)

        sms_group = QGroupBox("SMS notifikace")
        sms_layout = QVBoxLayout(sms_group)

        self.chk_sms_enabled = QCheckBox("Povolit SMS notifikace")
        self.chk_sms_enabled.stateChanged.connect(self.on_setting_changed)
        sms_layout.addWidget(self.chk_sms_enabled)

        self.chk_sms_reminder = QCheckBox("SMS připomínka před událostí")
        self.chk_sms_reminder.stateChanged.connect(self.on_setting_changed)
        sms_layout.addWidget(self.chk_sms_reminder)

        self.chk_sms_confirmation = QCheckBox("SMS potvrzení rezervace")
        self.chk_sms_confirmation.stateChanged.connect(self.on_setting_changed)
        sms_layout.addWidget(self.chk_sms_confirmation)

        sms_note = QLabel("⚠️ SMS vyžaduje konfiguraci SMS brány")
        sms_note.setStyleSheet("color: #856404; font-style: italic;")
        sms_layout.addWidget(sms_note)

        layout.addWidget(sms_group)

        auto_reminders = QGroupBox("Automatické připomínky")
        auto_layout = QVBoxLayout(auto_reminders)

        self.chk_auto_stk = QCheckBox("Automatické připomínky STK (30 dní předem)")
        self.chk_auto_stk.setChecked(True)
        self.chk_auto_stk.stateChanged.connect(self.on_setting_changed)
        auto_layout.addWidget(self.chk_auto_stk)

        self.chk_auto_insurance = QCheckBox("Automatické připomínky pojištění")
        self.chk_auto_insurance.setChecked(True)
        self.chk_auto_insurance.stateChanged.connect(self.on_setting_changed)
        auto_layout.addWidget(self.chk_auto_insurance)

        self.chk_auto_service = QCheckBox("Automatické připomínky pravidelného servisu")
        self.chk_auto_service.stateChanged.connect(self.on_setting_changed)
        auto_layout.addWidget(self.chk_auto_service)

        service_interval_layout = QHBoxLayout()
        service_interval_layout.addWidget(QLabel("Interval servisu:"))
        self.spin_service_interval = QSpinBox()
        self.spin_service_interval.setRange(1, 24)
        self.spin_service_interval.setValue(6)
        self.spin_service_interval.setSuffix(" měsíců")
        self.spin_service_interval.valueChanged.connect(self.on_setting_changed)
        service_interval_layout.addWidget(self.spin_service_interval)
        service_interval_layout.addStretch()
        auto_layout.addLayout(service_interval_layout)

        layout.addWidget(auto_reminders)

        timing_group = QGroupBox("Čas notifikací")
        timing_layout = QFormLayout(timing_group)
        timing_layout.setSpacing(10)

        self.cmb_notify_before_1 = QComboBox()
        self.cmb_notify_before_1.addItem("1 den", 1440)
        self.cmb_notify_before_1.addItem("2 dny", 2880)
        self.cmb_notify_before_1.addItem("3 dny", 4320)
        self.cmb_notify_before_1.addItem("1 týden", 10080)
        self.cmb_notify_before_1.currentIndexChanged.connect(self.on_setting_changed)
        timing_layout.addRow("První připomínka:", self.cmb_notify_before_1)

        self.cmb_notify_before_2 = QComboBox()
        self.cmb_notify_before_2.addItem("1 hodina", 60)
        self.cmb_notify_before_2.addItem("2 hodiny", 120)
        self.cmb_notify_before_2.addItem("3 hodiny", 180)
        self.cmb_notify_before_2.currentIndexChanged.connect(self.on_setting_changed)
        timing_layout.addRow("Druhá připomínka:", self.cmb_notify_before_2)

        layout.addWidget(timing_group)

        layout.addStretch()

        return tab

    def create_integrations_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        google_group = QGroupBox("Google Calendar")
        google_layout = QVBoxLayout(google_group)

        self.chk_google_sync = QCheckBox("Synchronizovat s Google Calendar")
        self.chk_google_sync.stateChanged.connect(self.on_setting_changed)
        google_layout.addWidget(self.chk_google_sync)

        google_form = QFormLayout()
        google_form.setSpacing(10)

        self.txt_google_calendar_id = QLineEdit()
        self.txt_google_calendar_id.setPlaceholderText("calendar-id@group.calendar.google.com")
        self.txt_google_calendar_id.setEnabled(False)
        google_form.addRow("Calendar ID:", self.txt_google_calendar_id)

        google_layout.addLayout(google_form)

        google_buttons = QHBoxLayout()

        self.btn_google_connect = QPushButton("🔗 Připojit účet")
        self.btn_google_connect.clicked.connect(self.connect_google)
        google_buttons.addWidget(self.btn_google_connect)

        self.btn_google_sync_now = QPushButton("🔄 Synchronizovat nyní")
        self.btn_google_sync_now.setEnabled(False)
        self.btn_google_sync_now.clicked.connect(self.sync_google_now)
        google_buttons.addWidget(self.btn_google_sync_now)

        google_buttons.addStretch()
        google_layout.addLayout(google_buttons)

        google_note = QLabel("⚠️ Vyžaduje konfiguraci Google API credentials")
        google_note.setStyleSheet("color: #856404; font-style: italic;")
        google_layout.addWidget(google_note)

        layout.addWidget(google_group)

        import_group = QGroupBox("Import dat")
        import_layout = QVBoxLayout(import_group)

        import_buttons = QHBoxLayout()

        btn_import_holidays = QPushButton("📅 Import svátků")
        btn_import_holidays.clicked.connect(self.import_holidays)
        import_buttons.addWidget(btn_import_holidays)

        btn_import_ical = QPushButton("📥 Import z iCalendar")
        btn_import_ical.clicked.connect(self.import_ical)
        import_buttons.addWidget(btn_import_ical)

        btn_import_csv = QPushButton("📋 Import z CSV")
        btn_import_csv.clicked.connect(self.import_csv)
        import_buttons.addWidget(btn_import_csv)

        import_buttons.addStretch()
        import_layout.addLayout(import_buttons)

        layout.addWidget(import_group)

        export_group = QGroupBox("Export nastavení")
        export_layout = QVBoxLayout(export_group)

        export_buttons = QHBoxLayout()

        btn_export_settings = QPushButton("💾 Exportovat nastavení")
        btn_export_settings.clicked.connect(self.export_settings)
        export_buttons.addWidget(btn_export_settings)

        btn_import_settings = QPushButton("📥 Importovat nastavení")
        btn_import_settings.clicked.connect(self.import_settings)
        export_buttons.addWidget(btn_import_settings)

        btn_reset_defaults = QPushButton("🔄 Obnovit výchozí")
        btn_reset_defaults.clicked.connect(self.reset_to_defaults)
        export_buttons.addWidget(btn_reset_defaults)

        export_buttons.addStretch()
        export_layout.addLayout(export_buttons)

        layout.addWidget(export_group)

        api_group = QGroupBox("API nastavení")
        api_layout = QFormLayout(api_group)
        api_layout.setSpacing(10)

        self.txt_api_key = QLineEdit()
        self.txt_api_key.setPlaceholderText("Váš API klíč")
        self.txt_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addRow("API klíč:", self.txt_api_key)

        self.txt_webhook_url = QLineEdit()
        self.txt_webhook_url.setPlaceholderText("https://vas-server.cz/webhook")
        api_layout.addRow("Webhook URL:", self.txt_webhook_url)

        layout.addWidget(api_group)

        layout.addStretch()

        return tab

    def create_permissions_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        events_permissions = QGroupBox("Správa událostí")
        events_layout = QFormLayout(events_permissions)
        events_layout.setSpacing(12)

        self.cmb_create_events = QComboBox()
        self.cmb_create_events.addItem("Všichni uživatelé", "all")
        self.cmb_create_events.addItem("Pouze mechanici a admin", "mechanic")
        self.cmb_create_events.addItem("Pouze admin", "admin")
        self.cmb_create_events.currentIndexChanged.connect(self.on_setting_changed)
        events_layout.addRow("Kdo může vytvářet události:", self.cmb_create_events)

        self.cmb_edit_events = QComboBox()
        self.cmb_edit_events.addItem("Vlastní události + admin", "own")
        self.cmb_edit_events.addItem("Všechny události", "all")
        self.cmb_edit_events.addItem("Pouze admin", "admin")
        self.cmb_edit_events.currentIndexChanged.connect(self.on_setting_changed)
        events_layout.addRow("Kdo může editovat události:", self.cmb_edit_events)

        self.cmb_delete_events = QComboBox()
        self.cmb_delete_events.addItem("Pouze admin", "admin")
        self.cmb_delete_events.addItem("Mechanici a admin", "mechanic")
        self.cmb_delete_events.addItem("Všichni uživatelé", "all")
        self.cmb_delete_events.currentIndexChanged.connect(self.on_setting_changed)
        events_layout.addRow("Kdo může mazat události:", self.cmb_delete_events)

        layout.addWidget(events_permissions)

        view_permissions = QGroupBox("Zobrazení")
        view_layout = QFormLayout(view_permissions)
        view_layout.setSpacing(12)

        self.cmb_view_all_mechanics = QComboBox()
        self.cmb_view_all_mechanics.addItem("Všichni uživatelé", "all")
        self.cmb_view_all_mechanics.addItem("Pouze mechanici a admin", "mechanic")
        self.cmb_view_all_mechanics.addItem("Pouze admin", "admin")
        self.cmb_view_all_mechanics.currentIndexChanged.connect(self.on_setting_changed)
        view_layout.addRow("Kdo vidí všechny mechaniky:", self.cmb_view_all_mechanics)

        self.cmb_view_customer_info = QComboBox()
        self.cmb_view_customer_info.addItem("Všichni uživatelé", "all")
        self.cmb_view_customer_info.addItem("Pouze mechanici a admin", "mechanic")
        self.cmb_view_customer_info.addItem("Pouze admin", "admin")
        self.cmb_view_customer_info.currentIndexChanged.connect(self.on_setting_changed)
        view_layout.addRow("Kdo vidí kontakty zákazníků:", self.cmb_view_customer_info)

        self.cmb_view_reports = QComboBox()
        self.cmb_view_reports.addItem("Všichni uživatelé", "all")
        self.cmb_view_reports.addItem("Pouze admin", "admin")
        self.cmb_view_reports.currentIndexChanged.connect(self.on_setting_changed)
        view_layout.addRow("Kdo vidí reporty:", self.cmb_view_reports)

        layout.addWidget(view_permissions)

        settings_permissions = QGroupBox("Nastavení")
        settings_layout = QFormLayout(settings_permissions)
        settings_layout.setSpacing(12)

        self.cmb_change_settings = QComboBox()
        self.cmb_change_settings.addItem("Pouze admin", "admin")
        self.cmb_change_settings.addItem("Mechanici a admin", "mechanic")
        self.cmb_change_settings.currentIndexChanged.connect(self.on_setting_changed)
        settings_layout.addRow("Kdo může měnit nastavení:", self.cmb_change_settings)

        self.cmb_manage_availability = QComboBox()
        self.cmb_manage_availability.addItem("Pouze admin", "admin")
        self.cmb_manage_availability.addItem("Každý vlastní dostupnost", "own")
        self.cmb_manage_availability.currentIndexChanged.connect(self.on_setting_changed)
        settings_layout.addRow("Kdo může měnit dostupnost:", self.cmb_manage_availability)

        self.cmb_manage_bookings = QComboBox()
        self.cmb_manage_bookings.addItem("Pouze admin", "admin")
        self.cmb_manage_bookings.addItem("Mechanici a admin", "mechanic")
        self.cmb_manage_bookings.addItem("Všichni uživatelé", "all")
        self.cmb_manage_bookings.currentIndexChanged.connect(self.on_setting_changed)
        settings_layout.addRow("Kdo spravuje online rezervace:", self.cmb_manage_bookings)

        layout.addWidget(settings_permissions)

        logging_group = QGroupBox("Logování a audit")
        logging_layout = QVBoxLayout(logging_group)

        self.chk_log_all_changes = QCheckBox("Logovat všechny změny v kalendáři")
        self.chk_log_all_changes.setChecked(True)
        self.chk_log_all_changes.stateChanged.connect(self.on_setting_changed)
        logging_layout.addWidget(self.chk_log_all_changes)

        self.chk_log_login = QCheckBox("Logovat přihlášení uživatelů")
        self.chk_log_login.setChecked(True)
        self.chk_log_login.stateChanged.connect(self.on_setting_changed)
        logging_layout.addWidget(self.chk_log_login)

        self.chk_log_exports = QCheckBox("Logovat exporty dat")
        self.chk_log_exports.setChecked(True)
        self.chk_log_exports.stateChanged.connect(self.on_setting_changed)
        logging_layout.addWidget(self.chk_log_exports)

        btn_view_logs = QPushButton("📋 Zobrazit logy")
        btn_view_logs.clicked.connect(self.view_logs)
        logging_layout.addWidget(btn_view_logs)

        layout.addWidget(logging_group)

        layout.addStretch()

        return tab

    def create_buttons_panel(self):
        panel = QFrame()
        panel.setObjectName("buttonsPanel")
        panel.setFixedHeight(60)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(15, 10, 15, 10)

        self.btn_reset = QPushButton("🔄 Obnovit výchozí")
        self.btn_reset.clicked.connect(self.reset_to_defaults)
        layout.addWidget(self.btn_reset)

        layout.addStretch()

        self.lbl_unsaved = QLabel("⚠️ Neuložené změny")
        self.lbl_unsaved.setObjectName("unsavedLabel")
        self.lbl_unsaved.setVisible(False)
        layout.addWidget(self.lbl_unsaved)

        self.btn_cancel = QPushButton("❌ Zrušit změny")
        self.btn_cancel.clicked.connect(self.cancel_changes)
        layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("💾 Uložit nastavení")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.clicked.connect(self.save_settings)
        layout.addWidget(self.btn_save)

        panel.setStyleSheet(f"""
            #buttonsPanel {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}
            #primaryButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 25px;
                font-weight: bold;
            }}
            #primaryButton:hover {{
                background-color: #2980b9;
            }}
            #unsavedLabel {{
                color: {config.COLOR_WARNING};
                font-weight: bold;
            }}
            QPushButton {{
                padding: 8px 15px;
            }}
        """)

        return panel

    def load_mechanics_combo(self):
        mechanics = db.fetch_all("""
            SELECT id, full_name FROM users
            WHERE role IN ('mechanik', 'admin') AND active = 1
            ORDER BY full_name
        """)

        for m in mechanics:
            self.cmb_default_mechanic.addItem(f"👤 {m['full_name']}", m['id'])

    def on_setting_changed(self):
        self.lbl_unsaved.setVisible(True)
        self.settings_changed.emit()

    def on_duration_preset_changed(self):
        preset = self.cmb_duration_preset.currentData()
        if preset:
            self.spin_default_duration.setValue(preset)

    def get_setting(self, key, default=None):
        """Načte hodnotu nastavení z databáze"""
        result = db.fetch_one(
            "SELECT setting_value FROM calendar_settings WHERE setting_key = ?",
            (key,)
        )
        if result:
            return result['setting_value']
        return default

    def set_setting(self, key, value):
        """Uloží hodnotu nastavení do databáze"""
        existing = db.fetch_one(
            "SELECT id FROM calendar_settings WHERE setting_key = ?",
            (key,)
        )

        if existing:
            db.execute_query(
                "UPDATE calendar_settings SET setting_value = ? WHERE setting_key = ?",
                (str(value), key)
            )
        else:
            db.execute_query(
                "INSERT INTO calendar_settings (setting_key, setting_value) VALUES (?, ?)",
                (key, str(value))
            )

    def load_settings(self):
        """Načte všechna nastavení z databáze"""

        work_start = self.get_setting('work_start_time', '08:00')
        work_end = self.get_setting('work_end_time', '17:00')
        sat_start = self.get_setting('saturday_start_time', '08:00')
        sat_end = self.get_setting('saturday_end_time', '12:00')
        sunday_closed = self.get_setting('sunday_closed', '1')

        for day_key, widgets in self.day_widgets.items():
            if day_key == 'sunday':
                widgets['checkbox'].setChecked(sunday_closed != '1')
                widgets['from'].setTime(QTime(8, 0))
                widgets['to'].setTime(QTime(12, 0))
            elif day_key == 'saturday':
                widgets['checkbox'].setChecked(True)
                widgets['from'].setTime(QTime.fromString(sat_start, "HH:mm"))
                widgets['to'].setTime(QTime.fromString(sat_end, "HH:mm"))
            else:
                widgets['checkbox'].setChecked(True)
                widgets['from'].setTime(QTime.fromString(work_start, "HH:mm"))
                widgets['to'].setTime(QTime.fromString(work_end, "HH:mm"))

        duration = int(self.get_setting('default_event_duration', '60'))
        self.spin_default_duration.setValue(duration)

        event_type = self.get_setting('default_event_type', 'service')
        for i in range(self.cmb_default_type.count()):
            if self.cmb_default_type.itemData(i) == event_type:
                self.cmb_default_type.setCurrentIndex(i)
                break

        reminder_mins = int(self.get_setting('default_reminder_minutes', '60'))
        for i in range(self.cmb_reminder_time.count()):
            if self.cmb_reminder_time.itemData(i) == reminder_mins:
                self.cmb_reminder_time.setCurrentIndex(i)
                break

        first_day = int(self.get_setting('first_day_of_week', '1'))
        for i in range(self.cmb_first_day.count()):
            if self.cmb_first_day.itemData(i) == first_day:
                self.cmb_first_day.setCurrentIndex(i)
                break

        show_weekends = self.get_setting('show_weekends', '1') == '1'
        self.chk_show_weekends.setChecked(show_weekends)

        auto_reminders = self.get_setting('auto_reminders_enabled', '1') == '1'
        self.chk_default_reminder.setChecked(auto_reminders)

        sms_enabled = self.get_setting('sms_reminders_enabled', '0') == '1'
        self.chk_sms_enabled.setChecked(sms_enabled)

        email_enabled = self.get_setting('email_reminders_enabled', '1') == '1'
        self.chk_email_enabled.setChecked(email_enabled)

        self.lbl_unsaved.setVisible(False)
        self.lbl_status.setText("Nastavení načteno")

    def save_settings(self):
        """Uloží všechna nastavení do databáze"""
        try:
            mon_widgets = self.day_widgets['monday']
            self.set_setting('work_start_time', mon_widgets['from'].time().toString("HH:mm"))
            self.set_setting('work_end_time', mon_widgets['to'].time().toString("HH:mm"))

            sat_widgets = self.day_widgets['saturday']
            self.set_setting('saturday_start_time', sat_widgets['from'].time().toString("HH:mm"))
            self.set_setting('saturday_end_time', sat_widgets['to'].time().toString("HH:mm"))

            sun_closed = '0' if self.day_widgets['sunday']['checkbox'].isChecked() else '1'
            self.set_setting('sunday_closed', sun_closed)

            self.set_setting('default_event_duration', str(self.spin_default_duration.value()))
            self.set_setting('default_event_type', self.cmb_default_type.currentData())
            self.set_setting('default_reminder_minutes', str(self.cmb_reminder_time.currentData()))

            self.set_setting('first_day_of_week', str(self.cmb_first_day.currentData()))
            self.set_setting('time_slot_interval', str(self.spin_default_duration.value()))
            self.set_setting('show_weekends', '1' if self.chk_show_weekends.isChecked() else '0')

            self.set_setting('auto_reminders_enabled', '1' if self.chk_default_reminder.isChecked() else '0')
            self.set_setting('sms_reminders_enabled', '1' if self.chk_sms_enabled.isChecked() else '0')
            self.set_setting('email_reminders_enabled', '1' if self.chk_email_enabled.isChecked() else '0')

            self.set_setting('default_priority', str(self.cmb_default_priority.currentData()))
            self.set_setting('default_view', self.cmb_default_view.currentData())
            self.set_setting('zoom_level', str(self.spin_zoom.value()))
            self.set_setting('time_format', self.cmb_time_format.currentData())
            self.set_setting('color_scheme', self.cmb_color_scheme.currentData())

            self.set_setting('auto_stk_reminders', '1' if self.chk_auto_stk.isChecked() else '0')
            self.set_setting('auto_insurance_reminders', '1' if self.chk_auto_insurance.isChecked() else '0')
            self.set_setting('service_interval_months', str(self.spin_service_interval.value()))

            self.set_setting('perm_create_events', self.cmb_create_events.currentData())
            self.set_setting('perm_edit_events', self.cmb_edit_events.currentData())
            self.set_setting('perm_delete_events', self.cmb_delete_events.currentData())
            self.set_setting('perm_view_mechanics', self.cmb_view_all_mechanics.currentData())
            self.set_setting('perm_view_customers', self.cmb_view_customer_info.currentData())
            self.set_setting('perm_view_reports', self.cmb_view_reports.currentData())

            self.lbl_unsaved.setVisible(False)
            self.lbl_status.setText("✅ Nastavení uloženo")

            QMessageBox.information(self, "Úspěch", "Nastavení bylo úspěšně uloženo.")

            self.settings_saved.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při ukládání nastavení: {e}")

    def cancel_changes(self):
        reply = QMessageBox.question(
            self,
            "Potvrzení",
            "Opravdu chcete zrušit všechny neuložené změny?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.load_settings()

    def reset_to_defaults(self):
        reply = QMessageBox.question(
            self,
            "Potvrzení",
            "Opravdu chcete obnovit výchozí nastavení?\n\nToto přepíše všechna vaše nastavení.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            default_days = {
                'monday': True, 'tuesday': True, 'wednesday': True,
                'thursday': True, 'friday': True, 'saturday': True, 'sunday': False
            }

            for day_key, widgets in self.day_widgets.items():
                widgets['checkbox'].setChecked(default_days.get(day_key, False))
                if day_key == 'saturday':
                    widgets['from'].setTime(QTime(8, 0))
                    widgets['to'].setTime(QTime(12, 0))
                elif day_key == 'sunday':
                    widgets['from'].setTime(QTime(8, 0))
                    widgets['to'].setTime(QTime(12, 0))
                else:
                    widgets['from'].setTime(QTime(8, 0))
                    widgets['to'].setTime(QTime(17, 0))

            self.chk_lunch_break.setChecked(True)
            self.time_lunch_from.setTime(QTime(12, 0))
            self.time_lunch_to.setTime(QTime(13, 0))

            self.spin_default_duration.setValue(60)
            self.cmb_default_type.setCurrentIndex(0)
            self.cmb_default_priority.setCurrentIndex(1)
            self.cmb_default_mechanic.setCurrentIndex(0)

            self.spin_zoom.setValue(100)
            self.chk_show_weekends.setChecked(True)
            self.chk_show_week_numbers.setChecked(True)
            self.chk_highlight_today.setChecked(True)

            self.lbl_unsaved.setVisible(True)
            self.lbl_status.setText("Výchozí nastavení obnoveno")

    def manage_holidays(self):
        QMessageBox.information(
            self,
            "Správa svátků",
            "Otevře se dialog pro správu svátků a speciálních dnů."
        )

    def connect_google(self):
        QMessageBox.information(
            self,
            "Google Calendar",
            "Pro připojení Google Calendar je potřeba:\n\n"
            "1. Vytvořit projekt v Google Cloud Console\n"
            "2. Povolit Google Calendar API\n"
            "3. Stáhnout credentials.json\n"
            "4. Autorizovat aplikaci\n\n"
            "Podrobnosti v dokumentaci."
        )

    def sync_google_now(self):
        QMessageBox.information(self, "Synchronizace", "Synchronizace s Google Calendar probíhá...")

    def import_holidays(self):
        QMessageBox.information(
            self,
            "Import svátků",
            "Budou importovány české státní svátky pro aktuální rok."
        )

    def import_ical(self):
        QMessageBox.information(
            self,
            "Import iCalendar",
            "Vyberte .ics soubor pro import událostí do kalendáře."
        )

    def import_csv(self):
        QMessageBox.information(
            self,
            "Import CSV",
            "Vyberte CSV soubor s událostmi.\n\n"
            "Formát: datum;čas;název;typ;popis"
        )

    def export_settings(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export nastavení",
            "calendar_settings.json",
            "JSON soubory (*.json)"
        )

        if file_path:
            try:
                all_settings = db.fetch_all("SELECT setting_key, setting_value FROM calendar_settings")
                settings_dict = {s['setting_key']: s['setting_value'] for s in all_settings}

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(settings_dict, f, ensure_ascii=False, indent=2)

                QMessageBox.information(self, "Export", f"Nastavení exportováno do:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Chyba při exportu: {e}")

    def import_settings(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import nastavení",
            "",
            "JSON soubory (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                for key, value in settings.items():
                    self.set_setting(key, value)

                self.load_settings()
                self.lbl_unsaved.setVisible(False)

                QMessageBox.information(self, "Import", "Nastavení bylo importováno a uloženo.")
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Chyba při importu: {e}")

    def view_logs(self):
        QMessageBox.information(
            self,
            "Logy",
            "Zobrazí se historie změn v kalendáři.\n\n"
            "Logy obsahují informace o:\n"
            "- Vytváření událostí\n"
            "- Editaci událostí\n"
            "- Mazání událostí\n"
            "- Změnách nastavení\n"
            "- Přihlášení uživatelů"
        )
