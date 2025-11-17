# -*- coding: utf-8 -*-
"""
Měsíční pohled kalendáře
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea, QToolTip
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QCursor
from datetime import datetime, date, timedelta
from database_manager import db
import config


class DayCell(QFrame):
    """Widget pro jeden den v kalendáři"""

    clicked = pyqtSignal(QDate)
    double_clicked = pyqtSignal(QDate)
    event_clicked = pyqtSignal(int)
    event_double_clicked = pyqtSignal(int)

    def __init__(self, date_obj, is_current_month=True, parent=None):
        super().__init__(parent)
        self.date = date_obj
        self.is_current_month = is_current_month
        self.is_today = date_obj == QDate.currentDate()
        self.is_selected = False
        self.events = []
        self.is_holiday = False
        self.holiday_name = ""
        self.is_weekend = date_obj.dayOfWeek() in [6, 7]

        self.setMinimumHeight(100)
        self.setObjectName("dayCell")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

        self.init_ui()
        self.update_style()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        # Číslo dne
        self.day_label = QLabel(str(self.date.day()))
        self.day_label.setObjectName("dayNumber")
        font = QFont()
        font.setPointSize(12)
        if self.is_today:
            font.setBold(True)
        self.day_label.setFont(font)

        # Header s číslem dne
        header = QHBoxLayout()
        header.addWidget(self.day_label)
        header.addStretch()

        # Indikátor počtu událostí
        self.count_label = QLabel("")
        self.count_label.setObjectName("eventCount")
        self.count_label.setVisible(False)
        header.addWidget(self.count_label)

        layout.addLayout(header)

        # Scroll area pro události
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setObjectName("eventsScroll")
        scroll.setStyleSheet("background: transparent; border: none;")

        self.events_widget = QWidget()
        self.events_layout = QVBoxLayout(self.events_widget)
        self.events_layout.setContentsMargins(0, 0, 0, 0)
        self.events_layout.setSpacing(2)
        self.events_layout.addStretch()

        scroll.setWidget(self.events_widget)
        layout.addWidget(scroll)

    def set_events(self, events):
        """Nastavení událostí pro tento den"""
        self.events = events

        # Vyčistit staré události
        while self.events_layout.count() > 1:
            item = self.events_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Přidat nové události (max 3 zobrazené, zbytek jako číslo)
        visible_count = min(len(events), 3)
        for i in range(visible_count):
            event = events[i]
            event_widget = self.create_event_widget(event)
            self.events_layout.insertWidget(i, event_widget)

        # Pokud je více událostí, zobrazit počet
        if len(events) > 3:
            more_label = QLabel(f"+{len(events) - 3} další")
            more_label.setObjectName("moreEvents")
            more_label.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
            self.events_layout.insertWidget(3, more_label)

        # Aktualizovat indikátor
        if len(events) > 0:
            self.count_label.setText(str(len(events)))
            self.count_label.setVisible(True)
        else:
            self.count_label.setVisible(False)

    def create_event_widget(self, event):
        """Vytvoření widgetu pro událost"""
        widget = QFrame()
        widget.setObjectName("eventItem")
        widget.setCursor(Qt.CursorShape.PointingHandCursor)

        # Barva podle typu nebo vlastní barva
        color = event.get('color', '#3498db')
        widget.setStyleSheet(f"""
            #eventItem {{
                background-color: {color};
                border-radius: 3px;
                padding: 2px 4px;
            }}
        """)

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        # Ikona podle typu
        type_icons = {
            'service': '🔧',
            'meeting': '📞',
            'delivery': '📦',
            'handover': '🚗',
            'reminder': '⏰',
            'other': '📅'
        }
        icon = type_icons.get(event.get('event_type', 'other'), '📅')

        # Čas
        start_time = ""
        if event.get('start_datetime'):
            try:
                dt = datetime.fromisoformat(event['start_datetime'])
                start_time = dt.strftime('%H:%M')
            except:
                pass

        # Zkrácený název
        title = event.get('title', 'Událost')
        if len(title) > 15:
            title = title[:12] + "..."

        label = QLabel(f"{icon} {start_time} {title}")
        label.setStyleSheet("color: white; font-size: 10px;")
        layout.addWidget(label)

        # Uložit ID události pro kliknutí
        widget.event_id = event.get('id')
        widget.mousePressEvent = lambda e: self.on_event_click(event.get('id'))
        widget.mouseDoubleClickEvent = lambda e: self.on_event_double_click(event.get('id'))

        # Tooltip
        tooltip_text = self.create_event_tooltip(event)
        widget.setToolTip(tooltip_text)

        return widget

    def create_event_tooltip(self, event):
        """Vytvoření tooltipu pro událost"""
        lines = [f"<b>{event.get('title', 'Událost')}</b>"]

        if event.get('start_datetime'):
            try:
                dt = datetime.fromisoformat(event['start_datetime'])
                lines.append(f"Čas: {dt.strftime('%H:%M')}")
            except:
                pass

        if event.get('customer_name'):
            lines.append(f"Zákazník: {event['customer_name']}")

        if event.get('vehicle_info'):
            lines.append(f"Vozidlo: {event['vehicle_info']}")

        if event.get('mechanic_name'):
            lines.append(f"Mechanik: {event['mechanic_name']}")

        status_names = {
            'scheduled': 'Naplánováno',
            'confirmed': 'Potvrzeno',
            'in_progress': 'Probíhá',
            'completed': 'Dokončeno',
            'cancelled': 'Zrušeno'
        }
        status = status_names.get(event.get('status', ''), event.get('status', ''))
        lines.append(f"Stav: {status}")

        if event.get('description'):
            desc = event['description']
            if len(desc) > 100:
                desc = desc[:97] + "..."
            lines.append(f"Popis: {desc}")

        return "<br>".join(lines)

    def on_event_click(self, event_id):
        """Kliknutí na událost"""
        if event_id:
            self.event_clicked.emit(event_id)

    def on_event_double_click(self, event_id):
        """Dvojklik na událost"""
        if event_id:
            self.event_double_clicked.emit(event_id)

    def set_holiday(self, is_holiday, name=""):
        """Nastavení svátku"""
        self.is_holiday = is_holiday
        self.holiday_name = name
        self.update_style()

        if is_holiday and name:
            self.setToolTip(f"🎉 {name}")

    def set_selected(self, selected):
        """Nastavení výběru"""
        self.is_selected = selected
        self.update_style()

    def update_style(self):
        """Aktualizace stylu podle stavu"""
        if not self.is_current_month:
            bg_color = "#f5f5f5"
            text_color = "#aaa"
        elif self.is_holiday:
            bg_color = "#fff3e0"
            text_color = "#e65100"
        elif self.is_weekend:
            bg_color = "#fafafa"
            text_color = "#666"
        else:
            bg_color = "white"
            text_color = "#333"

        border_color = "#e0e0e0"
        if self.is_selected:
            border_color = config.COLOR_SECONDARY
            bg_color = "#e3f2fd"

        if self.is_today:
            self.day_label.setStyleSheet(f"""
                color: white;
                background-color: {config.COLOR_SECONDARY};
                border-radius: 12px;
                padding: 2px 6px;
                font-weight: bold;
            """)
        else:
            self.day_label.setStyleSheet(f"color: {text_color};")

        self.setStyleSheet(f"""
            #dayCell {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 5px;
            }}
            #dayCell:hover {{
                border-color: {config.COLOR_SECONDARY};
                background-color: #f0f8ff;
            }}
            #eventCount {{
                background-color: {config.COLOR_WARNING};
                color: white;
                border-radius: 10px;
                padding: 2px 6px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)

    def mousePressEvent(self, event):
        """Kliknutí na den"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.date)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Dvojklik na den"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.date)
        super().mouseDoubleClickEvent(event)


class CalendarMonthView(QWidget):
    """Widget pro měsíční pohled kalendáře"""

    date_clicked = pyqtSignal(QDate)
    event_clicked = pyqtSignal(int)
    event_double_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_date = QDate.currentDate()
        self.selected_date = None
        self.mechanic_filter = None
        self.event_type_filter = None
        self.day_cells = {}
        self.holidays = {}

        self.init_ui()
        self.load_holidays()

    def init_ui(self):
        """Inicializace UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Hlavička s dny v týdnu
        header_frame = QFrame()
        header_frame.setObjectName("weekHeader")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        days_cz = ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"]
        for i, day_name in enumerate(days_cz):
            label = QLabel(day_name)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setObjectName("weekDayLabel")
            font = QFont()
            font.setBold(True)
            label.setFont(font)

            # Víkend jinou barvou
            if i >= 5:
                label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            else:
                label.setStyleSheet("color: #2c3e50; font-weight: bold;")

            header_layout.addWidget(label)

        main_layout.addWidget(header_frame)

        # Mřížka kalendáře
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(5)

        main_layout.addWidget(self.grid_widget, 1)

        self.set_styles()

    def set_current_date(self, date):
        """Nastavení aktuálního měsíce"""
        self.current_date = date

    def set_filters(self, mechanic_id=None, event_type=None):
        """Nastavení filtrů"""
        self.mechanic_filter = mechanic_id
        self.event_type_filter = event_type

    def load_holidays(self):
        """Načtení svátků"""
        query = "SELECT holiday_date, name FROM calendar_holidays WHERE is_closed = 1"
        results = db.fetch_all(query)

        self.holidays = {}
        for row in results:
            self.holidays[row['holiday_date']] = row['name']

    def refresh(self):
        """Obnovení zobrazení"""
        self.build_calendar_grid()
        self.load_events()

    def build_calendar_grid(self):
        """Sestavení mřížky kalendáře"""
        # Vyčistit starou mřížku
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.day_cells = {}

        # První den měsíce
        first_day = QDate(self.current_date.year(), self.current_date.month(), 1)
        # Den v týdnu (1 = pondělí, 7 = neděle)
        first_weekday = first_day.dayOfWeek()

        # Počet dní v měsíci
        days_in_month = first_day.daysInMonth()

        # Předchozí měsíc
        prev_month = first_day.addMonths(-1)
        days_in_prev = prev_month.daysInMonth()

        # Vyplnění dnů z předchozího měsíce
        current_row = 0
        current_col = 0

        # Dny z předchozího měsíce
        for i in range(first_weekday - 1):
            day_num = days_in_prev - (first_weekday - 2 - i)
            day_date = QDate(prev_month.year(), prev_month.month(), day_num)
            cell = DayCell(day_date, is_current_month=False)
            self.connect_cell_signals(cell)
            self.grid_layout.addWidget(cell, current_row, current_col)
            self.day_cells[day_date.toString("yyyy-MM-dd")] = cell
            current_col += 1

        # Dny aktuálního měsíce
        for day in range(1, days_in_month + 1):
            day_date = QDate(self.current_date.year(), self.current_date.month(), day)
            cell = DayCell(day_date, is_current_month=True)
            self.connect_cell_signals(cell)

            # Kontrola svátku
            date_str = day_date.toString("yyyy-MM-dd")
            if date_str in self.holidays:
                cell.set_holiday(True, self.holidays[date_str])

            self.grid_layout.addWidget(cell, current_row, current_col)
            self.day_cells[date_str] = cell

            current_col += 1
            if current_col > 6:
                current_col = 0
                current_row += 1

        # Dny z následujícího měsíce
        next_month = first_day.addMonths(1)
        next_day = 1
        while current_col <= 6 and current_row < 6:
            day_date = QDate(next_month.year(), next_month.month(), next_day)
            cell = DayCell(day_date, is_current_month=False)
            self.connect_cell_signals(cell)
            self.grid_layout.addWidget(cell, current_row, current_col)
            self.day_cells[day_date.toString("yyyy-MM-dd")] = cell

            next_day += 1
            current_col += 1
            if current_col > 6:
                current_col = 0
                current_row += 1
                if current_row >= 6:
                    break

        # Nastavení rovnoměrného rozprostření
        for i in range(7):
            self.grid_layout.setColumnStretch(i, 1)
        for i in range(current_row + 1):
            self.grid_layout.setRowStretch(i, 1)

    def connect_cell_signals(self, cell):
        """Propojení signálů buňky"""
        cell.clicked.connect(self.on_day_clicked)
        cell.double_clicked.connect(self.on_day_double_clicked)
        cell.event_clicked.connect(self.on_event_clicked)
        cell.event_double_clicked.connect(self.on_event_double_clicked)

    def load_events(self):
        """Načtení událostí pro aktuální měsíc"""
        # Rozsah dat pro načtení (celý měsíc + přesahy)
        first_day = QDate(self.current_date.year(), self.current_date.month(), 1)
        first_weekday = first_day.dayOfWeek()
        start_date = first_day.addDays(-(first_weekday - 1))
        end_date = first_day.addMonths(1).addDays(7)

        # Sestavení dotazu
        query = """
            SELECT
                e.id, e.title, e.description, e.event_type,
                e.start_datetime, e.end_datetime, e.all_day,
                e.customer_id, e.vehicle_id, e.order_id,
                e.mechanic_id, e.priority, e.color, e.status,
                c.first_name || ' ' || c.last_name as customer_name,
                v.brand || ' ' || v.model || ' (' || v.license_plate || ')' as vehicle_info,
                u.full_name as mechanic_name
            FROM calendar_events e
            LEFT JOIN customers c ON e.customer_id = c.id
            LEFT JOIN vehicles v ON e.vehicle_id = v.id
            LEFT JOIN users u ON e.mechanic_id = u.id
            WHERE DATE(e.start_datetime) BETWEEN ? AND ?
        """
        params = [start_date.toString("yyyy-MM-dd"), end_date.toString("yyyy-MM-dd")]

        # Aplikace filtrů
        if self.mechanic_filter:
            query += " AND e.mechanic_id = ?"
            params.append(self.mechanic_filter)

        if self.event_type_filter:
            query += " AND e.event_type = ?"
            params.append(self.event_type_filter)

        query += " ORDER BY e.start_datetime"

        events = db.fetch_all(query, tuple(params))

        # Seskupení událostí podle dne
        events_by_day = {}
        for event in events:
            if event['start_datetime']:
                try:
                    dt = datetime.fromisoformat(event['start_datetime'])
                    day_str = dt.strftime("%Y-%m-%d")
                    if day_str not in events_by_day:
                        events_by_day[day_str] = []
                    events_by_day[day_str].append(dict(event))
                except Exception as e:
                    print(f"Chyba při parsování data: {e}")

        # Přiřazení událostí do buněk
        for date_str, cell in self.day_cells.items():
            if date_str in events_by_day:
                cell.set_events(events_by_day[date_str])
            else:
                cell.set_events([])

    def on_day_clicked(self, date):
        """Kliknutí na den"""
        # Zrušit výběr předchozího dne
        if self.selected_date:
            prev_str = self.selected_date.toString("yyyy-MM-dd")
            if prev_str in self.day_cells:
                self.day_cells[prev_str].set_selected(False)

        # Nastavit nový výběr
        self.selected_date = date
        date_str = date.toString("yyyy-MM-dd")
        if date_str in self.day_cells:
            self.day_cells[date_str].set_selected(True)

        self.date_clicked.emit(date)

    def on_day_double_clicked(self, date):
        """Dvojklik na den - vytvoření nové události"""
        # TODO: Otevřít dialog pro vytvoření události
        pass

    def on_event_clicked(self, event_id):
        """Kliknutí na událost"""
        self.event_clicked.emit(event_id)

    def on_event_double_clicked(self, event_id):
        """Dvojklik na událost"""
        self.event_double_clicked.emit(event_id)

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet(f"""
            #weekHeader {{
                background-color: #f8f9fa;
                border-radius: 5px;
                padding: 10px;
            }}

            #weekDayLabel {{
                font-size: 13px;
                padding: 5px;
            }}
        """)
