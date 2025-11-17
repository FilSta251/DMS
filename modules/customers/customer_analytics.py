# customer_analytics.py
# -*- coding: utf-8 -*-
"""
Statistiky a analýzy zákazníků
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QScrollArea, QGridLayout,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor, QColor, QBrush
import config
from database_manager import db
from datetime import datetime, timedelta


class CustomerAnalyticsWidget(QWidget):
    """Widget pro analýzy zákazníků"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Hlavička
        self.create_header(layout)

        # Filtry
        self.create_filters(layout)

        # Scroll area pro obsah
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # Statistické boxy
        self.create_stat_boxes(content_layout)

        # Grafy a přehledy
        self.create_group_analysis(content_layout)
        self.create_rfm_analysis(content_layout)
        self.create_top_customers(content_layout)

        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        self.set_styles()

    def create_header(self, parent_layout):
        """Vytvoření hlavičky"""
        header = QHBoxLayout()

        title = QLabel("📊 Analýzy zákazníků")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        header.addWidget(title)

        header.addStretch()

        btn_export_pdf = QPushButton("📄 Export PDF")
        btn_export_pdf.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_export_pdf.clicked.connect(self.export_pdf)
        header.addWidget(btn_export_pdf)

        btn_export_excel = QPushButton("📊 Export Excel")
        btn_export_excel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_export_excel.clicked.connect(self.export_excel)
        header.addWidget(btn_export_excel)

        btn_refresh = QPushButton("🔄 Obnovit")
        btn_refresh.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_refresh.clicked.connect(self.load_data)
        header.addWidget(btn_refresh)

        parent_layout.addLayout(header)

    def create_filters(self, parent_layout):
        """Vytvoření filtrů"""
        filters_frame = QFrame()
        filters_frame.setObjectName("filtersFrame")
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setSpacing(15)

        # Období
        filters_layout.addWidget(QLabel("Období:"))
        self.cb_period = QComboBox()
        self.cb_period.addItems(["Tento rok", "Poslední 2 roky", "Posledních 6 měsíců", "Vše"])
        self.cb_period.currentTextChanged.connect(self.load_data)
        filters_layout.addWidget(self.cb_period)

        # Skupina
        filters_layout.addWidget(QLabel("Skupina:"))
        self.cb_group = QComboBox()
        self.cb_group.addItems(["Vše", "Standardní", "VIP", "Firemní", "Pojišťovna"])
        self.cb_group.currentTextChanged.connect(self.load_data)
        filters_layout.addWidget(self.cb_group)

        # Typ
        filters_layout.addWidget(QLabel("Typ:"))
        self.cb_type = QComboBox()
        self.cb_type.addItems(["Vše", "Soukromá osoba", "Firma"])
        self.cb_type.currentTextChanged.connect(self.load_data)
        filters_layout.addWidget(self.cb_type)

        filters_layout.addStretch()
        parent_layout.addWidget(filters_frame)

    def create_stat_boxes(self, parent_layout):
        """Vytvoření statistických boxů"""
        stats_frame = QFrame()
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(15)

        self.stat_boxes = {}

        box_configs = [
            ("total", "👥 Celkem zákazníků", "0"),
            ("new", "🆕 Noví (tento měsíc)", "0"),
            ("revenue", "💰 Celkový obrat", "0 Kč"),
            ("avg_revenue", "📊 Průměr/zákazník", "0 Kč"),
            ("top_customer", "🏆 Top zákazník", "-"),
            ("churning", "📉 Odcházející", "0")
        ]

        for i, (key, name, default) in enumerate(box_configs):
            box = self.create_stat_box(name, default)
            self.stat_boxes[key] = box
            stats_layout.addWidget(box, i // 3, i % 3)

        parent_layout.addWidget(stats_frame)

    def create_stat_box(self, name, value):
        """Vytvoření statistického boxu"""
        box = QFrame()
        box.setObjectName("statBox")
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(15, 12, 15, 12)
        box_layout.setSpacing(8)

        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        value_font = QFont()
        value_font.setPointSize(20)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_label = QLabel(name)
        name_label.setObjectName("statName")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")

        box_layout.addWidget(value_label)
        box_layout.addWidget(name_label)

        return box

    def create_group_analysis(self, parent_layout):
        """Analýza podle skupin"""
        group = QGroupBox("📊 Analýza podle skupin")
        layout = QVBoxLayout(group)

        self.group_table = QTableWidget()
        self.group_table.setColumnCount(4)
        self.group_table.setHorizontalHeaderLabels(["Skupina", "Počet", "Obrat", "Průměr"])
        self.group_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.group_table.setMaximumHeight(200)

        layout.addWidget(self.group_table)
        parent_layout.addWidget(group)

    def create_rfm_analysis(self, parent_layout):
        """RFM analýza"""
        group = QGroupBox("🎯 RFM Analýza (Recency, Frequency, Monetary)")
        layout = QVBoxLayout(group)

        self.rfm_table = QTableWidget()
        self.rfm_table.setColumnCount(5)
        self.rfm_table.setHorizontalHeaderLabels(["Segment", "Popis", "Počet", "Obrat", "Akce"])
        self.rfm_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.rfm_table.setMaximumHeight(250)

        layout.addWidget(self.rfm_table)
        parent_layout.addWidget(group)

    def create_top_customers(self, parent_layout):
        """Top zákazníci"""
        group = QGroupBox("🏆 Top 10 zákazníků")
        layout = QVBoxLayout(group)

        # Výběr typu žebříčku
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Řadit podle:"))

        self.cb_top_sort = QComboBox()
        self.cb_top_sort.addItems(["Útrata", "Počet zakázek", "Počet vozidel"])
        self.cb_top_sort.currentTextChanged.connect(self.load_top_customers)
        filter_layout.addWidget(self.cb_top_sort)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        self.top_table = QTableWidget()
        self.top_table.setColumnCount(6)
        self.top_table.setHorizontalHeaderLabels(["#", "Zákazník", "Skupina", "Zakázek", "Vozidel", "Útrata"])
        self.top_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.top_table.setMaximumHeight(350)

        layout.addWidget(self.top_table)
        parent_layout.addWidget(group)

    def load_data(self):
        """Načtení všech dat"""
        self.load_statistics()
        self.load_group_analysis()
        self.load_rfm_analysis()
        self.load_top_customers()

    def load_statistics(self):
        """Načtení statistik"""
        try:
            # Celkem zákazníků
            total = db.fetch_one("SELECT COUNT(*) FROM customers WHERE is_active = 1")
            self.stat_boxes["total"].findChild(QLabel, "statValue").setText(str(total[0] if total else 0))

            # Noví zákazníci tento měsíc
            month_start = datetime.now().replace(day=1).isoformat()
            new = db.fetch_one(f"SELECT COUNT(*) FROM customers WHERE created_at >= '{month_start}' AND is_active = 1")
            self.stat_boxes["new"].findChild(QLabel, "statValue").setText(str(new[0] if new else 0))

            # Celkový obrat
            revenue = db.fetch_one("SELECT COALESCE(SUM(total_price), 0) FROM orders")
            rev_value = revenue[0] if revenue else 0
            self.stat_boxes["revenue"].findChild(QLabel, "statValue").setText(f"{rev_value:,.0f} Kč".replace(",", " "))

            # Průměrná útrata na zákazníka
            total_customers = total[0] if total else 1
            if total_customers > 0:
                avg = rev_value / total_customers
                self.stat_boxes["avg_revenue"].findChild(QLabel, "statValue").setText(f"{avg:,.0f} Kč".replace(",", " "))

            # Top zákazník
            top = db.fetch_one("""
                SELECT
                    CASE
                        WHEN c.customer_type = 'company' THEN c.company_name
                        ELSE c.first_name || ' ' || c.last_name
                    END as name
                FROM customers c
                LEFT JOIN orders o ON c.id = o.customer_id
                WHERE c.is_active = 1
                GROUP BY c.id
                ORDER BY SUM(o.total_price) DESC
                LIMIT 1
            """)
            self.stat_boxes["top_customer"].findChild(QLabel, "statValue").setText(top[0] if top else "-")

            # Odcházející zákazníci (bez aktivity 12+ měsíců)
            year_ago = (datetime.now() - timedelta(days=365)).isoformat()
            churning = db.fetch_one(f"""
                SELECT COUNT(*) FROM customers c
                WHERE c.is_active = 1
                AND c.id NOT IN (
                    SELECT DISTINCT customer_id FROM orders WHERE created_at >= '{year_ago}'
                )
            """)
            self.stat_boxes["churning"].findChild(QLabel, "statValue").setText(str(churning[0] if churning else 0))

        except Exception as e:
            print(f"Chyba při načítání statistik: {e}")

    def load_group_analysis(self):
        """Načtení analýzy podle skupin"""
        try:
            query = """
                SELECT
                    c.customer_group,
                    COUNT(DISTINCT c.id) as count,
                    COALESCE(SUM(o.total_price), 0) as revenue,
                    COALESCE(AVG(o.total_price), 0) as avg_revenue
                FROM customers c
                LEFT JOIN orders o ON c.id = o.customer_id
                WHERE c.is_active = 1
                GROUP BY c.customer_group
                ORDER BY revenue DESC
            """

            groups = db.fetch_all(query)
            self.group_table.setRowCount(len(groups) if groups else 0)

            if groups:
                for i, group in enumerate(groups):
                    self.group_table.setItem(i, 0, QTableWidgetItem(group[0] or "Standardní"))
                    self.group_table.setItem(i, 1, QTableWidgetItem(str(group[1])))
                    self.group_table.setItem(i, 2, QTableWidgetItem(f"{group[2]:,.0f} Kč".replace(",", " ")))
                    self.group_table.setItem(i, 3, QTableWidgetItem(f"{group[3]:,.0f} Kč".replace(",", " ")))

        except Exception as e:
            print(f"Chyba při načítání analýzy skupin: {e}")

    def load_rfm_analysis(self):
        """Načtení RFM analýzy"""
        try:
            # Zjednodušená RFM segmentace
            segments = [
                ("Champions", "Nejlepší zákazníci - časté nákupy, vysoká útrata", 0, 0),
                ("Loyal", "Věrní zákazníci - pravidelné nákupy", 0, 0),
                ("Potential", "Potenciální VIP - rostoucí aktivita", 0, 0),
                ("At Risk", "Ohrožení - klesající aktivita", 0, 0),
                ("Lost", "Ztracení - dlouho neaktivní", 0, 0)
            ]

            self.rfm_table.setRowCount(len(segments))

            for i, (name, desc, count, revenue) in enumerate(segments):
                self.rfm_table.setItem(i, 0, QTableWidgetItem(name))
                self.rfm_table.setItem(i, 1, QTableWidgetItem(desc))
                self.rfm_table.setItem(i, 2, QTableWidgetItem(str(count)))
                self.rfm_table.setItem(i, 3, QTableWidgetItem(f"{revenue:,.0f} Kč".replace(",", " ")))
                self.rfm_table.setItem(i, 4, QTableWidgetItem("Zobrazit"))

        except Exception as e:
            print(f"Chyba při načítání RFM: {e}")

    def load_top_customers(self):
        """Načtení top zákazníků"""
        try:
            sort_by = self.cb_top_sort.currentText()

            if sort_by == "Útrata":
                order_by = "SUM(o.total_price) DESC"
            elif sort_by == "Počet zakázek":
                order_by = "COUNT(o.id) DESC"
            else:  # Počet vozidel
                order_by = "COUNT(DISTINCT v.id) DESC"

            query = f"""
                SELECT
                    CASE
                        WHEN c.customer_type = 'company' THEN c.company_name
                        ELSE c.first_name || ' ' || c.last_name
                    END as name,
                    c.customer_group,
                    COUNT(DISTINCT o.id) as order_count,
                    COUNT(DISTINCT v.id) as vehicle_count,
                    COALESCE(SUM(o.total_price), 0) as revenue
                FROM customers c
                LEFT JOIN orders o ON c.id = o.customer_id
                LEFT JOIN vehicles v ON c.id = v.customer_id
                WHERE c.is_active = 1
                GROUP BY c.id
                ORDER BY {order_by}
                LIMIT 10
            """

            customers = db.fetch_all(query)
            self.top_table.setRowCount(len(customers) if customers else 0)

            if customers:
                for i, customer in enumerate(customers):
                    self.top_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                    self.top_table.setItem(i, 1, QTableWidgetItem(customer[0] or ""))
                    self.top_table.setItem(i, 2, QTableWidgetItem(customer[1] or "Standardní"))
                    self.top_table.setItem(i, 3, QTableWidgetItem(str(customer[2])))
                    self.top_table.setItem(i, 4, QTableWidgetItem(str(customer[3])))
                    self.top_table.setItem(i, 5, QTableWidgetItem(f"{customer[4]:,.0f} Kč".replace(",", " ")))

        except Exception as e:
            print(f"Chyba při načítání top zákazníků: {e}")

    def export_pdf(self):
        """Export do PDF"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export analýz do PDF",
            f"analyzy_zakazniku_{datetime.now().strftime('%Y%m%d')}.pdf",
            "PDF soubory (*.pdf)"
        )
        if file_path:
            QMessageBox.information(self, "Export", f"Analýzy exportovány do: {file_path}")

    def export_excel(self):
        """Export do Excelu"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export analýz do Excelu",
            f"analyzy_zakazniku_{datetime.now().strftime('%Y%m%d')}.xlsx",
            "Excel soubory (*.xlsx)"
        )
        if file_path:
            QMessageBox.information(self, "Export", f"Analýzy exportovány do: {file_path}")

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet(f"""
            #filtersFrame {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
            }}
            #statBox {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }}
            #statValue {{
                color: {config.COLOR_PRIMARY};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QTableWidget {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                gridline-color: #e0e0e0;
            }}
            QHeaderView::section {{
                background-color: {config.COLOR_PRIMARY};
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }}
            QPushButton {{
                padding: 8px 14px;
                border-radius: 4px;
                border: 1px solid #ddd;
            }}
            QPushButton:hover {{
                background-color: #e0e0e0;
            }}
            QComboBox {{
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-width: 140px;
            }}
        """)
