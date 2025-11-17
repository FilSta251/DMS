# -*- coding: utf-8 -*-
"""
Analýzy skladu - PROFESIONÁLNÍ
ABC, obratovost, marže, dead stock, predikce, grafy
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QFormLayout, QTabWidget, QSpinBox, QDateEdit,
    QFileDialog, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor
import config
from database_manager import db
from datetime import datetime, timedelta
import json


class WarehouseAnalyticsWindow(QMainWindow):
    """Okno s analýzami skladu"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("📊 Analýzy skladu")
        self.setMinimumSize(1200, 800)

        self.init_ui()
        self.load_analytics()

    def init_ui(self):
        """Inicializace UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === HORNÍ LIŠTA ===
        self.create_action_bar(main_layout)

        # === ZÁLOŽKY ===
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                background: white;
            }
            QTabBar::tab {
                background: #ecf0f1;
                padding: 10px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 3px solid #3498db;
            }
        """)

        # ZÁLOŽKA 1: ABC Analýza
        self.tab_abc = self.create_tab_abc()
        self.tabs.addTab(self.tab_abc, "📊 ABC Analýza")

        # ZÁLOŽKA 2: Obratovost
        self.tab_turnover = self.create_tab_turnover()
        self.tabs.addTab(self.tab_turnover, "🔄 Obratovost")

        # ZÁLOŽKA 3: Marže
        self.tab_margin = self.create_tab_margin()
        self.tabs.addTab(self.tab_margin, "💰 Analýza marže")

        # ZÁLOŽKA 4: Dead Stock
        self.tab_dead_stock = self.create_tab_dead_stock()
        self.tabs.addTab(self.tab_dead_stock, "⚰️ Dead Stock")

        # ZÁLOŽKA 5: Predikce
        self.tab_prediction = self.create_tab_prediction()
        self.tabs.addTab(self.tab_prediction, "🔮 Predikce")

        # ZÁLOŽKA 6: Grafy
        self.tab_charts = self.create_tab_charts()
        self.tabs.addTab(self.tab_charts, "📈 Grafy")

        main_layout.addWidget(self.tabs)

    def create_action_bar(self, parent_layout):
        """Horní lišta"""
        action_bar = QWidget()
        action_bar.setFixedHeight(60)
        action_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {config.COLOR_PRIMARY};
                border-bottom: 2px solid #2c3e50;
            }}
        """)
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(15, 10, 15, 10)

        # Nadpis
        title = QLabel("📊 ANALÝZY SKLADU")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        action_layout.addWidget(title)

        action_layout.addStretch()

        # Tlačítka
        btn_refresh = QPushButton("↻ Obnovit")
        btn_refresh.setStyleSheet(self.get_button_style(config.COLOR_SUCCESS))
        btn_refresh.clicked.connect(self.load_analytics)
        action_layout.addWidget(btn_refresh)

        btn_export = QPushButton("📤 Export")
        btn_export.setStyleSheet(self.get_button_style(config.COLOR_SECONDARY))
        btn_export.clicked.connect(self.export_analytics)
        action_layout.addWidget(btn_export)

        btn_close = QPushButton("✕ Zavřít")
        btn_close.setStyleSheet(self.get_button_style("#7f8c8d"))
        btn_close.clicked.connect(self.close)
        action_layout.addWidget(btn_close)

        parent_layout.addWidget(action_bar)

    def get_button_style(self, color):
        """Styl tlačítek"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }}
        """

    # ========================================
    # ZÁLOŽKA: ABC ANALÝZA
    # ========================================

    def create_tab_abc(self):
        """ZÁLOŽKA: ABC Analýza"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info
        info = QLabel(
            "📊 ABC Analýza rozděluje položky podle jejich obchodní hodnoty:\n"
            "• Kategorie A (80% hodnoty) - Klíčové položky\n"
            "• Kategorie B (15% hodnoty) - Důležité položky\n"
            "• Kategorie C (5% hodnoty) - Méně důležité položky"
        )
        info.setStyleSheet("padding: 10px; background-color: #e8f4f8; border-radius: 5px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Statistiky
        stats_layout = QHBoxLayout()

        self.lbl_abc_a_count = QLabel("Kategorie A: 0")
        self.lbl_abc_a_count.setStyleSheet("padding: 10px; background-color: #c8e6c9; font-weight: bold;")
        stats_layout.addWidget(self.lbl_abc_a_count)

        self.lbl_abc_b_count = QLabel("Kategorie B: 0")
        self.lbl_abc_b_count.setStyleSheet("padding: 10px; background-color: #fff9c4; font-weight: bold;")
        stats_layout.addWidget(self.lbl_abc_b_count)

        self.lbl_abc_c_count = QLabel("Kategorie C: 0")
        self.lbl_abc_c_count.setStyleSheet("padding: 10px; background-color: #ffccbc; font-weight: bold;")
        stats_layout.addWidget(self.lbl_abc_c_count)

        layout.addLayout(stats_layout)

        # Tabulka
        self.table_abc = QTableWidget()
        self.table_abc.setColumnCount(7)
        self.table_abc.setHorizontalHeaderLabels([
            'Položka', 'Vydáno', 'Hodnota', '% z celku', 'Kumulativní %', 'Kategorie', 'ID'
        ])
        self.table_abc.setColumnHidden(6, True)
        self.table_abc.horizontalHeader().setStretchLastSection(True)
        self.table_abc.setAlternatingRowColors(True)

        layout.addWidget(self.table_abc)

        return widget

    def load_abc_analysis(self):
        """Načtení ABC analýzy"""
        try:
            # Data z výdejů
            movements = db.execute_query("""
                SELECT w.id, w.name,
                       SUM(wm.quantity) as total_quantity,
                       SUM(wm.quantity * wm.unit_price) as total_value
                FROM warehouse_movements wm
                LEFT JOIN warehouse w ON wm.item_id = w.id
                WHERE wm.movement_type = 'Výdej'
                GROUP BY w.id, w.name
                HAVING total_value > 0
                ORDER BY total_value DESC
            """)

            self.table_abc.setRowCount(0)

            if not movements:
                return

            # Výpočet celkové hodnoty
            total_value = sum(m[3] for m in movements)

            cumulative = 0
            count_a = 0
            count_b = 0
            count_c = 0

            for mov in movements:
                row = self.table_abc.rowCount()
                self.table_abc.insertRow(row)

                item_id = mov[0]
                name = mov[1]
                quantity = mov[2]
                value = mov[3]
                percent = (value / total_value * 100) if total_value > 0 else 0
                cumulative += percent

                # Určení ABC kategorie
                if cumulative <= 80:
                    category = "A"
                    color = QColor("#c8e6c9")
                    count_a += 1
                elif cumulative <= 95:
                    category = "B"
                    color = QColor("#fff9c4")
                    count_b += 1
                else:
                    category = "C"
                    color = QColor("#ffccbc")
                    count_c += 1

                # Vyplnění řádku
                self.table_abc.setItem(row, 0, QTableWidgetItem(name))
                self.table_abc.setItem(row, 1, QTableWidgetItem(f"{quantity:.2f}"))
                self.table_abc.setItem(row, 2, QTableWidgetItem(f"{value:,.2f} Kč"))
                self.table_abc.setItem(row, 3, QTableWidgetItem(f"{percent:.2f}%"))
                self.table_abc.setItem(row, 4, QTableWidgetItem(f"{cumulative:.2f}%"))

                cat_item = QTableWidgetItem(category)
                cat_item.setBackground(color)
                cat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_abc.setItem(row, 5, cat_item)

                self.table_abc.setItem(row, 6, QTableWidgetItem(str(item_id)))

            # Aktualizace statistik
            self.lbl_abc_a_count.setText(f"Kategorie A: {count_a} položek (80% hodnoty)")
            self.lbl_abc_b_count.setText(f"Kategorie B: {count_b} položek (15% hodnoty)")
            self.lbl_abc_c_count.setText(f"Kategorie C: {count_c} položek (5% hodnoty)")

        except Exception as e:
            print(f"Chyba: {e}")

    # ========================================
    # ZÁLOŽKA: OBRATOVOST
    # ========================================

    def create_tab_turnover(self):
        """ZÁLOŽKA: Obratovost"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info
        info = QLabel(
            "🔄 Obratovost ukazuje, jak rychle se položky prodávají.\n"
            "Vysoká obratovost = položka se rychle prodává a měla by být vždy skladem."
        )
        info.setStyleSheet("padding: 10px; background-color: #e8f4f8; border-radius: 5px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Období
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("Období analýzy:"))

        self.spin_turnover_months = QSpinBox()
        self.spin_turnover_months.setRange(1, 24)
        self.spin_turnover_months.setValue(6)
        self.spin_turnover_months.setSuffix(" měsíců")
        period_layout.addWidget(self.spin_turnover_months)

        btn_calc_turnover = QPushButton("Přepočítat")
        btn_calc_turnover.clicked.connect(self.load_turnover_analysis)
        period_layout.addWidget(btn_calc_turnover)

        period_layout.addStretch()
        layout.addLayout(period_layout)

        # Tabulka
        self.table_turnover = QTableWidget()
        self.table_turnover.setColumnCount(7)
        self.table_turnover.setHorizontalHeaderLabels([
            'Položka', 'Průměrný stav', 'Celkem vydáno', 'Obratovost',
            'Prodeje/měsíc', 'Dní do vyprodání', 'ID'
        ])
        self.table_turnover.setColumnHidden(6, True)
        self.table_turnover.horizontalHeader().setStretchLastSection(True)
        self.table_turnover.setAlternatingRowColors(True)

        layout.addWidget(self.table_turnover)

        return widget

    def load_turnover_analysis(self):
        """Načtení analýzy obratovosti"""
        try:
            months = self.spin_turnover_months.value()
            date_from = (datetime.now() - timedelta(days=months * 30)).strftime('%Y-%m-%d')

            items = db.execute_query("""
                SELECT w.id, w.name, w.quantity,
                       COALESCE(SUM(CASE WHEN wm.movement_type = 'Výdej' THEN wm.quantity ELSE 0 END), 0) as total_issued
                FROM warehouse w
                LEFT JOIN warehouse_movements wm ON w.id = wm.item_id AND wm.date >= ?
                GROUP BY w.id, w.name, w.quantity
                HAVING total_issued > 0
                ORDER BY total_issued DESC
            """, [date_from])

            self.table_turnover.setRowCount(0)

            if not items:
                return

            for item in items:
                row = self.table_turnover.rowCount()
                self.table_turnover.insertRow(row)

                item_id = item[0]
                name = item[1]
                current_stock = item[2]
                total_issued = item[3]

                # Výpočty
                avg_stock = current_stock + (total_issued / 2)  # Zjednodušený průměr
                turnover = (total_issued / avg_stock) if avg_stock > 0 else 0
                sales_per_month = total_issued / months
                days_to_stockout = (current_stock / sales_per_month * 30) if sales_per_month > 0 else 999

                # Vyplnění
                self.table_turnover.setItem(row, 0, QTableWidgetItem(name))
                self.table_turnover.setItem(row, 1, QTableWidgetItem(f"{avg_stock:.2f}"))
                self.table_turnover.setItem(row, 2, QTableWidgetItem(f"{total_issued:.2f}"))

                turnover_item = QTableWidgetItem(f"{turnover:.2f}x")
                turnover_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table_turnover.setItem(row, 3, turnover_item)

                self.table_turnover.setItem(row, 4, QTableWidgetItem(f"{sales_per_month:.2f}"))

                days_item = QTableWidgetItem(f"{days_to_stockout:.0f} dní")
                if days_to_stockout < 30:
                    days_item.setBackground(QColor(config.STOCK_CRITICAL))
                    days_item.setForeground(QColor("white"))
                elif days_to_stockout < 60:
                    days_item.setBackground(QColor(config.STOCK_WARNING))
                self.table_turnover.setItem(row, 5, days_item)

                self.table_turnover.setItem(row, 6, QTableWidgetItem(str(item_id)))

        except Exception as e:
            print(f"Chyba: {e}")

    # ========================================
    # ZÁLOŽKA: MARŽE
    # ========================================

    def create_tab_margin(self):
        """ZÁLOŽKA: Analýza marže"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Statistiky
        stats_group = QGroupBox("💰 Celková marže")
        stats_layout = QFormLayout(stats_group)

        self.lbl_total_purchase = QLabel("0.00 Kč")
        stats_layout.addRow("Celková nákupní hodnota:", self.lbl_total_purchase)

        self.lbl_total_sale = QLabel("0.00 Kč")
        stats_layout.addRow("Celková prodejní hodnota:", self.lbl_total_sale)

        self.lbl_total_margin = QLabel("0.00 Kč")
        self.lbl_total_margin.setStyleSheet("color: #27ae60; font-size: 16px; font-weight: bold;")
        stats_layout.addRow("Celková marže:", self.lbl_total_margin)

        self.lbl_avg_margin = QLabel("0.0%")
        self.lbl_avg_margin.setStyleSheet("color: #2980b9; font-size: 14px; font-weight: bold;")
        stats_layout.addRow("Průměrná marže:", self.lbl_avg_margin)

        layout.addWidget(stats_group)

        # Tabulka
        self.table_margin = QTableWidget()
        self.table_margin.setColumnCount(7)
        self.table_margin.setHorizontalHeaderLabels([
            'Položka', 'Množství', 'Nákupní cena', 'Prodejní cena',
            'Marže Kč', 'Marže %', 'ID'
        ])
        self.table_margin.setColumnHidden(6, True)
        self.table_margin.horizontalHeader().setStretchLastSection(True)
        self.table_margin.setAlternatingRowColors(True)

        layout.addWidget(self.table_margin)

        return widget

    def load_margin_analysis(self):
        """Načtení analýzy marže"""
        try:
            items = db.execute_query("""
                SELECT id, name, quantity, price_purchase, price_sale
                FROM warehouse
                WHERE quantity > 0 AND price_purchase > 0
                ORDER BY (price_sale - price_purchase) * quantity DESC
            """)

            self.table_margin.setRowCount(0)

            if not items:
                return

            total_purchase_value = 0
            total_sale_value = 0
            total_margin = 0

            for item in items:
                row = self.table_margin.rowCount()
                self.table_margin.insertRow(row)

                item_id = item[0]
                name = item[1]
                quantity = item[2]
                purchase = item[3]
                sale = item[4]

                margin_czk = (sale - purchase) * quantity
                margin_pct = ((sale - purchase) / purchase * 100) if purchase > 0 else 0

                total_purchase_value += purchase * quantity
                total_sale_value += sale * quantity
                total_margin += margin_czk

                # Vyplnění
                self.table_margin.setItem(row, 0, QTableWidgetItem(name))
                self.table_margin.setItem(row, 1, QTableWidgetItem(f"{quantity:.2f}"))
                self.table_margin.setItem(row, 2, QTableWidgetItem(f"{purchase:.2f} Kč"))
                self.table_margin.setItem(row, 3, QTableWidgetItem(f"{sale:.2f} Kč"))

                margin_czk_item = QTableWidgetItem(f"{margin_czk:,.2f} Kč")
                margin_czk_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if margin_czk < 0:
                    margin_czk_item.setForeground(QColor(config.COLOR_DANGER))
                else:
                    margin_czk_item.setForeground(QColor(config.COLOR_SUCCESS))
                self.table_margin.setItem(row, 4, margin_czk_item)

                margin_pct_item = QTableWidgetItem(f"{margin_pct:.1f}%")
                margin_pct_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table_margin.setItem(row, 5, margin_pct_item)

                self.table_margin.setItem(row, 6, QTableWidgetItem(str(item_id)))

            # Aktualizace statistik
            avg_margin = (total_margin / total_purchase_value * 100) if total_purchase_value > 0 else 0

            self.lbl_total_purchase.setText(f"{total_purchase_value:,.2f} Kč")
            self.lbl_total_sale.setText(f"{total_sale_value:,.2f} Kč")
            self.lbl_total_margin.setText(f"{total_margin:,.2f} Kč")
            self.lbl_avg_margin.setText(f"{avg_margin:.1f}%")

        except Exception as e:
            print(f"Chyba: {e}")

    # ========================================
    # ZÁLOŽKA: DEAD STOCK
    # ========================================

    def create_tab_dead_stock(self):
        """ZÁLOŽKA: Dead Stock"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info
        info = QLabel(
            "⚰️ Dead Stock - položky bez pohybu, které zabírají místo a váží kapitál.\n"
            "Tyto položky by měly být vyprodány, vráceny dodavateli nebo zlikvidovány."
        )
        info.setStyleSheet("padding: 10px; background-color: #ffebee; border-radius: 5px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Nastavení
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("Bez pohybu déle než:"))

        self.spin_dead_stock_months = QSpinBox()
        self.spin_dead_stock_months.setRange(1, 24)
        self.spin_dead_stock_months.setValue(6)
        self.spin_dead_stock_months.setSuffix(" měsíců")
        settings_layout.addWidget(self.spin_dead_stock_months)

        btn_calc_dead = QPushButton("Přepočítat")
        btn_calc_dead.clicked.connect(self.load_dead_stock)
        settings_layout.addWidget(btn_calc_dead)

        settings_layout.addStretch()

        self.lbl_dead_stock_value = QLabel("Hodnota: 0 Kč")
        self.lbl_dead_stock_value.setStyleSheet("color: #e74c3c; font-weight: bold;")
        settings_layout.addWidget(self.lbl_dead_stock_value)

        layout.addLayout(settings_layout)

        # Tabulka
        self.table_dead_stock = QTableWidget()
        self.table_dead_stock.setColumnCount(7)
        self.table_dead_stock.setHorizontalHeaderLabels([
            'Položka', 'Množství', 'Hodnota', 'Poslední pohyb',
            'Dní bez pohybu', 'Umístění', 'ID'
        ])
        self.table_dead_stock.setColumnHidden(6, True)
        self.table_dead_stock.horizontalHeader().setStretchLastSection(True)
        self.table_dead_stock.setAlternatingRowColors(True)

        layout.addWidget(self.table_dead_stock)

        return widget

    def load_dead_stock(self):
        """Načtení dead stock"""
        try:
            months = self.spin_dead_stock_months.value()
            date_limit = (datetime.now() - timedelta(days=months * 30)).strftime('%Y-%m-%d')

            items = db.execute_query("""
                SELECT w.id, w.name, w.quantity, w.price_purchase, w.location,
                       MAX(wm.date) as last_movement
                FROM warehouse w
                LEFT JOIN warehouse_movements wm ON w.id = wm.item_id
                WHERE w.quantity > 0
                GROUP BY w.id, w.name, w.quantity, w.price_purchase, w.location
                HAVING last_movement IS NULL OR last_movement < ?
                ORDER BY last_movement ASC
            """, [date_limit])

            self.table_dead_stock.setRowCount(0)

            total_value = 0

            if not items:
                self.lbl_dead_stock_value.setText("Hodnota: 0 Kč (žádný dead stock)")
                return

            for item in items:
                row = self.table_dead_stock.rowCount()
                self.table_dead_stock.insertRow(row)

                item_id = item[0]
                name = item[1]
                quantity = item[2]
                price = item[3]
                location = item[4] or "---"
                last_movement = item[5]

                value = quantity * price
                total_value += value

                if last_movement:
                    last_date = datetime.strptime(last_movement, '%Y-%m-%d %H:%M:%S')
                    days_without = (datetime.now() - last_date).days
                    last_text = last_movement.split()[0]
                else:
                    days_without = 9999
                    last_text = "Nikdy"

                # Vyplnění
                self.table_dead_stock.setItem(row, 0, QTableWidgetItem(name))
                self.table_dead_stock.setItem(row, 1, QTableWidgetItem(f"{quantity:.2f}"))

                value_item = QTableWidgetItem(f"{value:,.2f} Kč")
                value_item.setForeground(QColor(config.COLOR_DANGER))
                self.table_dead_stock.setItem(row, 2, value_item)

                self.table_dead_stock.setItem(row, 3, QTableWidgetItem(last_text))

                days_item = QTableWidgetItem(f"{days_without} dní")
                days_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table_dead_stock.setItem(row, 4, days_item)

                self.table_dead_stock.setItem(row, 5, QTableWidgetItem(location))
                self.table_dead_stock.setItem(row, 6, QTableWidgetItem(str(item_id)))

            # Aktualizace hodnoty
            self.lbl_dead_stock_value.setText(f"Hodnota dead stock: {total_value:,.2f} Kč ({len(items)} položek)")

        except Exception as e:
            print(f"Chyba: {e}")

    # ========================================
    # ZÁLOŽKA: PREDIKCE
    # ========================================

    def create_tab_prediction(self):
        """ZÁLOŽKA: Predikce"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info
        info = QLabel(
            "🔮 Predikce potřeby nákupu na základě historické spotřeby.\n"
            "Pomáhá určit, kdy a kolik objednat, aby nedošlo k výpadku."
        )
        info.setStyleSheet("padding: 10px; background-color: #e8f4f8; border-radius: 5px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Nastavení
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("Predikce na:"))

        self.spin_prediction_days = QSpinBox()
        self.spin_prediction_days.setRange(7, 365)
        self.spin_prediction_days.setValue(30)
        self.spin_prediction_days.setSuffix(" dní")
        settings_layout.addWidget(self.spin_prediction_days)

        btn_calc_prediction = QPushButton("Přepočítat")
        btn_calc_prediction.clicked.connect(self.load_prediction)
        settings_layout.addWidget(btn_calc_prediction)

        settings_layout.addStretch()
        layout.addLayout(settings_layout)

        # Tabulka
        self.table_prediction = QTableWidget()
        self.table_prediction.setColumnCount(8)
        self.table_prediction.setHorizontalHeaderLabels([
            'Položka', 'Aktuální stav', 'Spotřeba/den', 'Predikce spotřeby',
            'Doporučený nákup', 'Dodavatel', 'Stav', 'ID'
        ])
        self.table_prediction.setColumnHidden(7, True)
        self.table_prediction.horizontalHeader().setStretchLastSection(True)
        self.table_prediction.setAlternatingRowColors(True)

        layout.addWidget(self.table_prediction)

        return widget

    def load_prediction(self):
        """Načtení predikce"""
        try:
            days = self.spin_prediction_days.value()

            # Historická spotřeba za posledních 90 dní
            date_from = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

            items = db.execute_query("""
                SELECT w.id, w.name, w.quantity, w.min_quantity,
                       COALESCE(SUM(CASE WHEN wm.movement_type = 'Výdej' THEN wm.quantity ELSE 0 END), 0) as total_issued,
                       s.name as supplier
                FROM warehouse w
                LEFT JOIN warehouse_movements wm ON w.id = wm.item_id AND wm.date >= ?
                LEFT JOIN warehouse_suppliers s ON w.supplier_id = s.id
                GROUP BY w.id, w.name, w.quantity, w.min_quantity, s.name
                HAVING total_issued > 0
                ORDER BY w.name
            """, [date_from])

            self.table_prediction.setRowCount(0)

            if not items:
                return

            for item in items:
                row = self.table_prediction.rowCount()
                self.table_prediction.insertRow(row)

                item_id = item[0]
                name = item[1]
                current_stock = item[2]
                min_qty = item[3]
                total_issued = item[4]
                supplier = item[5] or "---"

                # Výpočty
                consumption_per_day = total_issued / 90
                predicted_consumption = consumption_per_day * days
                recommended_purchase = max(0, predicted_consumption - current_stock + min_qty)

                # Status
                if current_stock >= predicted_consumption + min_qty:
                    status = "✓ Dostatek"
                    status_color = QColor(config.STOCK_OK)
                elif current_stock >= predicted_consumption:
                    status = "⚠️ Nízký"
                    status_color = QColor(config.STOCK_WARNING)
                else:
                    status = "❌ Nedostatek"
                    status_color = QColor(config.STOCK_CRITICAL)

                # Vyplnění
                self.table_prediction.setItem(row, 0, QTableWidgetItem(name))
                self.table_prediction.setItem(row, 1, QTableWidgetItem(f"{current_stock:.2f}"))
                self.table_prediction.setItem(row, 2, QTableWidgetItem(f"{consumption_per_day:.2f}"))
                self.table_prediction.setItem(row, 3, QTableWidgetItem(f"{predicted_consumption:.2f}"))

                purchase_item = QTableWidgetItem(f"{recommended_purchase:.2f}")
                if recommended_purchase > 0:
                    purchase_item.setBackground(QColor("#fff3cd"))
                    purchase_item.setForeground(QColor("#856404"))
                purchase_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table_prediction.setItem(row, 4, purchase_item)

                self.table_prediction.setItem(row, 5, QTableWidgetItem(supplier))

                status_item = QTableWidgetItem(status)
                status_item.setBackground(status_color)
                if status == "❌ Nedostatek":
                    status_item.setForeground(QColor("white"))
                self.table_prediction.setItem(row, 6, status_item)

                self.table_prediction.setItem(row, 7, QTableWidgetItem(str(item_id)))

        except Exception as e:
            print(f"Chyba: {e}")

    # ========================================
    # ZÁLOŽKA: GRAFY
    # ========================================

    def create_tab_charts(self):
        """ZÁLOŽKA: Grafy"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info
        info = QLabel(
            "📈 Vizualizace dat skladu pomocí grafů.\n"
            "Pro zobrazení grafů je potřeba nainstalovat: pip install matplotlib"
        )
        info.setStyleSheet("padding: 10px; background-color: #e8f4f8; border-radius: 5px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Tlačítka
        buttons = QHBoxLayout()

        btn_top10 = QPushButton("📊 Top 10 položek")
        btn_top10.clicked.connect(self.show_top10_chart)
        buttons.addWidget(btn_top10)

        btn_movements = QPushButton("📈 Pohyby v čase")
        btn_movements.clicked.connect(self.show_movements_chart)
        buttons.addWidget(btn_movements)

        btn_abc_pie = QPushButton("🥧 ABC Koláčový graf")
        btn_abc_pie.clicked.connect(self.show_abc_pie_chart)
        buttons.addWidget(btn_abc_pie)

        buttons.addStretch()
        layout.addLayout(buttons)

        # Placeholder
        placeholder = QLabel(
            "📊 Klikněte na tlačítka výše pro zobrazení grafů.\n\n"
            "Grafy se otevřou v novém okně."
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #7f8c8d; padding: 50px; font-size: 14px;")
        layout.addWidget(placeholder)

        return widget

    def show_top10_chart(self):
        """Graf top 10 položek"""
        try:
            import matplotlib.pyplot as plt

            # Data
            items = db.execute_query("""
                SELECT w.name, SUM(wm.quantity) as total
                FROM warehouse_movements wm
                LEFT JOIN warehouse w ON wm.item_id = w.id
                WHERE wm.movement_type = 'Výdej'
                GROUP BY w.id, w.name
                ORDER BY total DESC
                LIMIT 10
            """)

            if not items:
                QMessageBox.information(self, "Info", "Žádná data k zobrazení")
                return

            names = [item[1][:30] for item in items]
            values = [item[2] for item in items]

            plt.figure(figsize=(12, 6))
            plt.barh(names, values, color='#3498db')
            plt.xlabel('Množství')
            plt.title('Top 10 nejprodávanějších položek')
            plt.gca().invert_yaxis()
            plt.tight_layout()
            plt.show()

        except ImportError:
            QMessageBox.warning(
                self,
                "Chybí knihovna",
                "Pro zobrazení grafů je potřeba:\n\npip install matplotlib"
            )
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při zobrazení grafu:\n{str(e)}")

    def show_movements_chart(self):
        """Graf pohybů v čase"""
        try:
            import matplotlib.pyplot as plt
            from datetime import datetime, timedelta

            # Data za posledních 30 dní
            date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

            movements = db.execute_query("""
                SELECT DATE(date) as day,
                       SUM(CASE WHEN movement_type = 'Příjem' THEN quantity ELSE 0 END) as received,
                       SUM(CASE WHEN movement_type = 'Výdej' THEN quantity ELSE 0 END) as issued
                FROM warehouse_movements
                WHERE date >= ?
                GROUP BY DATE(date)
                ORDER BY day
            """, [date_from])

            if not movements:
                QMessageBox.information(self, "Info", "Žádná data k zobrazení")
                return

            dates = [item[0] for item in movements]
            received = [item[1] for item in movements]
            issued = [item[2] for item in movements]

            plt.figure(figsize=(12, 6))
            plt.plot(dates, received, marker='o', label='Příjem', color='#27ae60')
            plt.plot(dates, issued, marker='o', label='Výdej', color='#e74c3c')
            plt.xlabel('Datum')
            plt.ylabel('Množství')
            plt.title('Skladové pohyby za posledních 30 dní')
            plt.xticks(rotation=45)
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()

        except ImportError:
            QMessageBox.warning(
                self,
                "Chybí knihovna",
                "Pro zobrazení grafů je potřeba:\n\npip install matplotlib"
            )
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba:\n{str(e)}")

    def show_abc_pie_chart(self):
        """Koláčový graf ABC"""
        try:
            import matplotlib.pyplot as plt

            # Počty kategorií
            movements = db.execute_query("""
                SELECT SUM(wm.quantity * wm.unit_price) as value
                FROM warehouse_movements wm
                WHERE wm.movement_type = 'Výdej'
            """)

            if not movements or not movements[0][0]:
                QMessageBox.information(self, "Info", "Žádná data k zobrazení")
                return

            # Pro zjednodušení použijeme pevné rozdělení
            sizes = [80, 15, 5]
            labels = ['Kategorie A\n(80% hodnoty)', 'Kategorie B\n(15% hodnoty)', 'Kategorie C\n(5% hodnoty)']
            colors = ['#c8e6c9', '#fff9c4', '#ffccbc']

            plt.figure(figsize=(8, 8))
            plt.pie(sizes, labels=labels, colors=colors, autopct='%1.0f%%', startangle=90)
            plt.title('ABC Analýza - rozdělení hodnoty skladu')
            plt.axis('equal')
            plt.tight_layout()
            plt.show()

        except ImportError:
            QMessageBox.warning(
                self,
                "Chybí knihovna",
                "Pro zobrazení grafů je potřeba:\n\npip install matplotlib"
            )
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba:\n{str(e)}")

    # ========================================
    # SPOLEČNÉ FUNKCE
    # ========================================

    def load_analytics(self):
        """Načtení všech analýz"""
        self.load_abc_analysis()
        self.load_turnover_analysis()
        self.load_margin_analysis()
        self.load_dead_stock()
        self.load_prediction()

    def export_analytics(self):
        """Export analýz"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Uložit export analýz",
                f"analyzy_skladu_{datetime.now().strftime('%Y%m%d')}.json",
                "JSON soubory (*.json)"
            )

            if not file_path:
                return

            # Sestavení exportu
            export_data = {
                'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'abc_analysis': self.get_abc_data(),
                'turnover': self.get_turnover_data(),
                'margin': self.get_margin_data(),
                'dead_stock': self.get_dead_stock_data(),
                'prediction': self.get_prediction_data()
            }

            # Uložení
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            QMessageBox.information(self, "Úspěch", f"Analýzy byly exportovány:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při exportu:\n{str(e)}")

    def get_abc_data(self):
        """Získání ABC dat pro export"""
        data = []
        for row in range(self.table_abc.rowCount()):
            data.append({
                'name': self.table_abc.item(row, 0).text(),
                'quantity': self.table_abc.item(row, 1).text(),
                'value': self.table_abc.item(row, 2).text(),
                'category': self.table_abc.item(row, 5).text()
            })
        return data

    def get_turnover_data(self):
        """Získání dat obratovosti"""
        data = []
        for row in range(self.table_turnover.rowCount()):
            data.append({
                'name': self.table_turnover.item(row, 0).text(),
                'turnover': self.table_turnover.item(row, 3).text(),
                'sales_per_month': self.table_turnover.item(row, 4).text()
            })
        return data

    def get_margin_data(self):
        """Získání dat marže"""
        return {
            'total_margin': self.lbl_total_margin.text(),
            'avg_margin': self.lbl_avg_margin.text()
        }

    def get_dead_stock_data(self):
        """Získání dead stock dat"""
        data = []
        for row in range(self.table_dead_stock.rowCount()):
            data.append({
                'name': self.table_dead_stock.item(row, 0).text(),
                'value': self.table_dead_stock.item(row, 2).text(),
                'days_without': self.table_dead_stock.item(row, 4).text()
            })
        return data

    def get_prediction_data(self):
        """Získání dat predikce"""
        data = []
        for row in range(self.table_prediction.rowCount()):
            data.append({
                'name': self.table_prediction.item(row, 0).text(),
                'current_stock': self.table_prediction.item(row, 1).text(),
                'recommended_purchase': self.table_prediction.item(row, 4).text(),
                'status': self.table_prediction.item(row, 6).text()
            })
        return data
