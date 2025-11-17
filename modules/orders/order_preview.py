# -*- coding: utf-8 -*-
"""
Náhled dokumentů - proforma, faktura (před tiskem/stažením)
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextBrowser, QMessageBox, QLabel
)
from PyQt6.QtCore import Qt
import config
from database_manager import db


class ProformaPreviewDialog(QDialog):
    """Dialog pro náhled proformy s možností tisku"""

    def __init__(self, order_id, parent=None):
        super().__init__(parent)
        self.order_id = order_id

        self.setWindowTitle("Náhled proformy")
        self.setModal(True)
        self.setMinimumSize(800, 900)

        self.init_ui()
        self.load_preview()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # === HLAVIČKA ===
        header = QLabel("📋 Náhled proformy")
        header.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {config.COLOR_PRIMARY};
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 5px;
        """)
        layout.addWidget(header)

        # === NÁHLED ===
        self.preview_browser = QTextBrowser()
        self.preview_browser.setStyleSheet("""
            QTextBrowser {
                background-color: white;
                border: 1px solid #ddd;
                padding: 20px;
            }
        """)
        layout.addWidget(self.preview_browser)

        # === TLAČÍTKA ===
        buttons = QHBoxLayout()

        btn_close = QPushButton("Zavřít")
        btn_close.clicked.connect(self.reject)

        btn_print = QPushButton("🖨️ Vytisknout")
        btn_print.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_PRIMARY};
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
        """)
        btn_print.clicked.connect(self.print_document)

        btn_save_pdf = QPushButton("💾 Uložit jako PDF")
        btn_save_pdf.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
        """)
        btn_save_pdf.clicked.connect(self.save_pdf)

        buttons.addWidget(btn_close)
        buttons.addStretch()
        buttons.addWidget(btn_print)
        buttons.addWidget(btn_save_pdf)

        layout.addLayout(buttons)

    def load_preview(self):
        """Načtení náhledu"""
        try:
            # Načtení dat
            order = db.execute_query(
                """SELECT
                    o.order_number, o.total_price, o.created_date,
                    c.first_name || ' ' || c.last_name as customer_name,
                    c.phone, c.address, c.city, c.postal_code,
                    v.brand || ' ' || v.model || ' (' || v.license_plate || ')' as vehicle
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                LEFT JOIN vehicles v ON o.vehicle_id = v.id
                WHERE o.id = ?""",
                [self.order_id]
            )

            if not order:
                return

            order = order[0]

            # Položky
            items = db.execute_query(
                """SELECT item_type, name, quantity, unit, unit_price, total_price
                   FROM order_items WHERE order_id = ?""",
                [self.order_id]
            )

            # Sestavení HTML náhledu
            html = self.generate_proforma_html(order, items)
            self.preview_browser.setHtml(html)

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při načítání:\n{str(e)}")

    def generate_proforma_html(self, order, items):
        """Generování HTML náhledu proformy"""

        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 20px;
                }}
                h1 {{
                    color: {config.COLOR_PRIMARY};
                    border-bottom: 3px solid {config.COLOR_PRIMARY};
                    padding-bottom: 10px;
                }}
                .header {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 30px;
                }}
                .info-box {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th {{
                    background-color: #34495e;
                    color: white;
                    padding: 12px;
                    text-align: left;
                }}
                td {{
                    padding: 10px;
                    border-bottom: 1px solid #ddd;
                }}
                tr:hover {{
                    background-color: #f8f9fa;
                }}
                .total {{
                    text-align: right;
                    font-size: 20px;
                    font-weight: bold;
                    color: {config.COLOR_SUCCESS};
                    margin-top: 20px;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                }}
            </style>
        </head>
        <body>
            <h1>PROFORMA</h1>

            <div class="header">
                <div>
                    <strong>Číslo zakázky:</strong> {order[0]}<br>
                    <strong>Datum:</strong> {order[2]}
                </div>
            </div>

            <div class="info-box">
                <h3>Zákazník</h3>
                <strong>{order[3]}</strong><br>
                {order[5] or ''}<br>
                {order[7] or ''} {order[6] or ''}<br>
                Tel.: {order[4] or ''}
            </div>

            <div class="info-box">
                <h3>Vozidlo</h3>
                {order[8] or '---'}
            </div>

            <h3>Položky</h3>
            <table>
                <tr>
                    <th>Popis</th>
                    <th style="text-align: center;">Množství</th>
                    <th style="text-align: right;">Cena/jedn.</th>
                    <th style="text-align: right;">Celkem</th>
                </tr>
        """

        # Položky
        total = 0
        for item in items:
            html += f"""
                <tr>
                    <td><strong>{item[0]}</strong><br>{item[1]}</td>
                    <td style="text-align: center;">{item[2]:.2f} {item[3]}</td>
                    <td style="text-align: right;">{item[4]:.2f} Kč</td>
                    <td style="text-align: right;"><strong>{item[5]:.2f} Kč</strong></td>
                </tr>
            """
            total += item[5]

        html += f"""
            </table>

            <div class="total">
                CELKEM: {total:.2f} Kč
            </div>

            <p style="color: #7f8c8d; font-size: 12px; margin-top: 30px;">
                Toto je nezávazná cenová nabídka.<br>
                Platnost: 14 dní od data vystavení.
            </p>
        </body>
        </html>
        """

        return html

    def print_document(self):
        """Tisk dokumentu"""
        from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

        printer = QPrinter()
        dialog = QPrintDialog(printer, self)

        if dialog.exec():
            self.preview_browser.print(printer)
            QMessageBox.information(self, "Úspěch", "Dokument byl vytištěn")

    def save_pdf(self):
        """Uložení jako PDF"""
        try:
            from .order_export import exporter
            success = exporter.export_proforma(self.order_id, self)

            if success:
                QMessageBox.information(self, "Úspěch", "PDF bylo uloženo")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba:\n{str(e)}")
