# customer_communication.py
# -*- coding: utf-8 -*-
"""
Widget pro historii komunikace se zákazníkem
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QScrollArea, QTextEdit, QLineEdit,
    QMessageBox, QDialog, QFormLayout, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor, QDesktopServices
from PyQt6.QtCore import QUrl
import config
from database_manager import db
from datetime import datetime


class CustomerCommunicationWidget(QWidget):
    """Widget pro správu komunikace se zákazníkem"""

    communication_added = pyqtSignal()

    def __init__(self, customer_id):
        super().__init__()
        self.customer_id = customer_id
        self.customer_email = ""
        self.customer_phone = ""
        self.init_ui()
        self.load_customer_info()
        self.load_communication()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Hlavička
        self.create_header(layout)

        # Filtry
        self.create_filters(layout)

        # Timeline komunikace
        self.create_timeline(layout)

        # Šablony
        self.create_templates_section(layout)

        self.set_styles()

    def create_header(self, parent_layout):
        """Vytvoření hlavičky"""
        header = QHBoxLayout()

        title = QLabel("📧 Historie komunikace")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header.addWidget(title)

        header.addStretch()

        btn_email = QPushButton("📧 Nový email")
        btn_email.setObjectName("btnPrimary")
        btn_email.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_email.clicked.connect(self.send_email)
        header.addWidget(btn_email)

        btn_sms = QPushButton("📱 Nová SMS")
        btn_sms.setObjectName("btnPrimary")
        btn_sms.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_sms.clicked.connect(self.send_sms)
        header.addWidget(btn_sms)

        btn_note = QPushButton("📝 Poznámka")
        btn_note.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_note.clicked.connect(self.add_note)
        header.addWidget(btn_note)

        btn_refresh = QPushButton("🔄")
        btn_refresh.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_refresh.clicked.connect(self.load_communication)
        header.addWidget(btn_refresh)

        parent_layout.addLayout(header)

    def create_filters(self, parent_layout):
        """Vytvoření filtrů"""
        filters_frame = QFrame()
        filters_frame.setObjectName("filtersFrame")
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setSpacing(10)

        # Typ komunikace
        filters_layout.addWidget(QLabel("Typ:"))
        self.cb_type = QComboBox()
        self.cb_type.addItems(["Vše", "Email", "SMS", "Telefon", "Osobně"])
        self.cb_type.currentTextChanged.connect(self.filter_communication)
        filters_layout.addWidget(self.cb_type)

        # Období
        filters_layout.addWidget(QLabel("Období:"))
        self.cb_period = QComboBox()
        self.cb_period.addItems(["Vše", "Poslední měsíc", "Poslední 3 měsíce", "Poslední rok"])
        self.cb_period.currentTextChanged.connect(self.filter_communication)
        filters_layout.addWidget(self.cb_period)

        filters_layout.addStretch()

        # Statistiky
        self.lbl_stats = QLabel("Celkem: 0 záznamů")
        self.lbl_stats.setStyleSheet("color: #7f8c8d;")
        filters_layout.addWidget(self.lbl_stats)

        parent_layout.addWidget(filters_frame)

    def create_timeline(self, parent_layout):
        """Vytvoření timeline komunikace"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("timelineScroll")

        self.timeline_widget = QWidget()
        self.timeline_layout = QVBoxLayout(self.timeline_widget)
        self.timeline_layout.setSpacing(10)
        self.timeline_layout.setContentsMargins(10, 10, 10, 10)

        # Placeholder
        placeholder = QLabel("Žádná komunikace k zobrazení")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #7f8c8d; padding: 50px;")
        self.timeline_layout.addWidget(placeholder)

        self.timeline_layout.addStretch()
        scroll.setWidget(self.timeline_widget)
        parent_layout.addWidget(scroll, 1)

    def create_templates_section(self, parent_layout):
        """Vytvoření sekce šablon"""
        templates_group = QGroupBox("📋 Rychlé šablony")
        templates_layout = QHBoxLayout(templates_group)
        templates_layout.setSpacing(10)

        templates = [
            ("Připomínka STK", "stk_reminder"),
            ("Potvrzení zakázky", "order_confirm"),
            ("Faktura", "invoice"),
            ("Nabídka servisu", "service_offer")
        ]

        for name, template_id in templates:
            btn = QPushButton(name)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(lambda checked, t=template_id: self.use_template(t))
            templates_layout.addWidget(btn)

        templates_layout.addStretch()
        parent_layout.addWidget(templates_group)

    def load_customer_info(self):
        """Načtení kontaktních údajů zákazníka"""
        try:
            customer = db.fetch_one(
                "SELECT email, phone FROM customers WHERE id = ?",
                (self.customer_id,)
            )
            if customer:
                self.customer_email = customer[0] or ""
                self.customer_phone = customer[1] or ""
        except Exception as e:
            print(f"Chyba při načítání kontaktů: {e}")

    def load_communication(self):
        """Načtení historie komunikace"""
        try:
            query = """
                SELECT
                    id,
                    comm_type,
                    subject,
                    content,
                    created_at,
                    direction,
                    status,
                    created_by
                FROM customer_communications
                WHERE customer_id = ?
                ORDER BY created_at DESC
            """

            communications = db.fetch_all(query, (self.customer_id,))
            self.all_communications = communications if communications else []
            self.populate_timeline(self.all_communications)
            self.update_stats(len(self.all_communications))

        except Exception as e:
            print(f"Chyba při načítání komunikace: {e}")
            self.all_communications = []
            self.populate_timeline([])

    def populate_timeline(self, communications):
        """Naplnění timeline"""
        # Vyčistit timeline
        while self.timeline_layout.count() > 0:
            item = self.timeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not communications:
            placeholder = QLabel("Žádná komunikace k zobrazení")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: #7f8c8d; padding: 50px;")
            self.timeline_layout.addWidget(placeholder)
        else:
            for comm in communications:
                card = self.create_communication_card(comm)
                self.timeline_layout.addWidget(card)

        self.timeline_layout.addStretch()

    def create_communication_card(self, comm):
        """Vytvoření karty komunikace"""
        card = QFrame()
        card.setObjectName("commCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)
        card_layout.setSpacing(8)

        # Hlavička karty
        header_layout = QHBoxLayout()

        # Ikona typu
        type_icons = {
            "Email": "📧",
            "SMS": "📱",
            "Telefon": "📞",
            "Osobně": "👤",
            "Poznámka": "📝"
        }
        comm_type = comm[1] or "Poznámka"
        icon = type_icons.get(comm_type, "📝")

        type_label = QLabel(f"{icon} {comm_type}")
        type_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(type_label)

        # Směr
        direction = comm[5] or "Odchozí"
        direction_label = QLabel(f"({direction})")
        direction_label.setStyleSheet("color: #7f8c8d;")
        header_layout.addWidget(direction_label)

        header_layout.addStretch()

        # Datum a čas
        date_str = comm[4] or ""
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str)
                date_str = dt.strftime("%d.%m.%Y %H:%M")
            except:
                pass

        date_label = QLabel(date_str)
        date_label.setStyleSheet("color: #95a5a6; font-size: 12px;")
        header_layout.addWidget(date_label)

        card_layout.addLayout(header_layout)

        # Předmět
        subject = comm[2] or ""
        if subject:
            subject_label = QLabel(f"<b>Předmět:</b> {subject}")
            subject_label.setWordWrap(True)
            card_layout.addWidget(subject_label)

        # Obsah (zkráceně)
        content = comm[3] or ""
        if len(content) > 200:
            content = content[:200] + "..."

        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setStyleSheet("color: #2c3e50;")
        card_layout.addWidget(content_label)

        # Stav
        status = comm[6] or ""
        if status:
            status_colors = {
                "Odesláno": "#3498db",
                "Doručeno": "#27ae60",
                "Přečteno": "#27ae60",
                "Chyba": "#e74c3c"
            }
            status_color = status_colors.get(status, "#95a5a6")
            status_label = QLabel(f"Stav: {status}")
            status_label.setStyleSheet(f"color: {status_color}; font-size: 11px;")
            card_layout.addWidget(status_label)

        # Autor
        created_by = comm[7] or ""
        if created_by:
            author_label = QLabel(f"Vytvořil: {created_by}")
            author_label.setStyleSheet("color: #95a5a6; font-size: 11px;")
            card_layout.addWidget(author_label)

        card.setStyleSheet("""
            #commCard {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                border-left: 4px solid #3498db;
            }
            #commCard:hover {
                border-left: 4px solid #2980b9;
                background-color: #f8f9fa;
            }
        """)

        return card

    def filter_communication(self):
        """Filtrování komunikace"""
        comm_type = self.cb_type.currentText()
        period = self.cb_period.currentText()

        filtered = self.all_communications

        # Filtr typu
        if comm_type != "Vše":
            filtered = [c for c in filtered if c[1] == comm_type]

        # Filtr období (zjednodušený)
        # V produkci by bylo potřeba implementovat správné filtrování podle data

        self.populate_timeline(filtered)
        self.update_stats(len(filtered))

    def update_stats(self, count):
        """Aktualizace statistik"""
        self.lbl_stats.setText(f"Celkem: {count} záznamů")

    def send_email(self):
        """Odeslání emailu"""
        dialog = EmailDialog(self.customer_email, self)
        if dialog.exec():
            email_data = dialog.get_data()
            self.save_communication("Email", email_data["subject"], email_data["content"], "Odchozí", "Odesláno")

            # Otevřít emailový klient
            if self.customer_email:
                QDesktopServices.openUrl(QUrl(f"mailto:{self.customer_email}?subject={email_data['subject']}&body={email_data['content']}"))

            QMessageBox.information(self, "Email", "Email byl připraven k odeslání")
            self.load_communication()

    def send_sms(self):
        """Odeslání SMS"""
        dialog = SMSDialog(self.customer_phone, self)
        if dialog.exec():
            sms_data = dialog.get_data()
            self.save_communication("SMS", "", sms_data["content"], "Odchozí", "Odesláno")
            QMessageBox.information(self, "SMS", f"SMS byla odeslána na {self.customer_phone}")
            self.load_communication()

    def add_note(self):
        """Přidání poznámky"""
        dialog = NoteDialog(self)
        if dialog.exec():
            note_data = dialog.get_data()
            self.save_communication("Poznámka", note_data["subject"], note_data["content"], "Interní", "")
            QMessageBox.information(self, "Poznámka", "Poznámka byla přidána")
            self.load_communication()

    def save_communication(self, comm_type, subject, content, direction, status):
        """Uložení komunikace do databáze"""
        try:
            from utils_auth import get_current_username
            username = get_current_username() or "Systém"

            db.execute(
                """INSERT INTO customer_communications
                   (customer_id, comm_type, subject, content, direction, status, created_by, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (self.customer_id, comm_type, subject, content, direction, status, username, datetime.now().isoformat())
            )
            self.communication_added.emit()
        except Exception as e:
            print(f"Chyba při ukládání komunikace: {e}")

    def use_template(self, template_id):
        """Použití šablony"""
        templates = {
            "stk_reminder": {
                "subject": "Připomínka STK",
                "content": "Dobrý den,\n\nrádi bychom Vám připomněli blížící se konec platnosti STK Vašeho vozidla.\n\nS pozdravem"
            },
            "order_confirm": {
                "subject": "Potvrzení zakázky",
                "content": "Dobrý den,\n\npotvrzujeme přijetí Vaší zakázky.\n\nS pozdravem"
            },
            "invoice": {
                "subject": "Faktura",
                "content": "Dobrý den,\n\nv příloze zasíláme fakturu za provedené služby.\n\nS pozdravem"
            },
            "service_offer": {
                "subject": "Nabídka servisu",
                "content": "Dobrý den,\n\nrádi bychom Vám nabídli pravidelný servis Vašeho vozidla.\n\nS pozdravem"
            }
        }

        template = templates.get(template_id)
        if template:
            dialog = EmailDialog(self.customer_email, self, template["subject"], template["content"])
            if dialog.exec():
                email_data = dialog.get_data()
                self.save_communication("Email", email_data["subject"], email_data["content"], "Odchozí", "Odesláno")
                self.load_communication()

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet(f"""
            #filtersFrame {{
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 10px;
            }}
            #timelineScroll {{
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            #btnPrimary {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }}
            #btnPrimary:hover {{
                background-color: #2980b9;
            }}
            QPushButton {{
                padding: 6px 12px;
                border-radius: 4px;
                border: 1px solid #ddd;
            }}
            QPushButton:hover {{
                background-color: #e0e0e0;
            }}
            QComboBox {{
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-width: 120px;
            }}
        """)


class EmailDialog(QDialog):
    """Dialog pro odeslání emailu"""

    def __init__(self, email, parent=None, subject="", content=""):
        super().__init__(parent)
        self.email = email
        self.default_subject = subject
        self.default_content = content
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("Nový email")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        # Příjemce
        self.le_to = QLineEdit(self.email)
        form_layout.addRow("Komu:", self.le_to)

        # Předmět
        self.le_subject = QLineEdit(self.default_subject)
        form_layout.addRow("Předmět:", self.le_subject)

        layout.addLayout(form_layout)

        # Obsah
        layout.addWidget(QLabel("Zpráva:"))
        self.te_content = QTextEdit()
        self.te_content.setPlainText(self.default_content)
        layout.addWidget(self.te_content)

        # Tlačítka
        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_send = QPushButton("📧 Odeslat")
        btn_send.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; font-weight: bold;")
        btn_send.clicked.connect(self.accept)
        buttons.addWidget(btn_send)

        layout.addLayout(buttons)

    def get_data(self):
        """Získání dat"""
        return {
            "to": self.le_to.text(),
            "subject": self.le_subject.text(),
            "content": self.te_content.toPlainText()
        }


class SMSDialog(QDialog):
    """Dialog pro odeslání SMS"""

    def __init__(self, phone, parent=None):
        super().__init__(parent)
        self.phone = phone
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("Nová SMS")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)

        # Příjemce
        layout.addWidget(QLabel(f"Příjemce: {self.phone}"))

        # Obsah
        layout.addWidget(QLabel("Zpráva (max 160 znaků):"))
        self.te_content = QTextEdit()
        self.te_content.setMaximumHeight(100)
        self.te_content.textChanged.connect(self.update_char_count)
        layout.addWidget(self.te_content)

        self.lbl_chars = QLabel("0/160 znaků")
        layout.addWidget(self.lbl_chars)

        # Tlačítka
        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_send = QPushButton("📱 Odeslat")
        btn_send.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; font-weight: bold;")
        btn_send.clicked.connect(self.accept)
        buttons.addWidget(btn_send)

        layout.addLayout(buttons)

    def update_char_count(self):
        """Aktualizace počtu znaků"""
        count = len(self.te_content.toPlainText())
        self.lbl_chars.setText(f"{count}/160 znaků")
        if count > 160:
            self.lbl_chars.setStyleSheet("color: #e74c3c;")
        else:
            self.lbl_chars.setStyleSheet("color: #7f8c8d;")

    def get_data(self):
        """Získání dat"""
        return {
            "phone": self.phone,
            "content": self.te_content.toPlainText()[:160]
        }


class NoteDialog(QDialog):
    """Dialog pro přidání poznámky"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("Nová poznámka")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        # Předmět
        self.le_subject = QLineEdit()
        self.le_subject.setPlaceholderText("Např. Telefonický hovor, Osobní schůzka...")
        form_layout.addRow("Typ/Předmět:", self.le_subject)

        layout.addLayout(form_layout)

        # Obsah
        layout.addWidget(QLabel("Poznámka:"))
        self.te_content = QTextEdit()
        self.te_content.setPlaceholderText("Obsah poznámky...")
        layout.addWidget(self.te_content)

        # Tlačítka
        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Uložit")
        btn_save.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; font-weight: bold;")
        btn_save.clicked.connect(self.accept)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

    def get_data(self):
        """Získání dat"""
        return {
            "subject": self.le_subject.text(),
            "content": self.te_content.toPlainText()
        }
