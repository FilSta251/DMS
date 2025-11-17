# -*- coding: utf-8 -*-
"""
Denní zobrazení kalendáře
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QFrame, QPushButton
)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QPen
from datetime import datetime, timedelta
from database_manager import db
import config


class CalendarDayView(QWidget):
    """Denní zobrazení kalendáře"""

    event_clicked = pyqtSignal(int)
    event_double_clicked = pyqtSignal(int)
    new_event_requested = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_date = QDate.currentDate()
        self.mechanic_filter = None
        self.event_type_filter = None
        self.events = []
        self.start_hour = 7
        self.end_hour = 19
        self.hour_height = 60

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        header = self.create_header()
        main_layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("dayScroll")

        self.timeline_widget = QWidget()
        self.timeline_layout = QVBoxLayout(self.timeline_widget)
        self.timeline_layout.setContentsMargins(0, 0, 0, 0)
        self.timeline_layout.setSpacing(0)

        self.create_timeline()

        scroll.setWidget(self.timeline_widget)
        main_layout.addWidget(scroll)

        self.setStyleSheet("""
            #dayScroll {
                background-color: white;
                border: none;
            }
        """)

    def create_header(self):
        header = QFrame()
        header.setObjectName("dayHeader")
        header.setFixedHeight(60)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 10, 10, 10)

        self.lbl_date = QLabel()
        self.lbl_date.setObjectName("dateLabel")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.lbl_date.setFont(font)
        layout.addWidget(self.lbl_date)

        layout.addStretch()

        self.lbl_events_count = QLabel("0 událostí")
        self.lbl_events_count.setObjectName("countLabel")
        layout.addWidget(self.lbl_events_count)

        header.setStyleSheet(f"""
            #dayHeader {{
                background-color: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
            }}
            #dateLabel {{
                color: {config.COLOR_PRIMARY};
            }}
            #countLabel {{
                color: #666;
            }}
        """)

        return header

    def create_timeline(self):
        for i in reversed(range(self.timeline_layout.count())):
            widget = self.timeline_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        for hour in range(self.start_hour, self.end_hour + 1):
            hour_row = self.create_hour_row(hour)
            self.timeline_layout.addWidget(hour_row)

        self.timeline_layout.addStretch()

    def create_hour_row(self, hour):
        row = QFrame()
        row.setObjectName("hourRow")
        row.setFixedHeight(self.hour_height)
        row.hour = hour

        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        time_label = QLabel(f"{hour:02d}:00")
        time_label.setFixedWidth(60)
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        time_label.setObjectName("timeLabel")
        time_label.setStyleSheet("padding-right: 10px; padding-top: 5px; color: #666;")
        layout.addWidget(time_label)

        content = QFrame()
        content.setObjectName("hourContent")
        content.hour = hour
        content.mousePressEvent = lambda e, h=hour: self.on_hour_clicked(h)
        content.mouseDoubleClickEvent = lambda e, h=hour: self.on_hour_double_clicked(h)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(5, 2, 5, 2)
        content_layout.setSpacing(2)

        row.content_widget = content
        layout.addWidget(content)

        row.setStyleSheet("""
            #hourRow {
                background-color: white;
                border-bottom: 1px solid #e0e0e0;
            }
            #hourContent {
                background-color: white;
                border-left: 1px solid #e0e0e0;
            }
            #hourContent:hover {
                background-color: #f8f9fa;
            }
        """)

        return row

    def set_current_date(self, date):
        if isinstance(date, QDate):
            self.current_date = date
        else:
            self.current_date = QDate(date.year, date.month, date.day)
        self.update_header()

    def set_filters(self, mechanic_id=None, event_type=None):
        self.mechanic_filter = mechanic_id
        self.event_type_filter = event_type

    def update_header(self):
        days_cz = ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"]
        day_name = days_cz[self.current_date.dayOfWeek() - 1]
        date_str = f"{day_name} {self.current_date.day()}.{self.current_date.month()}.{self.current_date.year()}"
        self.lbl_date.setText(date_str)

    def refresh(self):
        self.load_events()
        self.display_events()
        self.update_header()

    def load_events(self):
        date_str = self.current_date.toPyDate().isoformat()

        query = """
            SELECT
                e.id, e.title, e.event_type, e.start_datetime, e.end_datetime,
                e.status, e.priority, e.color, e.description,
                c.first_name || ' ' || c.last_name as customer_name,
                v.license_plate,
                u.full_name as mechanic_name
            FROM calendar_events e
            LEFT JOIN customers c ON e.customer_id = c.id
            LEFT JOIN vehicles v ON e.vehicle_id = v.id
            LEFT JOIN users u ON e.mechanic_id = u.id
            WHERE DATE(e.start_datetime) = ?
        """
        params = [date_str]

        if self.mechanic_filter:
            query += " AND e.mechanic_id = ?"
            params.append(self.mechanic_filter)

        if self.event_type_filter:
            query += " AND e.event_type = ?"
            params.append(self.event_type_filter)

        query += " ORDER BY e.start_datetime"

        self.events = db.fetch_all(query, tuple(params))
        self.lbl_events_count.setText(f"{len(self.events)} událostí")

    def display_events(self):
        for i in range(self.timeline_layout.count()):
            item = self.timeline_layout.itemAt(i)
            if item and item.widget():
                row = item.widget()
                if hasattr(row, 'content_widget'):
                    content_layout = row.content_widget.layout()
                    while content_layout.count():
                        child = content_layout.takeAt(0)
                        if child.widget():
                            child.widget().deleteLater()

        for event in self.events:
            if event['start_datetime']:
                start_dt = datetime.fromisoformat(event['start_datetime'])
                event_hour = start_dt.hour

                for i in range(self.timeline_layout.count()):
                    item = self.timeline_layout.itemAt(i)
                    if item and item.widget():
                        row = item.widget()
                        if hasattr(row, 'hour') and row.hour == event_hour:
                            event_widget = self.create_event_widget(event)
                            row.content_widget.layout().addWidget(event_widget)
                            break

    def create_event_widget(self, event):
        widget = QFrame()
        widget.setObjectName("eventWidget")
        widget.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(10)

        if event['start_datetime']:
            start_dt = datetime.fromisoformat(event['start_datetime'])
            time_str = start_dt.strftime("%H:%M")
        else:
            time_str = "--:--"

        time_label = QLabel(time_str)
        time_label.setObjectName("eventTime")
        time_label.setFixedWidth(50)
        layout.addWidget(time_label)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        title_label = QLabel(event['title'] or "Událost")
        title_label.setObjectName("eventTitle")
        font = QFont()
        font.setBold(True)
        title_label.setFont(font)
        info_layout.addWidget(title_label)

        if event['customer_name']:
            customer_label = QLabel(f"👤 {event['customer_name']}")
            customer_label.setObjectName("eventDetail")
            info_layout.addWidget(customer_label)

        if event['license_plate']:
            vehicle_label = QLabel(f"🚗 {event['license_plate']}")
            vehicle_label.setObjectName("eventDetail")
            info_layout.addWidget(vehicle_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        if event['mechanic_name']:
            mechanic_label = QLabel(f"👷 {event['mechanic_name']}")
            mechanic_label.setObjectName("eventMechanic")
            layout.addWidget(mechanic_label)

        color = event['color'] or '#3498db'

        widget.setStyleSheet(f"""
            #eventWidget {{
                background-color: {color}20;
                border-left: 4px solid {color};
                border-radius: 5px;
                margin: 2px 0;
            }}
            #eventWidget:hover {{
                background-color: {color}40;
            }}
            #eventTime {{
                color: #666;
                font-size: 11px;
            }}
            #eventTitle {{
                color: #2c3e50;
            }}
            #eventDetail {{
                color: #666;
                font-size: 11px;
            }}
            #eventMechanic {{
                color: #888;
                font-size: 10px;
            }}
        """)

        widget.mousePressEvent = lambda e, eid=event['id']: self.event_clicked.emit(eid)
        widget.mouseDoubleClickEvent = lambda e, eid=event['id']: self.event_double_clicked.emit(eid)

        return widget

    def on_hour_clicked(self, hour):
        pass

    def on_hour_double_clicked(self, hour):
        selected_datetime = datetime(
            self.current_date.year(),
            self.current_date.month(),
            self.current_date.day(),
            hour, 0
        )
        self.new_event_requested.emit(selected_datetime)
