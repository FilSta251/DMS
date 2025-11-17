# -*- coding: utf-8 -*-
"""
Hlavní modul kalendáře - správa servisních termínů
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QPushButton, QLabel, QComboBox, QFrame, QSplitter,
    QMessageBox, QToolButton, QMenu
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QAction
from datetime import datetime, date, timedelta
from database_manager import db
import config


class CalendarModule(QWidget):
    """Hlavní widget modulu kalendář"""

    event_selected = pyqtSignal(int)
    date_selected = pyqtSignal(object)
    view_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_date = QDate.currentDate()
        self.selected_mechanic_id = None
        self.selected_event_type = None
        self.current_view = "month"

        self.init_ui()
        self.load_filters()
        self.refresh()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        self.create_top_panel(main_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        splitter.setSizes([250, 1000])

        main_layout.addWidget(splitter)

        self.create_bottom_panel(main_layout)

        self.set_styles()

    def create_top_panel(self, parent_layout):
        top_frame = QFrame()
        top_frame.setObjectName("topPanel")
        top_frame.setFixedHeight(70)
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(15, 10, 15, 10)

        view_frame = QFrame()
        view_layout = QHBoxLayout(view_frame)
        view_layout.setContentsMargins(0, 0, 0, 0)
        view_layout.setSpacing(5)

        self.btn_month = QPushButton("📅 Měsíc")
        self.btn_month.setCheckable(True)
        self.btn_month.setChecked(True)
        self.btn_month.clicked.connect(lambda: self.switch_view("month"))

        self.btn_week = QPushButton("📊 Týden")
        self.btn_week.setCheckable(True)
        self.btn_week.clicked.connect(lambda: self.switch_view("week"))

        self.btn_day = QPushButton("📋 Den")
        self.btn_day.setCheckable(True)
        self.btn_day.clicked.connect(lambda: self.switch_view("day"))

        self.btn_list = QPushButton("📝 Seznam")
        self.btn_list.setCheckable(True)
        self.btn_list.clicked.connect(lambda: self.switch_view("list"))

        for btn in [self.btn_month, self.btn_week, self.btn_day, self.btn_list]:
            btn.setObjectName("viewButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(40)
            view_layout.addWidget(btn)

        top_layout.addWidget(view_frame)

        nav_frame = QFrame()
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(10)

        self.btn_prev = QPushButton("◀")
        self.btn_prev.setObjectName("navButton")
        self.btn_prev.setFixedSize(40, 40)
        self.btn_prev.clicked.connect(self.navigate_prev)

        self.btn_today = QPushButton("Dnes")
        self.btn_today.setObjectName("todayButton")
        self.btn_today.setFixedHeight(40)
        self.btn_today.clicked.connect(self.navigate_today)

        self.lbl_current_period = QLabel()
        self.lbl_current_period.setObjectName("periodLabel")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.lbl_current_period.setFont(font)
        self.lbl_current_period.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_current_period.setMinimumWidth(250)

        self.btn_next = QPushButton("▶")
        self.btn_next.setObjectName("navButton")
        self.btn_next.setFixedSize(40, 40)
        self.btn_next.clicked.connect(self.navigate_next)

        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.btn_today)
        nav_layout.addWidget(self.lbl_current_period)
        nav_layout.addWidget(self.btn_next)

        top_layout.addWidget(nav_frame)
        top_layout.addStretch()

        actions_frame = QFrame()
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(10)

        self.btn_new_event = QPushButton("➕ Nová událost")
        self.btn_new_event.setObjectName("primaryButton")
        self.btn_new_event.setFixedHeight(40)
        self.btn_new_event.clicked.connect(self.create_new_event)

        self.btn_export = QToolButton()
        self.btn_export.setText("📤 Export")
        self.btn_export.setObjectName("actionButton")
        self.btn_export.setFixedHeight(40)
        self.btn_export.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        export_menu = QMenu(self.btn_export)
        export_menu.addAction("📄 Export do PDF", self.export_pdf)
        export_menu.addAction("📊 Export do Excel", self.export_excel)
        export_menu.addAction("📅 Export do iCalendar", self.export_icalendar)
        self.btn_export.setMenu(export_menu)

        self.btn_print = QPushButton("🖨️ Tisk")
        self.btn_print.setObjectName("actionButton")
        self.btn_print.setFixedHeight(40)
        self.btn_print.clicked.connect(self.print_calendar)

        actions_layout.addWidget(self.btn_new_event)
        actions_layout.addWidget(self.btn_export)
        actions_layout.addWidget(self.btn_print)

        top_layout.addWidget(actions_frame)

        parent_layout.addWidget(top_frame)

    def create_left_panel(self):
        left_frame = QFrame()
        left_frame.setObjectName("leftPanel")
        left_frame.setMinimumWidth(230)
        left_frame.setMaximumWidth(300)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(15)

        mini_cal_label = QLabel("📅 Rychlá navigace")
        mini_cal_label.setObjectName("sectionLabel")
        left_layout.addWidget(mini_cal_label)

        filters_label = QLabel("🔍 Filtry")
        filters_label.setObjectName("sectionLabel")
        left_layout.addWidget(filters_label)

        mechanic_label = QLabel("Mechanik:")
        left_layout.addWidget(mechanic_label)

        self.cmb_mechanic = QComboBox()
        self.cmb_mechanic.setObjectName("filterCombo")
        self.cmb_mechanic.addItem("👥 Všichni mechanici", None)
        self.cmb_mechanic.currentIndexChanged.connect(self.on_filter_changed)
        left_layout.addWidget(self.cmb_mechanic)

        type_label = QLabel("Typ události:")
        left_layout.addWidget(type_label)

        self.cmb_event_type = QComboBox()
        self.cmb_event_type.setObjectName("filterCombo")
        self.cmb_event_type.addItem("📋 Všechny typy", None)
        self.cmb_event_type.addItem("🔧 Servisní termín", "service")
        self.cmb_event_type.addItem("📞 Schůzka", "meeting")
        self.cmb_event_type.addItem("📦 Příjem dílu", "delivery")
        self.cmb_event_type.addItem("🚗 Předání vozidla", "handover")
        self.cmb_event_type.addItem("⏰ Připomínka", "reminder")
        self.cmb_event_type.addItem("📅 Jiné", "other")
        self.cmb_event_type.currentIndexChanged.connect(self.on_filter_changed)
        left_layout.addWidget(self.cmb_event_type)

        status_label = QLabel("Stav:")
        left_layout.addWidget(status_label)

        self.cmb_status = QComboBox()
        self.cmb_status.setObjectName("filterCombo")
        self.cmb_status.addItem("📊 Všechny stavy", None)
        self.cmb_status.addItem("📅 Naplánováno", "scheduled")
        self.cmb_status.addItem("✅ Potvrzeno", "confirmed")
        self.cmb_status.addItem("🔄 Probíhá", "in_progress")
        self.cmb_status.addItem("✔️ Dokončeno", "completed")
        self.cmb_status.addItem("❌ Zrušeno", "cancelled")
        self.cmb_status.currentIndexChanged.connect(self.on_filter_changed)
        left_layout.addWidget(self.cmb_status)

        self.btn_reset_filters = QPushButton("🔄 Resetovat filtry")
        self.btn_reset_filters.setObjectName("secondaryButton")
        self.btn_reset_filters.clicked.connect(self.reset_filters)
        left_layout.addWidget(self.btn_reset_filters)

        left_layout.addSpacing(20)

        stats_label = QLabel("📊 Statistiky dne")
        stats_label.setObjectName("sectionLabel")
        left_layout.addWidget(stats_label)

        self.stats_frame = QFrame()
        self.stats_frame.setObjectName("statsFrame")
        stats_layout = QVBoxLayout(self.stats_frame)
        stats_layout.setContentsMargins(10, 10, 10, 10)
        stats_layout.setSpacing(8)

        self.lbl_today_events = QLabel("Dnes: 0 událostí")
        self.lbl_week_events = QLabel("Tento týden: 0 událostí")
        self.lbl_pending = QLabel("Čeká na potvrzení: 0")
        self.lbl_capacity = QLabel("Vytížení: 0%")

        for lbl in [self.lbl_today_events, self.lbl_week_events,
                    self.lbl_pending, self.lbl_capacity]:
            lbl.setObjectName("statLabel")
            stats_layout.addWidget(lbl)

        left_layout.addWidget(self.stats_frame)

        left_layout.addStretch()

        nav_label = QLabel("🧭 Navigace")
        nav_label.setObjectName("sectionLabel")
        left_layout.addWidget(nav_label)

        self.btn_mechanics = QPushButton("👷 Vytížení mechaniků")
        self.btn_mechanics.setObjectName("navSectionButton")
        self.btn_mechanics.clicked.connect(lambda: self.switch_view("mechanics"))
        left_layout.addWidget(self.btn_mechanics)

        self.btn_reminders = QPushButton("⏰ Připomínky")
        self.btn_reminders.setObjectName("navSectionButton")
        self.btn_reminders.clicked.connect(lambda: self.switch_view("reminders"))
        left_layout.addWidget(self.btn_reminders)

        self.btn_bookings = QPushButton("📞 Online rezervace")
        self.btn_bookings.setObjectName("navSectionButton")
        self.btn_bookings.clicked.connect(lambda: self.switch_view("bookings"))
        left_layout.addWidget(self.btn_bookings)

        self.btn_reports = QPushButton("📊 Reporty")
        self.btn_reports.setObjectName("navSectionButton")
        self.btn_reports.clicked.connect(lambda: self.switch_view("reports"))
        left_layout.addWidget(self.btn_reports)

        self.btn_settings = QPushButton("⚙️ Nastavení")
        self.btn_settings.setObjectName("navSectionButton")
        self.btn_settings.clicked.connect(lambda: self.switch_view("settings"))
        left_layout.addWidget(self.btn_settings)

        return left_frame

    def create_right_panel(self):
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentStack")

        from .calendar_month_view import CalendarMonthView
        self.month_view = CalendarMonthView(self)
        self.month_view.date_clicked.connect(self.on_date_clicked)
        self.month_view.event_clicked.connect(self.on_event_clicked)
        self.month_view.event_double_clicked.connect(self.edit_event)
        self.content_stack.addWidget(self.month_view)

        from .calendar_week_view import CalendarWeekView
        self.week_view = CalendarWeekView(self)
        self.week_view.event_clicked.connect(self.on_event_clicked)
        self.week_view.event_double_clicked.connect(self.edit_event)
        self.content_stack.addWidget(self.week_view)

        from .calendar_day_view import CalendarDayView
        self.day_view = CalendarDayView(self)
        self.day_view.event_clicked.connect(self.on_event_clicked)
        self.day_view.event_double_clicked.connect(self.edit_event)
        self.day_view.new_event_requested.connect(self.create_new_event_at)
        self.content_stack.addWidget(self.day_view)

        from .calendar_events_list import CalendarEventsList
        self.list_view = CalendarEventsList(self)
        self.list_view.event_selected.connect(self.on_event_clicked)
        self.list_view.event_edit_requested.connect(self.edit_event)
        self.content_stack.addWidget(self.list_view)

        from .calendar_mechanic_capacity import CalendarMechanicCapacity
        self.mechanics_view = CalendarMechanicCapacity(self)
        self.content_stack.addWidget(self.mechanics_view)

        from .calendar_reminders import CalendarReminders
        self.reminders_view = CalendarReminders(self)
        self.content_stack.addWidget(self.reminders_view)

        from .calendar_booking import CalendarBooking
        self.bookings_view = CalendarBooking(self)
        self.content_stack.addWidget(self.bookings_view)

        from .calendar_reports import CalendarReports
        self.reports_view = CalendarReports(self)
        self.content_stack.addWidget(self.reports_view)

        from .calendar_settings import CalendarSettings
        self.settings_view = CalendarSettings(self)
        self.settings_view.settings_saved.connect(self.on_settings_saved)
        self.content_stack.addWidget(self.settings_view)

        return self.content_stack

    def create_bottom_panel(self, parent_layout):
        bottom_frame = QFrame()
        bottom_frame.setObjectName("bottomPanel")
        bottom_frame.setFixedHeight(50)
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(15, 5, 15, 5)

        self.lbl_total_events = QLabel("Celkem událostí: 0")
        self.lbl_total_events.setObjectName("bottomStat")

        self.lbl_free_slots = QLabel("Volné termíny: 0")
        self.lbl_free_slots.setObjectName("bottomStat")

        self.lbl_upcoming = QLabel("Nadcházející: 0")
        self.lbl_upcoming.setObjectName("bottomStat")

        self.lbl_last_update = QLabel(f"Poslední aktualizace: {datetime.now().strftime('%H:%M')}")
        self.lbl_last_update.setObjectName("bottomStat")

        bottom_layout.addWidget(self.lbl_total_events)
        bottom_layout.addWidget(self.lbl_free_slots)
        bottom_layout.addWidget(self.lbl_upcoming)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.lbl_last_update)

        parent_layout.addWidget(bottom_frame)

    def load_filters(self):
        query = """
            SELECT id, full_name FROM users
            WHERE role IN ('mechanik', 'admin') AND active = 1
            ORDER BY full_name
        """
        mechanics = db.fetch_all(query)

        self.cmb_mechanic.clear()
        self.cmb_mechanic.addItem("👥 Všichni mechanici", None)
        for m in mechanics:
            self.cmb_mechanic.addItem(f"👤 {m['full_name']}", m['id'])

    def switch_view(self, view_name):
        self.current_view = view_name

        for btn in [self.btn_month, self.btn_week, self.btn_day, self.btn_list]:
            btn.setChecked(False)

        if view_name == "month":
            self.btn_month.setChecked(True)
            self.content_stack.setCurrentWidget(self.month_view)
        elif view_name == "week":
            self.btn_week.setChecked(True)
            self.content_stack.setCurrentWidget(self.week_view)
        elif view_name == "day":
            self.btn_day.setChecked(True)
            self.content_stack.setCurrentWidget(self.day_view)
        elif view_name == "list":
            self.btn_list.setChecked(True)
            self.content_stack.setCurrentWidget(self.list_view)
        elif view_name == "mechanics":
            self.content_stack.setCurrentWidget(self.mechanics_view)
        elif view_name == "reminders":
            self.content_stack.setCurrentWidget(self.reminders_view)
        elif view_name == "bookings":
            self.content_stack.setCurrentWidget(self.bookings_view)
        elif view_name == "reports":
            self.content_stack.setCurrentWidget(self.reports_view)
        elif view_name == "settings":
            self.content_stack.setCurrentWidget(self.settings_view)

        self.update_period_label()
        self.view_changed.emit(view_name)
        self.refresh()

    def navigate_prev(self):
        if self.current_view == "month":
            self.current_date = self.current_date.addMonths(-1)
        elif self.current_view == "week":
            self.current_date = self.current_date.addDays(-7)
        elif self.current_view == "day":
            self.current_date = self.current_date.addDays(-1)

        self.update_period_label()
        self.refresh()

    def navigate_next(self):
        if self.current_view == "month":
            self.current_date = self.current_date.addMonths(1)
        elif self.current_view == "week":
            self.current_date = self.current_date.addDays(7)
        elif self.current_view == "day":
            self.current_date = self.current_date.addDays(1)

        self.update_period_label()
        self.refresh()

    def navigate_today(self):
        self.current_date = QDate.currentDate()
        self.update_period_label()
        self.refresh()

    def update_period_label(self):
        months_cz = [
            "", "Leden", "Únor", "Březen", "Duben", "Květen", "Červen",
            "Červenec", "Srpen", "Září", "Říjen", "Listopad", "Prosinec"
        ]
        days_cz = ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"]

        if self.current_view == "month":
            month_name = months_cz[self.current_date.month()]
            text = f"{month_name} {self.current_date.year()}"
        elif self.current_view == "week":
            day_of_week = self.current_date.dayOfWeek()
            first_day = self.current_date.addDays(-(day_of_week - 1))
            last_day = first_day.addDays(6)
            text = f"{first_day.day()}.{first_day.month()}. - {last_day.day()}.{last_day.month()}. {last_day.year()}"
        elif self.current_view == "day":
            day_name = days_cz[self.current_date.dayOfWeek() - 1]
            text = f"{day_name} {self.current_date.day()}.{self.current_date.month()}.{self.current_date.year()}"
        else:
            text = f"{months_cz[self.current_date.month()]} {self.current_date.year()}"

        self.lbl_current_period.setText(text)

    def on_filter_changed(self):
        self.selected_mechanic_id = self.cmb_mechanic.currentData()
        self.selected_event_type = self.cmb_event_type.currentData()
        self.refresh()

    def reset_filters(self):
        self.cmb_mechanic.setCurrentIndex(0)
        self.cmb_event_type.setCurrentIndex(0)
        self.cmb_status.setCurrentIndex(0)
        self.refresh()

    def on_date_clicked(self, date):
        self.current_date = date
        self.date_selected.emit(date)

    def on_event_clicked(self, event_id):
        self.event_selected.emit(event_id)

    def create_new_event(self):
        from .calendar_event_dialog import CalendarEventDialog
        dialog = CalendarEventDialog(parent=self)
        if dialog.exec():
            self.refresh()

    def create_new_event_at(self, dt):
        from .calendar_event_dialog import CalendarEventDialog
        dialog = CalendarEventDialog(default_datetime=dt, parent=self)
        if dialog.exec():
            self.refresh()

    def edit_event(self, event_id):
        from .calendar_event_dialog import CalendarEventDialog
        dialog = CalendarEventDialog(event_id=event_id, parent=self)
        if dialog.exec():
            self.refresh()

    def on_settings_saved(self):
        self.refresh()
        QMessageBox.information(self, "Nastavení", "Nastavení kalendáře bylo uloženo.")

    def export_pdf(self):
        from .calendar_export import CalendarExport
        self.switch_view("export")

    def export_excel(self):
        QMessageBox.information(self, "Export", "Export do Excel bude implementován.")

    def export_icalendar(self):
        QMessageBox.information(self, "Export", "Export do iCalendar bude implementován.")

    def print_calendar(self):
        QMessageBox.information(self, "Tisk", "Tisk kalendáře bude implementován.")

    def refresh(self):
        self.load_statistics()
        self.update_period_label()

        if self.current_view == "month" and hasattr(self.month_view, 'refresh'):
            self.month_view.set_current_date(self.current_date)
            self.month_view.set_filters(self.selected_mechanic_id, self.selected_event_type)
            self.month_view.refresh()
        elif self.current_view == "week" and hasattr(self.week_view, 'refresh'):
            self.week_view.set_current_date(self.current_date)
            self.week_view.set_filters(self.selected_mechanic_id, self.selected_event_type)
            self.week_view.refresh()
        elif self.current_view == "day" and hasattr(self.day_view, 'refresh'):
            self.day_view.set_current_date(self.current_date)
            self.day_view.set_filters(self.selected_mechanic_id, self.selected_event_type)
            self.day_view.refresh()
        elif self.current_view == "list" and hasattr(self.list_view, 'refresh'):
            self.list_view.refresh()
        elif self.current_view == "mechanics" and hasattr(self.mechanics_view, 'refresh'):
            self.mechanics_view.refresh()
        elif self.current_view == "reminders" and hasattr(self.reminders_view, 'refresh'):
            self.reminders_view.refresh()
        elif self.current_view == "bookings" and hasattr(self.bookings_view, 'refresh'):
            self.bookings_view.refresh()
        elif self.current_view == "reports" and hasattr(self.reports_view, 'refresh'):
            self.reports_view.refresh()

        self.lbl_last_update.setText(f"Poslední aktualizace: {datetime.now().strftime('%H:%M')}")

    def load_statistics(self):
        today = date.today().isoformat()

        query = """
            SELECT COUNT(*) as count FROM calendar_events
            WHERE DATE(start_datetime) = ? AND status != 'cancelled'
        """
        result = db.fetch_one(query, (today,))
        today_count = result['count'] if result else 0
        self.lbl_today_events.setText(f"Dnes: {today_count} událostí")

        week_start = (date.today() - timedelta(days=date.today().weekday())).isoformat()
        week_end = (date.today() + timedelta(days=6-date.today().weekday())).isoformat()
        query = """
            SELECT COUNT(*) as count FROM calendar_events
            WHERE DATE(start_datetime) BETWEEN ? AND ? AND status != 'cancelled'
        """
        result = db.fetch_one(query, (week_start, week_end))
        week_count = result['count'] if result else 0
        self.lbl_week_events.setText(f"Tento týden: {week_count} událostí")

        query = """
            SELECT COUNT(*) as count FROM calendar_events
            WHERE status = 'scheduled' AND DATE(start_datetime) >= ?
        """
        result = db.fetch_one(query, (today,))
        pending_count = result['count'] if result else 0
        self.lbl_pending.setText(f"Čeká na potvrzení: {pending_count}")

        self.lbl_capacity.setText("Vytížení: --")

        query = """
            SELECT COUNT(*) as count FROM calendar_events
            WHERE strftime('%Y-%m', start_datetime) = ?
        """
        month_str = f"{self.current_date.year()}-{self.current_date.month():02d}"
        result = db.fetch_one(query, (month_str,))
        total_month = result['count'] if result else 0
        self.lbl_total_events.setText(f"Celkem událostí (měsíc): {total_month}")

        query = """
            SELECT COUNT(*) as count FROM calendar_events
            WHERE DATE(start_datetime) > ? AND status NOT IN ('completed', 'cancelled')
        """
        result = db.fetch_one(query, (today,))
        upcoming = result['count'] if result else 0
        self.lbl_upcoming.setText(f"Nadcházející: {upcoming}")

    def set_styles(self):
        self.setStyleSheet(f"""
            QWidget {{
                font-family: 'Segoe UI';
                font-size: 13px;
            }}

            #topPanel {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}

            #leftPanel {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}

            #bottomPanel {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}

            #viewButton {{
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }}

            #viewButton:checked {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border-color: {config.COLOR_SECONDARY};
            }}

            #viewButton:hover {{
                background-color: #e0e0e0;
            }}

            #viewButton:checked:hover {{
                background-color: #2980b9;
            }}

            #navButton {{
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }}

            #navButton:hover {{
                background-color: #e0e0e0;
            }}

            #todayButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: bold;
            }}

            #todayButton:hover {{
                background-color: #229954;
            }}

            #periodLabel {{
                color: {config.COLOR_PRIMARY};
            }}

            #primaryButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }}

            #primaryButton:hover {{
                background-color: #2980b9;
            }}

            #actionButton {{
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 8px 15px;
            }}

            #actionButton:hover {{
                background-color: #e0e0e0;
            }}

            #sectionLabel {{
                font-weight: bold;
                color: {config.COLOR_PRIMARY};
                font-size: 14px;
                padding: 5px 0;
            }}

            #filterCombo {{
                padding: 8px;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                background-color: white;
            }}

            #filterCombo:hover {{
                border-color: {config.COLOR_SECONDARY};
            }}

            #secondaryButton {{
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }}

            #secondaryButton:hover {{
                background-color: #7f8c8d;
            }}

            #statsFrame {{
                background-color: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
            }}

            #statLabel {{
                color: #555;
                padding: 2px 0;
            }}

            #navSectionButton {{
                background-color: transparent;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 10px;
                text-align: left;
            }}

            #navSectionButton:hover {{
                background-color: #f0f0f0;
                border-color: {config.COLOR_SECONDARY};
            }}

            #bottomStat {{
                color: #666;
                font-size: 12px;
            }}

            #contentStack {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}
        """)
