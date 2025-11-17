# -*- coding: utf-8 -*-
"""
Management Financial - Finanční analýzy
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QFrame, QScrollArea, QTabWidget,
                             QMessageBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from .management_widgets import (MetricCard, TrendCard, LineChartWidget,
                                 BarChartWidget, PieChartWidget, AnalyticsTable, RankingTable)
from database_manager import db
from datetime import datetime, timedelta


class ManagementFinancial(QWidget):
    """Finanční analýzy"""

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

        # Hlavní finanční metriky
        self.create_main_metrics(content_layout)

        # Záložky s analýzami
        self.create_analysis_tabs(content_layout)

        content_layout.addStretch()

    def create_main_metrics(self, parent_layout):
        """Hlavní finanční metriky"""
        metrics_container = QFrame()
        metrics_layout = QGridLayout(metrics_container)
        metrics_layout.setSpacing(15)

        # Karty
        self.metric_total_revenue = TrendCard("Celkové příjmy", "0 Kč", "+0%", True, "💰")
        self.metric_total_costs = TrendCard("Celkové náklady", "0 Kč", "+0%", False, "💸")
        self.metric_gross_profit = TrendCard("Hrubý zisk", "0 Kč", "+0%", True, "💵")
        self.metric_net_profit = TrendCard("Čistý zisk", "0 Kč", "+0%", True, "💎")
        self.metric_margin = TrendCard("Marže", "0%", "+0%", True, "💹")
        self.metric_cash_flow = TrendCard("Cash Flow", "0 Kč", "+0%", True, "💱")

        metrics_layout.addWidget(self.metric_total_revenue, 0, 0)
        metrics_layout.addWidget(self.metric_total_costs, 0, 1)
        metrics_layout.addWidget(self.metric_gross_profit, 0, 2)
        metrics_layout.addWidget(self.metric_net_profit, 1, 0)
        metrics_layout.addWidget(self.metric_margin, 1, 1)
        metrics_layout.addWidget(self.metric_cash_flow, 1, 2)

        parent_layout.addWidget(metrics_container)

    def create_analysis_tabs(self, parent_layout):
        """Záložky s analýzami"""
        tabs = QTabWidget()
        tabs.setObjectName("analysisTabs")

        # Tab 1: Přehled
        tab_overview = self.create_overview_tab()
        tabs.addTab(tab_overview, "📊 Přehled")

        # Tab 2: Příjmy
        tab_revenue = self.create_revenue_tab()
        tabs.addTab(tab_revenue, "💰 Příjmy")

        # Tab 3: Náklady
        tab_costs = self.create_costs_tab()
        tabs.addTab(tab_costs, "💸 Náklady")

        # Tab 4: Rentabilita
        tab_profitability = self.create_profitability_tab()
        tabs.addTab(tab_profitability, "📈 Rentabilita")

        # Tab 5: Trendy
        tab_trends = self.create_trends_tab()
        tabs.addTab(tab_trends, "📉 Trendy")

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
        """Tab s přehledem"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Grafy přehledu
        row1 = QHBoxLayout()

        self.chart_revenue_vs_costs = LineChartWidget("Příjmy vs Náklady")
        row1.addWidget(self.chart_revenue_vs_costs)

        self.chart_profit_margin = LineChartWidget("Profit Margin")
        row1.addWidget(self.chart_profit_margin)

        layout.addLayout(row1)

        # Druhý řádek
        row2 = QHBoxLayout()

        self.chart_cash_flow = LineChartWidget("Cash Flow")
        row2.addWidget(self.chart_cash_flow)

        self.chart_monthly_comparison = BarChartWidget("Měsíční srovnání")
        row2.addWidget(self.chart_monthly_comparison)

        layout.addLayout(row2)

        return tab

    def create_revenue_tab(self):
        """Tab s příjmy"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Metriky příjmů
        revenue_metrics = QFrame()
        revenue_metrics_layout = QGridLayout(revenue_metrics)
        revenue_metrics_layout.setSpacing(15)

        self.revenue_orders = MetricCard("Příjmy z prací", "0 Kč", "🔧")
        self.revenue_materials = MetricCard("Příjmy z materiálu", "0 Kč", "📦")
        self.revenue_parts = MetricCard("Příjmy z dílů", "0 Kč", "⚙️")
        self.revenue_other = MetricCard("Ostatní příjmy", "0 Kč", "💵")

        revenue_metrics_layout.addWidget(self.revenue_orders, 0, 0)
        revenue_metrics_layout.addWidget(self.revenue_materials, 0, 1)
        revenue_metrics_layout.addWidget(self.revenue_parts, 1, 0)
        revenue_metrics_layout.addWidget(self.revenue_other, 1, 1)

        layout.addWidget(revenue_metrics)

        # Grafy
        row = QHBoxLayout()

        self.chart_revenue_breakdown = PieChartWidget("Rozdělení příjmů")
        row.addWidget(self.chart_revenue_breakdown)

        self.chart_revenue_trend = LineChartWidget("Trend příjmů")
        row.addWidget(self.chart_revenue_trend)

        layout.addLayout(row)

        # Tabulka top zakázek
        table_label = QLabel("💰 Top příjmy podle zakázek")
        label_font = QFont()
        label_font.setPointSize(12)
        label_font.setBold(True)
        table_label.setFont(label_font)
        layout.addWidget(table_label)

        self.table_top_revenue = RankingTable()
        layout.addWidget(self.table_top_revenue)

        return tab

    def create_costs_tab(self):
        """Tab s náklady"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Metriky nákladů
        costs_metrics = QFrame()
        costs_metrics_layout = QGridLayout(costs_metrics)
        costs_metrics_layout.setSpacing(15)

        self.costs_materials = MetricCard("Materiál", "0 Kč", "📦")
        self.costs_wages = MetricCard("Mzdy", "0 Kč", "👨‍🔧")
        self.costs_operation = MetricCard("Provoz", "0 Kč", "🏢")
        self.costs_other = MetricCard("Ostatní", "0 Kč", "💸")

        costs_metrics_layout.addWidget(self.costs_materials, 0, 0)
        costs_metrics_layout.addWidget(self.costs_wages, 0, 1)
        costs_metrics_layout.addWidget(self.costs_operation, 1, 0)
        costs_metrics_layout.addWidget(self.costs_other, 1, 1)

        layout.addWidget(costs_metrics)

        # Grafy
        row = QHBoxLayout()

        self.chart_costs_breakdown = PieChartWidget("Rozdělení nákladů")
        row.addWidget(self.chart_costs_breakdown)

        self.chart_costs_trend = LineChartWidget("Trend nákladů")
        row.addWidget(self.chart_costs_trend)

        layout.addLayout(row)

        # Tabulka nákladných zakázek
        table_label = QLabel("💸 Nákladné zakázky")
        label_font = QFont()
        label_font.setPointSize(12)
        label_font.setBold(True)
        table_label.setFont(label_font)
        layout.addWidget(table_label)

        self.table_costly_orders = RankingTable()
        layout.addWidget(self.table_costly_orders)

        return tab

    def create_profitability_tab(self):
        """Tab s rentabilitou"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Grafy rentability
        row1 = QHBoxLayout()

        self.chart_profitability_by_type = BarChartWidget("Rentabilita podle typu zakázky")
        row1.addWidget(self.chart_profitability_by_type)

        self.chart_profit_trend = LineChartWidget("Trend zisku")
        row1.addWidget(self.chart_profit_trend)

        layout.addLayout(row1)

        # Break-even analýza
        breakeven_frame = QFrame()
        breakeven_frame.setObjectName("breakevenFrame")
        breakeven_layout = QVBoxLayout(breakeven_frame)

        breakeven_title = QLabel("📊 Break-Even Analýza")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        breakeven_title.setFont(title_font)
        breakeven_layout.addWidget(breakeven_title)

        self.chart_breakeven = LineChartWidget("")
        breakeven_layout.addWidget(self.chart_breakeven)

        breakeven_frame.setStyleSheet("""
            QFrame#breakevenFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout.addWidget(breakeven_frame)

        # Tabulka rentability
        table_label = QLabel("📈 Rentabilita podle zakázek")
        label_font = QFont()
        label_font.setPointSize(12)
        label_font.setBold(True)
        table_label.setFont(label_font)
        layout.addWidget(table_label)

        self.table_profitability = AnalyticsTable()
        layout.addWidget(self.table_profitability)

        return tab

    def create_trends_tab(self):
        """Tab s trendy"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Grafy trendů
        row1 = QHBoxLayout()

        self.chart_seasonal_revenue = BarChartWidget("Sezónnost příjmů (měsíční)")
        row1.addWidget(self.chart_seasonal_revenue)

        self.chart_yoy_comparison = BarChartWidget("Meziroční srovnání (YoY)")
        row1.addWidget(self.chart_yoy_comparison)

        layout.addLayout(row1)

        # Predikce
        prediction_frame = QFrame()
        prediction_frame.setObjectName("predictionFrame")
        prediction_layout = QVBoxLayout(prediction_frame)

        prediction_title = QLabel("🔮 Predikce příjmů")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        prediction_title.setFont(title_font)
        prediction_layout.addWidget(prediction_title)

        # Metriky predikce
        pred_metrics = QGridLayout()

        self.pred_next_month = MetricCard("Příští měsíc", "0 Kč", "📅")
        self.pred_next_quarter = MetricCard("Příští kvartál", "0 Kč", "📆")
        self.pred_growth_rate = MetricCard("Míra růstu", "0%", "📈")

        pred_metrics.addWidget(self.pred_next_month, 0, 0)
        pred_metrics.addWidget(self.pred_next_quarter, 0, 1)
        pred_metrics.addWidget(self.pred_growth_rate, 0, 2)

        prediction_layout.addLayout(pred_metrics)

        self.chart_prediction = LineChartWidget("")
        prediction_layout.addWidget(self.chart_prediction)

        prediction_frame.setStyleSheet("""
            QFrame#predictionFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout.addWidget(prediction_frame)

        return tab

    def refresh(self):
        """Refresh dat"""
        if self.date_from is None or self.date_to is None:
            self.date_to = QDate.currentDate()
            self.date_from = self.date_to.addMonths(-1)

        self.load_main_metrics()
        self.load_overview_data()
        self.load_revenue_data()
        self.load_costs_data()
        self.load_profitability_data()
        self.load_trends_data()

    def set_date_range(self, date_from, date_to):
        """Nastavení období"""
        self.date_from = date_from
        self.date_to = date_to

    def load_main_metrics(self):
        """Načtení hlavních metrik"""
        try:
            date_from_str = self.date_from.toString("yyyy-MM-dd")
            date_to_str = self.date_to.toString("yyyy-MM-dd")

            # Celkové příjmy
            query = """
                SELECT COALESCE(SUM(total_price), 0)
                FROM orders
                WHERE created_date BETWEEN ? AND ?
                AND status != 'Zrušeno'
            """
            result = db.fetch_one(query, (date_from_str, date_to_str))
            total_revenue = result[0] if result else 0

            # Předchozí období
            days_diff = self.date_from.daysTo(self.date_to)
            prev_date_to = self.date_from.addDays(-1)
            prev_date_from = prev_date_to.addDays(-days_diff)

            prev_revenue = db.fetch_one(query,
                                       (prev_date_from.toString("yyyy-MM-dd"),
                                        prev_date_to.toString("yyyy-MM-dd")))
            prev_total_revenue = prev_revenue[0] if prev_revenue else 0

            revenue_trend = 0
            if prev_total_revenue > 0:
                revenue_trend = ((total_revenue - prev_total_revenue) / prev_total_revenue) * 100

            self.metric_total_revenue.set_value(
                f"{total_revenue:,.0f} Kč",
                f"{abs(revenue_trend):.1f}%",
                revenue_trend >= 0
            )

            # Celkové náklady (materiál z zakázek)
            query = """
                SELECT COALESCE(SUM(material_cost), 0)
                FROM orders
                WHERE created_date BETWEEN ? AND ?
                AND status != 'Zrušeno'
            """
            result = db.fetch_one(query, (date_from_str, date_to_str))
            material_costs = result[0] if result else 0

            # Mzdy (odpracované hodiny * sazba - zjednodušené)
            query = """
                SELECT COALESCE(SUM(hours_worked), 0)
                FROM order_work_log
                WHERE date BETWEEN ? AND ?
            """
            result = db.fetch_one(query, (date_from_str, date_to_str))
            total_hours = result[0] if result else 0
            avg_hourly_rate = 300  # Průměrná hodinová sazba
            wage_costs = total_hours * avg_hourly_rate

            total_costs = material_costs + wage_costs

            # Předchozí náklady
            prev_material = db.fetch_one(
                "SELECT COALESCE(SUM(material_cost), 0) FROM orders WHERE created_date BETWEEN ? AND ? AND status != 'Zrušeno'",
                (prev_date_from.toString("yyyy-MM-dd"), prev_date_to.toString("yyyy-MM-dd"))
            )
            prev_hours = db.fetch_one(
                "SELECT COALESCE(SUM(hours_worked), 0) FROM order_work_log WHERE date BETWEEN ? AND ?",
                (prev_date_from.toString("yyyy-MM-dd"), prev_date_to.toString("yyyy-MM-dd"))
            )
            prev_total_costs = (prev_material[0] if prev_material else 0) + ((prev_hours[0] if prev_hours else 0) * avg_hourly_rate)

            costs_trend = 0
            if prev_total_costs > 0:
                costs_trend = ((total_costs - prev_total_costs) / prev_total_costs) * 100

            self.metric_total_costs.set_value(
                f"{total_costs:,.0f} Kč",
                f"{abs(costs_trend):.1f}%",
                costs_trend <= 0  # Pro náklady je lepší pokles
            )

            # Hrubý zisk
            gross_profit = total_revenue - material_costs
            prev_gross = prev_total_revenue - (prev_material[0] if prev_material else 0)

            gross_trend = 0
            if prev_gross > 0:
                gross_trend = ((gross_profit - prev_gross) / prev_gross) * 100

            self.metric_gross_profit.set_value(
                f"{gross_profit:,.0f} Kč",
                f"{abs(gross_trend):.1f}%",
                gross_trend >= 0
            )

            # Čistý zisk
            net_profit = total_revenue - total_costs
            prev_net = prev_total_revenue - prev_total_costs

            net_trend = 0
            if prev_net != 0:
                net_trend = ((net_profit - prev_net) / abs(prev_net)) * 100

            self.metric_net_profit.set_value(
                f"{net_profit:,.0f} Kč",
                f"{abs(net_trend):.1f}%",
                net_trend >= 0
            )

            # Marže
            margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
            prev_margin = (prev_net / prev_total_revenue * 100) if prev_total_revenue > 0 else 0
            margin_trend = margin - prev_margin

            self.metric_margin.set_value(
                f"{margin:.1f}%",
                f"{abs(margin_trend):.1f}%",
                margin_trend >= 0
            )

            # Cash flow (zjednodušený)
            cash_flow = net_profit
            self.metric_cash_flow.set_value(
                f"{cash_flow:,.0f} Kč",
                f"{abs(net_trend):.1f}%",
                cash_flow >= 0
            )

        except Exception as e:
            print(f"Chyba při načítání metrik: {e}")

    def load_overview_data(self):
        """Načtení dat pro přehled"""
        try:
            # Příjmy vs náklady v čase (měsíčně)
            query = """
                SELECT
                    strftime('%Y-%m', created_date) as month,
                    SUM(total_price) as revenue,
                    SUM(material_cost) as costs
                FROM orders
                WHERE created_date >= date('now', '-12 months')
                AND status != 'Zrušeno'
                GROUP BY strftime('%Y-%m', created_date)
                ORDER BY month
            """
            results = db.fetch_all(query)
            if results:
                months = [r[0] for r in results]
                revenues = [r[1] for r in results]
                costs = [r[2] for r in results]

                self.chart_revenue_vs_costs.plot_multiple([
                    (months, revenues, "Příjmy"),
                    (months, costs, "Náklady")
                ], "Měsíc", "Kč")

            # Profit margin
            if results:
                margins = [(r[1] - r[2]) / r[1] * 100 if r[1] > 0 else 0 for r in results]
                self.chart_profit_margin.plot(months, margins, "Měsíc", "Marže (%)", "#27ae60")

            # Cash flow
            if results:
                cash_flows = [r[1] - r[2] for r in results]
                self.chart_cash_flow.plot(months, cash_flows, "Měsíc", "Cash Flow (Kč)", "#9b59b6")

            # Měsíční srovnání (poslední 6 měsíců)
            if len(results) >= 6:
                last_6 = results[-6:]
                months_short = [r[0][-2:] for r in last_6]
                profits = [r[1] - r[2] for r in last_6]
                self.chart_monthly_comparison.plot(months_short, profits, "Měsíc", "Zisk (Kč)", "#3498db")

        except Exception as e:
            print(f"Chyba při načítání přehledu: {e}")

    def load_revenue_data(self):
        """Načtení dat o příjmech"""
        try:
            date_from_str = self.date_from.toString("yyyy-MM-dd")
            date_to_str = self.date_to.toString("yyyy-MM-dd")

            # Celkové příjmy (už máme)
            query = """
                SELECT COALESCE(SUM(total_price), 0)
                FROM orders
                WHERE created_date BETWEEN ? AND ?
                AND status != 'Zrušeno'
            """
            result = db.fetch_one(query, (date_from_str, date_to_str))
            total_revenue = result[0] if result else 0

            # Rozdělení příjmů (zjednodušené)
            # Práce = total_price - material_cost
            # Materiál = material_cost
            query = """
                SELECT
                    COALESCE(SUM(total_price - material_cost), 0) as labor,
                    COALESCE(SUM(material_cost), 0) as materials
                FROM orders
                WHERE created_date BETWEEN ? AND ?
                AND status != 'Zrušeno'
            """
            result = db.fetch_one(query, (date_from_str, date_to_str))

            if result:
                labor_revenue = result[0]
                material_revenue = result[1]
                parts_revenue = material_revenue * 0.6  # Zjednodušené - 60% z materiálu jsou díly
                pure_material = material_revenue * 0.4
                other_revenue = 0

                self.revenue_orders.set_value(f"{labor_revenue:,.0f} Kč")
                self.revenue_materials.set_value(f"{pure_material:,.0f} Kč")
                self.revenue_parts.set_value(f"{parts_revenue:,.0f} Kč")
                self.revenue_other.set_value(f"{other_revenue:,.0f} Kč")

                # Koláčový graf
                labels = ["Práce", "Materiál", "Díly", "Ostatní"]
                sizes = [labor_revenue, pure_material, parts_revenue, other_revenue]
                self.chart_revenue_breakdown.plot(labels, sizes)

            # Trend příjmů
            query = """
                SELECT
                    strftime('%Y-%m', created_date) as month,
                    SUM(total_price) as revenue
                FROM orders
                WHERE created_date >= date('now', '-12 months')
                AND status != 'Zrušeno'
                GROUP BY strftime('%Y-%m', created_date)
                ORDER BY month
            """
            results = db.fetch_all(query)
            if results:
                months = [r[0] for r in results]
                revenues = [r[1] for r in results]
                self.chart_revenue_trend.plot(months, revenues, "Měsíc", "Příjmy (Kč)", "#27ae60")

            # Top zakázky podle příjmů
            query = """
                SELECT
                    order_number,
                    created_date,
                    total_price,
                    material_cost,
                    (total_price - material_cost) as profit
                FROM orders
                WHERE created_date BETWEEN ? AND ?
                AND status != 'Zrušeno'
                ORDER BY total_price DESC
                LIMIT 10
            """
            results = db.fetch_all(query, (date_from_str, date_to_str))
            if results:
                headers = ["Pořadí", "Číslo", "Datum", "Příjem", "Náklady", "Zisk"]
                data = [
                    [
                        f"#{i+1}",
                        r[0],
                        r[1],
                        f"{r[2]:,.0f} Kč",
                        f"{r[3]:,.0f} Kč",
                        f"{r[4]:,.0f} Kč"
                    ]
                    for i, r in enumerate(results)
                ]
                self.table_top_revenue.set_ranking_data(headers, data)

        except Exception as e:
            print(f"Chyba při načítání příjmů: {e}")

    def load_costs_data(self):
        """Načtení dat o nákladech"""
        try:
            date_from_str = self.date_from.toString("yyyy-MM-dd")
            date_to_str = self.date_to.toString("yyyy-MM-dd")

            # Náklady na materiál
            query = """
                SELECT COALESCE(SUM(material_cost), 0)
                FROM orders
                WHERE created_date BETWEEN ? AND ?
                AND status != 'Zrušeno'
            """
            result = db.fetch_one(query, (date_from_str, date_to_str))
            material_costs = result[0] if result else 0
            self.costs_materials.set_value(f"{material_costs:,.0f} Kč")

            # Mzdy
            query = """
                SELECT COALESCE(SUM(hours_worked), 0)
                FROM order_work_log
                WHERE date BETWEEN ? AND ?
            """
            result = db.fetch_one(query, (date_from_str, date_to_str))
            total_hours = result[0] if result else 0
            avg_rate = 300
            wage_costs = total_hours * avg_rate
            self.costs_wages.set_value(f"{wage_costs:,.0f} Kč")

            # Provozní náklady (odhad 15% z celkových příjmů)
            query = """
                SELECT COALESCE(SUM(total_price), 0)
                FROM orders
                WHERE created_date BETWEEN ? AND ?
                AND status != 'Zrušeno'
            """
            result = db.fetch_one(query, (date_from_str, date_to_str))
            total_revenue = result[0] if result else 0
            operation_costs = total_revenue * 0.15
            self.costs_operation.set_value(f"{operation_costs:,.0f} Kč")

            # Ostatní náklady
            other_costs = 0
            self.costs_other.set_value(f"{other_costs:,.0f} Kč")

            # Koláčový graf nákladů
            labels = ["Materiál", "Mzdy", "Provoz", "Ostatní"]
            sizes = [material_costs, wage_costs, operation_costs, other_costs]
            self.chart_costs_breakdown.plot(labels, sizes)

            # Trend nákladů
            query = """
                SELECT
                    strftime('%Y-%m', created_date) as month,
                    SUM(material_cost) as costs
                FROM orders
                WHERE created_date >= date('now', '-12 months')
                AND status != 'Zrušeno'
                GROUP BY strftime('%Y-%m', created_date)
                ORDER BY month
            """
            results = db.fetch_all(query)
            if results:
                months = [r[0] for r in results]
                costs = [r[1] for r in results]
                self.chart_costs_trend.plot(months, costs, "Měsíc", "Náklady (Kč)", "#e74c3c")

            # Nákladné zakázky
            query = """
                SELECT
                    order_number,
                    created_date,
                    material_cost,
                    total_price,
                    (material_cost / total_price * 100) as cost_pct
                FROM orders
                WHERE created_date BETWEEN ? AND ?
                AND status != 'Zrušeno'
                AND total_price > 0
                ORDER BY material_cost DESC
                LIMIT 10
            """
            results = db.fetch_all(query, (date_from_str, date_to_str))
            if results:
                headers = ["Pořadí", "Číslo", "Datum", "Náklady", "Celkem", "% nákladů"]
                data = [
                    [
                        f"#{i+1}",
                        r[0],
                        r[1],
                        f"{r[2]:,.0f} Kč",
                        f"{r[3]:,.0f} Kč",
                        f"{r[4]:.1f}%"
                    ]
                    for i, r in enumerate(results)
                ]
                self.table_costly_orders.set_ranking_data(headers, data)

        except Exception as e:
            print(f"Chyba při načítání nákladů: {e}")

    def load_profitability_data(self):
        """Načtení dat o rentabilitě"""
        try:
            date_from_str = self.date_from.toString("yyyy-MM-dd")
            date_to_str = self.date_to.toString("yyyy-MM-dd")

            # Rentabilita podle typu
            query = """
                SELECT
                    order_type,
                    COUNT(*) as count,
                    SUM(total_price) as revenue,
                    SUM(material_cost) as costs,
                    (SUM(total_price) - SUM(material_cost)) / SUM(total_price) * 100 as margin
                FROM orders
                WHERE created_date BETWEEN ? AND ?
                AND status != 'Zrušeno'
                AND total_price > 0
                GROUP BY order_type
            """
            results = db.fetch_all(query, (date_from_str, date_to_str))
            if results:
                types = [r[0] for r in results]
                margins = [r[4] for r in results]
                self.chart_profitability_by_type.plot(types, margins, "Typ", "Marže (%)", "#3498db")

            # Trend zisku
            query = """
                SELECT
                    strftime('%Y-%m', created_date) as month,
                    SUM(total_price - material_cost) as profit
                FROM orders
                WHERE created_date >= date('now', '-12 months')
                AND status != 'Zrušeno'
                GROUP BY strftime('%Y-%m', created_date)
                ORDER BY month
            """
            results = db.fetch_all(query)
            if results:
                months = [r[0] for r in results]
                profits = [r[1] for r in results]
                self.chart_profit_trend.plot(months, profits, "Měsíc", "Zisk (Kč)", "#27ae60")

            # Break-even graf (zjednodušený)
            # Fixní náklady vs variabilní náklady
            if results:
                # Simulace break-even
                units = list(range(0, 101, 10))
                fixed_costs = [50000] * len(units)  # Fixní 50k
                variable_costs = [u * 1000 for u in units]  # 1000 Kč na jednotku
                revenue = [u * 1500 for u in units]  # 1500 Kč cena

                self.chart_breakeven.plot_multiple([
                    (units, fixed_costs, "Fixní náklady"),
                    (units, variable_costs, "Celkové náklady"),
                    (units, revenue, "Příjmy")
                ], "Počet zakázek", "Kč")

            # Tabulka rentability
            query = """
                SELECT
                    order_number,
                    order_type,
                    total_price,
                    material_cost,
                    (total_price - material_cost) as profit,
                    ((total_price - material_cost) / total_price * 100) as margin_pct
                FROM orders
                WHERE created_date BETWEEN ? AND ?
                AND status != 'Zrušeno'
                AND total_price > 0
                ORDER BY margin_pct DESC
                LIMIT 20
            """
            results = db.fetch_all(query, (date_from_str, date_to_str))
            if results:
                headers = ["Číslo", "Typ", "Příjem", "Náklady", "Zisk", "Marže %"]
                data = [
                    [
                        r[0],
                        r[1],
                        f"{r[2]:,.0f} Kč",
                        f"{r[3]:,.0f} Kč",
                        f"{r[4]:,.0f} Kč",
                        f"{r[5]:.1f}%"
                    ]
                    for r in results
                ]
                self.table_profitability.set_data(headers, data)

        except Exception as e:
            print(f"Chyba při načítání rentability: {e}")

    def load_trends_data(self):
        """Načtení trendů"""
        try:
            # Sezónnost (průměry po měsících za celou historii)
            query = """
                SELECT
                    CAST(strftime('%m', created_date) AS INTEGER) as month_num,
                    AVG(total_price) as avg_revenue
                FROM orders
                WHERE status != 'Zrušeno'
                GROUP BY month_num
                ORDER BY month_num
            """
            results = db.fetch_all(query)
            if results:
                month_names = ["Led", "Úno", "Bře", "Dub", "Kvě", "Čer",
                              "Čvc", "Srp", "Zář", "Říj", "Lis", "Pro"]
                months = [month_names[r[0]-1] for r in results]
                avg_revenues = [r[1] for r in results]
                self.chart_seasonal_revenue.plot(months, avg_revenues, "Měsíc", "Průměrný příjem (Kč)", "#3498db")

            # YoY srovnání
            current_year = datetime.now().year
            query = f"""
                SELECT
                    CAST(strftime('%m', created_date) AS INTEGER) as month_num,
                    SUM(CASE WHEN strftime('%Y', created_date) = '{current_year}' THEN total_price ELSE 0 END) as current_year,
                    SUM(CASE WHEN strftime('%Y', created_date) = '{current_year-1}' THEN total_price ELSE 0 END) as last_year
                FROM orders
                WHERE status != 'Zrušeno'
                AND strftime('%Y', created_date) IN ('{current_year}', '{current_year-1}')
                GROUP BY month_num
                ORDER BY month_num
            """
            results = db.fetch_all(query)
            if results:
                month_names = ["Led", "Úno", "Bře", "Dub", "Kvě", "Čer",
                              "Čvc", "Srp", "Zář", "Říj", "Lis", "Pro"]
                months = [month_names[r[0]-1] for r in results]
                current = [r[1] for r in results]
                last = [r[2] for r in results]

                # Pro zjednodušení použijeme sloupcový graf pro aktuální rok
                self.chart_yoy_comparison.plot(months, current, "Měsíc", "Příjmy (Kč)", "#27ae60")

            # Predikce (jednoduchý lineární trend)
            query = """
                SELECT
                    strftime('%Y-%m', created_date) as month,
                    SUM(total_price) as revenue
                FROM orders
                WHERE created_date >= date('now', '-6 months')
                AND status != 'Zrušeno'
                GROUP BY strftime('%Y-%m', created_date)
                ORDER BY month
            """
            results = db.fetch_all(query)
            if results and len(results) >= 3:
                revenues = [r[1] for r in results]
                avg_revenue = sum(revenues) / len(revenues)

                # Jednoduchá predikce = průměr + trend
                trend = (revenues[-1] - revenues[0]) / len(revenues) if len(revenues) > 1 else 0

                next_month = avg_revenue + trend
                next_quarter = next_month * 3

                growth_rate = (trend / avg_revenue * 100) if avg_revenue > 0 else 0

                self.pred_next_month.set_value(f"{next_month:,.0f} Kč")
                self.pred_next_quarter.set_value(f"{next_quarter:,.0f} Kč")
                self.pred_growth_rate.set_value(f"{growth_rate:.1f}%")

                # Graf predikce
                months = [r[0] for r in results]
                # Přidáme 3 budoucí měsíce
                future_months = months + ["Predikce 1", "Predikce 2", "Predikce 3"]
                future_revenues = revenues + [next_month] * 3

                self.chart_prediction.plot(future_months, future_revenues,
                                          "Měsíc", "Příjmy (Kč)", "#9b59b6")

        except Exception as e:
            print(f"Chyba při načítání trendů: {e}")
