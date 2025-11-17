# customer_vehicles.py
# -*- coding: utf-8 -*-
"""
Widget pro zobrazení vozidel zákazníka
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QBrush, QCursor
import config
from database_manager import db
from datetime import datetime, date


class CustomerVehiclesWidget(QWidget):
    """Widget pro správu vozidel zákazníka"""

    vehicle_selected = pyqtSignal(int)

    def __init__(self, customer_id):
        super().__init__()
        self.customer_id = customer_id
        self.init_ui()
        self.load_vehicles()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Hlavička
        header = QHBoxLayout()

        title = QLabel("🏍️ Vozidla zákazníka")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header.addWidget(title)

        header.addStretch()

        btn_add = QPushButton("➕ Přidat vozidlo")
        btn_add.setObjectName("btnSuccess")
        btn_add.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_add.clicked.connect(self.add_vehicle)
        header.addWidget(btn_add)

        btn_refresh = QPushButton("🔄 Obnovit")
        btn_refresh.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_refresh.clicked.connect(self.load_vehicles)
        header.addWidget(btn_refresh)

        layout.addLayout(header)

        # Statistiky
        self.create_statistics(layout)

        # Tabulka
        self.create_table(layout)

        self.set_styles()

    def create_statistics(self, parent_layout):
        """Vytvoření statistik"""
        stats_frame = QFrame()
        stats_frame.setObjectName("statsFrame")
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(20)

        self.stat_labels = {}

        for key, name in [
            ("total", "Celkem vozidel"),
            ("active", "Aktivních"),
            ("valid_stk", "Platná STK"),
            ("invalid_stk", "Neplatná STK")
        ]:
            stat_widget = QFrame()
            stat_widget.setObjectName("statCard")
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(10, 5, 10, 5)

            value_label = QLabel("0")
            value_label.setObjectName("statValue")
            value_font = QFont()
            value_font.setPointSize(18)
            value_font.setBold(True)
            value_label.setFont(value_font)
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            name_label = QLabel(name)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")

            stat_layout.addWidget(value_label)
            stat_layout.addWidget(name_label)

            self.stat_labels[key] = value_label
            stats_layout.addWidget(stat_widget)

        stats_layout.addStretch()
        parent_layout.addWidget(stats_frame)

    def create_table(self, parent_layout):
        """Vytvoření tabulky"""
        self.table = QTableWidget()
        self.table.setObjectName("vehiclesTable")

        columns = [
            "ID", "SPZ", "Značka", "Model", "Rok", "Barva",
            "STK do", "Zakázek", "Poslední servis", "Útrata", "Akce"
        ]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)

        self.table.setColumnHidden(0, True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)

        self.table.doubleClicked.connect(self.open_vehicle_detail)

        parent_layout.addWidget(self.table)

    def load_vehicles(self):
        """Načtení vozidel"""
        try:
            query = """
                SELECT
                    v.id,
                    v.license_plate,
                    v.brand,
                    v.model,
                    v.year,
                    v.color,
                    v.stk_valid_until,
                    (SELECT COUNT(*) FROM orders WHERE vehicle_id = v.id) as order_count,
                    (SELECT MAX(created_at) FROM orders WHERE vehicle_id = v.id) as last_service,
                    (SELECT COALESCE(SUM(total_price), 0) FROM orders WHERE vehicle_id = v.id) as total_spent
                FROM vehicles v
                WHERE v.customer_id = ? AND v.is_active = 1
                ORDER BY v.license_plate
            """

            vehicles = db.fetch_all(query, (self.customer_id,))
            self.populate_table(vehicles if vehicles else [])
            self.update_statistics(vehicles if vehicles else [])

        except Exception as e:
            print(f"Chyba při načítání vozidel: {e}")
            self.populate_table([])

    def populate_table(self, vehicles):
        """Naplnění tabulky"""
        self.table.setRowCount(0)

        for vehicle in vehicles:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(vehicle[0])))

            # SPZ
            spz_item = QTableWidgetItem(str(vehicle[1] or ""))
            spz_font = QFont()
            spz_font.setBold(True)
            spz_item.setFont(spz_font)
            self.table.setItem(row, 1, spz_item)

            # Značka
            self.table.setItem(row, 2, QTableWidgetItem(str(vehicle[2] or "")))

            # Model
            self.table.setItem(row, 3, QTableWidgetItem(str(vehicle[3] or "")))

            # Rok
            year_item = QTableWidgetItem(str(vehicle[4] or ""))
            year_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, year_item)

            # Barva
            self.table.setItem(row, 5, QTableWidgetItem(str(vehicle[5] or "")))

            # STK do
            stk_date = vehicle[6]
            stk_item = QTableWidgetItem("")
            if stk_date:
                try:
                    if isinstance(stk_date, str):
                        stk_dt = datetime.fromisoformat(stk_date).date()
                    else:
                        stk_dt = stk_date
                    stk_item.setText(stk_dt.strftime("%d.%m.%Y"))

                    # Barevné označení
                    today = date.today()
                    if stk_dt < today:
                        stk_item.setBackground(QBrush(QColor("#ffcccc")))  # Červená - neplatná
                    elif (stk_dt - today).days < 30:
                        stk_item.setBackground(QBrush(QColor("#fff3cd")))  # Žlutá - brzy vyprší
                    else:
                        stk_item.setBackground(QBrush(QColor("#d4edda")))  # Zelená - platná
                except:
                    pass
            stk_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, stk_item)

            # Počet zakázek
            orders_item = QTableWidgetItem(str(vehicle[7] or 0))
            orders_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 7, orders_item)

            # Poslední servis
            last_service = vehicle[8] or ""
            if last_service:
                try:
                    dt = datetime.fromisoformat(last_service)
                    last_service = dt.strftime("%d.%m.%Y")
                except:
                    pass
            self.table.setItem(row, 8, QTableWidgetItem(last_service))

            # Útrata
            spent = vehicle[9] or 0
            spent_item = QTableWidgetItem(f"{spent:,.0f} Kč".replace(",", " "))
            spent_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 9, spent_item)

            # Akce - prázdné, pro tlačítka
            self.table.setItem(row, 10, QTableWidgetItem(""))

    def update_statistics(self, vehicles):
        """Aktualizace statistik"""
        total = len(vehicles)
        valid_stk = 0
        invalid_stk = 0
        active = 0

        today = date.today()

        for vehicle in vehicles:
            # STK
            stk_date = vehicle[6]
            if stk_date:
                try:
                    if isinstance(stk_date, str):
                        stk_dt = datetime.fromisoformat(stk_date).date()
                    else:
                        stk_dt = stk_date

                    if stk_dt >= today:
                        valid_stk += 1
                    else:
                        invalid_stk += 1
                except:
                    pass

            # Aktivní (měl servis za poslední rok)
            if vehicle[7] and vehicle[7] > 0:
                active += 1

        self.stat_labels["total"].setText(str(total))
        self.stat_labels["active"].setText(str(active))
        self.stat_labels["valid_stk"].setText(str(valid_stk))
        self.stat_labels["invalid_stk"].setText(str(invalid_stk))

        # Barevné označení neplatných STK
        if invalid_stk > 0:
            self.stat_labels["invalid_stk"].setStyleSheet("color: #e74c3c; font-weight: bold;")

    def add_vehicle(self):
        """Přidání nového vozidla"""
        QMessageBox.information(
            self,
            "Přidat vozidlo",
            f"Přidání vozidla pro zákazníka ID: {self.customer_id}"
        )

    def open_vehicle_detail(self):
        """Otevření detailu vozidla"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            vehicle_id = int(self.table.item(current_row, 0).text())
            self.vehicle_selected.emit(vehicle_id)
            QMessageBox.information(self, "Detail", f"Otevření detailu vozidla ID: {vehicle_id}")

    def create_order_for_vehicle(self, vehicle_id):
        """Vytvoření zakázky pro vozidlo"""
        QMessageBox.information(
            self,
            "Nová zakázka",
            f"Vytvoření zakázky pro vozidlo ID: {vehicle_id}"
        )

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet(f"""
            #statsFrame {{
                background-color: transparent;
            }}
            #statCard {{
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                min-width: 100px;
            }}
            #statValue {{
                color: {config.COLOR_PRIMARY};
            }}
            #vehiclesTable {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                gridline-color: #e0e0e0;
            }}
            #vehiclesTable::item {{
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
        """)
