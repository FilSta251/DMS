# -*- coding: utf-8 -*-
"""
Náhled zakázkového listu před tiskem
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextBrowser, QMessageBox, QLabel
)
from PyQt6.QtCore import Qt
import config


class WorkOrderPreviewDialog(QDialog):
    """Dialog pro náhled zakázkového listu"""

    def __init__(self, form_data, parent=None):
        super().__init__(parent)
        self.form_data = form_data

        self.setWindowTitle("Náhled zakázkového listu")
        self.setModal(True)
        self.setMinimumSize(800, 900)

        self.init_ui()
        self.load_preview()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # === HLAVIČKA ===
        header = QLabel("📄 Náhled zakázkového listu")
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

        btn_edit = QPushButton("✏️ Upravit")
        btn_edit.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
        """)
        btn_edit.clicked.connect(self.reject)  # Zavře náhled, vrátí se k editoru

        buttons.addWidget(btn_close)
        buttons.addStretch()
        buttons.addWidget(btn_edit)

        layout.addLayout(buttons)

    def load_preview(self):
        """Načtení náhledu"""
        html = self.generate_html()
        self.preview_browser.setHtml(html)

    def generate_html(self):
        """Generování HTML náhledu"""
        d = self.form_data

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
                h2 {{
                    color: #34495e;
                    margin-top: 25px;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 5px;
                }}
                .info-box {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 15px 0;
                    border-left: 4px solid {config.COLOR_PRIMARY};
                }}
                .label {{
                    font-weight: bold;
                    color: #7f8c8d;
                }}
                .value {{
                    color: #2c3e50;
                }}
                .work-description {{
                    background-color: #fff;
                    border: 1px solid #ddd;
                    padding: 15px;
                    border-radius: 5px;
                    white-space: pre-wrap;
                    font-family: monospace;
                    margin: 10px 0;
                }}
                .extension-box {{
                    background-color: #fff3cd;
                    border: 1px solid #ffc107;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
                .price {{
                    font-size: 20px;
                    font-weight: bold;
                    color: {config.COLOR_SUCCESS};
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    text-align: right;
                }}
            </style>
        </head>
        <body>
            <h1>ZAKÁZKOVÝ LIST</h1>

            <div class="info-box">
                <span class="label">Číslo zakázky:</span> <span class="value">{d['order_number']}</span><br>
                <span class="label">Datum příjmu:</span> <span class="value">{d['date_received']}</span><br>
                <span class="label">Předběžný termín dokončení:</span> <span class="value">{d['date_estimated']}</span>
            </div>

            <h2>Zákazník</h2>
            <div class="info-box">
                <strong>{d['customer']}</strong>
            </div>

            <h2>Vozidlo</h2>
            <div class="info-box">
                <strong>{d['vehicle']}</strong>
            </div>

            <h2>Stav vozidla při příjmu</h2>
            <div class="info-box">
                <span class="label">Stav PHM:</span> <span class="value">{d['fuel_level'] or '---'}</span><br>
                <span class="label">Stav km:</span> <span class="value">{d['mileage'] or '---'}</span><br><br>
                <span class="label">Výbava vozidla / poškození:</span><br>
                <span class="value">{d['equipment'] or 'Neuvedeno'}</span>
            </div>

            <h2>Popis prací / požadavky zákazníka</h2>
            <div class="work-description">
{d['work_description'] or 'Neuvedeno'}
            </div>
        """

        # Rozšíření zakázky
        if d['extension']:
            html += f"""
            <h2>Rozšíření zakázky / vyjádření opravny</h2>
            <div class="extension-box">
                {d['extension']}
            </div>
            """

        # Cena
        html += f"""
            <h2>Předběžná cena</h2>
            <div class="price">
                Odhad ceny vč. DPH: {d['estimated_price'] or '---'} Kč
            </div>
        """

        # Poznámky
        if d['notes']:
            html += f"""
            <h2>Poznámky</h2>
            <div class="info-box">
                {d['notes']}
            </div>
            """

        html += """
            <br><br>
            <hr>
            <p style="color: #7f8c8d; font-size: 12px; text-align: center;">
                Zakázkový list uschovejte do vydání vozidla!
            </p>
        </body>
        </html>
        """

        return html
