# -*- coding: utf-8 -*-
"""
Společné widgety pro manažerský modul
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
                             QDateEdit, QPushButton, QComboBox, QProgressBar)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class MetricCard(QFrame):
    """Karta zobrazující jednu metriku"""

    def __init__(self, title, value, icon="📊", parent=None):
        super().__init__(parent)
        self.setObjectName("metricCard")
        self.init_ui(title, value, icon)

    def init_ui(self, title, value, icon):
        """Inicializace UI"""
        self.setFixedHeight(120)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # Ikona a titulek
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 12px;")

        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Hodnota
        self.value_label = QLabel(str(value))
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setStyleSheet("color: #2c3e50;")

        layout.addLayout(header_layout)
        layout.addWidget(self.value_label)
        layout.addStretch()

        self.setStyleSheet("""
            QFrame#metricCard {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)

    def set_value(self, value):
        """Nastavení hodnoty"""
        self.value_label.setText(str(value))


class TrendCard(QFrame):
    """Karta s metrikou a trendem"""

    def __init__(self, title, value, trend_value, trend_up=True, icon="📈", parent=None):
        super().__init__(parent)
        self.setObjectName("trendCard")
        self.init_ui(title, value, trend_value, trend_up, icon)

    def init_ui(self, title, value, trend_value, trend_up, icon):
        """Inicializace UI"""
        self.setFixedHeight(120)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # Ikona a titulek
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 12px;")

        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Hodnota a trend
        value_layout = QHBoxLayout()

        self.value_label = QLabel(str(value))
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setStyleSheet("color: #2c3e50;")

        # Trend
        trend_icon = "↑" if trend_up else "↓"
        trend_color = "#27ae60" if trend_up else "#e74c3c"
        self.trend_label = QLabel(f"{trend_icon} {trend_value}")
        self.trend_label.setStyleSheet(f"color: {trend_color}; font-size: 14px; font-weight: bold;")

        value_layout.addWidget(self.value_label)
        value_layout.addWidget(self.trend_label, alignment=Qt.AlignmentFlag.AlignBottom)
        value_layout.addStretch()

        layout.addLayout(header_layout)
        layout.addLayout(value_layout)
        layout.addStretch()

        self.setStyleSheet("""
            QFrame#trendCard {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)

    def set_value(self, value, trend_value, trend_up=True):
        """Nastavení hodnoty a trendu"""
        self.value_label.setText(str(value))
        trend_icon = "↑" if trend_up else "↓"
        trend_color = "#27ae60" if trend_up else "#e74c3c"
        self.trend_label.setText(f"{trend_icon} {trend_value}")
        self.trend_label.setStyleSheet(f"color: {trend_color}; font-size: 14px; font-weight: bold;")


class ProgressCard(QFrame):
    """Karta s progress barem"""

    def __init__(self, title, value, max_value, icon="🎯", parent=None):
        super().__init__(parent)
        self.setObjectName("progressCard")
        self.max_value = max_value
        self.init_ui(title, value, icon)

    def init_ui(self, title, value, icon):
        """Inicializace UI"""
        self.setFixedHeight(120)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # Ikona a titulek
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 12px;")

        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Hodnota
        self.value_label = QLabel(f"{value} / {self.max_value}")
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setStyleSheet("color: #2c3e50;")

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(int((value / self.max_value) * 100) if self.max_value > 0 else 0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat(f"{int((value / self.max_value) * 100) if self.max_value > 0 else 0}%")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)

        layout.addLayout(header_layout)
        layout.addWidget(self.value_label)
        layout.addWidget(self.progress_bar)

        self.setStyleSheet("""
            QFrame#progressCard {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
        """)

    def set_value(self, value):
        """Nastavení hodnoty"""
        self.value_label.setText(f"{value} / {self.max_value}")
        percentage = int((value / self.max_value) * 100) if self.max_value > 0 else 0
        self.progress_bar.setValue(percentage)
        self.progress_bar.setFormat(f"{percentage}%")


class ChartWidget(QWidget):
    """Základní widget pro grafy"""

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.title = title
        self.figure = Figure(figsize=(8, 6), facecolor='white')
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if self.title:
            title_label = QLabel(self.title)
            title_font = QFont()
            title_font.setPointSize(14)
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setStyleSheet("color: #2c3e50; padding: 10px;")
            layout.addWidget(title_label)

        layout.addWidget(self.canvas)

    def clear(self):
        """Vymazání grafu"""
        self.ax.clear()
        self.canvas.draw()


class LineChartWidget(ChartWidget):
    """Widget pro čárový graf"""

    def __init__(self, title="", parent=None):
        super().__init__(title, parent)

    def plot(self, x_data, y_data, xlabel="", ylabel="", color="#3498db", label=""):
        """Vykreslení čárového grafu"""
        self.ax.clear()
        self.ax.plot(x_data, y_data, color=color, linewidth=2, marker='o', label=label)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.grid(True, alpha=0.3)
        if label:
            self.ax.legend()
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_multiple(self, data_series, xlabel="", ylabel=""):
        """Vykreslení více čar"""
        self.ax.clear()
        colors = ['#3498db', '#e74c3c', '#27ae60', '#f39c12', '#9b59b6']
        for i, (x_data, y_data, label) in enumerate(data_series):
            color = colors[i % len(colors)]
            self.ax.plot(x_data, y_data, color=color, linewidth=2, marker='o', label=label)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.grid(True, alpha=0.3)
        self.ax.legend()
        self.figure.tight_layout()
        self.canvas.draw()


class BarChartWidget(ChartWidget):
    """Widget pro sloupcový graf"""

    def __init__(self, title="", parent=None):
        super().__init__(title, parent)

    def plot(self, x_data, y_data, xlabel="", ylabel="", color="#3498db"):
        """Vykreslení sloupcového grafu"""
        self.ax.clear()
        self.ax.bar(x_data, y_data, color=color, alpha=0.8)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.grid(True, alpha=0.3, axis='y')

        # Rotace popisků na ose X pokud je jich hodně
        if len(x_data) > 5:
            plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

        self.figure.tight_layout()
        self.canvas.draw()


class PieChartWidget(ChartWidget):
    """Widget pro koláčový graf"""

    def __init__(self, title="", parent=None):
        super().__init__(title, parent)

    def plot(self, labels, sizes, colors=None):
        """Vykreslení koláčového grafu"""
        self.ax.clear()
        if colors is None:
            colors = ['#3498db', '#e74c3c', '#27ae60', '#f39c12', '#9b59b6', '#1abc9c', '#34495e']

        # Filtrování nulových hodnot
        filtered_data = [(l, s) for l, s in zip(labels, sizes) if s > 0]
        if not filtered_data:
            return

        labels, sizes = zip(*filtered_data)

        self.ax.pie(sizes, labels=labels, colors=colors[:len(labels)], autopct='%1.1f%%',
                    startangle=90, textprops={'fontsize': 10})
        self.ax.axis('equal')
        self.figure.tight_layout()
        self.canvas.draw()


class AnalyticsTable(QTableWidget):
    """Tabulka pro zobrazení analytických dat"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_style()

    def setup_style(self):
        """Nastavení stylu tabulky"""
        self.setAlternatingRowColors(True)
        self.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)

        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)

    def set_data(self, headers, data):
        """Nastavení dat do tabulky"""
        self.clear()
        self.setRowCount(len(data))
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

        for row_idx, row_data in enumerate(data):
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(row_idx, col_idx, item)


class RankingTable(AnalyticsTable):
    """Tabulka pro žebříčky (top 10)"""

    def __init__(self, parent=None):
        super().__init__(parent)

    def set_ranking_data(self, headers, data):
        """Nastavení dat se zvýrazněním TOP 3"""
        self.set_data(headers, data)

        # Zvýraznění TOP 3
        colors = {
            0: QColor(255, 215, 0, 50),   # Zlatá
            1: QColor(192, 192, 192, 50), # Stříbrná
            2: QColor(205, 127, 50, 50)   # Bronzová
        }

        for row in range(min(3, self.rowCount())):
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    item.setBackground(colors[row])


class DateRangeFilter(QWidget):
    """Widget pro výběr časového období"""

    date_changed = pyqtSignal(QDate, QDate)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Rychlé filtry
        quick_filter_label = QLabel("Období:")
        quick_filter_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(quick_filter_label)

        self.quick_filter = QComboBox()
        self.quick_filter.addItems([
            "Tento měsíc",
            "Tento kvartál",
            "Tento rok",
            "Poslední měsíc",
            "Posledních 3 měsíce",
            "Posledních 6 měsíců",
            "Posledních 12 měsíců",
            "Vlastní období"
        ])
        self.quick_filter.currentIndexChanged.connect(self.on_quick_filter_changed)
        layout.addWidget(self.quick_filter)

        layout.addSpacing(20)

        # Od
        from_label = QLabel("Od:")
        layout.addWidget(from_label)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.dateChanged.connect(self.on_date_changed)
        layout.addWidget(self.date_from)

        # Do
        to_label = QLabel("Do:")
        layout.addWidget(to_label)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self.on_date_changed)
        layout.addWidget(self.date_to)

        # Tlačítko aplikovat
        apply_btn = QPushButton("Aplikovat")
        apply_btn.clicked.connect(self.on_apply_clicked)
        layout.addWidget(apply_btn)

        layout.addStretch()

        # Nastavení výchozího období
        self.on_quick_filter_changed(0)

    def on_quick_filter_changed(self, index):
        """Změna rychlého filtru"""
        today = QDate.currentDate()

        if index == 0:  # Tento měsíc
            self.date_from.setDate(QDate(today.year(), today.month(), 1))
            self.date_to.setDate(today)
        elif index == 1:  # Tento kvartál
            quarter = (today.month() - 1) // 3 + 1
            first_month = (quarter - 1) * 3 + 1
            self.date_from.setDate(QDate(today.year(), first_month, 1))
            self.date_to.setDate(today)
        elif index == 2:  # Tento rok
            self.date_from.setDate(QDate(today.year(), 1, 1))
            self.date_to.setDate(today)
        elif index == 3:  # Poslední měsíc
            self.date_from.setDate(today.addMonths(-1))
            self.date_to.setDate(today)
        elif index == 4:  # Posledních 3 měsíce
            self.date_from.setDate(today.addMonths(-3))
            self.date_to.setDate(today)
        elif index == 5:  # Posledních 6 měsíců
            self.date_from.setDate(today.addMonths(-6))
            self.date_to.setDate(today)
        elif index == 6:  # Posledních 12 měsíců
            self.date_from.setDate(today.addMonths(-12))
            self.date_to.setDate(today)

    def on_date_changed(self):
        """Změna data - přepnutí na vlastní období"""
        if self.quick_filter.currentIndex() != 7:
            self.quick_filter.blockSignals(True)
            self.quick_filter.setCurrentIndex(7)
            self.quick_filter.blockSignals(False)

    def on_apply_clicked(self):
        """Kliknutí na aplikovat"""
        self.date_changed.emit(self.date_from.date(), self.date_to.date())

    def get_date_range(self):
        """Získání vybraného období"""
        return self.date_from.date(), self.date_to.date()
