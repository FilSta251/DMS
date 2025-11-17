# -*- coding: utf-8 -*-
"""
Management Trends - Trendy, predikce a forecasting
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QFrame, QScrollArea, QTabWidget,
                             QComboBox, QSpinBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from .management_widgets import (MetricCard, TrendCard, LineChartWidget,
                                 BarChartWidget, PieChartWidget, AnalyticsTable)
from database_manager import db
from datetime import datetime, timedelta


class ManagementTrends(QWidget):
    """Trendy, predikce a forecasting"""

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

        # Hlavní metriky trendů
        self.create_trend_metrics(content_layout)

        # Filtry
        self.create_filters(content_layout)

        # Záložky s analýzami
        self.create_analysis_tabs(content_layout)

        content_layout.addStretch()

    def create_trend_metrics(self, parent_layout):
        """Hlavní metriky trendů"""
        metrics_container = QFrame()
        metrics_layout = QGridLayout(metrics_container)
        metrics_layout.setSpacing(15)

        # Karty
        self.metric_growth_rate = TrendCard("Míra růstu", "0%", "+0%", True, "📈")
        self.metric_avg_trend = TrendCard("Průměrný trend", "0 Kč", "+0%", True, "📊")
        self.metric_seasonality = MetricCard("Sezónní index", "1.0", "🌡️")
        self.metric_yoy_growth = TrendCard("YoY růst", "0%", "+0%", True, "📅")
        self.metric_qoq_growth = TrendCard("QoQ růst", "0%", "+0%", True, "📆")
        self.metric_prediction_accuracy = MetricCard("Přesnost predikce", "0%", "🎯")

        metrics_layout.addWidget(self.metric_growth_rate, 0, 0)
        metrics_layout.addWidget(self.metric_avg_trend, 0, 1)
        metrics_layout.addWidget(self.metric_seasonality, 0, 2)
        metrics_layout.addWidget(self.metric_yoy_growth, 1, 0)
        metrics_layout.addWidget(self.metric_qoq_growth, 1, 1)
        metrics_layout.addWidget(self.metric_prediction_accuracy, 1, 2)

        parent_layout.addWidget(metrics_container)

    def create_filters(self, parent_layout):
        """Filtry"""
        filters_frame = QFrame()
        filters_frame.setObjectName("filtersFrame")
        filters_layout = QHBoxLayout(filters_frame)

        # Typ analýzy
        type_label = QLabel("Typ analýzy:")
        type_label.setStyleSheet("font-weight: bold;")
        filters_layout.addWidget(type_label)

        self.filter_analysis_type = QComboBox()
        self.filter_analysis_type.addItems(["Denní", "Týdenní", "Měsíční", "Čtvrtletní"])
        self.filter_analysis_type.setCurrentIndex(2)  # Měsíční jako výchozí
        self.filter_analysis_type.currentIndexChanged.connect(self.on_filter_changed)
        filters_layout.addWidget(self.filter_analysis_type)

        filters_layout.addSpacing(20)

        # Období predikce
        pred_label = QLabel("Predikce na:")
        pred_label.setStyleSheet("font-weight: bold;")
        filters_layout.addWidget(pred_label)

        self.spin_prediction_periods = QSpinBox()
        self.spin_prediction_periods.setRange(1, 12)
        self.spin_prediction_periods.setValue(3)
        self.spin_prediction_periods.setSuffix(" období")
        self.spin_prediction_periods.valueChanged.connect(self.on_filter_changed)
        filters_layout.addWidget(self.spin_prediction_periods)

        filters_layout.addStretch()

        # Tlačítko refresh
        refresh_btn = QPushButton("🔄 Přepočítat")
        refresh_btn.clicked.connect(self.refresh)
        filters_layout.addWidget(refresh_btn)

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
        """Záložky s analýzami"""
        tabs = QTabWidget()
        tabs.setObjectName("analysisTabs")

        # Tab 1: Časové trendy
        tab_time_trends = self.create_time_trends_tab()
        tabs.addTab(tab_time_trends, "📊 Časové trendy")

        # Tab 2: Sezónnost
        tab_seasonality = self.create_seasonality_tab()
        tabs.addTab(tab_seasonality, "🌡️ Sezónnost")

        # Tab 3: Srovnání
        tab_comparison = self.create_comparison_tab()
        tabs.addTab(tab_comparison, "⚖️ Srovnání")

        # Tab 4: Predikce obratu
        tab_revenue_pred = self.create_revenue_prediction_tab()
        tabs.addTab(tab_revenue_pred, "💰 Predikce obratu")

        # Tab 5: Predikce zakázek
        tab_orders_pred = self.create_orders_prediction_tab()
        tabs.addTab(tab_orders_pred, "📋 Predikce zakázek")

        # Tab 6: Predikce skladu
        tab_warehouse_pred = self.create_warehouse_prediction_tab()
        tabs.addTab(tab_warehouse_pred, "📦 Predikce skladu")

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

    def create_time_trends_tab(self):
        """Tab s časovými trendy"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Grafy
        row1 = QHBoxLayout()

        self.chart_revenue_trend = LineChartWidget("Trend obratu")
        row1.addWidget(self.chart_revenue_trend)

        self.chart_orders_trend = LineChartWidget("Trend zakázek")
        row1.addWidget(self.chart_orders_trend)

        layout.addLayout(row1)

        # Druhý řádek
        row2 = QHBoxLayout()

        self.chart_moving_average = LineChartWidget("Klouzavý průměr (3 období)")
        row2.addWidget(self.chart_moving_average)

        self.chart_growth_curve = LineChartWidget("Růstová křivka")
        row2.addWidget(self.chart_growth_curve)

        layout.addLayout(row2)

        # Tabulka trendů
        table_label = QLabel("📊 Detailní trendy")
        label_font = QFont()
        label_font.setPointSize(12)
        label_font.setBold(True)
        table_label.setFont(label_font)
        layout.addWidget(table_label)

        self.table_trends = AnalyticsTable()
        layout.addWidget(self.table_trends)

        return tab

    def create_seasonality_tab(self):
        """Tab se sezónností"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Grafy sezónnosti
        row1 = QHBoxLayout()

        self.chart_monthly_pattern = BarChartWidget("Měsíční sezónní vzorec")
        row1.addWidget(self.chart_monthly_pattern)

        self.chart_weekly_pattern = BarChartWidget("Týdenní vzorec")
        row1.addWidget(self.chart_weekly_pattern)

        layout.addLayout(row1)

        # Heatmapa sezónnosti (simulace)
        seasonality_frame = QFrame()
        seasonality_frame.setObjectName("seasonalityFrame")
        seasonality_layout = QVBoxLayout(seasonality_frame)

        season_title = QLabel("🌡️ Sezónní indexy")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        season_title.setFont(title_font)
        seasonality_layout.addWidget(season_title)

        self.table_seasonality = AnalyticsTable()
        seasonality_layout.addWidget(self.table_seasonality)

        seasonality_frame.setStyleSheet("""
            QFrame#seasonalityFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout.addWidget(seasonality_frame)

        return tab

    def create_comparison_tab(self):
        """Tab se srovnáním"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Grafy srovnání
        row1 = QHBoxLayout()

        self.chart_yoy_comparison = BarChartWidget("Meziroční srovnání (YoY)")
        row1.addWidget(self.chart_yoy_comparison)

        self.chart_qoq_comparison = BarChartWidget("Mezičtvrtletní (QoQ)")
        row1.addWidget(self.chart_qoq_comparison)

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

    def create_revenue_prediction_tab(self):
        """Tab s predikcí obratu"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Metriky predikce
        pred_metrics = QFrame()
        pred_metrics_layout = QGridLayout(pred_metrics)
        pred_metrics_layout.setSpacing(15)

        self.pred_revenue_next = MetricCard("Příští období", "0 Kč", "📅")
        self.pred_revenue_quarter = MetricCard("Příští kvartál", "0 Kč", "📆")
        self.pred_revenue_year = MetricCard("Příští rok", "0 Kč", "📊")
        self.pred_revenue_confidence = MetricCard("Spolehlivost", "0%", "🎯")

        pred_metrics_layout.addWidget(self.pred_revenue_next, 0, 0)
        pred_metrics_layout.addWidget(self.pred_revenue_quarter, 0, 1)
        pred_metrics_layout.addWidget(self.pred_revenue_year, 1, 0)
        pred_metrics_layout.addWidget(self.pred_revenue_confidence, 1, 1)

        layout.addWidget(pred_metrics)

        # Graf predikce
        self.chart_revenue_prediction = LineChartWidget("Predikce obratu s intervalem spolehlivosti")
        layout.addWidget(self.chart_revenue_prediction)

        # Tabulka predikce
        pred_table_label = QLabel("💰 Detailní predikce obratu")
        label_font = QFont()
        label_font.setPointSize(12)
        label_font.setBold(True)
        pred_table_label.setFont(label_font)
        layout.addWidget(pred_table_label)

        self.table_revenue_prediction = AnalyticsTable()
        layout.addWidget(self.table_revenue_prediction)

        return tab

    def create_orders_prediction_tab(self):
        """Tab s predikcí zakázek"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Metriky
        pred_metrics = QFrame()
        pred_metrics_layout = QGridLayout(pred_metrics)
        pred_metrics_layout.setSpacing(15)

        self.pred_orders_next = MetricCard("Zakázek příští měsíc", "0", "📋")
        self.pred_orders_avg_value = MetricCard("Průměrná hodnota", "0 Kč", "💰")
        self.pred_orders_capacity = MetricCard("Vytížení kapacity", "0%", "⚙️")

        pred_metrics_layout.addWidget(self.pred_orders_next, 0, 0)
        pred_metrics_layout.addWidget(self.pred_orders_avg_value, 0, 1)
        pred_metrics_layout.addWidget(self.pred_orders_capacity, 0, 2)

        layout.addWidget(pred_metrics)

        # Grafy
        row = QHBoxLayout()

        self.chart_orders_prediction = LineChartWidget("Predikce počtu zakázek")
        row.addWidget(self.chart_orders_prediction)

        self.chart_orders_by_type = PieChartWidget("Predikované rozdělení typů")
        row.addWidget(self.chart_orders_by_type)

        layout.addLayout(row)

        return tab

    def create_warehouse_prediction_tab(self):
        """Tab s predikcí skladu"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Info
        info = QLabel(
            "📦 Predikce potřeby skladu vychází z historické spotřeby a trendů.\n"
            "Pomáhá plánovat nákupy a udržovat optimální stavy."
        )
        info.setStyleSheet("padding: 10px; background-color: #e8f4f8; border-radius: 5px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Graf predikce
        self.chart_warehouse_prediction = LineChartWidget("Predikce potřeby top položek")
        layout.addWidget(self.chart_warehouse_prediction)

        # Tabulka doporučení
        table_label = QLabel("📋 Doporučené objednávky")
        label_font = QFont()
        label_font.setPointSize(12)
        label_font.setBold(True)
        table_label.setFont(label_font)
        layout.addWidget(table_label)

        self.table_warehouse_prediction = AnalyticsTable()
        layout.addWidget(self.table_warehouse_prediction)

        return tab

    def refresh(self):
        """Refresh dat"""
        if self.date_from is None or self.date_to is None:
            self.date_to = QDate.currentDate()
            self.date_from = self.date_to.addMonths(-12)

        self.load_trend_metrics()
        self.load_time_trends()
        self.load_seasonality()
        self.load_comparison()
        self.load_revenue_prediction()
        self.load_orders_prediction()
        self.load_warehouse_prediction()

    def set_date_range(self, date_from, date_to):
        """Nastavení období"""
        self.date_from = date_from
        self.date_to = date_to

    def on_filter_changed(self):
        """Změna filtru"""
        # Placeholder - pro budoucí implementaci
        pass

    def load_trend_metrics(self):
        """Načtení metrik trendů"""
        try:
            # Získání dat za poslední rok
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

            if len(results) >= 2:
                revenues = [r[1] for r in results]

                # Míra růstu (poslední vs první)
                growth_rate = ((revenues[-1] - revenues[0]) / revenues[0] * 100) if revenues[0] > 0 else 0
                trend_direction = growth_rate >= 0

                self.metric_growth_rate.set_value(
                    f"{abs(growth_rate):.1f}%",
                    f"{abs(growth_rate):.1f}%",
                    trend_direction
                )

                # Průměrný trend
                avg_revenue = sum(revenues) / len(revenues)
                avg_growth = ((revenues[-1] - avg_revenue) / avg_revenue * 100) if avg_revenue > 0 else 0

                self.metric_avg_trend.set_value(
                    f"{avg_revenue:,.0f} Kč",
                    f"{abs(avg_growth):.1f}%",
                    avg_growth >= 0
                )

                # Sezónní index (zjednodušený)
                if len(revenues) >= 12:
                    current_month_idx = datetime.now().month - 1
                    seasonal_index = revenues[-1] / avg_revenue if avg_revenue > 0 else 1
                    self.metric_seasonality.set_value(f"{seasonal_index:.2f}")

            # YoY růst
            current_year = datetime.now().year
            query_yoy = f"""
                SELECT
                    SUM(CASE WHEN strftime('%Y', created_date) = '{current_year}' THEN total_price ELSE 0 END) as current,
                    SUM(CASE WHEN strftime('%Y', created_date) = '{current_year-1}' THEN total_price ELSE 0 END) as last
                FROM orders
                WHERE status != 'Zrušeno'
            """
            result = db.fetch_one(query_yoy)
            if result:
                current_year_rev = result[0] or 0
                last_year_rev = result[1] or 0
                yoy_growth = ((current_year_rev - last_year_rev) / last_year_rev * 100) if last_year_rev > 0 else 0

                self.metric_yoy_growth.set_value(
                    f"{abs(yoy_growth):.1f}%",
                    f"{abs(yoy_growth):.1f}%",
                    yoy_growth >= 0
                )

            # QoQ růst (zjednodušený)
            current_quarter = (datetime.now().month - 1) // 3 + 1
            self.metric_qoq_growth.set_value("0%", "0%", True)

            # Přesnost predikce (placeholder)
            self.metric_prediction_accuracy.set_value("85%")

        except Exception as e:
            print(f"Chyba při načítání metrik trendů: {e}")

    def load_time_trends(self):
        """Načtení časových trendů"""
        try:
            analysis_type = self.filter_analysis_type.currentText()

            # Určení formátu podle typu
            if analysis_type == "Denní":
                date_format = "%Y-%m-%d"
                period = "-30 days"
            elif analysis_type == "Týdenní":
                date_format = "%Y-%W"
                period = "-24 weeks"
            elif analysis_type == "Čtvrtletní":
                date_format = "%Y-Q"
                period = "-24 months"
            else:  # Měsíční
                date_format = "%Y-%m"
                period = "-12 months"

            # Trend obratu
            query = f"""
                SELECT
                    strftime('{date_format}', created_date) as period,
                    SUM(total_price) as revenue
                FROM orders
                WHERE created_date >= date('now', '{period}')
                AND status != 'Zrušeno'
                GROUP BY period
                ORDER BY period
            """
            results = db.fetch_all(query)

            if results:
                periods = [r[0] for r in results]
                revenues = [r[1] for r in results]

                self.chart_revenue_trend.plot(periods, revenues, "Období", "Obrat (Kč)", "#3498db")

                # Klouzavý průměr
                if len(revenues) >= 3:
                    moving_avg = []
                    for i in range(len(revenues)):
                        if i < 2:
                            moving_avg.append(revenues[i])
                        else:
                            avg = (revenues[i-2] + revenues[i-1] + revenues[i]) / 3
                            moving_avg.append(avg)

                    self.chart_moving_average.plot_multiple([
                        (periods, revenues, "Skutečnost"),
                        (periods, moving_avg, "Klouzavý průměr")
                    ], "Období", "Kč")

                # Růstová křivka
                growth_curve = [revenues[0]]
                for i in range(1, len(revenues)):
                    growth = ((revenues[i] - revenues[i-1]) / revenues[i-1] * 100) if revenues[i-1] > 0 else 0
                    growth_curve.append(growth)

                self.chart_growth_curve.plot(periods, growth_curve, "Období", "Růst (%)", "#27ae60")

            # Trend zakázek
            query_orders = f"""
                SELECT
                    strftime('{date_format}', created_date) as period,
                    COUNT(*) as order_count
                FROM orders
                WHERE created_date >= date('now', '{period}')
                AND status != 'Zrušeno'
                GROUP BY period
                ORDER BY period
            """
            results = db.fetch_all(query_orders)

            if results:
                periods = [r[0] for r in results]
                counts = [r[1] for r in results]
                self.chart_orders_trend.plot(periods, counts, "Období", "Počet", "#e74c3c")

            # Tabulka trendů
            if results:
                headers = ["Období", "Zakázky", "Obrat", "Průměr/zakázka", "Růst %"]
                data = []

                query_detail = f"""
                    SELECT
                        strftime('{date_format}', created_date) as period,
                        COUNT(*) as orders,
                        SUM(total_price) as revenue,
                        AVG(total_price) as avg_value
                    FROM orders
                    WHERE created_date >= date('now', '{period}')
                    AND status != 'Zrušeno'
                    GROUP BY period
                    ORDER BY period
                """
                results = db.fetch_all(query_detail)

                prev_revenue = 0
                for r in results:
                    growth = ((r[2] - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
                    data.append([
                        r[0],
                        r[1],
                        f"{r[2]:,.0f} Kč",
                        f"{r[3]:,.0f} Kč",
                        f"{growth:+.1f}%"
                    ])
                    prev_revenue = r[2]

                self.table_trends.set_data(headers, data)

        except Exception as e:
            print(f"Chyba při načítání trendů: {e}")

    def load_seasonality(self):
        """Načtení sezónnosti"""
        try:
            # Měsíční vzorec
            query = """
                SELECT
                    CAST(strftime('%m', created_date) AS INTEGER) as month_num,
                    AVG(total_price) as avg_revenue,
                    COUNT(*) as order_count
                FROM orders
                WHERE status != 'Zrušeno'
                GROUP BY month_num
                ORDER BY month_num
            """
            results = db.fetch_all(query)

            if results:
                month_names = ["Led", "Úno", "Bře", "Dub", "Kvě", "Čer",
                              "Čvc", "Srp", "Zář", "Říj", "Lis", "Pro"]
                months = [month_names[r[0]-1] if r[0] <= 12 else f"M{r[0]}" for r in results]
                avg_revenues = [r[1] for r in results]

                self.chart_monthly_pattern.plot(months, avg_revenues,
                                                "Měsíc", "Průměrný obrat (Kč)", "#3498db")

                # Výpočet sezónních indexů
                overall_avg = sum(avg_revenues) / len(avg_revenues) if avg_revenues else 1
                seasonal_indices = [rev / overall_avg for rev in avg_revenues]

                # Tabulka sezónnosti
                headers = ["Měsíc", "Průměrný obrat", "Zakázek", "Sezónní index", "Kategorie"]
                data = []

                for i, r in enumerate(results):
                    index = seasonal_indices[i]
                    if index > 1.15:
                        category = "🔥 Vysoká sezóna"
                    elif index > 0.85:
                        category = "➡️ Normální"
                    else:
                        category = "❄️ Nízká sezóna"

                    data.append([
                        months[i],
                        f"{r[1]:,.0f} Kč",
                        r[2],
                        f"{index:.2f}",
                        category
                    ])

                self.table_seasonality.set_data(headers, data)

            # Týdenní vzorec (den v týdnu)
            query_weekly = """
                SELECT
                    CAST(strftime('%w', created_date) AS INTEGER) as day_of_week,
                    COUNT(*) as order_count
                FROM orders
                WHERE status != 'Zrušeno'
                GROUP BY day_of_week
                ORDER BY day_of_week
            """
            results = db.fetch_all(query_weekly)

            if results:
                day_names = ["Ne", "Po", "Út", "St", "Čt", "Pá", "So"]
                days = [day_names[r[0]] for r in results]
                counts = [r[1] for r in results]

                self.chart_weekly_pattern.plot(days, counts,
                                              "Den v týdnu", "Zakázek", "#27ae60")

        except Exception as e:
            print(f"Chyba při načítání sezónnosti: {e}")

    def load_comparison(self):
        """Načtení srovnání"""
        try:
            current_year = datetime.now().year

            # YoY srovnání
            query_yoy = f"""
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
            results = db.fetch_all(query_yoy)

            if results:
                month_names = ["Led", "Úno", "Bře", "Dub", "Kvě", "Čer",
                              "Čvc", "Srp", "Zář", "Říj", "Lis", "Pro"]
                months = [month_names[r[0]-1] for r in results if r[0] <= 12]
                current = [r[1] for r in results if r[0] <= 12]

                # Pro zjednodušení použijeme sloupcový graf
                self.chart_yoy_comparison.plot(months[:len(current)], current,
                                              "Měsíc", f"Obrat {current_year} (Kč)", "#3498db")

            # QoQ srovnání (poslední 4 kvartály)
            query_qoq = """
                SELECT
                    strftime('%Y', created_date) || '-Q' ||
                    CAST((CAST(strftime('%m', created_date) AS INTEGER) - 1) / 3 + 1 AS TEXT) as quarter,
                    SUM(total_price) as revenue
                FROM orders
                WHERE created_date >= date('now', '-18 months')
                AND status != 'Zrušeno'
                GROUP BY quarter
                ORDER BY quarter DESC
                LIMIT 4
            """
            results = db.fetch_all(query_qoq)

            if results:
                quarters = [r[0] for r in reversed(results)]
                revenues = [r[1] for r in reversed(results)]

                self.chart_qoq_comparison.plot(quarters, revenues,
                                              "Kvartál", "Obrat (Kč)", "#e74c3c")

            # Srovnávací tabulka
            headers = ["Měsíc", f"{current_year}", f"{current_year-1}", "Změna", "% změna"]
            data = []

            query_detail = f"""
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
            results = db.fetch_all(query_detail)

            for r in results:
                if r[0] <= 12:
                    month_name = month_names[r[0]-1]
                    current_val = r[1]
                    last_val = r[2]
                    change = current_val - last_val
                    pct_change = (change / last_val * 100) if last_val > 0 else 0

                    data.append([
                        month_name,
                        f"{current_val:,.0f} Kč",
                        f"{last_val:,.0f} Kč",
                        f"{change:+,.0f} Kč",
                        f"{pct_change:+.1f}%"
                    ])

            self.table_comparison.set_data(headers, data)

        except Exception as e:
            print(f"Chyba při načítání srovnání: {e}")

    def load_revenue_prediction(self):
        """Načtení predikce obratu"""
        try:
            # Historická data za 12 měsíců
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

            if len(results) >= 3:
                revenues = [r[1] for r in results]

                # Jednoduchá lineární predikce
                n = len(revenues)
                sum_x = sum(range(n))
                sum_y = sum(revenues)
                sum_xy = sum(i * revenues[i] for i in range(n))
                sum_x2 = sum(i * i for i in range(n))

                # Koeficienty lineární regrese
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0
                intercept = (sum_y - slope * sum_x) / n

                # Predikce na příštích N období
                periods = self.spin_prediction_periods.value()
                predictions = []
                for i in range(n, n + periods):
                    pred = slope * i + intercept
                    predictions.append(max(0, pred))  # Zabránit záporným hodnotám

                # Metriky
                if predictions:
                    self.pred_revenue_next.set_value(f"{predictions[0]:,.0f} Kč")

                    if len(predictions) >= 3:
                        quarter_pred = sum(predictions[:3])
                        self.pred_revenue_quarter.set_value(f"{quarter_pred:,.0f} Kč")

                    year_pred = sum(predictions) if len(predictions) >= 12 else sum(predictions) * (12 / len(predictions))
                    self.pred_revenue_year.set_value(f"{year_pred:,.0f} Kč")

                    # Spolehlivost (zjednodušená - na základě variability dat)
                    avg = sum(revenues) / len(revenues)
                    variance = sum((r - avg) ** 2 for r in revenues) / len(revenues)
                    cv = (variance ** 0.5) / avg if avg > 0 else 0
                    confidence = max(0, 100 - cv * 100)
                    self.pred_revenue_confidence.set_value(f"{confidence:.0f}%")

                # Graf s predikcí
                months = [r[0] for r in results]
                future_months = [f"Predikce {i+1}" for i in range(periods)]
                all_months = months + future_months
                all_revenues = revenues + predictions

                self.chart_revenue_prediction.plot_multiple([
                    (months, revenues, "Historická data"),
                    (future_months, predictions, "Predikce")
                ], "Měsíc", "Obrat (Kč)")

                # Tabulka predikce
                headers = ["Období", "Predikovaný obrat", "Dolní interval", "Horní interval"]
                data = []

                for i, pred in enumerate(predictions):
                    # Interval spolehlivosti ±15%
                    lower = pred * 0.85
                    upper = pred * 1.15

                    data.append([
                        future_months[i],
                        f"{pred:,.0f} Kč",
                        f"{lower:,.0f} Kč",
                        f"{upper:,.0f} Kč"
                    ])

                self.table_revenue_prediction.set_data(headers, data)

        except Exception as e:
            print(f"Chyba při načítání predikce obratu: {e}")

    def load_orders_prediction(self):
        """Načtení predikce zakázek"""
        try:
            # Historická data
            query = """
                SELECT
                    COUNT(*) as order_count,
                    AVG(total_price) as avg_value
                FROM orders
                WHERE created_date >= date('now', '-3 months')
                AND status != 'Zrušeno'
            """
            result = db.fetch_one(query)

            if result:
                # Průměrný počet zakázek za měsíc
                avg_orders_per_month = result[0] / 3
                avg_value = result[1] or 0

                # Predikce pro příští měsíc (s malým růstem 5%)
                predicted_orders = int(avg_orders_per_month * 1.05)

                self.pred_orders_next.set_value(str(predicted_orders))
                self.pred_orders_avg_value.set_value(f"{avg_value:,.0f} Kč")

                # Vytížení kapacity (předpokládáme 100 zakázek/měsíc jako maximum)
                capacity = (predicted_orders / 100 * 100) if predicted_orders <= 100 else 100
                self.pred_orders_capacity.set_value(f"{capacity:.0f}%")

            # Graf predikce počtu
            query_trend = """
                SELECT
                    strftime('%Y-%m', created_date) as month,
                    COUNT(*) as order_count
                FROM orders
                WHERE created_date >= date('now', '-6 months')
                AND status != 'Zrušeno'
                GROUP BY month
                ORDER BY month
            """
            results = db.fetch_all(query_trend)

            if len(results) >= 3:
                months = [r[0] for r in results]
                counts = [r[1] for r in results]

                # Jednoduchá predikce
                avg_count = sum(counts) / len(counts)
                trend = (counts[-1] - counts[0]) / len(counts) if len(counts) > 1 else 0

                periods = 3
                predictions = []
                for i in range(periods):
                    pred = avg_count + trend * (len(counts) + i)
                    predictions.append(max(0, int(pred)))

                future_months = [f"Predikce {i+1}" for i in range(periods)]

                self.chart_orders_prediction.plot_multiple([
                    (months, counts, "Historická data"),
                    (future_months, predictions, "Predikce")
                ], "Měsíc", "Počet zakázek")

            # Rozdělení podle typů
            query_types = """
                SELECT
                    order_type,
                    COUNT(*) as count
                FROM orders
                WHERE created_date >= date('now', '-3 months')
                AND status != 'Zrušeno'
                GROUP BY order_type
            """
            results = db.fetch_all(query_types)

            if results:
                labels = [r[0] for r in results]
                sizes = [r[1] for r in results]
                self.chart_orders_by_type.plot(labels, sizes)

        except Exception as e:
            print(f"Chyba při načítání predikce zakázek: {e}")

    def load_warehouse_prediction(self):
        """Načtení predikce skladu"""
        try:
            # Top 10 položek podle spotřeby
            query = """
                SELECT
                    w.name,
                    w.quantity as current_stock,
                    COALESCE(SUM(wm.quantity), 0) as total_issued
                FROM warehouse w
                LEFT JOIN warehouse_movements wm ON w.id = wm.item_id
                    AND wm.movement_type = 'Výdej'
                    AND wm.date >= date('now', '-3 months')
                GROUP BY w.id, w.name, w.quantity
                HAVING total_issued > 0
                ORDER BY total_issued DESC
                LIMIT 10
            """
            results = db.fetch_all(query)

            if results:
                # Graf predikce
                names = [r[0][:20] for r in results]  # Zkrátit názvy
                current_stocks = [r[1] for r in results]

                self.chart_warehouse_prediction.plot(names, current_stocks,
                                                     "Položka", "Aktuální stav", "#3498db")

                # Tabulka doporučení
                headers = ["Položka", "Aktuální stav", "Spotřeba/měsíc", "Dní zásoby", "Doporučení"]
                data = []

                for r in results:
                    name = r[0]
                    current = r[1]
                    issued = r[2]

                    # Spotřeba za měsíc
                    monthly_consumption = issued / 3

                    # Dny zásoby
                    days_supply = (current / (monthly_consumption / 30)) if monthly_consumption > 0 else 999

                    # Doporučení
                    if days_supply < 15:
                        recommendation = "🔴 Objednat ihned"
                    elif days_supply < 30:
                        recommendation = "🟡 Objednat brzy"
                    else:
                        recommendation = "🟢 Dostatečná zásoba"

                    data.append([
                        name,
                        f"{current:.1f}",
                        f"{monthly_consumption:.1f}",
                        f"{int(days_supply)} dní" if days_supply < 999 else "∞",
                        recommendation
                    ])

                self.table_warehouse_prediction.set_data(headers, data)

        except Exception as e:
            print(f"Chyba při načítání predikce skladu: {e}")
