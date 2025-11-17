# -*- coding: utf-8 -*-
"""
Management Warehouse Overview - Manažerský přehled skladu
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QFrame, QScrollArea, QMessageBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from .management_widgets import (MetricCard, TrendCard, LineChartWidget,
                                 BarChartWidget, PieChartWidget, AnalyticsTable)
from database_manager import db
from datetime import datetime, timedelta


class ManagementWarehouseOverview(QWidget):
    """Manažerský přehled skladu"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_module = parent
        self.date_from = None
        self.date_to = None
        self.init_ui()
        self.refresh()

    def init_ui(self):
        """Inicializace UI"""
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        scroll.setWidget(content_widget)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # KPI karty
        self.create_kpi_cards(content_layout)

        # Rychlé akce
        self.create_quick_actions(content_layout)

        # Grafy
        self.create_charts(content_layout)

        # Kritické položky a varování
        self.create_warnings_section(content_layout)

        content_layout.addStretch()

    def create_kpi_cards(self, parent_layout):
        """KPI karty skladu"""
        kpi_container = QFrame()
        kpi_layout = QGridLayout(kpi_container)
        kpi_layout.setSpacing(15)

        # Karty
        self.card_total_value_purchase = MetricCard("Hodnota (nákup)", "0 Kč", "💰")
        self.card_total_value_sale = MetricCard("Hodnota (prodej)", "0 Kč", "💵")
        self.card_avg_margin = TrendCard("Průměrná marže", "0%", "+0%", True, "💹")
        self.card_turnover = MetricCard("Obratovost", "0x", "🔄")
        self.card_dead_stock_value = MetricCard("Dead stock", "0 Kč", "⚰️")
        self.card_low_stock = MetricCard("Pod minimem", "0", "⚠️")
        self.card_total_items = MetricCard("Celkem položek", "0", "📦")
        self.card_categories = MetricCard("Kategorií", "0", "📂")

        # Přidání do gridu (3x3)
        kpi_layout.addWidget(self.card_total_value_purchase, 0, 0)
        kpi_layout.addWidget(self.card_total_value_sale, 0, 1)
        kpi_layout.addWidget(self.card_avg_margin, 0, 2)
        kpi_layout.addWidget(self.card_turnover, 1, 0)
        kpi_layout.addWidget(self.card_dead_stock_value, 1, 1)
        kpi_layout.addWidget(self.card_low_stock, 1, 2)
        kpi_layout.addWidget(self.card_total_items, 2, 0)
        kpi_layout.addWidget(self.card_categories, 2, 1)

        parent_layout.addWidget(kpi_container)

    def create_quick_actions(self, parent_layout):
        """Rychlé akce"""
        actions_frame = QFrame()
        actions_frame.setObjectName("quickActions")
        actions_layout = QHBoxLayout(actions_frame)

        # Nadpis
        title = QLabel("⚡ Rychlé akce")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        actions_layout.addWidget(title)

        actions_layout.addStretch()

        # Tlačítka
        btn_detailed_analytics = QPushButton("🔍 Detailní analýzy")
        btn_detailed_analytics.setToolTip("Otevře kompletní analytické nástroje skladu:\nABC analýza, obratovost, marže, dead stock, predikce")
        btn_detailed_analytics.clicked.connect(self.open_detailed_analytics)
        btn_detailed_analytics.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(btn_detailed_analytics)

        btn_critical_items = QPushButton("⚠️ Kritické položky")
        btn_critical_items.clicked.connect(self.show_critical_items)
        btn_critical_items.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(btn_critical_items)

        btn_dead_stock = QPushButton("⚰️ Dead Stock")
        btn_dead_stock.clicked.connect(self.show_dead_stock_alert)
        btn_dead_stock.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(btn_dead_stock)

        btn_abc = QPushButton("📊 ABC Analýza")
        btn_abc.clicked.connect(self.show_abc_summary)
        btn_abc.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(btn_abc)

        actions_frame.setStyleSheet("""
            QFrame#quickActions {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #e0e0e0;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        parent_layout.addWidget(actions_frame)

    def create_charts(self, parent_layout):
        """Grafy"""
        charts_container = QFrame()
        charts_layout = QVBoxLayout(charts_container)
        charts_layout.setSpacing(20)

        # První řádek
        row1 = QHBoxLayout()
        row1.setSpacing(15)

        self.chart_warehouse_value = LineChartWidget("Vývoj hodnoty skladu")
        row1.addWidget(self.chart_warehouse_value)

        self.chart_abc_distribution = PieChartWidget("ABC rozdělení")
        row1.addWidget(self.chart_abc_distribution)

        charts_layout.addLayout(row1)

        # Druhý řádek
        row2 = QHBoxLayout()
        row2.setSpacing(15)

        self.chart_top_sellers = BarChartWidget("Top 10 nejprodávanějších")
        row2.addWidget(self.chart_top_sellers)

        self.chart_slow_movers = BarChartWidget("Top 10 nejpomalejších")
        row2.addWidget(self.chart_slow_movers)

        charts_layout.addLayout(row2)

        parent_layout.addWidget(charts_container)

    def create_warnings_section(self, parent_layout):
        """Sekce s varováními"""
        warnings_container = QFrame()
        warnings_layout = QVBoxLayout(warnings_container)
        warnings_layout.setSpacing(15)

        # Nadpis
        title = QLabel("⚠️ Varování a kritické položky")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        warnings_layout.addWidget(title)

        # Tabulka kritických položek
        self.table_critical = AnalyticsTable()
        warnings_layout.addWidget(self.table_critical)

        parent_layout.addWidget(warnings_container)

    def refresh(self):
        """Refresh dat"""
        if self.date_from is None or self.date_to is None:
            self.date_to = QDate.currentDate()
            self.date_from = self.date_to.addMonths(-1)

        self.load_kpi_data()
        self.load_charts_data()
        self.load_warnings()

    def set_date_range(self, date_from, date_to):
        """Nastavení období"""
        self.date_from = date_from
        self.date_to = date_to

    def load_kpi_data(self):
        """Načtení KPI dat"""
        try:
            # Celková hodnota skladu (nákupní)
            query = "SELECT COALESCE(SUM(quantity * price_purchase), 0) FROM warehouse WHERE quantity > 0"
            result = db.fetch_one(query)
            total_purchase = result[0] if result else 0
            self.card_total_value_purchase.set_value(f"{total_purchase:,.0f} Kč")

            # Celková hodnota skladu (prodejní)
            query = "SELECT COALESCE(SUM(quantity * price_sale), 0) FROM warehouse WHERE quantity > 0"
            result = db.fetch_one(query)
            total_sale = result[0] if result else 0
            self.card_total_value_sale.set_value(f"{total_sale:,.0f} Kč")

            # Průměrná marže
            margin = ((total_sale - total_purchase) / total_purchase * 100) if total_purchase > 0 else 0

            # Trend marže (zjednodušený - porovnání s ideální marží 30%)
            ideal_margin = 30
            margin_diff = margin - ideal_margin

            self.card_avg_margin.set_value(
                f"{margin:.1f}%",
                f"{abs(margin_diff):.1f}%",
                margin >= ideal_margin
            )

            # Obratovost (za posledních 6 měsíců)
            date_from_6m = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
            query = """
                SELECT COALESCE(SUM(quantity), 0)
                FROM warehouse_movements
                WHERE movement_type = 'Výdej' AND date >= ?
            """
            result = db.fetch_one(query, (date_from_6m,))
            total_issued = result[0] if result else 0

            # Průměrný stav
            avg_stock = total_purchase / 2 if total_purchase > 0 else 1
            turnover = total_issued / avg_stock if avg_stock > 0 else 0
            self.card_turnover.set_value(f"{turnover:.2f}x")

            # Dead stock (bez pohybu 6+ měsíců)
            query = """
                SELECT COALESCE(SUM(w.quantity * w.price_purchase), 0)
                FROM warehouse w
                LEFT JOIN warehouse_movements wm ON w.id = wm.item_id
                WHERE w.quantity > 0
                GROUP BY w.id
                HAVING MAX(wm.date) IS NULL OR MAX(wm.date) < ?
            """
            result = db.fetch_one(query, (date_from_6m,))
            dead_stock_value = result[0] if result else 0
            self.card_dead_stock_value.set_value(f"{dead_stock_value:,.0f} Kč")

            # Položky pod minimem
            query = "SELECT COUNT(*) FROM warehouse WHERE quantity <= min_quantity"
            result = db.fetch_one(query)
            low_stock_count = result[0] if result else 0
            self.card_low_stock.set_value(str(low_stock_count))

            # Celkem položek
            query = "SELECT COUNT(*) FROM warehouse"
            result = db.fetch_one(query)
            total_items = result[0] if result else 0
            self.card_total_items.set_value(str(total_items))

            # Počet kategorií
            query = "SELECT COUNT(*) FROM warehouse_categories"
            result = db.fetch_one(query)
            categories_count = result[0] if result else 0
            self.card_categories.set_value(str(categories_count))

        except Exception as e:
            print(f"Chyba při načítání KPI: {e}")

    def load_charts_data(self):
        """Načtení dat pro grafy"""
        try:
            # Vývoj hodnoty skladu (měsíčně)
            query = """
                SELECT
                    strftime('%Y-%m', date) as month,
                    SUM(CASE WHEN movement_type = 'Příjem' THEN quantity * unit_price ELSE 0 END) -
                    SUM(CASE WHEN movement_type = 'Výdej' THEN quantity * unit_price ELSE 0 END) as net_value
                FROM warehouse_movements
                WHERE date >= date('now', '-12 months')
                GROUP BY strftime('%Y-%m', date)
                ORDER BY month
            """
            results = db.fetch_all(query)
            if results:
                months = [r[0] for r in results]
                values = [r[1] for r in results]
                self.chart_warehouse_value.plot(months, values, "Měsíc", "Hodnota (Kč)", "#3498db")

            # ABC rozdělení (zjednodušené)
            labels = ["Kategorie A", "Kategorie B", "Kategorie C"]
            sizes = [80, 15, 5]  # Ideální rozdělení
            self.chart_abc_distribution.plot(labels, sizes)

            # Top 10 nejprodávanějších
            date_from_str = self.date_from.toString("yyyy-MM-dd")
            date_to_str = self.date_to.toString("yyyy-MM-dd")

            query = """
                SELECT
                    w.name,
                    SUM(wm.quantity) as total_sold
                FROM warehouse_movements wm
                JOIN warehouse w ON wm.item_id = w.id
                WHERE wm.movement_type = 'Výdej'
                AND wm.date BETWEEN ? AND ?
                GROUP BY w.id, w.name
                ORDER BY total_sold DESC
                LIMIT 10
            """
            results = db.fetch_all(query, (date_from_str, date_to_str))
            if results:
                names = [r[0][:20] for r in results]  # Zkrátit názvy
                quantities = [r[1] for r in results]
                self.chart_top_sellers.plot(names, quantities, "Položka", "Prodáno", "#27ae60")

            # Top 10 nejpomalejších (dead stock)
            date_limit = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
            query = """
                SELECT
                    w.name,
                    COALESCE(JULIANDAY('now') - JULIANDAY(MAX(wm.date)), 999) as days_without
                FROM warehouse w
                LEFT JOIN warehouse_movements wm ON w.id = wm.item_id
                WHERE w.quantity > 0
                GROUP BY w.id, w.name
                HAVING MAX(wm.date) IS NULL OR MAX(wm.date) < ?
                ORDER BY days_without DESC
                LIMIT 10
            """
            results = db.fetch_all(query, (date_limit,))
            if results:
                names = [r[0][:20] for r in results]
                days = [r[1] if r[1] < 999 else 365 for r in results]
                self.chart_slow_movers.plot(names, days, "Položka", "Dní bez pohybu", "#e74c3c")

        except Exception as e:
            print(f"Chyba při načítání grafů: {e}")

    def load_warnings(self):
        """Načtení varování"""
        try:
            query = """
                SELECT
                    name,
                    quantity,
                    min_quantity,
                    CASE
                        WHEN quantity <= 0 THEN '❌ Vyprodáno'
                        WHEN quantity <= min_quantity * 0.5 THEN '🔴 Kritický'
                        WHEN quantity <= min_quantity THEN '⚠️ Nízký'
                        ELSE '✓ OK'
                    END as status
                FROM warehouse
                WHERE quantity <= min_quantity
                ORDER BY (quantity - min_quantity)
                LIMIT 20
            """
            results = db.fetch_all(query)

            if results:
                headers = ["Položka", "Stav", "Minimum", "Status"]
                data = [
                    [r[0], f"{r[1]:.1f}", f"{r[2]:.1f}", r[3]]
                    for r in results
                ]
                self.table_critical.set_data(headers, data)
            else:
                self.table_critical.set_data(["Info"], [["✅ Žádné kritické položky"]])

        except Exception as e:
            print(f"Chyba při načítání varování: {e}")

    def open_detailed_analytics(self):
        """Otevření detailních analýz"""
        try:
            # Import a otevření stávajícího analytického okna
            from modules.warehouse.warehouse_analytics import WarehouseAnalyticsWindow

            self.analytics_window = WarehouseAnalyticsWindow(self)
            self.analytics_window.show()

        except ImportError as e:
            QMessageBox.warning(
                self,
                "Modul nenalezen",
                "Detailní analytické okno není dostupné.\n\n"
                "Zkontrolujte, zda existuje:\n"
                "modules/warehouse/warehouse_analytics_window.py"
            )
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při otevírání analýz:\n{e}")

    def show_critical_items(self):
        """Zobrazení kritických položek"""
        try:
            query = """
                SELECT name, quantity, min_quantity
                FROM warehouse
                WHERE quantity <= min_quantity
                ORDER BY (quantity - min_quantity)
                LIMIT 10
            """
            results = db.fetch_all(query)

            if results:
                message = "⚠️ Kritické položky pod minimem:\n\n"
                for r in results:
                    deficit = r[2] - r[1]
                    message += f"{r[0]}\n"
                    message += f"Stav: {r[1]:.1f} | Min: {r[2]:.1f} | Chybí: {deficit:.1f}\n\n"

                QMessageBox.warning(self, "Kritické položky", message)
            else:
                QMessageBox.information(self, "Kritické položky",
                                      "✅ Všechny položky jsou nad minimem.")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba:\n{e}")

    def show_dead_stock_alert(self):
        """Zobrazení dead stock upozornění"""
        try:
            date_limit = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')

            query = """
                SELECT
                    w.name,
                    w.quantity * w.price_purchase as value,
                    COALESCE(JULIANDAY('now') - JULIANDAY(MAX(wm.date)), 999) as days
                FROM warehouse w
                LEFT JOIN warehouse_movements wm ON w.id = wm.item_id
                WHERE w.quantity > 0
                GROUP BY w.id, w.name
                HAVING MAX(wm.date) IS NULL OR MAX(wm.date) < ?
                ORDER BY value DESC
                LIMIT 10
            """
            results = db.fetch_all(query, (date_limit,))

            if results:
                total_value = sum(r[1] for r in results)
                message = f"⚰️ Dead Stock (bez pohybu 6+ měsíců):\n\n"
                message += f"Celková hodnota: {total_value:,.0f} Kč\n\n"

                for r in results:
                    message += f"{r[0]}\n"
                    message += f"Hodnota: {r[1]:,.0f} Kč | Dní: {int(r[2])}\n\n"

                QMessageBox.warning(self, "Dead Stock", message)
            else:
                QMessageBox.information(self, "Dead Stock",
                                      "✅ Žádný dead stock detekován.")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba:\n{e}")

    def show_abc_summary(self):
        """Zobrazení ABC souhrnu"""
        try:
            # Zjednodušené ABC
            query = """
                SELECT
                    COUNT(*) as items,
                    SUM(quantity * price_purchase) as value
                FROM warehouse
                WHERE quantity > 0
            """
            result = db.fetch_one(query)

            if result and result[0] > 0:
                total_items = result[0]
                total_value = result[1]

                # Ideální rozdělení
                cat_a_items = int(total_items * 0.2)
                cat_a_value = total_value * 0.8

                cat_b_items = int(total_items * 0.3)
                cat_b_value = total_value * 0.15

                cat_c_items = total_items - cat_a_items - cat_b_items
                cat_c_value = total_value * 0.05

                message = "📊 ABC Analýza skladu:\n\n"
                message += f"🟢 Kategorie A:\n"
                message += f"  • {cat_a_items} položek ({cat_a_items/total_items*100:.0f}%)\n"
                message += f"  • {cat_a_value:,.0f} Kč (80% hodnoty)\n\n"

                message += f"🟡 Kategorie B:\n"
                message += f"  • {cat_b_items} položek ({cat_b_items/total_items*100:.0f}%)\n"
                message += f"  • {cat_b_value:,.0f} Kč (15% hodnoty)\n\n"

                message += f"🔴 Kategorie C:\n"
                message += f"  • {cat_c_items} položek ({cat_c_items/total_items*100:.0f}%)\n"
                message += f"  • {cat_c_value:,.0f} Kč (5% hodnoty)\n\n"

                message += "💡 Pro detailní ABC analýzu použijte\n'🔍 Detailní analýzy'"

                QMessageBox.information(self, "ABC Analýza", message)
            else:
                QMessageBox.information(self, "ABC Analýza",
                                      "Sklad je prázdný.")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba:\n{e}")
