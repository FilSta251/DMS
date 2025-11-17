# -*- coding: utf-8 -*-
"""
Správa opakujících se událostí
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QLabel,
    QComboBox, QFrame, QDialog, QFormLayout, QLineEdit,
    QSpinBox, QDateEdit, QCheckBox, QGroupBox, QMessageBox,
    QListWidget, QListWidgetItem, QTextEdit
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, date, timedelta
from database_manager import db
import config
import json


class RecurringRuleDialog(QDialog):
    """Dialog pro vytvoření/editaci pravidla opakování"""

    def __init__(self, rule_id=None, parent=None):
        super().__init__(parent)
        self.rule_id = rule_id
        self.is_edit = rule_id is not None

        self.setWindowTitle("Editace pravidla" if self.is_edit else "Nové pravidlo opakování")
        self.setMinimumSize(600, 550)
        self.setModal(True)

        self.init_ui()

        if self.is_edit:
            self.load_rule_data()
        else:
            self.set_defaults()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        form = QFormLayout()
        form.setSpacing(12)

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Název pravidla...")
        form.addRow("Název: *", self.txt_name)

        self.cmb_frequency = QComboBox()
        self.cmb_frequency.addItem("Denně", "daily")
        self.cmb_frequency.addItem("Pouze pracovní dny", "weekdays")
        self.cmb_frequency.addItem("Týdně", "weekly")
        self.cmb_frequency.addItem("Měsíčně", "monthly")
        self.cmb_frequency.addItem("Ročně", "yearly")
        self.cmb_frequency.addItem("Vlastní interval", "custom")
        self.cmb_frequency.currentIndexChanged.connect(self.on_frequency_changed)
        form.addRow("Frekvence: *", self.cmb_frequency)

        interval_layout = QHBoxLayout()
        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(1, 365)
        self.spin_interval.setValue(1)
        interval_layout.addWidget(self.spin_interval)
        self.lbl_interval_unit = QLabel("den/dní")
        interval_layout.addWidget(self.lbl_interval_unit)
        interval_layout.addStretch()
        form.addRow("Interval:", interval_layout)

        layout.addLayout(form)

        self.weekly_group = QGroupBox("Dny v týdnu")
        weekly_layout = QHBoxLayout(self.weekly_group)

        self.day_checkboxes = {}
        days = [("Po", 0), ("Út", 1), ("St", 2), ("Čt", 3), ("Pá", 4), ("So", 5), ("Ne", 6)]
        for name, value in days:
            cb = QCheckBox(name)
            self.day_checkboxes[value] = cb
            weekly_layout.addWidget(cb)

        self.weekly_group.setVisible(False)
        layout.addWidget(self.weekly_group)

        self.monthly_group = QGroupBox("Den v měsíci")
        monthly_layout = QHBoxLayout(self.monthly_group)
        monthly_layout.addWidget(QLabel("Den:"))
        self.spin_day_of_month = QSpinBox()
        self.spin_day_of_month.setRange(1, 31)
        self.spin_day_of_month.setValue(1)
        monthly_layout.addWidget(self.spin_day_of_month)
        monthly_layout.addStretch()
        self.monthly_group.setVisible(False)
        layout.addWidget(self.monthly_group)

        end_group = QGroupBox("Ukončení opakování")
        end_layout = QVBoxLayout(end_group)

        self.rb_never = QCheckBox("Nikdy nekončí")
        self.rb_never.setChecked(True)
        self.rb_never.stateChanged.connect(self.on_end_type_changed)
        end_layout.addWidget(self.rb_never)

        count_layout = QHBoxLayout()
        self.rb_count = QCheckBox("Po počtu opakování:")
        self.rb_count.stateChanged.connect(self.on_end_type_changed)
        count_layout.addWidget(self.rb_count)
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 1000)
        self.spin_count.setValue(10)
        self.spin_count.setEnabled(False)
        count_layout.addWidget(self.spin_count)
        count_layout.addStretch()
        end_layout.addLayout(count_layout)

        date_layout = QHBoxLayout()
        self.rb_date = QCheckBox("K datu:")
        self.rb_date.stateChanged.connect(self.on_end_type_changed)
        date_layout.addWidget(self.rb_date)
        self.dt_end = QDateEdit()
        self.dt_end.setCalendarPopup(True)
        self.dt_end.setDate(QDate.currentDate().addYears(1))
        self.dt_end.setEnabled(False)
        date_layout.addWidget(self.dt_end)
        date_layout.addStretch()
        end_layout.addLayout(date_layout)

        layout.addWidget(end_group)

        exceptions_group = QGroupBox("Výjimky (dny, kdy se událost neopakuje)")
        exceptions_layout = QVBoxLayout(exceptions_group)

        self.chk_skip_holidays = QCheckBox("Přeskočit státní svátky")
        self.chk_skip_holidays.setChecked(True)
        exceptions_layout.addWidget(self.chk_skip_holidays)

        self.chk_skip_weekends = QCheckBox("Přeskočit víkendy")
        exceptions_layout.addWidget(self.chk_skip_weekends)

        custom_exceptions_layout = QHBoxLayout()
        custom_exceptions_layout.addWidget(QLabel("Vlastní výjimky (data):"))
        self.txt_exceptions = QLineEdit()
        self.txt_exceptions.setPlaceholderText("např. 2025-12-24, 2025-12-31")
        custom_exceptions_layout.addWidget(self.txt_exceptions)
        exceptions_layout.addLayout(custom_exceptions_layout)

        layout.addWidget(exceptions_group)

        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Uložit")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self.save_rule)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

        self.setStyleSheet(f"""
            QLineEdit, QComboBox, QSpinBox, QDateEdit {{
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
        """)

    def on_frequency_changed(self):
        frequency = self.cmb_frequency.currentData()

        self.weekly_group.setVisible(frequency == "weekly")
        self.monthly_group.setVisible(frequency == "monthly")

        if frequency == "daily":
            self.lbl_interval_unit.setText("den/dní")
        elif frequency == "weekly":
            self.lbl_interval_unit.setText("týden/týdnů")
        elif frequency == "monthly":
            self.lbl_interval_unit.setText("měsíc/měsíců")
        elif frequency == "yearly":
            self.lbl_interval_unit.setText("rok/let")
        else:
            self.lbl_interval_unit.setText("den/dní")

    def on_end_type_changed(self):
        if self.rb_never.isChecked():
            self.rb_count.setChecked(False)
            self.rb_date.setChecked(False)
            self.spin_count.setEnabled(False)
            self.dt_end.setEnabled(False)
        elif self.rb_count.isChecked():
            self.rb_never.setChecked(False)
            self.rb_date.setChecked(False)
            self.spin_count.setEnabled(True)
            self.dt_end.setEnabled(False)
        elif self.rb_date.isChecked():
            self.rb_never.setChecked(False)
            self.rb_count.setChecked(False)
            self.spin_count.setEnabled(False)
            self.dt_end.setEnabled(True)

    def set_defaults(self):
        self.cmb_frequency.setCurrentIndex(0)
        self.spin_interval.setValue(1)
        self.rb_never.setChecked(True)

    def load_rule_data(self):
        rule = db.fetch_one("SELECT * FROM calendar_recurring_rules WHERE id = ?", (self.rule_id,))
        if not rule:
            QMessageBox.warning(self, "Chyba", "Pravidlo nebylo nalezeno.")
            self.reject()
            return

        self.txt_name.setText(dict(rule).get('name', ''))

        frequency = dict(rule).get('frequency', 'daily')
        for i in range(self.cmb_frequency.count()):
            if self.cmb_frequency.itemData(i) == frequency:
                self.cmb_frequency.setCurrentIndex(i)
                break

        self.spin_interval.setValue(dict(rule).get('interval_value', 1))

        if dict(rule).get('days_of_week'):
            days = json.loads(rule['days_of_week'])
            for day in days:
                if day in self.day_checkboxes:
                    self.day_checkboxes[day].setChecked(True)

        if dict(rule).get('day_of_month'):
            self.spin_day_of_month.setValue(rule['day_of_month'])

        if dict(rule).get('end_date'):
            self.rb_date.setChecked(True)
            self.dt_end.setDate(QDate.fromString(rule['end_date'], Qt.DateFormat.ISODate))
        elif dict(rule).get('occurrence_count'):
            self.rb_count.setChecked(True)
            self.spin_count.setValue(rule['occurrence_count'])
        else:
            self.rb_never.setChecked(True)

        if dict(rule).get('exceptions'):
            exceptions = json.loads(rule['exceptions'])
            self.chk_skip_holidays.setChecked(exceptions.get('skip_holidays', False))
            self.chk_skip_weekends.setChecked(exceptions.get('skip_weekends', False))
            if exceptions.get('custom_dates'):
                self.txt_exceptions.setText(", ".join(exceptions['custom_dates']))

    def save_rule(self):
        if not self.txt_name.text().strip():
            QMessageBox.warning(self, "Chyba", "Název pravidla je povinný.")
            return

        data = {
            'name': self.txt_name.text().strip(),
            'frequency': self.cmb_frequency.currentData(),
            'interval_value': self.spin_interval.value(),
            'days_of_week': None,
            'day_of_month': None,
            'end_date': None,
            'occurrence_count': None,
            'exceptions': None
        }

        if self.cmb_frequency.currentData() == "weekly":
            selected_days = [day for day, cb in self.day_checkboxes.items() if cb.isChecked()]
            data['days_of_week'] = json.dumps(selected_days)

        if self.cmb_frequency.currentData() == "monthly":
            data['day_of_month'] = self.spin_day_of_month.value()

        if self.rb_count.isChecked():
            data['occurrence_count'] = self.spin_count.value()
        elif self.rb_date.isChecked():
            data['end_date'] = self.dt_end.date().toString(Qt.DateFormat.ISODate)

        exceptions = {
            'skip_holidays': self.chk_skip_holidays.isChecked(),
            'skip_weekends': self.chk_skip_weekends.isChecked(),
            'custom_dates': [d.strip() for d in self.txt_exceptions.text().split(",") if d.strip()]
        }
        data['exceptions'] = json.dumps(exceptions)

        try:
            if self.is_edit:
                set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
                query = f"UPDATE calendar_recurring_rules SET {set_clause} WHERE id = ?"
                params = list(data.values()) + [self.rule_id]
                db.execute_query(query, tuple(params))
                QMessageBox.information(self, "Úspěch", "Pravidlo bylo aktualizováno.")
            else:
                data['created_at'] = datetime.now().isoformat()
                columns = ", ".join(data.keys())
                placeholders = ", ".join(["?" for _ in data])
                query = f"INSERT INTO calendar_recurring_rules ({columns}) VALUES ({placeholders})"
                db.execute_query(query, tuple(data.values()))
                QMessageBox.information(self, "Úspěch", "Pravidlo bylo vytvořeno.")

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při ukládání: {e}")


class CalendarRecurring(QWidget):
    """Widget pro správu opakujících se událostí"""

    rule_selected = pyqtSignal(int)
    generate_requested = pyqtSignal(int)

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

        content_layout = QHBoxLayout()

        rules_panel = self.create_rules_panel()
        content_layout.addWidget(rules_panel, 2)

        detail_panel = self.create_detail_panel()
        content_layout.addWidget(detail_panel, 3)

        main_layout.addLayout(content_layout)

        examples_panel = self.create_examples_panel()
        main_layout.addWidget(examples_panel)

    def create_top_panel(self):
        panel = QFrame()
        panel.setObjectName("topPanel")
        panel.setFixedHeight(60)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(15, 10, 15, 10)

        title = QLabel("🔄 Opakující se události")
        title.setObjectName("panelTitle")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        layout.addStretch()

        self.btn_new_rule = QPushButton("➕ Nové pravidlo")
        self.btn_new_rule.setObjectName("primaryButton")
        self.btn_new_rule.clicked.connect(self.create_rule)
        layout.addWidget(self.btn_new_rule)

        self.btn_generate_all = QPushButton("⚡ Generovat všechny instance")
        self.btn_generate_all.setObjectName("actionButton")
        self.btn_generate_all.clicked.connect(self.generate_all_instances)
        layout.addWidget(self.btn_generate_all)

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
        """)

        return panel

    def create_rules_panel(self):
        panel = QFrame()
        panel.setObjectName("rulesPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        header = QLabel("📋 Pravidla opakování")
        header.setObjectName("sectionHeader")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        header.setFont(font)
        layout.addWidget(header)

        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(5)
        self.rules_table.setHorizontalHeaderLabels(["ID", "Název", "Frekvence", "Aktivní", "Akce"])
        self.rules_table.setColumnHidden(0, True)
        self.rules_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.rules_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.rules_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.rules_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.rules_table.setColumnWidth(3, 80)
        self.rules_table.setColumnWidth(4, 120)
        self.rules_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.rules_table.setAlternatingRowColors(True)
        self.rules_table.doubleClicked.connect(self.on_rule_double_clicked)
        layout.addWidget(self.rules_table)

        panel.setStyleSheet(f"""
            #rulesPanel {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}
            #sectionHeader {{
                color: {config.COLOR_PRIMARY};
                padding: 5px;
            }}
            QTableWidget {{
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }}
        """)

        return panel

    def create_detail_panel(self):
        panel = QFrame()
        panel.setObjectName("detailPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        self.detail_header = QLabel("📊 Detail pravidla")
        self.detail_header.setObjectName("detailHeader")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14)
        self.detail_header.setFont(font)
        layout.addWidget(self.detail_header)

        info_group = QGroupBox("Informace o pravidle")
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(8)

        self.lbl_frequency = QLabel("-")
        info_layout.addRow("Frekvence:", self.lbl_frequency)

        self.lbl_interval = QLabel("-")
        info_layout.addRow("Interval:", self.lbl_interval)

        self.lbl_end = QLabel("-")
        info_layout.addRow("Ukončení:", self.lbl_end)

        self.lbl_exceptions = QLabel("-")
        info_layout.addRow("Výjimky:", self.lbl_exceptions)

        self.lbl_instances = QLabel("-")
        info_layout.addRow("Generované instance:", self.lbl_instances)

        layout.addWidget(info_group)

        preview_group = QGroupBox("Náhled příštích instancí")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_list = QListWidget()
        self.preview_list.setMaximumHeight(150)
        preview_layout.addWidget(self.preview_list)

        layout.addWidget(preview_group)

        actions_layout = QHBoxLayout()

        self.btn_edit_rule = QPushButton("✏️ Editovat pravidlo")
        self.btn_edit_rule.clicked.connect(self.edit_selected_rule)
        actions_layout.addWidget(self.btn_edit_rule)

        self.btn_generate = QPushButton("⚡ Generovat instance")
        self.btn_generate.clicked.connect(self.generate_instances)
        actions_layout.addWidget(self.btn_generate)

        self.btn_delete_rule = QPushButton("🗑️ Smazat pravidlo")
        self.btn_delete_rule.setObjectName("dangerButton")
        self.btn_delete_rule.clicked.connect(self.delete_selected_rule)
        actions_layout.addWidget(self.btn_delete_rule)

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
            #dangerButton {{
                background-color: {config.COLOR_DANGER};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }}
        """)

        return panel

    def create_examples_panel(self):
        panel = QFrame()
        panel.setObjectName("examplesPanel")
        panel.setFixedHeight(100)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 10, 15, 10)

        title = QLabel("💡 Příklady použití")
        title.setObjectName("examplesTitle")
        font = QFont()
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        examples_layout = QHBoxLayout()

        examples = [
            ("📅 Pravidelný servis", "Každé 3 měsíce"),
            ("👥 Týdenní schůzka", "Každé pondělí"),
            ("📦 Měsíční inventura", "1. den v měsíci"),
            ("🚗 Roční STK", "Každý rok ve stejný den")
        ]

        for name, desc in examples:
            example_frame = QFrame()
            example_frame.setObjectName("exampleFrame")
            example_layout = QVBoxLayout(example_frame)
            example_layout.setContentsMargins(10, 5, 10, 5)
            example_layout.setSpacing(2)

            name_label = QLabel(name)
            name_label.setStyleSheet("font-weight: bold; font-size: 11px;")
            example_layout.addWidget(name_label)

            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: #666; font-size: 10px;")
            example_layout.addWidget(desc_label)

            examples_layout.addWidget(example_frame)

        layout.addLayout(examples_layout)

        panel.setStyleSheet(f"""
            #examplesPanel {{
                background-color: #e3f2fd;
                border-radius: 8px;
                border: 1px solid #90caf9;
            }}
            #examplesTitle {{
                color: {config.COLOR_PRIMARY};
            }}
            #exampleFrame {{
                background-color: white;
                border-radius: 5px;
                border: 1px solid #90caf9;
            }}
        """)

        return panel

    def refresh(self):
        self.load_rules()

    def load_rules(self):
        rules = db.fetch_all("""
            SELECT id, name, frequency, interval_value, end_date, occurrence_count
            FROM calendar_recurring_rules
            ORDER BY name
        """)

        self.rules_table.setRowCount(len(rules))

        frequency_names = {
            'daily': 'Denně',
            'weekdays': 'Pracovní dny',
            'weekly': 'Týdně',
            'monthly': 'Měsíčně',
            'yearly': 'Ročně',
            'custom': 'Vlastní'
        }

        for row, rule in enumerate(rules):
            id_item = QTableWidgetItem(str(rule['id']))
            self.rules_table.setItem(row, 0, id_item)

            name_item = QTableWidgetItem(rule['name'] or "")
            self.rules_table.setItem(row, 1, name_item)

            freq_text = frequency_names.get(rule['frequency'], rule['frequency'])
            if rule['interval_value'] > 1:
                freq_text += f" (každý {rule['interval_value']})"
            freq_item = QTableWidgetItem(freq_text)
            self.rules_table.setItem(row, 2, freq_item)

            active_item = QTableWidgetItem("✅")
            active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.rules_table.setItem(row, 3, active_item)

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.setSpacing(3)

            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(30, 25)
            btn_edit.setToolTip("Editovat")
            btn_edit.clicked.connect(lambda checked, rid=rule['id']: self.edit_rule(rid))
            actions_layout.addWidget(btn_edit)

            btn_generate = QPushButton("⚡")
            btn_generate.setFixedSize(30, 25)
            btn_generate.setToolTip("Generovat")
            btn_generate.clicked.connect(lambda checked, rid=rule['id']: self.generate_for_rule(rid))
            actions_layout.addWidget(btn_generate)

            btn_delete = QPushButton("🗑️")
            btn_delete.setFixedSize(30, 25)
            btn_delete.setToolTip("Smazat")
            btn_delete.clicked.connect(lambda checked, rid=rule['id']: self.delete_rule(rid))
            actions_layout.addWidget(btn_delete)

            self.rules_table.setCellWidget(row, 4, actions_widget)

    def on_rule_double_clicked(self, index):
        row = index.row()
        rule_id = int(self.rules_table.item(row, 0).text())
        self.load_rule_detail(rule_id)

    def load_rule_detail(self, rule_id):
        rule = db.fetch_one("SELECT * FROM calendar_recurring_rules WHERE id = ?", (rule_id,))
        if not rule:
            return

        self.detail_header.setText(f"📊 Detail: {rule['name']}")

        frequency_names = {
            'daily': 'Denně',
            'weekdays': 'Pouze pracovní dny',
            'weekly': 'Týdně',
            'monthly': 'Měsíčně',
            'yearly': 'Ročně',
            'custom': 'Vlastní interval'
        }
        self.lbl_frequency.setText(frequency_names.get(rule['frequency'], rule['frequency']))

        self.lbl_interval.setText(f"Každý {rule['interval_value']}. interval")

        if rule['end_date']:
            self.lbl_end.setText(f"Do: {rule['end_date']}")
        elif rule['occurrence_count']:
            self.lbl_end.setText(f"Po {rule['occurrence_count']} opakováních")
        else:
            self.lbl_end.setText("Nikdy nekončí")

        if rule['exceptions']:
            exceptions = json.loads(rule['exceptions'])
            exc_text = []
            if exceptions.get('skip_holidays'):
                exc_text.append("Svátky")
            if exceptions.get('skip_weekends'):
                exc_text.append("Víkendy")
            if exceptions.get('custom_dates'):
                exc_text.append(f"{len(exceptions['custom_dates'])} vlastních dat")
            self.lbl_exceptions.setText(", ".join(exc_text) if exc_text else "Žádné")
        else:
            self.lbl_exceptions.setText("Žádné")

        instances_count = db.fetch_one("""
            SELECT COUNT(*) as count FROM calendar_events
            WHERE recurring_rule_id = ?
        """, (rule_id,))
        self.lbl_instances.setText(str(instances_count['count'] if instances_count else 0))

        self.generate_preview(rule)

    def generate_preview(self, rule):
        self.preview_list.clear()

        today = date.today()
        preview_dates = []

        for i in range(10):
            if rule['frequency'] == 'daily':
                next_date = today + timedelta(days=i * rule['interval_value'])
            elif rule['frequency'] == 'weekly':
                next_date = today + timedelta(weeks=i * rule['interval_value'])
            elif rule['frequency'] == 'monthly':
                month_offset = i * rule['interval_value']
                year_offset = month_offset // 12
                month = today.month + (month_offset % 12)
                if month > 12:
                    month -= 12
                    year_offset += 1
                day = min(today.day, 28)
                next_date = today.replace(year=today.year + year_offset, month=month, day=day)
            else:
                next_date = today + timedelta(days=i)

            skip = False
            if rule['exceptions']:
                exceptions = json.loads(rule['exceptions'])
                if exceptions.get('skip_weekends') and next_date.weekday() >= 5:
                    skip = True

            if not skip:
                preview_dates.append(next_date)

        days_cz = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]
        for d in preview_dates[:10]:
            day_name = days_cz[d.weekday()]
            item = QListWidgetItem(f"📅 {day_name} {d.strftime('%d.%m.%Y')}")
            self.preview_list.addItem(item)

    def create_rule(self):
        dialog = RecurringRuleDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def edit_rule(self, rule_id):
        dialog = RecurringRuleDialog(rule_id=rule_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def edit_selected_rule(self):
        current_row = self.rules_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Upozornění", "Nejprve vyberte pravidlo.")
            return

        rule_id = int(self.rules_table.item(current_row, 0).text())
        self.edit_rule(rule_id)

    def delete_rule(self, rule_id):
        reply = QMessageBox.question(
            self,
            "Potvrzení",
            "Opravdu chcete smazat toto pravidlo?\n\nVšechny vygenerované instance zůstanou zachovány.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                db.execute_query(
                    "UPDATE calendar_events SET recurring_rule_id = NULL WHERE recurring_rule_id = ?",
                    (rule_id,)
                )
                db.execute_query("DELETE FROM calendar_recurring_rules WHERE id = ?", (rule_id,))
                QMessageBox.information(self, "Úspěch", "Pravidlo bylo smazáno.")
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Chyba při mazání: {e}")

    def delete_selected_rule(self):
        current_row = self.rules_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Upozornění", "Nejprve vyberte pravidlo.")
            return

        rule_id = int(self.rules_table.item(current_row, 0).text())
        self.delete_rule(rule_id)

    def generate_for_rule(self, rule_id):
        rule = db.fetch_one("SELECT * FROM calendar_recurring_rules WHERE id = ?", (rule_id,))
        if not rule:
            return

        generated = self.generate_instances_for_rule(rule)

        QMessageBox.information(
            self,
            "Generování dokončeno",
            f"Bylo vygenerováno {generated} nových instancí události."
        )
        self.refresh()

    def generate_instances(self):
        current_row = self.rules_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Upozornění", "Nejprve vyberte pravidlo.")
            return

        rule_id = int(self.rules_table.item(current_row, 0).text())
        self.generate_for_rule(rule_id)

    def generate_instances_for_rule(self, rule):
        today = date.today()
        end_date = today + timedelta(days=365)

        if rule['end_date']:
            end_date = min(end_date, datetime.fromisoformat(rule['end_date']).date())

        exceptions = {}
        if rule['exceptions']:
            exceptions = json.loads(rule['exceptions'])

        holidays = set()
        if exceptions.get('skip_holidays'):
            holiday_rows = db.fetch_all("SELECT holiday_date FROM calendar_holidays WHERE is_closed = 1")
            for h in holiday_rows:
                holidays.add(h['holiday_date'])

        generated = 0
        current_date = today
        count = 0
        max_count = rule['occurrence_count'] or 1000

        while current_date <= end_date and count < max_count:
            skip = False

            if exceptions.get('skip_weekends') and current_date.weekday() >= 5:
                skip = True

            if current_date.isoformat() in holidays:
                skip = True

            if exceptions.get('custom_dates') and current_date.isoformat() in exceptions['custom_dates']:
                skip = True

            if not skip:
                existing = db.fetch_one("""
                    SELECT id FROM calendar_events
                    WHERE recurring_rule_id = ? AND DATE(start_datetime) = ?
                """, (rule['id'], current_date.isoformat()))

                if not existing:
                    event_data = {
                        'title': f"{rule['name']} (opakující se)",
                        'event_type': 'service',
                        'start_datetime': f"{current_date.isoformat()}T09:00:00",
                        'end_datetime': f"{current_date.isoformat()}T10:00:00",
                        'all_day': 0,
                        'recurring_rule_id': rule['id'],
                        'priority': 2,
                        'color': '#3498db',
                        'status': 'scheduled',
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }

                    columns = ", ".join(event_data.keys())
                    placeholders = ", ".join(["?" for _ in event_data])
                    query = f"INSERT INTO calendar_events ({columns}) VALUES ({placeholders})"
                    db.execute_query(query, tuple(event_data.values()))
                    generated += 1

                count += 1

            if rule['frequency'] == 'daily':
                current_date += timedelta(days=rule['interval_value'])
            elif rule['frequency'] == 'weekdays':
                current_date += timedelta(days=1)
                while current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
            elif rule['frequency'] == 'weekly':
                current_date += timedelta(weeks=rule['interval_value'])
            elif rule['frequency'] == 'monthly':
                month = current_date.month + rule['interval_value']
                year = current_date.year
                while month > 12:
                    month -= 12
                    year += 1
                day = min(current_date.day, 28)
                current_date = current_date.replace(year=year, month=month, day=day)
            elif rule['frequency'] == 'yearly':
                current_date = current_date.replace(year=current_date.year + rule['interval_value'])
            else:
                current_date += timedelta(days=1)

        return generated

    def generate_all_instances(self):
        reply = QMessageBox.question(
            self,
            "Generovat všechny instance",
            "Chcete vygenerovat instance pro všechna pravidla na příští rok?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            rules = db.fetch_all("SELECT * FROM calendar_recurring_rules")
            total_generated = 0

            for rule in rules:
                generated = self.generate_instances_for_rule(dict(rule))
                total_generated += generated

            QMessageBox.information(
                self,
                "Generování dokončeno",
                f"Celkem vygenerováno {total_generated} nových instancí."
            )
            self.refresh()
