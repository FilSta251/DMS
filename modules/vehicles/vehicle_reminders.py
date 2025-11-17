# -*- coding: utf-8 -*-
"""
Systém připomínek pro vozidlo - STK, emise, pojištění, servis, vlastní připomínky
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QFrame, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QTextEdit, QSpinBox, QDateEdit,
    QGroupBox, QCheckBox, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QFont, QColor, QBrush
from datetime import datetime, date, timedelta
import config
from database_manager import db


class VehicleRemindersWidget(QWidget):
    """Widget pro správu připomínek vozidla"""

    def __init__(self, vehicle_id, parent=None):
        super().__init__(parent)
        self.vehicle_id = vehicle_id
        self.reminders = []
        self.init_ui()
        self.ensure_reminders_table()
        self.load_reminders()
        self.check_automatic_reminders()

    def ensure_reminders_table(self):
        """Zajištění existence tabulky pro připomínky"""
        try:
            db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicle_reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_id INTEGER NOT NULL,
                    reminder_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date DATE,
                    due_mileage INTEGER,
                    priority INTEGER DEFAULT 2,
                    status TEXT DEFAULT 'active',
                    notify_email INTEGER DEFAULT 0,
                    notify_sms INTEGER DEFAULT 0,
                    notify_days_before INTEGER DEFAULT 7,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    snoozed_until DATE,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
                )
            """)
            db.connection.commit()
        except Exception as e:
            print(f"Chyba při vytváření tabulky připomínek: {e}")

    def init_ui(self):
        """Inicializace uživatelského rozhraní"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        # Hlavička
        header_panel = self.create_header_panel()
        layout.addWidget(header_panel)

        # Kritické připomínky
        self.critical_panel = self.create_critical_panel()
        layout.addWidget(self.critical_panel)

        # Statistiky
        self.stats_panel = self.create_stats_panel()
        layout.addWidget(self.stats_panel)

        # Tabulka připomínek
        self.table = self.create_table()
        layout.addWidget(self.table)

    def create_header_panel(self):
        """Vytvoření hlavičky"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QHBoxLayout(panel)
        layout.setSpacing(15)

        # Titulek
        title = QLabel("🔔 Připomínky")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        layout.addStretch()

        # Filtr stavu
        status_label = QLabel("Stav:")
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Vše", "Aktivní", "Splněno", "Ignorováno", "Odloženo"])
        self.status_filter.setMinimumWidth(120)
        self.status_filter.currentTextChanged.connect(self.filter_reminders)

        layout.addWidget(status_label)
        layout.addWidget(self.status_filter)

        # Filtr priority
        priority_label = QLabel("Priorita:")
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["Vše", "Kritická", "Vysoká", "Střední", "Nízká"])
        self.priority_filter.setMinimumWidth(120)
        self.priority_filter.currentTextChanged.connect(self.filter_reminders)

        layout.addWidget(priority_label)
        layout.addWidget(self.priority_filter)

        # Tlačítko refresh
        btn_refresh = QPushButton("🔄 Obnovit")
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_refresh.clicked.connect(self.refresh_all)
        layout.addWidget(btn_refresh)

        # Tlačítko přidat
        btn_add = QPushButton("➕ Nová připomínka")
        btn_add.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #219a52;
            }}
        """)
        btn_add.clicked.connect(self.add_reminder)
        layout.addWidget(btn_add)

        return panel

    def create_critical_panel(self):
        """Vytvoření panelu s kritickými připomínkami"""
        panel = QFrame()
        panel.setObjectName("critical_panel")
        panel.setStyleSheet("""
            QFrame#critical_panel {
                background-color: #fadbd8;
                border: 2px solid #e74c3c;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setSpacing(5)

        title = QLabel("⚠️ KRITICKÉ PŘIPOMÍNKY")
        title.setStyleSheet("""
            QLabel {
                color: #c0392b;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        layout.addWidget(title)

        self.critical_list = QLabel("")
        self.critical_list.setWordWrap(True)
        self.critical_list.setStyleSheet("""
            QLabel {
                color: #922b21;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.critical_list)

        panel.hide()
        return panel

    def create_stats_panel(self):
        """Vytvoření panelu se statistikami"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 10px;
                border: 1px solid #ddd;
            }
        """)

        layout = QHBoxLayout(panel)
        layout.setSpacing(20)

        self.stat_total = QLabel("<b>Celkem:</b> 0")
        self.stat_active = QLabel("<b>Aktivních:</b> 0")
        self.stat_critical = QLabel("<b>Kritických:</b> 0")
        self.stat_upcoming = QLabel("<b>Blížících se:</b> 0")

        layout.addWidget(self.stat_total)
        layout.addWidget(self.stat_active)
        layout.addWidget(self.stat_critical)
        layout.addWidget(self.stat_upcoming)
        layout.addStretch()

        return panel

    def create_table(self):
        """Vytvoření tabulky připomínek"""
        table = QTableWidget()
        table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                gridline-color: #ecf0f1;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                font-weight: bold;
                border: none;
            }
        """)

        # Sloupce
        columns = [
            "ID", "Typ", "Název", "Popis", "Datum/km", "Zbývá", "Priorita", "Stav", "Akce"
        ]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)

        # Nastavení
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setColumnHidden(0, True)  # Skrýt ID

        # Roztažení sloupců
        header = table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)

        return table

    def load_reminders(self):
        """Načtení připomínek z databáze"""
        try:
            self.reminders = db.fetch_all("""
                SELECT * FROM vehicle_reminders
                WHERE vehicle_id = ?
                ORDER BY
                    CASE WHEN status = 'active' THEN 0 ELSE 1 END,
                    priority ASC,
                    due_date ASC
            """, (self.vehicle_id,))

            self.populate_table(self.reminders)
            self.update_statistics()
            self.check_critical_reminders()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst připomínky:\n{e}")

    def populate_table(self, reminders):
        """Naplnění tabulky daty"""
        self.table.setRowCount(0)

        today = date.today()

        for reminder in reminders:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # ID (skrytý)
            id_item = QTableWidgetItem()
            id_item.setData(Qt.ItemDataRole.DisplayRole, reminder['id'])
            self.table.setItem(row, 0, id_item)

            # Typ s ikonou
            reminder_type = reminder['reminder_type']
            type_icon = self.get_type_icon(reminder_type)
            type_item = QTableWidgetItem(f"{type_icon} {reminder_type}")
            self.table.setItem(row, 1, type_item)

            # Název
            title_item = QTableWidgetItem(reminder['title'] or '')
            title_font = title_item.font()
            title_font.setBold(True)
            title_item.setFont(title_font)
            self.table.setItem(row, 2, title_item)

            # Popis
            desc = reminder['description'] or ''
            if len(desc) > 50:
                desc = desc[:47] + "..."
            self.table.setItem(row, 3, QTableWidgetItem(desc))

            # Datum/km
            due_text = ""
            if reminder['due_date']:
                try:
                    due_date = datetime.strptime(str(reminder['due_date']), "%Y-%m-%d").date()
                    due_text = due_date.strftime("%d.%m.%Y")
                except:
                    pass
            if reminder['due_mileage']:
                if due_text:
                    due_text += f" / {reminder['due_mileage']:,} km".replace(",", " ")
                else:
                    due_text = f"{reminder['due_mileage']:,} km".replace(",", " ")
            self.table.setItem(row, 4, QTableWidgetItem(due_text))

            # Zbývá
            remaining_item = QTableWidgetItem()
            if reminder['status'] == 'active' and reminder['due_date']:
                try:
                    due_date = datetime.strptime(str(reminder['due_date']), "%Y-%m-%d").date()
                    days_left = (due_date - today).days

                    if days_left < 0:
                        remaining_item.setText(f"⚠️ {abs(days_left)} dní po")
                        remaining_item.setForeground(QBrush(QColor("#c0392b")))
                    elif days_left == 0:
                        remaining_item.setText("⚠️ DNES!")
                        remaining_item.setForeground(QBrush(QColor("#c0392b")))
                    elif days_left <= 7:
                        remaining_item.setText(f"🔴 {days_left} dní")
                        remaining_item.setForeground(QBrush(QColor("#e74c3c")))
                    elif days_left <= 30:
                        remaining_item.setText(f"🟠 {days_left} dní")
                        remaining_item.setForeground(QBrush(QColor("#f39c12")))
                    elif days_left <= 90:
                        remaining_item.setText(f"🟡 {days_left} dní")
                        remaining_item.setForeground(QBrush(QColor("#f1c40f")))
                    else:
                        remaining_item.setText(f"🟢 {days_left} dní")
                        remaining_item.setForeground(QBrush(QColor("#27ae60")))
                except:
                    pass
            self.table.setItem(row, 5, remaining_item)

            # Priorita
            priority = reminder['priority']
            priority_text, priority_color = self.get_priority_info(priority)
            priority_item = QTableWidgetItem(priority_text)
            priority_item.setBackground(QBrush(QColor(priority_color)))
            priority_item.setForeground(QBrush(QColor("white")))
            self.table.setItem(row, 6, priority_item)

            # Stav
            status = reminder['status']
            status_text = self.get_status_text(status)
            status_item = QTableWidgetItem(status_text)
            if status == 'completed':
                status_item.setForeground(QBrush(QColor("#27ae60")))
            elif status == 'ignored':
                status_item.setForeground(QBrush(QColor("#95a5a6")))
            elif status == 'snoozed':
                status_item.setForeground(QBrush(QColor("#f39c12")))
            self.table.setItem(row, 7, status_item)

            # Akce
            actions_widget = self.create_actions_widget(reminder)
            self.table.setCellWidget(row, 8, actions_widget)

    def get_type_icon(self, reminder_type):
        """Získání ikony podle typu"""
        icons = {
            "STK": "🔧",
            "Emise": "💨",
            "Pojištění": "📄",
            "Servis": "🛠️",
            "Výměna oleje": "🔄",
            "Výměna řetězu": "⚙️",
            "Výměna rozvodů": "⚙️",
            "Vlastní": "📅"
        }
        return icons.get(reminder_type, "🔔")

    def get_priority_info(self, priority):
        """Získání textu a barvy priority"""
        priorities = {
            1: ("Kritická", "#c0392b"),
            2: ("Vysoká", "#e74c3c"),
            3: ("Střední", "#f39c12"),
            4: ("Nízká", "#27ae60")
        }
        return priorities.get(priority, ("Střední", "#f39c12"))

    def get_status_text(self, status):
        """Získání textu stavu"""
        statuses = {
            "active": "✅ Aktivní",
            "completed": "✔️ Splněno",
            "ignored": "❌ Ignorováno",
            "snoozed": "⏰ Odloženo"
        }
        return statuses.get(status, status)

    def create_actions_widget(self, reminder):
        """Vytvoření widgetu s akcemi"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(3)

        if reminder['status'] == 'active':
            # Splnit
            btn_complete = QPushButton("✔️")
            btn_complete.setToolTip("Označit jako splněno")
            btn_complete.setFixedSize(28, 28)
            btn_complete.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #219a52;
                }
            """)
            btn_complete.clicked.connect(lambda: self.mark_completed(reminder['id']))
            layout.addWidget(btn_complete)

            # Odložit
            btn_snooze = QPushButton("⏰")
            btn_snooze.setToolTip("Odložit")
            btn_snooze.setFixedSize(28, 28)
            btn_snooze.setStyleSheet("""
                QPushButton {
                    background-color: #f39c12;
                    color: white;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #e67e22;
                }
            """)
            btn_snooze.clicked.connect(lambda: self.snooze_reminder(reminder['id']))
            layout.addWidget(btn_snooze)

        # Smazat
        btn_delete = QPushButton("🗑️")
        btn_delete.setToolTip("Smazat")
        btn_delete.setFixedSize(28, 28)
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        btn_delete.clicked.connect(lambda: self.delete_reminder(reminder['id']))
        layout.addWidget(btn_delete)

        return widget

    def update_statistics(self):
        """Aktualizace statistik"""
        total = len(self.reminders)
        active = sum(1 for r in self.reminders if r['status'] == 'active')

        today = date.today()
        critical = 0
        upcoming = 0

        for r in self.reminders:
            if r['status'] == 'active' and r['due_date']:
                try:
                    due_date = datetime.strptime(str(r['due_date']), "%Y-%m-%d").date()
                    days_left = (due_date - today).days

                    if days_left <= 7:
                        critical += 1
                    elif days_left <= 30:
                        upcoming += 1
                except:
                    pass

        self.stat_total.setText(f"<b>Celkem:</b> {total}")
        self.stat_active.setText(f"<b>Aktivních:</b> {active}")
        self.stat_critical.setText(f"<b>Kritických:</b> {critical}")
        self.stat_upcoming.setText(f"<b>Blížících se:</b> {upcoming}")

    def check_critical_reminders(self):
        """Kontrola kritických připomínek"""
        today = date.today()
        critical_list = []

        for r in self.reminders:
            if r['status'] == 'active' and r['due_date']:
                try:
                    due_date = datetime.strptime(str(r['due_date']), "%Y-%m-%d").date()
                    days_left = (due_date - today).days

                    if days_left <= 7:
                        if days_left < 0:
                            critical_list.append(f"🔴 <b>{r['title']}</b> - {abs(days_left)} dní PO TERMÍNU!")
                        elif days_left == 0:
                            critical_list.append(f"🔴 <b>{r['title']}</b> - DNES!")
                        else:
                            critical_list.append(f"🔴 <b>{r['title']}</b> - za {days_left} dní ({due_date.strftime('%d.%m.%Y')})")
                except:
                    pass

        if critical_list:
            self.critical_list.setText("<br>".join(critical_list))
            self.critical_panel.show()
        else:
            self.critical_panel.hide()

    def check_automatic_reminders(self):
        """Automatická kontrola STK, emisí a pojištění z vozidla"""
        try:
            vehicle = db.fetch_one("""
                SELECT stk_valid_until FROM vehicles WHERE id = ?
            """, (self.vehicle_id,))

            if vehicle and vehicle['stk_valid_until']:
                # Kontrola zda už existuje připomínka na STK
                existing = db.fetch_one("""
                    SELECT id FROM vehicle_reminders
                    WHERE vehicle_id = ? AND reminder_type = 'STK' AND status = 'active'
                """, (self.vehicle_id,))

                if not existing:
                    # Vytvoření automatické připomínky
                    stk_date = datetime.strptime(str(vehicle['stk_valid_until']), "%Y-%m-%d").date()

                    db.execute_query("""
                        INSERT INTO vehicle_reminders (
                            vehicle_id, reminder_type, title, description,
                            due_date, priority, notify_days_before
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.vehicle_id,
                        "STK",
                        "Platnost STK",
                        "Automaticky vytvořená připomínka na konec platnosti STK",
                        stk_date.strftime("%Y-%m-%d"),
                        2,  # Vysoká priorita
                        30  # Notifikace 30 dní předem
                    ))

                    self.load_reminders()
        except Exception as e:
            print(f"Chyba při automatické kontrole: {e}")

    def filter_reminders(self):
        """Filtrování připomínek"""
        status_filter = self.status_filter.currentText()
        priority_filter = self.priority_filter.currentText()

        filtered = []

        for r in self.reminders:
            # Filtr stavu
            if status_filter != "Vše":
                status_map = {
                    "Aktivní": "active",
                    "Splněno": "completed",
                    "Ignorováno": "ignored",
                    "Odloženo": "snoozed"
                }
                if r['status'] != status_map.get(status_filter, ''):
                    continue

            # Filtr priority
            if priority_filter != "Vše":
                priority_map = {
                    "Kritická": 1,
                    "Vysoká": 2,
                    "Střední": 3,
                    "Nízká": 4
                }
                if r['priority'] != priority_map.get(priority_filter, 0):
                    continue

            filtered.append(r)

        self.populate_table(filtered)

    def add_reminder(self):
        """Přidání nové připomínky"""
        dialog = AddReminderDialog(self)
        if dialog.exec():
            data = dialog.get_data()

            try:
                db.execute_query("""
                    INSERT INTO vehicle_reminders (
                        vehicle_id, reminder_type, title, description,
                        due_date, due_mileage, priority, notify_email,
                        notify_sms, notify_days_before
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.vehicle_id,
                    data['reminder_type'],
                    data['title'],
                    data['description'],
                    data['due_date'],
                    data['due_mileage'],
                    data['priority'],
                    data['notify_email'],
                    data['notify_sms'],
                    data['notify_days_before']
                ))

                self.load_reminders()
                QMessageBox.information(self, "Úspěch", "Připomínka byla vytvořena.")

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se vytvořit připomínku:\n{e}")

    def mark_completed(self, reminder_id):
        """Označení připomínky jako splněné"""
        try:
            db.execute_query("""
                UPDATE vehicle_reminders
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (reminder_id,))

            self.load_reminders()
            QMessageBox.information(self, "Úspěch", "Připomínka byla označena jako splněná.")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při aktualizaci:\n{e}")

    def snooze_reminder(self, reminder_id):
        """Odložení připomínky"""
        dialog = SnoozeDialog(self)
        if dialog.exec():
            days = dialog.get_days()
            snooze_until = date.today() + timedelta(days=days)

            try:
                db.execute_query("""
                    UPDATE vehicle_reminders
                    SET status = 'snoozed', snoozed_until = ?
                    WHERE id = ?
                """, (snooze_until.strftime("%Y-%m-%d"), reminder_id))

                self.load_reminders()
                QMessageBox.information(
                    self,
                    "Úspěch",
                    f"Připomínka byla odložena do {snooze_until.strftime('%d.%m.%Y')}."
                )

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Chyba při odložení:\n{e}")

    def delete_reminder(self, reminder_id):
        """Smazání připomínky"""
        reply = QMessageBox.question(
            self,
            "Potvrzení",
            "Opravdu chcete smazat tuto připomínku?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                db.execute_query(
                    "DELETE FROM vehicle_reminders WHERE id = ?",
                    (reminder_id,)
                )

                self.load_reminders()
                QMessageBox.information(self, "Úspěch", "Připomínka byla smazána.")

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Chyba při mazání:\n{e}")

    def refresh_all(self):
        """Obnovení všech dat"""
        self.check_automatic_reminders()
        self.load_reminders()
        QMessageBox.information(self, "Obnoveno", "Připomínky byly aktualizovány.")


class AddReminderDialog(QDialog):
    """Dialog pro přidání připomínky"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("➕ Nová připomínka")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Typ připomínky
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "STK",
            "Emise",
            "Pojištění",
            "Servis",
            "Výměna oleje",
            "Výměna řetězu",
            "Výměna rozvodů",
            "Vlastní"
        ])
        form_layout.addRow("Typ *:", self.type_combo)

        # Název
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("např. Výměna oleje po 10 000 km")
        form_layout.addRow("Název *:", self.title_input)

        # Popis
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Detailní popis připomínky...")
        self.description_input.setMaximumHeight(80)
        form_layout.addRow("Popis:", self.description_input)

        # Datum
        self.due_date_input = QDateEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDate(QDate.currentDate().addMonths(1))
        self.due_date_input.setDisplayFormat("dd.MM.yyyy")
        self.due_date_input.setSpecialValueText("Bez data")
        form_layout.addRow("Datum:", self.due_date_input)

        # Kilometry
        self.mileage_input = QSpinBox()
        self.mileage_input.setRange(0, 999999)
        self.mileage_input.setSuffix(" km")
        self.mileage_input.setSpecialValueText("Bez km")
        form_layout.addRow("Stav km:", self.mileage_input)

        # Priorita
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Kritická", "Vysoká", "Střední", "Nízká"])
        self.priority_combo.setCurrentIndex(2)  # Střední
        form_layout.addRow("Priorita:", self.priority_combo)

        layout.addLayout(form_layout)

        # Notifikace
        notify_group = QGroupBox("🔔 Notifikace")
        notify_layout = QFormLayout(notify_group)

        self.notify_email = QCheckBox("Email zákazníkovi")
        notify_layout.addRow(self.notify_email)

        self.notify_sms = QCheckBox("SMS zákazníkovi (pokud je dostupné)")
        notify_layout.addRow(self.notify_sms)

        self.notify_days = QSpinBox()
        self.notify_days.setRange(1, 90)
        self.notify_days.setValue(7)
        self.notify_days.setSuffix(" dní předem")
        notify_layout.addRow("Upozornit:", self.notify_days)

        layout.addWidget(notify_group)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Vytvořit")
        btn_save.setStyleSheet(f"background-color: {config.COLOR_SUCCESS};")
        btn_save.clicked.connect(self.validate_and_accept)
        buttons_layout.addWidget(btn_save)

        layout.addLayout(buttons_layout)

    def validate_and_accept(self):
        """Validace a potvrzení"""
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Chyba", "Název je povinný údaj.")
            return

        self.accept()

    def get_data(self):
        """Získání dat"""
        priority_map = {
            "Kritická": 1,
            "Vysoká": 2,
            "Střední": 3,
            "Nízká": 4
        }

        due_date = None
        if self.due_date_input.date() > self.due_date_input.minimumDate():
            due_date = self.due_date_input.date().toString("yyyy-MM-dd")

        due_mileage = None
        if self.mileage_input.value() > 0:
            due_mileage = self.mileage_input.value()

        return {
            'reminder_type': self.type_combo.currentText(),
            'title': self.title_input.text().strip(),
            'description': self.description_input.toPlainText().strip(),
            'due_date': due_date,
            'due_mileage': due_mileage,
            'priority': priority_map.get(self.priority_combo.currentText(), 3),
            'notify_email': 1 if self.notify_email.isChecked() else 0,
            'notify_sms': 1 if self.notify_sms.isChecked() else 0,
            'notify_days_before': self.notify_days.value()
        }


class SnoozeDialog(QDialog):
    """Dialog pro odložení připomínky"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("⏰ Odložit připomínku")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        label = QLabel("Odložit připomínku o:")
        layout.addWidget(label)

        # Radio tlačítka
        self.days_group = QButtonGroup(self)

        options = [
            ("1 den", 1),
            ("3 dny", 3),
            ("1 týden", 7),
            ("2 týdny", 14),
            ("1 měsíc", 30)
        ]

        for text, days in options:
            radio = QRadioButton(text)
            radio.setProperty("days", days)
            self.days_group.addButton(radio)
            layout.addWidget(radio)

            if days == 7:  # Výchozí
                radio.setChecked(True)

        # Vlastní počet dní
        custom_layout = QHBoxLayout()
        self.custom_radio = QRadioButton("Vlastní:")
        self.days_group.addButton(self.custom_radio)
        custom_layout.addWidget(self.custom_radio)

        self.custom_days = QSpinBox()
        self.custom_days.setRange(1, 365)
        self.custom_days.setValue(7)
        self.custom_days.setSuffix(" dní")
        custom_layout.addWidget(self.custom_days)
        custom_layout.addStretch()

        layout.addLayout(custom_layout)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        btn_snooze = QPushButton("⏰ Odložit")
        btn_snooze.setStyleSheet(f"background-color: {config.COLOR_WARNING};")
        btn_snooze.clicked.connect(self.accept)
        buttons_layout.addWidget(btn_snooze)

        layout.addLayout(buttons_layout)

    def get_days(self):
        """Získání počtu dní"""
        if self.custom_radio.isChecked():
            return self.custom_days.value()

        selected = self.days_group.checkedButton()
        if selected:
            return selected.property("days")

        return 7
