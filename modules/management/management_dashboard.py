# -*- coding: utf-8 -*-
"""
Management Dashboard - Hlavní přehled
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QFrame, QScrollArea, QMessageBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from .management_widgets import (MetricCard, TrendCard, LineChartWidget,
                                 BarChartWidget, PieChartWidget)
from database_manager import db
from datetime import datetime, timedelta


class ManagementDashboard(QWidget):
    """Hlavní dashboard s přehledem všech klíčových metrik"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_module = parent
        self.date_from = None
        self.date_to = None
        self.init_ui()
        self.refresh()

    def init_ui(self):
        """Inicializace UI"""
        # Scroll area pro celý obsah
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

        # Metrické karty
        self.create_metric_cards(content_layout)

        # Grafy
        self.create_charts(content_layout)

        # Rychlé akce
        self.create_quick_actions(content_layout)

        content_layout.addStretch()

    def create_metric_cards(self, parent_layout):
        """Vytvoření metrikových karet"""
        # Kontejner pro karty
        cards_container = QFrame()
        cards_container.setObjectName("cardsContainer")
        cards_layout = QGridLayout(cards_container)
        cards_layout.setSpacing(15)

        # Vytvoření karet (4 řádky po 2 kartách)
        self.card_revenue = TrendCard("Celkový obrat", "0 Kč", "+0%", True, "💰")
        self.card_orders = TrendCard("Počet zakázek", "0", "+0%", True, "📋")
        self.card_avg_order = MetricCard("Průměrná zakázka", "0 Kč", "📊")
        self.card_margin = TrendCard("Marže", "0%", "+0%", True, "💹")
        self.card_hours = MetricCard("Odpracované hodiny", "0 h", "⏱️")
        self.card_mechanic_util = TrendCard("Využití mechaniků", "0%", "+0%", True, "👨‍🔧")
        self.card_warehouse_value = MetricCard("Hodnota skladu", "0 Kč", "📦")
        self.card_low_stock = MetricCard("Položky pod minimem", "0", "⚠️")

        # Přidání karet do gridu
        cards_layout.addWidget(self.card_revenue, 0, 0)
        cards_layout.addWidget(self.card_orders, 0, 1)
        cards_layout.addWidget(self.card_avg_order, 1, 0)
        cards_layout.addWidget(self.card_margin, 1, 1)
        cards_layout.addWidget(self.card_hours, 2, 0)
        cards_layout.addWidget(self.card_mechanic_util, 2, 1)
        cards_layout.addWidget(self.card_warehouse_value, 3, 0)
        cards_layout.addWidget(self.card_low_stock, 3, 1)

        parent_layout.addWidget(cards_container)

    def create_charts(self, parent_layout):
        """Vytvoření grafů"""
        # Kontejner pro grafy
        charts_container = QFrame()
        charts_layout = QVBoxLayout(charts_container)
        charts_layout.setSpacing(20)

        # První řádek - 2 grafy vedle sebe
        row1 = QHBoxLayout()
        row1.setSpacing(15)

        # Graf obratu v čase
        self.chart_revenue_trend = LineChartWidget("Obrat v čase (posledních 12 měsíců)")
        row1.addWidget(self.chart_revenue_trend)

        # Graf top 5 mechaniků
        self.chart_top_mechanics = BarChartWidget("Top 5 mechaniků podle výkonu")
        row1.addWidget(self.chart_top_mechanics)

        charts_layout.addLayout(row1)

        # Druhý řádek - 2 grafy vedle sebe
        row2 = QHBoxLayout()
        row2.setSpacing(15)

        # Graf rozdělení zakázek podle typu
        self.chart_order_types = PieChartWidget("Rozdělení zakázek podle typu")
        row2.addWidget(self.chart_order_types)

        # Graf trendů prodeje
        self.chart_sales_trend = LineChartWidget("Trendy prodeje")
        row2.addWidget(self.chart_sales_trend)

        charts_layout.addLayout(row2)

        parent_layout.addWidget(charts_container)

    def create_quick_actions(self, parent_layout):
        """Vytvoření rychlých akcí"""
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
        btn_today_orders = QPushButton("📋 Dnešní zakázky")
        btn_today_orders.clicked.connect(self.show_today_orders)
        btn_today_orders.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(btn_today_orders)

        btn_critical_stock = QPushButton("⚠️ Kritické položky")
        btn_critical_stock.clicked.connect(self.show_critical_stock)
        btn_critical_stock.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(btn_critical_stock)

        btn_pending_tasks = QPushButton("⏳ Pending úkoly")
        btn_pending_tasks.clicked.connect(self.show_pending_tasks)
        btn_pending_tasks.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(btn_pending_tasks)

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

    def refresh(self):
        """Refresh dat dashboardu"""
        if self.date_from is None or self.date_to is None:
            # Výchozí období - poslední měsíc
            self.date_to = QDate.currentDate()
            self.date_from = self.date_to.addMonths(-1)

        self.load_metrics()
        self.load_charts()

    def set_date_range(self, date_from, date_to):
        """Nastavení období"""
        self.date_from = date_from
        self.date_to = date_to

    def load_metrics(self):
        """Načtení metrik"""
        try:
            # Převod QDate na string pro SQL
            date_from_str = self.date_from.toString("yyyy-MM-dd")
            date_to_str = self.date_to.toString("yyyy-MM-dd")

            # Celkový obrat
            query_revenue = """
                SELECT COALESCE(SUM(total_price), 0) as total
                FROM orders
                WHERE order_date BETWEEN ? AND ?
                AND status != 'cancelled'
            """
            result = db.fetch_one(query_revenue, (date_from_str, date_to_str))
            total_revenue = result[0] if result else 0

            # Předchozí období pro trend
            days_diff = self.date_from.daysTo(self.date_to)
            prev_date_to = self.date_from.addDays(-1)
            prev_date_from = prev_date_to.addDays(-days_diff)

            prev_revenue_query = """
                SELECT COALESCE(SUM(total_price), 0) as total
                FROM orders
                WHERE order_date BETWEEN ? AND ?
                AND status != 'cancelled'
            """
            prev_result = db.fetch_one(prev_revenue_query,
                                      (prev_date_from.toString("yyyy-MM-dd"),
                                       prev_date_to.toString("yyyy-MM-dd")))
            prev_revenue = prev_result[0] if prev_result else 0

            # Výpočet trendu
            revenue_trend = 0
            if prev_revenue > 0:
                revenue_trend = ((total_revenue - prev_revenue) / prev_revenue) * 100

            self.card_revenue.set_value(
                f"{total_revenue:,.0f} Kč",
                f"{abs(revenue_trend):.1f}%",
                revenue_trend >= 0
            )

            # Počet zakázek
            query_orders = """
                SELECT COUNT(*) as count
                FROM orders
                WHERE order_date BETWEEN ? AND ?
                AND status != 'cancelled'
            """
            result = db.fetch_one(query_orders, (date_from_str, date_to_str))
            orders_count = result[0] if result else 0

            # Předchozí období
            prev_orders = db.fetch_one(query_orders,
                                      (prev_date_from.toString("yyyy-MM-dd"),
                                       prev_date_to.toString("yyyy-MM-dd")))
            prev_orders_count = prev_orders[0] if prev_orders else 0

            orders_trend = 0
            if prev_orders_count > 0:
                orders_trend = ((orders_count - prev_orders_count) / prev_orders_count) * 100

            self.card_orders.set_value(
                f"{orders_count}",
                f"{abs(orders_trend):.1f}%",
                orders_trend >= 0
            )

            # Průměrná hodnota zakázky
            avg_order = total_revenue / orders_count if orders_count > 0 else 0
            self.card_avg_order.set_value(f"{avg_order:,.0f} Kč")

            # Marže
            query_margin = """
                SELECT
                    COALESCE(SUM(total_price), 0) as revenue,
                    COALESCE(SUM(material_cost), 0) as costs
                FROM orders
                WHERE order_date BETWEEN ? AND ?
                AND status != 'cancelled'
            """
            result = db.fetch_one(query_margin, (date_from_str, date_to_str))
            if result:
                revenue = result[0]
                costs = result[1]
                margin = ((revenue - costs) / revenue * 100) if revenue > 0 else 0

                # Předchozí období
                prev_result = db.fetch_one(query_margin,
                                          (prev_date_from.toString("yyyy-MM-dd"),
                                           prev_date_to.toString("yyyy-MM-dd")))
                prev_margin = 0
                if prev_result and prev_result[0] > 0:
                    prev_margin = ((prev_result[0] - prev_result[1]) / prev_result[0] * 100)

                margin_trend = margin - prev_margin

                self.card_margin.set_value(
                    f"{margin:.1f}%",
                    f"{abs(margin_trend):.1f}%",
                    margin_trend >= 0
                )
            else:
                self.card_margin.set_value("0%", "0%", True)

            # Odpracované hodiny
            query_hours = """
                SELECT COALESCE(SUM(hours_worked), 0) as total_hours
                FROM order_work_log
                WHERE date BETWEEN ? AND ?
            """
            result = db.fetch_one(query_hours, (date_from_str, date_to_str))
            total_hours = result[0] if result else 0
            self.card_hours.set_value(f"{total_hours:.1f} h")

            # Využití mechaniků
            query_mechanics = """
                SELECT COUNT(DISTINCT user_id) as mechanic_count
                FROM users
                WHERE role = 'mechanic' AND active = 1
            """
            result = db.fetch_one(query_mechanics)
            mechanic_count = result[0] if result else 1

            # Pracovní dny v období
            working_days = self.calculate_working_days(self.date_from, self.date_to)
            expected_hours = mechanic_count * working_days * 8  # 8 hodin denně

            utilization = (total_hours / expected_hours * 100) if expected_hours > 0 else 0

            # Předchozí období
            prev_hours = db.fetch_one(query_hours,
                                     (prev_date_from.toString("yyyy-MM-dd"),
                                      prev_date_to.toString("yyyy-MM-dd")))
            prev_total_hours = prev_hours[0] if prev_hours else 0
            prev_working_days = self.calculate_working_days(prev_date_from, prev_date_to)
            prev_expected = mechanic_count * prev_working_days * 8
            prev_utilization = (prev_total_hours / prev_expected * 100) if prev_expected > 0 else 0

            util_trend = utilization - prev_utilization

            self.card_mechanic_util.set_value(
                f"{utilization:.1f}%",
                f"{abs(util_trend):.1f}%",
                util_trend >= 0
            )

            # Hodnota skladu
            query_warehouse = """
                SELECT COALESCE(SUM(quantity * purchase_price), 0) as value
                FROM warehouse_items
            """
            result = db.fetch_one(query_warehouse)
            warehouse_value = result[0] if result else 0
            self.card_warehouse_value.set_value(f"{warehouse_value:,.0f} Kč")

            # Položky pod minimem
            query_low_stock = """
                SELECT COUNT(*) as count
                FROM warehouse_items
                WHERE quantity <= min_quantity
            """
            result = db.fetch_one(query_low_stock)
            low_stock_count = result[0] if result else 0
            self.card_low_stock.set_value(str(low_stock_count))

        except Exception as e:
            print(f"Chyba při načítání metrik: {e}")

    def load_charts(self):
        """Načtení grafů"""
        try:
            # Graf obratu v čase (posledních 12 měsíců)
            query_revenue_trend = """
                SELECT
                    strftime('%Y-%m', order_date) as month,
                    SUM(total_price) as revenue
                FROM orders
                WHERE order_date >= date('now', '-12 months')
                AND status != 'cancelled'
                GROUP BY strftime('%Y-%m', order_date)
                ORDER BY month
            """
            results = db.fetch_all(query_revenue_trend)
            if results:
                months = [r[0] for r in results]
                revenues = [r[1] for r in results]
                self.chart_revenue_trend.plot(months, revenues, "Měsíc", "Obrat (Kč)", "#3498db")

            # Top 5 mechaniků
            date_from_str = self.date_from.toString("yyyy-MM-dd")
            date_to_str = self.date_to.toString("yyyy-MM-dd")

            query_top_mechanics = """
                SELECT
                    u.name,
                    COALESCE(SUM(wl.hours_worked), 0) as total_hours
                FROM users u
                LEFT JOIN order_work_log wl ON u.user_id = wl.user_id
                    AND wl.date BETWEEN ? AND ?
                WHERE u.role = 'mechanic' AND u.active = 1
                GROUP BY u.user_id, u.name
                ORDER BY total_hours DESC
                LIMIT 5
            """
            results = db.fetch_all(query_top_mechanics, (date_from_str, date_to_str))
            if results:
                names = [r[0] for r in results]
                hours = [r[1] for r in results]
                self.chart_top_mechanics.plot(names, hours, "Mechanik", "Hodiny", "#27ae60")

            # Rozdělení zakázek podle typu
            query_order_types = """
                SELECT
                    order_type,
                    COUNT(*) as count
                FROM orders
                WHERE order_date BETWEEN ? AND ?
                AND status != 'cancelled'
                GROUP BY order_type
            """
            results = db.fetch_all(query_order_types, (date_from_str, date_to_str))
            if results:
                type_names = {"service": "Servis", "repair": "Oprava",
                             "inspection": "Kontrola", "sale": "Prodej"}
                labels = [type_names.get(r[0], r[0]) for r in results]
                sizes = [r[1] for r in results]
                self.chart_order_types.plot(labels, sizes)

            # Trendy prodeje (týdenní)
            query_sales_trend = """
                SELECT
                    strftime('%Y-%W', order_date) as week,
                    COUNT(*) as order_count
                FROM orders
                WHERE order_date >= date('now', '-12 weeks')
                AND status != 'cancelled'
                GROUP BY strftime('%Y-%W', order_date)
                ORDER BY week
            """
            results = db.fetch_all(query_sales_trend)
            if results:
                weeks = [f"Týden {r[0][-2:]}" for r in results]
                counts = [r[1] for r in results]
                self.chart_sales_trend.plot(weeks, counts, "Týden", "Počet zakázek", "#e74c3c")

        except Exception as e:
            print(f"Chyba při načítání grafů: {e}")

    def calculate_working_days(self, date_from, date_to):
        """Výpočet pracovních dnů (pondělí-pátek)"""
        working_days = 0
        current = date_from
        while current <= date_to:
            if current.dayOfWeek() <= 5:  # 1-5 = Po-Pá
                working_days += 1
            current = current.addDays(1)
        return working_days

    def show_today_orders(self):
        """Zobrazení dnešních zakázek"""
        try:
            today = QDate.currentDate().toString("yyyy-MM-dd")
            query = """
                SELECT
                    order_id,
                    customer_name,
                    vehicle_info,
                    status,
                    total_price
                FROM orders
                WHERE order_date = ?
                ORDER BY order_id DESC
            """
            results = db.fetch_all(query, (today,))

            if results:
                message = "📋 Dnešní zakázky:\n\n"
                for r in results:
                    status_names = {
                        "new": "Nová",
                        "in_progress": "Rozpracovaná",
                        "completed": "Dokončená",
                        "cancelled": "Zrušená"
                    }
                    status = status_names.get(r[3], r[3])
                    message += f"#{r[0]} - {r[1]} ({r[2]})\n"
                    message += f"Status: {status} | Cena: {r[4]:,.0f} Kč\n\n"

                QMessageBox.information(self, "Dnešní zakázky", message)
            else:
                QMessageBox.information(self, "Dnešní zakázky",
                                      "Dnes zatím nejsou žádné zakázky.")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při načítání zakázek: {e}")

    def show_critical_stock(self):
        """Zobrazení kritických položek skladu"""
        try:
            query = """
                SELECT
                    name,
                    quantity,
                    min_quantity,
                    unit
                FROM warehouse_items
                WHERE quantity <= min_quantity
                ORDER BY (quantity - min_quantity)
                LIMIT 10
            """
            results = db.fetch_all(query)

            if results:
                message = "⚠️ Kritické položky skladu:\n\n"
                for r in results:
                    message += f"{r[0]}\n"
                    message += f"Aktuální: {r[1]} {r[3]} | Minimum: {r[2]} {r[3]}\n\n"

                QMessageBox.warning(self, "Kritické položky", message)
            else:
                QMessageBox.information(self, "Kritické položky",
                                      "Všechny položky jsou nad minimem.")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při načítání skladu: {e}")

    def show_pending_tasks(self):
        """Zobrazení pending úkolů"""
        try:
            query = """
                SELECT
                    order_id,
                    customer_name,
                    vehicle_info,
                    order_date
                FROM orders
                WHERE status = 'in_progress'
                ORDER BY order_date
                LIMIT 10
            """
            results = db.fetch_all(query)

            if results:
                message = "⏳ Rozpracované zakázky:\n\n"
                for r in results:
                    message += f"#{r[0]} - {r[1]} ({r[2]})\n"
                    message += f"Datum: {r[3]}\n\n"

                QMessageBox.information(self, "Pending úkoly", message)
            else:
                QMessageBox.information(self, "Pending úkoly",
                                      "Žádné rozpracované zakázky.")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při načítání úkolů: {e}")
