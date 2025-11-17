# -*- coding: utf-8 -*-
"""
Statistiky a analýzy vozidel - grafy, přehledy, exporty
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QGroupBox, QMessageBox, QFileDialog, QSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QBrush, QPainter, QPen
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from datetime import datetime, date, timedelta
import config
from database_manager import db


class VehicleAnalyticsWidget(QWidget):
    """Widget pro statistiky a analýzy vozidel"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_data = {}
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Inicializace uživatelského rozhraní"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Hlavička s filtry
        header_panel = self.create_header_panel()
        main_layout.addWidget(header_panel)

        # Scrollovací oblast pro obsah
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f5f5f5;
            }
        """)

        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(20)

        # Statistické boxy
        stats_panel = self.create_stats_panel()
        self.content_layout.addWidget(stats_panel)

        # Grafy a tabulky
        charts_layout = QHBoxLayout()

        # Levý sloupec - grafy
        left_column = QVBoxLayout()

        # Graf značek
        self.brand_chart_group = self.create_brand_chart()
        left_column.addWidget(self.brand_chart_group)

        # Graf roku výroby
        self.year_chart_group = self.create_year_chart()
        left_column.addWidget(self.year_chart_group)

        charts_layout.addLayout(left_column)

        # Pravý sloupec - tabulky
        right_column = QVBoxLayout()

        # Top vozidla podle útraty
        self.top_vehicles_group = self.create_top_vehicles()
        right_column.addWidget(self.top_vehicles_group)

        # Průměrná cena podle značky
        self.avg_cost_group = self.create_avg_cost_table()
        right_column.addWidget(self.avg_cost_group)

        charts_layout.addLayout(right_column)

        self.content_layout.addLayout(charts_layout)

        # Sezónní trendy
        self.seasonal_group = self.create_seasonal_trends()
        self.content_layout.addWidget(self.seasonal_group)

        self.content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def create_header_panel(self):
        """Vytvoření hlavičky s filtry"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        layout = QHBoxLayout(panel)
        layout.setSpacing(15)

        # Titulek
        title = QLabel("📊 Analýzy a statistiky vozidel")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        layout.addStretch()

        # Filtr období
        period_label = QLabel("Období:")
        self.period_filter = QComboBox()
        self.period_filter.addItems([
            "Vše",
            "Tento měsíc",
            "Tento kvartál",
            "Tento rok",
            "Poslední rok",
            "Poslední 2 roky"
        ])
        self.period_filter.setMinimumWidth(150)
        self.period_filter.currentTextChanged.connect(self.apply_filters)

        layout.addWidget(period_label)
        layout.addWidget(self.period_filter)

        # Filtr značky
        brand_label = QLabel("Značka:")
        self.brand_filter = QComboBox()
        self.brand_filter.addItem("Vše")
        self.brand_filter.setMinimumWidth(150)
        self.brand_filter.currentTextChanged.connect(self.apply_filters)

        layout.addWidget(brand_label)
        layout.addWidget(self.brand_filter)

        # Filtr roku výroby
        year_label = QLabel("Rok výroby:")
        self.year_from = QSpinBox()
        self.year_from.setRange(1900, datetime.now().year)
        self.year_from.setValue(2000)
        self.year_from.setPrefix("od ")

        self.year_to = QSpinBox()
        self.year_to.setRange(1900, datetime.now().year + 1)
        self.year_to.setValue(datetime.now().year)
        self.year_to.setPrefix("do ")

        layout.addWidget(year_label)
        layout.addWidget(self.year_from)
        layout.addWidget(self.year_to)

        # Tlačítko obnovit
        btn_refresh = QPushButton("🔄 Obnovit")
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: #2980b9;
            }}
        """)
        btn_refresh.clicked.connect(self.load_data)
        layout.addWidget(btn_refresh)

        # Tlačítko export
        btn_export = QPushButton("📤 Export PDF")
        btn_export.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: #219a52;
            }}
        """)
        btn_export.clicked.connect(self.export_report)
        layout.addWidget(btn_export)

        return panel

    def create_stats_panel(self):
        """Vytvoření panelu se statistickými boxy"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        layout = QGridLayout(panel)
        layout.setSpacing(15)

        # Statistické karty
        self.stat_total = self.create_stat_card("🏍️ Celkem vozidel", "0", "#3498db")
        self.stat_stk_valid = self.create_stat_card("✅ Platná STK", "0", "#27ae60")
        self.stat_stk_warning = self.create_stat_card("⚠️ STK expiruje brzy", "0", "#f39c12")
        self.stat_stk_invalid = self.create_stat_card("❌ Neplatná STK", "0", "#e74c3c")
        self.stat_avg_cost = self.create_stat_card("💰 Průměrná útrata", "0 Kč", "#9b59b6")
        self.stat_avg_services = self.create_stat_card("🔧 Průměr servisů", "0", "#1abc9c")

        layout.addWidget(self.stat_total, 0, 0)
        layout.addWidget(self.stat_stk_valid, 0, 1)
        layout.addWidget(self.stat_stk_warning, 0, 2)
        layout.addWidget(self.stat_stk_invalid, 0, 3)
        layout.addWidget(self.stat_avg_cost, 0, 4)
        layout.addWidget(self.stat_avg_services, 0, 5)

        return panel

    def create_stat_card(self, label, value, color):
        """Vytvoření karty se statistikou"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                padding: 15px;
                min-width: 150px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(5)

        value_label = QLabel(value)
        value_label.setObjectName("stat_value")
        value_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel(label)
        text_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 11px;
            }
        """)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setWordWrap(True)

        layout.addWidget(value_label)
        layout.addWidget(text_label)

        return card

    def create_brand_chart(self):
        """Vytvoření koláčového grafu značek"""
        group = QGroupBox("📊 Rozložení podle značky")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout = QVBoxLayout(group)

        # Graf
        self.brand_chart = QChart()
        self.brand_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.brand_chart.legend().setVisible(True)
        self.brand_chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)

        chart_view = QChartView(self.brand_chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setMinimumHeight(300)

        layout.addWidget(chart_view)

        # Tabulka
        self.brand_table = QTableWidget()
        self.brand_table.setColumnCount(4)
        self.brand_table.setHorizontalHeaderLabels(["Značka", "Počet", "Procento", "Celková útrata"])
        self.brand_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.brand_table.setAlternatingRowColors(True)
        self.brand_table.setMaximumHeight(200)

        header = self.brand_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.brand_table)

        return group

    def create_year_chart(self):
        """Vytvoření sloupcového grafu roků výroby"""
        group = QGroupBox("📅 Rozložení podle roku výroby")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout = QVBoxLayout(group)

        # Graf
        self.year_chart = QChart()
        self.year_chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.year_chart.legend().setVisible(False)

        chart_view = QChartView(self.year_chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setMinimumHeight(250)

        layout.addWidget(chart_view)

        return group

    def create_top_vehicles(self):
        """Vytvoření tabulky top vozidel podle útraty"""
        group = QGroupBox("💰 Top 10 vozidel podle útraty")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout = QVBoxLayout(group)

        self.top_vehicles_table = QTableWidget()
        self.top_vehicles_table.setColumnCount(5)
        self.top_vehicles_table.setHorizontalHeaderLabels([
            "Pořadí", "SPZ", "Značka/Model", "Počet servisů", "Celková útrata"
        ])
        self.top_vehicles_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.top_vehicles_table.setAlternatingRowColors(True)

        header = self.top_vehicles_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.top_vehicles_table)

        return group

    def create_avg_cost_table(self):
        """Vytvoření tabulky průměrných nákladů podle značky"""
        group = QGroupBox("📈 Průměrná cena servisu podle značky")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout = QVBoxLayout(group)

        self.avg_cost_table = QTableWidget()
        self.avg_cost_table.setColumnCount(4)
        self.avg_cost_table.setHorizontalHeaderLabels([
            "Značka", "Počet servisů", "Průměrná cena", "Max cena"
        ])
        self.avg_cost_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.avg_cost_table.setAlternatingRowColors(True)

        header = self.avg_cost_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.avg_cost_table)

        return group

    def create_seasonal_trends(self):
        """Vytvoření přehledu sezónních trendů"""
        group = QGroupBox("🗓️ Sezónní trendy (počet servisů podle měsíce)")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout = QVBoxLayout(group)

        self.seasonal_table = QTableWidget()
        self.seasonal_table.setColumnCount(12)
        self.seasonal_table.setHorizontalHeaderLabels([
            "Led", "Úno", "Bře", "Dub", "Kvě", "Čer",
            "Čvc", "Srp", "Zář", "Říj", "Lis", "Pro"
        ])
        self.seasonal_table.setRowCount(1)
        self.seasonal_table.setVerticalHeaderLabels(["Počet servisů"])
        self.seasonal_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.seasonal_table.setMaximumHeight(80)

        header = self.seasonal_table.horizontalHeader()
        for i in range(12):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.seasonal_table)

        return group

    def load_data(self):
        """Načtení dat z databáze"""
        try:
            # Načtení vozidel
            vehicles = db.fetch_all("""
                SELECT v.*,
                       c.first_name || ' ' || c.last_name as customer_name
                FROM vehicles v
                LEFT JOIN customers c ON v.customer_id = c.id
            """)

            # Načtení zakázek
            orders = db.fetch_all("""
                SELECT o.*, v.brand, v.model, v.license_plate
                FROM orders o
                JOIN vehicles v ON o.vehicle_id = v.id
            """)

            self.all_data = {
                'vehicles': vehicles,
                'orders': orders
            }

            # Aktualizace filtru značek
            brands = set()
            for v in vehicles:
                if v['brand']:
                    brands.add(v['brand'])

            current_brand = self.brand_filter.currentText()
            self.brand_filter.blockSignals(True)
            self.brand_filter.clear()
            self.brand_filter.addItem("Vše")
            for brand in sorted(brands):
                self.brand_filter.addItem(brand)
            if current_brand in ["Vše"] + list(brands):
                self.brand_filter.setCurrentText(current_brand)
            self.brand_filter.blockSignals(False)

            self.apply_filters()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst data:\n{e}")

    def apply_filters(self):
        """Aplikace filtrů a aktualizace zobrazení"""
        if not self.all_data:
            return

        vehicles = self.all_data.get('vehicles', [])
        orders = self.all_data.get('orders', [])

        # Filtr značky
        brand_filter = self.brand_filter.currentText()
        if brand_filter != "Vše":
            vehicles = [v for v in vehicles if v['brand'] == brand_filter]
            orders = [o for o in orders if o['brand'] == brand_filter]

        # Filtr roku výroby
        year_from = self.year_from.value()
        year_to = self.year_to.value()
        vehicles = [v for v in vehicles if v['year'] is None or (year_from <= v['year'] <= year_to)]

        # Filtr období pro zakázky
        period_filter = self.period_filter.currentText()
        if period_filter != "Vše":
            today = date.today()

            if period_filter == "Tento měsíc":
                cutoff = date(today.year, today.month, 1)
            elif period_filter == "Tento kvartál":
                quarter_month = ((today.month - 1) // 3) * 3 + 1
                cutoff = date(today.year, quarter_month, 1)
            elif period_filter == "Tento rok":
                cutoff = date(today.year, 1, 1)
            elif period_filter == "Poslední rok":
                cutoff = today - timedelta(days=365)
            elif period_filter == "Poslední 2 roky":
                cutoff = today - timedelta(days=730)
            else:
                cutoff = None

            if cutoff:
                filtered_orders = []
                for o in orders:
                    if o['created_date']:
                        try:
                            order_date = datetime.strptime(str(o['created_date']), "%Y-%m-%d").date()
                            if order_date >= cutoff:
                                filtered_orders.append(o)
                        except:
                            pass
                orders = filtered_orders

        # Aktualizace zobrazení
        self.update_statistics(vehicles, orders)
        self.update_brand_chart(vehicles, orders)
        self.update_year_chart(vehicles)
        self.update_top_vehicles(vehicles, orders)
        self.update_avg_cost_table(orders)
        self.update_seasonal_trends(orders)

    def update_statistics(self, vehicles, orders):
        """Aktualizace statistických boxů"""
        total = len(vehicles)

        today = date.today()
        warning_date = today + timedelta(days=30)

        stk_valid = 0
        stk_warning = 0
        stk_invalid = 0

        for v in vehicles:
            if v['stk_valid_until']:
                try:
                    stk_date = datetime.strptime(str(v['stk_valid_until']), "%Y-%m-%d").date()
                    if stk_date < today:
                        stk_invalid += 1
                    elif stk_date <= warning_date:
                        stk_warning += 1
                    else:
                        stk_valid += 1
                except:
                    pass

        # Průměrná útrata na vozidlo
        vehicle_costs = {}
        for o in orders:
            vid = o['vehicle_id']
            if vid not in vehicle_costs:
                vehicle_costs[vid] = 0
            vehicle_costs[vid] += o['total_price'] or 0

        if vehicle_costs:
            avg_cost = sum(vehicle_costs.values()) / len(vehicle_costs)
        else:
            avg_cost = 0

        # Průměrný počet servisů
        if total > 0:
            avg_services = len(orders) / total
        else:
            avg_services = 0

        # Aktualizace hodnot
        self.stat_total.findChild(QLabel, "stat_value").setText(str(total))
        self.stat_stk_valid.findChild(QLabel, "stat_value").setText(str(stk_valid))
        self.stat_stk_warning.findChild(QLabel, "stat_value").setText(str(stk_warning))
        self.stat_stk_invalid.findChild(QLabel, "stat_value").setText(str(stk_invalid))
        self.stat_avg_cost.findChild(QLabel, "stat_value").setText(f"{avg_cost:,.0f} Kč".replace(",", " "))
        self.stat_avg_services.findChild(QLabel, "stat_value").setText(f"{avg_services:.1f}")

    def update_brand_chart(self, vehicles, orders):
        """Aktualizace grafu značek"""
        # Seskupení podle značky
        brand_data = {}
        for v in vehicles:
            brand = v['brand'] or 'Neznámá'
            if brand not in brand_data:
                brand_data[brand] = {'count': 0, 'cost': 0}
            brand_data[brand]['count'] += 1

        # Přidání nákladů
        for o in orders:
            brand = o['brand'] or 'Neznámá'
            if brand in brand_data:
                brand_data[brand]['cost'] += o['total_price'] or 0

        # Graf
        self.brand_chart.removeAllSeries()
        series = QPieSeries()

        colors = ["#3498db", "#27ae60", "#f39c12", "#e74c3c", "#9b59b6", "#1abc9c", "#34495e"]

        total = sum(d['count'] for d in brand_data.values())

        for idx, (brand, data) in enumerate(sorted(brand_data.items(), key=lambda x: x[1]['count'], reverse=True)):
            slice_ = series.append(brand, data['count'])
            slice_.setColor(QColor(colors[idx % len(colors)]))
            if total > 0 and data['count'] / total > 0.05:
                slice_.setLabelVisible(True)

        self.brand_chart.addSeries(series)

        # Tabulka
        self.brand_table.setRowCount(0)
        for brand, data in sorted(brand_data.items(), key=lambda x: x[1]['count'], reverse=True):
            row = self.brand_table.rowCount()
            self.brand_table.insertRow(row)

            self.brand_table.setItem(row, 0, QTableWidgetItem(brand))
            self.brand_table.setItem(row, 1, QTableWidgetItem(str(data['count'])))

            if total > 0:
                percent = (data['count'] / total) * 100
                self.brand_table.setItem(row, 2, QTableWidgetItem(f"{percent:.1f} %"))
            else:
                self.brand_table.setItem(row, 2, QTableWidgetItem("0 %"))

            self.brand_table.setItem(row, 3, QTableWidgetItem(f"{data['cost']:,.0f} Kč".replace(",", " ")))

    def update_year_chart(self, vehicles):
        """Aktualizace grafu roků výroby"""
        # Seskupení podle roku
        year_data = {}
        for v in vehicles:
            if v['year']:
                year = v['year']
                if year not in year_data:
                    year_data[year] = 0
                year_data[year] += 1

        # Graf
        self.year_chart.removeAllSeries()

        if year_data:
            series = QBarSeries()
            bar_set = QBarSet("Počet vozidel")
            bar_set.setColor(QColor("#3498db"))

            categories = []
            for year in sorted(year_data.keys()):
                bar_set.append(year_data[year])
                categories.append(str(year))

            series.append(bar_set)
            self.year_chart.addSeries(series)

            # Osy
            axis_x = QBarCategoryAxis()
            axis_x.append(categories)
            self.year_chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            series.attachAxis(axis_x)

            axis_y = QValueAxis()
            axis_y.setRange(0, max(year_data.values()) + 1)
            self.year_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
            series.attachAxis(axis_y)

    def update_top_vehicles(self, vehicles, orders):
        """Aktualizace tabulky top vozidel"""
        # Seskupení podle vozidla
        vehicle_data = {}
        for v in vehicles:
            vehicle_data[v['id']] = {
                'spz': v['license_plate'],
                'brand_model': f"{v['brand']} {v['model']}",
                'count': 0,
                'cost': 0
            }

        for o in orders:
            vid = o['vehicle_id']
            if vid in vehicle_data:
                vehicle_data[vid]['count'] += 1
                vehicle_data[vid]['cost'] += o['total_price'] or 0

        # Seřazení podle útraty
        sorted_vehicles = sorted(vehicle_data.values(), key=lambda x: x['cost'], reverse=True)[:10]

        # Tabulka
        self.top_vehicles_table.setRowCount(0)
        for idx, data in enumerate(sorted_vehicles):
            row = self.top_vehicles_table.rowCount()
            self.top_vehicles_table.insertRow(row)

            # Pořadí
            rank_item = QTableWidgetItem(str(idx + 1))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.top_vehicles_table.setItem(row, 0, rank_item)

            # SPZ
            spz_item = QTableWidgetItem(data['spz'])
            spz_font = spz_item.font()
            spz_font.setBold(True)
            spz_item.setFont(spz_font)
            self.top_vehicles_table.setItem(row, 1, spz_item)

            # Značka/Model
            self.top_vehicles_table.setItem(row, 2, QTableWidgetItem(data['brand_model']))

            # Počet servisů
            self.top_vehicles_table.setItem(row, 3, QTableWidgetItem(str(data['count'])))

            # Útrata
            cost_item = QTableWidgetItem(f"{data['cost']:,.0f} Kč".replace(",", " "))
            cost_font = cost_item.font()
            cost_font.setBold(True)
            cost_item.setFont(cost_font)
            self.top_vehicles_table.setItem(row, 4, cost_item)

    def update_avg_cost_table(self, orders):
        """Aktualizace tabulky průměrných nákladů"""
        # Seskupení podle značky
        brand_costs = {}
        for o in orders:
            brand = o['brand'] or 'Neznámá'
            if brand not in brand_costs:
                brand_costs[brand] = []
            brand_costs[brand].append(o['total_price'] or 0)

        # Tabulka
        self.avg_cost_table.setRowCount(0)
        for brand in sorted(brand_costs.keys()):
            costs = brand_costs[brand]

            row = self.avg_cost_table.rowCount()
            self.avg_cost_table.insertRow(row)

            self.avg_cost_table.setItem(row, 0, QTableWidgetItem(brand))
            self.avg_cost_table.setItem(row, 1, QTableWidgetItem(str(len(costs))))

            avg = sum(costs) / len(costs) if costs else 0
            self.avg_cost_table.setItem(row, 2, QTableWidgetItem(f"{avg:,.0f} Kč".replace(",", " ")))

            max_cost = max(costs) if costs else 0
            self.avg_cost_table.setItem(row, 3, QTableWidgetItem(f"{max_cost:,.0f} Kč".replace(",", " ")))

    def update_seasonal_trends(self, orders):
        """Aktualizace sezónních trendů"""
        # Počet servisů podle měsíce
        monthly_counts = {i: 0 for i in range(1, 13)}

        for o in orders:
            if o['created_date']:
                try:
                    order_date = datetime.strptime(str(o['created_date']), "%Y-%m-%d")
                    monthly_counts[order_date.month] += 1
                except:
                    pass

        # Aktualizace tabulky
        for month in range(1, 13):
            item = QTableWidgetItem(str(monthly_counts[month]))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Barevné zvýraznění
            count = monthly_counts[month]
            max_count = max(monthly_counts.values()) if monthly_counts.values() else 1

            if count == max_count and count > 0:
                item.setBackground(QBrush(QColor("#27ae60")))
                item.setForeground(QBrush(QColor("white")))
            elif count > max_count * 0.7:
                item.setBackground(QBrush(QColor("#f39c12")))

            self.seasonal_table.setItem(0, month - 1, item)

    def export_report(self):
        """Export reportu do PDF"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exportovat report",
                f"analyza_vozidel_{datetime.now().strftime('%Y%m%d')}.pdf",
                "PDF soubory (*.pdf)"
            )

            if not file_path:
                return

            doc = SimpleDocTemplate(file_path, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()

            # Titulek
            elements.append(Paragraph("Analýza vozidel - Report", styles['Title']))
            elements.append(Spacer(1, 20))

            # Datum
            elements.append(Paragraph(f"Vygenerováno: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Normal']))
            elements.append(Spacer(1, 20))

            # Statistiky
            elements.append(Paragraph("Základní statistiky", styles['Heading2']))

            stats_data = [
                ["Celkem vozidel", self.stat_total.findChild(QLabel, "stat_value").text()],
                ["Platná STK", self.stat_stk_valid.findChild(QLabel, "stat_value").text()],
                ["STK expiruje brzy", self.stat_stk_warning.findChild(QLabel, "stat_value").text()],
                ["Neplatná STK", self.stat_stk_invalid.findChild(QLabel, "stat_value").text()],
                ["Průměrná útrata", self.stat_avg_cost.findChild(QLabel, "stat_value").text()],
                ["Průměr servisů", self.stat_avg_services.findChild(QLabel, "stat_value").text()]
            ]

            stats_table = Table(stats_data, colWidths=[200, 150])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(stats_table)
            elements.append(Spacer(1, 20))

            # Top vozidla
            elements.append(Paragraph("Top 10 vozidel podle útraty", styles['Heading2']))

            top_data = [["Pořadí", "SPZ", "Značka/Model", "Počet servisů", "Útrata"]]
            for row in range(self.top_vehicles_table.rowCount()):
                row_data = []
                for col in range(self.top_vehicles_table.columnCount()):
                    item = self.top_vehicles_table.item(row, col)
                    row_data.append(item.text() if item else "")
                top_data.append(row_data)

            top_table = Table(top_data, colWidths=[50, 80, 150, 80, 100])
            top_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(top_table)

            doc.build(elements)
            QMessageBox.information(self, "Export dokončen", f"Report byl exportován do:\n{file_path}")

        except ImportError:
            QMessageBox.warning(
                self,
                "Chybí knihovna",
                "Pro export PDF je potřeba nainstalovat reportlab:\n\npip install reportlab"
            )
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se exportovat report:\n{e}")
