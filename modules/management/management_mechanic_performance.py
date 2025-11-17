# -*- coding: utf-8 -*-
"""
Management Mechanic Performance - Analýza výkonu mechaniků
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QFrame, QScrollArea, QTabWidget,
                             QComboBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from .management_widgets import (MetricCard, TrendCard, LineChartWidget,
                                 BarChartWidget, PieChartWidget, AnalyticsTable, RankingTable)
from database_manager import db


class ManagementMechanicPerformance(QWidget):
    """Analýza výkonu mechaniků"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_module = parent
        self.date_from = None
        self.date_to = None
        self.selected_mechanic_id = None
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

        # Celkové metriky
        self.create_overall_metrics(content_layout)

        # Filtr mechanika
        self.create_mechanic_filter(content_layout)

        # Záložky s analýzami
        self.create_analysis_tabs(content_layout)

        content_layout.addStretch()

    def create_overall_metrics(self, parent_layout):
        """Celkové metriky pro všechny mechaniky"""
        metrics_container = QFrame()
        metrics_layout = QGridLayout(metrics_container)
        metrics_layout.setSpacing(15)

        # Karty
        self.metric_total_mechanics = MetricCard("Celkem mechaniků", "0", "👨‍🔧")
        self.metric_total_hours = MetricCard("Celkem hodin", "0 h", "⏱️")
        self.metric_avg_hours = MetricCard("Průměr hodin/mechanik", "0 h", "📊")
        self.metric_total_orders = MetricCard("Dokončené zakázky", "0", "📋")
        self.metric_avg_efficiency = TrendCard("Průměrná efektivita", "0%", "+0%", True, "💹")
        self.metric_capacity_util = TrendCard("Využití kapacity", "0%", "+0%", True, "📈")

        metrics_layout.addWidget(self.metric_total_mechanics, 0, 0)
        metrics_layout.addWidget(self.metric_total_hours, 0, 1)
        metrics_layout.addWidget(self.metric_avg_hours, 0, 2)
        metrics_layout.addWidget(self.metric_total_orders, 1, 0)
        metrics_layout.addWidget(self.metric_avg_efficiency, 1, 1)
        metrics_layout.addWidget(self.metric_capacity_util, 1, 2)

        parent_layout.addWidget(metrics_container)

    def create_mechanic_filter(self, parent_layout):
        """Filtr pro výběr konkrétního mechanika"""
        filter_frame = QFrame()
        filter_frame.setObjectName("mechanicFilter")
        filter_layout = QHBoxLayout(filter_frame)

        label = QLabel("📍 Vybrat mechanika:")
        label_font = QFont()
        label_font.setBold(True)
        label.setFont(label_font)
        filter_layout.addWidget(label)

        self.mechanic_combo = QComboBox()
        self.mechanic_combo.addItem("Všichni mechanici", None)
        self.mechanic_combo.currentIndexChanged.connect(self.on_mechanic_changed)
        filter_layout.addWidget(self.mechanic_combo)

        filter_layout.addStretch()

        # Tlačítko refresh
        refresh_btn = QPushButton("🔄 Obnovit")
        refresh_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(refresh_btn)

        filter_frame.setStyleSheet("""
            QFrame#mechanicFilter {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #e0e0e0;
            }
        """)

        parent_layout.addWidget(filter_frame)

    def create_analysis_tabs(self, parent_layout):
        """Záložky s analýzami"""
        tabs = QTabWidget()
        tabs.setObjectName("analysisTabs")

        # Tab 1: Přehled mechaniků
        tab_overview = self.create_overview_tab()
        tabs.addTab(tab_overview, "📊 Přehled")

        # Tab 2: Detaily mechanika
        tab_detail = self.create_detail_tab()
        tabs.addTab(tab_detail, "🔍 Detail mechanika")

        # Tab 3: Srovnání
        tab_comparison = self.create_comparison_tab()
        tabs.addTab(tab_comparison, "⚖️ Srovnání")

        # Tab 4: Trendy
        tab_trends = self.create_trends_tab()
        tabs.addTab(tab_trends, "📈 Trendy")

        # Tab 5: Specializace
        tab_specialization = self.create_specialization_tab()
        tabs.addTab(tab_specialization, "🎯 Specializace")

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
        """Tab s přehledem všech mechaniků"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Grafy - první řádek
        row1 = QHBoxLayout()

        self.chart_top_hours = BarChartWidget("Top mechanici podle hodin")
        row1.addWidget(self.chart_top_hours)

        self.chart_top_orders = BarChartWidget("Top mechanici podle zakázek")
        row1.addWidget(self.chart_top_orders)

        layout.addLayout(row1)

        # Tabulka přehledu
        table_label = QLabel("👨‍🔧 Přehled všech mechaniků")
        label_font = QFont()
        label_font.setPointSize(12)
        label_font.setBold(True)
        table_label.setFont(label_font)
        layout.addWidget(table_label)

        self.table_mechanics_overview = RankingTable()
        layout.addWidget(self.table_mechanics_overview)

        return tab

    def create_detail_tab(self):
        """Tab s detaily vybraného mechanika"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)

        # Info o vybraném mechanikovi
        self.detail_info_label = QLabel("Vyberte mechanika v horním filtru")
        info_font = QFont()
        info_font.setPointSize(14)
        info_font.setBold(True)
        self.detail_info_label.setFont(info_font)
        self.detail_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.detail_info_label)

        # Metriky vybraného mechanika
        self.detail_metrics_container = QFrame()
        detail_metrics_layout = QGridLayout(self.detail_metrics_container)
        detail_metrics_layout.setSpacing(15)

        self.detail_total_hours = MetricCard("Odpracované hodiny", "0 h", "⏱️")
        self.detail_total_orders = MetricCard("Dokončené zakázky", "0", "📋")
        self.detail_avg_time = MetricCard("Průměrný čas/zakázka", "0 h", "📊")
        self.detail_efficiency = MetricCard("Efektivita", "0%", "💹")

        detail_metrics_layout.addWidget(self.detail_total_hours, 0, 0)
        detail_metrics_layout.addWidget(self.detail_total_orders, 0, 1)
        detail_metrics_layout.addWidget(self.detail_avg_time, 1, 0)
        detail_metrics_layout.addWidget(self.detail_efficiency, 1, 1)

        layout.addWidget(self.detail_metrics_container)

        # Tabulka zakázek mechanika
        orders_label = QLabel("📋 Zakázky mechanika")
        label_font = QFont()
        label_font.setPointSize(12)
        label_font.setBold(True)
        orders_label.setFont(label_font)
        layout.addWidget(orders_label)

        self.table_mechanic_orders = AnalyticsTable()
        layout.addWidget(self.table_mechanic_orders)

        return tab

    def create_comparison_tab(self):
        """Tab se srovnáním mechaniků"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Grafy srovnání
        row1 = QHBoxLayout()

        self.chart_hours_comparison = BarChartWidget("Srovnání odpracovaných hodin")
        row1.addWidget(self.chart_hours_comparison)

        self.chart_efficiency_comparison = BarChartWidget("Srovnání efektivity")
        row1.addWidget(self.chart_efficiency_comparison)

        layout.addLayout(row1)

        # Tabulka srovnání
        comparison_label = QLabel("⚖️ Srovnávací tabulka")
        label_font = QFont()
        label_font.setPointSize(12)
        label_font.setBold(True)
        comparison_label.setFont(label_font)
        layout.addWidget(comparison_label)

        self.table_comparison = AnalyticsTable()
        layout.addWidget(self.table_comparison)

        return tab

    def create_trends_tab(self):
        """Tab s trendy výkonu"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Grafy trendů
        row1 = QHBoxLayout()

        self.chart_hours_trend = LineChartWidget("Trend odpracovaných hodin")
        row1.addWidget(self.chart_hours_trend)

        self.chart_orders_trend = LineChartWidget("Trend počtu zakázek")
        row1.addWidget(self.chart_orders_trend)

        layout.addLayout(row1)

        # Druhý řádek
        row2 = QHBoxLayout()

        self.chart_capacity_trend = LineChartWidget("Využití kapacity v čase")
        row2.addWidget(self.chart_capacity_trend)

        self.chart_efficiency_trend = LineChartWidget("Trend efektivity")
        row2.addWidget(self.chart_efficiency_trend)

        layout.addLayout(row2)

        return tab

    def create_specialization_tab(self):
        """Tab se specializací mechaniků"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Grafy specializace
        row1 = QHBoxLayout()

        self.chart_work_types = PieChartWidget("Rozdělení typů prací")
        row1.addWidget(self.chart_work_types)

        # Tabulka specializace
        spec_container = QWidget()
        spec_layout = QVBoxLayout(spec_container)

        spec_label = QLabel("🎯 Specializace mechaniků")
        label_font = QFont()
        label_font.setPointSize(12)
        label_font.setBold(True)
        spec_label.setFont(label_font)
        spec_layout.addWidget(spec_label)

        self.table_specialization = AnalyticsTable()
        spec_layout.addWidget(self.table_specialization)

        row1.addWidget(spec_container)

        layout.addLayout(row1)

        return tab

    def refresh(self):
        """Refresh dat"""
        if self.date_from is None or self.date_to is None:
            self.date_to = QDate.currentDate()
            self.date_from = self.date_to.addMonths(-1)

        self.load_mechanics_list()
        self.load_overall_metrics()
        self.load_overview_data()
        self.load_detail_data()
        self.load_comparison_data()
        self.load_trends_data()
        self.load_specialization_data()

    def set_date_range(self, date_from, date_to):
        """Nastavení období"""
        self.date_from = date_from
        self.date_to = date_to

    def load_mechanics_list(self):
        """Načtení seznamu mechaniků do comboboxu"""
        try:
            query = """
                SELECT id, full_name
                FROM users
                WHERE role = 'mechanik' AND active = 1
                ORDER BY full_name
            """
            results = db.fetch_all(query)

            # Vyčistit a naplnit combo
            self.mechanic_combo.clear()
            self.mechanic_combo.addItem("Všichni mechanici", None)

            for r in results:
                self.mechanic_combo.addItem(r[1], r[0])

        except Exception as e:
            print(f"Chyba při načítání mechaniků: {e}")

    def on_mechanic_changed(self, index):
        """Změna vybraného mechanika"""
        self.selected_mechanic_id = self.mechanic_combo.currentData()
        self.load_detail_data()

    def load_overall_metrics(self):
        """Načtení celkových metrik"""
        try:
            date_from_str = self.date_from.toString("yyyy-MM-dd")
            date_to_str = self.date_to.toString("yyyy-MM-dd")

            # Počet aktivních mechaniků
            query = "SELECT COUNT(*) FROM users WHERE role = 'mechanik' AND active = 1"
            result = db.fetch_one(query)
            total_mechanics = result[0] if result else 0
            self.metric_total_mechanics.set_value(str(total_mechanics))

            # Celkem odpracovaných hodin
            query = """
                SELECT COALESCE(SUM(hours_worked), 0)
                FROM order_work_log
                WHERE date BETWEEN ? AND ?
            """
            result = db.fetch_one(query, (date_from_str, date_to_str))
            total_hours = result[0] if result else 0
            self.metric_total_hours.set_value(f"{total_hours:.1f} h")

            # Průměr hodin na mechanika
            avg_hours = total_hours / total_mechanics if total_mechanics > 0 else 0
            self.metric_avg_hours.set_value(f"{avg_hours:.1f} h")

            # Celkem dokončených zakázek
            query = """
                SELECT COUNT(DISTINCT o.id)
                FROM orders o
                JOIN order_work_log wl ON o.id = wl.order_id
                WHERE wl.date BETWEEN ? AND ?
                AND o.status = 'Dokončeno'
            """
            result = db.fetch_one(query, (date_from_str, date_to_str))
            total_orders = result[0] if result else 0
            self.metric_total_orders.set_value(str(total_orders))

            # Průměrná efektivita (skutečné hodiny vs plánované)
            # Pro zjednodušení použijeme procento využití kapacity
            working_days = self.calculate_working_days(self.date_from, self.date_to)
            expected_hours = total_mechanics * working_days * 8
            efficiency = (total_hours / expected_hours * 100) if expected_hours > 0 else 0

            # Předchozí období
            days_diff = self.date_from.daysTo(self.date_to)
            prev_date_to = self.date_from.addDays(-1)
            prev_date_from = prev_date_to.addDays(-days_diff)

            prev_hours_query = """
                SELECT COALESCE(SUM(hours_worked), 0)
                FROM order_work_log
                WHERE date BETWEEN ? AND ?
            """
            prev_result = db.fetch_one(prev_hours_query,
                                      (prev_date_from.toString("yyyy-MM-dd"),
                                       prev_date_to.toString("yyyy-MM-dd")))
            prev_hours = prev_result[0] if prev_result else 0
            prev_working_days = self.calculate_working_days(prev_date_from, prev_date_to)
            prev_expected = total_mechanics * prev_working_days * 8
            prev_efficiency = (prev_hours / prev_expected * 100) if prev_expected > 0 else 0

            efficiency_trend = efficiency - prev_efficiency

            self.metric_avg_efficiency.set_value(
                f"{efficiency:.1f}%",
                f"{abs(efficiency_trend):.1f}%",
                efficiency_trend >= 0
            )

            # Využití kapacity (stejné jako efektivita)
            self.metric_capacity_util.set_value(
                f"{efficiency:.1f}%",
                f"{abs(efficiency_trend):.1f}%",
                efficiency_trend >= 0
            )

        except Exception as e:
            print(f"Chyba při načítání metrik: {e}")

    def load_overview_data(self):
        """Načtení dat pro přehled"""
        try:
            date_from_str = self.date_from.toString("yyyy-MM-dd")
            date_to_str = self.date_to.toString("yyyy-MM-dd")

            # Top mechanici podle hodin
            query = """
                SELECT
                    u.full_name,
                    COALESCE(SUM(wl.hours_worked), 0) as total_hours
                FROM users u
                LEFT JOIN order_work_log wl ON u.user_id = wl.user_id
                    AND wl.date BETWEEN ? AND ?
                WHERE u.role = 'mechanik' AND u.active = 1
                GROUP BY u.user_id, u.full_name
                ORDER BY total_hours DESC
                LIMIT 10
            """
            results = db.fetch_all(query, (date_from_str, date_to_str))
            if results:
                names = [r[0] for r in results]
                hours = [r[1] for r in results]
                self.chart_top_hours.plot(names, hours, "Mechanik", "Hodiny", "#3498db")

            # Top mechanici podle zakázek
            query = """
                SELECT
                    u.full_name,
                    COUNT(DISTINCT wl.order_id) as order_count
                FROM users u
                LEFT JOIN order_work_log wl ON u.user_id = wl.user_id
                    AND wl.date BETWEEN ? AND ?
                WHERE u.role = 'mechanik' AND u.active = 1
                GROUP BY u.user_id, u.full_name
                ORDER BY order_count DESC
                LIMIT 10
            """
            results = db.fetch_all(query, (date_from_str, date_to_str))
            if results:
                names = [r[0] for r in results]
                counts = [r[1] for r in results]
                self.chart_top_orders.plot(names, counts, "Mechanik", "Zakázky", "#27ae60")

            # Tabulka přehledu
            query = """
                SELECT
                    u.full_name,
                    COALESCE(SUM(wl.hours_worked), 0) as total_hours,
                    COUNT(DISTINCT wl.order_id) as order_count,
                    CASE
                        WHEN COUNT(DISTINCT wl.order_id) > 0
                        THEN COALESCE(SUM(wl.hours_worked), 0) / COUNT(DISTINCT wl.order_id)
                        ELSE 0
                    END as avg_time
                FROM users u
                LEFT JOIN order_work_log wl ON u.user_id = wl.user_id
                    AND wl.date BETWEEN ? AND ?
                WHERE u.role = 'mechanik' AND u.active = 1
                GROUP BY u.user_id, u.full_name
                ORDER BY total_hours DESC
            """
            results = db.fetch_all(query, (date_from_str, date_to_str))
            if results:
                headers = ["Pořadí", "Mechanik", "Hodiny", "Zakázky", "Průměr h/zakázka"]
                data = [
                    [
                        f"#{i+1}",
                        r[0],
                        f"{r[1]:.1f} h",
                        r[2],
                        f"{r[3]:.1f} h"
                    ]
                    for i, r in enumerate(results)
                ]
                self.table_mechanics_overview.set_ranking_data(headers, data)

        except Exception as e:
            print(f"Chyba při načítání přehledu: {e}")

    def load_detail_data(self):
        """Načtení detailů vybraného mechanika"""
        try:
            if self.selected_mechanic_id is None:
                self.detail_info_label.setText("Vyberte mechanika v horním filtru")
                self.table_mechanic_orders.set_data(["Info"], [["Vyberte mechanika"]])
                return

            # Načtení jména mechanika
            query = "SELECT full_name FROM users WHERE id = ?"
            result = db.fetch_one(query, (self.selected_mechanic_id,))
            if not result:
                return

            mechanic_name = result[0]
            self.detail_info_label.setText(f"👨‍🔧 Detail: {mechanic_name}")

            date_from_str = self.date_from.toString("yyyy-MM-dd")
            date_to_str = self.date_to.toString("yyyy-MM-dd")

            # Metriky mechanika
            query = """
                SELECT
                    COALESCE(SUM(hours_worked), 0) as total_hours,
                    COUNT(DISTINCT order_id) as order_count
                FROM order_work_log
                WHERE user_id = ? AND date BETWEEN ? AND ?
            """
            result = db.fetch_one(query, (self.selected_mechanic_id, date_from_str, date_to_str))
            if result:
                total_hours = result[0]
                order_count = result[1]
                avg_time = total_hours / order_count if order_count > 0 else 0

                self.detail_total_hours.set_value(f"{total_hours:.1f} h")
                self.detail_total_orders.set_value(str(order_count))
                self.detail_avg_time.set_value(f"{avg_time:.1f} h")

                # Efektivita (zjednodušená - % z maximální kapacity)
                working_days = self.calculate_working_days(self.date_from, self.date_to)
                max_hours = working_days * 8
                efficiency = (total_hours / max_hours * 100) if max_hours > 0 else 0
                self.detail_efficiency.set_value(f"{efficiency:.1f}%")

            # Tabulka zakázek
            query = """
                SELECT
                    o.order_number,
                    o.created_date,
                    o.customer_id,
                    wl.hours_worked,
                    wl.description
                FROM order_work_log wl
                JOIN orders o ON wl.order_id = o.id
                WHERE wl.user_id = ? AND wl.date BETWEEN ? AND ?
                ORDER BY wl.date DESC
                LIMIT 50
            """
            results = db.fetch_all(query, (self.selected_mechanic_id, date_from_str, date_to_str))
            if results:
                # Načtení jmen zákazníků
                headers = ["Číslo zakázky", "Datum", "Zákazník", "Hodiny", "Popis"]
                data = []
                for r in results:
                    # Načtení zákazníka
                    cust_query = "SELECT first_name, last_name FROM customers WHERE id = ?"
                    cust = db.fetch_one(cust_query, (r[2],))
                    customer_name = f"{cust[0]} {cust[1]}" if cust else "N/A"

                    data.append([
                        r[0],
                        r[1],
                        customer_name,
                        f"{r[3]:.1f} h",
                        r[4] or "-"
                    ])
                self.table_mechanic_orders.set_data(headers, data)
            else:
                self.table_mechanic_orders.set_data(["Info"], [["Žádné zakázky"]])

        except Exception as e:
            print(f"Chyba při načítání detailů: {e}")

    def load_comparison_data(self):
        """Načtení dat pro srovnání"""
        try:
            date_from_str = self.date_from.toString("yyyy-MM-dd")
            date_to_str = self.date_to.toString("yyyy-MM-dd")

            # Graf srovnání hodin
            query = """
                SELECT
                    u.full_name,
                    COALESCE(SUM(wl.hours_worked), 0) as total_hours
                FROM users u
                LEFT JOIN order_work_log wl ON u.user_id = wl.user_id
                    AND wl.date BETWEEN ? AND ?
                WHERE u.role = 'mechanik' AND u.active = 1
                GROUP BY u.user_id, u.full_name
                ORDER BY total_hours DESC
            """
            results = db.fetch_all(query, (date_from_str, date_to_str))
            if results:
                names = [r[0] for r in results]
                hours = [r[1] for r in results]
                self.chart_hours_comparison.plot(names, hours, "Mechanik", "Hodiny", "#3498db")

            # Graf srovnání efektivity
            working_days = self.calculate_working_days(self.date_from, self.date_to)
            max_hours = working_days * 8

            if results:
                efficiencies = [(h / max_hours * 100) if max_hours > 0 else 0 for _, h in results]
                self.chart_efficiency_comparison.plot(names, efficiencies,
                                                      "Mechanik", "Efektivita (%)", "#e74c3c")

            # Srovnávací tabulka
            query = """
                SELECT
                    u.full_name,
                    COALESCE(SUM(wl.hours_worked), 0) as total_hours,
                    COUNT(DISTINCT wl.order_id) as order_count,
                    CASE
                        WHEN COUNT(DISTINCT wl.order_id) > 0
                        THEN COALESCE(SUM(wl.hours_worked), 0) / COUNT(DISTINCT wl.order_id)
                        ELSE 0
                    END as avg_time
                FROM users u
                LEFT JOIN order_work_log wl ON u.user_id = wl.user_id
                    AND wl.date BETWEEN ? AND ?
                WHERE u.role = 'mechanik' AND u.active = 1
                GROUP BY u.user_id, u.full_name
                ORDER BY total_hours DESC
            """
            results = db.fetch_all(query, (date_from_str, date_to_str))
            if results:
                headers = ["Mechanik", "Hodiny", "Zakázky", "Průměr h/zakázka", "Efektivita"]
                data = [
                    [
                        r[0],
                        f"{r[1]:.1f} h",
                        r[2],
                        f"{r[3]:.1f} h",
                        f"{(r[1] / max_hours * 100):.1f}%" if max_hours > 0 else "0%"
                    ]
                    for r in results
                ]
                self.table_comparison.set_data(headers, data)

        except Exception as e:
            print(f"Chyba při načítání srovnání: {e}")

    def load_trends_data(self):
        """Načtení trendů výkonu"""
        try:
            # Trend hodin (týdenní)
            query = """
                SELECT
                    strftime('%Y-%W', date) as week,
                    SUM(hours_worked) as total_hours
                FROM order_work_log
                WHERE date >= date('now', '-12 weeks')
                GROUP BY strftime('%Y-%W', date)
                ORDER BY week
            """
            results = db.fetch_all(query)
            if results:
                weeks = [f"Týden {r[0][-2:]}" for r in results]
                hours = [r[1] for r in results]
                self.chart_hours_trend.plot(weeks, hours, "Týden", "Hodiny", "#3498db")

            # Trend zakázek
            query = """
                SELECT
                    strftime('%Y-%W', date) as week,
                    COUNT(DISTINCT order_id) as order_count
                FROM order_work_log
                WHERE date >= date('now', '-12 weeks')
                GROUP BY strftime('%Y-%W', date)
                ORDER BY week
            """
            results = db.fetch_all(query)
            if results:
                weeks = [f"Týden {r[0][-2:]}" for r in results]
                counts = [r[1] for r in results]
                self.chart_orders_trend.plot(weeks, counts, "Týden", "Zakázky", "#27ae60")

            # Trend využití kapacity
            query = """
                SELECT
                    strftime('%Y-%W', date) as week,
                    SUM(hours_worked) as total_hours,
                    COUNT(DISTINCT user_id) as mechanic_count
                FROM order_work_log
                WHERE date >= date('now', '-12 weeks')
                GROUP BY strftime('%Y-%W', date)
                ORDER BY week
            """
            results = db.fetch_all(query)
            if results:
                weeks = [f"Týden {r[0][-2:]}" for r in results]
                # Předpokládáme 5 pracovních dnů v týdnu, 8h denně
                capacities = [(r[1] / (r[2] * 5 * 8) * 100) if r[2] > 0 else 0 for r in results]
                self.chart_capacity_trend.plot(weeks, capacities,
                                              "Týden", "Využití (%)", "#9b59b6")

            # Trend efektivity (zjednodušený)
            if results:
                self.chart_efficiency_trend.plot(weeks, capacities,
                                                "Týden", "Efektivita (%)", "#e74c3c")

        except Exception as e:
            print(f"Chyba při načítání trendů: {e}")

    def load_specialization_data(self):
        """Načtení dat o specializaci"""
        try:
            date_from_str = self.date_from.toString("yyyy-MM-dd")
            date_to_str = self.date_to.toString("yyyy-MM-dd")

            # Koláčový graf typů prací
            query = """
                SELECT
                    o.order_type,
                    COUNT(*) as count
                FROM order_work_log wl
                JOIN orders o ON wl.order_id = o.id
                WHERE wl.date BETWEEN ? AND ?
                GROUP BY o.order_type
            """
            results = db.fetch_all(query, (date_from_str, date_to_str))
            if results:
                type_names = {
                    "Zakázka": "Zakázka",
                    "Servis": "Servis",
                    "Oprava": "Oprava"
                }
                labels = [type_names.get(r[0], r[0]) for r in results]
                sizes = [r[1] for r in results]
                self.chart_work_types.plot(labels, sizes)

            # Tabulka specializace
            query = """
                SELECT
                    u.full_name,
                    o.order_type,
                    COUNT(*) as count,
                    SUM(wl.hours_worked) as total_hours
                FROM users u
                JOIN order_work_log wl ON u.user_id = wl.user_id
                JOIN orders o ON wl.order_id = o.id
                WHERE wl.date BETWEEN ? AND ?
                AND u.role = 'mechanik' AND u.active = 1
                GROUP BY u.user_id, u.full_name, o.order_type
                ORDER BY u.full_name, count DESC
            """
            results = db.fetch_all(query, (date_from_str, date_to_str))
            if results:
                headers = ["Mechanik", "Typ práce", "Počet", "Hodiny", "% času"]

                # Výpočet celkového času každého mechanika pro %
                mechanic_totals = {}
                for r in results:
                    if r[0] not in mechanic_totals:
                        mechanic_totals[r[0]] = 0
                    mechanic_totals[r[0]] += r[3]

                data = [
                    [
                        r[0],
                        r[1],
                        r[2],
                        f"{r[3]:.1f} h",
                        f"{(r[3] / mechanic_totals[r[0]] * 100):.1f}%"
                            if mechanic_totals[r[0]] > 0 else "0%"
                    ]
                    for r in results
                ]
                self.table_specialization.set_data(headers, data)

        except Exception as e:
            print(f"Chyba při načítání specializace: {e}")

    def calculate_working_days(self, date_from, date_to):
        """Výpočet pracovních dnů (pondělí-pátek)"""
        working_days = 0
        current = date_from
        while current <= date_to:
            if current.dayOfWeek() <= 5:  # 1-5 = Po-Pá
                working_days += 1
            current = current.addDays(1)
        return working_days
