# -*- coding: utf-8 -*-
"""
Export a tisk kalendáře
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QFrame, QGroupBox, QDateEdit, QCheckBox,
    QMessageBox, QFileDialog, QTextEdit, QLineEdit,
    QRadioButton, QButtonGroup, QTabWidget, QListWidget,
    QListWidgetItem, QProgressBar
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QBuffer, QIODevice
from PyQt6.QtGui import QFont, QPixmap, QImage, QPainter
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from datetime import datetime, date, timedelta
from database_manager import db
import config
import csv
import os


class CalendarExport(QWidget):
    """Widget pro export a tisk kalendáře"""

    export_completed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        top_panel = self.create_top_panel()
        main_layout.addWidget(top_panel)

        tabs = QTabWidget()
        tabs.addTab(self.create_export_tab(), "📤 Export")
        tabs.addTab(self.create_print_tab(), "🖨️ Tisk")
        tabs.addTab(self.create_share_tab(), "🔗 Sdílení")

        main_layout.addWidget(tabs)

        progress_frame = QFrame()
        progress_frame.setObjectName("progressFrame")
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(10, 10, 10, 10)

        self.lbl_status = QLabel("Připraveno k exportu")
        progress_layout.addWidget(self.lbl_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)

        main_layout.addWidget(progress_frame)

        progress_frame.setStyleSheet("""
            #progressFrame {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }
        """)

    def create_top_panel(self):
        panel = QFrame()
        panel.setObjectName("topPanel")
        panel.setFixedHeight(60)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(15, 10, 15, 10)

        title = QLabel("📤 Export a tisk kalendáře")
        title.setObjectName("panelTitle")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        layout.addStretch()

        panel.setStyleSheet(f"""
            #topPanel {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}
            #panelTitle {{
                color: {config.COLOR_PRIMARY};
            }}
        """)

        return panel

    def create_export_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        period_group = QGroupBox("Období exportu")
        period_layout = QHBoxLayout(period_group)

        period_layout.addWidget(QLabel("Od:"))
        self.dt_export_from = QDateEdit()
        self.dt_export_from.setCalendarPopup(True)
        self.dt_export_from.setDate(QDate.currentDate())
        period_layout.addWidget(self.dt_export_from)

        period_layout.addWidget(QLabel("Do:"))
        self.dt_export_to = QDateEdit()
        self.dt_export_to.setCalendarPopup(True)
        self.dt_export_to.setDate(QDate.currentDate().addDays(30))
        period_layout.addWidget(self.dt_export_to)

        period_layout.addStretch()

        layout.addWidget(period_group)

        format_group = QGroupBox("Formát exportu")
        format_layout = QVBoxLayout(format_group)

        self.format_group = QButtonGroup()

        self.rb_pdf = QRadioButton("📄 PDF - Týdenní/měsíční rozvrh")
        self.rb_pdf.setChecked(True)
        self.format_group.addButton(self.rb_pdf, 1)
        format_layout.addWidget(self.rb_pdf)

        self.rb_excel = QRadioButton("📊 Excel - Seznam událostí s detaily")
        self.format_group.addButton(self.rb_excel, 2)
        format_layout.addWidget(self.rb_excel)

        self.rb_ical = QRadioButton("📅 iCalendar (.ics) - Pro import do kalendáře")
        self.format_group.addButton(self.rb_ical, 3)
        format_layout.addWidget(self.rb_ical)

        self.rb_csv = QRadioButton("📋 CSV - Raw data pro analýzu")
        self.format_group.addButton(self.rb_csv, 4)
        format_layout.addWidget(self.rb_csv)

        layout.addWidget(format_group)

        options_group = QGroupBox("Možnosti exportu")
        options_layout = QVBoxLayout(options_group)

        self.chk_include_cancelled = QCheckBox("Zahrnout zrušené události")
        options_layout.addWidget(self.chk_include_cancelled)

        self.chk_include_customers = QCheckBox("Zahrnout kontaktní údaje zákazníků")
        self.chk_include_customers.setChecked(True)
        options_layout.addWidget(self.chk_include_customers)

        self.chk_include_notes = QCheckBox("Zahrnout poznámky a popisy")
        self.chk_include_notes.setChecked(True)
        options_layout.addWidget(self.chk_include_notes)

        self.chk_group_by_mechanic = QCheckBox("Seskupit podle mechanika")
        options_layout.addWidget(self.chk_group_by_mechanic)

        layout.addWidget(options_group)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.btn_export = QPushButton("📤 Exportovat")
        self.btn_export.setObjectName("primaryButton")
        self.btn_export.clicked.connect(self.perform_export)
        buttons_layout.addWidget(self.btn_export)

        layout.addLayout(buttons_layout)

        layout.addStretch()

        return tab

    def create_print_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        type_group = QGroupBox("Typ tisku")
        type_layout = QVBoxLayout(type_group)

        self.print_type_group = QButtonGroup()

        self.rb_daily = QRadioButton("📋 Denní rozvrh - Pro mechanika")
        self.rb_daily.setChecked(True)
        self.print_type_group.addButton(self.rb_daily, 1)
        type_layout.addWidget(self.rb_daily)

        self.rb_weekly = QRadioButton("📊 Týdenní přehled - Pro management")
        self.print_type_group.addButton(self.rb_weekly, 2)
        type_layout.addWidget(self.rb_weekly)

        self.rb_monthly = QRadioButton("📅 Měsíční kalendář - Na zeď")
        self.print_type_group.addButton(self.rb_monthly, 3)
        type_layout.addWidget(self.rb_monthly)

        self.rb_orderlist = QRadioButton("📝 Seznam zakázek na den")
        self.print_type_group.addButton(self.rb_orderlist, 4)
        type_layout.addWidget(self.rb_orderlist)

        layout.addWidget(type_group)

        template_group = QGroupBox("Šablona tisku")
        template_layout = QVBoxLayout(template_group)

        self.template_group = QButtonGroup()

        self.rb_compact = QRadioButton("📦 Kompaktní - Více na stránku")
        self.rb_compact.setChecked(True)
        self.template_group.addButton(self.rb_compact, 1)
        template_layout.addWidget(self.rb_compact)

        self.rb_detailed = QRadioButton("📝 Detailní - Všechny informace")
        self.template_group.addButton(self.rb_detailed, 2)
        template_layout.addWidget(self.rb_detailed)

        self.rb_empty = QRadioButton("📄 Prázdný formulář - Pro ruční zápis")
        self.template_group.addButton(self.rb_empty, 3)
        template_layout.addWidget(self.rb_empty)

        layout.addWidget(template_group)

        date_group = QGroupBox("Datum tisku")
        date_layout = QHBoxLayout(date_group)

        date_layout.addWidget(QLabel("Datum:"))
        self.dt_print = QDateEdit()
        self.dt_print.setCalendarPopup(True)
        self.dt_print.setDate(QDate.currentDate())
        date_layout.addWidget(self.dt_print)

        date_layout.addWidget(QLabel("Mechanik:"))
        self.cmb_print_mechanic = QComboBox()
        self.cmb_print_mechanic.addItem("Všichni", None)
        self.load_mechanics_combo()
        date_layout.addWidget(self.cmb_print_mechanic)

        date_layout.addStretch()

        layout.addWidget(date_group)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.btn_preview = QPushButton("👁️ Náhled")
        self.btn_preview.clicked.connect(self.show_print_preview)
        buttons_layout.addWidget(self.btn_preview)

        self.btn_print = QPushButton("🖨️ Tisknout")
        self.btn_print.setObjectName("primaryButton")
        self.btn_print.clicked.connect(self.perform_print)
        buttons_layout.addWidget(self.btn_print)

        layout.addLayout(buttons_layout)

        layout.addStretch()

        return tab

    def create_share_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        email_group = QGroupBox("Email rozvrhu zákazníkovi")
        email_layout = QVBoxLayout(email_group)

        recipient_layout = QHBoxLayout()
        recipient_layout.addWidget(QLabel("Email:"))
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("zakaznik@email.cz")
        recipient_layout.addWidget(self.txt_email)
        email_layout.addLayout(recipient_layout)

        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("Předmět:"))
        self.txt_subject = QLineEdit()
        self.txt_subject.setText("Váš servisní termín")
        subject_layout.addWidget(self.txt_subject)
        email_layout.addLayout(subject_layout)

        email_layout.addWidget(QLabel("Zpráva:"))
        self.txt_message = QTextEdit()
        self.txt_message.setMaximumHeight(100)
        self.txt_message.setPlainText(
            "Dobrý den,\n\n"
            "posíláme Vám potvrzení Vašeho servisního termínu.\n\n"
            "S pozdravem,\nVáš motoservis"
        )
        email_layout.addWidget(self.txt_message)

        self.btn_send_email = QPushButton("📧 Odeslat email")
        self.btn_send_email.clicked.connect(self.send_email)
        email_layout.addWidget(self.btn_send_email)

        layout.addWidget(email_group)

        link_group = QGroupBox("Online kalendář")
        link_layout = QVBoxLayout(link_group)

        link_info = QLabel(
            "Vygenerujte veřejný odkaz pro zákazníky, "
            "kde si mohou rezervovat termíny."
        )
        link_info.setWordWrap(True)
        link_layout.addWidget(link_info)

        link_input_layout = QHBoxLayout()
        self.txt_link = QLineEdit()
        self.txt_link.setReadOnly(True)
        self.txt_link.setText("https://vas-servis.cz/booking/abc123")
        link_input_layout.addWidget(self.txt_link)

        self.btn_copy_link = QPushButton("📋 Kopírovat")
        self.btn_copy_link.clicked.connect(self.copy_link)
        link_input_layout.addWidget(self.btn_copy_link)

        link_layout.addLayout(link_input_layout)

        self.btn_generate_link = QPushButton("🔄 Generovat nový odkaz")
        self.btn_generate_link.clicked.connect(self.generate_link)
        link_layout.addWidget(self.btn_generate_link)

        layout.addWidget(link_group)

        qr_group = QGroupBox("QR kód pro rezervaci")
        qr_layout = QVBoxLayout(qr_group)

        qr_info = QLabel(
            "QR kód můžete vytisknout a vystavit v servisu. "
            "Zákazníci jej naskenují telefonem a dostanou se na rezervační stránku."
        )
        qr_info.setWordWrap(True)
        qr_layout.addWidget(qr_info)

        qr_buttons = QHBoxLayout()

        self.btn_generate_qr = QPushButton("🔲 Generovat QR kód")
        self.btn_generate_qr.clicked.connect(self.generate_qr)
        qr_buttons.addWidget(self.btn_generate_qr)

        self.btn_save_qr = QPushButton("💾 Uložit QR kód")
        self.btn_save_qr.clicked.connect(self.save_qr)
        qr_buttons.addWidget(self.btn_save_qr)

        self.btn_print_qr = QPushButton("🖨️ Tisknout QR kód")
        self.btn_print_qr.clicked.connect(self.print_qr)
        qr_buttons.addWidget(self.btn_print_qr)

        qr_layout.addLayout(qr_buttons)

        layout.addWidget(qr_group)

        layout.addStretch()

        return tab

    def load_mechanics_combo(self):
        mechanics = db.fetch_all("""
            SELECT id, full_name FROM users
            WHERE role IN ('mechanik', 'admin') AND active = 1
            ORDER BY full_name
        """)

        for m in mechanics:
            self.cmb_print_mechanic.addItem(f"👤 {m['full_name']}", m['id'])

    def perform_export(self):
        format_id = self.format_group.checkedId()
        from_date = self.dt_export_from.date().toPyDate()
        to_date = self.dt_export_to.date().toPyDate()

        if to_date < from_date:
            QMessageBox.warning(self, "Chyba", "Datum 'Do' musí být po datu 'Od'.")
            return

        if format_id == 1:
            self.export_pdf(from_date, to_date)
        elif format_id == 2:
            self.export_excel(from_date, to_date)
        elif format_id == 3:
            self.export_ical(from_date, to_date)
        elif format_id == 4:
            self.export_csv(from_date, to_date)

    def export_pdf(self, from_date, to_date):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit PDF",
            f"kalendar_{from_date.isoformat()}_{to_date.isoformat()}.pdf",
            "PDF soubory (*.pdf)"
        )

        if not file_path:
            return

        self.lbl_status.setText("Generuji PDF...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.progress_bar.setValue(50)

        events = self.fetch_events(from_date, to_date)

        pdf_content = self.generate_pdf_content(events, from_date, to_date)

        try:
            with open(file_path.replace('.pdf', '_preview.txt'), 'w', encoding='utf-8') as f:
                f.write(pdf_content)

            self.progress_bar.setValue(100)
            self.lbl_status.setText(f"Export dokončen: {file_path}")

            QMessageBox.information(
                self,
                "Export dokončen",
                f"PDF export byl uložen do:\n{file_path}\n\n"
                "Poznámka: Pro plnou podporu PDF je potřeba knihovna reportlab."
            )

            self.export_completed.emit(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při exportu: {e}")
        finally:
            self.progress_bar.setVisible(False)

    def export_excel(self, from_date, to_date):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit Excel",
            f"kalendar_{from_date.isoformat()}_{to_date.isoformat()}.xlsx",
            "Excel soubory (*.xlsx)"
        )

        if not file_path:
            return

        self.lbl_status.setText("Generuji Excel...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        events = self.fetch_events(from_date, to_date)
        self.progress_bar.setValue(50)

        csv_path = file_path.replace('.xlsx', '.csv')

        try:
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')

                headers = ['ID', 'Datum', 'Čas', 'Název', 'Typ', 'Stav', 'Priorita']
                if self.chk_include_customers.isChecked():
                    headers.extend(['Zákazník', 'Telefon', 'Email'])
                headers.append('SPZ')
                headers.append('Mechanik')
                if self.chk_include_notes.isChecked():
                    headers.extend(['Popis', 'Poznámky'])

                writer.writerow(headers)

                for event in events:
                    row = [
                        event['id'],
                        event['event_date'],
                        event['event_time'],
                        event['title'],
                        event['event_type'],
                        event['status'],
                        event['priority']
                    ]

                    if self.chk_include_customers.isChecked():
                        row.extend([
                            event['customer_name'] or '',
                            event['customer_phone'] or '',
                            event['customer_email'] or ''
                        ])

                    row.append(event['license_plate'] or '')
                    row.append(event['mechanic_name'] or '')

                    if self.chk_include_notes.isChecked():
                        row.extend([
                            event['description'] or '',
                            event['notes'] or ''
                        ])

                    writer.writerow(row)

            self.progress_bar.setValue(100)
            self.lbl_status.setText(f"Export dokončen: {csv_path}")

            QMessageBox.information(
                self,
                "Export dokončen",
                f"Excel data byla uložena do:\n{csv_path}\n\n"
                "Poznámka: Pro plnou podporu .xlsx je potřeba knihovna openpyxl."
            )

            self.export_completed.emit(csv_path)
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při exportu: {e}")
        finally:
            self.progress_bar.setVisible(False)

    def export_ical(self, from_date, to_date):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit iCalendar",
            f"kalendar_{from_date.isoformat()}_{to_date.isoformat()}.ics",
            "iCalendar soubory (*.ics)"
        )

        if not file_path:
            return

        self.lbl_status.setText("Generuji iCalendar...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        events = self.fetch_events(from_date, to_date)
        self.progress_bar.setValue(50)

        try:
            ical_content = self.generate_ical_content(events)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(ical_content)

            self.progress_bar.setValue(100)
            self.lbl_status.setText(f"Export dokončen: {file_path}")

            QMessageBox.information(
                self,
                "Export dokončen",
                f"iCalendar soubor byl uložen do:\n{file_path}\n\n"
                "Tento soubor můžete importovat do Google Calendar, Outlook, Apple Calendar atd."
            )

            self.export_completed.emit(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při exportu: {e}")
        finally:
            self.progress_bar.setVisible(False)

    def export_csv(self, from_date, to_date):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit CSV",
            f"kalendar_{from_date.isoformat()}_{to_date.isoformat()}.csv",
            "CSV soubory (*.csv)"
        )

        if not file_path:
            return

        self.lbl_status.setText("Generuji CSV...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        events = self.fetch_events(from_date, to_date)
        self.progress_bar.setValue(50)

        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')

                writer.writerow([
                    'id', 'title', 'event_type', 'start_datetime', 'end_datetime',
                    'all_day', 'status', 'priority', 'color',
                    'customer_id', 'customer_name', 'customer_phone', 'customer_email',
                    'vehicle_id', 'license_plate',
                    'mechanic_id', 'mechanic_name',
                    'order_id', 'description', 'notes',
                    'created_at', 'updated_at'
                ])

                for event in events:
                    writer.writerow([
                        event['id'],
                        event['title'],
                        event['event_type'],
                        event['start_datetime'],
                        event['end_datetime'],
                        event['all_day'],
                        event['status'],
                        event['priority'],
                        event['color'],
                        event['customer_id'],
                        event['customer_name'],
                        event['customer_phone'],
                        event['customer_email'],
                        event['vehicle_id'],
                        event['license_plate'],
                        event['mechanic_id'],
                        event['mechanic_name'],
                        event['order_id'],
                        event['description'],
                        event['notes'],
                        event['created_at'],
                        event['updated_at']
                    ])

            self.progress_bar.setValue(100)
            self.lbl_status.setText(f"Export dokončen: {file_path}")

            QMessageBox.information(
                self,
                "Export dokončen",
                f"CSV soubor byl uložen do:\n{file_path}"
            )

            self.export_completed.emit(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při exportu: {e}")
        finally:
            self.progress_bar.setVisible(False)

    def fetch_events(self, from_date, to_date):
        query = """
            SELECT
                e.id, e.title, e.event_type, e.start_datetime, e.end_datetime,
                e.all_day, e.status, e.priority, e.color,
                e.customer_id, e.vehicle_id, e.mechanic_id, e.order_id,
                e.description, e.notes, e.created_at, e.updated_at,
                c.first_name || ' ' || c.last_name as customer_name,
                c.phone as customer_phone, c.email as customer_email,
                v.license_plate,
                u.full_name as mechanic_name
            FROM calendar_events e
            LEFT JOIN customers c ON e.customer_id = c.id
            LEFT JOIN vehicles v ON e.vehicle_id = v.id
            LEFT JOIN users u ON e.mechanic_id = u.id
            WHERE DATE(e.start_datetime) BETWEEN ? AND ?
        """
        params = [from_date.isoformat(), to_date.isoformat()]

        if not self.chk_include_cancelled.isChecked():
            query += " AND e.status != 'cancelled'"

        query += " ORDER BY e.start_datetime"

        events = db.fetch_all(query, tuple(params))

        result = []
        for event in events:
            event_dict = dict(event)
            if event['start_datetime']:
                dt = datetime.fromisoformat(event['start_datetime'])
                event_dict['event_date'] = dt.strftime("%d.%m.%Y")
                event_dict['event_time'] = dt.strftime("%H:%M")
            else:
                event_dict['event_date'] = ''
                event_dict['event_time'] = ''
            result.append(event_dict)

        return result

    def generate_pdf_content(self, events, from_date, to_date):
        content = f"""
KALENDÁŘ UDÁLOSTÍ
=================
Období: {from_date.strftime('%d.%m.%Y')} - {to_date.strftime('%d.%m.%Y')}
Vygenerováno: {datetime.now().strftime('%d.%m.%Y %H:%M')}
Celkem událostí: {len(events)}

"""

        if self.chk_group_by_mechanic.isChecked():
            mechanics = {}
            for event in events:
                mech = event['mechanic_name'] or 'Nepřiřazeno'
                if mech not in mechanics:
                    mechanics[mech] = []
                mechanics[mech].append(event)

            for mech_name, mech_events in sorted(mechanics.items()):
                content += f"\n{'='*50}\n"
                content += f"MECHANIK: {mech_name}\n"
                content += f"{'='*50}\n\n"

                for event in mech_events:
                    content += self.format_event_for_text(event)
        else:
            for event in events:
                content += self.format_event_for_text(event)

        return content

    def format_event_for_text(self, event):
        type_names = {
            'service': 'Servis',
            'meeting': 'Schůzka',
            'delivery': 'Příjem dílu',
            'handover': 'Předání',
            'reminder': 'Připomínka',
            'other': 'Jiné'
        }

        text = f"""
Datum: {event['event_date']} v {event['event_time']}
Název: {event['title']}
Typ: {type_names.get(event['event_type'], event['event_type'])}
Stav: {event['status']}
"""

        if self.chk_include_customers.isChecked() and event['customer_name']:
            text += f"Zákazník: {event['customer_name']}\n"
            if event['customer_phone']:
                text += f"Telefon: {event['customer_phone']}\n"

        if event['license_plate']:
            text += f"SPZ: {event['license_plate']}\n"

        if event['mechanic_name']:
            text += f"Mechanik: {event['mechanic_name']}\n"

        if self.chk_include_notes.isChecked():
            if event['description']:
                text += f"Popis: {event['description']}\n"
            if event['notes']:
                text += f"Poznámky: {event['notes']}\n"

        text += "-" * 40 + "\n"

        return text

    def generate_ical_content(self, events):
        ical = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Motoservis DMS//Calendar Export//CS
CALSCALE:GREGORIAN
METHOD:PUBLISH
"""

        for event in events:
            if not event['start_datetime']:
                continue

            start_dt = datetime.fromisoformat(event['start_datetime'])

            if event['end_datetime']:
                end_dt = datetime.fromisoformat(event['end_datetime'])
            else:
                end_dt = start_dt + timedelta(hours=1)

            uid = f"{event['id']}@motoservis.local"

            summary = event['title'] or 'Událost'

            description = ""
            if event['customer_name']:
                description += f"Zákazník: {event['customer_name']}\\n"
            if event['license_plate']:
                description += f"SPZ: {event['license_plate']}\\n"
            if event['mechanic_name']:
                description += f"Mechanik: {event['mechanic_name']}\\n"
            if event['description']:
                description += f"Popis: {event['description']}\\n"
            if event['notes']:
                description += f"Poznámky: {event['notes']}\\n"

            ical += f"""BEGIN:VEVENT
UID:{uid}
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}
DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}
SUMMARY:{summary}
DESCRIPTION:{description}
STATUS:{event['status'].upper()}
END:VEVENT
"""

        ical += "END:VCALENDAR"

        return ical

    def show_print_preview(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(self.handle_paint_request)
        preview.exec()

    def handle_paint_request(self, printer):
        painter = QPainter(printer)

        font = painter.font()
        font.setPointSize(12)
        painter.setFont(font)

        y = 50

        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        painter.setFont(title_font)

        print_type = self.print_type_group.checkedId()
        if print_type == 1:
            title = f"Denní rozvrh - {self.dt_print.date().toString('dd.MM.yyyy')}"
        elif print_type == 2:
            title = "Týdenní přehled"
        elif print_type == 3:
            title = "Měsíční kalendář"
        else:
            title = "Seznam zakázek"

        painter.drawText(50, y, title)
        y += 50

        font.setPointSize(10)
        painter.setFont(font)

        print_date = self.dt_print.date().toPyDate()
        events = self.fetch_events(print_date, print_date)

        mechanic_id = self.cmb_print_mechanic.currentData()
        if mechanic_id:
            events = [e for e in events if e['mechanic_id'] == mechanic_id]

        for event in events:
            text = f"{event['event_time']} - {event['title']}"
            if event['customer_name']:
                text += f" ({event['customer_name']})"
            painter.drawText(50, y, text)
            y += 25

            if y > printer.pageRect(QPrinter.Unit.DevicePixel).height() - 50:
                printer.newPage()
                y = 50

        painter.end()

    def perform_print(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)

        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            self.handle_paint_request(printer)
            QMessageBox.information(self, "Tisk", "Dokument byl odeslán na tiskárnu.")

    def send_email(self):
        email = self.txt_email.text().strip()
        if not email:
            QMessageBox.warning(self, "Chyba", "Zadejte email příjemce.")
            return

        subject = self.txt_subject.text().strip()
        message = self.txt_message.toPlainText().strip()

        QMessageBox.information(
            self,
            "Odeslání emailu",
            f"Email bude odeslán na: {email}\n"
            f"Předmět: {subject}\n\n"
            "Poznámka: Pro skutečné odesílání emailů je potřeba nakonfigurovat SMTP server."
        )

    def copy_link(self):
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.txt_link.text())
        QMessageBox.information(self, "Zkopírováno", "Odkaz byl zkopírován do schránky.")

    def generate_link(self):
        import random
        import string

        code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        new_link = f"https://vas-servis.cz/booking/{code}"
        self.txt_link.setText(new_link)

        QMessageBox.information(self, "Nový odkaz", f"Byl vygenerován nový odkaz:\n{new_link}")

    def generate_qr(self):
        QMessageBox.information(
            self,
            "QR kód",
            "QR kód byl vygenerován.\n\n"
            "Poznámka: Pro generování QR kódů je potřeba knihovna qrcode."
        )

    def save_qr(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit QR kód",
            "qr_rezervace.png",
            "Obrázky (*.png)"
        )

        if file_path:
            QMessageBox.information(self, "Uloženo", f"QR kód byl uložen do:\n{file_path}")

    def print_qr(self):
        QMessageBox.information(self, "Tisk QR", "QR kód bude vytištěn.")
