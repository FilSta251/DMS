# -*- coding: utf-8 -*-
"""
Management KPI - Monitoring klíčových ukazatelů výkonu
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QFrame, QScrollArea, QMessageBox,
                             QDialog, QFormLayout, QDoubleSpinBox, QSpinBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
from .management_widgets import (MetricCard, ProgressCard, TrendCard,
                                 LineChartWidget, AnalyticsTable)
from database_manager import db
from datetime import datetime, timedelta


class KPITargets:
    """Třída pro uchování cílů KPI"""

    def __init__(self):
        # Výchozí cíle
        self.monthly_revenue = 500000  # Měsíční obrat
        self.monthly_orders = 50  # Počet zakázek za měsíc
        self.avg_order_value = 10000  # Průměrná hodnota zakázky
        self.mechanic_utilization = 80  # Využití mechaniků v %
        self.margin_target = 30  # Cílová marže v %
        self.customer_satisfaction = 90  # Spokojenost zákazníků v %

    def load_from_db(self):
        """Načtení cílů z databáze"""
        try:
            settings = {
                'kpi_monthly_revenue': 'monthly_revenue',
                'kpi_monthly_orders': 'monthly_orders',
                'kpi_avg_order_value': 'avg_order_value',
                'kpi_mechanic_utilization': 'mechanic_utilization',
                'kpi_margin_target': 'margin_target',
                'kpi_customer_satisfaction': 'customer_satisfaction'
            }

            for key, attr in settings.items():
                result = db.fetch_one("SELECT value FROM settings WHERE key = ?", (key,))
                if result:
                    setattr(self, attr, float(result[0]))

        except Exception as e:
            print(f"Chyba při načítání cílů: {e}")

    def save_to_db(self):
        """Uložení cílů do databáze"""
        try:
            settings = {
                'kpi_monthly_revenue': self.monthly_revenue,
                'kpi_monthly_orders': self.monthly_orders,
                'kpi_avg_order_value': self.avg_order_value,
                'kpi_mechanic_utilization': self.mechanic_utilization,
                'kpi_margin_target': self.margin_target,
                'kpi_customer_satisfaction': self.customer_satisfaction
            }

            for key, value in settings.items():
                db.execute_query("""
                    INSERT INTO settings (key, value, description)
                    VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = ?
                """, (key, str(value), f'KPI cíl: {key}', str(value)))

        except Exception as e:
            print(f"Chyba při ukládání cílů: {e}")


class ManagementKPI(QWidget):
    """KPI Monitoring"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_module = parent
        self.date_from = None
        self.date_to = None
        self.targets = KPITargets()
        self.targets.load_from_db()
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

        # Tlačítka nastavení
        self.create_settings_bar(content_layout)

        # KPI karty
        self.create_kpi_cards(content_layout)

        # Alerty
        self.create_alerts_section(content_layout)

        # Grafy trendů
        self.create_trends_section(content_layout)

        content_layout.addStretch()

    def create_settings_bar(self, parent_layout):
        """Horní lišta s nastavením"""
        settings_bar = QFrame()
        settings_bar.setObjectName("settingsBar")
        settings_layout = QHBoxLayout(settings_bar)

        title = QLabel("🎯 KPI Dashboard")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        settings_layout.addWidget(title)

        settings_layout.addStretch()

        # Tlačítko nastavení cílů
        btn_set_targets = QPushButton("⚙️ Nastavit cíle")
        btn_set_targets.clicked.connect(self.open_targets_dialog)
        btn_set_targets.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_layout.addWidget(btn_set_targets)

        # Tlačítko refresh
        btn_refresh = QPushButton("🔄 Obnovit")
        btn_refresh.clicked.connect(self.refresh)
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_layout.addWidget(btn_refresh)

        settings_bar.setStyleSheet("""
            QFrame#settingsBar {
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

        parent_layout.addWidget(settings_bar)

    def create_kpi_cards(self, parent_layout):
        """KPI karty s progress bary"""
        kpi_container = QFrame()
        kpi_layout = QGridLayout(kpi_container)
        kpi_layout.setSpacing(15)

        # Vytvoření karet
        self.kpi_revenue = ProgressCard("Měsíční obrat", 0, self.targets.monthly_revenue, "💰")
        self.kpi_orders = ProgressCard("Počet zakázek", 0, self.targets.monthly_orders, "📋")
        self.kpi_avg_order = ProgressCard("Průměrná zakázka", 0, self.targets.avg_order_value, "📊")
        self.kpi_utilization = ProgressCard("Využití mechaniků", 0, 100, "👨‍🔧")
        self.kpi_margin = ProgressCard("Marže", 0, 100, "💹")
        self.kpi_satisfaction = ProgressCard("Spokojenost", 0, 100, "⭐")

        kpi_layout.addWidget(self.kpi_revenue, 0, 0)
        kpi_layout.addWidget(self.kpi_orders, 0, 1)
        kpi_layout.addWidget(self.kpi_avg_order, 0, 2)
        kpi_layout.addWidget(self.kpi_utilization, 1, 0)
        kpi_layout.addWidget(self.kpi_margin, 1, 1)
        kpi_layout.addWidget(self.kpi_satisfaction, 1, 2)

        parent_layout.addWidget(kpi_container)

    def create_alerts_section(self, parent_layout):
        """Sekce s alerty"""
        alerts_frame = QFrame()
        alerts_frame.setObjectName("alertsFrame")
        alerts_layout = QVBoxLayout(alerts_frame)

        # Nadpis
        title = QLabel("⚠️ Alerty a doporučení")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        alerts_layout.addWidget(title)

        # Tabulka alertů
        self.table_alerts = AnalyticsTable()
        alerts_layout.addWidget(self.table_alerts)

        alerts_frame.setStyleSheet("""
            QFrame#alertsFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #e0e0e0;
            }
        """)

        parent_layout.addWidget(alerts_frame)

    def create_trends_section(self, parent_layout):
        """Sekce s trendy"""
        trends_container = QFrame()
        trends_layout = QVBoxLayout(trends_container)
        trends_layout.setSpacing(15)

        # Nadpis
        title = QLabel("📈 Trendy KPI")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        trends_layout.addWidget(title)

        # Grafy
        row1 = QHBoxLayout()

        self.chart_revenue_trend = LineChartWidget("Měsíční obrat vs cíl")
        row1.addWidget(self.chart_revenue_trend)

        self.chart_orders_trend = LineChartWidget("Počet zakázek vs cíl")
        row1.addWidget(self.chart_orders_trend)

        trends_layout.addLayout(row1)

        row2 = QHBoxLayout()

        self.chart_margin_trend = LineChartWidget("Marže vs cíl")
        row2.addWidget(self.chart_margin_trend)

        self.chart_utilization_trend = LineChartWidget("Využití mechaniků vs cíl")
        row2.addWidget(self.chart_utilization_trend)

        trends_layout.addLayout(row2)

        parent_layout.addWidget(trends_container)

    def refresh(self):
        """Refresh dat"""
        if self.date_from is None or self.date_to is None:
            # Aktuální měsíc
            self.date_to = QDate.currentDate()
            self.date_from = QDate(self.date_to.year(), self.date_to.month(), 1)

        self.load_kpi_data()
        self.check_alerts()
        self.load_trends()

    def set_date_range(self, date_from, date_to):
        """Nastavení období"""
        self.date_from = date_from
        self.date_to = date_to

    def load_kpi_data(self):
        """Načtení KPI dat"""
        try:
            date_from_str = self.date_from.toString("yyyy-MM-dd")
            date_to_str = self.date_to.toString("yyyy-MM-dd")

            # 1. Měsíční obrat
            query = """
                SELECT COALESCE(SUM(total_price), 0)
                FROM orders
                WHERE created_date BETWEEN ? AND ?
                AND status != 'Zrušeno'
            """
            result = db.fetch_one(query, (date_from_str, date_to_str))
            actual_revenue = result[0] if result else 0

            # Aktualizace karty s cílem
            self.kpi_revenue.max_value = self.targets.monthly_revenue
            self.kpi_revenue.set_value(actual_revenue)

            # 2. Počet zakázek
            query = """
                SELECT COUNT(*)
                FROM orders
                WHERE created_date BETWEEN ? AND ?
                AND status != 'Zrušeno'
            """
            result = db.fetch_one(query, (date_from_str, date_to_str))
            actual_orders = result[0] if result else 0

            self.kpi_orders.max_value = self.targets.monthly_orders
            self.kpi_orders.set_value(actual_orders)

            # 3. Průměrná hodnota zakázky
            avg_order = actual_revenue / actual_orders if actual_orders > 0 else 0

            self.kpi_avg_order.max_value = self.targets.avg_order_value
            self.kpi_avg_order.set_value(avg_order)

            # 4. Využití mechaniků
            query = """
                SELECT COALESCE(SUM(hours_worked), 0)
                FROM order_work_log
                WHERE date BETWEEN ? AND ?
            """
            result = db.fetch_one(query, (date_from_str, date_to_str))
            actual_hours = result[0] if result else 0

            # Počet mechaniků
            query = "SELECT COUNT(*) FROM users WHERE role = 'mechanik' AND active = 1"
            result = db.fetch_one(query)
            mechanic_count = result[0] if result else 1

            # Pracovní dny v období
            working_days = self.calculate_working_days(self.date_from, self.date_to)
            max_hours = mechanic_count * working_days * 8
            utilization = (actual_hours / max_hours * 100) if max_hours > 0 else 0

            self.kpi_utilization.max_value = 100
            self.kpi_utilization.set_value(utilization)

            # 5. Marže
            query = """
                SELECT
                    COALESCE(SUM(total_price), 0) as revenue,
                    COALESCE(SUM(material_cost), 0) as costs
                FROM orders
                WHERE created_date BETWEEN ? AND ?
                AND status != 'Zrušeno'
            """
            result = db.fetch_one(query, (date_from_str, date_to_str))
            if result:
                revenue = result[0]
                costs = result[1]
                margin = ((revenue - costs) / revenue * 100) if revenue > 0 else 0

                self.kpi_margin.max_value = 100
                self.kpi_margin.set_value(margin)

            # 6. Spokojenost zákazníků (simulovaná - můžeš nahradit skutečnými daty)
            # Pro ukázku použijeme náhodnou hodnotu kolem 85%
            satisfaction = 85  # TODO: Implementovat skutečné hodnocení

            self.kpi_satisfaction.max_value = 100
            self.kpi_satisfaction.set_value(satisfaction)

        except Exception as e:
            print(f"Chyba při načítání KPI: {e}")

    def check_alerts(self):
        """Kontrola alertů"""
        try:
            alerts = []

            # Získání aktuálních hodnot z karet
            revenue_progress = float(self.kpi_revenue.progress_bar.value())
            orders_progress = float(self.kpi_orders.progress_bar.value())
            avg_order_progress = float(self.kpi_avg_order.progress_bar.value())
            utilization_progress = float(self.kpi_utilization.progress_bar.value())
            margin_progress = float(self.kpi_margin.progress_bar.value())

            # Kontrola měsíčního obratu
            if revenue_progress < 70:
                severity = "🔴 Kritický"
                recommendation = f"Aktuálně na {revenue_progress:.0f}% cíle. Doporučení: Zvýšit marketingové aktivity a kontaktovat stávající zákazníky."
                alerts.append(("Měsíční obrat", severity, recommendation))
            elif revenue_progress < 90:
                severity = "🟡 Varování"
                recommendation = f"Aktuálně na {revenue_progress:.0f}% cíle. Blíží se konec měsíce, zvažte akční nabídky."
                alerts.append(("Měsíční obrat", severity, recommendation))
            else:
                severity = "🟢 OK"
                recommendation = f"Výborně! {revenue_progress:.0f}% cíle splněno."
                alerts.append(("Měsíční obrat", severity, recommendation))

            # Kontrola počtu zakázek
            if orders_progress < 70:
                severity = "🔴 Kritický"
                recommendation = f"Pouze {orders_progress:.0f}% cílového počtu zakázek. Doporučení: Aktivní telefonní kampaň k zákazníkům."
                alerts.append(("Počet zakázek", severity, recommendation))
            elif orders_progress < 90:
                severity = "🟡 Varování"
                recommendation = f"{orders_progress:.0f}% cíle. Kontaktujte zákazníky s blížící se servisní prohlídkou."
                alerts.append(("Počet zakázek", severity, recommendation))

            # Kontrola průměrné hodnoty
            if avg_order_progress < 80:
                severity = "🟡 Varování"
                recommendation = "Průměrná hodnota zakázky je nízká. Zvažte cross-selling a up-selling."
                alerts.append(("Průměrná zakázka", severity, recommendation))

            # Kontrola využití mechaniků
            if utilization_progress < 60:
                severity = "🟡 Varování"
                recommendation = f"Mechanici využiti pouze na {utilization_progress:.0f}%. Možná je potřeba více zakázek nebo optimalizace."
                alerts.append(("Využití mechaniků", severity, recommendation))
            elif utilization_progress > 95:
                severity = "🟡 Varování"
                recommendation = f"Přetížení mechaniků ({utilization_progress:.0f}%). Zvažte dodatečnou kapacitu nebo odmítnutí některých zakázek."
                alerts.append(("Využití mechaniků", severity, recommendation))

            # Kontrola marže
            target_margin = self.targets.margin_target
            actual_margin = margin_progress  # Progress bar ukazuje skutečnou hodnotu

            if actual_margin < target_margin * 0.7:
                severity = "🔴 Kritický"
                recommendation = f"Marže {actual_margin:.1f}% je pod cílem {target_margin:.0f}%. Zkontrolujte ceny materiálu a hodinové sazby."
                alerts.append(("Marže", severity, recommendation))
            elif actual_margin < target_margin:
                severity = "🟡 Varování"
                recommendation = f"Marže {actual_margin:.1f}% je pod cílem {target_margin:.0f}%. Optimalizujte náklady."
                alerts.append(("Marže", severity, recommendation))

            # Zobrazení alertů v tabulce
            if alerts:
                headers = ["KPI", "Stav", "Doporučení"]
                self.table_alerts.set_data(headers, alerts)
            else:
                self.table_alerts.set_data(["Info"], [["✅ Všechny KPI jsou v pořádku"]])

        except Exception as e:
            print(f"Chyba při kontrole alertů: {e}")

    def load_trends(self):
        """Načtení trendů KPI"""
        try:
            # Trend obratu (poslední 6 měsíců)
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
            if results:
                months = [r[0] for r in results]
                revenues = [r[1] for r in results]
                targets = [self.targets.monthly_revenue] * len(months)

                self.chart_revenue_trend.plot_multiple([
                    (months, revenues, "Skutečnost"),
                    (months, targets, "Cíl")
                ], "Měsíc", "Kč")

            # Trend počtu zakázek
            query = """
                SELECT
                    strftime('%Y-%m', created_date) as month,
                    COUNT(*) as count
                FROM orders
                WHERE created_date >= date('now', '-6 months')
                AND status != 'Zrušeno'
                GROUP BY strftime('%Y-%m', created_date)
                ORDER BY month
            """
            results = db.fetch_all(query)
            if results:
                months = [r[0] for r in results]
                counts = [r[1] for r in results]
                targets = [self.targets.monthly_orders] * len(months)

                self.chart_orders_trend.plot_multiple([
                    (months, counts, "Skutečnost"),
                    (months, targets, "Cíl")
                ], "Měsíc", "Počet")

            # Trend marže
            query = """
                SELECT
                    strftime('%Y-%m', created_date) as month,
                    CASE
                        WHEN SUM(total_price) > 0
                        THEN (SUM(total_price) - SUM(material_cost)) / SUM(total_price) * 100
                        ELSE 0
                    END as margin
                FROM orders
                WHERE created_date >= date('now', '-6 months')
                AND status != 'Zrušeno'
                GROUP BY strftime('%Y-%m', created_date)
                ORDER BY month
            """
            results = db.fetch_all(query)
            if results:
                months = [r[0] for r in results]
                margins = [r[1] for r in results]
                targets = [self.targets.margin_target] * len(months)

                self.chart_margin_trend.plot_multiple([
                    (months, margins, "Skutečnost"),
                    (months, targets, "Cíl")
                ], "Měsíc", "%")

            # Trend využití mechaniků (zjednodušený)
            query = """
                SELECT
                    strftime('%Y-%m', date) as month,
                    SUM(hours_worked) as total_hours
                FROM order_work_log
                WHERE date >= date('now', '-6 months')
                GROUP BY strftime('%Y-%m', date)
                ORDER BY month
            """
            results = db.fetch_all(query)
            if results:
                months = [r[0] for r in results]

                # Výpočet využití
                query_mechanics = "SELECT COUNT(*) FROM users WHERE role = 'mechanik' AND active = 1"
                mech_count = db.fetch_one(query_mechanics)
                mechanic_count = mech_count[0] if mech_count else 1

                utilizations = []
                for r in results:
                    # Zjednodušené: 20 pracovních dnů, 8 hodin denně
                    max_hours = mechanic_count * 20 * 8
                    util = (r[1] / max_hours * 100) if max_hours > 0 else 0
                    utilizations.append(util)

                targets = [self.targets.mechanic_utilization] * len(months)

                self.chart_utilization_trend.plot_multiple([
                    (months, utilizations, "Skutečnost"),
                    (months, targets, "Cíl")
                ], "Měsíc", "%")

        except Exception as e:
            print(f"Chyba při načítání trendů: {e}")

    def open_targets_dialog(self):
        """Otevření dialogu pro nastavení cílů"""
        dialog = TargetsDialog(self.targets, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.targets.save_to_db()
            self.refresh()
            QMessageBox.information(self, "Uloženo", "Cíle byly úspěšně uloženy.")

    def calculate_working_days(self, date_from, date_to):
        """Výpočet pracovních dnů"""
        working_days = 0
        current = date_from
        while current <= date_to:
            if current.dayOfWeek() <= 5:  # 1-5 = Po-Pá
                working_days += 1
            current = current.addDays(1)
        return working_days


class TargetsDialog(QDialog):
    """Dialog pro nastavení cílů KPI"""

    def __init__(self, targets, parent=None):
        super().__init__(parent)
        self.targets = targets
        self.setWindowTitle("⚙️ Nastavení cílů KPI")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # Formulář
        form_layout = QFormLayout()

        # Měsíční obrat
        self.spin_revenue = QDoubleSpinBox()
        self.spin_revenue.setRange(0, 10000000)
        self.spin_revenue.setValue(self.targets.monthly_revenue)
        self.spin_revenue.setSuffix(" Kč")
        self.spin_revenue.setDecimals(0)
        self.spin_revenue.setSingleStep(10000)
        form_layout.addRow("💰 Měsíční obrat:", self.spin_revenue)

        # Počet zakázek
        self.spin_orders = QSpinBox()
        self.spin_orders.setRange(0, 1000)
        self.spin_orders.setValue(int(self.targets.monthly_orders))
        self.spin_orders.setSuffix(" zakázek")
        form_layout.addRow("📋 Počet zakázek:", self.spin_orders)

        # Průměrná hodnota
        self.spin_avg_order = QDoubleSpinBox()
        self.spin_avg_order.setRange(0, 1000000)
        self.spin_avg_order.setValue(self.targets.avg_order_value)
        self.spin_avg_order.setSuffix(" Kč")
        self.spin_avg_order.setDecimals(0)
        self.spin_avg_order.setSingleStep(1000)
        form_layout.addRow("📊 Průměrná zakázka:", self.spin_avg_order)

        # Využití mechaniků
        self.spin_utilization = QSpinBox()
        self.spin_utilization.setRange(0, 100)
        self.spin_utilization.setValue(int(self.targets.mechanic_utilization))
        self.spin_utilization.setSuffix(" %")
        form_layout.addRow("👨‍🔧 Využití mechaniků:", self.spin_utilization)

        # Marže
        self.spin_margin = QSpinBox()
        self.spin_margin.setRange(0, 100)
        self.spin_margin.setValue(int(self.targets.margin_target))
        self.spin_margin.setSuffix(" %")
        form_layout.addRow("💹 Cílová marže:", self.spin_margin)

        # Spokojenost
        self.spin_satisfaction = QSpinBox()
        self.spin_satisfaction.setRange(0, 100)
        self.spin_satisfaction.setValue(int(self.targets.customer_satisfaction))
        self.spin_satisfaction.setSuffix(" %")
        form_layout.addRow("⭐ Spokojenost:", self.spin_satisfaction)

        layout.addLayout(form_layout)

        # Tlačítka
        buttons_layout = QHBoxLayout()

        btn_save = QPushButton("💾 Uložit")
        btn_save.clicked.connect(self.save_targets)
        buttons_layout.addWidget(btn_save)

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        layout.addLayout(buttons_layout)

    def save_targets(self):
        """Uložení cílů"""
        self.targets.monthly_revenue = self.spin_revenue.value()
        self.targets.monthly_orders = self.spin_orders.value()
        self.targets.avg_order_value = self.spin_avg_order.value()
        self.targets.mechanic_utilization = self.spin_utilization.value()
        self.targets.margin_target = self.spin_margin.value()
        self.targets.customer_satisfaction = self.spin_satisfaction.value()

        self.accept()
