# -*- coding: utf-8 -*-
"""
Analýzy zakázek - statistiky, přehledy, grafy
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
import config
from database_manager import db
from datetime import datetime, timedelta


class OrderAnalyticsWidget(QWidget):
    """Widget pro analýzy zakázek"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_analytics()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Hlavička
        header = QHBoxLayout()

        title = QLabel("📊 Analýzy zakázek")
        title.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {config.COLOR_PRIMARY};
        """)
        header.addWidget(title)
        header.addStretch()

        # Filtr období
        header.addWidget(QLabel("Období:"))
        self.combo_period = QComboBox()
        self.combo_period.addItems([
            "Tento měsíc",
            "Poslední 3 měsíce",
            "Poslední 6 měsíců",
            "Tento rok",
            "Vše"
        ])
        self.combo_period.currentTextChanged.connect(self.load_analytics)
        header.addWidget(self.combo_period)

        btn_refresh = QPushButton("🔄 Obnovit")
        btn_refresh.clicked.connect(self.load_analytics)
        btn_refresh.setStyleSheet(self.get_button_style(config.COLOR_SECONDARY))
        header.addWidget(btn_refresh)

        layout.addLayout(header)

        # Statistiky - přehledové boxy
        stats_layout = QGridLayout()

        # Box 1 - Celkový počet zakázek
        self.box_total = self.create_stat_box("📋", "Celkem zakázek", "0", config.COLOR_PRIMARY)
        stats_layout.addWidget(self.box_total, 0, 0)

        # Box 2 - Aktivní zakázky
        self.box_active = self.create_stat_box("🔄", "Aktivní zakázky", "0", config.COLOR_WARNING)
        stats_layout.addWidget(self.box_active, 0, 1)

        # Box 3 - Dokončené zakázky
        self.box_completed = self.create_stat_box("✅", "Dokončené", "0", config.COLOR_SUCCESS)
        stats_layout.addWidget(self.box_completed, 0, 2)

        # Box 4 - Celkový obrat
        self.box_revenue = self.create_stat_box("💰", "Celkový obrat", "0 Kč", config.COLOR_SECONDARY)
        stats_layout.addWidget(self.box_revenue, 1, 0)

        # Box 5 - Průměrná cena zakázky
        self.box_avg = self.create_stat_box("📊", "Průměrná cena", "0 Kč", "#9b59b6")
        stats_layout.addWidget(self.box_avg, 1, 1)

        # Box 6 - Čeká na díly
        self.box_waiting = self.create_stat_box("⏳", "Čeká na díly", "0", "#e67e22")
        stats_layout.addWidget(self.box_waiting, 1, 2)

        layout.addLayout(stats_layout)

        # Tabulky s detaily
        tables_layout = QHBoxLayout()

        # Tabulka podle typu
        type_group = QGroupBox("Zakázky podle typu")
        type_layout = QVBoxLayout(type_group)

        self.table_by_type = QTableWidget()
        self.table_by_type.setColumnCount(3)
        self.table_by_type.setHorizontalHeaderLabels(["Typ", "Počet", "Obrat"])
        self.setup_table_style(self.table_by_type)
        type_layout.addWidget(self.table_by_type)

        tables_layout.addWidget(type_group)

        # Tabulka podle stavu
        status_group = QGroupBox("Zakázky podle stavu")
        status_layout = QVBoxLayout(status_group)

        self.table_by_status = QTableWidget()
        self.table_by_status.setColumnCount(3)
        self.table_by_status.setHorizontalHeaderLabels(["Stav", "Počet", "Obrat"])
        self.setup_table_style(self.table_by_status)
        status_layout.addWidget(self.table_by_status)

        tables_layout.addWidget(status_group)

        layout.addLayout(tables_layout)

        # Top zákazníci
        customers_group = QGroupBox("Top 10 zákazníků")
        customers_layout = QVBoxLayout(customers_group)

        self.table_top_customers = QTableWidget()
        self.table_top_customers.setColumnCount(3)
        self.table_top_customers.setHorizontalHeaderLabels(["Zákazník", "Počet zakázek", "Celkový obrat"])
        self.setup_table_style(self.table_top_customers)
        customers_layout.addWidget(self.table_top_customers)

        layout.addWidget(customers_group)

    def create_stat_box(self, icon, title, value, color):
        """Vytvoření statistického boxu"""
        box = QWidget()
        box.setStyleSheet(f"""
            QWidget {{
                background-color: {color};
                border-radius: 10px;
                padding: 20px;
            }}
            QLabel {{
                color: white;
                border: none;
            }}
        """)

        layout = QVBoxLayout(box)
        layout.setSpacing(5)

        # Ikona
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 32px;")
        layout.addWidget(lbl_icon)

        # Název
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 12px; font-weight: normal;")
        layout.addWidget(lbl_title)

        # Hodnota
        lbl_value = QLabel(value)
        lbl_value.setStyleSheet("font-size: 24px; font-weight: bold;")
        lbl_value.setObjectName("value_label")
        layout.addWidget(lbl_value)

        layout.addStretch()

        return box

    def setup_table_style(self, table):
        """Nastavení stylu tabulky"""
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet("""
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

    def get_button_style(self, color):
        """Styl pro tlačítka"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """

    def get_date_filter(self):
        """Získání filtru data podle vybraného období"""
        period = self.combo_period.currentText()
        today = datetime.now()

        if period == "Tento měsíc":
            start_date = today.replace(day=1).strftime("%Y-%m-%d")
        elif period == "Poslední 3 měsíce":
            start_date = (today - timedelta(days=90)).strftime("%Y-%m-%d")
        elif period == "Poslední 6 měsíců":
            start_date = (today - timedelta(days=180)).strftime("%Y-%m-%d")
        elif period == "Tento rok":
            start_date = today.replace(month=1, day=1).strftime("%Y-%m-%d")
        else:  # Vše
            return None

        return start_date

    def load_analytics(self):
        """Načtení analytických dat"""
        try:
            start_date = self.get_date_filter()
            date_filter = f"WHERE created_date >= '{start_date}'" if start_date else ""

            # Celkový počet zakázek
            total = db.execute_query(
                f"SELECT COUNT(*) FROM orders {date_filter}"
            )[0][0]

            # Aktivní zakázky (ne Archiv ani Hotová)
            active = db.execute_query(
                f"""SELECT COUNT(*) FROM orders
                    WHERE status NOT IN ('Archiv', 'Hotová')
                    {('AND ' + date_filter.replace('WHERE ', '')) if start_date else ''}"""
            )[0][0]

            # Dokončené zakázky
            completed = db.execute_query(
                f"""SELECT COUNT(*) FROM orders
                    WHERE status = 'Hotová'
                    {('AND ' + date_filter.replace('WHERE ', '')) if start_date else ''}"""
            )[0][0]

            # Celkový obrat
            revenue = db.execute_query(
                f"""SELECT COALESCE(SUM(total_price), 0) FROM orders
                    WHERE status IN ('Hotová', 'Archiv')
                    {('AND ' + date_filter.replace('WHERE ', '')) if start_date else ''}"""
            )[0][0]

            # Průměrná cena
            avg_price = revenue / completed if completed > 0 else 0

            # Čeká na díly
            waiting = db.execute_query(
                f"""SELECT COUNT(*) FROM orders
                    WHERE status = 'Čeká na díly'
                    {('AND ' + date_filter.replace('WHERE ', '')) if start_date else ''}"""
            )[0][0]

            # Aktualizace boxů
            self.update_stat_box(self.box_total, str(total))
            self.update_stat_box(self.box_active, str(active))
            self.update_stat_box(self.box_completed, str(completed))
            self.update_stat_box(self.box_revenue, f"{revenue:,.2f} Kč")
            self.update_stat_box(self.box_avg, f"{avg_price:,.2f} Kč")
            self.update_stat_box(self.box_waiting, str(waiting))

            # Načtení tabulek
            self.load_by_type(date_filter)
            self.load_by_status(date_filter)
            self.load_top_customers(date_filter)

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při načítání analýz:\n{str(e)}")

    def update_stat_box(self, box, value):
        """Aktualizace hodnoty v statistickém boxu"""
        for child in box.findChildren(QLabel):
            if child.objectName() == "value_label":
                child.setText(value)
                break

    def load_by_type(self, date_filter):
        """Načtení statistik podle typu"""
        try:
            stats = db.execute_query(
                f"""SELECT
                    order_type,
                    COUNT(*) as count,
                    COALESCE(SUM(total_price), 0) as revenue
                FROM orders
                {date_filter}
                GROUP BY order_type
                ORDER BY count DESC"""
            )

            self.table_by_type.setRowCount(0)

            for stat in stats:
                row = self.table_by_type.rowCount()
                self.table_by_type.insertRow(row)

                self.table_by_type.setItem(row, 0, QTableWidgetItem(stat[0]))
                self.table_by_type.setItem(row, 1, QTableWidgetItem(str(stat[1])))

                revenue_item = QTableWidgetItem(f"{stat[2]:,.2f} Kč")
                revenue_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table_by_type.setItem(row, 2, revenue_item)

            self.table_by_type.resizeColumnsToContents()

        except Exception as e:
            print(f"Chyba při načítání statistik podle typu: {e}")

    def load_by_status(self, date_filter):
        """Načtení statistik podle stavu"""
        try:
            stats = db.execute_query(
                f"""SELECT
                    status,
                    COUNT(*) as count,
                    COALESCE(SUM(total_price), 0) as revenue
                FROM orders
                {date_filter}
                GROUP BY status
                ORDER BY count DESC"""
            )

            self.table_by_status.setRowCount(0)

            for stat in stats:
                row = self.table_by_status.rowCount()
                self.table_by_status.insertRow(row)

                # Stav s barevným pozadím
                status_item = QTableWidgetItem(stat[0])
                status_color = config.ORDER_STATUS_COLORS.get(stat[0], "#95a5a6")
                status_item.setBackground(QColor(status_color))
                status_item.setForeground(QColor("white"))
                self.table_by_status.setItem(row, 0, status_item)

                self.table_by_status.setItem(row, 1, QTableWidgetItem(str(stat[1])))

                revenue_item = QTableWidgetItem(f"{stat[2]:,.2f} Kč")
                revenue_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table_by_status.setItem(row, 2, revenue_item)

            self.table_by_status.resizeColumnsToContents()

        except Exception as e:
            print(f"Chyba při načítání statistik podle stavu: {e}")

    def load_top_customers(self, date_filter):
        """Načtení top zákazníků"""
        try:
            stats = db.execute_query(
                f"""SELECT
                    c.name || ' ' || c.surname as customer_name,
                    COUNT(o.id) as order_count,
                    COALESCE(SUM(o.total_price), 0) as total_revenue
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                {date_filter}
                GROUP BY o.customer_id
                ORDER BY total_revenue DESC
                LIMIT 10"""
            )

            self.table_top_customers.setRowCount(0)

            for stat in stats:
                row = self.table_top_customers.rowCount()
                self.table_top_customers.insertRow(row)

                self.table_top_customers.setItem(row, 0, QTableWidgetItem(stat[0]))

                count_item = QTableWidgetItem(str(stat[1]))
                count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_top_customers.setItem(row, 1, count_item)

                revenue_item = QTableWidgetItem(f"{stat[2]:,.2f} Kč")
                revenue_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table_top_customers.setItem(row, 2, revenue_item)

            self.table_top_customers.resizeColumnsToContents()

        except Exception as e:
            print(f"Chyba při načítání top zákazníků: {e}")
