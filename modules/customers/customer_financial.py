# customer_financial.py
# -*- coding: utf-8 -*-
"""
Widget pro finanční přehled zákazníka
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QProgressBar, QMessageBox, QAbstractItemView, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QBrush, QCursor
import config
from database_manager import db
from datetime import datetime, date


class CustomerFinancialWidget(QWidget):
    """Widget pro finanční přehled zákazníka"""

    invoice_paid = pyqtSignal(int)

    def __init__(self, customer_id):
        super().__init__()
        self.customer_id = customer_id
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Hlavička
        self.create_header(layout)

        # Přehledové boxy
        self.create_overview_boxes(layout)

        # Kredit limit
        self.create_credit_section(layout)

        # Tabulka faktur
        self.create_invoices_table(layout)

        # Tlačítka akcí
        self.create_action_buttons(layout)

        self.set_styles()

    def create_header(self, parent_layout):
        """Vytvoření hlavičky"""
        header = QHBoxLayout()

        title = QLabel("💰 Finanční přehled")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header.addWidget(title)

        header.addStretch()

        btn_export = QPushButton("📤 Export výpisu")
        btn_export.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_export.clicked.connect(self.export_statement)
        header.addWidget(btn_export)

        btn_refresh = QPushButton("🔄 Obnovit")
        btn_refresh.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_refresh.clicked.connect(self.load_data)
        header.addWidget(btn_refresh)

        parent_layout.addLayout(header)

    def create_overview_boxes(self, parent_layout):
        """Vytvoření přehledových boxů"""
        boxes_frame = QFrame()
        boxes_frame.setObjectName("overviewFrame")
        boxes_layout = QHBoxLayout(boxes_frame)
        boxes_layout.setSpacing(15)

        self.overview_labels = {}

        box_configs = [
            ("total_spent", "💰 Celková útrata", "0 Kč", "#27ae60"),
            ("this_year", "📅 Tento rok", "0 Kč", "#3498db"),
            ("avg_year", "📊 Průměr/rok", "0 Kč", "#9b59b6"),
            ("invoice_count", "🧾 Počet faktur", "0", "#f39c12"),
            ("unpaid", "❌ Neuhrazeno", "0 Kč", "#e74c3c"),
            ("overdue", "⚠️ Po splatnosti", "0 Kč", "#c0392b")
        ]

        for key, name, default, color in box_configs:
            box = self.create_stat_box(name, default, color)
            self.overview_labels[key] = box.findChild(QLabel, "boxValue")
            boxes_layout.addWidget(box)

        parent_layout.addWidget(boxes_frame)

    def create_stat_box(self, name, value, color):
        """Vytvoření statistického boxu"""
        box = QFrame()
        box.setObjectName("statBox")
        box.setStyleSheet(f"""
            #statBox {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 10px;
                min-width: 130px;
            }}
        """)

        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(10, 8, 10, 8)
        box_layout.setSpacing(5)

        value_label = QLabel(value)
        value_label.setObjectName("boxValue")
        value_font = QFont()
        value_font.setPointSize(16)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet(f"color: {color};")

        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        name_label.setWordWrap(True)

        box_layout.addWidget(value_label)
        box_layout.addWidget(name_label)

        return box

    def create_credit_section(self, parent_layout):
        """Vytvoření sekce kreditního limitu"""
        credit_group = QGroupBox("💳 Kreditní limit")
        credit_layout = QVBoxLayout(credit_group)

        # Info řádek
        info_layout = QHBoxLayout()

        self.lbl_credit_limit = QLabel("Limit: 0 Kč")
        self.lbl_credit_limit.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.lbl_credit_limit)

        info_layout.addStretch()

        self.lbl_credit_used = QLabel("Využito: 0 Kč")
        info_layout.addWidget(self.lbl_credit_used)

        info_layout.addStretch()

        self.lbl_credit_available = QLabel("Dostupné: 0 Kč")
        self.lbl_credit_available.setStyleSheet("font-weight: bold; color: #27ae60;")
        info_layout.addWidget(self.lbl_credit_available)

        credit_layout.addLayout(info_layout)

        # Progress bar
        self.credit_progress = QProgressBar()
        self.credit_progress.setRange(0, 100)
        self.credit_progress.setValue(0)
        self.credit_progress.setTextVisible(True)
        self.credit_progress.setFormat("%v%")
        self.credit_progress.setFixedHeight(25)
        credit_layout.addWidget(self.credit_progress)

        parent_layout.addWidget(credit_group)

    def create_invoices_table(self, parent_layout):
        """Vytvoření tabulky faktur"""
        invoices_group = QGroupBox("🧾 Faktury")
        invoices_layout = QVBoxLayout(invoices_group)

        self.invoices_table = QTableWidget()
        self.invoices_table.setObjectName("invoicesTable")

        columns = [
            "ID", "Číslo faktury", "Datum vystavení", "Splatnost",
            "Částka", "Stav", "Zbývá uhradit", "Akce"
        ]
        self.invoices_table.setColumnCount(len(columns))
        self.invoices_table.setHorizontalHeaderLabels(columns)

        self.invoices_table.setColumnHidden(0, True)

        header = self.invoices_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)

        self.invoices_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.invoices_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.invoices_table.setAlternatingRowColors(True)

        invoices_layout.addWidget(self.invoices_table)
        parent_layout.addWidget(invoices_group)

    def create_action_buttons(self, parent_layout):
        """Vytvoření tlačítek akcí"""
        actions_layout = QHBoxLayout()

        btn_reminder1 = QPushButton("📧 1. Upomínka")
        btn_reminder1.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_reminder1.clicked.connect(lambda: self.send_reminder(1))
        actions_layout.addWidget(btn_reminder1)

        btn_reminder2 = QPushButton("📧 2. Upomínka")
        btn_reminder2.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_reminder2.clicked.connect(lambda: self.send_reminder(2))
        actions_layout.addWidget(btn_reminder2)

        btn_reminder3 = QPushButton("⚠️ 3. Upomínka")
        btn_reminder3.setObjectName("btnDanger")
        btn_reminder3.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_reminder3.clicked.connect(lambda: self.send_reminder(3))
        actions_layout.addWidget(btn_reminder3)

        actions_layout.addStretch()

        btn_mark_paid = QPushButton("✅ Označit jako zaplaceno")
        btn_mark_paid.setObjectName("btnSuccess")
        btn_mark_paid.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_mark_paid.clicked.connect(self.mark_selected_as_paid)
        actions_layout.addWidget(btn_mark_paid)

        parent_layout.addLayout(actions_layout)

    def load_data(self):
        """Načtení finančních dat"""
        try:
            self.load_statistics()
            self.load_credit_info()
            self.load_invoices()
        except Exception as e:
            print(f"Chyba při načítání finančních dat: {e}")

    def load_statistics(self):
        """Načtení statistik"""
        try:
            # Celková útrata
            total = db.fetch_one(
                "SELECT COALESCE(SUM(total_price), 0) FROM orders WHERE customer_id = ?",
                (self.customer_id,)
            )
            total_spent = total[0] if total else 0
            self.overview_labels["total_spent"].setText(f"{total_spent:,.0f} Kč".replace(",", " "))

            # Útrata tento rok
            year_start = datetime(datetime.now().year, 1, 1).isoformat()
            this_year = db.fetch_one(
                f"SELECT COALESCE(SUM(total_price), 0) FROM orders WHERE customer_id = ? AND created_at >= '{year_start}'",
                (self.customer_id,)
            )
            year_spent = this_year[0] if this_year else 0
            self.overview_labels["this_year"].setText(f"{year_spent:,.0f} Kč".replace(",", " "))

            # Průměrná útrata za rok
            years = db.fetch_one(
                "SELECT MIN(created_at) FROM orders WHERE customer_id = ?",
                (self.customer_id,)
            )
            if years and years[0]:
                first_order = datetime.fromisoformat(years[0])
                years_count = max(1, (datetime.now() - first_order).days / 365)
                avg_year = total_spent / years_count
            else:
                avg_year = 0
            self.overview_labels["avg_year"].setText(f"{avg_year:,.0f} Kč".replace(",", " "))

            # Počet faktur
            invoice_count = db.fetch_one(
                "SELECT COUNT(*) FROM invoices WHERE customer_id = ?",
                (self.customer_id,)
            )
            count = invoice_count[0] if invoice_count else 0
            self.overview_labels["invoice_count"].setText(str(count))

            # Neuhrazené faktury
            unpaid = db.fetch_one(
                "SELECT COALESCE(SUM(amount - paid_amount), 0) FROM invoices WHERE customer_id = ? AND status != 'Zaplaceno'",
                (self.customer_id,)
            )
            unpaid_amount = unpaid[0] if unpaid else 0
            self.overview_labels["unpaid"].setText(f"{unpaid_amount:,.0f} Kč".replace(",", " "))

            # Po splatnosti
            today = date.today().isoformat()
            overdue = db.fetch_one(
                f"SELECT COALESCE(SUM(amount - paid_amount), 0) FROM invoices WHERE customer_id = ? AND status != 'Zaplaceno' AND due_date < '{today}'",
                (self.customer_id,)
            )
            overdue_amount = overdue[0] if overdue else 0
            self.overview_labels["overdue"].setText(f"{overdue_amount:,.0f} Kč".replace(",", " "))

            if overdue_amount > 0:
                self.overview_labels["overdue"].setStyleSheet("color: #c0392b; font-weight: bold;")

        except Exception as e:
            print(f"Chyba při načítání statistik: {e}")

    def load_credit_info(self):
        """Načtení informací o kreditu"""
        try:
            customer = db.fetch_one(
                "SELECT credit_limit FROM customers WHERE id = ?",
                (self.customer_id,)
            )

            credit_limit = customer[0] if customer and customer[0] else 0

            # Využitý kredit = neuhrazené faktury
            used = db.fetch_one(
                "SELECT COALESCE(SUM(amount - paid_amount), 0) FROM invoices WHERE customer_id = ? AND status != 'Zaplaceno'",
                (self.customer_id,)
            )
            credit_used = used[0] if used else 0

            credit_available = max(0, credit_limit - credit_used)

            self.lbl_credit_limit.setText(f"Limit: {credit_limit:,.0f} Kč".replace(",", " "))
            self.lbl_credit_used.setText(f"Využito: {credit_used:,.0f} Kč".replace(",", " "))
            self.lbl_credit_available.setText(f"Dostupné: {credit_available:,.0f} Kč".replace(",", " "))

            # Progress bar
            if credit_limit > 0:
                percentage = int((credit_used / credit_limit) * 100)
                self.credit_progress.setValue(min(100, percentage))

                # Barva podle využití
                if percentage > 90:
                    self.credit_progress.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")
                    self.lbl_credit_available.setStyleSheet("font-weight: bold; color: #e74c3c;")
                elif percentage > 70:
                    self.credit_progress.setStyleSheet("QProgressBar::chunk { background-color: #f39c12; }")
                    self.lbl_credit_available.setStyleSheet("font-weight: bold; color: #f39c12;")
                else:
                    self.credit_progress.setStyleSheet("QProgressBar::chunk { background-color: #27ae60; }")
                    self.lbl_credit_available.setStyleSheet("font-weight: bold; color: #27ae60;")
            else:
                self.credit_progress.setValue(0)

        except Exception as e:
            print(f"Chyba při načítání kreditu: {e}")

    def load_invoices(self):
        """Načtení faktur"""
        try:
            query = """
                SELECT
                    id,
                    invoice_number,
                    issue_date,
                    due_date,
                    amount,
                    status,
                    amount - paid_amount as remaining
                FROM invoices
                WHERE customer_id = ?
                ORDER BY issue_date DESC
            """

            invoices = db.fetch_all(query, (self.customer_id,))
            self.populate_invoices_table(invoices if invoices else [])

        except Exception as e:
            print(f"Chyba při načítání faktur: {e}")
            self.populate_invoices_table([])

    def populate_invoices_table(self, invoices):
        """Naplnění tabulky faktur"""
        self.invoices_table.setRowCount(0)

        today = date.today()

        for invoice in invoices:
            row = self.invoices_table.rowCount()
            self.invoices_table.insertRow(row)

            # ID
            self.invoices_table.setItem(row, 0, QTableWidgetItem(str(invoice[0])))

            # Číslo faktury
            inv_num_item = QTableWidgetItem(str(invoice[1] or ""))
            inv_num_font = QFont()
            inv_num_font.setBold(True)
            inv_num_item.setFont(inv_num_font)
            self.invoices_table.setItem(row, 1, inv_num_item)

            # Datum vystavení
            issue_date = invoice[2] or ""
            if issue_date:
                try:
                    dt = datetime.fromisoformat(issue_date).date()
                    issue_date = dt.strftime("%d.%m.%Y")
                except:
                    pass
            self.invoices_table.setItem(row, 2, QTableWidgetItem(issue_date))

            # Splatnost
            due_date = invoice[3]
            due_date_str = ""
            due_dt = None
            if due_date:
                try:
                    if isinstance(due_date, str):
                        due_dt = datetime.fromisoformat(due_date).date()
                    else:
                        due_dt = due_date
                    due_date_str = due_dt.strftime("%d.%m.%Y")
                except:
                    pass

            due_item = QTableWidgetItem(due_date_str)
            due_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Barevné označení splatnosti
            if due_dt and invoice[5] != "Zaplaceno":
                if due_dt < today:
                    due_item.setBackground(QBrush(QColor("#ffcccc")))  # Po splatnosti
                elif (due_dt - today).days <= 3:
                    due_item.setBackground(QBrush(QColor("#fff3cd")))  # Brzy vyprší

            self.invoices_table.setItem(row, 3, due_item)

            # Částka
            amount = invoice[4] or 0
            amount_item = QTableWidgetItem(f"{amount:,.0f} Kč".replace(",", " "))
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.invoices_table.setItem(row, 4, amount_item)

            # Stav
            status = str(invoice[5] or "Nezaplaceno")
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            if status == "Zaplaceno":
                status_item.setBackground(QBrush(QColor("#d4edda")))
            elif status == "Nezaplaceno":
                if due_dt and due_dt < today:
                    status_item.setBackground(QBrush(QColor("#f8d7da")))
                else:
                    status_item.setBackground(QBrush(QColor("#fff3cd")))
            else:
                status_item.setBackground(QBrush(QColor("#fff3cd")))

            self.invoices_table.setItem(row, 5, status_item)

            # Zbývá uhradit
            remaining = invoice[6] or 0
            remaining_item = QTableWidgetItem(f"{remaining:,.0f} Kč".replace(",", " "))
            remaining_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if remaining > 0:
                remaining_item.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.invoices_table.setItem(row, 6, remaining_item)

            # Akce
            self.invoices_table.setItem(row, 7, QTableWidgetItem(""))

    def mark_selected_as_paid(self):
        """Označení vybrané faktury jako zaplacené"""
        current_row = self.invoices_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Chyba", "Vyberte fakturu k zaplacení")
            return

        invoice_id = int(self.invoices_table.item(current_row, 0).text())
        invoice_num = self.invoices_table.item(current_row, 1).text()

        reply = QMessageBox.question(
            self,
            "Označit jako zaplaceno",
            f"Opravdu chcete označit fakturu {invoice_num} jako zaplacenou?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                db.execute(
                    "UPDATE invoices SET status = 'Zaplaceno', paid_amount = amount, paid_date = ? WHERE id = ?",
                    (datetime.now().isoformat(), invoice_id)
                )
                self.invoice_paid.emit(invoice_id)
                self.load_data()
                QMessageBox.information(self, "Úspěch", f"Faktura {invoice_num} byla označena jako zaplacená")
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se aktualizovat fakturu: {e}")

    def send_reminder(self, level):
        """Odeslání upomínky"""
        current_row = self.invoices_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Chyba", "Vyberte fakturu pro upomínku")
            return

        invoice_num = self.invoices_table.item(current_row, 1).text()

        if level == 3:
            reply = QMessageBox.warning(
                self,
                "⚠️ 3. Upomínka",
                f"3. upomínka pro fakturu {invoice_num} bude odeslána jako předání právníkovi.\n\nPokračovat?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
        else:
            reply = QMessageBox.question(
                self,
                f"{level}. Upomínka",
                f"Odeslat {level}. upomínku pro fakturu {invoice_num}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(
                self,
                "Upomínka odeslána",
                f"{level}. upomínka pro fakturu {invoice_num} byla odeslána"
            )

    def export_statement(self):
        """Export výpisu"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export finančního výpisu",
            f"financni_vypis_zakaznik_{self.customer_id}.pdf",
            "PDF soubory (*.pdf);;Excel soubory (*.xlsx)"
        )
        if file_path:
            QMessageBox.information(self, "Export", f"Export do: {file_path}")

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet(f"""
            #overviewFrame {{
                background-color: transparent;
            }}
            #invoicesTable {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                gridline-color: #e0e0e0;
            }}
            #invoicesTable::item {{
                padding: 6px;
            }}
            QHeaderView::section {{
                background-color: {config.COLOR_PRIMARY};
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
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
            QProgressBar {{
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: #27ae60;
                border-radius: 4px;
            }}
            #btnSuccess {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }}
            #btnSuccess:hover {{
                background-color: #219a52;
            }}
            #btnDanger {{
                background-color: {config.COLOR_DANGER};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }}
            #btnDanger:hover {{
                background-color: #c0392b;
            }}
            QPushButton {{
                padding: 6px 12px;
                border-radius: 4px;
                border: 1px solid #ddd;
            }}
            QPushButton:hover {{
                background-color: #e0e0e0;
            }}
        """)
