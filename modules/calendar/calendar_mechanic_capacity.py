# -*- coding: utf-8 -*-
"""
Přehled vytížení mechaniků a plánování kapacity
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QLabel,
    QComboBox, QFrame, QSplitter, QProgressBar, QMessageBox,
    QScrollArea, QGridLayout, QGroupBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush
from datetime import datetime, date, timedelta
from database_manager import db
import config


class CapacityProgressBar(QProgressBar):
    """Vlastní progress bar pro zobrazení kapacity"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self.setMinimum(0)
        self.setMaximum(100)
        self.optimal_value = 80

    def setValue(self, value):
        super().setValue(value)
        self.update_style(value)

    def update_style(self, value):
        if value < 50:
            color = config.COLOR_SUCCESS
            bg = "#e8f5e9"
        elif value < 80:
            color = config.COLOR_WARNING
            bg = "#fff8e1"
        elif value <= 100:
            color = "#e67e22"
            bg = "#ffeaa7"
        else:
            color = config.COLOR_DANGER
            bg = "#ffebee"

        self.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #d0d0d0;
                border-radius: 8px;
                background-color: {bg};
                text-align: center;
                font-weight: bold;
                font-size: 12px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 6px;
            }}
        """)


class MechanicCapacityCard(QFrame):
    """Karta s přehledem mechanika"""

    clicked = pyqtSignal(int)

    def __init__(self, mechanic_data, parent=None):
        super().__init__(parent)
        self.mechanic_id = mechanic_data['id']
        self.mechanic_data = mechanic_data

        self.setObjectName("mechanicCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(160)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        name_label = QLabel(f"👤 {self.mechanic_data['full_name']}")
        name_label.setObjectName("mechanicName")
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        name_label.setFont(font)
        header.addWidget(name_label)
        header.addStretch()

        status_text = "🟢 Dostupný" if self.mechanic_data.get('is_available', True) else "🔴 Nedostupný"
        status_label = QLabel(status_text)
        status_label.setObjectName("statusLabel")
        header.addWidget(status_label)

        layout.addLayout(header)

        today_capacity = self.mechanic_data.get('today_capacity', 0)
        today_bar = CapacityProgressBar()
        today_bar.setValue(min(today_capacity, 150))
        today_bar.setFormat(f"Dnes: {today_capacity}%")
        layout.addWidget(today_bar)

        week_capacity = self.mechanic_data.get('week_capacity', 0)
        week_bar = CapacityProgressBar()
        week_bar.setValue(min(week_capacity, 150))
        week_bar.setFormat(f"Týden: {week_capacity}%")
        layout.addWidget(week_bar)

        stats_layout = QHBoxLayout()

        events_today = self.mechanic_data.get('events_today', 0)
        today_label = QLabel(f"📅 Dnes: {events_today}")
        today_label.setObjectName("statLabel")
        stats_layout.addWidget(today_label)

        events_week = self.mechanic_data.get('events_week', 0)
        week_label = QLabel(f"📊 Týden: {events_week}")
        week_label.setObjectName("statLabel")
        stats_layout.addWidget(week_label)

        free_slots = self.mechanic_data.get('free_slots', 0)
        free_label = QLabel(f"🟢 Volno: {free_slots}")
        free_label.setObjectName("statLabel")
        stats_layout.addWidget(free_label)

        layout.addLayout(stats_layout)

        self.setStyleSheet(f"""
            #mechanicCard {{
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
            }}
            #mechanicCard:hover {{
                border-color: {config.COLOR_SECONDARY};
                background-color: #f8f9fa;
            }}
            #mechanicName {{
                color: {config.COLOR_PRIMARY};
            }}
            #statusLabel {{
                font-size: 11px;
            }}
            #statLabel {{
                font-size: 11px;
                color: #666;
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.mechanic_id)
        super().mousePressEvent(event)


class CalendarMechanicCapacity(QWidget):
    """Widget pro přehled vytížení mechaniků"""

    mechanic_selected = pyqtSignal(int)
    find_slot_requested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_mechanic_id = None
        self.selected_date = QDate.currentDate()

        self.init_ui()
        self.refresh()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        top_panel = self.create_top_panel()
        main_layout.addWidget(top_panel)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = self.create_mechanics_panel()
        splitter.addWidget(left_panel)

        right_panel = self.create_detail_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([400, 700])

        main_layout.addWidget(splitter)

        bottom_panel = self.create_statistics_panel()
        main_layout.addWidget(bottom_panel)

    def create_top_panel(self):
        panel = QFrame()
        panel.setObjectName("topPanel")
        panel.setFixedHeight(60)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(15, 10, 15, 10)

        title = QLabel("👷 Vytížení mechaniků")
        title.setObjectName("panelTitle")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        layout.addStretch()

        period_label = QLabel("Období:")
        layout.addWidget(period_label)

        self.cmb_period = QComboBox()
        self.cmb_period.addItem("Dnes", "today")
        self.cmb_period.addItem("Tento týden", "week")
        self.cmb_period.addItem("Tento měsíc", "month")
        self.cmb_period.setCurrentIndex(1)
        self.cmb_period.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.cmb_period)

        layout.addSpacing(20)

        self.btn_find_slot = QPushButton("🔍 Najít volný termín")
        self.btn_find_slot.setObjectName("primaryButton")
        self.btn_find_slot.clicked.connect(self.find_free_slot)
        layout.addWidget(self.btn_find_slot)

        self.btn_optimize = QPushButton("⚡ Optimalizovat rozvrh")
        self.btn_optimize.setObjectName("actionButton")
        self.btn_optimize.clicked.connect(self.optimize_schedule)
        layout.addWidget(self.btn_optimize)

        self.btn_refresh = QPushButton("🔄 Obnovit")
        self.btn_refresh.setObjectName("actionButton")
        self.btn_refresh.clicked.connect(self.refresh)
        layout.addWidget(self.btn_refresh)

        panel.setStyleSheet(f"""
            #topPanel {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}
            #panelTitle {{
                color: {config.COLOR_PRIMARY};
            }}
            #primaryButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
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
            QComboBox {{
                padding: 6px 10px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }}
        """)

        return panel

    def create_mechanics_panel(self):
        panel = QFrame()
        panel.setObjectName("mechanicsPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        header = QLabel("📋 Přehled mechaniků")
        header.setObjectName("sectionHeader")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        header.setFont(font)
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setObjectName("mechanicsScroll")

        self.cards_widget = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setContentsMargins(5, 5, 5, 5)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch()

        scroll.setWidget(self.cards_widget)
        layout.addWidget(scroll)

        panel.setStyleSheet(f"""
            #mechanicsPanel {{
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}
            #sectionHeader {{
                color: {config.COLOR_PRIMARY};
                padding: 5px;
            }}
            #mechanicsScroll {{
                background: transparent;
                border: none;
            }}
        """)

        return panel

    def create_detail_panel(self):
        panel = QFrame()
        panel.setObjectName("detailPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        self.detail_header = QLabel("📊 Detail mechanika")
        self.detail_header.setObjectName("detailHeader")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        self.detail_header.setFont(font)
        layout.addWidget(self.detail_header)

        capacity_group = QGroupBox("Vytížení")
        capacity_layout = QGridLayout(capacity_group)
        capacity_layout.setSpacing(10)

        capacity_layout.addWidget(QLabel("Dnešní vytížení:"), 0, 0)
        self.today_progress = CapacityProgressBar()
        capacity_layout.addWidget(self.today_progress, 0, 1)
        self.lbl_today_hours = QLabel("0 / 8 hodin")
        capacity_layout.addWidget(self.lbl_today_hours, 0, 2)

        capacity_layout.addWidget(QLabel("Týdenní vytížení:"), 1, 0)
        self.week_progress = CapacityProgressBar()
        capacity_layout.addWidget(self.week_progress, 1, 1)
        self.lbl_week_hours = QLabel("0 / 40 hodin")
        capacity_layout.addWidget(self.lbl_week_hours, 1, 2)

        capacity_layout.addWidget(QLabel("Měsíční vytížení:"), 2, 0)
        self.month_progress = CapacityProgressBar()
        capacity_layout.addWidget(self.month_progress, 2, 1)
        self.lbl_month_hours = QLabel("0 / 160 hodin")
        capacity_layout.addWidget(self.lbl_month_hours, 2, 2)

        layout.addWidget(capacity_group)

        events_group = QGroupBox("Naplánované události")
        events_layout = QVBoxLayout(events_group)

        self.events_table = QTableWidget()
        self.events_table.setColumnCount(4)
        self.events_table.setHorizontalHeaderLabels(["Datum", "Čas", "Událost", "Zákazník"])
        self.events_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.events_table.setMaximumHeight(200)
        self.events_table.setAlternatingRowColors(True)
        events_layout.addWidget(self.events_table)

        layout.addWidget(events_group)

        slots_group = QGroupBox("Volné termíny (nejbližší)")
        slots_layout = QVBoxLayout(slots_group)

        self.slots_list = QVBoxLayout()
        self.slots_list.setSpacing(5)
        slots_layout.addLayout(self.slots_list)

        layout.addWidget(slots_group)

        actions_layout = QHBoxLayout()

        self.btn_assign_event = QPushButton("📅 Přiřadit událost")
        self.btn_assign_event.setObjectName("primaryButton")
        self.btn_assign_event.clicked.connect(self.assign_event_to_mechanic)
        actions_layout.addWidget(self.btn_assign_event)

        self.btn_view_calendar = QPushButton("📆 Zobrazit kalendář")
        self.btn_view_calendar.setObjectName("actionButton")
        self.btn_view_calendar.clicked.connect(self.view_mechanic_calendar)
        actions_layout.addWidget(self.btn_view_calendar)

        actions_layout.addStretch()

        layout.addLayout(actions_layout)
        layout.addStretch()

        panel.setStyleSheet(f"""
            #detailPanel {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}
            #detailHeader {{
                color: {config.COLOR_PRIMARY};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            #primaryButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }}
            #actionButton {{
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 8px 15px;
            }}
        """)

        return panel

    def create_statistics_panel(self):
        panel = QFrame()
        panel.setObjectName("statsPanel")
        panel.setFixedHeight(80)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(20, 10, 20, 10)

        self.lbl_avg_capacity = QLabel("Průměrné vytížení: 0%")
        self.lbl_avg_capacity.setObjectName("mainStat")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.lbl_avg_capacity.setFont(font)
        layout.addWidget(self.lbl_avg_capacity)

        layout.addSpacing(30)

        self.lbl_least_busy = QLabel("Nejméně vytížený: -")
        self.lbl_least_busy.setObjectName("statLabel")
        layout.addWidget(self.lbl_least_busy)

        self.lbl_most_busy = QLabel("Nejvíce vytížený: -")
        self.lbl_most_busy.setObjectName("statLabel")
        layout.addWidget(self.lbl_most_busy)

        layout.addStretch()

        warning_frame = QFrame()
        warning_frame.setObjectName("warningFrame")
        warning_layout = QHBoxLayout(warning_frame)
        warning_layout.setContentsMargins(10, 5, 10, 5)

        self.lbl_warnings = QLabel("⚠️ Žádná upozornění")
        self.lbl_warnings.setObjectName("warningLabel")
        warning_layout.addWidget(self.lbl_warnings)

        layout.addWidget(warning_frame)

        panel.setStyleSheet(f"""
            #statsPanel {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}
            #mainStat {{
                color: {config.COLOR_PRIMARY};
            }}
            #statLabel {{
                color: #555;
                font-size: 12px;
            }}
            #warningFrame {{
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 5px;
            }}
            #warningLabel {{
                color: #856404;
                font-weight: bold;
            }}
        """)

        return panel

    def refresh(self):
        self.load_mechanics_data()
        self.load_statistics()
        self.check_warnings()

        if self.selected_mechanic_id:
            self.load_mechanic_detail(self.selected_mechanic_id)

    def load_mechanics_data(self):
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        mechanics = db.fetch_all("""
            SELECT id, full_name, role FROM users
            WHERE role IN ('mechanik', 'admin') AND active = 1
            ORDER BY full_name
        """)

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        for mech in mechanics:
            mech_data = dict(mech)

            today_events = db.fetch_one("""
                SELECT COUNT(*) as count FROM calendar_events
                WHERE mechanic_id = ? AND DATE(start_datetime) = ? AND status != 'cancelled'
            """, (mech['id'], today.isoformat()))
            mech_data['events_today'] = today_events['count'] if today_events else 0

            week_events = db.fetch_one("""
                SELECT COUNT(*) as count FROM calendar_events
                WHERE mechanic_id = ? AND DATE(start_datetime) BETWEEN ? AND ? AND status != 'cancelled'
            """, (mech['id'], week_start.isoformat(), week_end.isoformat()))
            mech_data['events_week'] = week_events['count'] if week_events else 0

            today_hours = mech_data['events_today'] * 1.0
            week_hours = mech_data['events_week'] * 1.0

            mech_data['today_capacity'] = int((today_hours / 8.0) * 100)
            mech_data['week_capacity'] = int((week_hours / 40.0) * 100)

            free_slots = max(0, 8 - mech_data['events_today'])
            mech_data['free_slots'] = free_slots
            mech_data['is_available'] = free_slots > 0

            card = MechanicCapacityCard(mech_data)
            card.clicked.connect(self.on_mechanic_selected)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def on_mechanic_selected(self, mechanic_id):
        self.selected_mechanic_id = mechanic_id
        self.mechanic_selected.emit(mechanic_id)
        self.load_mechanic_detail(mechanic_id)

    def load_mechanic_detail(self, mechanic_id):
        mechanic = db.fetch_one("SELECT full_name FROM users WHERE id = ?", (mechanic_id,))
        if not mechanic:
            return

        self.detail_header.setText(f"📊 Detail: {mechanic['full_name']}")

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        month_start = today.replace(day=1)
        if today.month == 12:
            month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

        today_count = db.fetch_one("""
            SELECT COUNT(*) as count FROM calendar_events
            WHERE mechanic_id = ? AND DATE(start_datetime) = ? AND status != 'cancelled'
        """, (mechanic_id, today.isoformat()))
        today_hours = (today_count['count'] if today_count else 0) * 1.0
        today_percent = int((today_hours / 8.0) * 100)
        self.today_progress.setValue(min(today_percent, 150))
        self.lbl_today_hours.setText(f"{today_hours:.1f} / 8 hodin")

        week_count = db.fetch_one("""
            SELECT COUNT(*) as count FROM calendar_events
            WHERE mechanic_id = ? AND DATE(start_datetime) BETWEEN ? AND ? AND status != 'cancelled'
        """, (mechanic_id, week_start.isoformat(), week_end.isoformat()))
        week_hours = (week_count['count'] if week_count else 0) * 1.0
        week_percent = int((week_hours / 40.0) * 100)
        self.week_progress.setValue(min(week_percent, 150))
        self.lbl_week_hours.setText(f"{week_hours:.1f} / 40 hodin")

        month_count = db.fetch_one("""
            SELECT COUNT(*) as count FROM calendar_events
            WHERE mechanic_id = ? AND DATE(start_datetime) BETWEEN ? AND ? AND status != 'cancelled'
        """, (mechanic_id, month_start.isoformat(), month_end.isoformat()))
        month_hours = (month_count['count'] if month_count else 0) * 1.0
        month_percent = int((month_hours / 160.0) * 100)
        self.month_progress.setValue(min(month_percent, 150))
        self.lbl_month_hours.setText(f"{month_hours:.1f} / 160 hodin")

        events = db.fetch_all("""
            SELECT
                e.start_datetime, e.title,
                c.first_name || ' ' || c.last_name as customer_name
            FROM calendar_events e
            LEFT JOIN customers c ON e.customer_id = c.id
            WHERE e.mechanic_id = ? AND DATE(e.start_datetime) >= ? AND e.status != 'cancelled'
            ORDER BY e.start_datetime
            LIMIT 10
        """, (mechanic_id, today.isoformat()))

        self.events_table.setRowCount(len(events))
        for row, event in enumerate(events):
            if event['start_datetime']:
                dt = datetime.fromisoformat(event['start_datetime'])
                date_item = QTableWidgetItem(dt.strftime("%d.%m.%Y"))
                time_item = QTableWidgetItem(dt.strftime("%H:%M"))
            else:
                date_item = QTableWidgetItem("")
                time_item = QTableWidgetItem("")

            title_item = QTableWidgetItem(event['title'] or "")
            customer_item = QTableWidgetItem(event['customer_name'] or "")

            self.events_table.setItem(row, 0, date_item)
            self.events_table.setItem(row, 1, time_item)
            self.events_table.setItem(row, 2, title_item)
            self.events_table.setItem(row, 3, customer_item)

        self.load_free_slots(mechanic_id)

    def load_free_slots(self, mechanic_id):
        while self.slots_list.count():
            item = self.slots_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        today = date.today()
        free_slots = []

        for day_offset in range(7):
            check_date = today + timedelta(days=day_offset)

            if check_date.weekday() == 6:
                continue

            if check_date.weekday() == 5:
                work_hours = [(8, 12)]
            else:
                work_hours = [(8, 12), (13, 17)]

            busy_times = db.fetch_all("""
                SELECT start_datetime, end_datetime FROM calendar_events
                WHERE mechanic_id = ? AND DATE(start_datetime) = ? AND status != 'cancelled'
            """, (mechanic_id, check_date.isoformat()))

            busy_hours = set()
            for event in busy_times:
                if event['start_datetime']:
                    start_dt = datetime.fromisoformat(event['start_datetime'])
                    end_dt = datetime.fromisoformat(event['end_datetime']) if event['end_datetime'] else start_dt + timedelta(hours=1)
                    for h in range(start_dt.hour, min(end_dt.hour + 1, 18)):
                        busy_hours.add(h)

            for start_h, end_h in work_hours:
                for hour in range(start_h, end_h):
                    if hour not in busy_hours:
                        free_slots.append((check_date, hour))
                        if len(free_slots) >= 6:
                            break
                if len(free_slots) >= 6:
                    break
            if len(free_slots) >= 6:
                break

        days_cz = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]

        for slot_date, slot_hour in free_slots[:6]:
            slot_frame = QFrame()
            slot_frame.setObjectName("slotFrame")
            slot_layout = QHBoxLayout(slot_frame)
            slot_layout.setContentsMargins(8, 5, 8, 5)

            day_name = days_cz[slot_date.weekday()]
            slot_label = QLabel(f"🟢 {day_name} {slot_date.strftime('%d.%m.')} - {slot_hour:02d}:00")
            slot_label.setStyleSheet("font-size: 12px;")
            slot_layout.addWidget(slot_label)

            slot_layout.addStretch()

            btn_book = QPushButton("📅")
            btn_book.setFixedSize(30, 25)
            btn_book.setToolTip("Rezervovat")
            btn_book.clicked.connect(lambda checked, d=slot_date, h=slot_hour: self.book_slot(d, h))
            slot_layout.addWidget(btn_book)

            slot_frame.setStyleSheet("""
                #slotFrame {
                    background-color: #e8f5e9;
                    border: 1px solid #c8e6c9;
                    border-radius: 5px;
                }
            """)

            self.slots_list.addWidget(slot_frame)

        if not free_slots:
            no_slots = QLabel("Žádné volné termíny v příštích 7 dnech")
            no_slots.setStyleSheet("color: #e74c3c; font-style: italic;")
            self.slots_list.addWidget(no_slots)

    def book_slot(self, slot_date, slot_hour):
        QMessageBox.information(
            self,
            "Rezervace termínu",
            f"Rezervace termínu: {slot_date.strftime('%d.%m.%Y')} v {slot_hour:02d}:00\n\n"
            "Otevře se dialog pro vytvoření nové události."
        )

    def load_statistics(self):
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        mechanics = db.fetch_all("""
            SELECT u.id, u.full_name,
                   (SELECT COUNT(*) FROM calendar_events
                    WHERE mechanic_id = u.id AND DATE(start_datetime) BETWEEN ? AND ?
                    AND status != 'cancelled') as week_events
            FROM users u
            WHERE u.role IN ('mechanik', 'admin') AND u.active = 1
        """, (week_start.isoformat(), week_end.isoformat()))

        if mechanics:
            total_capacity = sum(m['week_events'] for m in mechanics)
            avg_capacity = int((total_capacity / (len(mechanics) * 40)) * 100)
            self.lbl_avg_capacity.setText(f"Průměrné vytížení: {avg_capacity}%")

            sorted_mechs = sorted(mechanics, key=lambda x: x['week_events'])
            least = sorted_mechs[0]
            most = sorted_mechs[-1]

            self.lbl_least_busy.setText(f"Nejméně vytížený: {least['full_name']} ({least['week_events']} událostí)")
            self.lbl_most_busy.setText(f"Nejvíce vytížený: {most['full_name']} ({most['week_events']} událostí)")
        else:
            self.lbl_avg_capacity.setText("Průměrné vytížení: 0%")
            self.lbl_least_busy.setText("Nejméně vytížený: -")
            self.lbl_most_busy.setText("Nejvíce vytížený: -")

    def check_warnings(self):
        today = date.today()

        overloaded = db.fetch_all("""
            SELECT u.full_name, COUNT(*) as count
            FROM users u
            JOIN calendar_events e ON u.id = e.mechanic_id
            WHERE DATE(e.start_datetime) = ? AND e.status != 'cancelled'
            GROUP BY u.id
            HAVING count > 8
        """, (today.isoformat(),))

        if overloaded:
            names = ", ".join([m['full_name'] for m in overloaded])
            self.lbl_warnings.setText(f"⚠️ Přetížení: {names}")
            self.lbl_warnings.parentWidget().setStyleSheet("""
                #warningFrame {
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    border-radius: 5px;
                }
            """)
        else:
            self.lbl_warnings.setText("✅ Žádná upozornění")
            self.lbl_warnings.parentWidget().setStyleSheet("""
                #warningFrame {
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 5px;
                }
            """)

    def find_free_slot(self):
        today = date.today()

        best_slot = None
        best_mechanic = None
        min_load = float('inf')

        for day_offset in range(14):
            check_date = today + timedelta(days=day_offset)

            if check_date.weekday() == 6:
                continue

            mechanics = db.fetch_all("""
                SELECT u.id, u.full_name,
                       (SELECT COUNT(*) FROM calendar_events
                        WHERE mechanic_id = u.id AND DATE(start_datetime) = ?
                        AND status != 'cancelled') as day_events
                FROM users u
                WHERE u.role IN ('mechanik', 'admin') AND u.active = 1
            """, (check_date.isoformat(),))

            for mech in mechanics:
                max_events = 4 if check_date.weekday() == 5 else 8
                if mech['day_events'] < max_events and mech['day_events'] < min_load:
                    min_load = mech['day_events']
                    best_mechanic = mech
                    best_slot = check_date

        if best_slot and best_mechanic:
            QMessageBox.information(
                self,
                "Nejbližší volný termín",
                f"Doporučený termín:\n\n"
                f"📅 Datum: {best_slot.strftime('%d.%m.%Y')}\n"
                f"👤 Mechanik: {best_mechanic['full_name']}\n"
                f"📊 Vytížení: {best_mechanic['day_events']}/8 událostí"
            )
        else:
            QMessageBox.warning(
                self,
                "Žádný volný termín",
                "V příštích 14 dnech není k dispozici žádný volný termín."
            )

    def optimize_schedule(self):
        reply = QMessageBox.question(
            self,
            "Optimalizace rozvrhu",
            "Chcete automaticky přerozdělit události mezi mechaniky pro optimální vytížení?\n\n"
            "Tato akce přesune události od přetížených mechaniků k méně vytíženým.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.perform_optimization()

    def perform_optimization(self):
        today = date.today()
        week_end = today + timedelta(days=6)

        overloaded_events = db.fetch_all("""
            SELECT e.id, e.mechanic_id, e.start_datetime
            FROM calendar_events e
            JOIN (
                SELECT mechanic_id, DATE(start_datetime) as event_date, COUNT(*) as count
                FROM calendar_events
                WHERE DATE(start_datetime) BETWEEN ? AND ? AND status != 'cancelled'
                GROUP BY mechanic_id, DATE(start_datetime)
                HAVING count > 6
            ) overload ON e.mechanic_id = overload.mechanic_id
                       AND DATE(e.start_datetime) = overload.event_date
            WHERE e.status != 'cancelled'
            ORDER BY overload.count DESC
            LIMIT 5
        """, (today.isoformat(), week_end.isoformat()))

        moved_count = 0
        for event in overloaded_events:
            event_date = datetime.fromisoformat(event['start_datetime']).date()

            available_mechanic = db.fetch_one("""
                SELECT u.id FROM users u
                WHERE u.role IN ('mechanik', 'admin') AND u.active = 1
                AND u.id != ?
                AND (SELECT COUNT(*) FROM calendar_events
                     WHERE mechanic_id = u.id AND DATE(start_datetime) = ?
                     AND status != 'cancelled') < 6
                ORDER BY (SELECT COUNT(*) FROM calendar_events
                         WHERE mechanic_id = u.id AND DATE(start_datetime) = ?
                         AND status != 'cancelled')
                LIMIT 1
            """, (event['mechanic_id'], event_date.isoformat(), event_date.isoformat()))

            if available_mechanic:
                db.execute_query(
                    "UPDATE calendar_events SET mechanic_id = ?, updated_at = ? WHERE id = ?",
                    (available_mechanic['id'], datetime.now().isoformat(), event['id'])
                )
                moved_count += 1

        if moved_count > 0:
            QMessageBox.information(
                self,
                "Optimalizace dokončena",
                f"Bylo přesunuto {moved_count} událostí pro lepší rozložení zátěže."
            )
            self.refresh()
        else:
            QMessageBox.information(
                self,
                "Optimalizace",
                "Rozvrh je již optimální, nebyly provedeny žádné změny."
            )

    def assign_event_to_mechanic(self):
        if not self.selected_mechanic_id:
            QMessageBox.warning(self, "Upozornění", "Nejprve vyberte mechanika.")
            return

        QMessageBox.information(
            self,
            "Přiřazení události",
            "Otevře se dialog pro vytvoření nové události s předvybraným mechanikem."
        )

    def view_mechanic_calendar(self):
        if not self.selected_mechanic_id:
            QMessageBox.warning(self, "Upozornění", "Nejprve vyberte mechanika.")
            return

        mechanic = db.fetch_one("SELECT full_name FROM users WHERE id = ?", (self.selected_mechanic_id,))
        if mechanic:
            QMessageBox.information(
                self,
                "Kalendář mechanika",
                f"Přepnutí na kalendář mechanika: {mechanic['full_name']}"
            )
