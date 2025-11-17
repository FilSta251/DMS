# customer_orders.py
# -*- coding: utf-8 -*-
"""
Widget pro zobrazení zakázek zákazníka
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QComboBox, QMessageBox, QAbstractItemView, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QBrush, QCursor
import config
from database_manager import db
from datetime import datetime, timedelta


class CustomerOrdersWidget(QWidget):
    """Widget pro správu zakázek zákazníka"""

    order_selected = pyqtSignal(int)

    def __init__(self, customer_id):
        super().__init__()
        self.customer_id = customer_id
        self.init_ui()
        self.load_orders()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Hlavička
        self.create_header(layout)

        # Filtry
        self.create_filters(layout)

        # Souhrn
        self.create_summary(layout)

        # Tabulka
        self.create_table(layout)

        self.set_styles()

    def create_header(self, parent_layout):
        """Vytvoření hlavičky"""
        header = QHBoxLayout()

        title = QLabel("📋 Historie zakázek")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header.addWidget(title)

        header.addStretch()

        btn_new = QPushButton("➕ Nová zakázka")
        btn_new.setObjectName("btnSuccess")
        btn_new.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_new.clicked.connect(self.create_new_order)
        header.addWidget(btn_new)

        btn_export = QPushButton("📤 Export")
        btn_export.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_export.clicked.connect(self.export_history)
        header.addWidget(btn_export)

        parent_layout.addLayout(header)

    def create_filters(self, parent_layout):
        """Vytvoření filtrů"""
        filters_frame = QFrame()
        filters_frame.setObjectName("filtersFrame")
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setSpacing(10)

        # Období
        filters_layout.addWidget(QLabel("Období:"))
        self.cb_period = QComboBox()
        self.cb_period.addItems(["Vše", "Tento rok", "Poslední 2 roky", "Posledních 6 měsíců"])
        self.cb_period.currentTextChanged.connect(self.filter_orders)
        filters_layout.addWidget(self.cb_period)

        # Stav
        filters_layout.addWidget(QLabel("Stav:"))
        self.cb_status = QComboBox()
        self.cb_status.addItems(["Vše", "V přípravě", "Otevřená", "Rozpracovaná", "Dokončené"])
        self.cb_status.currentTextChanged.connect(self.filter_orders)
        filters_layout.addWidget(self.cb_status)

        # Vozidlo
        filters_layout.addWidget(QLabel("Vozidlo:"))
        self.cb_vehicle = QComboBox()
        self.cb_vehicle.addItem("Vše")
        self.load_vehicles_filter()
        self.cb_vehicle.currentTextChanged.connect(self.filter_orders)
        filters_layout.addWidget(self.cb_vehicle)

        filters_layout.addStretch()

        btn_reset = QPushButton("🔄 Reset")
        btn_reset.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_reset.clicked.connect(self.reset_filters)
        filters_layout.addWidget(btn_reset)

        parent_layout.addWidget(filters_frame)

    def create_summary(self, parent_layout):
        """Vytvoření souhrnu"""
        summary_frame = QFrame()
        summary_frame.setObjectName("summaryFrame")
        summary_layout = QHBoxLayout(summary_frame)
        summary_layout.setSpacing(30)

        self.summary_labels = {}

        for key, name in [
            ("count", "Celkem zakázek"),
            ("total", "Celková útrata"),
            ("average", "Průměrná cena"),
            ("common_type", "Nejčastější typ")
        ]:
            item_layout = QVBoxLayout()

            value_label = QLabel("0")
            value_font = QFont()
            value_font.setPointSize(16)
            value_font.setBold(True)
            value_label.setFont(value_font)
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            name_label = QLabel(name)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setStyleSheet("color: #7f8c8d;")

            item_layout.addWidget(value_label)
            item_layout.addWidget(name_label)

            self.summary_labels[key] = value_label
            summary_layout.addLayout(item_layout)

        summary_layout.addStretch()
        parent_layout.addWidget(summary_frame)

    def create_table(self, parent_layout):
        """Vytvoření tabulky"""
        self.table = QTableWidget()
        self.table.setObjectName("ordersTable")

        columns = [
            "ID", "Číslo zakázky", "Datum", "Typ", "Vozidlo",
            "Stav", "Položek", "Cena bez DPH", "Cena s DPH", "Poznámka"
        ]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)

        self.table.setColumnHidden(0, True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Stretch)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)

        self.table.doubleClicked.connect(self.open_order_detail)

        parent_layout.addWidget(self.table)

    def load_vehicles_filter(self):
        """Načtení vozidel do filtru"""
        try:
            vehicles = db.fetch_all(
                "SELECT license_plate FROM vehicles WHERE customer_id = ? AND is_active = 1",
                (self.customer_id,)
            )
            if vehicles:
                for vehicle in vehicles:
                    self.cb_vehicle.addItem(vehicle[0])
        except Exception as e:
            print(f"Chyba při načítání vozidel: {e}")

    def load_orders(self):
        """Načtení zakázek"""
        try:
            query = """
                SELECT
                    o.id,
                    o.order_number,
                    o.created_at,
                    o.order_type,
                    v.license_plate,
                    o.status,
                    (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) as item_count,
                    o.total_price_without_vat,
                    o.total_price,
                    o.notes
                FROM orders o
                LEFT JOIN vehicles v ON o.vehicle_id = v.id
                WHERE o.customer_id = ?
                ORDER BY o.created_at DESC
            """

            orders = db.fetch_all(query, (self.customer_id,))
            self.all_orders = orders if orders else []
            self.populate_table(self.all_orders)
            self.update_summary(self.all_orders)

        except Exception as e:
            print(f"Chyba při načítání zakázek: {e}")
            self.all_orders = []
            self.populate_table([])

    def populate_table(self, orders):
        """Naplnění tabulky"""
        self.table.setRowCount(0)

        for order in orders:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(order[0])))

            # Číslo zakázky
            order_num_item = QTableWidgetItem(str(order[1] or ""))
            order_num_font = QFont()
            order_num_font.setBold(True)
            order_num_item.setFont(order_num_font)
            self.table.setItem(row, 1, order_num_item)

            # Datum
            date_str = order[2] or ""
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str)
                    date_str = dt.strftime("%d.%m.%Y")
                except:
                    pass
            self.table.setItem(row, 2, QTableWidgetItem(date_str))

            # Typ
            self.table.setItem(row, 3, QTableWidgetItem(str(order[3] or "")))

            # Vozidlo
            self.table.setItem(row, 4, QTableWidgetItem(str(order[4] or "")))

            # Stav (barevný badge)
            status = str(order[5] or "")
            status_item = QTableWidgetItem(status)
            status_color = config.ORDER_STATUS_COLORS.get(status, "#95a5a6")
            status_item.setBackground(QBrush(QColor(status_color)))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, status_item)

            # Počet položek
            items_item = QTableWidgetItem(str(order[6] or 0))
            items_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, items_item)

            # Cena bez DPH
            price_no_vat = order[7] or 0
            price_no_vat_item = QTableWidgetItem(f"{price_no_vat:,.0f} Kč".replace(",", " "))
            price_no_vat_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 7, price_no_vat_item)

            # Cena s DPH
            price_vat = order[8] or 0
            price_vat_item = QTableWidgetItem(f"{price_vat:,.0f} Kč".replace(",", " "))
            price_vat_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            price_vat_font = QFont()
            price_vat_font.setBold(True)
            price_vat_item.setFont(price_vat_font)
            self.table.setItem(row, 8, price_vat_item)

            # Poznámka
            notes = str(order[9] or "")
            if len(notes) > 50:
                notes = notes[:50] + "..."
            self.table.setItem(row, 9, QTableWidgetItem(notes))

    def update_summary(self, orders):
        """Aktualizace souhrnu"""
        count = len(orders)
        total = sum(order[8] or 0 for order in orders)
        average = total / count if count > 0 else 0

        # Nejčastější typ
        types = {}
        for order in orders:
            order_type = order[3] or "Neznámý"
            types[order_type] = types.get(order_type, 0) + 1

        common_type = max(types, key=types.get) if types else "-"

        self.summary_labels["count"].setText(str(count))
        self.summary_labels["total"].setText(f"{total:,.0f} Kč".replace(",", " "))
        self.summary_labels["average"].setText(f"{average:,.0f} Kč".replace(",", " "))
        self.summary_labels["common_type"].setText(common_type)

    def filter_orders(self):
        """Filtrování zakázek"""
        period = self.cb_period.currentText()
        status = self.cb_status.currentText()
        vehicle = self.cb_vehicle.currentText()

        filtered = self.all_orders

        # Filtr období
        if period != "Vše":
            now = datetime.now()
            if period == "Tento rok":
                start_date = datetime(now.year, 1, 1)
            elif period == "Poslední 2 roky":
                start_date = now - timedelta(days=730)
            elif period == "Posledních 6 měsíců":
                start_date = now - timedelta(days=180)
            else:
                start_date = None

            if start_date:
                new_filtered = []
                for order in filtered:
                    if order[2]:
                        try:
                            order_date = datetime.fromisoformat(order[2])
                            if order_date >= start_date:
                                new_filtered.append(order)
                        except:
                            pass
                filtered = new_filtered

        # Filtr stavu
        if status != "Vše":
            filtered = [o for o in filtered if o[5] == status]

        # Filtr vozidla
        if vehicle != "Vše":
            filtered = [o for o in filtered if o[4] == vehicle]

        self.populate_table(filtered)
        self.update_summary(filtered)

    def reset_filters(self):
        """Reset filtrů"""
        self.cb_period.setCurrentIndex(0)
        self.cb_status.setCurrentIndex(0)
        self.cb_vehicle.setCurrentIndex(0)
        self.populate_table(self.all_orders)
        self.update_summary(self.all_orders)

    def create_new_order(self):
        """Vytvoření nové zakázky"""
        QMessageBox.information(
            self,
            "Nová zakázka",
            f"Vytvoření zakázky pro zákazníka ID: {self.customer_id}"
        )

    def open_order_detail(self):
        """Otevření detailu zakázky"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            order_id = int(self.table.item(current_row, 0).text())
            self.order_selected.emit(order_id)
            QMessageBox.information(self, "Detail", f"Otevření detailu zakázky ID: {order_id}")

    def export_history(self):
        """Export historie do PDF/Excel"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export historie zakázek",
            f"zakazky_zakaznik_{self.customer_id}.xlsx",
            "Excel soubory (*.xlsx);;PDF soubory (*.pdf)"
        )
        if file_path:
            QMessageBox.information(self, "Export", f"Export do: {file_path}")

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet(f"""
            #filtersFrame {{
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 10px;
            }}
            #summaryFrame {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 15px;
            }}
            #ordersTable {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                gridline-color: #e0e0e0;
            }}
            #ordersTable::item {{
                padding: 8px;
            }}
            QHeaderView::section {{
                background-color: {config.COLOR_PRIMARY};
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
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
