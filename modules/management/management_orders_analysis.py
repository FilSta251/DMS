# -*- coding: utf-8 -*-
"""
Management Orders Analysis - Detailní analýza zakázek
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QFrame, QScrollArea, QComboBox,
                             QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from .management_widgets import (MetricCard, TrendCard, LineChartWidget,
                                 PieChartWidget, AnalyticsTable, RankingTable)
from database_manager import db


class ManagementOrdersAnalysis(QWidget):
    """Detailní analýza zakázek"""

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

        # Základní statistiky
        self.create_statistics_section(content_layout)

        # Filtry
        self.create_filters_section(content_layout)

        # Záložky s analýzami
        self.create_analysis_tabs(content_layout)

        content_layout.addStretch()

    def create_statistics_section(self, parent_layout):
        """Základní statistiky"""
        stats_container = QFrame()
        stats_layout = QGridLayout(stats_container)
        stats_layout.setSpacing(15)

        # Karty se statistikami
        self.stat_total_orders = MetricCard("Celkem zakázek", "0", "📋")
        self.stat_total_revenue = MetricCard("Celkový obrat", "0 Kč", "💰")
        self.stat_avg_revenue = MetricCard("Průměr", "0 Kč", "📊")
        self.stat_median_revenue = MetricCard("Medián", "0 Kč", "📈")
        self.stat_total_margin = MetricCard("Celková marže", "0 Kč", "💹")
        self.stat_avg_margin = MetricCard("Průměrná marže", "0%", "📉")
        self.stat_avg_completion = MetricCard("Rychlost dokončení", "0 dní", "⏱️")
        self.stat_orders_per_day = MetricCard("Zakázek/den", "0", "📅")

        # Přidání do gridu (4x2)
        stats_layout.addWidget(self.stat_total_orders, 0, 0)
        stats_layout.addWidget(self.stat_total_revenue, 0, 1)
        stats_layout.addWidget(self.stat_avg_revenue, 1, 0)
        stats_layout.addWidget(self.stat_median_revenue, 1, 1)
        stats_layout.addWidget(self.stat_total_margin, 2, 0)
        stats_layout.addWidget(self.stat_avg_margin, 2, 1)
        stats_layout.addWidget(self.stat_avg_completion, 3, 0)
        stats_layout.addWidget(self.stat_orders_per_day, 3, 1)

        parent_layout.addWidget(stats_container)

    def create_filters_section(self, parent_layout):
        """Sekce s filtry"""
        filters_frame = QFrame()
        filters_frame.setObjectName("filtersFrame")
        filters_layout = QHBoxLayout(filters_frame)

        # Filtr podle typu
        type_label = QLabel("Typ zakázky:")
        type_label.setStyleSheet("font-weight: bold;")
        filters_layout.addWidget(type_label)

        self.filter_type = QComboBox()
        self.filter_type.addItems(["Všechny", "Servis", "Oprava", "Kontrola", "Prodej"])
        self.filter_type.currentIndexChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.filter_type)

        filters_layout.addSpacing(20)

        # Filtr podle stavu
        status_label = QLabel("Stav:")
        status_label.setStyleSheet("font-weight: bold;")
        filters_layout.addWidget(status_label)

        self.filter_status = QComboBox()
        self.filter_status.addItems(["Všechny", "Nové", "Rozpracované", "Dokončené", "Zrušené"])
        self.filter_status.currentIndexChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.filter_status)

        filters_layout.addSpacing(20)

        # Tlačítko refresh
        refresh_btn = QPushButton("🔄 Obnovit")
        refresh_btn.clicked.connect(self.refresh)
        filters_layout.addWidget(refresh_btn)

        filters_layout.addStretch()

        filters_frame.setStyleSheet("""
            QFrame#filtersFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #e0e0e0;
            }
        """)

        parent_layout.addWidget(filters_frame)

    def create_analysis_tabs(self, parent_layout):
        """Záložky s různými analýzami"""
        tabs = QTabWidget()
        tabs.setObjectName("analysisTabs")

        # Tab 1: Přehled a grafy
        tab_overview = self.create_overview_tab()
        tabs.addTab(tab_overview, "📊 Přehled")

        # Tab 2: Top zakázky
        tab_top = self.create_top_orders_tab()
        tabs.addTab(tab_top, "🏆 Top zakázky")

        # Tab 3: Problémové zakázky
        tab_problems = self.create_problems_tab()
        tabs.addTab(tab_problems, "⚠️ Problémy")

        # Tab 4: Podle zákazníků
        tab_customers = self.create_customers_tab()
        tabs.addTab(tab_customers, "👥 Zákazníci")

        # Tab 5: Podle vozidel
        tab_vehicles = self.create_vehicles_tab()
        tabs.addTab(tab_vehicles, "🚗 Vozidla")

        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                background-color: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                padding: 10px 20px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
            }
        """)

        parent_layout.addWidget(tabs)

    def create_overview_tab(self):
        """Tab s přehledem a grafy"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Grafy - první řádek
        row1 = QHBoxLayout()

        self.chart_revenue_time = LineChartWidget("Obrat v čase")
        row1.addWidget(self.chart_revenue_time)

        self.chart_orders_time = LineChartWidget("Počet zakázek v čase")
        row1.addWidget(self.chart_orders_time)

        layout.addLayout(row1)

        # Grafy - druhý řádek
        row2 = QHBoxLayout()

        self.chart_avg_value = LineChartWidget("Průměrná hodnota zakázky")
        row2.addWidget(self.chart_avg_value)

        self.chart_order_types = PieChartWidget("Rozdělení podle typu")
        row2.addWidget(self.chart_order_types)

        layout.addLayout(row2)

        # Tabulka všech zakázek
        table_label = QLabel("📋 Všechny zakázky")
        label_font = QFont()
        label_font.setPointSize(12)
        label_font.setBold(True)
        table_label.setFont(label_font)
        layout.addWidget(table_label)

        self.table_all_orders = AnalyticsTable()
        layout.addWidget(self.table_all_orders)

        return tab

    def create_top_orders_tab(self):
        """Tab s top zakázkami"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Nadpis
        title = QLabel("🏆 Top 10 nejvýnosnějších zakázek")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Tabulka
        self.table_top_orders = RankingTable()
        layout.addWidget(self.table_top_orders)

        return tab

    def create_problems_tab(self):
        """Tab s problémovými zakázkami"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # Přečasované zakázky
        overdue_label = QLabel("⏰ Přečasované zakázky")
        label_font = QFont()
        label_font.setPointSize(12)
        label_font.setBold(True)
        overdue_label.setFont(label_font)
        layout.addWidget(overdue_label)

        self.table_overdue = AnalyticsTable()
        layout.addWidget(self.table_overdue)

        # Zakázky s nízkou marží
        low_margin_label = QLabel("📉 Zakázky s nízkou marží (< 20%)")
        low_margin_label.setFont(label_font)
        layout.addWidget(low_margin_label)

        self.table_low_margin = AnalyticsTable()
        layout.addWidget(self.table_low_margin)

        return tab

    def create_customers_tab(self):
        """Tab s analýzou podle zákazníků"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Top zákazníci podle obratu
        title = QLabel("👥 Top zákazníci podle obratu")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        self.table_top_customers = RankingTable()
        layout.addWidget(self.table_top_customers)

        return tab

    def create_vehicles_tab(self):
        """Tab s analýzou podle vozidel"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # Grafy - značky vozidel
        row1 = QHBoxLayout()

        self.chart_vehicle_brands = PieChartWidget("Rozdělení podle značek")
        row1.addWidget(self.chart_vehicle_brands)

        # Tabulka - top modely
        vehicles_container = QWidget()
        vehicles_layout = QVBoxLayout(vehicles_container)

        models_label = QLabel("🚗 Top modely vozidel")
        label_font = QFont()
        label_font.setPointSize(12)
        label_font.setBold(True)
        models_label.setFont(label_font)
        vehicles_layout.addWidget(models_label)

        self.table_top_models = RankingTable()
        vehicles_layout.addWidget(self.table_top_models)

        row1.addWidget(vehicles_container)

        layout.addLayout(row1)

        return tab

    def refresh(self):
        """Refresh dat"""
        if self.date_from is None or self.date_to is None:
            self.date_to = QDate.currentDate()
            self.date_from = self.date_to.addMonths(-1)

        self.load_statistics()
        self.load_overview_data()
        self.load_top_orders()
        self.load_problems()
        self.load_customers_analysis()
        self.load_vehicles_analysis()

    def set_date_range(self, date_from, date_to):
        """Nastavení období"""
        self.date_from = date_from
        self.date_to = date_to

    def apply_filters(self):
        """Aplikace filtrů"""
        self.refresh()

    def get_filter_conditions(self):
        """Získání SQL podmínek podle filtrů"""
        conditions = []
        params = []

        # Typ zakázky
        type_filter = self.filter_type.currentText()
        if type_filter != "Všechny":
            type_map = {
                "Servis": "service",
                "Oprava": "repair",
                "Kontrola": "inspection",
                "Prodej": "sale"
            }
            conditions.append("order_type = ?")
            params.append(type_map.get(type_filter, "service"))

        # Stav
        status_filter = self.filter_status.currentText()
        if status_filter != "Všechny":
            status_map = {
                "Nové": "new",
                "Rozpracované": "in_progress",
                "Dokončené": "completed",
                "Zrušené": "cancelled"
            }
            conditions.append("status = ?")
            params.append(status_map.get(status_filter, "new"))

        return conditions, params

    def load_statistics(self):
        """Načtení základních statistik"""
        try:
            date_from_str = self.date_from.toString("yyyy-MM-dd")
            date_to_str = self.date_to.toString("yyyy-MM-dd")

            # Získání filter podmínek
            filter_conditions, filter_params = self.get_filter_conditions()
            where_clause = "WHERE order_date BETWEEN ? AND ?"
            if filter_conditions:
                where_clause += " AND " + " AND ".join(filter_conditions)

            params = [date_from_str, date_to_str] + filter_params

            # Celkem zakázek
            query = f"SELECT COUNT(*) FROM orders {where_clause}"
            result = db.fetch_one(query, params)
            total_orders = result[0] if result else 0
            self.stat_total_orders.set_value(str(total_orders))

            # Celkový obrat
            query = f"SELECT COALESCE(SUM(total_price), 0) FROM orders {where_clause}"
            result = db.fetch_one(query, params)
            total_revenue = result[0] if result else 0
            self.stat_total_revenue.set_value(f"{total_revenue:,.0f} Kč")

            # Průměr
            avg_revenue = total_revenue / total_orders if total_orders > 0 else 0
            self.stat_avg_revenue.set_value(f"{avg_revenue:,.0f} Kč")

            # Medián
            query = f"""
                SELECT total_price
                FROM orders {where_clause}
                ORDER BY total_price
            """
            results = db.fetch_all(query, params)
            if results:
                values = [r[0] for r in results]
                median = values[len(values) // 2] if values else 0
                self.stat_median_revenue.set_value(f"{median:,.0f} Kč")
            else:
                self.stat_median_revenue.set_value("0 Kč")

            # Celková marže
            query = f"""
                SELECT
                    COALESCE(SUM(total_price), 0) as revenue,
                    COALESCE(SUM(material_cost), 0) as costs
                FROM orders {where_clause}
            """
            result = db.fetch_one(query, params)
            if result:
                revenue = result[0]
                costs = result[1]
                total_margin = revenue - costs
                avg_margin_pct = (total_margin / revenue * 100) if revenue > 0 else 0

                self.stat_total_margin.set_value(f"{total_margin:,.0f} Kč")
                self.stat_avg_margin.set_value(f"{avg_margin_pct:.1f}%")
            else:
                self.stat_total_margin.set_value("0 Kč")
                self.stat_avg_margin.set_value("0%")

            # Rychlost dokončení
            query = f"""
                SELECT AVG(
                    JULIANDAY(completion_date) - JULIANDAY(order_date)
                ) as avg_days
                FROM orders
                {where_clause} AND status = 'completed'
                AND completion_date IS NOT NULL
            """
            result = db.fetch_one(query, params)
            avg_days = result[0] if result and result[0] else 0
            self.stat_avg_completion.set_value(f"{avg_days:.1f} dní")

            # Zakázek za den
            days = self.date_from.daysTo(self.date_to) + 1
            orders_per_day = total_orders / days if days > 0 else 0
            self.stat_orders_per_day.set_value(f"{orders_per_day:.1f}")

        except Exception as e:
            print(f"Chyba při načítání statistik: {e}")

    def load_overview_data(self):
        """Načtení dat pro přehled"""
        try:
            date_from_str = self.date_from.toString("yyyy-MM-dd")
            date_to_str = self.date_to.toString("yyyy-MM-dd")

            filter_conditions, filter_params = self.get_filter_conditions()
            where_clause = "WHERE order_date BETWEEN ? AND ?"
            if filter_conditions:
                where_clause += " AND " + " AND ".join(filter_conditions)

            params = [date_from_str, date_to_str] + filter_params

            # Graf obratu v čase
            query = f"""
                SELECT
                    order_date,
                    SUM(total_price) as revenue
                FROM orders
                {where_clause}
                GROUP BY order_date
                ORDER BY order_date
            """
            results = db.fetch_all(query, params)
            if results:
                dates = [r[0] for r in results]
                revenues = [r[1] for r in results]
                self.chart_revenue_time.plot(dates, revenues, "Datum", "Obrat (Kč)", "#3498db")

            # Graf počtu zakázek v čase
            query = f"""
                SELECT
                    order_date,
                    COUNT(*) as count
                FROM orders
                {where_clause}
                GROUP BY order_date
                ORDER BY order_date
            """
            results = db.fetch_all(query, params)
            if results:
                dates = [r[0] for r in results]
                counts = [r[1] for r in results]
                self.chart_orders_time.plot(dates, counts, "Datum", "Počet", "#e74c3c")

            # Graf průměrné hodnoty
            query = f"""
                SELECT
                    order_date,
                    AVG(total_price) as avg_value
                FROM orders
                {where_clause}
                GROUP BY order_date
                ORDER BY order_date
            """
            results = db.fetch_all(query, params)
            if results:
                dates = [r[0] for r in results]
                avgs = [r[1] for r in results]
                self.chart_avg_value.plot(dates, avgs, "Datum", "Průměr (Kč)", "#27ae60")

            # Koláčový graf typů
            query = f"""
                SELECT
                    order_type,
                    COUNT(*) as count
                FROM orders
                {where_clause}
                GROUP BY order_type
            """
            results = db.fetch_all(query, params)
            if results:
                type_names = {
                    "service": "Servis",
                    "repair": "Oprava",
                    "inspection": "Kontrola",
                    "sale": "Prodej"
                }
                labels = [type_names.get(r[0], r[0]) for r in results]
                sizes = [r[1] for r in results]
                self.chart_order_types.plot(labels, sizes)

            # Tabulka všech zakázek
            query = f"""
                SELECT
                    order_id,
                    order_date,
                    customer_name,
                    vehicle_info,
                    order_type,
                    status,
                    total_price
                FROM orders
                {where_clause}
                ORDER BY order_date DESC
                LIMIT 100
            """
            results = db.fetch_all(query, params)
            if results:
                headers = ["ID", "Datum", "Zákazník", "Vozidlo", "Typ", "Stav", "Cena"]

                # Mapování pro zobrazení
                type_map = {
                    "service": "Servis",
                    "repair": "Oprava",
                    "inspection": "Kontrola",
                    "sale": "Prodej"
                }
                status_map = {
                    "new": "Nová",
                    "in_progress": "Rozpracovaná",
                    "completed": "Dokončená",
                    "cancelled": "Zrušená"
                }

                data = [
                    [
                        r[0],
                        r[1],
                        r[2],
                        r[3],
                        type_map.get(r[4], r[4]),
                        status_map.get(r[5], r[5]),
                        f"{r[6]:,.0f} Kč"
                    ]
                    for r in results
                ]
                self.table_all_orders.set_data(headers, data)

        except Exception as e:
            print(f"Chyba při načítání přehledu: {e}")

    def load_top_orders(self):
        """Načtení top zakázek"""
        try:
            date_from_str = self.date_from.toString("yyyy-MM-dd")
            date_to_str = self.date_to.toString("yyyy-MM-dd")

            filter_conditions, filter_params = self.get_filter_conditions()
            where_clause = "WHERE order_date BETWEEN ? AND ?"
            if filter_conditions:
                where_clause += " AND " + " AND ".join(filter_conditions)

            params = [date_from_str, date_to_str] + filter_params

            query = f"""
                SELECT
                    order_id,
                    order_date,
                    customer_name,
                    vehicle_info,
                    total_price,
                    (total_price - material_cost) as margin
                FROM orders
                {where_clause}
                ORDER BY total_price DESC
                LIMIT 10
            """
            results = db.fetch_all(query, params)
            if results:
                headers = ["Pořadí", "ID", "Datum", "Zákazník", "Vozidlo", "Cena", "Marže"]
                data = [
                    [
                        f"#{i+1}",
                        r[0],
                        r[1],
                        r[2],
                        r[3],
                        f"{r[4]:,.0f} Kč",
                        f"{r[5]:,.0f} Kč"
                    ]
                    for i, r in enumerate(results)
                ]
                self.table_top_orders.set_ranking_data(headers, data)

        except Exception as e:
            print(f"Chyba při načítání top zakázek: {e}")

    def load_problems(self):
        """Načtení problémových zakázek"""
        try:
            date_from_str = self.date_from.toString("yyyy-MM-dd")
            date_to_str = self.date_to.toString("yyyy-MM-dd")

            # Přečasované zakázky (více než 7 dní)
            query = """
                SELECT
                    order_id,
                    order_date,
                    customer_name,
                    vehicle_info,
                    JULIANDAY('now') - JULIANDAY(order_date) as days_open
                FROM orders
                WHERE order_date BETWEEN ? AND ?
                AND status = 'in_progress'
                AND JULIANDAY('now') - JULIANDAY(order_date) > 7
                ORDER BY days_open DESC
                LIMIT 20
            """
            results = db.fetch_all(query, (date_from_str, date_to_str))
            if results:
                headers = ["ID", "Datum", "Zákazník", "Vozidlo", "Dnů otevřeno"]
                data = [
                    [r[0], r[1], r[2], r[3], f"{int(r[4])} dní"]
                    for r in results
                ]
                self.table_overdue.set_data(headers, data)
            else:
                self.table_overdue.set_data(["Info"], [["Žádné přečasované zakázky"]])

            # Nízká marže
            query = """
                SELECT
                    order_id,
                    order_date,
                    customer_name,
                    total_price,
                    material_cost,
                    ((total_price - material_cost) / total_price * 100) as margin_pct
                FROM orders
                WHERE order_date BETWEEN ? AND ?
                AND status != 'cancelled'
                AND total_price > 0
                AND ((total_price - material_cost) / total_price * 100) < 20
                ORDER BY margin_pct
                LIMIT 20
            """
            results = db.fetch_all(query, (date_from_str, date_to_str))
            if results:
                headers = ["ID", "Datum", "Zákazník", "Cena", "Náklady", "Marže %"]
                data = [
                    [
                        r[0],
                        r[1],
                        r[2],
                        f"{r[3]:,.0f} Kč",
                        f"{r[4]:,.0f} Kč",
                        f"{r[5]:.1f}%"
                    ]
                    for r in results
                ]
                self.table_low_margin.set_data(headers, data)
            else:
                self.table_low_margin.set_data(["Info"], [["Žádné zakázky s nízkou marží"]])

        except Exception as e:
            print(f"Chyba při načítání problémů: {e}")

    def load_customers_analysis(self):
        """Načtení analýzy zákazníků"""
        try:
            date_from_str = self.date_from.toString("yyyy-MM-dd")
            date_to_str = self.date_to.toString("yyyy-MM-dd")

            filter_conditions, filter_params = self.get_filter_conditions()
            where_clause = "WHERE order_date BETWEEN ? AND ?"
            if filter_conditions:
                where_clause += " AND " + " AND ".join(filter_conditions)

            params = [date_from_str, date_to_str] + filter_params

            query = f"""
                SELECT
                    customer_name,
                    COUNT(*) as order_count,
                    SUM(total_price) as total_revenue,
                    AVG(total_price) as avg_revenue
                FROM orders
                {where_clause}
                GROUP BY customer_name
                ORDER BY total_revenue DESC
                LIMIT 10
            """
            results = db.fetch_all(query, params)
            if results:
                headers = ["Pořadí", "Zákazník", "Zakázek", "Celkem", "Průměr"]
                data = [
                    [
                        f"#{i+1}",
                        r[0],
                        r[1],
                        f"{r[2]:,.0f} Kč",
                        f"{r[3]:,.0f} Kč"
                    ]
                    for i, r in enumerate(results)
                ]
                self.table_top_customers.set_ranking_data(headers, data)

        except Exception as e:
            print(f"Chyba při načítání analýzy zákazníků: {e}")

    def load_vehicles_analysis(self):
        """Načtení analýzy vozidel"""
        try:
            date_from_str = self.date_from.toString("yyyy-MM-dd")
            date_to_str = self.date_to.toString("yyyy-MM-dd")

            filter_conditions, filter_params = self.get_filter_conditions()
            where_clause = "WHERE order_date BETWEEN ? AND ?"
            if filter_conditions:
                where_clause += " AND " + " AND ".join(filter_conditions)

            params = [date_from_str, date_to_str] + filter_params

            # Graf značek - extrahovány ze sloupce vehicle_info
            query = f"""
                SELECT
                    SUBSTR(vehicle_info, 1, INSTR(vehicle_info || ' ', ' ') - 1) as brand,
                    COUNT(*) as count
                FROM orders
                {where_clause}
                GROUP BY brand
                ORDER BY count DESC
                LIMIT 10
            """
            results = db.fetch_all(query, params)
            if results:
                labels = [r[0] for r in results]
                sizes = [r[1] for r in results]
                self.chart_vehicle_brands.plot(labels, sizes)

            # Top modely
            query = f"""
                SELECT
                    vehicle_info,
                    COUNT(*) as count,
                    SUM(total_price) as total_revenue
                FROM orders
                {where_clause}
                GROUP BY vehicle_info
                ORDER BY count DESC
                LIMIT 10
            """
            results = db.fetch_all(query, params)
            if results:
                headers = ["Pořadí", "Vozidlo", "Zakázek", "Obrat"]
                data = [
                    [
                        f"#{i+1}",
                        r[0],
                        r[1],
                        f"{r[2]:,.0f} Kč"
                    ]
                    for i, r in enumerate(results)
                ]
                self.table_top_models.set_ranking_data(headers, data)

        except Exception as e:
            print(f"Chyba při načítání analýzy vozidel: {e}")
