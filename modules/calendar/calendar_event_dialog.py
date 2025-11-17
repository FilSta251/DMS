# -*- coding: utf-8 -*-
"""
Dialog pro vytvoření a editaci události v kalendáři
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QDateTimeEdit,
    QCheckBox, QSpinBox, QDoubleSpinBox, QPushButton,
    QLabel, QFrame, QTabWidget, QWidget, QMessageBox,
    QColorDialog, QCompleter, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QDateTime, QDate, QTime, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QIcon
from datetime import datetime, timedelta
from database_manager import db
import config


class CalendarEventDialog(QDialog):
    """Dialog pro vytvoření/editaci události"""

    event_saved = pyqtSignal(int)  # ID uložené události
    event_deleted = pyqtSignal(int)  # ID smazané události
    create_order_requested = pyqtSignal(int)  # ID události pro vytvoření zakázky

    def __init__(self, event_id=None, default_date=None, default_time=None, parent=None):
        super().__init__(parent)
        self.event_id = event_id
        self.is_edit_mode = event_id is not None
        self.selected_color = "#3498db"
        self.default_date = default_date or QDate.currentDate()
        self.default_time = default_time or QTime(9, 0)

        self.setWindowTitle("Editace události" if self.is_edit_mode else "Nová událost")
        self.setMinimumSize(700, 650)
        self.setModal(True)

        self.init_ui()
        self.load_data()

        if self.is_edit_mode:
            self.load_event_data()
        else:
            self.set_defaults()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_basic_tab(), "📋 Základní údaje")
        self.tabs.addTab(self.create_links_tab(), "🔗 Propojení")
        self.tabs.addTab(self.create_details_tab(), "📝 Detaily")
        self.tabs.addTab(self.create_notifications_tab(), "🔔 Notifikace")

        layout.addWidget(self.tabs)

        # Tlačítka
        buttons_layout = QHBoxLayout()

        if self.is_edit_mode:
            self.btn_delete = QPushButton("🗑️ Smazat")
            self.btn_delete.setObjectName("dangerButton")
            self.btn_delete.clicked.connect(self.delete_event)
            buttons_layout.addWidget(self.btn_delete)

            self.btn_create_order = QPushButton("📋 Vytvořit zakázku")
            self.btn_create_order.setObjectName("secondaryButton")
            self.btn_create_order.clicked.connect(self.create_order)
            buttons_layout.addWidget(self.btn_create_order)

        buttons_layout.addStretch()

        self.btn_cancel = QPushButton("❌ Zrušit")
        self.btn_cancel.setObjectName("cancelButton")
        self.btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("💾 Uložit")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.clicked.connect(self.save_event)
        buttons_layout.addWidget(self.btn_save)

        layout.addLayout(buttons_layout)

        self.set_styles()

    def create_basic_tab(self):
        """Záložka základních údajů"""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Název události
        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText("Zadejte název události...")
        self.txt_title.setObjectName("mainInput")
        layout.addRow("Název události: *", self.txt_title)

        # Typ události
        self.cmb_event_type = QComboBox()
        self.cmb_event_type.addItem("🔧 Servisní termín", "service")
        self.cmb_event_type.addItem("📞 Schůzka se zákazníkem", "meeting")
        self.cmb_event_type.addItem("📦 Příjem dílu", "delivery")
        self.cmb_event_type.addItem("🚗 Předání vozidla", "handover")
        self.cmb_event_type.addItem("⏰ Připomínka", "reminder")
        self.cmb_event_type.addItem("📅 Jiné", "other")
        self.cmb_event_type.currentIndexChanged.connect(self.on_type_changed)
        layout.addRow("Typ události: *", self.cmb_event_type)

        # Celodenní událost
        self.chk_all_day = QCheckBox("Celodenní událost")
        self.chk_all_day.stateChanged.connect(self.on_all_day_changed)
        layout.addRow("", self.chk_all_day)

        # Datum a čas od
        datetime_from_layout = QHBoxLayout()
        self.dt_start = QDateTimeEdit()
        self.dt_start.setCalendarPopup(True)
        self.dt_start.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.dt_start.dateTimeChanged.connect(self.on_start_changed)
        datetime_from_layout.addWidget(self.dt_start)
        layout.addRow("Začátek: *", datetime_from_layout)

        # Datum a čas do
        datetime_to_layout = QHBoxLayout()
        self.dt_end = QDateTimeEdit()
        self.dt_end.setCalendarPopup(True)
        self.dt_end.setDisplayFormat("dd.MM.yyyy HH:mm")
        datetime_to_layout.addWidget(self.dt_end)
        layout.addRow("Konec: *", datetime_to_layout)

        # Opakování
        self.cmb_recurring = QComboBox()
        self.cmb_recurring.addItem("Jednorázově", "none")
        self.cmb_recurring.addItem("Denně", "daily")
        self.cmb_recurring.addItem("Týdně", "weekly")
        self.cmb_recurring.addItem("Měsíčně", "monthly")
        self.cmb_recurring.addItem("Ročně", "yearly")
        layout.addRow("Opakování:", self.cmb_recurring)

        # Priorita
        priority_layout = QHBoxLayout()
        self.cmb_priority = QComboBox()
        self.cmb_priority.addItem("🟢 Nízká", 1)
        self.cmb_priority.addItem("🟡 Střední", 2)
        self.cmb_priority.addItem("🔴 Vysoká", 3)
        self.cmb_priority.setCurrentIndex(1)  # Výchozí střední
        priority_layout.addWidget(self.cmb_priority)
        layout.addRow("Priorita:", priority_layout)

        # Barva události
        color_layout = QHBoxLayout()
        self.btn_color = QPushButton()
        self.btn_color.setFixedSize(40, 30)
        self.btn_color.clicked.connect(self.choose_color)
        self.update_color_button()
        color_layout.addWidget(self.btn_color)

        self.lbl_color = QLabel(self.selected_color)
        color_layout.addWidget(self.lbl_color)
        color_layout.addStretch()

        # Přednastavené barvy
        preset_colors = ["#3498db", "#27ae60", "#f39c12", "#e74c3c", "#9b59b6", "#1abc9c"]
        for color in preset_colors:
            btn = QPushButton()
            btn.setFixedSize(25, 25)
            btn.setStyleSheet(f"background-color: {color}; border: 1px solid #ccc; border-radius: 3px;")
            btn.clicked.connect(lambda checked, c=color: self.set_color(c))
            color_layout.addWidget(btn)

        layout.addRow("Barva:", color_layout)

        return tab

    def create_links_tab(self):
        """Záložka propojení"""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Zákazník
        customer_layout = QVBoxLayout()

        self.txt_customer_search = QLineEdit()
        self.txt_customer_search.setPlaceholderText("Vyhledat zákazníka...")
        self.txt_customer_search.textChanged.connect(self.search_customers)
        customer_layout.addWidget(self.txt_customer_search)

        self.cmb_customer = QComboBox()
        self.cmb_customer.addItem("-- Nevybráno --", None)
        self.cmb_customer.currentIndexChanged.connect(self.on_customer_changed)
        customer_layout.addWidget(self.cmb_customer)

        layout.addRow("Zákazník:", customer_layout)

        # Vozidlo
        self.cmb_vehicle = QComboBox()
        self.cmb_vehicle.addItem("-- Nevybráno --", None)
        self.cmb_vehicle.setEnabled(False)
        layout.addRow("Vozidlo:", self.cmb_vehicle)

        # Zakázka
        order_layout = QVBoxLayout()

        self.cmb_order = QComboBox()
        self.cmb_order.addItem("-- Nevybráno --", None)
        self.cmb_order.addItem("➕ Vytvořit novou zakázku", "new")
        order_layout.addWidget(self.cmb_order)

        self.chk_link_order = QCheckBox("Propojit s existující zakázkou")
        self.chk_link_order.stateChanged.connect(self.on_link_order_changed)
        order_layout.addWidget(self.chk_link_order)

        layout.addRow("Zakázka:", order_layout)

        # Mechanik
        self.cmb_mechanic = QComboBox()
        self.cmb_mechanic.addItem("-- Nepřiřazeno --", None)
        layout.addRow("Mechanik:", self.cmb_mechanic)

        return tab

    def create_details_tab(self):
        """Záložka detailů"""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Popis práce
        self.txt_description = QTextEdit()
        self.txt_description.setPlaceholderText("Popište práci nebo účel události...")
        self.txt_description.setMaximumHeight(120)
        layout.addRow("Popis práce:", self.txt_description)

        # Odhadovaný čas
        time_layout = QHBoxLayout()
        self.spin_estimated_hours = QDoubleSpinBox()
        self.spin_estimated_hours.setRange(0.25, 24)
        self.spin_estimated_hours.setValue(1.0)
        self.spin_estimated_hours.setSingleStep(0.25)
        self.spin_estimated_hours.setSuffix(" h")
        time_layout.addWidget(self.spin_estimated_hours)
        time_layout.addStretch()
        layout.addRow("Odhadovaný čas:", time_layout)

        # Poznámky
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("Interní poznámky...")
        self.txt_notes.setMaximumHeight(100)
        layout.addRow("Poznámky:", self.txt_notes)

        # Přílohy (placeholder)
        attachments_frame = QFrame()
        attachments_frame.setObjectName("attachmentsFrame")
        attachments_layout = QVBoxLayout(attachments_frame)
        attachments_layout.setContentsMargins(10, 10, 10, 10)

        attach_label = QLabel("📎 Přílohy")
        attach_label.setObjectName("sectionLabel")
        attachments_layout.addWidget(attach_label)

        self.list_attachments = QListWidget()
        self.list_attachments.setMaximumHeight(80)
        attachments_layout.addWidget(self.list_attachments)

        attach_buttons = QHBoxLayout()
        self.btn_add_attachment = QPushButton("➕ Přidat")
        self.btn_add_attachment.clicked.connect(self.add_attachment)
        self.btn_remove_attachment = QPushButton("➖ Odebrat")
        self.btn_remove_attachment.clicked.connect(self.remove_attachment)
        attach_buttons.addWidget(self.btn_add_attachment)
        attach_buttons.addWidget(self.btn_remove_attachment)
        attach_buttons.addStretch()
        attachments_layout.addLayout(attach_buttons)

        layout.addRow("", attachments_frame)

        return tab

    def create_notifications_tab(self):
        """Záložka notifikací"""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Připomínka před událostí
        reminder_layout = QHBoxLayout()
        self.chk_reminder = QCheckBox("Připomenout před událostí")
        self.chk_reminder.setChecked(True)
        reminder_layout.addWidget(self.chk_reminder)

        self.cmb_reminder_time = QComboBox()
        self.cmb_reminder_time.addItem("15 minut", 15)
        self.cmb_reminder_time.addItem("30 minut", 30)
        self.cmb_reminder_time.addItem("1 hodina", 60)
        self.cmb_reminder_time.addItem("2 hodiny", 120)
        self.cmb_reminder_time.addItem("1 den", 1440)
        self.cmb_reminder_time.setCurrentIndex(2)  # 1 hodina
        reminder_layout.addWidget(self.cmb_reminder_time)
        reminder_layout.addStretch()

        layout.addRow("Připomínka:", reminder_layout)

        # Notifikace zákazníkovi
        customer_notif_frame = QFrame()
        customer_notif_frame.setObjectName("notifFrame")
        customer_notif_layout = QVBoxLayout(customer_notif_frame)
        customer_notif_layout.setContentsMargins(10, 10, 10, 10)

        notif_label = QLabel("📧 Notifikace zákazníkovi")
        notif_label.setObjectName("sectionLabel")
        customer_notif_layout.addWidget(notif_label)

        self.chk_email_customer = QCheckBox("Odeslat email zákazníkovi")
        self.chk_email_customer.setChecked(False)
        customer_notif_layout.addWidget(self.chk_email_customer)

        self.chk_sms_customer = QCheckBox("Odeslat SMS zákazníkovi")
        self.chk_sms_customer.setChecked(False)
        customer_notif_layout.addWidget(self.chk_sms_customer)

        layout.addRow("", customer_notif_frame)

        # Interní notifikace
        internal_notif_frame = QFrame()
        internal_notif_frame.setObjectName("notifFrame")
        internal_notif_layout = QVBoxLayout(internal_notif_frame)
        internal_notif_layout.setContentsMargins(10, 10, 10, 10)

        internal_label = QLabel("🔔 Interní notifikace")
        internal_label.setObjectName("sectionLabel")
        internal_notif_layout.addWidget(internal_label)

        self.chk_notify_mechanic = QCheckBox("Notifikovat přiřazeného mechanika")
        self.chk_notify_mechanic.setChecked(True)
        internal_notif_layout.addWidget(self.chk_notify_mechanic)

        self.chk_notify_admin = QCheckBox("Notifikovat vedoucího servisu")
        self.chk_notify_admin.setChecked(False)
        internal_notif_layout.addWidget(self.chk_notify_admin)

        layout.addRow("", internal_notif_frame)

        return tab

    def load_data(self):
        """Načtení dat pro combobox"""
        # Zákazníci
        customers = db.fetch_all("""
            SELECT id, first_name, last_name, company, phone
            FROM customers ORDER BY last_name, first_name
        """)

        self.customers_data = customers
        self.cmb_customer.clear()
        self.cmb_customer.addItem("-- Nevybráno --", None)
        for c in customers:
            name = f"{c['first_name']} {c['last_name']}"
            if c['company']:
                name += f" ({c['company']})"
            self.cmb_customer.addItem(name, c['id'])

        # Mechanici
        mechanics = db.fetch_all("""
            SELECT id, full_name FROM users
            WHERE role IN ('mechanik', 'admin') AND active = 1
            ORDER BY full_name
        """)

        self.cmb_mechanic.clear()
        self.cmb_mechanic.addItem("-- Nepřiřazeno --", None)
        for m in mechanics:
            self.cmb_mechanic.addItem(f"👤 {m['full_name']}", m['id'])

    def load_event_data(self):
        """Načtení dat existující události"""
        query = """
            SELECT * FROM calendar_events WHERE id = ?
        """
        event = db.fetch_one(query, (self.event_id,))

        if not event:
            QMessageBox.warning(self, "Chyba", "Událost nebyla nalezena.")
            self.reject()
            return

        # Základní údaje
        self.txt_title.setText(event['title'] or "")

        # Typ
        event_type = event['event_type'] or 'other'
        for i in range(self.cmb_event_type.count()):
            if self.cmb_event_type.itemData(i) == event_type:
                self.cmb_event_type.setCurrentIndex(i)
                break

        # Datum a čas
        if event['start_datetime']:
            dt = QDateTime.fromString(event['start_datetime'], Qt.DateFormat.ISODate)
            self.dt_start.setDateTime(dt)

        if event['end_datetime']:
            dt = QDateTime.fromString(event['end_datetime'], Qt.DateFormat.ISODate)
            self.dt_end.setDateTime(dt)

        # Celodenní
        self.chk_all_day.setChecked(bool(event['all_day']))

        # Priorita
        priority = event['priority'] or 2
        for i in range(self.cmb_priority.count()):
            if self.cmb_priority.itemData(i) == priority:
                self.cmb_priority.setCurrentIndex(i)
                break

        # Barva
        if event['color']:
            self.set_color(event['color'])

        # Propojení
        if event['customer_id']:
            for i in range(self.cmb_customer.count()):
                if self.cmb_customer.itemData(i) == event['customer_id']:
                    self.cmb_customer.setCurrentIndex(i)
                    break

        if event['mechanic_id']:
            for i in range(self.cmb_mechanic.count()):
                if self.cmb_mechanic.itemData(i) == event['mechanic_id']:
                    self.cmb_mechanic.setCurrentIndex(i)
                    break

        # Detaily
        self.txt_description.setPlainText(event['description'] or "")
        self.txt_notes.setPlainText(event['notes'] or "")

        # Připomínka
        if event['reminder_minutes']:
            for i in range(self.cmb_reminder_time.count()):
                if self.cmb_reminder_time.itemData(i) == event['reminder_minutes']:
                    self.cmb_reminder_time.setCurrentIndex(i)
                    break

    def set_defaults(self):
        """Nastavení výchozích hodnot pro novou událost"""
        start_dt = QDateTime(self.default_date, self.default_time)
        end_dt = start_dt.addSecs(3600)  # +1 hodina

        self.dt_start.setDateTime(start_dt)
        self.dt_end.setDateTime(end_dt)

    def on_type_changed(self):
        """Změna typu události"""
        event_type = self.cmb_event_type.currentData()

        # Nastavení výchozí barvy podle typu
        type_colors = {
            'service': '#3498db',
            'meeting': '#9b59b6',
            'delivery': '#f39c12',
            'handover': '#27ae60',
            'reminder': '#e74c3c',
            'other': '#95a5a6'
        }

        if event_type in type_colors:
            self.set_color(type_colors[event_type])

    def on_all_day_changed(self):
        """Změna celodenní události"""
        is_all_day = self.chk_all_day.isChecked()

        if is_all_day:
            self.dt_start.setDisplayFormat("dd.MM.yyyy")
            self.dt_end.setDisplayFormat("dd.MM.yyyy")
            self.dt_start.setTime(QTime(0, 0))
            self.dt_end.setTime(QTime(23, 59))
        else:
            self.dt_start.setDisplayFormat("dd.MM.yyyy HH:mm")
            self.dt_end.setDisplayFormat("dd.MM.yyyy HH:mm")

    def on_start_changed(self):
        """Změna začátku - automatická úprava konce"""
        start = self.dt_start.dateTime()
        end = self.dt_end.dateTime()

        if end <= start:
            self.dt_end.setDateTime(start.addSecs(3600))

    def on_customer_changed(self):
        """Změna zákazníka - načtení vozidel"""
        customer_id = self.cmb_customer.currentData()

        self.cmb_vehicle.clear()
        self.cmb_vehicle.addItem("-- Nevybráno --", None)

        if customer_id:
            self.cmb_vehicle.setEnabled(True)

            vehicles = db.fetch_all("""
                SELECT id, brand, model, license_plate
                FROM vehicles WHERE customer_id = ?
                ORDER BY brand, model
            """, (customer_id,))

            for v in vehicles:
                text = f"{v['brand']} {v['model']} ({v['license_plate']})"
                self.cmb_vehicle.addItem(text, v['id'])

            # Načíst zakázky zákazníka
            self.load_customer_orders(customer_id)
        else:
            self.cmb_vehicle.setEnabled(False)

    def load_customer_orders(self, customer_id):
        """Načtení zakázek zákazníka"""
        self.cmb_order.clear()
        self.cmb_order.addItem("-- Nevybráno --", None)
        self.cmb_order.addItem("➕ Vytvořit novou zakázku", "new")

        orders = db.fetch_all("""
            SELECT id, order_number, status, created_date
            FROM orders WHERE customer_id = ?
            ORDER BY created_date DESC
            LIMIT 20
        """, (customer_id,))

        for o in orders:
            text = f"#{o['order_number']} - {o['status']} ({o['created_date']})"
            self.cmb_order.addItem(text, o['id'])

    def on_link_order_changed(self):
        """Změna propojení se zakázkou"""
        self.cmb_order.setEnabled(self.chk_link_order.isChecked())

    def search_customers(self, text):
        """Vyhledávání zákazníků"""
        if len(text) < 2:
            return

        self.cmb_customer.clear()
        self.cmb_customer.addItem("-- Nevybráno --", None)

        text_lower = text.lower()
        for c in self.customers_data:
            name = f"{c['first_name']} {c['last_name']}"
            company = c['company'] or ""

            if (text_lower in name.lower() or
                text_lower in company.lower() or
                text_lower in (c['phone'] or "")):

                display = name
                if company:
                    display += f" ({company})"
                self.cmb_customer.addItem(display, c['id'])

    def choose_color(self):
        """Výběr barvy"""
        color = QColorDialog.getColor(QColor(self.selected_color), self)
        if color.isValid():
            self.set_color(color.name())

    def set_color(self, color):
        """Nastavení barvy"""
        self.selected_color = color
        self.update_color_button()
        self.lbl_color.setText(color)

    def update_color_button(self):
        """Aktualizace tlačítka barvy"""
        self.btn_color.setStyleSheet(f"""
            background-color: {self.selected_color};
            border: 2px solid #ccc;
            border-radius: 5px;
        """)

    def add_attachment(self):
        """Přidání přílohy"""
        # TODO: Implementovat dialog pro výběr souboru
        QMessageBox.information(self, "Info", "Funkce příloh bude implementována.")

    def remove_attachment(self):
        """Odebrání přílohy"""
        current = self.list_attachments.currentItem()
        if current:
            self.list_attachments.takeItem(self.list_attachments.row(current))

    def validate(self):
        """Validace formuláře"""
        if not self.txt_title.text().strip():
            QMessageBox.warning(self, "Chyba", "Název události je povinný.")
            self.tabs.setCurrentIndex(0)
            self.txt_title.setFocus()
            return False

        if self.dt_end.dateTime() <= self.dt_start.dateTime():
            QMessageBox.warning(self, "Chyba", "Konec události musí být po začátku.")
            self.tabs.setCurrentIndex(0)
            return False

        return True

    def save_event(self):
        """Uložení události"""
        if not self.validate():
            return

        # Příprava dat
        data = {
            'title': self.txt_title.text().strip(),
            'event_type': self.cmb_event_type.currentData(),
            'start_datetime': self.dt_start.dateTime().toString(Qt.DateFormat.ISODate),
            'end_datetime': self.dt_end.dateTime().toString(Qt.DateFormat.ISODate),
            'all_day': 1 if self.chk_all_day.isChecked() else 0,
            'priority': self.cmb_priority.currentData(),
            'color': self.selected_color,
            'customer_id': self.cmb_customer.currentData(),
            'vehicle_id': self.cmb_vehicle.currentData(),
            'mechanic_id': self.cmb_mechanic.currentData(),
            'description': self.txt_description.toPlainText().strip(),
            'notes': self.txt_notes.toPlainText().strip(),
            'reminder_minutes': self.cmb_reminder_time.currentData() if self.chk_reminder.isChecked() else None,
            'status': 'scheduled',
            'updated_at': datetime.now().isoformat()
        }

        # Zakázka
        if self.chk_link_order.isChecked():
            order_data = self.cmb_order.currentData()
            if order_data and order_data != "new":
                data['order_id'] = order_data

        try:
            if self.is_edit_mode:
                # UPDATE
                set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
                query = f"UPDATE calendar_events SET {set_clause} WHERE id = ?"
                params = list(data.values()) + [self.event_id]
                db.execute_query(query, tuple(params))

                QMessageBox.information(self, "Úspěch", "Událost byla aktualizována.")
                self.event_saved.emit(self.event_id)
            else:
                # INSERT
                data['created_at'] = datetime.now().isoformat()

                columns = ", ".join(data.keys())
                placeholders = ", ".join(["?" for _ in data])
                query = f"INSERT INTO calendar_events ({columns}) VALUES ({placeholders})"

                db.execute_query(query, tuple(data.values()))

                # Získat ID
                result = db.fetch_one("SELECT last_insert_rowid() as id")
                new_id = result['id'] if result else 0

                QMessageBox.information(self, "Úspěch", "Událost byla vytvořena.")
                self.event_saved.emit(new_id)

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při ukládání: {e}")

    def delete_event(self):
        """Smazání události"""
        reply = QMessageBox.question(
            self,
            "Potvrzení smazání",
            "Opravdu chcete smazat tuto událost?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                db.execute_query("DELETE FROM calendar_events WHERE id = ?", (self.event_id,))
                QMessageBox.information(self, "Úspěch", "Událost byla smazána.")
                self.event_deleted.emit(self.event_id)
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Chyba při mazání: {e}")

    def create_order(self):
        """Vytvoření zakázky z události"""
        self.create_order_requested.emit(self.event_id)

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #f5f5f5;
            }}

            QTabWidget::pane {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }}

            QTabBar::tab {{
                background-color: #f0f0f0;
                padding: 10px 20px;
                border: 1px solid #d0d0d0;
                border-bottom: none;
                border-radius: 5px 5px 0 0;
            }}

            QTabBar::tab:selected {{
                background-color: white;
                border-bottom: 2px solid {config.COLOR_SECONDARY};
            }}

            #mainInput {{
                font-size: 14px;
                padding: 8px;
                border: 2px solid #d0d0d0;
                border-radius: 5px;
            }}

            #mainInput:focus {{
                border-color: {config.COLOR_SECONDARY};
            }}

            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateTimeEdit {{
                padding: 6px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }}

            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border-color: {config.COLOR_SECONDARY};
            }}

            #primaryButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 25px;
                font-weight: bold;
                font-size: 13px;
            }}

            #primaryButton:hover {{
                background-color: #2980b9;
            }}

            #cancelButton {{
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 25px;
            }}

            #cancelButton:hover {{
                background-color: #7f8c8d;
            }}

            #dangerButton {{
                background-color: {config.COLOR_DANGER};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 25px;
            }}

            #dangerButton:hover {{
                background-color: #c0392b;
            }}

            #secondaryButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 25px;
            }}

            #secondaryButton:hover {{
                background-color: #229954;
            }}

            #notifFrame, #attachmentsFrame {{
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }}

            #sectionLabel {{
                font-weight: bold;
                color: {config.COLOR_PRIMARY};
            }}
        """)
