# -*- coding: utf-8 -*-
"""
Generování a tisk štítků skladu - PROFESIONÁLNÍ
QR kódy, čárové kódy, různé velikosti, náhled, hromadný tisk
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QSpinBox, QGroupBox, QFormLayout, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QTextEdit, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor, QPen, QImage
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
import config
from database_manager import db
from datetime import datetime
import os


class WarehouseLabelsDialog(QDialog):
    """Dialog pro generování a tisk štítků"""

    def __init__(self, parent=None, item_id=None, items_list=None):
        super().__init__(parent)

        self.item_id = item_id
        self.items_list = items_list or []
        self.label_images = []

        self.setWindowTitle("🏷️ Generování štítků")
        self.setModal(True)
        self.setMinimumSize(900, 700)

        self.init_ui()

        if item_id:
            self.load_single_item()
        elif items_list:
            self.load_multiple_items()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # Hlavička
        header = QLabel("🏷️ GENEROVÁNÍ ŠTÍTKŮ")
        header.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {config.COLOR_PRIMARY};
            padding: 15px;
            background-color: #ecf0f1;
            border-radius: 5px;
        """)
        layout.addWidget(header)

        # === NASTAVENÍ ===
        settings_group = QGroupBox("⚙️ Nastavení štítků")
        settings_layout = QFormLayout(settings_group)

        # Typ štítku
        self.combo_label_type = QComboBox()
        self.combo_label_type.addItem("📄 Malý štítek (5×3 cm)", "small")
        self.combo_label_type.addItem("📄 Střední štítek (7×5 cm)", "medium")
        self.combo_label_type.addItem("📄 Velký štítek (10×7 cm)", "large")
        self.combo_label_type.addItem("📄 A4 - 1 štítek", "a4_single")
        self.combo_label_type.addItem("📄 A4 - 6 štítků (2×3)", "a4_6up")
        self.combo_label_type.addItem("📄 A4 - 12 štítků (3×4)", "a4_12up")
        self.combo_label_type.currentIndexChanged.connect(self.update_preview)
        settings_layout.addRow("Velikost:", self.combo_label_type)

        # Typ kódu
        self.combo_code_type = QComboBox()
        self.combo_code_type.addItem("📊 Čárový kód (Code128)", "barcode")
        self.combo_code_type.addItem("🔲 QR kód", "qr")
        self.combo_code_type.addItem("🔲 QR + čárový kód", "both")
        self.combo_code_type.addItem("❌ Žádný kód", "none")
        self.combo_code_type.currentIndexChanged.connect(self.update_preview)
        settings_layout.addRow("Typ kódu:", self.combo_code_type)

        # Obsah štítku
        self.check_show_name = QCheckBox("Zobrazit název")
        self.check_show_name.setChecked(True)
        self.check_show_name.stateChanged.connect(self.update_preview)
        settings_layout.addRow("", self.check_show_name)

        self.check_show_code = QCheckBox("Zobrazit kód položky")
        self.check_show_code.setChecked(True)
        self.check_show_code.stateChanged.connect(self.update_preview)
        settings_layout.addRow("", self.check_show_code)

        self.check_show_price = QCheckBox("Zobrazit cenu")
        self.check_show_price.setChecked(True)
        self.check_show_price.stateChanged.connect(self.update_preview)
        settings_layout.addRow("", self.check_show_price)

        self.check_show_location = QCheckBox("Zobrazit umístění")
        self.check_show_location.setChecked(False)
        self.check_show_location.stateChanged.connect(self.update_preview)
        settings_layout.addRow("", self.check_show_location)

        # Počet kopií
        self.spin_copies = QSpinBox()
        self.spin_copies.setRange(1, 100)
        self.spin_copies.setValue(1)
        self.spin_copies.setSuffix(" ks")
        settings_layout.addRow("Počet kopií:", self.spin_copies)

        layout.addWidget(settings_group)

        # === POLOŽKY K TISKU ===
        items_group = QGroupBox("📦 Položky k tisku")
        items_layout = QVBoxLayout(items_group)

        self.table_items = QTableWidget()
        self.table_items.setColumnCount(5)
        self.table_items.setHorizontalHeaderLabels([
            'Název', 'Kód', 'Cena', 'Kopií', 'ID'
        ])
        self.table_items.setColumnHidden(4, True)
        self.table_items.horizontalHeader().setStretchLastSection(True)
        self.table_items.setMaximumHeight(150)
        items_layout.addWidget(self.table_items)

        # Tlačítka pro správu položek
        items_buttons = QHBoxLayout()

        btn_add_item = QPushButton("➕ Přidat položku")
        btn_add_item.clicked.connect(self.add_item)
        items_buttons.addWidget(btn_add_item)

        btn_remove_item = QPushButton("➖ Odebrat")
        btn_remove_item.clicked.connect(self.remove_item)
        items_buttons.addWidget(btn_remove_item)

        items_buttons.addStretch()

        self.lbl_total_labels = QLabel("Celkem štítků: 0")
        self.lbl_total_labels.setStyleSheet("font-weight: bold;")
        items_buttons.addWidget(self.lbl_total_labels)

        items_layout.addLayout(items_buttons)

        layout.addWidget(items_group)

        # === NÁHLED ===
        preview_group = QGroupBox("👁️ Náhled štítku")
        preview_layout = QVBoxLayout(preview_group)

        # Scroll area pro náhled
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(200)

        self.preview_widget = QLabel()
        self.preview_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_widget.setStyleSheet("background-color: white; border: 1px solid #ddd;")
        scroll.setWidget(self.preview_widget)

        preview_layout.addWidget(scroll)

        layout.addWidget(preview_group)

        # === TLAČÍTKA ===
        buttons = QHBoxLayout()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        buttons.addStretch()

        btn_save = QPushButton("💾 Uložit jako obrázek")
        btn_save.clicked.connect(self.save_as_image)
        buttons.addWidget(btn_save)

        btn_preview = QPushButton("👁️ Náhled tisku")
        btn_preview.clicked.connect(self.print_preview)
        buttons.addWidget(btn_preview)

        btn_print = QPushButton("🖨️ Tisknout")
        btn_print.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
        """)
        btn_print.clicked.connect(self.print_labels)
        buttons.addWidget(btn_print)

        layout.addLayout(buttons)

    def load_single_item(self):
        """Načtení jedné položky"""
        try:
            item = db.execute_query("""
                SELECT id, name, code, price_sale, location
                FROM warehouse WHERE id = ?
            """, [self.item_id])

            if item:
                self.table_items.setRowCount(1)

                self.table_items.setItem(0, 0, QTableWidgetItem(item[0][1]))
                self.table_items.setItem(0, 1, QTableWidgetItem(item[0][2] or "---"))
                self.table_items.setItem(0, 2, QTableWidgetItem(f"{item[0][3]:.2f} Kč"))

                spin = QSpinBox()
                spin.setRange(1, 100)
                spin.setValue(1)
                spin.valueChanged.connect(self.update_total_labels)
                self.table_items.setCellWidget(0, 3, spin)

                self.table_items.setItem(0, 4, QTableWidgetItem(str(item[0][0])))

                self.update_total_labels()
                self.update_preview()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba:\n{str(e)}")

    def load_multiple_items(self):
        """Načtení více položek"""
        try:
            self.table_items.setRowCount(0)

            for item_id in self.items_list:
                item = db.execute_query("""
                    SELECT id, name, code, price_sale, location
                    FROM warehouse WHERE id = ?
                """, [item_id])

                if item:
                    row = self.table_items.rowCount()
                    self.table_items.insertRow(row)

                    self.table_items.setItem(row, 0, QTableWidgetItem(item[0][1]))
                    self.table_items.setItem(row, 1, QTableWidgetItem(item[0][2] or "---"))
                    self.table_items.setItem(row, 2, QTableWidgetItem(f"{item[0][3]:.2f} Kč"))

                    spin = QSpinBox()
                    spin.setRange(1, 100)
                    spin.setValue(1)
                    spin.valueChanged.connect(self.update_total_labels)
                    self.table_items.setCellWidget(row, 3, spin)

                    self.table_items.setItem(row, 4, QTableWidgetItem(str(item[0][0])))

            self.update_total_labels()
            self.update_preview()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba:\n{str(e)}")

    def add_item(self):
        """Přidání položky"""
        from .warehouse_widgets import ItemSelectorDialog

        dialog = ItemSelectorDialog(self)
        if dialog.exec():
            selected = dialog.get_selected_items()
            if selected:
                self.items_list.extend(selected)
                self.load_multiple_items()

    def remove_item(self):
        """Odebrání položky"""
        current_row = self.table_items.currentRow()
        if current_row >= 0:
            self.table_items.removeRow(current_row)
            self.update_total_labels()

    def update_total_labels(self):
        """Aktualizace celkového počtu štítků"""
        total = 0
        for row in range(self.table_items.rowCount()):
            spin = self.table_items.cellWidget(row, 3)
            if spin:
                total += spin.value()

        self.lbl_total_labels.setText(f"Celkem štítků: {total}")

    def update_preview(self):
        """Aktualizace náhledu"""
        if self.table_items.rowCount() == 0:
            return

        try:
            # Načtení první položky pro náhled
            item_id = int(self.table_items.item(0, 4).text())

            item = db.execute_query("""
                SELECT name, code, ean, price_sale, location
                FROM warehouse WHERE id = ?
            """, [item_id])

            if item:
                item_data = {
                    'name': item[0][0],
                    'code': item[0][1] or "",
                    'ean': item[0][2] or "",
                    'price_sale': item[0][3],
                    'location': item[0][4] or ""
                }

                # Generování náhledu
                pixmap = self.generate_label_preview(item_data)
                self.preview_widget.setPixmap(pixmap)

        except Exception as e:
            print(f"Chyba náhledu: {e}")

    def generate_label_preview(self, item_data):
        """Generování náhledu štítku"""
        label_type = self.combo_label_type.currentData()
        code_type = self.combo_code_type.currentData()

        # Velikosti v pixelech (pro náhled)
        sizes = {
            'small': (200, 120),
            'medium': (280, 200),
            'large': (400, 280),
            'a4_single': (600, 800),
            'a4_6up': (280, 200),
            'a4_12up': (200, 150)
        }

        width, height = sizes.get(label_type, (280, 200))

        # Vytvoření obrázku
        image = QImage(width, height, QImage.Format.Format_RGB32)
        image.fill(QColor("white"))

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Okraje
        margin = 10
        y_pos = margin

        # === NÁZEV ===
        if self.check_show_name.isChecked():
            font = QFont("Arial", 12, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor("black"))

            # Zkrácení názvu pokud je moc dlouhý
            name = item_data['name'][:40]
            rect = QRectF(margin, y_pos, width - 2*margin, 30)
            painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, name)
            y_pos += 35

        # === KÓD POLOŽKY ===
        if self.check_show_code.isChecked() and item_data['code']:
            font = QFont("Arial", 9)
            painter.setFont(font)
            painter.setPen(QColor("#555"))

            rect = QRectF(margin, y_pos, width - 2*margin, 20)
            painter.drawText(rect, Qt.AlignmentFlag.AlignLeft, f"Kód: {item_data['code']}")
            y_pos += 25

        # === ČÁROVÝ/QR KÓD ===
        if code_type != "none":
            code_height = 60

            if code_type == "barcode" or code_type == "both":
                barcode_img = self.generate_barcode(item_data)
                if barcode_img:
                    painter.drawPixmap(margin, y_pos, width - 2*margin, code_height, barcode_img)
                    y_pos += code_height + 5

            if code_type == "qr" or code_type == "both":
                qr_img = self.generate_qr_code(item_data)
                if qr_img:
                    qr_size = min(80, width - 2*margin)
                    painter.drawPixmap(margin, y_pos, qr_size, qr_size, qr_img)
                    y_pos += qr_size + 5

        # === CENA ===
        if self.check_show_price.isChecked():
            font = QFont("Arial", 14, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor(config.COLOR_SUCCESS))

            price_text = f"{item_data['price_sale']:.2f} Kč"
            rect = QRectF(margin, y_pos, width - 2*margin, 30)
            painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, price_text)
            y_pos += 35

        # === UMÍSTĚNÍ ===
        if self.check_show_location.isChecked() and item_data['location']:
            font = QFont("Arial", 8)
            painter.setFont(font)
            painter.setPen(QColor("#888"))

            rect = QRectF(margin, y_pos, width - 2*margin, 20)
            painter.drawText(rect, Qt.AlignmentFlag.AlignLeft, f"📍 {item_data['location']}")

        # Rámeček
        painter.setPen(QPen(QColor("#ddd"), 2))
        painter.drawRect(1, 1, width-2, height-2)

        painter.end()

        return QPixmap.fromImage(image)

    def generate_barcode(self, item_data):
        """Generování čárového kódu"""
        try:
            import barcode
            from barcode.writer import ImageWriter
            from io import BytesIO

            # Použití EAN nebo kódu položky
            code = item_data.get('ean') or item_data.get('code') or "0000000000000"

            # Zajištění správného formátu
            if len(code) == 13 and code.isdigit():
                barcode_class = barcode.get_barcode_class('ean13')
            else:
                barcode_class = barcode.get_barcode_class('code128')
                code = str(code)

            # Generování do bufferu
            buffer = BytesIO()
            barcode_instance = barcode_class(code, writer=ImageWriter())

            options = {
                'module_width': 0.2,
                'module_height': 8.0,
                'quiet_zone': 2.0,
                'font_size': 8,
                'text_distance': 2.0,
            }

            barcode_instance.write(buffer, options)
            buffer.seek(0)

            # Načtení jako pixmap
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue())

            return pixmap

        except Exception as e:
            print(f"Chyba generování čárového kódu: {e}")
            return None

    def generate_qr_code(self, item_data):
        """Generování QR kódu"""
        try:
            import qrcode
            from io import BytesIO

            # Data pro QR kód
            qr_data = f"ITEM:{item_data['code']}\nNAME:{item_data['name']}\nPRICE:{item_data['price_sale']}"

            # Generování QR kódu
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=2,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Konverze na pixmap
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue())

            return pixmap

        except Exception as e:
            print(f"Chyba generování QR kódu: {e}")
            return None

    def print_preview(self):
        """Náhled tisku"""
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)

            preview = QPrintPreviewDialog(printer, self)
            preview.paintRequested.connect(self.handle_print_request)
            preview.exec()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba náhledu:\n{str(e)}")

    def print_labels(self):
        """Tisk štítků"""
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)

            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                self.handle_print_request(printer)
                QMessageBox.information(self, "Úspěch", "Štítky byly odeslány do tiskárny")
                self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba tisku:\n{str(e)}")

    def handle_print_request(self, printer):
        """Zpracování tisku"""
        painter = QPainter()
        painter.begin(printer)

        label_type = self.combo_label_type.currentData()

        # Rozměry stránky
        page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
        page_width = page_rect.width()
        page_height = page_rect.height()

        # Velikosti štítků v pixelech
        label_sizes = {
            'small': (int(5 * 96 / 2.54), int(3 * 96 / 2.54)),  # 5×3 cm
            'medium': (int(7 * 96 / 2.54), int(5 * 96 / 2.54)),  # 7×5 cm
            'large': (int(10 * 96 / 2.54), int(7 * 96 / 2.54)),  # 10×7 cm
            'a4_single': (int(page_width * 0.9), int(page_height * 0.9)),
            'a4_6up': (int(page_width / 2 - 40), int(page_height / 3 - 40)),
            'a4_12up': (int(page_width / 3 - 30), int(page_height / 4 - 30))
        }

        label_width, label_height = label_sizes.get(label_type, (280, 200))

        # Rozložení štítků na stránce
        if label_type == 'a4_6up':
            cols, rows = 2, 3
        elif label_type == 'a4_12up':
            cols, rows = 3, 4
        elif label_type == 'a4_single':
            cols, rows = 1, 1
        else:
            cols, rows = 1, 1

        # Tisk všech štítků
        label_index = 0
        page_index = 0

        for row in range(self.table_items.rowCount()):
            item_id = int(self.table_items.item(row, 4).text())
            spin = self.table_items.cellWidget(row, 3)
            copies = spin.value() if spin else 1

            # Načtení dat položky
            item = db.execute_query("""
                SELECT name, code, ean, price_sale, location
                FROM warehouse WHERE id = ?
            """, [item_id])

            if not item:
                continue

            item_data = {
                'name': item[0][0],
                'code': item[0][1] or "",
                'ean': item[0][2] or "",
                'price_sale': item[0][3],
                'location': item[0][4] or ""
            }

            # Tisk kopií
            for _ in range(copies):
                # Pozice na stránce
                col = label_index % cols
                row_pos = (label_index // cols) % rows

                x = 20 + col * (label_width + 20)
                y = 20 + row_pos * (label_height + 20)

                # Vykreslení štítku
                self.draw_label_on_painter(painter, item_data, x, y, label_width, label_height)

                label_index += 1

                # Nová stránka?
                if label_index >= cols * rows:
                    label_index = 0
                    page_index += 1
                    if page_index < self.get_total_labels_count():
                        printer.newPage()

        painter.end()

    def draw_label_on_painter(self, painter, item_data, x, y, width, height):
        """Vykreslení štítku na painteru"""
        painter.save()

        # Rámeček
        painter.setPen(QPen(QColor("#ddd"), 1))
        painter.drawRect(x, y, width, height)

        margin = 10
        y_pos = y + margin

        # Název
        if self.check_show_name.isChecked():
            font = QFont("Arial", 10, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor("black"))

            name = item_data['name'][:40]
            rect = QRectF(x + margin, y_pos, width - 2*margin, 25)
            painter.drawText(rect, Qt.AlignmentFlag.AlignLeft, name)
            y_pos += 30

        # Kód
        if self.check_show_code.isChecked() and item_data['code']:
            font = QFont("Arial", 8)
            painter.setFont(font)
            painter.setPen(QColor("#555"))

            rect = QRectF(x + margin, y_pos, width - 2*margin, 15)
            painter.drawText(rect, Qt.AlignmentFlag.AlignLeft, f"Kód: {item_data['code']}")
            y_pos += 20

        # Čárový/QR kód
        code_type = self.combo_code_type.currentData()
        if code_type != "none":
            if code_type == "barcode" or code_type == "both":
                barcode_img = self.generate_barcode(item_data)
                if barcode_img:
                    code_height = 50
                    painter.drawPixmap(x + margin, y_pos, width - 2*margin, code_height, barcode_img)
                    y_pos += code_height + 5

            if code_type == "qr" or code_type == "both":
                qr_img = self.generate_qr_code(item_data)
                if qr_img:
                    qr_size = min(60, width - 2*margin)
                    painter.drawPixmap(x + margin, y_pos, qr_size, qr_size, qr_img)
                    y_pos += qr_size + 5

        # Cena
        if self.check_show_price.isChecked():
            font = QFont("Arial", 12, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor(config.COLOR_SUCCESS))

            price_text = f"{item_data['price_sale']:.2f} Kč"
            rect = QRectF(x + margin, y_pos, width - 2*margin, 25)
            painter.drawText(rect, Qt.AlignmentFlag.AlignLeft, price_text)
            y_pos += 30

        # Umístění
        if self.check_show_location.isChecked() and item_data['location']:
            font = QFont("Arial", 7)
            painter.setFont(font)
            painter.setPen(QColor("#888"))

            rect = QRectF(x + margin, y_pos, width - 2*margin, 15)
            painter.drawText(rect, Qt.AlignmentFlag.AlignLeft, f"📍 {item_data['location']}")

        painter.restore()

    def get_total_labels_count(self):
        """Celkový počet štítků k tisku"""
        total = 0
        for row in range(self.table_items.rowCount()):
            spin = self.table_items.cellWidget(row, 3)
            if spin:
                total += spin.value()
        return total

    def save_as_image(self):
        """Uložení jako obrázek"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Uložit štítek",
                f"stitek_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                "PNG obrázky (*.png);;JPEG obrázky (*.jpg)"
            )

            if not file_path:
                return

            # Generování obrázku první položky
            if self.table_items.rowCount() > 0:
                item_id = int(self.table_items.item(0, 4).text())

                item = db.execute_query("""
                    SELECT name, code, ean, price_sale, location
                    FROM warehouse WHERE id = ?
                """, [item_id])

                if item:
                    item_data = {
                        'name': item[0][0],
                        'code': item[0][1] or "",
                        'ean': item[0][2] or "",
                        'price_sale': item[0][3],
                        'location': item[0][4] or ""
                    }

                    pixmap = self.generate_label_preview(item_data)
                    pixmap.save(file_path)

                    QMessageBox.information(self, "Úspěch", f"Štítek byl uložen:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba:\n{str(e)}")


# ========================================
# BARCODE SCANNER INTEGRATION
# ========================================

class BarcodeScannerWidget(QWidget):
    """Widget pro integraci s čtečkou čárových kódů"""

    code_scanned = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scan_buffer = ""
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        info = QLabel("📷 Čtečka čárových kódů aktivní\nNaskenujte čárový kód...")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("""
            padding: 20px;
            background-color: #e8f5e9;
            border: 2px dashed #4caf50;
            border-radius: 5px;
            font-size: 14px;
        """)
        layout.addWidget(info)

        self.text_scanned = QTextEdit()
        self.text_scanned.setReadOnly(True)
        self.text_scanned.setMaximumHeight(100)
        layout.addWidget(QLabel("Poslední naskenované kódy:"))
        layout.addWidget(self.text_scanned)

    def keyPressEvent(self, event):
        """Zachycení vstupu z čtečky"""
        key = event.text()

        # Čtečka obvykle posílá Enter na konci
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.scan_buffer:
                self.process_scanned_code(self.scan_buffer)
                self.scan_buffer = ""
        else:
            # Přidání znaku do bufferu
            if key.isprintable():
                self.scan_buffer += key

    def process_scanned_code(self, code):
        """Zpracování naskenovaného kódu"""
        self.text_scanned.append(f"{datetime.now().strftime('%H:%M:%S')} - {code}")
        self.code_scanned.emit(code)
