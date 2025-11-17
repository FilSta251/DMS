# -*- coding: utf-8 -*-
"""
Správa položek zakázky - díly, práce, ostatní (produkční verze)
Kompatibilní s DB schématem:
- order_items má sloupce: id, order_id, warehouse_id, item_name, name, quantity,
  unit, unit_price, vat_rate, total_price, item_type, created_at
- čtení názvu přes COALESCE(name, item_name)
- při uložení synchronizujeme name i item_name
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox,
    QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal
import math
import config
from database_manager import db


def _safe_round(value: float, ndigits: int = 2) -> float:
    """Stabilní zaokrouhlení finálních částek (ochrana před 1e-15 apod.)."""
    if value is None:
        return 0.0
    factor = 10 ** ndigits
    return math.floor(value * factor + 0.5) / factor


class OrderItemsWidget(QWidget):
    """Widget pro správu položek zakázky"""

    items_changed = pyqtSignal()

    def __init__(self, order_id, parent=None):
        super().__init__(parent)
        self.order_id = order_id
        self.init_ui()
        self.load_items()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # Hlavička
        header = QHBoxLayout()

        lbl_title = QLabel("📦 Položky zakázky")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(lbl_title)
        header.addStretch()

        # Tlačítka
        btn_add_part = QPushButton("+ Díl")
        btn_add_part.setStyleSheet(self.get_button_style(config.COLOR_SUCCESS))
        btn_add_part.clicked.connect(lambda: self.add_item("Díl"))

        btn_add_work = QPushButton("+ Práce")
        btn_add_work.setStyleSheet(self.get_button_style(config.COLOR_SECONDARY))
        btn_add_work.clicked.connect(lambda: self.add_item("Práce"))

        btn_add_other = QPushButton("+ Ostatní")
        btn_add_other.setStyleSheet(self.get_button_style(config.COLOR_WARNING))
        btn_add_other.clicked.connect(lambda: self.add_item("Ostatní"))

        btn_delete = QPushButton("🗑️ Smazat")
        btn_delete.setStyleSheet(self.get_button_style(config.COLOR_DANGER))
        btn_delete.clicked.connect(self.delete_item)

        header.addWidget(btn_add_part)
        header.addWidget(btn_add_work)
        header.addWidget(btn_add_other)
        header.addWidget(btn_delete)

        layout.addLayout(header)

        # Tabulka položek
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Typ", "Název", "Množství", "Jednotka",
            "Cena/jedn.", "DPH %", "Cena celkem", "ID"
        ])
        self.table.setColumnHidden(7, True)

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)

        # Dvojklik pro editaci
        self.table.doubleClicked.connect(self.edit_item)

        layout.addWidget(self.table)

        # Souhrn
        summary = QHBoxLayout()
        summary.addStretch()

        self.lbl_summary = QLabel("Celkem: 0.00 Kč (bez DPH: 0.00 Kč)")
        self.lbl_summary.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {config.COLOR_PRIMARY};
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 5px;
        """)
        summary.addWidget(self.lbl_summary)

        layout.addLayout(summary)

    def get_button_style(self, color):
        """Styl pro tlačítka"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """

    def load_items(self):
        """Načtení položek (odolné vůči starému schématu)"""
        try:
            items = db.execute_query(
                """
                SELECT
                    id,
                    item_type,
                    COALESCE(name, item_name) AS display_name,
                    quantity,
                    unit,
                    unit_price,
                    vat_rate,
                    total_price
                FROM order_items
                WHERE order_id = ?
                ORDER BY id
                """,
                [self.order_id]
            )

            self.table.setRowCount(0)
            total_with_vat = 0.0
            total_without_vat = 0.0

            for row_obj in items:
                # row_obj je sqlite3.Row -> přístup přes jména i indexy
                _id = row_obj["id"]
                _type = row_obj["item_type"] or ""
                _name = row_obj["display_name"] or ""
                _qty = float(row_obj["quantity"] or 0)
                _unit = row_obj["unit"] or "ks"
                _unit_price = float(row_obj["unit_price"] or 0)
                _vat_rate = float(row_obj["vat_rate"] or 0)
                _total_price = float(row_obj["total_price"] or 0)

                # součty (stabilně)
                total_with_vat += _total_price
                base = _total_price / (1 + (_vat_rate / 100)) if _vat_rate else _total_price
                total_without_vat += base

                row = self.table.rowCount()
                self.table.insertRow(row)

                # Typ
                self.table.setItem(row, 0, QTableWidgetItem(_type))
                # Název
                self.table.setItem(row, 1, QTableWidgetItem(_name))
                # Množství
                self.table.setItem(row, 2, QTableWidgetItem(f"{_qty:.2f}"))
                # Jednotka
                self.table.setItem(row, 3, QTableWidgetItem(_unit))

                # Cena/jedn. (zarovnání vpravo)
                it_unit_price = QTableWidgetItem(f"{_unit_price:.2f} Kč")
                it_unit_price.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 4, it_unit_price)

                # DPH %
                it_vat = QTableWidgetItem(f"{_vat_rate:.0f}%")
                it_vat.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 5, it_vat)

                # Cena celkem
                it_total = QTableWidgetItem(f"{_total_price:.2f} Kč")
                it_total.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 6, it_total)

                # ID (skryté)
                self.table.setItem(row, 7, QTableWidgetItem(str(_id)))

            total_with_vat = _safe_round(total_with_vat, 2)
            total_without_vat = _safe_round(total_without_vat, 2)

            # Aktualizace souhrnu
            self.lbl_summary.setText(
                f"Celkem: {total_with_vat:.2f} Kč (bez DPH: {total_without_vat:.2f} Kč)"
            )

            # Aktualizace celkové ceny v zakázce
            db.execute_query(
                "UPDATE orders SET total_price = ? WHERE id = ?",
                [total_with_vat, self.order_id]
            )

            # Automatické přizpůsobení šířky
            for i in range(7):
                self.table.resizeColumnToContents(i)

            self.items_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při načítání položek:\n{str(e)}")

    def add_item(self, item_type):
        """Přidání položky"""
        dialog = ItemDialog(self.order_id, item_type=item_type, parent=self)
        if dialog.exec():
            self.load_items()

    def edit_item(self):
        """Editace položky"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        item_id = int(self.table.item(current_row, 7).text())
        dialog = ItemDialog(self.order_id, item_id=item_id, parent=self)
        if dialog.exec():
            self.load_items()

    def delete_item(self):
        """Smazání položky"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Varování", "Vyberte položku ke smazání!")
            return

        item_name = self.table.item(current_row, 1).text()
        item_id = int(self.table.item(current_row, 7).text())

        reply = QMessageBox.question(
            self,
            "Potvrzení",
            f"Opravdu chcete smazat položku '{item_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                db.execute_query("DELETE FROM order_items WHERE id = ?", [item_id])
                self.load_items()
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Chyba při mazání:\n{str(e)}")


class ItemDialog(QDialog):
    """Dialog pro přidání/editaci položky"""

    def __init__(self, order_id, item_type=None, item_id=None, parent=None):
        super().__init__(parent)
        self.order_id = order_id
        self.item_type = item_type
        self.item_id = item_id
        self.is_edit_mode = item_id is not None

        self.setWindowTitle("Upravit položku" if self.is_edit_mode else f"Nová položka - {item_type}")
        self.setModal(True)
        self.setMinimumWidth(500)

        self.init_ui()

        if self.is_edit_mode:
            self.load_item_data()
        else:
            # přepočet výchozí ceny (0) s DPH 21%
            self.calculate_total()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # Formulář
        form = QFormLayout()

        # Typ položky
        self.combo_type = QComboBox()
        self.combo_type.addItems(["Díl", "Práce", "Ostatní"])
        if self.item_type:
            self.combo_type.setCurrentText(self.item_type)
        form.addRow("Typ:", self.combo_type)

        # Název
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Název položky...")
        form.addRow("Název:", self.input_name)

        # Množství
        self.spin_quantity = QDoubleSpinBox()
        self.spin_quantity.setRange(0.01, 9999.99)
        self.spin_quantity.setValue(1.0)
        self.spin_quantity.setDecimals(2)
        self.spin_quantity.valueChanged.connect(self.calculate_total)
        form.addRow("Množství:", self.spin_quantity)

        # Jednotka
        self.combo_unit = QComboBox()
        self.combo_unit.addItems(["ks", "hod", "m", "l", "kg", "m²", "set"])
        self.combo_unit.setEditable(True)
        form.addRow("Jednotka:", self.combo_unit)

        # Cena za jednotku (bez DPH)
        self.spin_unit_price = QDoubleSpinBox()
        self.spin_unit_price.setRange(0, 999999.99)
        self.spin_unit_price.setDecimals(2)
        self.spin_unit_price.setSuffix(" Kč")
        self.spin_unit_price.valueChanged.connect(self.calculate_total)
        form.addRow("Cena/jedn. (bez DPH):", self.spin_unit_price)

        # DPH
        self.combo_vat = QComboBox()
        self.combo_vat.addItems(["21%", "15%", "12%", "0%"])
        self.combo_vat.setCurrentText("21%")
        self.combo_vat.currentTextChanged.connect(self.calculate_total)
        form.addRow("Sazba DPH:", self.combo_vat)

        # Cena celkem (vypočtená)
        self.lbl_total_no_vat = QLabel("0.00 Kč")
        self.lbl_total_no_vat.setStyleSheet("font-weight: bold;")
        form.addRow("Cena bez DPH:", self.lbl_total_no_vat)

        self.lbl_vat_amount = QLabel("0.00 Kč")
        form.addRow("DPH:", self.lbl_vat_amount)

        self.lbl_total_with_vat = QLabel("0.00 Kč")
        self.lbl_total_with_vat.setStyleSheet("font-weight: bold; font-size: 16px; color: #27ae60;")
        form.addRow("Cena s DPH:", self.lbl_total_with_vat)

        layout.addLayout(form)

        # Tlačítka
        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Uložit")
        btn_save.clicked.connect(self.save_item)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 10px 30px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }}
        """)

        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

    def _current_vat_rate(self) -> float:
        """Získá sazbu DPH jako číslo (např. '21%' -> 21.0)."""
        try:
            return float(self.combo_vat.currentText().rstrip('%'))
        except Exception:
            return 0.0

    def calculate_total(self):
        """Výpočet celkové ceny"""
        quantity = float(self.spin_quantity.value())
        unit_price = float(self.spin_unit_price.value())
        vat_rate = self._current_vat_rate()

        total_no_vat = _safe_round(quantity * unit_price, 2)
        vat_amount = _safe_round(total_no_vat * (vat_rate / 100), 2)
        total_with_vat = _safe_round(total_no_vat + vat_amount, 2)

        self.lbl_total_no_vat.setText(f"{total_no_vat:.2f} Kč")
        self.lbl_vat_amount.setText(f"{vat_amount:.2f} Kč")
        self.lbl_total_with_vat.setText(f"{total_with_vat:.2f} Kč")

    def load_item_data(self):
        """Načtení dat položky (kompatibilně přes COALESCE)"""
        try:
            item_rows = db.execute_query(
                """
                SELECT
                    item_type,
                    COALESCE(name, item_name) AS display_name,
                    quantity, unit, unit_price, vat_rate
                FROM order_items
                WHERE id = ?
                """,
                [self.item_id]
            )
            if item_rows:
                it = item_rows[0]
                self.combo_type.setCurrentText(it["item_type"] or "Díl")
                self.input_name.setText(it["display_name"] or "")
                self.spin_quantity.setValue(float(it["quantity"] or 1))
                self.combo_unit.setCurrentText(it["unit"] or "ks")
                self.spin_unit_price.setValue(float(it["unit_price"] or 0))
                self.combo_vat.setCurrentText(f"{float(it['vat_rate'] or 21):.0f}%")
                self.calculate_total()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při načítání položky:\n{str(e)}")

    def save_item(self):
        """Uložení položky (synchronizuje name i item_name)"""
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Varování", "Vyplňte název položky!")
            return

        try:
            item_type = self.combo_type.currentText()
            quantity = float(self.spin_quantity.value())
            unit = self.combo_unit.currentText().strip() or "ks"
            unit_price = float(self.spin_unit_price.value())
            vat_rate = self._current_vat_rate()

            # Výpočet celkové ceny s DPH
            total_no_vat = _safe_round(quantity * unit_price, 2)
            total_price = _safe_round(total_no_vat * (1 + vat_rate / 100), 2)

            if self.is_edit_mode:
                db.execute_query(
                    """
                    UPDATE order_items SET
                        item_type = ?,
                        name = ?,            -- pro nové UI
                        item_name = ?,       -- pro starší náhledy/exporty
                        quantity = ?,
                        unit = ?,
                        unit_price = ?,
                        vat_rate = ?,
                        total_price = ?
                    WHERE id = ?
                    """,
                    [item_type, name, name, quantity, unit, unit_price, vat_rate, total_price, self.item_id]
                )
            else:
                db.execute_query(
                    """
                    INSERT INTO order_items
                        (order_id, item_type, name, item_name, quantity, unit,
                         unit_price, vat_rate, total_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [self.order_id, item_type, name, name, quantity, unit, unit_price, vat_rate, total_price]
                )

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při ukládání:\n{str(e)}")
