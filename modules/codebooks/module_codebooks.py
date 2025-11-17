# -*- coding: utf-8 -*-
"""
Modul Číselníky - Hlavní vstupní bod (PRODUKČNÍ VERZE)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFrame, QStackedWidget, QScrollArea,
                             QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import config
from database_manager import db


class CodebooksModule(QWidget):
    """Hlavní modul číselníky"""

    def __init__(self):
        super().__init__()
        self.current_section = None
        self.sections = {}
        self.section_buttons = {}
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Levé menu
        self.create_navigation_panel(main_layout)

        # Pravý panel s obsahem
        self.create_content_panel(main_layout)

        # Styly
        self.apply_styles()

        # Výchozí sekce
        self.switch_section("brands")

    def create_navigation_panel(self, parent_layout):
        """Vytvoření levého navigačního panelu"""
        nav_widget = QWidget()
        nav_widget.setObjectName("codebooksNavPanel")
        nav_widget.setFixedWidth(260)

        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        # Hlavička
        header = QFrame()
        header.setObjectName("codebooksNavHeader")
        header.setFixedHeight(80)
        header_layout = QVBoxLayout(header)

        title = QLabel("📚 Číselníky")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel("Správa základních dat")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(9)
        subtitle.setFont(subtitle_font)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        nav_layout.addWidget(header)

        # Scroll area pro tlačítka
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)

        # Sekce navigace
        sections = [
            ("brands", "🚗 Značky vozidel"),
            ("vehicle_types", "🏍️ Typy vozidel"),
            ("fuel_types", "⛽ Typy paliva"),
            ("colors", "🎨 Barvy vozidel"),
            ("separator1", "---"),
            ("repair_types", "🔧 Typy oprav"),
            ("order_statuses", "📋 Stavy zakázek"),
            ("units", "📏 Měrné jednotky"),
            ("separator2", "---"),
            ("positions", "👷 Pracovní pozice"),
            ("hourly_rates", "⏱️ Hodinové sazby"),
            ("customer_groups", "👥 Zákaznické skupiny"),
            ("separator3", "---"),
            ("payment_methods", "💳 Způsoby platby"),
            ("vat_rates", "📊 Sazby DPH"),
            ("currencies", "💱 Měny"),
        ]

        for section_id, section_name in sections:
            if section_id.startswith("separator"):
                # Oddělovač
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.HLine)
                separator.setStyleSheet("background-color: #1a252f; margin: 5px 10px;")
                scroll_layout.addWidget(separator)
            else:
                btn = QPushButton(section_name)
                btn.setObjectName("codebooksNavButton")
                btn.setFixedHeight(45)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda checked, s=section_id: self.switch_section(s))
                self.section_buttons[section_id] = btn
                scroll_layout.addWidget(btn)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        nav_layout.addWidget(scroll)

        # Spodní panel s akcemi
        bottom_panel = QFrame()
        bottom_panel.setObjectName("codebooksBottomPanel")
        bottom_panel.setFixedHeight(80)
        bottom_layout = QVBoxLayout(bottom_panel)

        export_btn = QPushButton("📤 Export všech")
        export_btn.setObjectName("codebooksActionButton")
        export_btn.clicked.connect(self.export_all_codebooks)
        bottom_layout.addWidget(export_btn)

        import_btn = QPushButton("📥 Import ze zálohy")
        import_btn.setObjectName("codebooksActionButton")
        import_btn.clicked.connect(self.import_all_codebooks)
        bottom_layout.addWidget(import_btn)

        nav_layout.addWidget(bottom_panel)

        parent_layout.addWidget(nav_widget)

    def create_content_panel(self, parent_layout):
        """Vytvoření pravého panelu s obsahem"""
        content_widget = QWidget()
        content_widget.setObjectName("codebooksContentPanel")

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Horní lišta
        top_bar = QFrame()
        top_bar.setObjectName("codebooksTopBar")
        top_bar.setFixedHeight(70)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(20, 10, 20, 10)

        # Název sekce
        self.section_title = QLabel("Značky vozidel")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.section_title.setFont(title_font)

        top_bar_layout.addWidget(self.section_title)
        top_bar_layout.addStretch()

        # Statistika
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #7f8c8d; font-size: 12pt;")
        top_bar_layout.addWidget(self.stats_label)

        content_layout.addWidget(top_bar)

        # Stack pro sekce
        self.section_stack = QStackedWidget()
        self.section_stack.setObjectName("codebooksSectionStack")

        # Vytvoření sekcí
        self.create_section_widgets()

        content_layout.addWidget(self.section_stack)

        parent_layout.addWidget(content_widget)

    def create_section_widgets(self):
        """Vytvoření widgetů pro jednotlivé sekce"""
        from .codebook_brands import BrandsWidget
        from .codebook_vehicle_types import VehicleTypesWidget
        from .codebook_fuel_types import FuelTypesWidget
        from .codebook_colors import ColorsWidget
        from .codebook_repair_types import RepairTypesWidget
        from .codebook_order_statuses import OrderStatusesWidget
        from .codebook_units import UnitsWidget
        from .codebook_positions import PositionsWidget
        from .codebook_hourly_rates import HourlyRatesWidget
        from .codebook_customer_groups import CustomerGroupsWidget
        from .codebook_payment_methods import PaymentMethodsWidget
        from .codebook_vat_rates import VatRatesWidget
        from .codebook_currencies import CurrenciesWidget

        # Značky vozidel
        self.sections["brands"] = BrandsWidget()
        self.section_stack.addWidget(self.sections["brands"])

        # Typy vozidel
        self.sections["vehicle_types"] = VehicleTypesWidget()
        self.section_stack.addWidget(self.sections["vehicle_types"])

        # Typy paliva
        self.sections["fuel_types"] = FuelTypesWidget()
        self.section_stack.addWidget(self.sections["fuel_types"])

        # Barvy
        self.sections["colors"] = ColorsWidget()
        self.section_stack.addWidget(self.sections["colors"])

        # Typy oprav
        self.sections["repair_types"] = RepairTypesWidget()
        self.section_stack.addWidget(self.sections["repair_types"])

        # Stavy zakázek
        self.sections["order_statuses"] = OrderStatusesWidget()
        self.section_stack.addWidget(self.sections["order_statuses"])

        # Jednotky
        self.sections["units"] = UnitsWidget()
        self.section_stack.addWidget(self.sections["units"])

        # Pozice
        self.sections["positions"] = PositionsWidget()
        self.section_stack.addWidget(self.sections["positions"])

        # Hodinové sazby
        self.sections["hourly_rates"] = HourlyRatesWidget()
        self.section_stack.addWidget(self.sections["hourly_rates"])

        # Zákaznické skupiny
        self.sections["customer_groups"] = CustomerGroupsWidget()
        self.section_stack.addWidget(self.sections["customer_groups"])

        # Způsoby platby
        self.sections["payment_methods"] = PaymentMethodsWidget()
        self.section_stack.addWidget(self.sections["payment_methods"])

        # Sazby DPH
        self.sections["vat_rates"] = VatRatesWidget()
        self.section_stack.addWidget(self.sections["vat_rates"])

        # Měny
        self.sections["currencies"] = CurrenciesWidget()
        self.section_stack.addWidget(self.sections["currencies"])

    def switch_section(self, section_id):
        """Přepnutí na jinou sekci"""
        if section_id in self.sections:
            # Zvýraznění aktivního tlačítka
            for btn_id, btn in self.section_buttons.items():
                btn.setProperty("active", btn_id == section_id)
                btn.style().unpolish(btn)
                btn.style().polish(btn)

            # Přepnutí stacku
            self.section_stack.setCurrentWidget(self.sections[section_id])
            self.current_section = section_id

            # Aktualizace titulku
            section_titles = {
                "brands": "🚗 Značky vozidel",
                "vehicle_types": "🏍️ Typy vozidel",
                "fuel_types": "⛽ Typy paliva",
                "colors": "🎨 Barvy vozidel",
                "repair_types": "🔧 Typy oprav",
                "order_statuses": "📋 Stavy zakázek",
                "units": "📏 Měrné jednotky",
                "positions": "👷 Pracovní pozice",
                "hourly_rates": "⏱️ Hodinové sazby",
                "customer_groups": "👥 Zákaznické skupiny",
                "payment_methods": "💳 Způsoby platby",
                "vat_rates": "📊 Sazby DPH",
                "currencies": "💱 Měny",
            }
            self.section_title.setText(section_titles.get(section_id, ""))

            # Refresh sekce a statistiky
            if hasattr(self.sections[section_id], 'refresh'):
                self.sections[section_id].refresh()

            self.update_stats()

    def update_stats(self):
        """Aktualizace statistik"""
        if not self.current_section or self.current_section not in self.sections:
            return

        widget = self.sections[self.current_section]
        if hasattr(widget, 'get_count'):
            count = widget.get_count()
            self.stats_label.setText(f"📊 Celkem položek: {count}")
        else:
            self.stats_label.setText("")

    def export_all_codebooks(self):
        """Export všech číselníků"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportovat číselníky",
            f"ciselniky_backup_{db.get_timestamp()}.json",
            "JSON soubory (*.json)"
        )

        if not file_path:
            return

        try:
            import json
            export_data = {
                "export_date": db.get_timestamp(),
                "version": "1.0",
                "codebooks": {}
            }

            # Export každého číselníku
            for section_id, widget in self.sections.items():
                if hasattr(widget, 'export_data'):
                    export_data["codebooks"][section_id] = widget.export_data()

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            QMessageBox.information(
                self,
                "Úspěch",
                f"Číselníky byly exportovány do:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se exportovat číselníky:\n{e}")

    def import_all_codebooks(self):
        """Import číselníků ze zálohy"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importovat číselníky",
            "",
            "JSON soubory (*.json)"
        )

        if not file_path:
            return

        reply = QMessageBox.question(
            self,
            "Import číselníků",
            "Opravdu chcete importovat číselníky?\n\n"
            "Existující data budou přepsána!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            import json

            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            if "codebooks" not in import_data:
                raise ValueError("Neplatný formát souboru")

            imported_count = 0

            for section_id, data in import_data["codebooks"].items():
                if section_id in self.sections:
                    widget = self.sections[section_id]
                    if hasattr(widget, 'import_data'):
                        widget.import_data(data)
                        imported_count += 1

            QMessageBox.information(
                self,
                "Úspěch",
                f"Importováno {imported_count} číselníků."
            )

            # Refresh aktuální sekce
            self.switch_section(self.current_section)

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se importovat číselníky:\n{e}")

    def refresh(self):
        """Obnovení dat modulu"""
        if self.current_section and hasattr(self.sections.get(self.current_section), 'refresh'):
            self.sections[self.current_section].refresh()
        self.update_stats()

    def apply_styles(self):
        """Aplikace stylů"""
        self.setStyleSheet(f"""
            #codebooksNavPanel {{
                background-color: {config.COLOR_PRIMARY};
                border-right: 2px solid #1a252f;
            }}
            #codebooksNavHeader {{
                background-color: #1a252f;
                color: white;
            }}
            #codebooksNavButton {{
                background-color: transparent;
                border: none;
                color: white;
                text-align: left;
                padding: 12px 15px;
                font-size: 12px;
                border-left: 3px solid transparent;
            }}
            #codebooksNavButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            #codebooksNavButton[active="true"] {{
                background-color: {config.COLOR_SECONDARY};
                border-left: 3px solid {config.COLOR_SUCCESS};
            }}
            #codebooksBottomPanel {{
                background-color: #1a252f;
                padding: 10px;
            }}
            #codebooksActionButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-size: 11px;
            }}
            #codebooksActionButton:hover {{
                background-color: #2980b9;
            }}
            #codebooksTopBar {{
                background-color: white;
                border-bottom: 2px solid #e0e0e0;
            }}
            #codebooksContentPanel {{
                background-color: #f5f5f5;
            }}
            #codebooksSectionStack {{
                background-color: #f5f5f5;
            }}
        """)
