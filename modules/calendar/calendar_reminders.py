# -*- coding: utf-8 -*-
"""
Správa připomínek a notifikací
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QLabel,
    QComboBox, QFrame, QScrollArea, QCheckBox, QMessageBox,
    QTextEdit, QDialog, QFormLayout, QDateTimeEdit, QLineEdit,
    QGroupBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QDate, QDateTime, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QIcon
from datetime import datetime, date, timedelta
from database_manager import db
import config


class ReminderCard(QFrame):
    """Karta připomínky"""

    completed = pyqtSignal(int)
    postponed = pyqtSignal(int)
    clicked = pyqtSignal(int)

    def __init__(self, reminder_data, parent=None):
        super().__init__(parent)
        self.reminder_id = reminder_data.get('id')
        self.reminder_data = reminder_data

        self.setObjectName("reminderCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        header = QHBoxLayout()

        type_icons = {
            'event': '🔔',
            'call': '📞',
            'order_part': '📦',
            'handover': '🚗',
            'complete_order': '📋',
            'invoice': '💰',
            'stk': '📅',
            'insurance': '🛡️'
        }
        icon = type_icons.get(self.reminder_data.get('reminder_type', 'event'), '🔔')

        title = self.reminder_data.get('title', 'Připomínka')
        title_label = QLabel(f"{icon} {title}")
        title_label.setObjectName("reminderTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        title_label.setFont(font)
        header.addWidget(title_label)

        header.addStretch()

        priority = self.reminder_data.get('priority', 'normal')
        if priority == 'high':
            priority_label = QLabel("🔴 Urgentní")
        elif priority == 'low':
            priority_label = QLabel("🟢 Nízká")
        else:
            priority_label = QLabel("🟡 Normální")
        priority_label.setObjectName("priorityLabel")
        header.addWidget(priority_label)

        layout.addLayout(header)

        if self.reminder_data.get('remind_at'):
            remind_dt = datetime.fromisoformat(self.reminder_data['remind_at'])
            time_label = QLabel(f"⏰ {remind_dt.strftime('%d.%m.%Y %H:%M')}")
            time_label.setObjectName("timeLabel")
            layout.addWidget(time_label)

        if self.reminder_data.get('description'):
            desc = self.reminder_data['description']
            if len(desc) > 100:
                desc = desc[:97] + "..."
            desc_label = QLabel(desc)
            desc_label.setObjectName("descLabel")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        if self.reminder_data.get('customer_name'):
            customer_label = QLabel(f"👤 {self.reminder_data['customer_name']}")
            customer_label.setObjectName("infoLabel")
            layout.addWidget(customer_label)

        if self.reminder_data.get('vehicle_info'):
            vehicle_label = QLabel(f"🏍️ {self.reminder_data['vehicle_info']}")
            vehicle_label.setObjectName("infoLabel")
            layout.addWidget(vehicle_label)

        buttons = QHBoxLayout()

        btn_complete = QPushButton("✅ Splněno")
        btn_complete.setObjectName("completeButton")
        btn_complete.setFixedHeight(30)
        btn_complete.clicked.connect(lambda: self.completed.emit(self.reminder_id))
        buttons.addWidget(btn_complete)

        btn_postpone = QPushButton("⏰ Odložit")
        btn_postpone.setObjectName("postponeButton")
        btn_postpone.setFixedHeight(30)
        btn_postpone.clicked.connect(lambda: self.postponed.emit(self.reminder_id))
        buttons.addWidget(btn_postpone)

        layout.addLayout(buttons)

    def setup_style(self):
        urgency = self.reminder_data.get('urgency', 'normal')

        if urgency == 'overdue':
            bg_color = "#ffebee"
            border_color = "#ef5350"
        elif urgency == 'today':
            bg_color = "#fff3e0"
            border_color = "#ff9800"
        elif urgency == 'tomorrow':
            bg_color = "#fffde7"
            border_color = "#fdd835"
        else:
            bg_color = "#f5f5f5"
            border_color = "#bdbdbd"

        self.setStyleSheet(f"""
            #reminderCard {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
            }}
            #reminderCard:hover {{
                background-color: white;
            }}
            #reminderTitle {{
                color: #2c3e50;
            }}
            #priorityLabel {{
                font-size: 10px;
            }}
            #timeLabel {{
                color: #555;
                font-size: 11px;
            }}
            #descLabel {{
                color: #666;
                font-size: 11px;
            }}
            #infoLabel {{
                color: #777;
                font-size: 10px;
            }}
            #completeButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }}
            #completeButton:hover {{
                background-color: #229954;
            }}
            #postponeButton {{
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }}
            #postponeButton:hover {{
                background-color: #e0e0e0;
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.reminder_id)
        super().mousePressEvent(event)


class NewReminderDialog(QDialog):
    """Dialog pro vytvoření nové připomínky"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nová připomínka")
        self.setMinimumSize(500, 450)
        self.setModal(True)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText("Název připomínky...")
        form.addRow("Název: *", self.txt_title)

        self.cmb_type = QComboBox()
        self.cmb_type.addItem("🔔 Servisní termín", "event")
        self.cmb_type.addItem("📞 Zavolat zákazníkovi", "call")
        self.cmb_type.addItem("📦 Objednat díl", "order_part")
        self.cmb_type.addItem("🚗 Předání vozidla", "handover")
        self.cmb_type.addItem("📋 Dokončit zakázku", "complete_order")
        self.cmb_type.addItem("💰 Fakturace", "invoice")
        self.cmb_type.addItem("📅 STK končí", "stk")
        self.cmb_type.addItem("🛡️ Pojištění končí", "insurance")
        form.addRow("Typ:", self.cmb_type)

        self.dt_remind = QDateTimeEdit()
        self.dt_remind.setCalendarPopup(True)
        self.dt_remind.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.dt_remind.setDisplayFormat("dd.MM.yyyy HH:mm")
        form.addRow("Připomenout: *", self.dt_remind)

        self.cmb_priority = QComboBox()
        self.cmb_priority.addItem("🟢 Nízká", "low")
        self.cmb_priority.addItem("🟡 Normální", "normal")
        self.cmb_priority.addItem("🔴 Vysoká", "high")
        self.cmb_priority.setCurrentIndex(1)
        form.addRow("Priorita:", self.cmb_priority)

        self.txt_description = QTextEdit()
        self.txt_description.setPlaceholderText("Popis připomínky...")
        self.txt_description.setMaximumHeight(100)
        form.addRow("Popis:", self.txt_description)

        layout.addLayout(form)

        notif_group = QGroupBox("Notifikace")
        notif_layout = QVBoxLayout(notif_group)

        self.chk_app_notification = QCheckBox("Notifikace v aplikaci")
        self.chk_app_notification.setChecked(True)
        notif_layout.addWidget(self.chk_app_notification)

        self.chk_email = QCheckBox("Odeslat email")
        notif_layout.addWidget(self.chk_email)

        self.chk_sms = QCheckBox("Odeslat SMS")
        notif_layout.addWidget(self.chk_sms)

        layout.addWidget(notif_group)

        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Uložit")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self.save_reminder)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

        self.setStyleSheet(f"""
            QLineEdit, QTextEdit, QComboBox, QDateTimeEdit {{
                padding: 8px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
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
        """)

    def save_reminder(self):
        if not self.txt_title.text().strip():
            QMessageBox.warning(self, "Chyba", "Název připomínky je povinný.")
            return

        data = {
            'title': self.txt_title.text().strip(),
            'reminder_type': self.cmb_type.currentData(),
            'remind_at': self.dt_remind.dateTime().toString(Qt.DateFormat.ISODate),
            'priority': self.cmb_priority.currentData(),
            'description': self.txt_description.toPlainText().strip(),
            'method': 'app' if self.chk_app_notification.isChecked() else 'none',
            'sent': 0,
            'created_at': datetime.now().isoformat()
        }

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        query = f"INSERT INTO calendar_reminders ({columns}) VALUES ({placeholders})"

        try:
            db.execute_query(query, tuple(data.values()))
            QMessageBox.information(self, "Úspěch", "Připomínka byla vytvořena.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při ukládání: {e}")


class CalendarReminders(QWidget):
    """Widget pro správu připomínek"""

    reminder_completed = pyqtSignal(int)
    reminder_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_ui()
        self.setup_auto_refresh()
        self.refresh()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        top_panel = self.create_top_panel()
        main_layout.addWidget(top_panel)

        content_layout = QHBoxLayout()

        reminders_panel = self.create_reminders_panel()
        content_layout.addWidget(reminders_panel, 3)

        side_panel = self.create_side_panel()
        content_layout.addWidget(side_panel, 1)

        main_layout.addLayout(content_layout)

        stats_panel = self.create_stats_panel()
        main_layout.addWidget(stats_panel)

    def create_top_panel(self):
        panel = QFrame()
        panel.setObjectName("topPanel")
        panel.setFixedHeight(60)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(15, 10, 15, 10)

        title = QLabel("⏰ Připomínky a notifikace")
        title.setObjectName("panelTitle")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        layout.addStretch()

        filter_label = QLabel("Zobrazit:")
        layout.addWidget(filter_label)

        self.cmb_filter = QComboBox()
        self.cmb_filter.addItem("Všechny aktivní", "active")
        self.cmb_filter.addItem("Dnes", "today")
        self.cmb_filter.addItem("Tento týden", "week")
        self.cmb_filter.addItem("Po splatnosti", "overdue")
        self.cmb_filter.addItem("Splněné", "completed")
        self.cmb_filter.currentIndexChanged.connect(self.refresh)
        layout.addWidget(self.cmb_filter)

        layout.addSpacing(20)

        self.btn_new = QPushButton("➕ Nová připomínka")
        self.btn_new.setObjectName("primaryButton")
        self.btn_new.clicked.connect(self.create_reminder)
        layout.addWidget(self.btn_new)

        self.btn_generate = QPushButton("🔄 Generovat automatické")
        self.btn_generate.setObjectName("actionButton")
        self.btn_generate.clicked.connect(self.generate_automatic)
        layout.addWidget(self.btn_generate)

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
            #actionButton {{
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 8px 15px;
            }}
            QComboBox {{
                padding: 6px 10px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }}
        """)

        return panel

    def create_reminders_panel(self):
        panel = QFrame()
        panel.setObjectName("remindersPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        overdue_group = QGroupBox("🔴 Po termínu")
        overdue_group.setObjectName("overdueGroup")
        self.overdue_layout = QVBoxLayout(overdue_group)
        self.overdue_layout.setSpacing(8)
        layout.addWidget(overdue_group)

        today_group = QGroupBox("🟠 Dnes")
        today_group.setObjectName("todayGroup")
        self.today_layout = QVBoxLayout(today_group)
        self.today_layout.setSpacing(8)
        layout.addWidget(today_group)

        tomorrow_group = QGroupBox("🟡 Zítra")
        tomorrow_group.setObjectName("tomorrowGroup")
        self.tomorrow_layout = QVBoxLayout(tomorrow_group)
        self.tomorrow_layout.setSpacing(8)
        layout.addWidget(tomorrow_group)

        later_group = QGroupBox("⚪ Později")
        later_group.setObjectName("laterGroup")
        self.later_layout = QVBoxLayout(later_group)
        self.later_layout.setSpacing(8)
        layout.addWidget(later_group)

        layout.addStretch()

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.addWidget(panel)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_widget)
        scroll.setObjectName("remindersScroll")

        panel.setStyleSheet(f"""
            #remindersPanel {{
                background-color: #f8f9fa;
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            #overdueGroup {{
                border-color: #ef5350;
            }}
            #todayGroup {{
                border-color: #ff9800;
            }}
            #tomorrowGroup {{
                border-color: #fdd835;
            }}
            #laterGroup {{
                border-color: #bdbdbd;
            }}
        """)

        return scroll

    def create_side_panel(self):
        panel = QFrame()
        panel.setObjectName("sidePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        quick_title = QLabel("⚡ Rychlé akce")
        quick_title.setObjectName("sectionTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        quick_title.setFont(font)
        layout.addWidget(quick_title)

        self.btn_call_customer = QPushButton("📞 Zavolat zákazníkovi")
        self.btn_call_customer.clicked.connect(lambda: self.quick_reminder("call"))
        layout.addWidget(self.btn_call_customer)

        self.btn_order_part = QPushButton("📦 Objednat díl")
        self.btn_order_part.clicked.connect(lambda: self.quick_reminder("order_part"))
        layout.addWidget(self.btn_order_part)

        self.btn_invoice = QPushButton("💰 Fakturovat")
        self.btn_invoice.clicked.connect(lambda: self.quick_reminder("invoice"))
        layout.addWidget(self.btn_invoice)

        layout.addSpacing(20)

        auto_title = QLabel("🤖 Automatické připomínky")
        auto_title.setObjectName("sectionTitle")
        auto_title.setFont(font)
        layout.addWidget(auto_title)

        self.chk_stk_reminders = QCheckBox("STK připomínky")
        self.chk_stk_reminders.setChecked(True)
        layout.addWidget(self.chk_stk_reminders)

        self.chk_insurance_reminders = QCheckBox("Pojištění připomínky")
        self.chk_insurance_reminders.setChecked(True)
        layout.addWidget(self.chk_insurance_reminders)

        self.chk_service_reminders = QCheckBox("Pravidelný servis")
        self.chk_service_reminders.setChecked(False)
        layout.addWidget(self.chk_service_reminders)

        layout.addStretch()

        panel.setStyleSheet(f"""
            #sidePanel {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}
            #sectionTitle {{
                color: {config.COLOR_PRIMARY};
                padding: 5px 0;
            }}
            QPushButton {{
                padding: 10px;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                background-color: #f8f9fa;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: #e9ecef;
                border-color: {config.COLOR_SECONDARY};
            }}
        """)

        return panel

    def create_stats_panel(self):
        panel = QFrame()
        panel.setObjectName("statsPanel")
        panel.setFixedHeight(70)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(20, 10, 20, 10)

        self.lbl_total = QLabel("Celkem: 0")
        self.lbl_total.setObjectName("mainStat")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.lbl_total.setFont(font)
        layout.addWidget(self.lbl_total)

        layout.addSpacing(30)

        self.lbl_overdue = QLabel("🔴 Po termínu: 0")
        self.lbl_overdue.setObjectName("statLabel")
        layout.addWidget(self.lbl_overdue)

        self.lbl_today = QLabel("🟠 Dnes: 0")
        self.lbl_today.setObjectName("statLabel")
        layout.addWidget(self.lbl_today)

        self.lbl_week = QLabel("🟡 Tento týden: 0")
        self.lbl_week.setObjectName("statLabel")
        layout.addWidget(self.lbl_week)

        self.lbl_completed = QLabel("✅ Splněno dnes: 0")
        self.lbl_completed.setObjectName("statLabel")
        layout.addWidget(self.lbl_completed)

        layout.addStretch()

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
        """)

        return panel

    def setup_auto_refresh(self):
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(300000)

    def refresh(self):
        self.load_reminders()
        self.load_statistics()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def load_reminders(self):
        self.clear_layout(self.overdue_layout)
        self.clear_layout(self.today_layout)
        self.clear_layout(self.tomorrow_layout)
        self.clear_layout(self.later_layout)

        filter_type = self.cmb_filter.currentData()
        today = date.today()
        tomorrow = today + timedelta(days=1)
        week_end = today + timedelta(days=7)

        query = """
            SELECT
                r.id, r.title, r.reminder_type, r.remind_at,
                r.priority, r.description, r.sent,
                e.title as event_title,
                c.first_name || ' ' || c.last_name as customer_name,
                v.brand || ' ' || v.model || ' (' || v.license_plate || ')' as vehicle_info
            FROM calendar_reminders r
            LEFT JOIN calendar_events e ON r.event_id = e.id
            LEFT JOIN customers c ON e.customer_id = c.id
            LEFT JOIN vehicles v ON e.vehicle_id = v.id
            WHERE r.sent = 0
        """
        params = []

        if filter_type == "today":
            query += " AND DATE(r.remind_at) = ?"
            params.append(today.isoformat())
        elif filter_type == "week":
            query += " AND DATE(r.remind_at) BETWEEN ? AND ?"
            params.extend([today.isoformat(), week_end.isoformat()])
        elif filter_type == "overdue":
            query += " AND DATE(r.remind_at) < ?"
            params.append(today.isoformat())
        elif filter_type == "completed":
            query = query.replace("r.sent = 0", "r.sent = 1")

        query += " ORDER BY r.remind_at"

        reminders = db.fetch_all(query, tuple(params))

        for reminder in reminders:
            reminder_dict = dict(reminder)

            if reminder['remind_at']:
                remind_date = datetime.fromisoformat(reminder['remind_at']).date()

                if remind_date < today:
                    reminder_dict['urgency'] = 'overdue'
                    target_layout = self.overdue_layout
                elif remind_date == today:
                    reminder_dict['urgency'] = 'today'
                    target_layout = self.today_layout
                elif remind_date == tomorrow:
                    reminder_dict['urgency'] = 'tomorrow'
                    target_layout = self.tomorrow_layout
                else:
                    reminder_dict['urgency'] = 'later'
                    target_layout = self.later_layout
            else:
                reminder_dict['urgency'] = 'normal'
                target_layout = self.later_layout

            card = ReminderCard(reminder_dict)
            card.completed.connect(self.mark_completed)
            card.postponed.connect(self.postpone_reminder)
            card.clicked.connect(self.reminder_clicked.emit)
            target_layout.addWidget(card)

        if self.overdue_layout.count() == 0:
            self.overdue_layout.addWidget(QLabel("Žádné připomínky po termínu"))
        if self.today_layout.count() == 0:
            self.today_layout.addWidget(QLabel("Žádné připomínky na dnes"))
        if self.tomorrow_layout.count() == 0:
            self.tomorrow_layout.addWidget(QLabel("Žádné připomínky na zítra"))
        if self.later_layout.count() == 0:
            self.later_layout.addWidget(QLabel("Žádné další připomínky"))

    def load_statistics(self):
        today = date.today()
        tomorrow = today + timedelta(days=1)
        week_end = today + timedelta(days=7)

        total = db.fetch_one("SELECT COUNT(*) as count FROM calendar_reminders WHERE sent = 0")
        self.lbl_total.setText(f"Celkem: {total['count'] if total else 0}")

        overdue = db.fetch_one(
            "SELECT COUNT(*) as count FROM calendar_reminders WHERE sent = 0 AND DATE(remind_at) < ?",
            (today.isoformat(),)
        )
        self.lbl_overdue.setText(f"🔴 Po termínu: {overdue['count'] if overdue else 0}")

        today_count = db.fetch_one(
            "SELECT COUNT(*) as count FROM calendar_reminders WHERE sent = 0 AND DATE(remind_at) = ?",
            (today.isoformat(),)
        )
        self.lbl_today.setText(f"🟠 Dnes: {today_count['count'] if today_count else 0}")

        week_count = db.fetch_one(
            "SELECT COUNT(*) as count FROM calendar_reminders WHERE sent = 0 AND DATE(remind_at) BETWEEN ? AND ?",
            (today.isoformat(), week_end.isoformat())
        )
        self.lbl_week.setText(f"🟡 Tento týden: {week_count['count'] if week_count else 0}")

        completed_today = db.fetch_one(
            "SELECT COUNT(*) as count FROM calendar_reminders WHERE sent = 1 AND DATE(sent_at) = ?",
            (today.isoformat(),)
        )
        self.lbl_completed.setText(f"✅ Splněno dnes: {completed_today['count'] if completed_today else 0}")

    def create_reminder(self):
        dialog = NewReminderDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def quick_reminder(self, reminder_type):
        type_names = {
            'call': 'Zavolat zákazníkovi',
            'order_part': 'Objednat díl',
            'invoice': 'Vystavit fakturu'
        }

        title = type_names.get(reminder_type, 'Připomínka')

        data = {
            'title': title,
            'reminder_type': reminder_type,
            'remind_at': (datetime.now() + timedelta(hours=1)).isoformat(),
            'priority': 'normal',
            'description': '',
            'method': 'app',
            'sent': 0,
            'created_at': datetime.now().isoformat()
        }

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        query = f"INSERT INTO calendar_reminders ({columns}) VALUES ({placeholders})"

        try:
            db.execute_query(query, tuple(data.values()))
            QMessageBox.information(self, "Úspěch", f"Připomínka '{title}' byla vytvořena.")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při vytváření: {e}")

    def mark_completed(self, reminder_id):
        try:
            db.execute_query(
                "UPDATE calendar_reminders SET sent = 1, sent_at = ? WHERE id = ?",
                (datetime.now().isoformat(), reminder_id)
            )
            self.reminder_completed.emit(reminder_id)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při označování: {e}")

    def postpone_reminder(self, reminder_id):
        new_time = datetime.now() + timedelta(hours=24)

        try:
            db.execute_query(
                "UPDATE calendar_reminders SET remind_at = ? WHERE id = ?",
                (new_time.isoformat(), reminder_id)
            )
            QMessageBox.information(
                self,
                "Odloženo",
                f"Připomínka byla odložena na {new_time.strftime('%d.%m.%Y %H:%M')}"
            )
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při odkládání: {e}")

    def generate_automatic(self):
        generated = 0
        today = date.today()

        if self.chk_stk_reminders.isChecked():
            vehicles_stk = db.fetch_all("""
                SELECT id, brand, model, license_plate
                FROM vehicles
                WHERE id NOT IN (
                    SELECT DISTINCT v.id FROM vehicles v
                    JOIN calendar_reminders r ON r.title LIKE '%STK%' AND r.title LIKE '%' || v.license_plate || '%'
                    WHERE r.sent = 0
                )
            """)

            for vehicle in vehicles_stk:
                stk_date = today + timedelta(days=365)

                data = {
                    'title': f"STK - {vehicle['license_plate']}",
                    'reminder_type': 'stk',
                    'remind_at': stk_date.isoformat(),
                    'priority': 'high',
                    'description': f"Vozidlo {vehicle['brand']} {vehicle['model']} ({vehicle['license_plate']}) - kontrola STK",
                    'method': 'app',
                    'sent': 0,
                    'created_at': datetime.now().isoformat()
                }

                columns = ", ".join(data.keys())
                placeholders = ", ".join(["?" for _ in data])
                query = f"INSERT INTO calendar_reminders ({columns}) VALUES ({placeholders})"
                db.execute_query(query, tuple(data.values()))
                generated += 1

        if generated > 0:
            QMessageBox.information(
                self,
                "Generování dokončeno",
                f"Bylo vygenerováno {generated} automatických připomínek."
            )
            self.refresh()
        else:
            QMessageBox.information(
                self,
                "Generování",
                "Nebyly nalezeny žádné nové položky pro vygenerování připomínek."
            )
