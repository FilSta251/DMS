# -*- coding: utf-8 -*-
"""
Modul Administrativa - Dialogy, widgety a komponenty (PRODUKČNÍ VERZE)
Pomocné komponenty pro administrativní modul
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QFrame,
                             QComboBox, QLineEdit, QDateEdit, QHeaderView,
                             QMessageBox, QDialog, QFormLayout, QTextEdit,
                             QSpinBox, QDoubleSpinBox, QFileDialog, QCheckBox,
                             QGroupBox, QTabWidget, QScrollArea, QProgressBar,
                             QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QIcon, QPainter
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
from datetime import datetime, timedelta, date
from pathlib import Path
import config
from database_manager import db


# =====================================================
# DIALOGY
# =====================================================

class QuickInvoiceDialog(QDialog):
    """Dialog pro rychlé vytvoření faktury ze zakázky"""

    invoice_created = pyqtSignal(int)  # ID vytvořené faktury

    def __init__(self, parent, order_id):
        super().__init__(parent)
        self.order_id = order_id
        self.order_data = None

        self.setWindowTitle("Rychlé vytvoření faktury")
        self.setMinimumWidth(600)

        self.init_ui()
        self.load_order()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # Info o zakázce
        self.order_info_label = QLabel("")
        self.order_info_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                padding: 15px;
                border-radius: 8px;
                font-size: 11pt;
            }
        """)
        layout.addWidget(self.order_info_label)

        # Formulář
        form_layout = QFormLayout()

        # Číslo faktury
        number_layout = QHBoxLayout()
        self.invoice_number = QLineEdit()
        number_layout.addWidget(self.invoice_number)

        auto_checkbox = QCheckBox("Automatické")
        auto_checkbox.setChecked(True)
        auto_checkbox.stateChanged.connect(lambda state: self.invoice_number.setEnabled(state != Qt.CheckState.Checked.value))
        number_layout.addWidget(auto_checkbox)

        form_layout.addRow("Číslo faktury:", number_layout)

        # Datum vystavení
        self.issue_date = QDateEdit()
        self.issue_date.setDate(QDate.currentDate())
        self.issue_date.setCalendarPopup(True)
        self.issue_date.setDisplayFormat("dd.MM.yyyy")
        self.issue_date.dateChanged.connect(self.update_due_date)
        form_layout.addRow("Datum vystavení:", self.issue_date)

        # Datum splatnosti
        self.due_date = QDateEdit()
        self.due_date.setDate(QDate.currentDate().addDays(14))
        self.due_date.setCalendarPopup(True)
        self.due_date.setDisplayFormat("dd.MM.yyyy")
        form_layout.addRow("Datum splatnosti:", self.due_date)

        # Způsob platby
        self.payment_method = QComboBox()
        self.payment_method.addItems([
            "Bankovní převod",
            "Hotovost",
            "Karta"
        ])
        form_layout.addRow("Způsob platby:", self.payment_method)

        # Poznámka
        self.note = QTextEdit()
        self.note.setMaximumHeight(80)
        self.note.setPlaceholderText("Poznámka k faktuře...")
        form_layout.addRow("Poznámka:", self.note)

        layout.addLayout(form_layout)

        # Položky
        items_group = QGroupBox("Položky faktury")
        items_layout = QVBoxLayout(items_group)

        info_label = QLabel("📦 Všechny položky ze zakázky budou automaticky přeneseny na fakturu.")
        info_label.setWordWrap(True)
        items_layout.addWidget(info_label)

        self.items_label = QLabel("")
        items_layout.addWidget(self.items_label)

        layout.addWidget(items_group)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        create_btn = QPushButton("💾 Vytvořit fakturu")
        create_btn.clicked.connect(self.create_invoice)
        create_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 10px 30px;
                font-weight: bold;
            }}
        """)
        buttons_layout.addWidget(create_btn)

        layout.addLayout(buttons_layout)

    def load_order(self):
        """Načtení zakázky"""
        try:
            query = """
                SELECT o.*, c.first_name, c.last_name, c.company
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                WHERE o.id = ?
            """
            self.order_data = db.fetch_one(query, (self.order_id,))

            if not self.order_data:
                QMessageBox.critical(self, "Chyba", "Zakázka nebyla nalezena.")
                self.reject()
                return

            # Aktualizovat info
            customer_name = self.order_data["company"] or f"{self.order_data['first_name']} {self.order_data['last_name']}"
            info_text = f"""
            <b>Zakázka:</b> {self.order_data['order_number']}<br>
            <b>Zákazník:</b> {customer_name}<br>
            <b>Celková cena:</b> {self.order_data['total_price']:,.2f} Kč
            """.replace(",", " ")
            self.order_info_label.setText(info_text)

            # Načíst položky
            query_items = "SELECT * FROM order_items WHERE order_id = ?"
            items = db.fetch_all(query_items, (self.order_id,))

            items_text = f"<b>Počet položek:</b> {len(items)}"
            self.items_label.setText(items_text)

            # Nastavit automatické číslo faktury
            next_number = db.get_next_invoice_number("issued")
            self.invoice_number.setText(next_number)
            self.invoice_number.setEnabled(False)

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst zakázku:\n{e}")
            self.reject()

    def update_due_date(self):
        """Aktualizace data splatnosti"""
        query = "SELECT setting_value FROM admin_settings WHERE setting_key = 'default_due_days'"
        result = db.fetch_one(query)
        due_days = int(result[0]) if result else 14

        new_due_date = self.issue_date.date().addDays(due_days)
        self.due_date.setDate(new_due_date)

    def create_invoice(self):
        """Vytvoření faktury"""
        try:
            # Validace
            if not self.invoice_number.text().strip():
                QMessageBox.warning(self, "Chyba", "Vyplňte číslo faktury.")
                return

            # Načíst položky zakázky
            query_items = """
                SELECT item_name, quantity, unit, unit_price
                FROM order_items
                WHERE order_id = ?
            """
            order_items = db.fetch_all(query_items, (self.order_id,))

            if not order_items:
                QMessageBox.warning(self, "Chyba", "Zakázka neobsahuje žádné položky.")
                return

            # Vypočítat součty
            total_without_vat = 0
            total_vat = 0

            for item in order_items:
                item_total = item["quantity"] * item["unit_price"]
                item_vat = item_total * 0.21  # 21% DPH
                total_without_vat += item_total
                total_vat += item_vat

            total_with_vat = total_without_vat + total_vat

            # Vytvořit fakturu
            invoice_query = """
                INSERT INTO invoices (
                    invoice_number, invoice_type, customer_id, order_id,
                    issue_date, due_date, tax_date, payment_method,
                    note, status, total_without_vat, total_vat, total_with_vat,
                    paid_amount, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            db.execute_query(invoice_query, (
                self.invoice_number.text().strip(),
                "issued",
                self.order_data["customer_id"],
                self.order_id,
                self.issue_date.date().toString("yyyy-MM-dd"),
                self.due_date.date().toString("yyyy-MM-dd"),
                self.issue_date.date().toString("yyyy-MM-dd"),
                self.payment_method.currentText(),
                self.note.toPlainText().strip() or None,
                "unpaid",
                total_without_vat,
                total_vat,
                total_with_vat,
                0,
                1  # TODO: ID přihlášeného uživatele
            ))

            invoice_id = db.cursor.lastrowid

            # Vytvořit položky faktury
            for item in order_items:
                item_total_without_vat = item["quantity"] * item["unit_price"]
                item_vat = item_total_without_vat * 0.21
                item_total_with_vat = item_total_without_vat + item_vat

                items_query = """
                    INSERT INTO invoice_items (
                        invoice_id, item_name, quantity, unit,
                        price_per_unit, vat_rate, total_without_vat,
                        total_vat, total_with_vat
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                db.execute_query(items_query, (
                    invoice_id,
                    item["item_name"],
                    item["quantity"],
                    item["unit"],
                    item["unit_price"],
                    21,
                    item_total_without_vat,
                    item_vat,
                    item_total_with_vat
                ))

            # Aktualizovat zakázku
            update_order = "UPDATE orders SET invoiced = 1 WHERE id = ?"
            db.execute_query(update_order, (self.order_id,))

            QMessageBox.information(
                self,
                "Úspěch",
                f"Faktura {self.invoice_number.text()} byla vytvořena."
            )

            self.invoice_created.emit(invoice_id)
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se vytvořit fakturu:\n{e}")


class ReminderDialog(QDialog):
    """Dialog pro vytvoření upomínky"""

    def __init__(self, parent, invoice_id):
        super().__init__(parent)
        self.invoice_id = invoice_id
        self.invoice_data = None

        self.setWindowTitle("Vytvoření upomínky")
        self.setMinimumWidth(500)

        self.init_ui()
        self.load_invoice()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # Info o faktuře
        self.invoice_info_label = QLabel("")
        self.invoice_info_label.setStyleSheet("""
            QLabel {
                background-color: #fff3cd;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #ffc107;
            }
        """)
        layout.addWidget(self.invoice_info_label)

        # Formulář
        form_layout = QFormLayout()

        # Stupeň upomínky
        self.reminder_level = QComboBox()
        self.reminder_level.addItem("1. upomínka (do 14 dní po splatnosti)", 1)
        self.reminder_level.addItem("2. upomínka (15-30 dní po splatnosti)", 2)
        self.reminder_level.addItem("3. upomínka (více než 30 dní po splatnosti)", 3)
        self.reminder_level.currentIndexChanged.connect(self.update_text)
        form_layout.addRow("Stupeň upomínky:", self.reminder_level)

        # Text upomínky
        self.reminder_text = QTextEdit()
        self.reminder_text.setMinimumHeight(200)
        form_layout.addRow("Text upomínky:", self.reminder_text)

        # Poplatek za upomínku
        self.fee_checkbox = QCheckBox("Připočítat poplatek za upomínku")
        form_layout.addRow("", self.fee_checkbox)

        self.fee_amount = QDoubleSpinBox()
        self.fee_amount.setRange(0, 10000)
        self.fee_amount.setValue(200)
        self.fee_amount.setSuffix(" Kč")
        self.fee_amount.setEnabled(False)
        self.fee_checkbox.stateChanged.connect(lambda state: self.fee_amount.setEnabled(state == Qt.CheckState.Checked.value))
        form_layout.addRow("Výše poplatku:", self.fee_amount)

        layout.addLayout(form_layout)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        preview_btn = QPushButton("👁️ Náhled")
        preview_btn.clicked.connect(self.preview_reminder)
        buttons_layout.addWidget(preview_btn)

        send_btn = QPushButton("📧 Vygenerovat a odeslat")
        send_btn.clicked.connect(self.send_reminder)
        send_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 20px;")
        buttons_layout.addWidget(send_btn)

        layout.addLayout(buttons_layout)

    def load_invoice(self):
        """Načtení faktury"""
        try:
            query = """
                SELECT i.*, c.first_name, c.last_name, c.company, c.email
                FROM invoices i
                LEFT JOIN customers c ON i.customer_id = c.id
                WHERE i.id = ?
            """
            self.invoice_data = db.fetch_one(query, (self.invoice_id,))

            if not self.invoice_data:
                QMessageBox.critical(self, "Chyba", "Faktura nebyla nalezena.")
                self.reject()
                return

            # Vypočítat dny po splatnosti
            due_date = datetime.fromisoformat(self.invoice_data["due_date"])
            days_overdue = (datetime.now() - due_date).days

            # Aktualizovat info
            customer_name = self.invoice_data["company"] or f"{self.invoice_data['first_name']} {self.invoice_data['last_name']}"
            remaining = self.invoice_data["total_with_vat"] - self.invoice_data["paid_amount"]

            info_text = f"""
            <b>Faktura:</b> {self.invoice_data['invoice_number']}<br>
            <b>Zákazník:</b> {customer_name}<br>
            <b>Datum splatnosti:</b> {due_date.strftime('%d.%m.%Y')}<br>
            <b>Dní po splatnosti:</b> {days_overdue}<br>
            <b>Dlužná částka:</b> {remaining:,.2f} Kč
            """.replace(",", " ")
            self.invoice_info_label.setText(info_text)

            # Nastavit správný stupeň upomínky
            if days_overdue <= 14:
                self.reminder_level.setCurrentIndex(0)
            elif days_overdue <= 30:
                self.reminder_level.setCurrentIndex(1)
            else:
                self.reminder_level.setCurrentIndex(2)

            # Vygenerovat text
            self.update_text()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst fakturu:\n{e}")
            self.reject()

    def update_text(self):
        """Aktualizace textu upomínky"""
        if not self.invoice_data:
            return

        level = self.reminder_level.currentData()
        customer_name = self.invoice_data["company"] or f"{self.invoice_data['first_name']} {self.invoice_data['last_name']}"
        remaining = self.invoice_data["total_with_vat"] - self.invoice_data["paid_amount"]
        due_date = datetime.fromisoformat(self.invoice_data["due_date"]).strftime('%d.%m.%Y')

        if level == 1:
            text = f"""Vážený zákazníku / Vážená zákaznice,

dovolujeme si Vás upozornit, že faktura č. {self.invoice_data['invoice_number']} je po datu splatnosti {due_date}.

Dlužná částka: {remaining:,.2f} Kč

Prosíme o úhradu v nejbližších dnech. V případě, že jste již úhradu provedli, považujte tuto upomínku za bezpředmětnou.

S pozdravem
"""

        elif level == 2:
            text = f"""Vážený zákazníku / Vážená zákaznice,

s politováním Vás musíme upozornit, že faktura č. {self.invoice_data['invoice_number']} je po splatnosti již více než 14 dní (datum splatnosti: {due_date}).

Dlužná částka: {remaining:,.2f} Kč

Pokud nedojde k úhradě do 7 dnů, budeme nuceni přistoupit k dalším krokům.

S pozdravem
"""

        else:
            text = f"""Vážený zákazníku / Vážená zákaznice,

toto je poslední výzva k úhradě faktury č. {self.invoice_data['invoice_number']}, která je po splatnosti více než 30 dní (datum splatnosti: {due_date}).

Dlužná částka: {remaining:,.2f} Kč

Pokud nedojde k okamžité úhradě, budeme nuceni věc postoupit k vymáhání.

S pozdravem
"""

        self.reminder_text.setPlainText(text.replace(",", " "))

    def preview_reminder(self):
        """Náhled upomínky"""
        QMessageBox.information(
            self,
            "Náhled",
            "Funkce náhledu upomínky bude implementována.\n\n"
            "Zobrazí se PDF dokument s upomínkou."
        )

    def send_reminder(self):
        """Odeslání upomínky"""
        try:
            # Uložit záznam o upomínce
            query = """
                INSERT INTO reminders (
                    invoice_id, reminder_level, reminder_text,
                    fee_amount, sent_date, created_by
                ) VALUES (?, ?, ?, ?, ?, ?)
            """
            db.execute_query(query, (
                self.invoice_id,
                self.reminder_level.currentData(),
                self.reminder_text.toPlainText(),
                self.fee_amount.value() if self.fee_checkbox.isChecked() else 0,
                datetime.now().strftime("%Y-%m-%d"),
                1  # TODO: ID přihlášeného uživatele
            ))

            QMessageBox.information(
                self,
                "Úspěch",
                f"Upomínka {self.reminder_level.currentData()}. stupně byla vytvořena.\n\n"
                "V produkční verzi bude také odeslána emailem zákazníkovi."
            )

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se vytvořit upomínku:\n{e}")


class DocumentUploadDialog(QDialog):
    """Dialog pro upload dokumentu"""

    def __init__(self, parent, entity_type=None, entity_id=None):
        super().__init__(parent)
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.file_path = None

        self.setWindowTitle("Nahrát dokument")
        self.setMinimumWidth(500)

        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QFormLayout(self)

        # Soubor
        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setReadOnly(True)
        file_layout.addWidget(self.file_path_input)

        browse_btn = QPushButton("📁 Procházet")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)

        layout.addRow("Soubor:", file_layout)

        # Název
        self.name_input = QLineEdit()
        layout.addRow("Název:", self.name_input)

        # Typ
        self.type_combo = QComboBox()
        self.type_combo.addItem("Faktura", "invoice_attachment")
        self.type_combo.addItem("Smlouva", "contract")
        self.type_combo.addItem("Protokol", "protocol")
        self.type_combo.addItem("Ostatní", "other")
        layout.addRow("Typ:", self.type_combo)

        # Kategorie
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("Např: Daňové doklady")
        layout.addRow("Kategorie:", self.category_input)

        # Poznámka
        self.note_input = QTextEdit()
        self.note_input.setMaximumHeight(80)
        layout.addRow("Poznámka:", self.note_input)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        upload_btn = QPushButton("📤 Nahrát")
        upload_btn.clicked.connect(self.upload_document)
        upload_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 20px;")
        buttons_layout.addWidget(upload_btn)

        layout.addRow(buttons_layout)

    def browse_file(self):
        """Procházet soubory"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Vyberte soubor",
            "",
            "Všechny soubory (*.*)"
        )

        if file_path:
            self.file_path = file_path
            self.file_path_input.setText(file_path)

            # Automaticky vyplnit název
            if not self.name_input.text():
                self.name_input.setText(Path(file_path).name)

    def upload_document(self):
        """Upload dokumentu"""
        try:
            # Validace
            if not self.file_path:
                QMessageBox.warning(self, "Chyba", "Vyberte soubor.")
                return

            if not self.name_input.text().strip():
                QMessageBox.warning(self, "Chyba", "Vyplňte název dokumentu.")
                return

            # Zkopírovat soubor
            documents_dir = Path(config.DATA_DIR) / "documents"
            documents_dir.mkdir(parents=True, exist_ok=True)

            source_path = Path(self.file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_filename = f"{timestamp}_{source_path.name}"
            dest_path = documents_dir / dest_filename

            import shutil
            shutil.copy2(source_path, dest_path)

            # Uložit do databáze
            file_size = dest_path.stat().st_size

            query = """
                INSERT INTO documents (
                    document_type, document_name, file_path, category,
                    note, file_size, linked_entity_type, linked_entity_id,
                    uploaded_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            db.execute_query(query, (
                self.type_combo.currentData(),
                self.name_input.text().strip(),
                str(dest_path),
                self.category_input.text().strip() or None,
                self.note_input.toPlainText().strip() or None,
                file_size,
                self.entity_type,
                self.entity_id,
                1  # TODO: ID přihlášeného uživatele
            ))

            QMessageBox.information(self, "Úspěch", "Dokument byl nahrán.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se nahrát dokument:\n{e}")


class TaxReportDialog(QDialog):
    """Dialog pro generování daňového přehledu"""

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Generovat daňový přehled")
        self.setMinimumWidth(400)

        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QFormLayout(self)

        # Období
        period_label = QLabel("Období:")
        self.period_combo = QComboBox()
        self.period_combo.addItem("Tento měsíc", "current_month")
        self.period_combo.addItem("Minulý měsíc", "last_month")
        self.period_combo.addItem("Toto čtvrtletí", "current_quarter")
        self.period_combo.addItem("Minulé čtvrtletí", "last_quarter")
        self.period_combo.addItem("Tento rok", "current_year")
        self.period_combo.addItem("Vlastní", "custom")
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        layout.addRow(period_label, self.period_combo)

        # Vlastní období
        custom_widget = QWidget()
        custom_layout = QHBoxLayout(custom_widget)
        custom_layout.setContentsMargins(0, 0, 0, 0)

        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd.MM.yyyy")
        custom_layout.addWidget(QLabel("Od:"))
        custom_layout.addWidget(self.date_from)

        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd.MM.yyyy")
        custom_layout.addWidget(QLabel("Do:"))
        custom_layout.addWidget(self.date_to)

        self.custom_widget = custom_widget
        self.custom_widget.setVisible(False)
        layout.addRow("", self.custom_widget)

        # Formát
        self.format_combo = QComboBox()
        self.format_combo.addItem("📄 PDF", "pdf")
        self.format_combo.addItem("📊 Excel", "excel")
        self.format_combo.addItem("📑 XML", "xml")
        layout.addRow("Formát:", self.format_combo)

        # Zahrnout
        self.include_vat = QCheckBox("Zahrnout DPH přehled")
        self.include_vat.setChecked(True)
        layout.addRow("", self.include_vat)

        self.include_income = QCheckBox("Zahrnout přehled příjmů")
        self.include_income.setChecked(True)
        layout.addRow("", self.include_income)

        self.include_expenses = QCheckBox("Zahrnout přehled výdajů")
        self.include_expenses.setChecked(True)
        layout.addRow("", self.include_expenses)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        generate_btn = QPushButton("📊 Generovat")
        generate_btn.clicked.connect(self.generate_report)
        generate_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 20px;")
        buttons_layout.addWidget(generate_btn)

        layout.addRow(buttons_layout)

    def on_period_changed(self, text):
        """Změna období"""
        self.custom_widget.setVisible(text == "Vlastní")

    def generate_report(self):
        """Generování přehledu"""
        QMessageBox.information(
            self,
            "Generování",
            "Funkce generování daňového přehledu bude implementována.\n\n"
            "Přehled bude obsahovat:\n"
            "- DPH na výstupu a vstupu\n"
            "- Přehled příjmů a výdajů\n"
            "- Kontrolní součty"
        )
        self.accept()


# =====================================================
# WIDGETY
# =====================================================

class InvoiceCard(QFrame):
    """Karta faktury pro preview"""

    clicked = pyqtSignal(int)  # ID faktury

    def __init__(self, invoice_data):
        super().__init__()
        self.invoice_data = invoice_data
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
            QFrame:hover {
                border: 2px solid #3498db;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)

        # Hlavička
        header_layout = QHBoxLayout()

        # Číslo faktury
        number_label = QLabel(self.invoice_data["invoice_number"])
        number_font = QFont()
        number_font.setBold(True)
        number_font.setPointSize(12)
        number_label.setFont(number_font)
        header_layout.addWidget(number_label)

        header_layout.addStretch()

        # Status
        status_widget = PaymentStatus(self.invoice_data["status"])
        header_layout.addWidget(status_widget)

        layout.addLayout(header_layout)

        # Zákazník
        customer_name = self.invoice_data.get("customer_name", "Neznámý")
        customer_label = QLabel(f"👤 {customer_name}")
        layout.addWidget(customer_label)

        # Datum
        issue_date = datetime.fromisoformat(self.invoice_data["issue_date"]).strftime("%d.%m.%Y")
        due_date = datetime.fromisoformat(self.invoice_data["due_date"]).strftime("%d.%m.%Y")
        date_label = QLabel(f"📅 {issue_date} → {due_date}")
        date_label.setStyleSheet("color: #7f8c8d; font-size: 9pt;")
        layout.addWidget(date_label)

        # Částka
        amount_label = QLabel(f"{self.invoice_data['total_with_vat']:,.2f} Kč".replace(",", " "))
        amount_font = QFont()
        amount_font.setBold(True)
        amount_font.setPointSize(14)
        amount_label.setFont(amount_font)
        amount_label.setStyleSheet("color: #27ae60;")
        layout.addWidget(amount_label)

    def mousePressEvent(self, event):
        """Kliknutí na kartu"""
        self.clicked.emit(self.invoice_data["id"])


class PaymentStatus(QLabel):
    """Widget pro zobrazení statusu platby"""

    def __init__(self, status):
        super().__init__()
        self.set_status(status)

    def set_status(self, status):
        """Nastavení statusu"""
        status_config = {
            "paid": ("✅ Zaplaceno", config.COLOR_SUCCESS),
            "unpaid": ("⏳ Nezaplaceno", config.COLOR_WARNING),
            "partial": ("💳 Částečně", "#3498db"),
            "overdue": ("⚠️ Po splatnosti", config.COLOR_DANGER),
            "cancelled": ("❌ Stornováno", "#95a5a6")
        }

        text, color = status_config.get(status, ("❓ Neznámý", "#95a5a6"))

        self.setText(text)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 9pt;
            }}
        """)


class TaxCalculator(QWidget):
    """Kalkulátor DPH"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # Formulář
        form_layout = QFormLayout()

        # Částka
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 999999999)
        self.amount_input.setDecimals(2)
        self.amount_input.setSuffix(" Kč")
        self.amount_input.valueChanged.connect(self.calculate)
        form_layout.addRow("Částka:", self.amount_input)

        # Směr výpočtu
        self.direction = QComboBox()
        self.direction.addItem("Bez DPH → S DPH", "add")
        self.direction.addItem("S DPH → Bez DPH", "remove")
        self.direction.currentTextChanged.connect(self.calculate)
        form_layout.addRow("Směr:", self.direction)

        # Sazba DPH
        self.vat_rate = QComboBox()
        self.vat_rate.addItem("21%", 21)
        self.vat_rate.addItem("12%", 12)
        self.vat_rate.addItem("0%", 0)
        self.vat_rate.currentTextChanged.connect(self.calculate)
        form_layout.addRow("Sazba DPH:", self.vat_rate)

        layout.addLayout(form_layout)

        # Výsledek
        result_frame = QFrame()
        result_frame.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        result_layout = QFormLayout(result_frame)

        self.base_label = QLabel("0,00 Kč")
        result_layout.addRow("Základ:", self.base_label)

        self.vat_label = QLabel("0,00 Kč")
        result_layout.addRow("DPH:", self.vat_label)

        self.total_label = QLabel("0,00 Kč")
        total_font = QFont()
        total_font.setBold(True)
        self.total_label.setFont(total_font)
        result_layout.addRow("Celkem:", self.total_label)

        layout.addWidget(result_frame)

    def calculate(self):
        """Výpočet DPH"""
        amount = self.amount_input.value()
        rate = self.vat_rate.currentData()
        direction = self.direction.currentData()

        if direction == "add":
            # Bez DPH → S DPH
            base = amount
            vat = amount * (rate / 100)
            total = base + vat
        else:
            # S DPH → Bez DPH
            total = amount
            base = amount / (1 + rate / 100)
            vat = total - base

        self.base_label.setText(f"{base:,.2f} Kč".replace(",", " "))
        self.vat_label.setText(f"{vat:,.2f} Kč".replace(",", " "))
        self.total_label.setText(f"{total:,.2f} Kč".replace(",", " "))


class CashFlowWidget(QWidget):
    """Widget s grafem cash flow"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # Graf
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        layout.addWidget(self.chart_view)

    def load_data(self, date_from, date_to):
        """Načtení dat pro graf"""
        # TODO: Implementovat načtení dat a vytvoření grafu
        pass


class DebtorsList(QWidget):
    """Seznam dlužníků"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # Tabulka
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Zákazník",
            "Dluh",
            "Dní po splatnosti",
            "Akce"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def load_data(self):
        """Načtení dat"""
        try:
            query = """
                SELECT
                    c.first_name || ' ' || c.last_name as customer_name,
                    SUM(i.total_with_vat - i.paid_amount) as debt,
                    MAX(JULIANDAY(DATE('now')) - JULIANDAY(i.due_date)) as max_days_overdue
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                WHERE i.invoice_type = 'issued'
                  AND i.status IN ('unpaid', 'partial', 'overdue')
                  AND i.due_date < DATE('now')
                GROUP BY i.customer_id
                HAVING debt > 0
                ORDER BY max_days_overdue DESC, debt DESC
            """
            debtors = db.fetch_all(query)

            self.table.setRowCount(len(debtors))

            for row, debtor in enumerate(debtors):
                # Zákazník
                self.table.setItem(row, 0, QTableWidgetItem(debtor["customer_name"]))

                # Dluh
                debt_item = QTableWidgetItem(f"{debtor['debt']:,.2f} Kč".replace(",", " "))
                debt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                debt_item.setForeground(QColor(config.COLOR_DANGER))
                self.table.setItem(row, 1, debt_item)

                # Dny po splatnosti
                days = int(debtor["max_days_overdue"])
                days_item = QTableWidgetItem(str(days))
                days_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if days > 60:
                    days_item.setBackground(QColor(config.COLOR_DANGER))
                    days_item.setForeground(QColor("white"))
                elif days > 30:
                    days_item.setBackground(QColor(config.COLOR_WARNING))

                self.table.setItem(row, 2, days_item)

                # Akce
                action_btn = QPushButton("📧 Upomínka")
                self.table.setCellWidget(row, 3, action_btn)

        except Exception as e:
            print(f"Chyba při načítání dlužníků: {e}")


# =====================================================
# TABULKY
# =====================================================

class InvoiceTable(QTableWidget):
    """Tabulka faktur s filtry"""

    invoice_selected = pyqtSignal(int)  # ID faktury

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels([
            "Číslo faktury",
            "Zákazník",
            "Datum vystavení",
            "Datum splatnosti",
            "Částka",
            "Status",
            "Akce"
        ])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.currentItemChanged.connect(self.on_selection_changed)

    def load_data(self, filters=None):
        """Načtení dat"""
        # TODO: Implementovat načtení s filtry
        pass

    def on_selection_changed(self):
        """Změna výběru"""
        current_row = self.currentRow()
        if current_row >= 0:
            invoice_id = self.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            if invoice_id:
                self.invoice_selected.emit(invoice_id)


class PaymentTable(QTableWidget):
    """Tabulka plateb"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "Datum",
            "Číslo faktury",
            "Partner",
            "Částka",
            "Způsob platby",
            "Typ"
        ])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setAlternatingRowColors(True)


class DocumentsTable(QTableWidget):
    """Tabulka dokumentů"""

    document_selected = pyqtSignal(int)  # ID dokumentu

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels([
            "Název",
            "Typ",
            "Datum nahrání",
            "Velikost",
            "Akce"
        ])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
