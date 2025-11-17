# -*- coding: utf-8 -*-
"""
Widgety a komponenty kalendáře
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QCalendarWidget, QTimeEdit, QComboBox, QLineEdit,
    QColorDialog, QDateEdit, QGridLayout, QSizePolicy,
    QProgressBar, QDialog, QFormLayout, QTextEdit,
    QDateTimeEdit, QSpinBox
)
from PyQt6.QtCore import Qt, QDate, QTime, QDateTime, pyqtSignal, QSize, QRect
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush, QTextCharFormat,
    QPalette, QPixmap
)
from datetime import datetime, date, timedelta
from database_manager import db
import config


class MiniCalendar(QCalendarWidget):
    """Malý měsíční kalendář"""

    date_selected = pyqtSignal(QDate)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setGridVisible(True)
        self.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        self.setFirstDayOfWeek(Qt.DayOfWeek.Monday)

        self.selectionChanged.connect(self.on_selection_changed)

        self.event_dates = set()

        self.setStyleSheet(f"""
            QCalendarWidget {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }}
            QCalendarWidget QToolButton {{
                color: {config.COLOR_PRIMARY};
                font-weight: bold;
            }}
            QCalendarWidget QMenu {{
                background-color: white;
            }}
            QCalendarWidget QSpinBox {{
                background-color: white;
            }}
        """)

    def on_selection_changed(self):
        self.date_selected.emit(self.selectedDate())

    def set_event_dates(self, dates):
        self.event_dates = set(dates)
        self.updateCells()

    def paintCell(self, painter, rect, date):
        super().paintCell(painter, rect, date)

        if date.toPyDate() in self.event_dates:
            painter.save()
            painter.setBrush(QBrush(QColor(config.COLOR_SECONDARY)))
            painter.setPen(Qt.PenStyle.NoPen)

            indicator_size = 6
            x = rect.x() + rect.width() - indicator_size - 3
            y = rect.y() + 3
            painter.drawEllipse(x, y, indicator_size, indicator_size)

            painter.restore()


class EventCard(QFrame):
    """Karta události"""

    clicked = pyqtSignal(int)
    edit_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)

    def __init__(self, event_data, parent=None):
        super().__init__(parent)
        self.event_id = event_data.get('id')
        self.event_data = event_data

        self.setObjectName("eventCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(80)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        header = QHBoxLayout()

        time_str = self.event_data.get('time', '00:00')
        time_label = QLabel(f"⏰ {time_str}")
        time_label.setObjectName("eventTime")
        header.addWidget(time_label)

        header.addStretch()

        type_badge = EventTypeBadge(self.event_data.get('event_type', 'other'))
        header.addWidget(type_badge)

        layout.addLayout(header)

        title = self.event_data.get('title', 'Událost')
        title_label = QLabel(title)
        title_label.setObjectName("eventTitle")
        font = QFont()
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)

        if self.event_data.get('customer_name'):
            customer_label = QLabel(f"👤 {self.event_data['customer_name']}")
            customer_label.setObjectName("eventCustomer")
            layout.addWidget(customer_label)

        color = self.event_data.get('color', '#3498db')
        self.setStyleSheet(f"""
            #eventCard {{
                background-color: white;
                border-left: 4px solid {color};
                border-radius: 5px;
                border: 1px solid #e0e0e0;
                border-left: 4px solid {color};
            }}
            #eventCard:hover {{
                background-color: #f8f9fa;
            }}
            #eventTime {{
                color: #666;
                font-size: 11px;
            }}
            #eventTitle {{
                color: #2c3e50;
            }}
            #eventCustomer {{
                color: #777;
                font-size: 10px;
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.event_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.edit_requested.emit(self.event_id)
        super().mouseDoubleClickEvent(event)


class TimeSlotPicker(QWidget):
    """Widget pro výběr časového slotu"""

    time_selected = pyqtSignal(QTime)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.start_hour = 8
        self.end_hour = 18
        self.slot_duration = 30

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.grid = QGridLayout()
        self.grid.setSpacing(3)

        row = 0
        col = 0
        max_cols = 4

        for hour in range(self.start_hour, self.end_hour):
            for minute in [0, 30]:
                time = QTime(hour, minute)
                btn = QPushButton(time.toString("HH:mm"))
                btn.setFixedSize(60, 30)
                btn.setObjectName("timeSlotButton")
                btn.clicked.connect(lambda checked, t=time: self.on_slot_clicked(t))

                self.grid.addWidget(btn, row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

        layout.addLayout(self.grid)

        self.setStyleSheet(f"""
            #timeSlotButton {{
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                font-size: 11px;
            }}
            #timeSlotButton:hover {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
            }}
            #timeSlotButton:pressed {{
                background-color: #2980b9;
            }}
        """)

    def on_slot_clicked(self, time):
        self.time_selected.emit(time)


class MechanicSelector(QComboBox):
    """Výběr mechanika s vizuálním indikátorem vytížení"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumWidth(200)
        self.load_mechanics()

    def load_mechanics(self):
        self.clear()
        self.addItem("-- Nepřiřazeno --", None)

        today = date.today()

        mechanics = db.fetch_all("""
            SELECT
                u.id, u.full_name,
                (SELECT COUNT(*) FROM calendar_events
                 WHERE mechanic_id = u.id AND DATE(start_datetime) = ?
                 AND status != 'cancelled') as today_events
            FROM users u
            WHERE u.role IN ('mechanik', 'admin') AND u.active = 1
            ORDER BY u.full_name
        """, (today.isoformat(),))

        for m in mechanics:
            events = m['today_events']
            if events >= 8:
                icon = "🔴"
            elif events >= 5:
                icon = "🟡"
            else:
                icon = "🟢"

            text = f"{icon} {m['full_name']} ({events}/8)"
            self.addItem(text, m['id'])

    def refresh(self):
        current_id = self.currentData()
        self.load_mechanics()

        if current_id:
            for i in range(self.count()):
                if self.itemData(i) == current_id:
                    self.setCurrentIndex(i)
                    break


class EventTypeBadge(QLabel):
    """Štítek typu události"""

    def __init__(self, event_type, parent=None):
        super().__init__(parent)

        type_config = {
            'service': ('🔧', 'Servis', '#3498db'),
            'meeting': ('📞', 'Schůzka', '#9b59b6'),
            'delivery': ('📦', 'Příjem', '#f39c12'),
            'handover': ('🚗', 'Předání', '#27ae60'),
            'reminder': ('⏰', 'Připomínka', '#e74c3c'),
            'other': ('📅', 'Jiné', '#95a5a6')
        }

        icon, text, color = type_config.get(event_type, type_config['other'])

        self.setText(f"{icon} {text}")
        self.setObjectName("typeBadge")

        self.setStyleSheet(f"""
            #typeBadge {{
                background-color: {color};
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)


class CapacityBar(QProgressBar):
    """Progress bar pro zobrazení vytížení"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setTextVisible(True)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setFormat("%p%")

    def setValue(self, value):
        super().setValue(min(value, 100))

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
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 6px;
            }}
        """)


class DayCell(QFrame):
    """Buňka dne v kalendářní mřížce"""

    clicked = pyqtSignal(QDate)
    double_clicked = pyqtSignal(QDate)

    def __init__(self, date_obj, parent=None):
        super().__init__(parent)
        self.date = date_obj
        self.events = []
        self.is_current_month = True
        self.is_today = date_obj == QDate.currentDate()

        self.setObjectName("dayCell")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(100)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        day_number = QLabel(str(self.date.day()))
        day_number.setObjectName("dayNumber")

        if self.is_today:
            day_number.setStyleSheet(f"""
                #dayNumber {{
                    background-color: {config.COLOR_SECONDARY};
                    color: white;
                    border-radius: 12px;
                    padding: 2px 6px;
                    font-weight: bold;
                }}
            """)
        else:
            day_number.setStyleSheet("""
                #dayNumber {
                    font-weight: bold;
                    color: #333;
                }
            """)

        layout.addWidget(day_number, alignment=Qt.AlignmentFlag.AlignLeft)

        self.events_container = QVBoxLayout()
        self.events_container.setSpacing(2)
        layout.addLayout(self.events_container)

        layout.addStretch()

        bg_color = "white" if self.is_current_month else "#f5f5f5"
        border_color = config.COLOR_SECONDARY if self.is_today else "#e0e0e0"

        self.setStyleSheet(f"""
            #dayCell {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 5px;
            }}
            #dayCell:hover {{
                background-color: #f0f8ff;
            }}
        """)

    def add_event(self, event_data):
        self.events.append(event_data)

        if len(self.events) <= 3:
            event_label = QLabel(f"• {event_data.get('title', '')[:15]}")
            event_label.setStyleSheet(f"""
                color: {event_data.get('color', '#3498db')};
                font-size: 10px;
            """)
            self.events_container.addWidget(event_label)
        elif len(self.events) == 4:
            more_label = QLabel(f"+ {len(self.events) - 3} další...")
            more_label.setStyleSheet("color: #666; font-size: 9px; font-style: italic;")
            self.events_container.addWidget(more_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.date)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.date)
        super().mouseDoubleClickEvent(event)


class EventBlock(QFrame):
    """Blok události v timeline zobrazení"""

    clicked = pyqtSignal(int)

    def __init__(self, event_data, parent=None):
        super().__init__(parent)
        self.event_id = event_data.get('id')
        self.event_data = event_data

        self.setObjectName("eventBlock")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 3, 5, 3)
        layout.setSpacing(2)

        title = self.event_data.get('title', 'Událost')
        title_label = QLabel(title)
        title_label.setObjectName("blockTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        title_label.setFont(font)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        if self.event_data.get('customer_name'):
            customer_label = QLabel(self.event_data['customer_name'])
            customer_label.setObjectName("blockCustomer")
            customer_label.setStyleSheet("font-size: 8px; color: rgba(255,255,255,0.8);")
            layout.addWidget(customer_label)

        color = self.event_data.get('color', '#3498db')

        self.setStyleSheet(f"""
            #eventBlock {{
                background-color: {color};
                border-radius: 4px;
                border: 1px solid rgba(0,0,0,0.1);
            }}
            #eventBlock:hover {{
                border: 2px solid rgba(0,0,0,0.3);
            }}
            #blockTitle {{
                color: white;
            }}
            #blockCustomer {{
                color: rgba(255,255,255,0.8);
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.event_id)
        super().mousePressEvent(event)


class HourRow(QFrame):
    """Řádek hodiny v denním zobrazení"""

    time_clicked = pyqtSignal(QTime)

    def __init__(self, hour, parent=None):
        super().__init__(parent)
        self.hour = hour

        self.setObjectName("hourRow")
        self.setFixedHeight(60)

        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        time_label = QLabel(f"{self.hour:02d}:00")
        time_label.setFixedWidth(60)
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        time_label.setObjectName("timeLabel")
        layout.addWidget(time_label)

        self.content_area = QFrame()
        self.content_area.setObjectName("contentArea")
        self.content_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.content_area.mousePressEvent = self.on_content_click
        layout.addWidget(self.content_area)

        self.setStyleSheet(f"""
            #hourRow {{
                background-color: white;
                border-bottom: 1px solid #e0e0e0;
            }}
            #timeLabel {{
                color: #666;
                font-size: 11px;
                padding-right: 10px;
            }}
            #contentArea {{
                background-color: white;
                border-left: 1px solid #e0e0e0;
            }}
            #contentArea:hover {{
                background-color: #f8f9fa;
            }}
        """)

    def on_content_click(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.time_clicked.emit(QTime(self.hour, 0))


class WeekHeader(QFrame):
    """Hlavička týdne s názvy dnů"""

    def __init__(self, start_date, parent=None):
        super().__init__(parent)
        self.start_date = start_date

        self.setObjectName("weekHeader")
        self.setFixedHeight(50)

        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(60, 0, 0, 0)
        layout.setSpacing(0)

        days_cz = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]

        for i in range(7):
            day_date = self.start_date.addDays(i)

            day_frame = QFrame()
            day_layout = QVBoxLayout(day_frame)
            day_layout.setContentsMargins(5, 5, 5, 5)
            day_layout.setSpacing(2)

            day_name = QLabel(days_cz[i])
            day_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            day_name.setObjectName("dayName")
            day_layout.addWidget(day_name)

            day_num = QLabel(str(day_date.day()))
            day_num.setAlignment(Qt.AlignmentFlag.AlignCenter)
            day_num.setObjectName("dayNum")

            if day_date == QDate.currentDate():
                day_num.setStyleSheet(f"""
                    #dayNum {{
                        background-color: {config.COLOR_SECONDARY};
                        color: white;
                        border-radius: 15px;
                        padding: 5px;
                        font-weight: bold;
                    }}
                """)

            day_layout.addWidget(day_num)

            layout.addWidget(day_frame)

        self.setStyleSheet(f"""
            #weekHeader {{
                background-color: #f8f9fa;
                border-bottom: 2px solid {config.COLOR_SECONDARY};
            }}
            #dayName {{
                font-weight: bold;
                color: #666;
            }}
            #dayNum {{
                font-size: 14px;
                color: #333;
            }}
        """)


class ColorPicker(QWidget):
    """Widget pro výběr barvy události"""

    color_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.selected_color = "#3498db"
        self.preset_colors = [
            "#3498db", "#27ae60", "#f39c12", "#e74c3c",
            "#9b59b6", "#1abc9c", "#95a5a6", "#2c3e50"
        ]

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.color_button = QPushButton()
        self.color_button.setFixedSize(35, 30)
        self.color_button.clicked.connect(self.open_color_dialog)
        self.update_button_color()
        layout.addWidget(self.color_button)

        for color in self.preset_colors:
            btn = QPushButton()
            btn.setFixedSize(25, 25)
            btn.setStyleSheet(f"""
                background-color: {color};
                border: 1px solid #ccc;
                border-radius: 3px;
            """)
            btn.clicked.connect(lambda checked, c=color: self.set_color(c))
            layout.addWidget(btn)

        layout.addStretch()

    def update_button_color(self):
        self.color_button.setStyleSheet(f"""
            background-color: {self.selected_color};
            border: 2px solid #ccc;
            border-radius: 5px;
        """)

    def set_color(self, color):
        self.selected_color = color
        self.update_button_color()
        self.color_selected.emit(color)

    def open_color_dialog(self):
        color = QColorDialog.getColor(QColor(self.selected_color), self)
        if color.isValid():
            self.set_color(color.name())

    def get_color(self):
        return self.selected_color


class DateRangePicker(QWidget):
    """Widget pro výběr období"""

    range_changed = pyqtSignal(QDate, QDate)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Od:"))

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate())
        self.date_from.dateChanged.connect(self.on_range_changed)
        layout.addWidget(self.date_from)

        layout.addWidget(QLabel("Do:"))

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate().addDays(30))
        self.date_to.dateChanged.connect(self.on_range_changed)
        layout.addWidget(self.date_to)

        self.cmb_preset = QComboBox()
        self.cmb_preset.addItem("Vlastní", None)
        self.cmb_preset.addItem("Dnes", "today")
        self.cmb_preset.addItem("Tento týden", "week")
        self.cmb_preset.addItem("Tento měsíc", "month")
        self.cmb_preset.addItem("Tento rok", "year")
        self.cmb_preset.currentIndexChanged.connect(self.on_preset_changed)
        layout.addWidget(self.cmb_preset)

    def on_range_changed(self):
        self.range_changed.emit(self.date_from.date(), self.date_to.date())

    def on_preset_changed(self):
        preset = self.cmb_preset.currentData()
        if not preset:
            return

        today = QDate.currentDate()

        if preset == "today":
            self.date_from.setDate(today)
            self.date_to.setDate(today)
        elif preset == "week":
            start = today.addDays(-today.dayOfWeek() + 1)
            end = start.addDays(6)
            self.date_from.setDate(start)
            self.date_to.setDate(end)
        elif preset == "month":
            start = today.addDays(-today.day() + 1)
            end = start.addMonths(1).addDays(-1)
            self.date_from.setDate(start)
            self.date_to.setDate(end)
        elif preset == "year":
            start = QDate(today.year(), 1, 1)
            end = QDate(today.year(), 12, 31)
            self.date_from.setDate(start)
            self.date_to.setDate(end)

    def get_range(self):
        return self.date_from.date(), self.date_to.date()


class TimeRangePicker(QWidget):
    """Widget pro výběr časového rozsahu"""

    range_changed = pyqtSignal(QTime, QTime)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Od:"))

        self.time_from = QTimeEdit()
        self.time_from.setDisplayFormat("HH:mm")
        self.time_from.setTime(QTime(9, 0))
        self.time_from.timeChanged.connect(self.on_range_changed)
        layout.addWidget(self.time_from)

        layout.addWidget(QLabel("Do:"))

        self.time_to = QTimeEdit()
        self.time_to.setDisplayFormat("HH:mm")
        self.time_to.setTime(QTime(10, 0))
        self.time_to.timeChanged.connect(self.on_range_changed)
        layout.addWidget(self.time_to)

        self.lbl_duration = QLabel("(1:00)")
        self.lbl_duration.setStyleSheet("color: #666;")
        layout.addWidget(self.lbl_duration)

    def on_range_changed(self):
        time_from = self.time_from.time()
        time_to = self.time_to.time()

        seconds_diff = time_from.secsTo(time_to)
        if seconds_diff < 0:
            seconds_diff += 86400

        hours = seconds_diff // 3600
        minutes = (seconds_diff % 3600) // 60
        self.lbl_duration.setText(f"({hours}:{minutes:02d})")

        self.range_changed.emit(time_from, time_to)

    def get_range(self):
        return self.time_from.time(), self.time_to.time()

    def set_range(self, from_time, to_time):
        self.time_from.setTime(from_time)
        self.time_to.setTime(to_time)


class QuickEventDialog(QDialog):
    """Rychlý dialog pro přidání události"""

    event_created = pyqtSignal(dict)

    def __init__(self, default_date=None, default_time=None, parent=None):
        super().__init__(parent)
        self.default_date = default_date or QDate.currentDate()
        self.default_time = default_time or QTime(9, 0)

        self.setWindowTitle("Rychlá událost")
        self.setFixedSize(400, 300)
        self.setModal(True)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText("Název události...")
        form.addRow("Název:", self.txt_title)

        self.cmb_type = QComboBox()
        self.cmb_type.addItem("🔧 Servis", "service")
        self.cmb_type.addItem("📞 Schůzka", "meeting")
        self.cmb_type.addItem("📦 Příjem dílu", "delivery")
        self.cmb_type.addItem("🚗 Předání", "handover")
        self.cmb_type.addItem("⏰ Připomínka", "reminder")
        form.addRow("Typ:", self.cmb_type)

        self.dt_datetime = QDateTimeEdit()
        self.dt_datetime.setCalendarPopup(True)
        self.dt_datetime.setDateTime(QDateTime(self.default_date, self.default_time))
        self.dt_datetime.setDisplayFormat("dd.MM.yyyy HH:mm")
        form.addRow("Datum a čas:", self.dt_datetime)

        self.cmb_mechanic = MechanicSelector()
        form.addRow("Mechanik:", self.cmb_mechanic)

        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_create = QPushButton("✅ Vytvořit")
        btn_create.setObjectName("primaryButton")
        btn_create.clicked.connect(self.create_event)
        buttons.addWidget(btn_create)

        layout.addLayout(buttons)

        self.setStyleSheet(f"""
            QLineEdit, QComboBox, QDateTimeEdit {{
                padding: 8px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }}
            #primaryButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: bold;
            }}
        """)

    def create_event(self):
        if not self.txt_title.text().strip():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Chyba", "Zadejte název události.")
            return

        event_data = {
            'title': self.txt_title.text().strip(),
            'event_type': self.cmb_type.currentData(),
            'datetime': self.dt_datetime.dateTime(),
            'mechanic_id': self.cmb_mechanic.currentData()
        }

        self.event_created.emit(event_data)
        self.accept()
