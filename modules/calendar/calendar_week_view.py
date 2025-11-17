# -*- coding: utf-8 -*-
"""
Týdenní pohled kalendáře s hodinovým rozvrhem
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea, QSplitter, QToolTip
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTime, QTimer, QRect
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush
from datetime import datetime, date, timedelta, time
from database_manager import db
import config


class WeekEventBlock(QFrame):
    """Widget pro událost v týdenním pohledu"""

    clicked = pyqtSignal(int)
    double_clicked = pyqtSignal(int)

    def __init__(self, event_data, parent=None):
        super().__init__(parent)
        self.event_data = event_data
        self.event_id = event_data.get('id')

        self.setObjectName("weekEventBlock")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setup_ui()
        self.setup_style()
        self.create_tooltip()

    def setup_ui(self):
        """Nastavení UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 3, 4, 3)
        layout.setSpacing(1)

        # Ikona typu + čas
        type_icons = {
            'service': '🔧',
            'meeting': '📞',
            'delivery': '📦',
            'handover': '🚗',
            'reminder': '⏰',
            'other': '📅'
        }
        icon = type_icons.get(self.event_data.get('event_type', 'other'), '📅')

        # Čas
        time_text = ""
        if self.event_data.get('start_datetime'):
            try:
                start = datetime.fromisoformat(self.event_data['start_datetime'])
                end_str = ""
                if self.event_data.get('end_datetime'):
                    end = datetime.fromisoformat(self.event_data['end_datetime'])
                    end_str = f" - {end.strftime('%H:%M')}"
                time_text = f"{start.strftime('%H:%M')}{end_str}"
            except:
                pass

        time_label = QLabel(f"{icon} {time_text}")
        time_label.setObjectName("eventTime")
        time_label.setStyleSheet("font-size: 10px; font-weight: bold; color: white;")
        layout.addWidget(time_label)

        # Název
        title = self.event_data.get('title', 'Událost')
        if len(title) > 25:
            title = title[:22] + "..."
        title_label = QLabel(title)
        title_label.setObjectName("eventTitle")
        title_label.setStyleSheet("font-size: 11px; color: white;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Zákazník/vozidlo (pokud je místo)
        if self.event_data.get('customer_name'):
            customer = self.event_data['customer_name']
            if len(customer) > 20:
                customer = customer[:17] + "..."
            cust_label = QLabel(f"👤 {customer}")
            cust_label.setStyleSheet("font-size: 9px; color: rgba(255,255,255,0.9);")
            layout.addWidget(cust_label)

        # Mechanik (iniciály)
        if self.event_data.get('mechanic_name'):
            name = self.event_data['mechanic_name']
            initials = ''.join([n[0].upper() for n in name.split()[:2]])
            mech_label = QLabel(f"👷 {initials}")
            mech_label.setStyleSheet("font-size: 9px; color: rgba(255,255,255,0.9);")
            layout.addWidget(mech_label)

        # Ikona stavu
        status_icons = {
            'scheduled': '📅',
            'confirmed': '✅',
            'in_progress': '🔄',
            'completed': '✔️',
            'cancelled': '❌'
        }
        status = self.event_data.get('status', 'scheduled')
        if status != 'scheduled':
            status_label = QLabel(status_icons.get(status, ''))
            status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            layout.addWidget(status_label)

        layout.addStretch()

    def setup_style(self):
        """Nastavení stylu podle barvy události"""
        color = self.event_data.get('color', '#3498db')
        self.setStyleSheet(f"""
            #weekEventBlock {{
                background-color: {color};
                border-radius: 4px;
                border-left: 4px solid {self.darken_color(color)};
            }}
            #weekEventBlock:hover {{
                background-color: {self.lighten_color(color)};
            }}
        """)

    def darken_color(self, hex_color):
        """Ztmavení barvy"""
        try:
            color = QColor(hex_color)
            return color.darker(120).name()
        except:
            return "#2980b9"

    def lighten_color(self, hex_color):
        """Zesvětlení barvy"""
        try:
            color = QColor(hex_color)
            return color.lighter(110).name()
        except:
            return "#5dade2"

    def create_tooltip(self):
        """Vytvoření tooltipu"""
        lines = [f"<b>{self.event_data.get('title', 'Událost')}</b>"]

        if self.event_data.get('start_datetime'):
            try:
                start = datetime.fromisoformat(self.event_data['start_datetime'])
                end_str = ""
                if self.event_data.get('end_datetime'):
                    end = datetime.fromisoformat(self.event_data['end_datetime'])
                    end_str = f" - {end.strftime('%H:%M')}"
                lines.append(f"Čas: {start.strftime('%H:%M')}{end_str}")
            except:
                pass

        if self.event_data.get('customer_name'):
            lines.append(f"Zákazník: {self.event_data['customer_name']}")

        if self.event_data.get('vehicle_info'):
            lines.append(f"Vozidlo: {self.event_data['vehicle_info']}")

        if self.event_data.get('mechanic_name'):
            lines.append(f"Mechanik: {self.event_data['mechanic_name']}")

        if self.event_data.get('description'):
            desc = self.event_data['description']
            if len(desc) > 100:
                desc = desc[:97] + "..."
            lines.append(f"Popis: {desc}")

        self.setToolTip("<br>".join(lines))

    def mousePressEvent(self, event):
        """Kliknutí"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.event_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Dvojklik"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.event_id)
        super().mouseDoubleClickEvent(event)


class TimeSlot(QFrame):
    """Widget pro časový slot"""

    clicked = pyqtSignal(QDate, QTime)
    double_clicked = pyqtSignal(QDate, QTime)

    def __init__(self, date_obj, time_obj, parent=None):
        super().__init__(parent)
        self.date = date_obj
        self.time = time_obj
        self.is_working_hours = self.check_working_hours()

        self.setObjectName("timeSlot")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(30)
        self.setup_style()

    def check_working_hours(self):
        """Kontrola zda je slot v pracovní době"""
        hour = self.time.hour()
        day_of_week = self.date.dayOfWeek()

        # Neděle
        if day_of_week == 7:
            return False
        # Sobota
        elif day_of_week == 6:
            return 8 <= hour < 12
        # Pracovní dny
        else:
            return 8 <= hour < 17

    def setup_style(self):
        """Nastavení stylu"""
        if self.is_working_hours:
            bg_color = "white"
        else:
            bg_color = "#f5f5f5"

        self.setStyleSheet(f"""
            #timeSlot {{
                background-color: {bg_color};
                border: 1px solid #e8e8e8;
            }}
            #timeSlot:hover {{
                background-color: #e3f2fd;
                border-color: {config.COLOR_SECONDARY};
            }}
        """)

    def mousePressEvent(self, event):
        """Kliknutí na slot"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.date, self.time)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Dvojklik - nová událost"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.date, self.time)
        super().mouseDoubleClickEvent(event)


class CalendarWeekView(QWidget):
    """Widget pro týdenní pohled kalendáře"""

    date_clicked = pyqtSignal(QDate)
    time_slot_clicked = pyqtSignal(QDate, QTime)
    time_slot_double_clicked = pyqtSignal(QDate, QTime)
    event_clicked = pyqtSignal(int)
    event_double_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_date = QDate.currentDate()
        self.week_start = self.get_week_start()
        self.mechanic_filter = None
        self.event_type_filter = None
        self.slot_interval = 30  # minuty
        self.start_hour = 6
        self.end_hour = 20
        self.events_cache = {}

        self.init_ui()
        self.setup_current_time_line()

    def init_ui(self):
        """Inicializace UI"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Hlavní splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Levý panel - časová osa + mřížka
        left_widget = self.create_calendar_grid()
        splitter.addWidget(left_widget)

        # Pravý panel - statistiky (volitelný)
        right_widget = self.create_side_panel()
        splitter.addWidget(right_widget)

        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([900, 200])

        main_layout.addWidget(splitter)

    def create_calendar_grid(self):
        """Vytvoření hlavní mřížky kalendáře"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Hlavička s dny
        header = self.create_week_header()
        layout.addWidget(header)

        # Scrollovací oblast pro časovou mřížku
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Grid s časovou osou
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(0)

        scroll.setWidget(self.grid_widget)
        layout.addWidget(scroll)

        return widget

    def create_week_header(self):
        """Vytvoření hlavičky s dny v týdnu"""
        header = QFrame()
        header.setObjectName("weekHeader")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        # Prázdný prostor pro časovou osu
        time_spacer = QLabel("")
        time_spacer.setFixedWidth(60)
        time_spacer.setObjectName("timeColumn")
        header_layout.addWidget(time_spacer)

        # Dny v týdnu
        days_cz = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]
        self.day_labels = []

        for i in range(7):
            day_date = self.week_start.addDays(i)

            day_widget = QFrame()
            day_widget.setObjectName("dayHeader")
            day_layout = QVBoxLayout(day_widget)
            day_layout.setContentsMargins(5, 5, 5, 5)
            day_layout.setSpacing(2)

            # Název dne
            day_name = QLabel(days_cz[i])
            day_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            day_name.setObjectName("dayName")
            font = QFont()
            font.setBold(True)
            day_name.setFont(font)

            # Datum
            date_label = QLabel(f"{day_date.day()}.{day_date.month()}.")
            date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            date_label.setObjectName("dateLabel")

            # Zvýraznění dnešního dne
            if day_date == QDate.currentDate():
                day_widget.setStyleSheet(f"""
                    #dayHeader {{
                        background-color: {config.COLOR_SECONDARY};
                        border-radius: 5px;
                    }}
                """)
                day_name.setStyleSheet("color: white; font-weight: bold;")
                date_label.setStyleSheet("color: white;")
            elif i >= 5:  # Víkend
                day_name.setStyleSheet("color: #e74c3c;")

            day_layout.addWidget(day_name)
            day_layout.addWidget(date_label)

            self.day_labels.append(day_widget)
            header_layout.addWidget(day_widget, 1)

        header.setStyleSheet("""
            #weekHeader {
                background-color: #f8f9fa;
                border-bottom: 2px solid #e0e0e0;
            }
            #timeColumn {
                background-color: #f0f0f0;
                border-right: 1px solid #e0e0e0;
            }
        """)

        return header

    def create_side_panel(self):
        """Vytvoření bočního panelu"""
        panel = QFrame()
        panel.setObjectName("sidePanel")
        panel.setMinimumWidth(180)
        panel.setMaximumWidth(250)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Statistiky týdne
        stats_label = QLabel("📊 Statistiky týdne")
        stats_label.setObjectName("sectionLabel")
        font = QFont()
        font.setBold(True)
        stats_label.setFont(font)
        layout.addWidget(stats_label)

        self.lbl_week_events = QLabel("Celkem událostí: 0")
        self.lbl_week_hours = QLabel("Naplánované hodiny: 0")
        self.lbl_week_confirmed = QLabel("Potvrzeno: 0")
        self.lbl_week_pending = QLabel("Čeká: 0")

        for lbl in [self.lbl_week_events, self.lbl_week_hours,
                    self.lbl_week_confirmed, self.lbl_week_pending]:
            lbl.setObjectName("statLabel")
            layout.addWidget(lbl)

        layout.addSpacing(20)

        # Dnešní události
        today_label = QLabel("📅 Dnes")
        today_label.setObjectName("sectionLabel")
        today_label.setFont(font)
        layout.addWidget(today_label)

        self.today_events_list = QVBoxLayout()
        self.today_events_list.setSpacing(5)
        layout.addLayout(self.today_events_list)

        layout.addStretch()

        panel.setStyleSheet("""
            #sidePanel {
                background-color: white;
                border-left: 1px solid #e0e0e0;
            }
            #sectionLabel {
                color: #2c3e50;
                padding: 5px 0;
            }
            #statLabel {
                color: #555;
                font-size: 12px;
                padding: 2px 0;
            }
        """)

        return panel

    def get_week_start(self):
        """Získání začátku týdne (pondělí)"""
        day_of_week = self.current_date.dayOfWeek()
        return self.current_date.addDays(-(day_of_week - 1))

    def set_current_date(self, date):
        """Nastavení aktuálního data"""
        self.current_date = date
        self.week_start = self.get_week_start()

    def set_filters(self, mechanic_id=None, event_type=None):
        """Nastavení filtrů"""
        self.mechanic_filter = mechanic_id
        self.event_type_filter = event_type

    def setup_current_time_line(self):
        """Nastavení aktualizace červené linie aktuálního času"""
        self.time_line_timer = QTimer(self)
        self.time_line_timer.timeout.connect(self.update_current_time_line)
        self.time_line_timer.start(60000)  # Každou minutu

    def update_current_time_line(self):
        """Aktualizace pozice červené linie"""
        # TODO: Implementovat vizuální linii aktuálního času
        pass

    def refresh(self):
        """Obnovení zobrazení"""
        self.week_start = self.get_week_start()
        self.build_time_grid()
        self.load_events()
        self.load_statistics()
        self.update_header()

    def update_header(self):
        """Aktualizace hlavičky s daty"""
        days_cz = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]

        for i, day_widget in enumerate(self.day_labels):
            day_date = self.week_start.addDays(i)

            # Najít a aktualizovat labely
            name_label = day_widget.findChild(QLabel, "dayName")
            date_label = day_widget.findChild(QLabel, "dateLabel")

            if date_label:
                date_label.setText(f"{day_date.day()}.{day_date.month()}.")

            # Reset stylů
            day_widget.setStyleSheet("")
            if name_label:
                if day_date == QDate.currentDate():
                    day_widget.setStyleSheet(f"""
                        #dayHeader {{
                            background-color: {config.COLOR_SECONDARY};
                            border-radius: 5px;
                        }}
                    """)
                    name_label.setStyleSheet("color: white; font-weight: bold;")
                    if date_label:
                        date_label.setStyleSheet("color: white;")
                elif i >= 5:
                    name_label.setStyleSheet("color: #e74c3c;")
                    if date_label:
                        date_label.setStyleSheet("")
                else:
                    name_label.setStyleSheet("")
                    if date_label:
                        date_label.setStyleSheet("")

    def build_time_grid(self):
        """Sestavení časové mřížky"""
        # Vyčistit
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Časové sloty
        row = 0
        for hour in range(self.start_hour, self.end_hour):
            for minute in [0, 30]:  # 30 minutové sloty
                # Časový label
                time_label = QLabel(f"{hour:02d}:{minute:02d}")
                time_label.setObjectName("timeLabel")
                time_label.setFixedWidth(60)
                time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
                time_label.setStyleSheet("""
                    color: #666;
                    font-size: 11px;
                    padding: 2px 5px;
                    background-color: #f8f8f8;
                    border-right: 1px solid #e0e0e0;
                """)
                self.grid_layout.addWidget(time_label, row, 0)

                # Sloty pro každý den
                for col in range(7):
                    day_date = self.week_start.addDays(col)
                    time_obj = QTime(hour, minute)

                    slot = TimeSlot(day_date, time_obj)
                    slot.clicked.connect(self.on_slot_clicked)
                    slot.double_clicked.connect(self.on_slot_double_clicked)

                    self.grid_layout.addWidget(slot, row, col + 1)

                row += 1

        # Nastavení stretch
        self.grid_layout.setColumnStretch(0, 0)
        for i in range(1, 8):
            self.grid_layout.setColumnStretch(i, 1)

    def load_events(self):
        """Načtení událostí pro týden"""
        week_end = self.week_start.addDays(6)

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
        params = [self.week_start.toString("yyyy-MM-dd"), week_end.toString("yyyy-MM-dd")]

        if self.mechanic_filter:
            query += " AND e.mechanic_id = ?"
            params.append(self.mechanic_filter)

        if self.event_type_filter:
            query += " AND e.event_type = ?"
            params.append(self.event_type_filter)

        query += " ORDER BY e.start_datetime"

        events = db.fetch_all(query, tuple(params))
        self.events_cache = {}

        # Umístění událostí do mřížky
        for event in events:
            self.place_event_in_grid(dict(event))

    def place_event_in_grid(self, event):
        """Umístění události do mřížky"""
        if not event.get('start_datetime'):
            return

        try:
            start_dt = datetime.fromisoformat(event['start_datetime'])
            end_dt = start_dt + timedelta(hours=1)  # Výchozí 1 hodina

            if event.get('end_datetime'):
                end_dt = datetime.fromisoformat(event['end_datetime'])

            # Zjistit sloupec (den)
            event_date = QDate(start_dt.year, start_dt.month, start_dt.day)
            col = self.week_start.daysTo(event_date) + 1

            if col < 1 or col > 7:
                return

            # Zjistit řádek (čas)
            start_hour = start_dt.hour
            start_minute = start_dt.minute

            if start_hour < self.start_hour or start_hour >= self.end_hour:
                return

            # Výpočet řádku (30 min sloty)
            row = (start_hour - self.start_hour) * 2
            if start_minute >= 30:
                row += 1

            # Výpočet výšky (počet slotů)
            duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
            slot_count = max(1, duration_minutes // 30)

            # Vytvořit event block
            event_block = WeekEventBlock(event)
            event_block.clicked.connect(self.event_clicked.emit)
            event_block.double_clicked.connect(self.event_double_clicked.emit)

            # Umístit do gridu (překrýt sloty)
            self.grid_layout.addWidget(event_block, row, col, slot_count, 1)

        except Exception as e:
            print(f"Chyba při umísťování události: {e}")

    def load_statistics(self):
        """Načtení statistik týdne"""
        week_end = self.week_start.addDays(6)

        # Celkem událostí
        query = """
            SELECT COUNT(*) as count FROM calendar_events
            WHERE DATE(start_datetime) BETWEEN ? AND ? AND status != 'cancelled'
        """
        result = db.fetch_one(query, (self.week_start.toString("yyyy-MM-dd"), week_end.toString("yyyy-MM-dd")))
        total = result['count'] if result else 0
        self.lbl_week_events.setText(f"Celkem událostí: {total}")

        # Potvrzené
        query = """
            SELECT COUNT(*) as count FROM calendar_events
            WHERE DATE(start_datetime) BETWEEN ? AND ? AND status = 'confirmed'
        """
        result = db.fetch_one(query, (self.week_start.toString("yyyy-MM-dd"), week_end.toString("yyyy-MM-dd")))
        confirmed = result['count'] if result else 0
        self.lbl_week_confirmed.setText(f"Potvrzeno: {confirmed}")

        # Čeká na potvrzení
        query = """
            SELECT COUNT(*) as count FROM calendar_events
            WHERE DATE(start_datetime) BETWEEN ? AND ? AND status = 'scheduled'
        """
        result = db.fetch_one(query, (self.week_start.toString("yyyy-MM-dd"), week_end.toString("yyyy-MM-dd")))
        pending = result['count'] if result else 0
        self.lbl_week_pending.setText(f"Čeká: {pending}")

        # Naplánované hodiny (zjednodušený výpočet)
        self.lbl_week_hours.setText(f"Naplánované hodiny: ~{total}")

        # Dnešní události
        self.load_today_events()

    def load_today_events(self):
        """Načtení dnešních událostí do bočního panelu"""
        # Vyčistit
        while self.today_events_list.count():
            item = self.today_events_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        today = date.today().isoformat()
        query = """
            SELECT id, title, start_datetime, event_type, color
            FROM calendar_events
            WHERE DATE(start_datetime) = ? AND status != 'cancelled'
            ORDER BY start_datetime
            LIMIT 10
        """
        events = db.fetch_all(query, (today,))

        if not events:
            no_events = QLabel("Žádné události")
            no_events.setStyleSheet("color: #999; font-style: italic;")
            self.today_events_list.addWidget(no_events)
            return

        for event in events:
            event_frame = QFrame()
            event_frame.setStyleSheet(f"""
                background-color: {event['color'] or '#3498db'};
                border-radius: 3px;
                padding: 5px;
            """)
            event_layout = QVBoxLayout(event_frame)
            event_layout.setContentsMargins(5, 3, 5, 3)
            event_layout.setSpacing(2)

            # Čas
            time_str = ""
            if event['start_datetime']:
                try:
                    dt = datetime.fromisoformat(event['start_datetime'])
                    time_str = dt.strftime('%H:%M')
                except:
                    pass

            time_label = QLabel(time_str)
            time_label.setStyleSheet("color: white; font-size: 10px; font-weight: bold;")
            event_layout.addWidget(time_label)

            # Název
            title = event['title']
            if len(title) > 20:
                title = title[:17] + "..."
            title_label = QLabel(title)
            title_label.setStyleSheet("color: white; font-size: 11px;")
            event_layout.addWidget(title_label)

            self.today_events_list.addWidget(event_frame)

    def on_slot_clicked(self, date, time):
        """Kliknutí na časový slot"""
        self.time_slot_clicked.emit(date, time)

    def on_slot_double_clicked(self, date, time):
        """Dvojklik na slot - nová událost"""
        self.time_slot_double_clicked.emit(date, time)
