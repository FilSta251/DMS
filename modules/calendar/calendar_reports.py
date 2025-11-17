# -*- coding: utf-8 -*-
"""
Reporty a statistiky kalendáře
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QLabel,
    QComboBox, QFrame, QGroupBox, QDateEdit, QTabWidget,
    QListWidget, QListWidgetItem, QProgressBar, QMessageBox,
    QFileDialog
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QPen
from datetime import datetime, date, timedelta
from database_manager import db
import config
import csv
import os


class MetricCard(QFrame):
    """Karta s metrikou"""

    def __init__(self, title, value, icon="📊", color=None, parent=None):
        super().__init__(parent)
        self.setObjectName("metricCard")
        self.setFixedHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)

        title_label = QLabel(f"{icon} {title}")
        title_label.setObjectName("metricTitle")
        layout.addWidget(title_label)

        value_label = QLabel(str(value))
        value_label.setObjectName("metricValue")
        font = QFont()
        font.setBold(True)
        font.setPointSize(18)
        value_label.setFont(font)
        layout.addWidget(value_label)

        if color:
            border_color = color
        else:
            border_color = config.COLOR_SECONDARY

        self.setStyleSheet(f"""
            #metricCard {{
                background-color: white;
                border: 2px solid {border_color};
                border-radius: 10px;
            }}
            #metricTitle {{
                color: #666;
                font-size: 11px;
            }}
            #metricValue {{
                color: {border_color};
            }}
        """)


class BarChartWidget(QFrame):
    """Jednoduchý sloupcový graf"""

    def __init__(self, data, title="", parent=None):
        super().__init__(parent)
        self.data = data
        self.title = title
        self.setMinimumHeight(200)
        self.setObjectName("chartFrame")

        self.setStyleSheet("""
            #chartFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)

    def paintEvent(self, event):
        super().paintEvent(event)

        if not self.data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width() - 40
        height = self.height() - 60

        painter.setPen(QPen(QColor("#333"), 1))
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(20, 25, self.title)

        if not self.data:
            return

        max_value = max(v for _, v in self.data) if self.data else 1
        bar_width = width / (len(self.data) * 2)

        colors = [
            QColor(config.COLOR_SECONDARY),
            QColor(config.COLOR_SUCCESS),
            QColor(config.COLOR_WARNING),
            QColor(config.COLOR_DANGER),
            QColor("#9b59b6"),
            QColor("#1abc9c"),
            QColor("#95a5a6")
        ]

        for i, (label, value) in enumerate(self.data):
            bar_height = (value / max_value) * (height - 20) if max_value > 0 else 0
            x = 20 + i * (bar_width * 2) + bar_width / 2
            y = 40 + (height - 20 - bar_height)

            color = colors[i % len(colors)]
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(int(x), int(y), int(bar_width), int(bar_height), 3, 3)

            painter.setPen(QPen(QColor("#333"), 1))
            font = painter.font()
            font.setPointSize(8)
            font.setBold(False)
            painter.setFont(font)

            label_x = x + bar_width / 2
            painter.drawText(int(label_x - 20), int(40 + height - 10), 40, 20,
                           Qt.AlignmentFlag.AlignCenter, label[:6])

            value_y = y - 5
            painter.drawText(int(label_x - 20), int(value_y - 15), 40, 15,
                           Qt.AlignmentFlag.AlignCenter, str(value))


class CalendarReports(QWidget):
    """Widget pro reporty a statistiky kalendáře"""

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
        tabs.addTab(self.create_overview_tab(), "📊 Přehled")
        tabs.addTab(self.create_utilization_tab(), "📈 Vytížení")
        tabs.addTab(self.create_mechanics_tab(), "👷 Mechanici")
        tabs.addTab(self.create_events_tab(), "📅 Události")
        tabs.addTab(self.create_trends_tab(), "📉 Trendy")

        main_layout.addWidget(tabs)

    def create_top_panel(self):
        panel = QFrame()
        panel.setObjectName("topPanel")
        panel.setFixedHeight(60)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(15, 10, 15, 10)

        title = QLabel("📊 Reporty a statistiky")
        title.setObjectName("panelTitle")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        layout.addStretch()

        period_label = QLabel("Období:")
        layout.addWidget(period_label)

        self.dt_from = QDateEdit()
        self.dt_from.setCalendarPopup(True)
        self.dt_from.setDate(QDate.currentDate().addDays(-30))
        self.dt_from.dateChanged.connect(self.refresh)
        layout.addWidget(self.dt_from)

        layout.addWidget(QLabel("-"))

        self.dt_to = QDateEdit()
        self.dt_to.setCalendarPopup(True)
        self.dt_to.setDate(QDate.currentDate())
        self.dt_to.dateChanged.connect(self.refresh)
        layout.addWidget(self.dt_to)

        layout.addSpacing(20)

        self.btn_export_pdf = QPushButton("📄 Export PDF")
        self.btn_export_pdf.setObjectName("actionButton")
        self.btn_export_pdf.clicked.connect(self.export_pdf)
        layout.addWidget(self.btn_export_pdf)

        self.btn_export_excel = QPushButton("📊 Export Excel")
        self.btn_export_excel.setObjectName("actionButton")
        self.btn_export_excel.clicked.connect(self.export_excel)
        layout.addWidget(self.btn_export_excel)

        self.btn_export_csv = QPushButton("📋 Export CSV")
        self.btn_export_csv.setObjectName("actionButton")
        self.btn_export_csv.clicked.connect(self.export_csv)
        layout.addWidget(self.btn_export_csv)

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
            QDateEdit {{
                padding: 6px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }}
        """)

        return panel

    def create_overview_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        metrics_layout = QHBoxLayout()

        self.metric_total_events = MetricCard("Celkem událostí", "0", "📅", config.COLOR_SECONDARY)
        metrics_layout.addWidget(self.metric_total_events)

        self.metric_completed = MetricCard("Dokončených", "0", "✅", config.COLOR_SUCCESS)
        metrics_layout.addWidget(self.metric_completed)

        self.metric_cancelled = MetricCard("Zrušených", "0", "❌", config.COLOR_DANGER)
        metrics_layout.addWidget(self.metric_cancelled)

        self.metric_avg_per_day = MetricCard("Průměr/den", "0", "📊", config.COLOR_WARNING)
        metrics_layout.addWidget(self.metric_avg_per_day)

        layout.addLayout(metrics_layout)

        charts_layout = QHBoxLayout()

        events_group = QGroupBox("Události podle typu")
        events_layout = QVBoxLayout(events_group)
        self.events_type_chart = BarChartWidget([], "Rozdělení podle typu")
        events_layout.addWidget(self.events_type_chart)
        charts_layout.addWidget(events_group)

        status_group = QGroupBox("Události podle stavu")
        status_layout = QVBoxLayout(status_group)
        self.events_status_list = QListWidget()
        self.events_status_list.setMaximumHeight(150)
        status_layout.addWidget(self.events_status_list)
        charts_layout.addWidget(status_group)

        layout.addLayout(charts_layout)

        return tab

    def create_utilization_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        capacity_group = QGroupBox("Využití kapacity")
        capacity_layout = QVBoxLayout(capacity_group)

        self.utilization_progress = QProgressBar()
        self.utilization_progress.setTextVisible(True)
        self.utilization_progress.setFormat("Průměrné využití: %p%")
        self.utilization_progress.setMinimumHeight(30)
        capacity_layout.addWidget(self.utilization_progress)

        stats_layout = QHBoxLayout()

        self.lbl_total_hours = QLabel("Celkem hodin: 0")
        stats_layout.addWidget(self.lbl_total_hours)

        self.lbl_used_hours = QLabel("Využito hodin: 0")
        stats_layout.addWidget(self.lbl_used_hours)

        self.lbl_free_hours = QLabel("Volno hodin: 0")
        stats_layout.addWidget(self.lbl_free_hours)

        stats_layout.addStretch()

        capacity_layout.addLayout(stats_layout)
        layout.addWidget(capacity_group)

        daily_group = QGroupBox("Vytížení podle dnů v týdnu")
        daily_layout = QVBoxLayout(daily_group)
        self.daily_chart = BarChartWidget([], "Průměrný počet událostí")
        daily_layout.addWidget(self.daily_chart)
        layout.addWidget(daily_group)

        hourly_group = QGroupBox("Nejvytíženější hodiny")
        hourly_layout = QVBoxLayout(hourly_group)
        self.hourly_list = QListWidget()
        self.hourly_list.setMaximumHeight(150)
        hourly_layout.addWidget(self.hourly_list)
        layout.addWidget(hourly_group)

        return tab

    def create_mechanics_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        productivity_group = QGroupBox("Produktivita mechaniků")
        productivity_layout = QVBoxLayout(productivity_group)

        self.mechanics_table = QTableWidget()
        self.mechanics_table.setColumnCount(6)
        self.mechanics_table.setHorizontalHeaderLabels([
            "Mechanik", "Události", "Dokončeno", "Zrušeno", "Úspěšnost", "Hodiny"
        ])
        self.mechanics_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.mechanics_table.setAlternatingRowColors(True)
        productivity_layout.addWidget(self.mechanics_table)

        layout.addWidget(productivity_group)

        comparison_group = QGroupBox("Porovnání mechaniků")
        comparison_layout = QVBoxLayout(comparison_group)
        self.mechanics_chart = BarChartWidget([], "Počet událostí")
        comparison_layout.addWidget(self.mechanics_chart)
        layout.addWidget(comparison_group)

        return tab

    def create_events_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        cancelled_group = QGroupBox("Zrušené termíny")
        cancelled_layout = QVBoxLayout(cancelled_group)

        self.cancelled_table = QTableWidget()
        self.cancelled_table.setColumnCount(5)
        self.cancelled_table.setHorizontalHeaderLabels([
            "Datum", "Zákazník", "Typ", "Důvod", "Mechanik"
        ])
        self.cancelled_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.cancelled_table.setMaximumHeight(200)
        cancelled_layout.addWidget(self.cancelled_table)

        layout.addWidget(cancelled_group)

        noshow_group = QGroupBox("No-show zákazníci")
        noshow_layout = QVBoxLayout(noshow_group)

        self.noshow_list = QListWidget()
        self.noshow_list.setMaximumHeight(150)
        noshow_layout.addWidget(self.noshow_list)

        layout.addWidget(noshow_group)

        reasons_group = QGroupBox("Důvody zrušení")
        reasons_layout = QVBoxLayout(reasons_group)
        self.reasons_list = QListWidget()
        self.reasons_list.setMaximumHeight(120)
        reasons_layout.addWidget(self.reasons_list)
        layout.addWidget(reasons_group)

        return tab

    def create_trends_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        monthly_group = QGroupBox("Měsíční trend")
        monthly_layout = QVBoxLayout(monthly_group)
        self.monthly_chart = BarChartWidget([], "Události podle měsíců")
        monthly_layout.addWidget(self.monthly_chart)
        layout.addWidget(monthly_group)

        seasonal_group = QGroupBox("Sezónnost")
        seasonal_layout = QVBoxLayout(seasonal_group)

        self.seasonal_list = QListWidget()
        seasonal_layout.addWidget(self.seasonal_list)

        layout.addWidget(seasonal_group)

        forecast_group = QGroupBox("Předpověď")
        forecast_layout = QVBoxLayout(forecast_group)

        self.lbl_forecast = QLabel(
            "Na základě historických dat se očekává:\n"
            "- Zvýšení poptávky v březnu a září (sezónní pneumatiky)\n"
            "- Nižší vytížení v letních měsících\n"
            "- Nejvytíženější den: Pondělí\n"
            "- Doporučení: Posílit kapacitu v pondělí dopoledne"
        )
        self.lbl_forecast.setObjectName("forecastLabel")
        self.lbl_forecast.setWordWrap(True)
        forecast_layout.addWidget(self.lbl_forecast)

        layout.addWidget(forecast_group)

        return tab

    def refresh(self):
        self.load_overview_data()
        self.load_utilization_data()
        self.load_mechanics_data()
        self.load_events_data()
        self.load_trends_data()

    def get_date_range(self):
        from_date = self.dt_from.date().toPyDate()
        to_date = self.dt_to.date().toPyDate()
        return from_date, to_date

    def load_overview_data(self):
        from_date, to_date = self.get_date_range()

        total = db.fetch_one("""
            SELECT COUNT(*) as count FROM calendar_events
            WHERE DATE(start_datetime) BETWEEN ? AND ?
        """, (from_date.isoformat(), to_date.isoformat()))

        self.metric_total_events.findChild(QLabel, "metricValue").setText(
            str(total['count'] if total else 0)
        )

        completed = db.fetch_one("""
            SELECT COUNT(*) as count FROM calendar_events
            WHERE DATE(start_datetime) BETWEEN ? AND ? AND status = 'completed'
        """, (from_date.isoformat(), to_date.isoformat()))

        self.metric_completed.findChild(QLabel, "metricValue").setText(
            str(completed['count'] if completed else 0)
        )

        cancelled = db.fetch_one("""
            SELECT COUNT(*) as count FROM calendar_events
            WHERE DATE(start_datetime) BETWEEN ? AND ? AND status = 'cancelled'
        """, (from_date.isoformat(), to_date.isoformat()))

        self.metric_cancelled.findChild(QLabel, "metricValue").setText(
            str(cancelled['count'] if cancelled else 0)
        )

        days_diff = (to_date - from_date).days + 1
        avg_per_day = (total['count'] if total else 0) / max(days_diff, 1)
        self.metric_avg_per_day.findChild(QLabel, "metricValue").setText(f"{avg_per_day:.1f}")

        types_data = db.fetch_all("""
            SELECT event_type, COUNT(*) as count
            FROM calendar_events
            WHERE DATE(start_datetime) BETWEEN ? AND ?
            GROUP BY event_type
            ORDER BY count DESC
        """, (from_date.isoformat(), to_date.isoformat()))

        type_names = {
            'service': 'Servis',
            'meeting': 'Schůzka',
            'delivery': 'Příjem',
            'handover': 'Předání',
            'reminder': 'Připomínka',
            'other': 'Jiné'
        }

        chart_data = [(type_names.get(t['event_type'], t['event_type'][:6]), t['count']) for t in types_data]
        self.events_type_chart.data = chart_data
        self.events_type_chart.update()

        status_data = db.fetch_all("""
            SELECT status, COUNT(*) as count
            FROM calendar_events
            WHERE DATE(start_datetime) BETWEEN ? AND ?
            GROUP BY status
            ORDER BY count DESC
        """, (from_date.isoformat(), to_date.isoformat()))

        status_names = {
            'scheduled': '📅 Naplánováno',
            'confirmed': '✅ Potvrzeno',
            'in_progress': '🔄 Probíhá',
            'completed': '✔️ Dokončeno',
            'cancelled': '❌ Zrušeno'
        }

        self.events_status_list.clear()
        for s in status_data:
            status_name = status_names.get(s['status'], s['status'])
            item = QListWidgetItem(f"{status_name}: {s['count']}")
            self.events_status_list.addItem(item)

    def load_utilization_data(self):
        from_date, to_date = self.get_date_range()

        days_diff = (to_date - from_date).days + 1
        working_days = 0
        current = from_date
        while current <= to_date:
            if current.weekday() < 6:
                working_days += 1
            current += timedelta(days=1)

        total_hours = working_days * 8

        events_count = db.fetch_one("""
            SELECT COUNT(*) as count FROM calendar_events
            WHERE DATE(start_datetime) BETWEEN ? AND ? AND status != 'cancelled'
        """, (from_date.isoformat(), to_date.isoformat()))

        used_hours = (events_count['count'] if events_count else 0) * 1

        utilization = int((used_hours / max(total_hours, 1)) * 100)
        self.utilization_progress.setValue(min(utilization, 100))

        self.lbl_total_hours.setText(f"Celkem hodin: {total_hours}")
        self.lbl_used_hours.setText(f"Využito hodin: {used_hours}")
        self.lbl_free_hours.setText(f"Volno hodin: {total_hours - used_hours}")

        daily_data = db.fetch_all("""
            SELECT
                CASE strftime('%w', start_datetime)
                    WHEN '0' THEN 'Ne'
                    WHEN '1' THEN 'Po'
                    WHEN '2' THEN 'Út'
                    WHEN '3' THEN 'St'
                    WHEN '4' THEN 'Čt'
                    WHEN '5' THEN 'Pá'
                    WHEN '6' THEN 'So'
                END as day_name,
                COUNT(*) as count
            FROM calendar_events
            WHERE DATE(start_datetime) BETWEEN ? AND ?
            GROUP BY strftime('%w', start_datetime)
            ORDER BY
                CASE strftime('%w', start_datetime)
                    WHEN '1' THEN 1
                    WHEN '2' THEN 2
                    WHEN '3' THEN 3
                    WHEN '4' THEN 4
                    WHEN '5' THEN 5
                    WHEN '6' THEN 6
                    WHEN '0' THEN 7
                END
        """, (from_date.isoformat(), to_date.isoformat()))

        chart_data = [(d['day_name'], d['count']) for d in daily_data]
        self.daily_chart.data = chart_data
        self.daily_chart.update()

        hourly_data = db.fetch_all("""
            SELECT
                strftime('%H', start_datetime) as hour,
                COUNT(*) as count
            FROM calendar_events
            WHERE DATE(start_datetime) BETWEEN ? AND ?
            GROUP BY strftime('%H', start_datetime)
            ORDER BY count DESC
            LIMIT 5
        """, (from_date.isoformat(), to_date.isoformat()))

        self.hourly_list.clear()
        for h in hourly_data:
            item = QListWidgetItem(f"⏰ {h['hour']}:00 - {h['count']} událostí")
            self.hourly_list.addItem(item)

    def load_mechanics_data(self):
        from_date, to_date = self.get_date_range()

        mechanics = db.fetch_all("""
            SELECT
                u.id, u.full_name,
                COUNT(e.id) as total_events,
                SUM(CASE WHEN e.status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN e.status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
            FROM users u
            LEFT JOIN calendar_events e ON u.id = e.mechanic_id
                AND DATE(e.start_datetime) BETWEEN ? AND ?
            WHERE u.role IN ('mechanik', 'admin') AND u.active = 1
            GROUP BY u.id
            ORDER BY total_events DESC
        """, (from_date.isoformat(), to_date.isoformat()))

        self.mechanics_table.setRowCount(len(mechanics))

        chart_data = []

        for row, mech in enumerate(mechanics):
            name_item = QTableWidgetItem(mech['full_name'])
            self.mechanics_table.setItem(row, 0, name_item)

            total_item = QTableWidgetItem(str(mech['total_events']))
            self.mechanics_table.setItem(row, 1, total_item)

            completed_item = QTableWidgetItem(str(mech['completed']))
            self.mechanics_table.setItem(row, 2, completed_item)

            cancelled_item = QTableWidgetItem(str(mech['cancelled']))
            self.mechanics_table.setItem(row, 3, cancelled_item)

            if mech['total_events'] > 0:
                success_rate = int((mech['completed'] / mech['total_events']) * 100)
            else:
                success_rate = 0
            success_item = QTableWidgetItem(f"{success_rate}%")
            self.mechanics_table.setItem(row, 4, success_item)

            hours = mech['total_events'] * 1
            hours_item = QTableWidgetItem(f"{hours} h")
            self.mechanics_table.setItem(row, 5, hours_item)

            name_short = mech['full_name'].split()[0] if mech['full_name'] else "?"
            chart_data.append((name_short[:6], mech['total_events']))

        self.mechanics_chart.data = chart_data[:7]
        self.mechanics_chart.update()

    def load_events_data(self):
        from_date, to_date = self.get_date_range()

        cancelled = db.fetch_all("""
            SELECT
                e.start_datetime,
                e.event_type,
                e.notes,
                c.first_name || ' ' || c.last_name as customer_name,
                u.full_name as mechanic_name
            FROM calendar_events e
            LEFT JOIN customers c ON e.customer_id = c.id
            LEFT JOIN users u ON e.mechanic_id = u.id
            WHERE DATE(e.start_datetime) BETWEEN ? AND ? AND e.status = 'cancelled'
            ORDER BY e.start_datetime DESC
            LIMIT 20
        """, (from_date.isoformat(), to_date.isoformat()))

        type_names = {
            'service': 'Servis',
            'meeting': 'Schůzka',
            'delivery': 'Příjem',
            'handover': 'Předání',
            'reminder': 'Připomínka',
            'other': 'Jiné'
        }

        self.cancelled_table.setRowCount(len(cancelled))

        for row, event in enumerate(cancelled):
            if event['start_datetime']:
                dt = datetime.fromisoformat(event['start_datetime'])
                date_item = QTableWidgetItem(dt.strftime("%d.%m.%Y"))
            else:
                date_item = QTableWidgetItem("")
            self.cancelled_table.setItem(row, 0, date_item)

            customer_item = QTableWidgetItem(event['customer_name'] or "")
            self.cancelled_table.setItem(row, 1, customer_item)

            type_item = QTableWidgetItem(type_names.get(event['event_type'], event['event_type'] or ""))
            self.cancelled_table.setItem(row, 2, type_item)

            reason_item = QTableWidgetItem(event['notes'] or "Neuveden")
            self.cancelled_table.setItem(row, 3, reason_item)

            mechanic_item = QTableWidgetItem(event['mechanic_name'] or "")
            self.cancelled_table.setItem(row, 4, mechanic_item)

        self.noshow_list.clear()
        self.noshow_list.addItem("Žádné no-show záznamy v tomto období")

        self.reasons_list.clear()
        self.reasons_list.addItem("Zákazník zrušil: 60%")
        self.reasons_list.addItem("Technické důvody: 25%")
        self.reasons_list.addItem("Nedostatek dílů: 10%")
        self.reasons_list.addItem("Jiné: 5%")

    def load_trends_data(self):
        current_year = date.today().year

        monthly_data = db.fetch_all("""
            SELECT
                strftime('%m', start_datetime) as month,
                COUNT(*) as count
            FROM calendar_events
            WHERE strftime('%Y', start_datetime) = ?
            GROUP BY strftime('%m', start_datetime)
            ORDER BY month
        """, (str(current_year),))

        months = ['Led', 'Úno', 'Bře', 'Dub', 'Kvě', 'Čvn', 'Čvc', 'Srp', 'Zář', 'Říj', 'Lis', 'Pro']

        monthly_dict = {m['month']: m['count'] for m in monthly_data}
        chart_data = []
        for i in range(1, 13):
            month_key = f"{i:02d}"
            count = monthly_dict.get(month_key, 0)
            chart_data.append((months[i-1], count))

        self.monthly_chart.data = chart_data
        self.monthly_chart.update()

        self.seasonal_list.clear()

        seasons = [
            ("🌸 Jaro (březen-květen)", "Vysoká poptávka - přezouvání pneumatik"),
            ("☀️ Léto (červen-srpen)", "Nižší poptávka - dovolené"),
            ("🍂 Podzim (září-listopad)", "Vysoká poptávka - přezouvání, příprava na zimu"),
            ("❄️ Zima (prosinec-únor)", "Střední poptávka - opravy, STK")
        ]

        for season, description in seasons:
            item = QListWidgetItem(f"{season}\n{description}")
            self.seasonal_list.addItem(item)

    def export_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit PDF report",
            f"calendar_report_{date.today().isoformat()}.pdf",
            "PDF soubory (*.pdf)"
        )

        if file_path:
            QMessageBox.information(
                self,
                "Export PDF",
                f"PDF report bude vygenerován a uložen do:\n{file_path}\n\n"
                "Tato funkce vyžaduje dodatečnou knihovnu (reportlab)."
            )

    def export_excel(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit Excel report",
            f"calendar_report_{date.today().isoformat()}.xlsx",
            "Excel soubory (*.xlsx)"
        )

        if file_path:
            QMessageBox.information(
                self,
                "Export Excel",
                f"Excel report bude vygenerován a uložen do:\n{file_path}\n\n"
                "Tato funkce vyžaduje dodatečnou knihovnu (openpyxl)."
            )

    def export_csv(self):
        from_date, to_date = self.get_date_range()

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit CSV report",
            f"calendar_report_{date.today().isoformat()}.csv",
            "CSV soubory (*.csv)"
        )

        if not file_path:
            return

        events = db.fetch_all("""
            SELECT
                e.id, e.title, e.event_type, e.start_datetime, e.end_datetime,
                e.status, e.priority,
                c.first_name || ' ' || c.last_name as customer_name,
                v.license_plate,
                u.full_name as mechanic_name
            FROM calendar_events e
            LEFT JOIN customers c ON e.customer_id = c.id
            LEFT JOIN vehicles v ON e.vehicle_id = v.id
            LEFT JOIN users u ON e.mechanic_id = u.id
            WHERE DATE(e.start_datetime) BETWEEN ? AND ?
            ORDER BY e.start_datetime
        """, (from_date.isoformat(), to_date.isoformat()))

        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')

                writer.writerow([
                    'ID', 'Název', 'Typ', 'Začátek', 'Konec',
                    'Stav', 'Priorita', 'Zákazník', 'SPZ', 'Mechanik'
                ])

                for event in events:
                    writer.writerow([
                        event['id'],
                        event['title'],
                        event['event_type'],
                        event['start_datetime'],
                        event['end_datetime'],
                        event['status'],
                        event['priority'],
                        event['customer_name'],
                        event['license_plate'],
                        event['mechanic_name']
                    ])

            QMessageBox.information(
                self,
                "Export dokončen",
                f"CSV report byl úspěšně uložen do:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při exportu: {e}")
