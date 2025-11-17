# -*- coding: utf-8 -*-
"""
Modul Administrativa - DPH a daňové přehledy (PRODUKČNÍ VERZE)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QFrame,
                             QComboBox, QLineEdit, QDateEdit, QHeaderView,
                             QMessageBox, QDialog, QFormLayout, QTextEdit,
                             QSpinBox, QDoubleSpinBox, QFileDialog, QCheckBox,
                             QGroupBox, QTabWidget, QScrollArea, QProgressBar,
                             QCalendarWidget)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter
from PyQt6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QValueAxis, QBarCategoryAxis
from datetime import datetime, timedelta, date
from pathlib import Path
import config
from database_manager import db


class TaxWidget(QWidget):
    """Widget pro DPH a daňové přehledy"""

    def __init__(self):
        super().__init__()
        self.current_period = {"from": None, "to": None}
        self.init_ui()
        self.load_data()
        self.check_deadlines()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Upozornění na termíny
        self.create_deadline_alert(layout)

        # Výběr období
        self.create_period_selector(layout)

        # DPH přehled
        self.create_vat_summary(layout)

        # Záložky
        tabs = QTabWidget()

        # Záložka: DPH Výstup (vydané faktury)
        self.tab_output = self.create_output_tab()
        tabs.addTab(self.tab_output, "📤 DPH na výstupu")

        # Záložka: DPH Vstup (přijaté faktury)
        self.tab_input = self.create_input_tab()
        tabs.addTab(self.tab_input, "📥 DPH na vstupu")

        # Záložka: Kontrolní výpočty
        self.tab_control = self.create_control_tab()
        tabs.addTab(self.tab_control, "✅ Kontrolní výpočty")

        # Záložka: Daňové doklady
        self.tab_documents = self.create_documents_tab()
        tabs.addTab(self.tab_documents, "📋 Daňové doklady")

        # Záložka: Archiv přiznání
        self.tab_archive = self.create_archive_tab()
        tabs.addTab(self.tab_archive, "📚 Archiv přiznání")

        layout.addWidget(tabs)

    def create_deadline_alert(self, parent_layout):
        """Panel s upozorněním na termíny"""
        self.deadline_frame = QFrame()
        self.deadline_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {config.COLOR_WARNING};
                border-radius: 8px;
                padding: 15px;
                border: 2px solid #f39c12;
            }}
        """)
        deadline_layout = QHBoxLayout(self.deadline_frame)

        self.deadline_label = QLabel("")
        deadline_font = QFont()
        deadline_font.setBold(True)
        deadline_font.setPointSize(11)
        self.deadline_label.setFont(deadline_font)
        deadline_layout.addWidget(self.deadline_label)

        deadline_layout.addStretch()

        dismiss_btn = QPushButton("✖ Zavřít")
        dismiss_btn.clicked.connect(lambda: self.deadline_frame.setVisible(False))
        deadline_layout.addWidget(dismiss_btn)

        self.deadline_frame.setVisible(False)
        parent_layout.addWidget(self.deadline_frame)

    def create_period_selector(self, parent_layout):
        """Výběr období"""
        period_frame = QFrame()
        period_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        period_layout = QHBoxLayout(period_frame)

        # Typ období
        period_label = QLabel("Období:")
        period_label_font = QFont()
        period_label_font.setBold(True)
        period_label.setFont(period_label_font)
        period_layout.addWidget(period_label)

        self.period_type_combo = QComboBox()
        self.period_type_combo.addItems([
            "Měsíční",
            "Čtvrtletní",
            "Roční",
            "Vlastní"
        ])
        self.period_type_combo.currentTextChanged.connect(self.on_period_type_changed)
        period_layout.addWidget(self.period_type_combo)

        # Měsíc/Čtvrtletí/Rok
        self.period_selector = QComboBox()
        self.load_period_options()
        self.period_selector.currentTextChanged.connect(self.on_period_selected)
        period_layout.addWidget(self.period_selector)

        # Nebo vlastní datum
        period_layout.addWidget(QLabel("Od:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd.MM.yyyy")
        self.date_from.dateChanged.connect(self.load_data)
        self.date_from.setEnabled(False)
        period_layout.addWidget(self.date_from)

        period_layout.addWidget(QLabel("Do:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd.MM.yyyy")
        self.date_to.dateChanged.connect(self.load_data)
        self.date_to.setEnabled(False)
        period_layout.addWidget(self.date_to)

        # Tlačítko refresh
        refresh_btn = QPushButton("🔄 Aktualizovat")
        refresh_btn.clicked.connect(self.load_data)
        period_layout.addWidget(refresh_btn)

        period_layout.addStretch()

        parent_layout.addWidget(period_frame)

    def create_vat_summary(self, parent_layout):
        """DPH souhrn"""
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                border: 1px solid #e0e0e0;
            }
        """)
        summary_layout = QHBoxLayout(summary_frame)

        # DPH na výstupu
        output_group = QGroupBox("📤 DPH na výstupu")
        output_group.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {config.COLOR_SUCCESS}; }}")
        output_layout = QVBoxLayout(output_group)

        self.vat_output_label = QLabel("0,00 Kč")
        vat_font = QFont()
        vat_font.setPointSize(18)
        vat_font.setBold(True)
        self.vat_output_label.setFont(vat_font)
        self.vat_output_label.setStyleSheet(f"color: {config.COLOR_SUCCESS};")
        output_layout.addWidget(self.vat_output_label)

        self.vat_output_detail = QLabel("z faktur zákazníkům")
        self.vat_output_detail.setStyleSheet("font-size: 9pt; color: #7f8c8d;")
        output_layout.addWidget(self.vat_output_detail)

        summary_layout.addWidget(output_group)

        # Minus
        minus_label = QLabel("−")
        minus_label.setStyleSheet("font-size: 32pt; font-weight: bold; color: #95a5a6;")
        minus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        summary_layout.addWidget(minus_label)

        # DPH na vstupu
        input_group = QGroupBox("📥 DPH na vstupu")
        input_group.setStyleSheet(f"QGroupBox {{ font-weight: bold; color: {config.COLOR_DANGER}; }}")
        input_layout = QVBoxLayout(input_group)

        self.vat_input_label = QLabel("0,00 Kč")
        self.vat_input_label.setFont(vat_font)
        self.vat_input_label.setStyleSheet(f"color: {config.COLOR_DANGER};")
        input_layout.addWidget(self.vat_input_label)

        self.vat_input_detail = QLabel("z přijatých faktur")
        self.vat_input_detail.setStyleSheet("font-size: 9pt; color: #7f8c8d;")
        input_layout.addWidget(self.vat_input_detail)

        summary_layout.addWidget(input_group)

        # Rovná se
        equals_label = QLabel("=")
        equals_label.setStyleSheet("font-size: 32pt; font-weight: bold; color: #95a5a6;")
        equals_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        summary_layout.addWidget(equals_label)

        # DPH k úhradě / nadměrný odpočet
        result_group = QGroupBox("💰 Výsledek")
        result_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        result_layout = QVBoxLayout(result_group)

        self.vat_result_label = QLabel("0,00 Kč")
        self.vat_result_label.setFont(vat_font)
        result_layout.addWidget(self.vat_result_label)

        self.vat_result_detail = QLabel("")
        self.vat_result_detail.setStyleSheet("font-size: 9pt; font-weight: bold;")
        result_layout.addWidget(self.vat_result_detail)

        summary_layout.addWidget(result_group)

        # Export tlačítka
        export_layout = QVBoxLayout()

        export_xml_btn = QPushButton("📄 Export XML")
        export_xml_btn.clicked.connect(self.export_xml)
        export_xml_btn.setStyleSheet(f"background-color: {config.COLOR_SECONDARY}; color: white; padding: 8px;")
        export_layout.addWidget(export_xml_btn)

        export_excel_btn = QPushButton("📊 Export Excel")
        export_excel_btn.clicked.connect(self.export_excel)
        export_layout.addWidget(export_excel_btn)

        save_declaration_btn = QPushButton("💾 Uložit přiznání")
        save_declaration_btn.clicked.connect(self.save_declaration)
        save_declaration_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px;")
        export_layout.addWidget(save_declaration_btn)

        summary_layout.addLayout(export_layout)

        parent_layout.addWidget(summary_frame)

    def create_output_tab(self):
        """Záložka: DPH na výstupu"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info
        info_label = QLabel("DPH z vydaných faktur (naše prodeje)")
        info_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(info_label)

        # Rozdělení podle sazeb
        rates_frame = QFrame()
        rates_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        rates_layout = QHBoxLayout(rates_frame)

        # Sazba 21%
        rate_21_group = QGroupBox("DPH 21%")
        rate_21_layout = QFormLayout(rate_21_group)
        self.output_21_base = QLabel("0 Kč")
        self.output_21_vat = QLabel("0 Kč")
        rate_21_layout.addRow("Základ:", self.output_21_base)
        rate_21_layout.addRow("DPH:", self.output_21_vat)
        rates_layout.addWidget(rate_21_group)

        # Sazba 12%
        rate_12_group = QGroupBox("DPH 12%")
        rate_12_layout = QFormLayout(rate_12_group)
        self.output_12_base = QLabel("0 Kč")
        self.output_12_vat = QLabel("0 Kč")
        rate_12_layout.addRow("Základ:", self.output_12_base)
        rate_12_layout.addRow("DPH:", self.output_12_vat)
        rates_layout.addWidget(rate_12_group)

        # Sazba 0%
        rate_0_group = QGroupBox("DPH 0%")
        rate_0_layout = QFormLayout(rate_0_group)
        self.output_0_base = QLabel("0 Kč")
        self.output_0_vat = QLabel("0 Kč")
        rate_0_layout.addRow("Základ:", self.output_0_base)
        rate_0_layout.addRow("DPH:", self.output_0_vat)
        rates_layout.addWidget(rate_0_group)

        # Celkem
        total_group = QGroupBox("Celkem")
        total_layout = QFormLayout(total_group)
        self.output_total_base = QLabel("0 Kč")
        self.output_total_vat = QLabel("0 Kč")
        total_font = QFont()
        total_font.setBold(True)
        self.output_total_base.setFont(total_font)
        self.output_total_vat.setFont(total_font)
        total_layout.addRow("Základ:", self.output_total_base)
        total_layout.addRow("DPH:", self.output_total_vat)
        rates_layout.addWidget(total_group)

        layout.addWidget(rates_frame)

        # Tabulka faktur
        self.output_table = QTableWidget()
        self.output_table.setColumnCount(8)
        self.output_table.setHorizontalHeaderLabels([
            "Číslo faktury",
            "Zákazník",
            "Datum",
            "Základ 21%",
            "DPH 21%",
            "Základ 12%",
            "DPH 12%",
            "Celkem DPH"
        ])
        self.output_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.output_table.setAlternatingRowColors(True)
        layout.addWidget(self.output_table)

        return widget

    def create_input_tab(self):
        """Záložka: DPH na vstupu"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info
        info_label = QLabel("DPH z přijatých faktur (naše nákupy)")
        info_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(info_label)

        # Rozdělení podle sazeb
        rates_frame = QFrame()
        rates_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        rates_layout = QHBoxLayout(rates_frame)

        # Sazba 21%
        rate_21_group = QGroupBox("DPH 21%")
        rate_21_layout = QFormLayout(rate_21_group)
        self.input_21_base = QLabel("0 Kč")
        self.input_21_vat = QLabel("0 Kč")
        rate_21_layout.addRow("Základ:", self.input_21_base)
        rate_21_layout.addRow("DPH:", self.input_21_vat)
        rates_layout.addWidget(rate_21_group)

        # Sazba 12%
        rate_12_group = QGroupBox("DPH 12%")
        rate_12_layout = QFormLayout(rate_12_group)
        self.input_12_base = QLabel("0 Kč")
        self.input_12_vat = QLabel("0 Kč")
        rate_12_layout.addRow("Základ:", self.input_12_base)
        rate_12_layout.addRow("DPH:", self.input_12_vat)
        rates_layout.addWidget(rate_12_group)

        # Sazba 0%
        rate_0_group = QGroupBox("DPH 0%")
        rate_0_layout = QFormLayout(rate_0_group)
        self.input_0_base = QLabel("0 Kč")
        self.input_0_vat = QLabel("0 Kč")
        rate_0_layout.addRow("Základ:", self.input_0_base)
        rate_0_layout.addRow("DPH:", self.input_0_vat)
        rates_layout.addWidget(rate_0_group)

        # Celkem
        total_group = QGroupBox("Celkem")
        total_layout = QFormLayout(total_group)
        self.input_total_base = QLabel("0 Kč")
        self.input_total_vat = QLabel("0 Kč")
        total_font = QFont()
        total_font.setBold(True)
        self.input_total_base.setFont(total_font)
        self.input_total_vat.setFont(total_font)
        total_layout.addRow("Základ:", self.input_total_base)
        total_layout.addRow("DPH:", self.input_total_vat)
        rates_layout.addWidget(total_group)

        layout.addWidget(rates_frame)

        # Tabulka faktur
        self.input_table = QTableWidget()
        self.input_table.setColumnCount(8)
        self.input_table.setHorizontalHeaderLabels([
            "Číslo faktury",
            "Dodavatel",
            "Datum",
            "Základ 21%",
            "DPH 21%",
            "Základ 12%",
            "DPH 12%",
            "Celkem DPH"
        ])
        self.input_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.input_table.setAlternatingRowColors(True)
        layout.addWidget(self.input_table)

        return widget

    def create_control_tab(self):
        """Záložka: Kontrolní výpočty"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Kontrolní součty
        control_group = QGroupBox("✅ Kontrolní součty")
        control_layout = QFormLayout(control_group)

        # Výstup
        output_section = QLabel("DPH na výstupu (vydané faktury):")
        output_section_font = QFont()
        output_section_font.setBold(True)
        output_section.setFont(output_section_font)
        control_layout.addRow(output_section)

        self.control_output_base = QLabel("0 Kč")
        control_layout.addRow("  Celkem bez DPH:", self.control_output_base)

        self.control_output_vat = QLabel("0 Kč")
        control_layout.addRow("  Celkem DPH:", self.control_output_vat)

        self.control_output_total = QLabel("0 Kč")
        control_layout.addRow("  Celkem s DPH:", self.control_output_total)

        # Vstup
        input_section = QLabel("DPH na vstupu (přijaté faktury):")
        input_section.setFont(output_section_font)
        control_layout.addRow(input_section)

        self.control_input_base = QLabel("0 Kč")
        control_layout.addRow("  Celkem bez DPH:", self.control_input_base)

        self.control_input_vat = QLabel("0 Kč")
        control_layout.addRow("  Celkem DPH:", self.control_input_vat)

        self.control_input_total = QLabel("0 Kč")
        control_layout.addRow("  Celkem s DPH:", self.control_input_total)

        # Rozdíl
        diff_section = QLabel("Výsledek:")
        diff_section.setFont(output_section_font)
        control_layout.addRow(diff_section)

        self.control_diff = QLabel("0 Kč")
        diff_font = QFont()
        diff_font.setBold(True)
        diff_font.setPointSize(14)
        self.control_diff.setFont(diff_font)
        control_layout.addRow("  DPH k úhradě / nadměrný odpočet:", self.control_diff)

        layout.addWidget(control_group)

        # Graf rozdělení DPH
        chart_group = QGroupBox("📊 Rozdělení DPH podle sazeb")
        chart_layout = QVBoxLayout(chart_group)

        self.control_chart = QChartView()
        self.control_chart.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.control_chart.setMinimumHeight(300)
        chart_layout.addWidget(self.control_chart)

        layout.addWidget(chart_group)

        # Kontrolní hlášení
        warning_frame = QFrame()
        warning_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        warning_layout = QVBoxLayout(warning_frame)

        warning_title = QLabel("⚠️ Upozornění:")
        warning_title_font = QFont()
        warning_title_font.setBold(True)
        warning_title.setFont(warning_title_font)
        warning_layout.addWidget(warning_title)

        warning_text = QLabel(
            "• Zkontrolujte správnost všech faktur\n"
            "• Ověřte datum zdanitelného plnění\n"
            "• Ujistěte se, že jsou faktury správně zaúčtovány\n"
            "• V případě nejasností konzultujte s daňovým poradcem"
        )
        warning_layout.addWidget(warning_text)

        layout.addWidget(warning_frame)

        layout.addStretch()

        return widget

    def create_documents_tab(self):
        """Záložka: Daňové doklady"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info
        info_label = QLabel("Přehled všech daňových dokladů v období")
        info_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(info_label)

        # Filtry
        filters_layout = QHBoxLayout()

        type_label = QLabel("Typ:")
        filters_layout.addWidget(type_label)

        self.doc_type_filter = QComboBox()
        self.doc_type_filter.addItems([
            "Všechny",
            "Vydané faktury",
            "Přijaté faktury",
            "Dobropisy",
            "Ostatní"
        ])
        self.doc_type_filter.currentTextChanged.connect(self.filter_documents)
        filters_layout.addWidget(self.doc_type_filter)

        filters_layout.addStretch()
        layout.addLayout(filters_layout)

        # Tabulka dokladů
        self.documents_table = QTableWidget()
        self.documents_table.setColumnCount(7)
        self.documents_table.setHorizontalHeaderLabels([
            "Číslo dokladu",
            "Typ",
            "Partner",
            "Datum vystavení",
            "Datum zdanit. plnění",
            "Základ DPH",
            "Celkem DPH"
        ])
        self.documents_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.documents_table.setAlternatingRowColors(True)
        layout.addWidget(self.documents_table)

        # Kontrola duplikátů
        check_btn = QPushButton("🔍 Kontrola duplikátů")
        check_btn.clicked.connect(self.check_duplicates)
        layout.addWidget(check_btn)

        return widget

    def create_archive_tab(self):
        """Záložka: Archiv přiznání"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info
        info_label = QLabel("Archiv podaných DPH přiznání")
        info_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(info_label)

        # Tabulka archivovaných přiznání
        self.archive_table = QTableWidget()
        self.archive_table.setColumnCount(7)
        self.archive_table.setHorizontalHeaderLabels([
            "Období",
            "Datum uložení",
            "DPH výstup",
            "DPH vstup",
            "K úhradě",
            "Stav",
            "Akce"
        ])
        self.archive_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.archive_table.setAlternatingRowColors(True)
        layout.addWidget(self.archive_table)

        return widget

    # =====================================================
    # NAČÍTÁNÍ DAT
    # =====================================================

    def load_period_options(self):
        """Načtení možností období"""
        self.period_selector.clear()

        period_type = self.period_type_combo.currentText()

        if period_type == "Měsíční":
            # Poslední 24 měsíců
            for i in range(24):
                date = QDate.currentDate().addMonths(-i)
                month_name = self.get_month_name(date.month())
                self.period_selector.addItem(f"{month_name} {date.year()}", date)

        elif period_type == "Čtvrtletní":
            # Poslední 8 čtvrtletí
            for i in range(8):
                quarter_start = QDate.currentDate().addMonths(-i * 3)
                quarter_num = (quarter_start.month() - 1) // 3 + 1
                self.period_selector.addItem(f"Q{quarter_num} {quarter_start.year()}", quarter_start)

        elif period_type == "Roční":
            # Poslední 5 let
            current_year = QDate.currentDate().year()
            for year in range(current_year, current_year - 5, -1):
                self.period_selector.addItem(str(year), QDate(year, 1, 1))

    def on_period_type_changed(self, period_type):
        """Změna typu období"""
        self.load_period_options()

        if period_type == "Vlastní":
            self.period_selector.setEnabled(False)
            self.date_from.setEnabled(True)
            self.date_to.setEnabled(True)
        else:
            self.period_selector.setEnabled(True)
            self.date_from.setEnabled(False)
            self.date_to.setEnabled(False)
            self.on_period_selected()

    def on_period_selected(self):
        """Změna vybraného období"""
        if self.period_type_combo.currentText() == "Vlastní":
            return

        period_type = self.period_type_combo.currentText()
        selected_date = self.period_selector.currentData()

        if not selected_date:
            return

        if period_type == "Měsíční":
            # První a poslední den měsíce
            first_day = QDate(selected_date.year(), selected_date.month(), 1)
            last_day = QDate(selected_date.year(), selected_date.month(), selected_date.daysInMonth())
            self.date_from.setDate(first_day)
            self.date_to.setDate(last_day)

        elif period_type == "Čtvrtletní":
            # První den čtvrtletí
            quarter_num = (selected_date.month() - 1) // 3 + 1
            first_month = (quarter_num - 1) * 3 + 1
            first_day = QDate(selected_date.year(), first_month, 1)

            # Poslední den čtvrtletí
            last_month = quarter_num * 3
            last_day = QDate(selected_date.year(), last_month, QDate(selected_date.year(), last_month, 1).daysInMonth())

            self.date_from.setDate(first_day)
            self.date_to.setDate(last_day)

        elif period_type == "Roční":
            # 1.1. - 31.12.
            self.date_from.setDate(QDate(selected_date.year(), 1, 1))
            self.date_to.setDate(QDate(selected_date.year(), 12, 31))

        self.load_data()

    def load_data(self):
        """Načtení všech dat"""
        self.current_period["from"] = self.date_from.date().toString("yyyy-MM-dd")
        self.current_period["to"] = self.date_to.date().toString("yyyy-MM-dd")

        self.load_vat_summary()
        self.load_output_vat()
        self.load_input_vat()
        self.load_control_calculations()
        self.load_documents()
        self.load_archive()

    def load_vat_summary(self):
        """Načtení souhrnu DPH"""
        try:
            date_from = self.current_period["from"]
            date_to = self.current_period["to"]

            # DPH na výstupu
            output_vat = self.calculate_output_vat(date_from, date_to)

            # DPH na vstupu
            input_vat = self.calculate_input_vat(date_from, date_to)

            # Rozdíl
            result = output_vat - input_vat

            # Aktualizace labelů
            self.vat_output_label.setText(f"{output_vat:,.2f} Kč".replace(",", " "))
            self.vat_input_label.setText(f"{input_vat:,.2f} Kč".replace(",", " "))

            self.vat_result_label.setText(f"{abs(result):,.2f} Kč".replace(",", " "))

            if result > 0:
                self.vat_result_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #e74c3c;")
                self.vat_result_detail.setText("K úhradě státu")
                self.vat_result_detail.setStyleSheet("color: #e74c3c;")
            elif result < 0:
                self.vat_result_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #27ae60;")
                self.vat_result_detail.setText("Nadměrný odpočet (vrátí nám stát)")
                self.vat_result_detail.setStyleSheet("color: #27ae60;")
            else:
                self.vat_result_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #95a5a6;")
                self.vat_result_detail.setText("Vyrovnáno")
                self.vat_result_detail.setStyleSheet("color: #95a5a6;")

        except Exception as e:
            print(f"Chyba při načítání DPH souhrnu: {e}")

    def calculate_output_vat(self, date_from, date_to):
        """Výpočet DPH na výstupu"""
        try:
            query = """
                SELECT COALESCE(SUM(ii.total_vat), 0) as total_vat
                FROM invoice_items ii
                JOIN invoices i ON ii.invoice_id = i.id
                WHERE i.invoice_type = 'issued'
                  AND i.tax_date BETWEEN ? AND ?
            """
            result = db.fetch_one(query, (date_from, date_to))
            return result["total_vat"] if result else 0
        except Exception as e:
            print(f"Chyba při výpočtu výstupního DPH: {e}")
            return 0

    def calculate_input_vat(self, date_from, date_to):
        """Výpočet DPH na vstupu"""
        try:
            query = """
                SELECT COALESCE(SUM(ii.total_vat), 0) as total_vat
                FROM invoice_items ii
                JOIN invoices i ON ii.invoice_id = i.id
                WHERE i.invoice_type = 'received'
                  AND i.tax_date BETWEEN ? AND ?
            """
            result = db.fetch_one(query, (date_from, date_to))
            return result["total_vat"] if result else 0
        except Exception as e:
            print(f"Chyba při výpočtu vstupního DPH: {e}")
            return 0

    def load_output_vat(self):
        """Načtení DPH na výstupu"""
        try:
            date_from = self.current_period["from"]
            date_to = self.current_period["to"]

            # Součty podle sazeb
            query_rates = """
                SELECT
                    ii.vat_rate,
                    SUM(ii.total_without_vat) as base,
                    SUM(ii.total_vat) as vat
                FROM invoice_items ii
                JOIN invoices i ON ii.invoice_id = i.id
                WHERE i.invoice_type = 'issued'
                  AND i.tax_date BETWEEN ? AND ?
                GROUP BY ii.vat_rate
            """
            rates = db.fetch_all(query_rates, (date_from, date_to))

            # Aktualizace labelů podle sazeb
            total_base = 0
            total_vat = 0

            for rate_data in rates:
                rate = rate_data["vat_rate"]
                base = rate_data["base"]
                vat = rate_data["vat"]

                total_base += base
                total_vat += vat

                if rate == 21:
                    self.output_21_base.setText(f"{base:,.2f} Kč".replace(",", " "))
                    self.output_21_vat.setText(f"{vat:,.2f} Kč".replace(",", " "))
                elif rate == 12:
                    self.output_12_base.setText(f"{base:,.2f} Kč".replace(",", " "))
                    self.output_12_vat.setText(f"{vat:,.2f} Kč".replace(",", " "))
                elif rate == 0:
                    self.output_0_base.setText(f"{base:,.2f} Kč".replace(",", " "))
                    self.output_0_vat.setText(f"{vat:,.2f} Kč".replace(",", " "))

            self.output_total_base.setText(f"{total_base:,.2f} Kč".replace(",", " "))
            self.output_total_vat.setText(f"{total_vat:,.2f} Kč".replace(",", " "))

            # Tabulka faktur
            query_invoices = """
                SELECT
                    i.invoice_number,
                    COALESCE(c.first_name || ' ' || c.last_name, c.company, 'Neznámý') as customer_name,
                    i.tax_date,
                    SUM(CASE WHEN ii.vat_rate = 21 THEN ii.total_without_vat ELSE 0 END) as base_21,
                    SUM(CASE WHEN ii.vat_rate = 21 THEN ii.total_vat ELSE 0 END) as vat_21,
                    SUM(CASE WHEN ii.vat_rate = 12 THEN ii.total_without_vat ELSE 0 END) as base_12,
                    SUM(CASE WHEN ii.vat_rate = 12 THEN ii.total_vat ELSE 0 END) as vat_12,
                    SUM(ii.total_vat) as total_vat
                FROM invoices i
                LEFT JOIN customers c ON i.customer_id = c.id
                JOIN invoice_items ii ON i.id = ii.invoice_id
                WHERE i.invoice_type = 'issued'
                  AND i.tax_date BETWEEN ? AND ?
                GROUP BY i.id
                ORDER BY i.tax_date
            """
            invoices = db.fetch_all(query_invoices, (date_from, date_to))

            self.output_table.setRowCount(len(invoices))

            for row, inv in enumerate(invoices):
                self.output_table.setItem(row, 0, QTableWidgetItem(inv["invoice_number"]))
                self.output_table.setItem(row, 1, QTableWidgetItem(inv["customer_name"]))

                tax_date = datetime.fromisoformat(inv["tax_date"]).strftime("%d.%m.%Y")
                self.output_table.setItem(row, 2, QTableWidgetItem(tax_date))

                for col, key in enumerate(["base_21", "vat_21", "base_12", "vat_12", "total_vat"], start=3):
                    value = inv[key]
                    item = QTableWidgetItem(f"{value:,.2f} Kč".replace(",", " "))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.output_table.setItem(row, col, item)

        except Exception as e:
            print(f"Chyba při načítání výstupního DPH: {e}")

    def load_input_vat(self):
        """Načtení DPH na vstupu"""
        try:
            date_from = self.current_period["from"]
            date_to = self.current_period["to"]

            # Součty podle sazeb
            query_rates = """
                SELECT
                    ii.vat_rate,
                    SUM(ii.total_without_vat) as base,
                    SUM(ii.total_vat) as vat
                FROM invoice_items ii
                JOIN invoices i ON ii.invoice_id = i.id
                WHERE i.invoice_type = 'received'
                  AND i.tax_date BETWEEN ? AND ?
                GROUP BY ii.vat_rate
            """
            rates = db.fetch_all(query_rates, (date_from, date_to))

            # Aktualizace labelů podle sazeb
            total_base = 0
            total_vat = 0

            for rate_data in rates:
                rate = rate_data["vat_rate"]
                base = rate_data["base"]
                vat = rate_data["vat"]

                total_base += base
                total_vat += vat

                if rate == 21:
                    self.input_21_base.setText(f"{base:,.2f} Kč".replace(",", " "))
                    self.input_21_vat.setText(f"{vat:,.2f} Kč".replace(",", " "))
                elif rate == 12:
                    self.input_12_base.setText(f"{base:,.2f} Kč".replace(",", " "))
                    self.input_12_vat.setText(f"{vat:,.2f} Kč".replace(",", " "))
                elif rate == 0:
                    self.input_0_base.setText(f"{base:,.2f} Kč".replace(",", " "))
                    self.input_0_vat.setText(f"{vat:,.2f} Kč".replace(",", " "))

            self.input_total_base.setText(f"{total_base:,.2f} Kč".replace(",", " "))
            self.input_total_vat.setText(f"{total_vat:,.2f} Kč".replace(",", " "))

            # Tabulka faktur
            query_invoices = """
                SELECT
                    i.invoice_number,
                    COALESCE(i.supplier_name, 'Neznámý dodavatel') as supplier_name,
                    i.tax_date,
                    SUM(CASE WHEN ii.vat_rate = 21 THEN ii.total_without_vat ELSE 0 END) as base_21,
                    SUM(CASE WHEN ii.vat_rate = 21 THEN ii.total_vat ELSE 0 END) as vat_21,
                    SUM(CASE WHEN ii.vat_rate = 12 THEN ii.total_without_vat ELSE 0 END) as base_12,
                    SUM(CASE WHEN ii.vat_rate = 12 THEN ii.total_vat ELSE 0 END) as vat_12,
                    SUM(ii.total_vat) as total_vat
                FROM invoices i
                JOIN invoice_items ii ON i.id = ii.invoice_id
                WHERE i.invoice_type = 'received'
                  AND i.tax_date BETWEEN ? AND ?
                GROUP BY i.id
                ORDER BY i.tax_date
            """
            invoices = db.fetch_all(query_invoices, (date_from, date_to))

            self.input_table.setRowCount(len(invoices))

            for row, inv in enumerate(invoices):
                self.input_table.setItem(row, 0, QTableWidgetItem(inv["invoice_number"]))
                self.input_table.setItem(row, 1, QTableWidgetItem(inv["supplier_name"]))

                tax_date = datetime.fromisoformat(inv["tax_date"]).strftime("%d.%m.%Y")
                self.output_table.setItem(row, 2, QTableWidgetItem(tax_date))

                for col, key in enumerate(["base_21", "vat_21", "base_12", "vat_12", "total_vat"], start=3):
                    value = inv[key]
                    item = QTableWidgetItem(f"{value:,.2f} Kč".replace(",", " "))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.input_table.setItem(row, col, item)

        except Exception as e:
            print(f"Chyba při načítání vstupního DPH: {e}")

    def load_control_calculations(self):
        """Načtení kontrolních výpočtů"""
        try:
            date_from = self.current_period["from"]
            date_to = self.current_period["to"]

            # Výstup
            output_query = """
                SELECT
                    SUM(i.total_without_vat) as base,
                    SUM(i.total_vat) as vat,
                    SUM(i.total_with_vat) as total
                FROM invoices i
                WHERE i.invoice_type = 'issued'
                  AND i.tax_date BETWEEN ? AND ?
            """
            output = db.fetch_one(output_query, (date_from, date_to))

            output_base = output["base"] if output else 0
            output_vat = output["vat"] if output else 0
            output_total = output["total"] if output else 0

            self.control_output_base.setText(f"{output_base:,.2f} Kč".replace(",", " "))
            self.control_output_vat.setText(f"{output_vat:,.2f} Kč".replace(",", " "))
            self.control_output_total.setText(f"{output_total:,.2f} Kč".replace(",", " "))

            # Vstup
            input_query = """
                SELECT
                    SUM(i.total_without_vat) as base,
                    SUM(i.total_vat) as vat,
                    SUM(i.total_with_vat) as total
                FROM invoices i
                WHERE i.invoice_type = 'received'
                  AND i.tax_date BETWEEN ? AND ?
            """
            input_data = db.fetch_one(input_query, (date_from, date_to))

            input_base = input_data["base"] if input_data else 0
            input_vat = input_data["vat"] if input_data else 0
            input_total = input_data["total"] if input_data else 0

            self.control_input_base.setText(f"{input_base:,.2f} Kč".replace(",", " "))
            self.control_input_vat.setText(f"{input_vat:,.2f} Kč".replace(",", " "))
            self.control_input_total.setText(f"{input_total:,.2f} Kč".replace(",", " "))

            # Rozdíl
            diff = output_vat - input_vat
            self.control_diff.setText(f"{abs(diff):,.2f} Kč".replace(",", " "))

            if diff > 0:
                self.control_diff.setStyleSheet("color: #e74c3c;")
            elif diff < 0:
                self.control_diff.setStyleSheet("color: #27ae60;")
            else:
                self.control_diff.setStyleSheet("color: #95a5a6;")

            # Graf
            self.create_control_chart(output_vat, input_vat)

        except Exception as e:
            print(f"Chyba při načítání kontrolních výpočtů: {e}")

    def create_control_chart(self, output_vat, input_vat):
        """Vytvoření grafu pro kontrolu"""
        try:
            series = QPieSeries()
            series.append(f"DPH výstup\n{output_vat:,.0f} Kč".replace(",", " "), output_vat)
            series.append(f"DPH vstup\n{input_vat:,.0f} Kč".replace(",", " "), input_vat)

            chart = QChart()
            chart.addSeries(series)
            chart.setTitle("Poměr DPH výstup/vstup")
            chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

            self.control_chart.setChart(chart)

        except Exception as e:
            print(f"Chyba při vytváření grafu: {e}")

    def load_documents(self):
        """Načtení daňových dokladů"""
        try:
            date_from = self.current_period["from"]
            date_to = self.current_period["to"]

            query = """
                SELECT
                    i.invoice_number,
                    i.invoice_type,
                    CASE
                        WHEN i.invoice_type = 'issued' THEN
                            COALESCE(c.first_name || ' ' || c.last_name, c.company, 'Neznámý')
                        ELSE
                            COALESCE(i.supplier_name, 'Neznámý dodavatel')
                    END as partner_name,
                    i.issue_date,
                    i.tax_date,
                    i.total_without_vat,
                    i.total_vat
                FROM invoices i
                LEFT JOIN customers c ON i.customer_id = c.id
                WHERE i.tax_date BETWEEN ? AND ?
                ORDER BY i.tax_date
            """
            documents = db.fetch_all(query, (date_from, date_to))

            self.documents_table.setRowCount(len(documents))

            for row, doc in enumerate(documents):
                self.documents_table.setItem(row, 0, QTableWidgetItem(doc["invoice_number"]))

                doc_type = "Vydaná faktura" if doc["invoice_type"] == "issued" else "Přijatá faktura"
                self.documents_table.setItem(row, 1, QTableWidgetItem(doc_type))

                self.documents_table.setItem(row, 2, QTableWidgetItem(doc["partner_name"]))

                issue_date = datetime.fromisoformat(doc["issue_date"]).strftime("%d.%m.%Y")
                self.documents_table.setItem(row, 3, QTableWidgetItem(issue_date))

                tax_date = datetime.fromisoformat(doc["tax_date"]).strftime("%d.%m.%Y")
                self.documents_table.setItem(row, 4, QTableWidgetItem(tax_date))

                base_item = QTableWidgetItem(f"{doc['total_without_vat']:,.2f} Kč".replace(",", " "))
                base_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.documents_table.setItem(row, 5, base_item)

                vat_item = QTableWidgetItem(f"{doc['total_vat']:,.2f} Kč".replace(",", " "))
                vat_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.documents_table.setItem(row, 6, vat_item)

        except Exception as e:
            print(f"Chyba při načítání dokladů: {e}")

    def load_archive(self):
        """Načtení archivu přiznání"""
        try:
            query = """
                SELECT * FROM vat_declarations
                ORDER BY period_end DESC
                LIMIT 50
            """
            declarations = db.fetch_all(query)

            self.archive_table.setRowCount(len(declarations))

            for row, decl in enumerate(declarations):
                # Období
                period_start = datetime.fromisoformat(decl["period_start"]).strftime("%d.%m.%Y")
                period_end = datetime.fromisoformat(decl["period_end"]).strftime("%d.%m.%Y")
                period_text = f"{period_start} - {period_end}"
                self.archive_table.setItem(row, 0, QTableWidgetItem(period_text))

                # Datum uložení
                saved_date = datetime.fromisoformat(decl["created_at"]).strftime("%d.%m.%Y %H:%M")
                self.archive_table.setItem(row, 1, QTableWidgetItem(saved_date))

                # DPH výstup
                output_item = QTableWidgetItem(f"{decl['vat_output']:,.2f} Kč".replace(",", " "))
                output_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.archive_table.setItem(row, 2, output_item)

                # DPH vstup
                input_item = QTableWidgetItem(f"{decl['vat_input']:,.2f} Kč".replace(",", " "))
                input_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.archive_table.setItem(row, 3, input_item)

                # K úhradě
                result_item = QTableWidgetItem(f"{decl['vat_result']:,.2f} Kč".replace(",", " "))
                result_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if decl['vat_result'] > 0:
                    result_item.setForeground(QColor(config.COLOR_DANGER))
                elif decl['vat_result'] < 0:
                    result_item.setForeground(QColor(config.COLOR_SUCCESS))
                self.archive_table.setItem(row, 4, result_item)

                # Stav
                status = decl["status"] or "Uloženo"
                self.archive_table.setItem(row, 5, QTableWidgetItem(status))

                # Akce
                view_btn = QPushButton("👁️ Zobrazit")
                view_btn.clicked.connect(lambda checked, d=decl: self.view_declaration(d))
                self.archive_table.setCellWidget(row, 6, view_btn)

        except Exception as e:
            print(f"Chyba při načítání archivu: {e}")

    def check_deadlines(self):
        """Kontrola termínů podání"""
        try:
            # Pro měsíční plátce: 25. den následujícího měsíce
            # Pro čtvrtletní plátce: 25. den po skončení čtvrtletí

            today = date.today()

            # Příští termín podání
            # Pro zjednodušení: 25. příštího měsíce
            if today.day < 25:
                deadline = date(today.year, today.month, 25)
            else:
                next_month = today.month + 1 if today.month < 12 else 1
                next_year = today.year if today.month < 12 else today.year + 1
                deadline = date(next_year, next_month, 25)

            days_remaining = (deadline - today).days

            if days_remaining <= 7:
                self.deadline_label.setText(
                    f"⚠️ Upozornění: Termín podání DPH přiznání za uplynulé období je {deadline.strftime('%d.%m.%Y')} "
                    f"(zbývá {days_remaining} dní)"
                )
                self.deadline_frame.setVisible(True)
            else:
                self.deadline_frame.setVisible(False)

        except Exception as e:
            print(f"Chyba při kontrole termínů: {e}")

    # =====================================================
    # POMOCNÉ METODY
    # =====================================================

    def get_month_name(self, month):
        """Vrátí název měsíce"""
        months = {
            1: "Leden", 2: "Únor", 3: "Březen", 4: "Duben",
            5: "Květen", 6: "Červen", 7: "Červenec", 8: "Srpen",
            9: "Září", 10: "Říjen", 11: "Listopad", 12: "Prosinec"
        }
        return months.get(month, "")

    def filter_documents(self):
        """Filtrování dokladů"""
        # TODO: Implementovat filtrování
        pass

    # =====================================================
    # AKCE
    # =====================================================

    def export_xml(self):
        """Export do XML pro Finanční správu"""
        QMessageBox.information(
            self,
            "Export XML",
            "Export DPH přiznání do XML formátu pro Finanční správu ČR bude implementován.\n\n"
            "Formát bude kompatibilní s elektronickým podáním EPO."
        )

    def export_excel(self):
        """Export do Excel"""
        QMessageBox.information(
            self,
            "Export Excel",
            "Export DPH přehledu do Excel bude implementován."
        )

    def save_declaration(self):
        """Uložení přiznání do archivu"""
        try:
            date_from = self.current_period["from"]
            date_to = self.current_period["to"]

            output_vat = self.calculate_output_vat(date_from, date_to)
            input_vat = self.calculate_input_vat(date_from, date_to)
            result = output_vat - input_vat

            # Uložit do databáze
            query = """
                INSERT INTO vat_declarations (
                    period_start, period_end, vat_output, vat_input, vat_result, status
                ) VALUES (?, ?, ?, ?, ?, ?)
            """
            db.execute_query(query, (
                date_from,
                date_to,
                output_vat,
                input_vat,
                result,
                "Uloženo"
            ))

            QMessageBox.information(
                self,
                "Úspěch",
                f"DPH přiznání za období {date_from} - {date_to} bylo uloženo do archivu."
            )

            self.load_archive()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit přiznání:\n{e}")

    def check_duplicates(self):
        """Kontrola duplikátů dokladů"""
        try:
            date_from = self.current_period["from"]
            date_to = self.current_period["to"]

            query = """
                SELECT invoice_number, COUNT(*) as count
                FROM invoices
                WHERE tax_date BETWEEN ? AND ?
                GROUP BY invoice_number
                HAVING count > 1
            """
            duplicates = db.fetch_all(query, (date_from, date_to))

            if duplicates:
                dup_list = "\n".join([f"- {d['invoice_number']} ({d['count']}x)" for d in duplicates])
                QMessageBox.warning(
                    self,
                    "Duplicitní doklady",
                    f"Nalezeny duplicitní doklady:\n\n{dup_list}\n\nKontrolujte správnost číselných řad."
                )
            else:
                QMessageBox.information(
                    self,
                    "Kontrola OK",
                    "Nebyly nalezeny žádné duplicitní doklady."
                )

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se zkontrolovat duplikáty:\n{e}")

    def view_declaration(self, declaration):
        """Zobrazení archivovaného přiznání"""
        QMessageBox.information(
            self,
            "Detail přiznání",
            f"Zobrazení detailu přiznání za období:\n"
            f"{declaration['period_start']} - {declaration['period_end']}\n\n"
            "Detail bude implementován."
        )

    def refresh(self):
        """Obnovení dat"""
        self.load_data()
        self.check_deadlines()
