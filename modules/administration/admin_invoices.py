# -*- coding: utf-8 -*-
"""
Modul Administrativa - Správa faktur (PRODUKČNÍ VERZE)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QFrame,
                             QComboBox, QLineEdit, QDateEdit, QHeaderView,
                             QMessageBox, QDialog, QFormLayout, QTextEdit,
                             QSpinBox, QDoubleSpinBox, QFileDialog, QCheckBox,
                             QGroupBox, QTabWidget, QScrollArea)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, timedelta, date
import config
from database_manager import db


class InvoicesWidget(QWidget):
    """Widget pro správu faktur"""

    invoice_changed = pyqtSignal()  # Signal pro refresh

    def __init__(self, invoice_type="issued"):
        """
        Args:
            invoice_type: "issued" (vydané) nebo "received" (přijaté)
        """
        super().__init__()
        self.invoice_type = invoice_type
        self.current_filters = {}
        self.init_ui()
        self.load_invoices()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Statistiky nahoře
        self.create_stats_panel(layout)

        # Filtry
        self.create_filters_panel(layout)

        # Tlačítka akcí
        self.create_action_buttons(layout)

        # Tabulka faktur
        self.create_invoices_table(layout)

    def create_stats_panel(self, parent_layout):
        """Panel s rychlými statistikami"""
        stats_frame = QFrame()
        stats_frame.setObjectName("statsFrame")
        stats_layout = QHBoxLayout(stats_frame)

        # Definice statistik
        stats = [
            ("💰 Celkem", "0 Kč", "total"),
            ("✅ Zaplaceno", "0 Kč", "paid"),
            ("⏳ Nezaplaceno", "0 Kč", "unpaid"),
            ("⚠️ Po splatnosti", "0 Kč", "overdue"),
        ]

        self.stat_labels = {}

        for title, value, key in stats:
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(15, 10, 15, 10)

            title_label = QLabel(title)
            title_font = QFont()
            title_font.setPointSize(10)
            title_label.setFont(title_font)
            title_label.setStyleSheet("color: #7f8c8d;")

            value_label = QLabel(value)
            value_font = QFont()
            value_font.setPointSize(16)
            value_font.setBold(True)
            value_label.setFont(value_font)

            self.stat_labels[key] = value_label

            stat_layout.addWidget(title_label)
            stat_layout.addWidget(value_label)

            stat_widget.setStyleSheet("""
                QWidget {
                    background-color: white;
                    border-radius: 8px;
                    border: 1px solid #e0e0e0;
                }
            """)

            stats_layout.addWidget(stat_widget)

        parent_layout.addWidget(stats_frame)

    def create_filters_panel(self, parent_layout):
        """Panel s filtry"""
        filters_frame = QFrame()
        filters_frame.setObjectName("filtersFrame")
        filters_layout = QHBoxLayout(filters_frame)

        # Filtr stavu
        status_label = QLabel("Stav:")
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "Všechny",
            "Nezaplacené",
            "Zaplacené",
            "Po splatnosti",
            "Částečně zaplacené"
        ])
        self.status_combo.currentTextChanged.connect(self.apply_filters)

        # Filtr období
        period_label = QLabel("Období:")
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "Tento měsíc",
            "Poslední 3 měsíce",
            "Tento rok",
            "Minulý rok",
            "Vlastní"
        ])
        self.period_combo.currentTextChanged.connect(self.on_period_changed)

        # Datum od
        date_from_label = QLabel("Od:")
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd.MM.yyyy")
        self.date_from.dateChanged.connect(self.apply_filters)

        # Datum do
        date_to_label = QLabel("Do:")
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd.MM.yyyy")
        self.date_to.dateChanged.connect(self.apply_filters)

        # Vyhledávání
        search_label = QLabel("Hledat:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Číslo faktury, zákazník...")
        self.search_input.textChanged.connect(self.apply_filters)

        # Přidání do layoutu
        filters_layout.addWidget(status_label)
        filters_layout.addWidget(self.status_combo)
        filters_layout.addSpacing(15)
        filters_layout.addWidget(period_label)
        filters_layout.addWidget(self.period_combo)
        filters_layout.addSpacing(15)
        filters_layout.addWidget(date_from_label)
        filters_layout.addWidget(self.date_from)
        filters_layout.addWidget(date_to_label)
        filters_layout.addWidget(self.date_to)
        filters_layout.addSpacing(15)
        filters_layout.addWidget(search_label)
        filters_layout.addWidget(self.search_input)
        filters_layout.addStretch()

        filters_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 10px;
                border: 1px solid #e0e0e0;
            }
        """)

        parent_layout.addWidget(filters_frame)

    def create_action_buttons(self, parent_layout):
        """Tlačítka akcí"""
        buttons_layout = QHBoxLayout()

        buttons = [
            ("➕ Nová faktura", self.new_invoice, config.COLOR_SUCCESS),
            ("📧 Odeslat email", self.send_email, config.COLOR_SECONDARY),
            ("🖨️ Tisk", self.print_invoice, config.COLOR_SECONDARY),
            ("📤 Export", self.export_invoices, config.COLOR_SECONDARY),
            ("💳 Zaznamenat platbu", self.record_payment, config.COLOR_WARNING),
            ("❌ Storno", self.cancel_invoice, config.COLOR_DANGER),
            ("📋 Dobropis", self.create_credit_note, config.COLOR_WARNING),
        ]

        for text, callback, color in buttons:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(callback)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    opacity: 0.9;
                }}
            """)
            buttons_layout.addWidget(btn)

        buttons_layout.addStretch()
        parent_layout.addLayout(buttons_layout)

    def create_invoices_table(self, parent_layout):
        """Tabulka s fakturami"""
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "Číslo faktury",
            "Zákazník/Dodavatel",
            "Datum vystavení",
            "Datum splatnosti",
            "Částka celkem",
            "Zaplaceno",
            "Zbývá",
            "Stav",
            "Zakázka"
        ])

        # Skrýt ID sloupec
        self.table.setColumnHidden(0, True)

        # Nastavení tabulky
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.open_invoice_detail)

        parent_layout.addWidget(self.table)

    def on_period_changed(self, period_text):
        """Změna předvoleného období"""
        today = QDate.currentDate()

        if period_text == "Tento měsíc":
            self.date_from.setDate(QDate(today.year(), today.month(), 1))
            self.date_to.setDate(today)
        elif period_text == "Poslední 3 měsíce":
            self.date_from.setDate(today.addMonths(-3))
            self.date_to.setDate(today)
        elif period_text == "Tento rok":
            self.date_from.setDate(QDate(today.year(), 1, 1))
            self.date_to.setDate(today)
        elif period_text == "Minulý rok":
            self.date_from.setDate(QDate(today.year() - 1, 1, 1))
            self.date_to.setDate(QDate(today.year() - 1, 12, 31))

        self.apply_filters()

    def load_invoices(self):
        """Načtení faktur z databáze"""
        try:
            query = """
                SELECT
                    i.id,
                    i.invoice_number,
                    CASE
                        WHEN i.invoice_type = 'issued' THEN
                            COALESCE(c.first_name || ' ' || c.last_name, c.company, i.supplier_name, 'Neznámý')
                        ELSE
                            COALESCE(i.supplier_name, 'Neznámý dodavatel')
                    END as partner_name,
                    i.issue_date,
                    i.due_date,
                    i.total_with_vat,
                    i.paid_amount,
                    (i.total_with_vat - i.paid_amount) as remaining,
                    i.status,
                    o.order_number
                FROM invoices i
                LEFT JOIN customers c ON i.customer_id = c.id
                LEFT JOIN orders o ON i.order_id = o.id
                WHERE i.invoice_type = ?
                ORDER BY i.issue_date DESC, i.invoice_number DESC
            """

            invoices = db.fetch_all(query, (self.invoice_type,))

            self.table.setRowCount(len(invoices))

            for row, invoice in enumerate(invoices):
                # ID (skrytý)
                self.table.setItem(row, 0, QTableWidgetItem(str(invoice["id"])))

                # Číslo faktury
                self.table.setItem(row, 1, QTableWidgetItem(invoice["invoice_number"]))

                # Zákazník/Dodavatel
                self.table.setItem(row, 2, QTableWidgetItem(invoice["partner_name"]))

                # Datum vystavení
                issue_date = datetime.fromisoformat(invoice["issue_date"]).strftime("%d.%m.%Y")
                self.table.setItem(row, 3, QTableWidgetItem(issue_date))

                # Datum splatnosti
                due_date = datetime.fromisoformat(invoice["due_date"]).strftime("%d.%m.%Y")
                self.table.setItem(row, 4, QTableWidgetItem(due_date))

                # Částka celkem
                total_item = QTableWidgetItem(f"{invoice['total_with_vat']:,.2f} Kč".replace(",", " "))
                total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 5, total_item)

                # Zaplaceno
                paid_item = QTableWidgetItem(f"{invoice['paid_amount']:,.2f} Kč".replace(",", " "))
                paid_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 6, paid_item)

                # Zbývá
                remaining_item = QTableWidgetItem(f"{invoice['remaining']:,.2f} Kč".replace(",", " "))
                remaining_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 7, remaining_item)

                # Stav - přepočítat podle skutečnosti
                actual_status = self.calculate_invoice_status(invoice)
                status_item = QTableWidgetItem(self.get_status_label(actual_status))
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Barevné rozlišení
                if actual_status == "paid":
                    status_item.setBackground(QColor(config.COLOR_SUCCESS))
                    status_item.setForeground(QColor("white"))
                elif actual_status == "overdue":
                    status_item.setBackground(QColor(config.COLOR_DANGER))
                    status_item.setForeground(QColor("white"))
                elif actual_status == "unpaid":
                    status_item.setBackground(QColor(config.COLOR_WARNING))
                    status_item.setForeground(QColor("white"))
                elif actual_status == "partial":
                    status_item.setBackground(QColor("#3498db"))
                    status_item.setForeground(QColor("white"))
                elif actual_status == "cancelled":
                    status_item.setBackground(QColor("#95a5a6"))
                    status_item.setForeground(QColor("white"))

                self.table.setItem(row, 8, status_item)

                # Zakázka
                order_text = invoice["order_number"] if invoice["order_number"] else "-"
                self.table.setItem(row, 9, QTableWidgetItem(order_text))

            # Aktualizace statistik
            self.update_statistics()

            # Aplikuj filtry
            self.apply_filters()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst faktury:\n{e}")

    def calculate_invoice_status(self, invoice):
        """Vypočítá aktuální stav faktury"""
        if invoice["status"] == "cancelled":
            return "cancelled"

        remaining = invoice["total_with_vat"] - invoice["paid_amount"]

        if remaining <= 0.01:  # Tolerance pro zaokrouhlení
            return "paid"
        elif invoice["paid_amount"] > 0:
            return "partial"
        else:
            # Zkontroluj splatnost
            due_date = datetime.fromisoformat(invoice["due_date"]).date()
            today = date.today()
            if due_date < today:
                return "overdue"
            else:
                return "unpaid"

    def get_status_label(self, status):
        """Vrátí popisek pro stav"""
        labels = {
            "paid": "Zaplaceno",
            "unpaid": "Nezaplaceno",
            "partial": "Částečně zaplaceno",
            "overdue": "Po splatnosti",
            "cancelled": "Stornováno"
        }
        return labels.get(status, status)

    def update_statistics(self):
        """Aktualizace statistik"""
        try:
            # Celkem
            query_total = """
                SELECT COALESCE(SUM(total_with_vat), 0) as total
                FROM invoices
                WHERE invoice_type = ? AND status != 'cancelled'
            """
            result = db.fetch_one(query_total, (self.invoice_type,))
            total = result["total"] if result else 0

            # Zaplaceno
            query_paid = """
                SELECT COALESCE(SUM(paid_amount), 0) as paid
                FROM invoices
                WHERE invoice_type = ? AND status != 'cancelled'
            """
            result = db.fetch_one(query_paid, (self.invoice_type,))
            paid = result["paid"] if result else 0

            # Nezaplaceno
            unpaid = total - paid

            # Po splatnosti
            query_overdue = """
                SELECT COALESCE(SUM(total_with_vat - paid_amount), 0) as overdue
                FROM invoices
                WHERE invoice_type = ?
                  AND status != 'cancelled'
                  AND (total_with_vat - paid_amount) > 0
                  AND due_date < date('now')
            """
            result = db.fetch_one(query_overdue, (self.invoice_type,))
            overdue = result["overdue"] if result else 0

            # Aktualizace labelů
            self.stat_labels["total"].setText(f"{total:,.2f} Kč".replace(",", " "))
            self.stat_labels["paid"].setText(f"{paid:,.2f} Kč".replace(",", " "))
            self.stat_labels["unpaid"].setText(f"{unpaid:,.2f} Kč".replace(",", " "))
            self.stat_labels["overdue"].setText(f"{overdue:,.2f} Kč".replace(",", " "))

        except Exception as e:
            print(f"Chyba při aktualizaci statistik: {e}")

    def apply_filters(self):
        """Aplikace filtrů"""
        search_text = self.search_input.text().lower()
        status_filter = self.status_combo.currentText()
        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()

        for row in range(self.table.rowCount()):
            show_row = True

            # Filtr vyhledávání
            if search_text:
                invoice_number = self.table.item(row, 1).text().lower()
                customer = self.table.item(row, 2).text().lower()
                if search_text not in invoice_number and search_text not in customer:
                    show_row = False

            # Filtr stavu
            if status_filter != "Všechny":
                row_status = self.table.item(row, 8).text()
                if status_filter != row_status:
                    show_row = False

            # Filtr data
            issue_date_text = self.table.item(row, 3).text()
            try:
                issue_date = datetime.strptime(issue_date_text, "%d.%m.%Y").date()
                if issue_date < date_from or issue_date > date_to:
                    show_row = False
            except:
                pass

            self.table.setRowHidden(row, not show_row)

    def new_invoice(self):
        """Vytvoření nové faktury"""
        dialog = InvoiceDialog(self, invoice_type=self.invoice_type)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_invoices()
            self.invoice_changed.emit()

    def send_email(self):
        """Odeslání faktury emailem"""
        if not self.table.selectedItems():
            QMessageBox.warning(self, "Upozornění", "Vyberte fakturu k odeslání.")
            return

        invoice_id = int(self.table.item(self.table.currentRow(), 0).text())
        invoice_number = self.table.item(self.table.currentRow(), 1).text()

        # TODO: Implementovat skutečné odesílání emailu
        QMessageBox.information(
            self,
            "Odeslání emailu",
            f"Funkce odeslání faktury {invoice_number} emailem bude implementována.\n\n"
            "Bude zahrnovat:\n"
            "- Generování PDF faktury\n"
            "- Načtení emailu zákazníka\n"
            "- Odeslání přes SMTP"
        )

    def print_invoice(self):
        """Tisk faktury"""
        if not self.table.selectedItems():
            QMessageBox.warning(self, "Upozornění", "Vyberte fakturu k tisku.")
            return

        invoice_id = int(self.table.item(self.table.currentRow(), 0).text())
        invoice_number = self.table.item(self.table.currentRow(), 1).text()

        # TODO: Implementovat generování PDF a tisk
        QMessageBox.information(
            self,
            "Tisk faktury",
            f"Funkce tisku faktury {invoice_number} bude implementována.\n\n"
            "Bude zahrnovat:\n"
            "- Generování PDF faktury\n"
            "- Odeslání na výchozí tiskárnu"
        )

    def export_invoices(self):
        """Export faktur"""
        # Dialog pro výběr formátu
        dialog = QDialog(self)
        dialog.setWindowTitle("Export faktur")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        label = QLabel("Vyberte formát exportu:")
        layout.addWidget(label)

        format_combo = QComboBox()
        format_combo.addItems(["Excel (.xlsx)", "PDF", "CSV"])
        layout.addWidget(format_combo)

        buttons_layout = QHBoxLayout()
        ok_btn = QPushButton("Export")
        cancel_btn = QPushButton("Zrušit")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        buttons_layout.addWidget(ok_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            format_text = format_combo.currentText()
            # TODO: Implementovat skutečný export
            QMessageBox.information(
                self,
                "Export",
                f"Export do formátu {format_text} bude implementován."
            )

    def record_payment(self):
        """Zaznamenání platby"""
        if not self.table.selectedItems():
            QMessageBox.warning(self, "Upozornění", "Vyberte fakturu pro zaznamenání platby.")
            return

        invoice_id = int(self.table.item(self.table.currentRow(), 0).text())
        invoice_number = self.table.item(self.table.currentRow(), 1).text()
        remaining = float(self.table.item(self.table.currentRow(), 7).text().replace(" Kč", "").replace(" ", ""))

        dialog = PaymentDialog(self, invoice_id, invoice_number, remaining)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_invoices()
            self.invoice_changed.emit()

    def cancel_invoice(self):
        """Storno faktury"""
        if not self.table.selectedItems():
            QMessageBox.warning(self, "Upozornění", "Vyberte fakturu ke stornování.")
            return

        invoice_id = int(self.table.item(self.table.currentRow(), 0).text())
        invoice_number = self.table.item(self.table.currentRow(), 1).text()

        reply = QMessageBox.question(
            self,
            "Storno faktury",
            f"Opravdu chcete stornovat fakturu {invoice_number}?\n\n"
            "Tato akce je nevratná!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = "UPDATE invoices SET status = 'cancelled' WHERE id = ?"
                db.execute_query(query, (invoice_id,))
                QMessageBox.information(self, "Úspěch", f"Faktura {invoice_number} byla stornována.")
                self.load_invoices()
                self.invoice_changed.emit()
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se stornovat fakturu:\n{e}")

    def create_credit_note(self):
        """Vytvoření dobropisu"""
        if not self.table.selectedItems():
            QMessageBox.warning(self, "Upozornění", "Vyberte fakturu pro vytvoření dobropisu.")
            return

        invoice_id = int(self.table.item(self.table.currentRow(), 0).text())

        # TODO: Implementovat dialog pro dobropis
        QMessageBox.information(
            self,
            "Dobropis",
            "Funkce vytvoření dobropisu bude implementována.\n\n"
            "Bude zahrnovat:\n"
            "- Načtení původní faktury\n"
            "- Vytvoření nové faktury se zápornými částkami\n"
            "- Propojení s původní fakturou"
        )

    def open_invoice_detail(self):
        """Otevření detailu faktury"""
        if not self.table.selectedItems():
            return

        invoice_id = int(self.table.item(self.table.currentRow(), 0).text())

        dialog = InvoiceDialog(self, invoice_type=self.invoice_type, invoice_id=invoice_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_invoices()
            self.invoice_changed.emit()

    def refresh(self):
        """Obnovení dat"""
        self.load_invoices()


# =====================================================
# DIALOGY
# =====================================================

class InvoiceDialog(QDialog):
    """Dialog pro vytvoření/editaci faktury"""

    def __init__(self, parent, invoice_type="issued", invoice_id=None):
        super().__init__(parent)
        self.invoice_type = invoice_type
        self.invoice_id = invoice_id
        self.is_edit = invoice_id is not None
        self.items_data = []

        self.setWindowTitle("Editace faktury" if self.is_edit else "Nová faktura")
        self.setMinimumSize(900, 700)

        self.init_ui()

        if self.is_edit:
            self.load_invoice()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # Záložky
        tabs = QTabWidget()

        # Záložka: Základní údaje
        self.tab_basic = self.create_basic_tab()
        tabs.addTab(self.tab_basic, "Základní údaje")

        # Záložka: Položky faktury
        self.tab_items = self.create_items_tab()
        tabs.addTab(self.tab_items, "Položky faktury")

        layout.addWidget(tabs)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Uložit")
        save_btn.clicked.connect(self.save_invoice)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 10px 30px;
                border-radius: 4px;
                font-weight: bold;
            }}
        """)
        buttons_layout.addWidget(save_btn)

        layout.addLayout(buttons_layout)

    def create_basic_tab(self):
        """Vytvoření záložky se základními údaji"""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Číslo faktury
        self.invoice_number_input = QLineEdit()
        if not self.is_edit:
            next_number = db.get_next_invoice_number(self.invoice_type)
            self.invoice_number_input.setText(next_number)
        layout.addRow("Číslo faktury:", self.invoice_number_input)

        # Zákazník/Dodavatel
        customer_layout = QHBoxLayout()
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        self.load_customers()
        customer_layout.addWidget(self.customer_combo)

        add_customer_btn = QPushButton("➕")
        add_customer_btn.setFixedWidth(40)
        add_customer_btn.clicked.connect(self.quick_add_customer)
        customer_layout.addWidget(add_customer_btn)

        if self.invoice_type == "issued":
            layout.addRow("Zákazník:", customer_layout)
        else:
            layout.addRow("Dodavatel:", customer_layout)

        # Datum vystavení
        self.issue_date = QDateEdit()
        self.issue_date.setDate(QDate.currentDate())
        self.issue_date.setCalendarPopup(True)
        self.issue_date.setDisplayFormat("dd.MM.yyyy")
        self.issue_date.dateChanged.connect(self.update_due_date)
        layout.addRow("Datum vystavení:", self.issue_date)

        # Datum splatnosti
        self.due_date = QDateEdit()
        self.due_date.setDate(QDate.currentDate().addDays(14))
        self.due_date.setCalendarPopup(True)
        self.due_date.setDisplayFormat("dd.MM.yyyy")
        layout.addRow("Datum splatnosti:", self.due_date)

        # Datum zdanitelného plnění
        self.tax_date = QDateEdit()
        self.tax_date.setDate(QDate.currentDate())
        self.tax_date.setCalendarPopup(True)
        self.tax_date.setDisplayFormat("dd.MM.yyyy")
        layout.addRow("Datum zdanitelného plnění:", self.tax_date)

        # Forma úhrady
        self.payment_method = QComboBox()
        self.payment_method.addItems([
            "Bankovní převod",
            "Hotovost",
            "Karta",
            "Ostatní"
        ])
        layout.addRow("Forma úhrady:", self.payment_method)

        # Variabilní symbol
        self.variable_symbol = QLineEdit()
        layout.addRow("Variabilní symbol:", self.variable_symbol)

        # Poznámka
        self.note_input = QTextEdit()
        self.note_input.setMaximumHeight(80)
        layout.addRow("Poznámka:", self.note_input)

        # Zakázka
        self.order_combo = QComboBox()
        self.order_combo.addItem("-- Bez zakázky --", None)
        self.load_orders()
        layout.addRow("Zakázka:", self.order_combo)

        return widget

    def create_items_tab(self):
        """Vytvoření záložky s položkami faktury"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        add_item_btn = QPushButton("➕ Přidat položku")
        add_item_btn.clicked.connect(self.add_invoice_item)
        buttons_layout.addWidget(add_item_btn)

        remove_item_btn = QPushButton("➖ Odebrat položku")
        remove_item_btn.clicked.connect(self.remove_invoice_item)
        buttons_layout.addWidget(remove_item_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # Tabulka položek
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            "Název", "Množství", "Jednotka", "Cena bez DPH", "DPH %", "Cena s DPH", "Celkem"
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.items_table)

        # Součty
        totals_group = QGroupBox("Celkem")
        totals_layout = QFormLayout(totals_group)

        self.total_without_vat_label = QLabel("0,00 Kč")
        self.total_without_vat_label.setStyleSheet("font-weight: bold;")
        totals_layout.addRow("Celkem bez DPH:", self.total_without_vat_label)

        self.total_vat_label = QLabel("0,00 Kč")
        self.total_vat_label.setStyleSheet("font-weight: bold;")
        totals_layout.addRow("Celkem DPH:", self.total_vat_label)

        self.total_with_vat_label = QLabel("0,00 Kč")
        self.total_with_vat_label.setStyleSheet("font-weight: bold; font-size: 14pt;")
        totals_layout.addRow("Celkem s DPH:", self.total_with_vat_label)

        layout.addWidget(totals_group)

        return widget

    def load_customers(self):
        """Načtení seznamu zákazníků"""
        try:
            query = """
                SELECT id, first_name, last_name, company
                FROM customers
                ORDER BY last_name, first_name
            """
            customers = db.fetch_all(query)

            self.customer_combo.clear()
            self.customer_combo.addItem("-- Vyberte zákazníka --", None)

            for customer in customers:
                if customer["company"]:
                    text = f"{customer['company']} ({customer['first_name']} {customer['last_name']})"
                else:
                    text = f"{customer['first_name']} {customer['last_name']}"
                self.customer_combo.addItem(text, customer["id"])

        except Exception as e:
            print(f"Chyba při načítání zákazníků: {e}")

    def load_orders(self):
        """Načtení seznamu zakázek"""
        try:
            query = """
                SELECT o.id, o.order_number, c.first_name, c.last_name
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                WHERE o.status != 'Dokončeno'
                ORDER BY o.created_date DESC
                LIMIT 50
            """
            orders = db.fetch_all(query)

            for order in orders:
                text = f"{order['order_number']} - {order['first_name']} {order['last_name']}"
                self.order_combo.addItem(text, order["id"])

        except Exception as e:
            print(f"Chyba při načítání zakázek: {e}")

    def update_due_date(self):
        """Aktualizace data splatnosti podle výchozího nastavení"""
        if not self.is_edit:
            query = "SELECT setting_value FROM admin_settings WHERE setting_key = 'default_due_days'"
            result = db.fetch_one(query)
            due_days = int(result[0]) if result else 14

            new_due_date = self.issue_date.date().addDays(due_days)
            self.due_date.setDate(new_due_date)

    def quick_add_customer(self):
        """Rychlé přidání zákazníka"""
        # TODO: Implementovat dialog pro rychlé přidání zákazníka
        QMessageBox.information(self, "Přidat zákazníka", "Dialog pro rychlé přidání zákazníka bude implementován.")

    def add_invoice_item(self):
        """Přidání položky faktury"""
        dialog = InvoiceItemDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            item_data = dialog.get_data()
            self.items_data.append(item_data)
            self.refresh_items_table()

    def remove_invoice_item(self):
        """Odebrání položky faktury"""
        current_row = self.items_table.currentRow()
        if current_row >= 0:
            del self.items_data[current_row]
            self.refresh_items_table()

    def refresh_items_table(self):
        """Obnovení tabulky položek"""
        self.items_table.setRowCount(len(self.items_data))

        total_without_vat = 0
        total_vat = 0
        total_with_vat = 0

        for row, item in enumerate(self.items_data):
            self.items_table.setItem(row, 0, QTableWidgetItem(item["name"]))
            self.items_table.setItem(row, 1, QTableWidgetItem(str(item["quantity"])))
            self.items_table.setItem(row, 2, QTableWidgetItem(item["unit"]))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{item['price']:,.2f}"))
            self.items_table.setItem(row, 4, QTableWidgetItem(f"{item['vat_rate']}%"))

            price_with_vat = item["price"] * (1 + item["vat_rate"] / 100)
            self.items_table.setItem(row, 5, QTableWidgetItem(f"{price_with_vat:,.2f}"))

            item_total = price_with_vat * item["quantity"]
            self.items_table.setItem(row, 6, QTableWidgetItem(f"{item_total:,.2f}"))

            # Součty
            item_total_without_vat = item["price"] * item["quantity"]
            item_vat = item_total_without_vat * item["vat_rate"] / 100

            total_without_vat += item_total_without_vat
            total_vat += item_vat
            total_with_vat += item_total

        # Aktualizace labelů
        self.total_without_vat_label.setText(f"{total_without_vat:,.2f} Kč".replace(",", " "))
        self.total_vat_label.setText(f"{total_vat:,.2f} Kč".replace(",", " "))
        self.total_with_vat_label.setText(f"{total_with_vat:,.2f} Kč".replace(",", " "))

    def load_invoice(self):
        """Načtení existující faktury"""
        try:
            query = """
                SELECT * FROM invoices WHERE id = ?
            """
            invoice = db.fetch_one(query, (self.invoice_id,))

            if not invoice:
                QMessageBox.critical(self, "Chyba", "Faktura nebyla nalezena.")
                return

            # Základní údaje
            self.invoice_number_input.setText(invoice["invoice_number"])

            if invoice["customer_id"]:
                index = self.customer_combo.findData(invoice["customer_id"])
                if index >= 0:
                    self.customer_combo.setCurrentIndex(index)

            self.issue_date.setDate(QDate.fromString(invoice["issue_date"], "yyyy-MM-dd"))
            self.due_date.setDate(QDate.fromString(invoice["due_date"], "yyyy-MM-dd"))
            self.tax_date.setDate(QDate.fromString(invoice["tax_date"], "yyyy-MM-dd"))

            if invoice["payment_method"]:
                index = self.payment_method.findText(invoice["payment_method"])
                if index >= 0:
                    self.payment_method.setCurrentIndex(index)

            if invoice["variable_symbol"]:
                self.variable_symbol.setText(invoice["variable_symbol"])

            if invoice["note"]:
                self.note_input.setPlainText(invoice["note"])

            if invoice["order_id"]:
                index = self.order_combo.findData(invoice["order_id"])
                if index >= 0:
                    self.order_combo.setCurrentIndex(index)

            # Načtení položek
            items_query = """
                SELECT * FROM invoice_items WHERE invoice_id = ?
            """
            items = db.fetch_all(items_query, (self.invoice_id,))

            self.items_data = []
            for item in items:
                self.items_data.append({
                    "name": item["item_name"],
                    "quantity": item["quantity"],
                    "unit": item["unit"] or "ks",
                    "price": item["price_per_unit"],
                    "vat_rate": item["vat_rate"]
                })

            self.refresh_items_table()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst fakturu:\n{e}")

    def save_invoice(self):
        """Uložení faktury"""
        try:
            # Validace
            if not self.invoice_number_input.text().strip():
                QMessageBox.warning(self, "Chyba", "Vyplňte číslo faktury.")
                return

            if self.customer_combo.currentData() is None and self.invoice_type == "issued":
                QMessageBox.warning(self, "Chyba", "Vyberte zákazníka.")
                return

            if len(self.items_data) == 0:
                QMessageBox.warning(self, "Chyba", "Přidejte alespoň jednu položku faktury.")
                return

            # Výpočet součtů
            total_without_vat = sum(item["price"] * item["quantity"] for item in self.items_data)
            total_vat = sum(item["price"] * item["quantity"] * item["vat_rate"] / 100 for item in self.items_data)
            total_with_vat = total_without_vat + total_vat

            # Data faktury
            invoice_data = {
                "invoice_number": self.invoice_number_input.text().strip(),
                "invoice_type": self.invoice_type,
                "customer_id": self.customer_combo.currentData(),
                "supplier_name": self.customer_combo.currentText() if self.invoice_type == "received" else None,
                "issue_date": self.issue_date.date().toString("yyyy-MM-dd"),
                "due_date": self.due_date.date().toString("yyyy-MM-dd"),
                "tax_date": self.tax_date.date().toString("yyyy-MM-dd"),
                "payment_method": self.payment_method.currentText(),
                "variable_symbol": self.variable_symbol.text().strip() or None,
                "note": self.note_input.toPlainText().strip() or None,
                "status": "unpaid",
                "total_without_vat": total_without_vat,
                "total_vat": total_vat,
                "total_with_vat": total_with_vat,
                "paid_amount": 0,
                "order_id": self.order_combo.currentData(),
                "created_by": 1  # TODO: Skutečné ID přihlášeného uživatele
            }

            if self.is_edit:
                # Aktualizace
                query = """
                    UPDATE invoices SET
                        invoice_number = ?, invoice_type = ?, customer_id = ?, supplier_name = ?,
                        issue_date = ?, due_date = ?, tax_date = ?, payment_method = ?,
                        variable_symbol = ?, note = ?, total_without_vat = ?, total_vat = ?,
                        total_with_vat = ?, order_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """
                db.execute_query(query, (
                    invoice_data["invoice_number"], invoice_data["invoice_type"],
                    invoice_data["customer_id"], invoice_data["supplier_name"],
                    invoice_data["issue_date"], invoice_data["due_date"], invoice_data["tax_date"],
                    invoice_data["payment_method"], invoice_data["variable_symbol"],
                    invoice_data["note"], invoice_data["total_without_vat"],
                    invoice_data["total_vat"], invoice_data["total_with_vat"],
                    invoice_data["order_id"], self.invoice_id
                ))

                # Smazat staré položky
                db.execute_query("DELETE FROM invoice_items WHERE invoice_id = ?", (self.invoice_id,))
                invoice_id = self.invoice_id

            else:
                # Vložení nové faktury
                query = """
                    INSERT INTO invoices (
                        invoice_number, invoice_type, customer_id, supplier_name,
                        issue_date, due_date, tax_date, payment_method, variable_symbol,
                        note, status, total_without_vat, total_vat, total_with_vat,
                        paid_amount, order_id, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                db.execute_query(query, (
                    invoice_data["invoice_number"], invoice_data["invoice_type"],
                    invoice_data["customer_id"], invoice_data["supplier_name"],
                    invoice_data["issue_date"], invoice_data["due_date"], invoice_data["tax_date"],
                    invoice_data["payment_method"], invoice_data["variable_symbol"],
                    invoice_data["note"], invoice_data["status"],
                    invoice_data["total_without_vat"], invoice_data["total_vat"],
                    invoice_data["total_with_vat"], invoice_data["paid_amount"],
                    invoice_data["order_id"], invoice_data["created_by"]
                ))

                # Získat ID nové faktury
                invoice_id = db.cursor.lastrowid

            # Vložení položek
            for item in self.items_data:
                item_total_without_vat = item["price"] * item["quantity"]
                item_vat = item_total_without_vat * item["vat_rate"] / 100
                item_total_with_vat = item_total_without_vat + item_vat

                query = """
                    INSERT INTO invoice_items (
                        invoice_id, item_name, quantity, unit, price_per_unit,
                        vat_rate, total_without_vat, total_vat, total_with_vat
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                db.execute_query(query, (
                    invoice_id, item["name"], item["quantity"], item["unit"],
                    item["price"], item["vat_rate"], item_total_without_vat,
                    item_vat, item_total_with_vat
                ))

            QMessageBox.information(
                self,
                "Úspěch",
                f"Faktura {invoice_data['invoice_number']} byla {'aktualizována' if self.is_edit else 'vytvořena'}."
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit fakturu:\n{e}")


class InvoiceItemDialog(QDialog):
    """Dialog pro přidání položky faktury"""

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Přidat položku")
        self.setMinimumWidth(500)

        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QFormLayout(self)

        # Název
        self.name_input = QLineEdit()
        layout.addRow("Název položky:", self.name_input)

        # Množství
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setDecimals(2)
        self.quantity_input.setMinimum(0.01)
        self.quantity_input.setMaximum(999999)
        self.quantity_input.setValue(1)
        layout.addRow("Množství:", self.quantity_input)

        # Jednotka
        self.unit_input = QComboBox()
        self.unit_input.setEditable(True)
        self.unit_input.addItems(["ks", "hod", "m", "m2", "m3", "kg", "l", "bal"])
        layout.addRow("Jednotka:", self.unit_input)

        # Cena bez DPH
        self.price_input = QDoubleSpinBox()
        self.price_input.setDecimals(2)
        self.price_input.setMinimum(0)
        self.price_input.setMaximum(999999)
        self.price_input.setSuffix(" Kč")
        layout.addRow("Cena bez DPH:", self.price_input)

        # Sazba DPH
        self.vat_input = QComboBox()
        self.vat_input.addItems(["21", "12", "0"])
        layout.addRow("Sazba DPH (%):", self.vat_input)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("Přidat")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 8px 20px;
            }}
        """)
        buttons_layout.addWidget(ok_btn)

        layout.addRow(buttons_layout)

    def get_data(self):
        """Vrátí data položky"""
        return {
            "name": self.name_input.text().strip(),
            "quantity": self.quantity_input.value(),
            "unit": self.unit_input.currentText(),
            "price": self.price_input.value(),
            "vat_rate": int(self.vat_input.currentText())
        }


class PaymentDialog(QDialog):
    """Dialog pro zaznamenání platby"""

    def __init__(self, parent, invoice_id, invoice_number, remaining_amount):
        super().__init__(parent)
        self.invoice_id = invoice_id
        self.invoice_number = invoice_number
        self.remaining_amount = remaining_amount

        self.setWindowTitle(f"Zaznamenat platbu - {invoice_number}")
        self.setMinimumWidth(400)

        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QFormLayout(self)

        # Info
        info_label = QLabel(f"Zbývá uhradit: <b>{self.remaining_amount:,.2f} Kč</b>".replace(",", " "))
        layout.addRow(info_label)

        # Datum platby
        self.payment_date = QDateEdit()
        self.payment_date.setDate(QDate.currentDate())
        self.payment_date.setCalendarPopup(True)
        self.payment_date.setDisplayFormat("dd.MM.yyyy")
        layout.addRow("Datum platby:", self.payment_date)

        # Částka
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setDecimals(2)
        self.amount_input.setMinimum(0.01)
        self.amount_input.setMaximum(self.remaining_amount)
        self.amount_input.setValue(self.remaining_amount)
        self.amount_input.setSuffix(" Kč")
        layout.addRow("Částka:", self.amount_input)

        # Způsob platby
        self.payment_method = QComboBox()
        self.payment_method.addItems([
            "Bankovní převod",
            "Hotovost",
            "Karta",
            "Ostatní"
        ])
        layout.addRow("Způsob platby:", self.payment_method)

        # Poznámka
        self.note_input = QTextEdit()
        self.note_input.setMaximumHeight(60)
        layout.addRow("Poznámka:", self.note_input)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Uložit platbu")
        save_btn.clicked.connect(self.save_payment)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 8px 20px;
            }}
        """)
        buttons_layout.addWidget(save_btn)

        layout.addRow(buttons_layout)

    def save_payment(self):
        """Uložení platby"""
        try:
            amount = self.amount_input.value()

            if amount <= 0:
                QMessageBox.warning(self, "Chyba", "Zadejte platnou částku.")
                return

            if amount > self.remaining_amount + 0.01:  # Tolerance
                QMessageBox.warning(self, "Chyba", "Částka platby překračuje zbývající dluh.")
                return

            # Vložení platby
            query = """
                INSERT INTO payments (
                    invoice_id, payment_date, amount, payment_method, note, created_by
                ) VALUES (?, ?, ?, ?, ?, ?)
            """
            db.execute_query(query, (
                self.invoice_id,
                self.payment_date.date().toString("yyyy-MM-dd"),
                amount,
                self.payment_method.currentText(),
                self.note_input.toPlainText().strip() or None,
                1  # TODO: Skutečné ID uživatele
            ))

            # Aktualizace zaplacené částky na faktuře
            update_query = """
                UPDATE invoices
                SET paid_amount = paid_amount + ?,
                    status = CASE
                        WHEN (paid_amount + ?) >= total_with_vat THEN 'paid'
                        WHEN (paid_amount + ?) > 0 THEN 'partial'
                        ELSE status
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            db.execute_query(update_query, (amount, amount, amount, self.invoice_id))

            QMessageBox.information(
                self,
                "Úspěch",
                f"Platba {amount:,.2f} Kč byla zaznamenána.".replace(",", " ")
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit platbu:\n{e}")
