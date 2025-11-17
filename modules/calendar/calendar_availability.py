# -*- coding: utf-8 -*-
"""
Správa dostupnosti a pracovní doby
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QLabel,
    QComboBox, QFrame, QDialog, QFormLayout, QTimeEdit,
    QCheckBox, QGroupBox, QMessageBox, QDateEdit,
    QTextEdit, QSpinBox, QTabWidget,QLineEdit
)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, date, timedelta
from database_manager import db
import config


class AvailabilityDialog(QDialog):
    """Dialog pro nastavení dostupnosti"""

    def __init__(self, mechanic_id=None, parent=None):
        super().__init__(parent)
        self.mechanic_id = mechanic_id

        title = "Nastavení dostupnosti" if not mechanic_id else "Dostupnost mechanika"
        self.setWindowTitle(title)
        self.setMinimumSize(500, 450)
        self.setModal(True)

        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        work_group = QGroupBox("Pracovní doba")
        work_layout = QVBoxLayout(work_group)

        self.day_widgets = {}
        days = [
            ("Pondělí", 1),
            ("Úterý", 2),
            ("Středa", 3),
            ("Čtvrtek", 4),
            ("Pátek", 5),
            ("Sobota", 6),
            ("Neděle", 0)
        ]

        for day_name, day_num in days:
            day_layout = QHBoxLayout()

            chk = QCheckBox(day_name)
            chk.setFixedWidth(100)
            day_layout.addWidget(chk)

            time_from = QTimeEdit()
            time_from.setDisplayFormat("HH:mm")
            time_from.setTime(QTime(8, 0))
            day_layout.addWidget(time_from)

            day_layout.addWidget(QLabel("-"))

            time_to = QTimeEdit()
            time_to.setDisplayFormat("HH:mm")
            time_to.setTime(QTime(17, 0))
            day_layout.addWidget(time_to)

            day_layout.addStretch()

            self.day_widgets[day_num] = {
                'checkbox': chk,
                'from': time_from,
                'to': time_to
            }

            work_layout.addLayout(day_layout)

        layout.addWidget(work_group)

        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Uložit")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self.save_availability)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QTimeEdit {{
                padding: 6px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }}
            #primaryButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 25px;
                font-weight: bold;
            }}
        """)

    def load_data(self):
        availability = db.fetch_all("""
            SELECT day_of_week, start_time, end_time, is_working
            FROM calendar_availability
            WHERE mechanic_id IS NULL OR mechanic_id = ?
        """, (self.mechanic_id,))

        for day_num, widgets in self.day_widgets.items():
            widgets['checkbox'].setChecked(False)
            widgets['from'].setTime(QTime(8, 0))
            widgets['to'].setTime(QTime(17, 0))

        for avail in availability:
            day_num = avail['day_of_week']
            if day_num in self.day_widgets:
                widgets = self.day_widgets[day_num]
                widgets['checkbox'].setChecked(bool(avail['is_working']))
                if avail['start_time']:
                    widgets['from'].setTime(QTime.fromString(avail['start_time'], "HH:mm"))
                if avail['end_time']:
                    widgets['to'].setTime(QTime.fromString(avail['end_time'], "HH:mm"))

    def save_availability(self):
        try:
            if self.mechanic_id:
                db.execute_query(
                    "DELETE FROM calendar_availability WHERE mechanic_id = ?",
                    (self.mechanic_id,)
                )
            else:
                db.execute_query(
                    "DELETE FROM calendar_availability WHERE mechanic_id IS NULL"
                )

            for day_num, widgets in self.day_widgets.items():
                data = {
                    'mechanic_id': self.mechanic_id,
                    'day_of_week': day_num,
                    'start_time': widgets['from'].time().toString("HH:mm"),
                    'end_time': widgets['to'].time().toString("HH:mm"),
                    'is_working': 1 if widgets['checkbox'].isChecked() else 0,
                    'created_at': datetime.now().isoformat()
                }

                columns = ", ".join(data.keys())
                placeholders = ", ".join(["?" for _ in data])
                query = f"INSERT INTO calendar_availability ({columns}) VALUES ({placeholders})"
                db.execute_query(query, tuple(data.values()))

            QMessageBox.information(self, "Úspěch", "Dostupnost byla uložena.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při ukládání: {e}")


class HolidayDialog(QDialog):
    """Dialog pro přidání svátku/volného dne"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Přidat svátek/volný den")
        self.setMinimumSize(400, 300)
        self.setModal(True)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        form = QFormLayout()
        form.setSpacing(12)

        self.dt_date = QDateEdit()
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDate(QDate.currentDate())
        form.addRow("Datum: *", self.dt_date)

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Název svátku/volného dne...")
        form.addRow("Název: *", self.txt_name)

        self.chk_closed = QCheckBox("Servis zavřen")
        self.chk_closed.setChecked(True)
        form.addRow("", self.chk_closed)

        self.txt_note = QTextEdit()
        self.txt_note.setPlaceholderText("Poznámka...")
        self.txt_note.setMaximumHeight(80)
        form.addRow("Poznámka:", self.txt_note)

        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Uložit")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self.save_holiday)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

        self.setStyleSheet(f"""
            QDateEdit, QLineEdit, QTextEdit {{
                padding: 8px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }}
            #primaryButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 25px;
                font-weight: bold;
            }}
        """)

    def save_holiday(self):
        if not self.txt_name.text().strip():
            QMessageBox.warning(self, "Chyba", "Název je povinný.")
            return

        data = {
            'holiday_date': self.dt_date.date().toString(Qt.DateFormat.ISODate),
            'name': self.txt_name.text().strip(),
            'is_closed': 1 if self.chk_closed.isChecked() else 0,
            'note': self.txt_note.toPlainText().strip(),
            'created_at': datetime.now().isoformat()
        }

        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            query = f"INSERT OR REPLACE INTO calendar_holidays ({columns}) VALUES ({placeholders})"
            db.execute_query(query, tuple(data.values()))

            QMessageBox.information(self, "Úspěch", "Svátek byl přidán.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při ukládání: {e}")


class VacationDialog(QDialog):
    """Dialog pro plánování dovolené"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plánování dovolené/absence")
        self.setMinimumSize(450, 400)
        self.setModal(True)

        self.init_ui()
        self.load_mechanics()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        form = QFormLayout()
        form.setSpacing(12)

        self.cmb_mechanic = QComboBox()
        form.addRow("Mechanik: *", self.cmb_mechanic)

        self.cmb_type = QComboBox()
        self.cmb_type.addItem("🏖️ Dovolená", "vacation")
        self.cmb_type.addItem("🤒 Nemoc", "sick")
        self.cmb_type.addItem("📚 Školení", "training")
        self.cmb_type.addItem("📅 Jiné", "other")
        form.addRow("Typ:", self.cmb_type)

        self.dt_from = QDateEdit()
        self.dt_from.setCalendarPopup(True)
        self.dt_from.setDate(QDate.currentDate())
        form.addRow("Od: *", self.dt_from)

        self.dt_to = QDateEdit()
        self.dt_to.setCalendarPopup(True)
        self.dt_to.setDate(QDate.currentDate().addDays(7))
        form.addRow("Do: *", self.dt_to)

        self.cmb_substitute = QComboBox()
        self.cmb_substitute.addItem("-- Bez zástupu --", None)
        form.addRow("Zástup:", self.cmb_substitute)

        self.txt_note = QTextEdit()
        self.txt_note.setPlaceholderText("Poznámka...")
        self.txt_note.setMaximumHeight(80)
        form.addRow("Poznámka:", self.txt_note)

        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Uložit")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self.save_vacation)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

        self.setStyleSheet(f"""
            QDateEdit, QComboBox, QTextEdit {{
                padding: 8px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }}
            #primaryButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 25px;
                font-weight: bold;
            }}
        """)

    def load_mechanics(self):
        mechanics = db.fetch_all("""
            SELECT id, full_name FROM users
            WHERE role IN ('mechanik', 'admin') AND active = 1
            ORDER BY full_name
        """)

        self.cmb_mechanic.clear()
        self.cmb_substitute.clear()
        self.cmb_substitute.addItem("-- Bez zástupu --", None)

        for m in mechanics:
            self.cmb_mechanic.addItem(f"👤 {m['full_name']}", m['id'])
            self.cmb_substitute.addItem(f"👤 {m['full_name']}", m['id'])

    def save_vacation(self):
        mechanic_id = self.cmb_mechanic.currentData()
        if not mechanic_id:
            QMessageBox.warning(self, "Chyba", "Vyberte mechanika.")
            return

        if self.dt_to.date() < self.dt_from.date():
            QMessageBox.warning(self, "Chyba", "Datum 'Do' musí být po datu 'Od'.")
            return

        absence_type = self.cmb_type.currentData()
        type_names = {
            'vacation': 'Dovolená',
            'sick': 'Nemoc',
            'training': 'Školení',
            'other': 'Absence'
        }

        mechanic_name = self.cmb_mechanic.currentText().replace("👤 ", "")

        current_date = self.dt_from.date().toPyDate()
        end_date = self.dt_to.date().toPyDate()

        try:
            while current_date <= end_date:
                if current_date.weekday() < 7:
                    event_data = {
                        'title': f"{type_names[absence_type]} - {mechanic_name}",
                        'event_type': 'other',
                        'start_datetime': f"{current_date.isoformat()}T00:00:00",
                        'end_datetime': f"{current_date.isoformat()}T23:59:59",
                        'all_day': 1,
                        'mechanic_id': mechanic_id,
                        'priority': 1,
                        'color': '#95a5a6',
                        'status': 'confirmed',
                        'notes': self.txt_note.toPlainText().strip(),
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }

                    columns = ", ".join(event_data.keys())
                    placeholders = ", ".join(["?" for _ in event_data])
                    query = f"INSERT INTO calendar_events ({columns}) VALUES ({placeholders})"
                    db.execute_query(query, tuple(event_data.values()))

                current_date += timedelta(days=1)

            QMessageBox.information(
                self,
                "Úspěch",
                f"{type_names[absence_type]} byla zaznamenána od {self.dt_from.date().toString('dd.MM.yyyy')} do {self.dt_to.date().toString('dd.MM.yyyy')}."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při ukládání: {e}")


class CalendarAvailability(QWidget):
    """Widget pro správu dostupnosti"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_ui()
        self.refresh()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        top_panel = self.create_top_panel()
        main_layout.addWidget(top_panel)

        tabs = QTabWidget()
        tabs.addTab(self.create_work_hours_tab(), "⏰ Pracovní doba")
        tabs.addTab(self.create_holidays_tab(), "🎉 Svátky")
        tabs.addTab(self.create_vacations_tab(), "🏖️ Dovolené")
        tabs.addTab(self.create_capacity_tab(), "📊 Kapacita")

        main_layout.addWidget(tabs)

    def create_top_panel(self):
        panel = QFrame()
        panel.setObjectName("topPanel")
        panel.setFixedHeight(60)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(15, 10, 15, 10)

        title = QLabel("🟢 Dostupnost a pracovní doba")
        title.setObjectName("panelTitle")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        layout.addStretch()

        self.btn_import_holidays = QPushButton("📥 Import svátků")
        self.btn_import_holidays.setObjectName("actionButton")
        self.btn_import_holidays.clicked.connect(self.import_czech_holidays)
        layout.addWidget(self.btn_import_holidays)

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
            #actionButton {{
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 8px 15px;
            }}
        """)

        return panel

    def create_work_hours_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        service_group = QGroupBox("Pracovní doba servisu (výchozí)")
        service_layout = QVBoxLayout(service_group)

        self.service_hours_table = QTableWidget()
        self.service_hours_table.setColumnCount(4)
        self.service_hours_table.setHorizontalHeaderLabels(["Den", "Otevřeno", "Od", "Do"])
        self.service_hours_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.service_hours_table.setMaximumHeight(250)
        service_layout.addWidget(self.service_hours_table)

        btn_edit_service = QPushButton("✏️ Upravit pracovní dobu servisu")
        btn_edit_service.clicked.connect(self.edit_service_hours)
        service_layout.addWidget(btn_edit_service)

        layout.addWidget(service_group)

        mechanics_group = QGroupBox("Individuální rozvrhy mechaniků")
        mechanics_layout = QVBoxLayout(mechanics_group)

        self.mechanics_table = QTableWidget()
        self.mechanics_table.setColumnCount(4)
        self.mechanics_table.setHorizontalHeaderLabels(["Mechanik", "Pracovní dny", "Hodiny/týden", "Akce"])
        self.mechanics_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        mechanics_layout.addWidget(self.mechanics_table)

        layout.addWidget(mechanics_group)

        return tab

    def create_holidays_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        header_layout = QHBoxLayout()

        year_label = QLabel("Rok:")
        header_layout.addWidget(year_label)

        self.cmb_year = QComboBox()
        current_year = date.today().year
        for year in range(current_year - 1, current_year + 3):
            self.cmb_year.addItem(str(year), year)
        self.cmb_year.setCurrentText(str(current_year))
        self.cmb_year.currentIndexChanged.connect(self.load_holidays)
        header_layout.addWidget(self.cmb_year)

        header_layout.addStretch()

        btn_add_holiday = QPushButton("➕ Přidat svátek")
        btn_add_holiday.setObjectName("primaryButton")
        btn_add_holiday.clicked.connect(self.add_holiday)
        header_layout.addWidget(btn_add_holiday)

        layout.addLayout(header_layout)

        self.holidays_table = QTableWidget()
        self.holidays_table.setColumnCount(5)
        self.holidays_table.setHorizontalHeaderLabels(["ID", "Datum", "Název", "Zavřeno", "Akce"])
        self.holidays_table.setColumnHidden(0, True)
        self.holidays_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.holidays_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.holidays_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.holidays_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.holidays_table.setColumnWidth(3, 80)
        self.holidays_table.setColumnWidth(4, 80)
        self.holidays_table.setAlternatingRowColors(True)
        layout.addWidget(self.holidays_table)

        layout.addWidget(QLabel(f"✅ Celkem svátků: <b id='holiday_count'>0</b>"))

        return tab

    def create_vacations_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        header_layout = QHBoxLayout()
        header_layout.addStretch()

        btn_plan_vacation = QPushButton("➕ Naplánovat dovolenou/absenci")
        btn_plan_vacation.setObjectName("primaryButton")
        btn_plan_vacation.clicked.connect(self.plan_vacation)
        header_layout.addWidget(btn_plan_vacation)

        layout.addLayout(header_layout)

        self.vacations_table = QTableWidget()
        self.vacations_table.setColumnCount(6)
        self.vacations_table.setHorizontalHeaderLabels(["Mechanik", "Typ", "Od", "Do", "Dní", "Poznámka"])
        self.vacations_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.vacations_table.setAlternatingRowColors(True)
        layout.addWidget(self.vacations_table)

        return tab

    def create_capacity_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        period_layout = QHBoxLayout()

        period_layout.addWidget(QLabel("Období:"))

        self.dt_capacity_from = QDateEdit()
        self.dt_capacity_from.setCalendarPopup(True)
        self.dt_capacity_from.setDate(QDate.currentDate())
        period_layout.addWidget(self.dt_capacity_from)

        period_layout.addWidget(QLabel("-"))

        self.dt_capacity_to = QDateEdit()
        self.dt_capacity_to.setCalendarPopup(True)
        self.dt_capacity_to.setDate(QDate.currentDate().addDays(30))
        period_layout.addWidget(self.dt_capacity_to)

        btn_calculate = QPushButton("📊 Vypočítat kapacitu")
        btn_calculate.clicked.connect(self.calculate_capacity)
        period_layout.addWidget(btn_calculate)

        period_layout.addStretch()

        layout.addLayout(period_layout)

        stats_frame = QFrame()
        stats_frame.setObjectName("statsFrame")
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(20, 15, 20, 15)

        self.lbl_total_hours = QLabel("Celkem hodin: 0")
        self.lbl_total_hours.setObjectName("mainStat")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        self.lbl_total_hours.setFont(font)
        stats_layout.addWidget(self.lbl_total_hours)

        stats_layout.addSpacing(30)

        self.lbl_working_days = QLabel("Pracovní dny: 0")
        self.lbl_working_days.setObjectName("statLabel")
        stats_layout.addWidget(self.lbl_working_days)

        self.lbl_holidays_count = QLabel("Svátky: 0")
        self.lbl_holidays_count.setObjectName("statLabel")
        stats_layout.addWidget(self.lbl_holidays_count)

        self.lbl_vacations_days = QLabel("Dovolené: 0 dní")
        self.lbl_vacations_days.setObjectName("statLabel")
        stats_layout.addWidget(self.lbl_vacations_days)

        stats_layout.addStretch()

        layout.addWidget(stats_frame)

        self.capacity_table = QTableWidget()
        self.capacity_table.setColumnCount(4)
        self.capacity_table.setHorizontalHeaderLabels(["Mechanik", "Dostupné hodiny", "Naplánované", "Volné"])
        self.capacity_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.capacity_table.setAlternatingRowColors(True)
        layout.addWidget(self.capacity_table)

        stats_frame.setStyleSheet(f"""
            #statsFrame {{
                background-color: #e3f2fd;
                border-radius: 8px;
                border: 1px solid #90caf9;
            }}
            #mainStat {{
                color: {config.COLOR_PRIMARY};
            }}
            #statLabel {{
                color: #555;
                font-size: 12px;
            }}
        """)

        return tab

    def refresh(self):
        self.load_service_hours()
        self.load_mechanics_availability()
        self.load_holidays()
        self.load_vacations()

    def load_service_hours(self):
        days_cz = ["Neděle", "Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota"]

        availability = db.fetch_all("""
            SELECT day_of_week, start_time, end_time, is_working
            FROM calendar_availability
            WHERE mechanic_id IS NULL
            ORDER BY CASE WHEN day_of_week = 0 THEN 7 ELSE day_of_week END
        """)

        avail_dict = {}
        for a in availability:
            avail_dict[a['day_of_week']] = a

        self.service_hours_table.setRowCount(7)

        for i in range(7):
            day_num = (i + 1) % 7

            day_item = QTableWidgetItem(days_cz[day_num])
            self.service_hours_table.setItem(i, 0, day_item)

            if day_num in avail_dict:
                avail = avail_dict[day_num]
                open_item = QTableWidgetItem("✅" if avail['is_working'] else "❌")
                from_item = QTableWidgetItem(avail['start_time'] or "")
                to_item = QTableWidgetItem(avail['end_time'] or "")
            else:
                open_item = QTableWidgetItem("❌")
                from_item = QTableWidgetItem("")
                to_item = QTableWidgetItem("")

            open_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.service_hours_table.setItem(i, 1, open_item)
            self.service_hours_table.setItem(i, 2, from_item)
            self.service_hours_table.setItem(i, 3, to_item)

    def load_mechanics_availability(self):
        mechanics = db.fetch_all("""
            SELECT id, full_name FROM users
            WHERE role IN ('mechanik', 'admin') AND active = 1
            ORDER BY full_name
        """)

        self.mechanics_table.setRowCount(len(mechanics))

        for row, mech in enumerate(mechanics):
            name_item = QTableWidgetItem(mech['full_name'])
            self.mechanics_table.setItem(row, 0, name_item)

            availability = db.fetch_all("""
                SELECT day_of_week, start_time, end_time, is_working
                FROM calendar_availability
                WHERE mechanic_id = ?
            """, (mech['id'],))

            if availability:
                working_days = sum(1 for a in availability if a['is_working'])
                total_hours = 0
                for a in availability:
                    if a['is_working'] and a['start_time'] and a['end_time']:
                        start = datetime.strptime(a['start_time'], "%H:%M")
                        end = datetime.strptime(a['end_time'], "%H:%M")
                        hours = (end - start).seconds / 3600
                        total_hours += hours

                days_item = QTableWidgetItem(f"{working_days} dní")
                hours_item = QTableWidgetItem(f"{total_hours:.0f} h")
            else:
                days_item = QTableWidgetItem("Výchozí")
                hours_item = QTableWidgetItem("Výchozí")

            self.mechanics_table.setItem(row, 1, days_item)
            self.mechanics_table.setItem(row, 2, hours_item)

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)

            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(30, 25)
            btn_edit.setToolTip("Upravit")
            btn_edit.clicked.connect(lambda checked, mid=mech['id']: self.edit_mechanic_availability(mid))
            actions_layout.addWidget(btn_edit)

            self.mechanics_table.setCellWidget(row, 3, actions_widget)

    def load_holidays(self):
        year = self.cmb_year.currentData()

        holidays = db.fetch_all("""
            SELECT id, holiday_date, name, is_closed
            FROM calendar_holidays
            WHERE strftime('%Y', holiday_date) = ?
            ORDER BY holiday_date
        """, (str(year),))

        self.holidays_table.setRowCount(len(holidays))

        for row, h in enumerate(holidays):
            id_item = QTableWidgetItem(str(h['id']))
            self.holidays_table.setItem(row, 0, id_item)

            if h['holiday_date']:
                dt = datetime.fromisoformat(h['holiday_date'])
                date_item = QTableWidgetItem(dt.strftime("%d.%m.%Y"))
            else:
                date_item = QTableWidgetItem("")
            self.holidays_table.setItem(row, 1, date_item)

            name_item = QTableWidgetItem(h['name'] or "")
            self.holidays_table.setItem(row, 2, name_item)

            closed_item = QTableWidgetItem("✅" if h['is_closed'] else "❌")
            closed_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.holidays_table.setItem(row, 3, closed_item)

            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedSize(30, 25)
            btn_delete.clicked.connect(lambda checked, hid=h['id']: self.delete_holiday(hid))
            self.holidays_table.setCellWidget(row, 4, btn_delete)

    def load_vacations(self):
        today = date.today()

        vacations = db.fetch_all("""
            SELECT
                u.full_name,
                e.title,
                MIN(DATE(e.start_datetime)) as from_date,
                MAX(DATE(e.end_datetime)) as to_date,
                COUNT(*) as days,
                e.notes
            FROM calendar_events e
            JOIN users u ON e.mechanic_id = u.id
            WHERE e.all_day = 1 AND e.event_type = 'other'
                AND (e.title LIKE '%Dovolená%' OR e.title LIKE '%Nemoc%' OR e.title LIKE '%Školení%')
                AND DATE(e.start_datetime) >= ?
            GROUP BY e.mechanic_id, e.title
            ORDER BY from_date
        """, (today.isoformat(),))

        self.vacations_table.setRowCount(len(vacations))

        for row, v in enumerate(vacations):
            self.vacations_table.setItem(row, 0, QTableWidgetItem(v['full_name'] or ""))

            title = v['title'] or ""
            if "Dovolená" in title:
                type_text = "🏖️ Dovolená"
            elif "Nemoc" in title:
                type_text = "🤒 Nemoc"
            elif "Školení" in title:
                type_text = "📚 Školení"
            else:
                type_text = "📅 Absence"
            self.vacations_table.setItem(row, 1, QTableWidgetItem(type_text))

            from_str = datetime.fromisoformat(v['from_date']).strftime("%d.%m.%Y") if v['from_date'] else ""
            to_str = datetime.fromisoformat(v['to_date']).strftime("%d.%m.%Y") if v['to_date'] else ""

            self.vacations_table.setItem(row, 2, QTableWidgetItem(from_str))
            self.vacations_table.setItem(row, 3, QTableWidgetItem(to_str))
            self.vacations_table.setItem(row, 4, QTableWidgetItem(str(v['days'])))
            self.vacations_table.setItem(row, 5, QTableWidgetItem(v['notes'] or ""))

    def edit_service_hours(self):
        dialog = AvailabilityDialog(mechanic_id=None, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def edit_mechanic_availability(self, mechanic_id):
        dialog = AvailabilityDialog(mechanic_id=mechanic_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def add_holiday(self):
        dialog = HolidayDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_holidays()

    def delete_holiday(self, holiday_id):
        reply = QMessageBox.question(
            self,
            "Potvrzení",
            "Opravdu chcete smazat tento svátek?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                db.execute_query("DELETE FROM calendar_holidays WHERE id = ?", (holiday_id,))
                self.load_holidays()
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Chyba při mazání: {e}")

    def plan_vacation(self):
        dialog = VacationDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_vacations()

    def import_czech_holidays(self):
        year = self.cmb_year.currentData()

        holidays = [
            (f"{year}-01-01", "Nový rok"),
            (f"{year}-05-01", "Svátek práce"),
            (f"{year}-05-08", "Den vítězství"),
            (f"{year}-07-05", "Den slovanských věrozvěstů"),
            (f"{year}-07-06", "Den upálení mistra Jana Husa"),
            (f"{year}-09-28", "Den české státnosti"),
            (f"{year}-10-28", "Den vzniku samostatného československého státu"),
            (f"{year}-11-17", "Den boje za svobodu a demokracii"),
            (f"{year}-12-24", "Štědrý den"),
            (f"{year}-12-25", "1. svátek vánoční"),
            (f"{year}-12-26", "2. svátek vánoční"),
        ]

        imported = 0
        for holiday_date, name in holidays:
            existing = db.fetch_one(
                "SELECT id FROM calendar_holidays WHERE holiday_date = ?",
                (holiday_date,)
            )

            if not existing:
                data = {
                    'holiday_date': holiday_date,
                    'name': name,
                    'is_closed': 1,
                    'created_at': datetime.now().isoformat()
                }

                columns = ", ".join(data.keys())
                placeholders = ", ".join(["?" for _ in data])
                query = f"INSERT INTO calendar_holidays ({columns}) VALUES ({placeholders})"
                db.execute_query(query, tuple(data.values()))
                imported += 1

        QMessageBox.information(
            self,
            "Import dokončen",
            f"Bylo importováno {imported} nových svátků pro rok {year}."
        )
        self.load_holidays()

    def calculate_capacity(self):
        from_date = self.dt_capacity_from.date().toPyDate()
        to_date = self.dt_capacity_to.date().toPyDate()

        working_days = 0
        current = from_date
        while current <= to_date:
            if current.weekday() < 5:
                working_days += 1
            current += timedelta(days=1)

        holidays_count = db.fetch_one("""
            SELECT COUNT(*) as count FROM calendar_holidays
            WHERE holiday_date BETWEEN ? AND ? AND is_closed = 1
        """, (from_date.isoformat(), to_date.isoformat()))
        holidays = holidays_count['count'] if holidays_count else 0

        total_hours = (working_days - holidays) * 8

        self.lbl_total_hours.setText(f"Celkem hodin: {total_hours}")
        self.lbl_working_days.setText(f"Pracovní dny: {working_days}")
        self.lbl_holidays_count.setText(f"Svátky: {holidays}")

        mechanics = db.fetch_all("""
            SELECT id, full_name FROM users
            WHERE role IN ('mechanik', 'admin') AND active = 1
            ORDER BY full_name
        """)

        self.capacity_table.setRowCount(len(mechanics))

        total_vacation_days = 0

        for row, mech in enumerate(mechanics):
            name_item = QTableWidgetItem(mech['full_name'])
            self.capacity_table.setItem(row, 0, name_item)

            vacation_days = db.fetch_one("""
                SELECT COUNT(*) as count FROM calendar_events
                WHERE mechanic_id = ? AND all_day = 1
                    AND DATE(start_datetime) BETWEEN ? AND ?
                    AND (title LIKE '%Dovolená%' OR title LIKE '%Nemoc%')
            """, (mech['id'], from_date.isoformat(), to_date.isoformat()))
            vac_days = vacation_days['count'] if vacation_days else 0
            total_vacation_days += vac_days

            available = (working_days - holidays - vac_days) * 8
            available_item = QTableWidgetItem(f"{available} h")
            self.capacity_table.setItem(row, 1, available_item)

            scheduled = db.fetch_one("""
                SELECT COUNT(*) as count FROM calendar_events
                WHERE mechanic_id = ? AND DATE(start_datetime) BETWEEN ? AND ?
                    AND all_day = 0 AND status != 'cancelled'
            """, (mech['id'], from_date.isoformat(), to_date.isoformat()))
            scheduled_hours = (scheduled['count'] if scheduled else 0) * 1
            scheduled_item = QTableWidgetItem(f"{scheduled_hours} h")
            self.capacity_table.setItem(row, 2, scheduled_item)

            free = available - scheduled_hours
            free_item = QTableWidgetItem(f"{free} h")
            if free < 0:
                free_item.setBackground(QColor("#ffebee"))
            elif free < available * 0.2:
                free_item.setBackground(QColor("#fff8e1"))
            else:
                free_item.setBackground(QColor("#e8f5e9"))
            self.capacity_table.setItem(row, 3, free_item)

        self.lbl_vacations_days.setText(f"Dovolené: {total_vacation_days} dní")
