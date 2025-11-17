# -*- coding: utf-8 -*-
"""
Modul Číselníky - Hlavní widget (PRODUKČNÍ VERZE)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QLabel, QFrame, QPushButton, QMessageBox,
                             QFileDialog, QProgressDialog, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime
import json
import config

# Import jednotlivých číselníků
from modules.codebooks.codebook_brands import BrandsWidget
from modules.codebooks.codebook_repair_types import RepairTypesWidget
from modules.codebooks.codebook_positions import PositionsWidget
from modules.codebooks.codebook_hourly_rates import HourlyRatesWidget
from modules.codebooks.codebook_customer_groups import CustomerGroupsWidget
from modules.codebooks.codebook_payment_methods import PaymentMethodsWidget
from modules.codebooks.codebook_vat_rates import VatRatesWidget
from modules.codebooks.codebook_order_statuses import OrderStatusesWidget
from modules.codebooks.codebook_units import UnitsWidget
from modules.codebooks.codebook_currencies import CurrenciesWidget


class CodebooksWidget(QWidget):
    """Hlavní widget pro správu všech číselníků"""

    data_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.codebook_widgets = {}
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Horní panel
        header = self.create_header()
        layout.addWidget(header)

        # Hlavní obsah - záložky
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.West)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background: white;
            }
            QTabBar::tab {
                background: #ecf0f1;
                padding: 12px 20px;
                margin-bottom: 2px;
                border-radius: 4px 0 0 4px;
                min-width: 180px;
                text-align: left;
            }
            QTabBar::tab:selected {
                background: white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #d5dbdb;
            }
        """)

        # Přidat jednotlivé číselníky
        self.add_codebook_tabs()

        layout.addWidget(self.tabs)

        # Spodní panel s informacemi
        footer = self.create_footer()
        layout.addWidget(footer)

    def create_header(self):
        """Vytvoření hlavičky"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {config.COLOR_PRIMARY};
                padding: 15px;
            }}
        """)
        layout = QHBoxLayout(frame)

        # Titulek
        title = QLabel("📚 Správa číselníků")
        title.setStyleSheet("color: white; font-size: 18pt; font-weight: bold;")
        layout.addWidget(title)

        layout.addStretch()

        # Akční tlačítka
        backup_btn = QPushButton("💾 Zálohovat vše")
        backup_btn.clicked.connect(self.backup_all)
        backup_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #2c3e50;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ecf0f1;
            }
        """)
        layout.addWidget(backup_btn)

        restore_btn = QPushButton("📂 Obnovit ze zálohy")
        restore_btn.clicked.connect(self.restore_from_backup)
        restore_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #2c3e50;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ecf0f1;
            }
        """)
        layout.addWidget(restore_btn)

        refresh_btn = QPushButton("🔄 Obnovit vše")
        refresh_btn.clicked.connect(self.refresh_all)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #2c3e50;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ecf0f1;
            }
        """)
        layout.addWidget(refresh_btn)

        return frame

    def add_codebook_tabs(self):
        """Přidání záložek pro jednotlivé číselníky"""
        # Definice číselníků - (název záložky, tooltip, widget třída, klíč)
        codebooks = [
            ("�icing Výrobci", "Výrobci motocyklů", BrandsWidget, "brands"),

            ("🔧 Typy oprav", "Typy servisních oprav", RepairTypesWidget, "repair_types"),
            ("👷 Pracovní pozice", "Pracovní pozice", PositionsWidget, "positions"),
            ("⏱️ Hodinové sazby", "Hodinové sazby práce", HourlyRatesWidget, "hourly_rates"),
            ("👥 Zákaznické skupiny", "Skupiny zákazníků", CustomerGroupsWidget, "customer_groups"),
            ("💳 Způsoby platby", "Způsoby úhrady", PaymentMethodsWidget, "payment_methods"),
            ("📊 Sazby DPH", "Sazby daně z přidané hodnoty", VatRatesWidget, "vat_rates"),
            ("📋 Stavy zakázek", "Stavy a workflow zakázek", OrderStatusesWidget, "order_statuses"),
            ("📏 Měrné jednotky", "Měrné jednotky", UnitsWidget, "units"),
            ("💱 Měny", "Měny", CurrenciesWidget, "currencies"),
        ]

        for tab_name, tooltip, widget_class, key in codebooks:
            try:
                widget = widget_class()
                widget.data_changed.connect(self.on_data_changed)
                self.codebook_widgets[key] = widget

                self.tabs.addTab(widget, tab_name)
                self.tabs.setTabToolTip(self.tabs.count() - 1, tooltip)

            except Exception as e:
                # Pokud se nepodaří načíst widget, zobrazit chybový placeholder
                error_widget = self.create_error_widget(tab_name, str(e))
                self.tabs.addTab(error_widget, tab_name)
                print(f"Chyba při načítání {key}: {e}")

    def create_error_widget(self, name, error):
        """Vytvoření widgetu pro chybový stav"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("⚠️")
        icon.setStyleSheet("font-size: 48pt;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        title = QLabel(f"Nepodařilo se načíst: {name}")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #e74c3c;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        error_label = QLabel(f"Chyba: {error}")
        error_label.setStyleSheet("color: #7f8c8d;")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setWordWrap(True)
        layout.addWidget(error_label)

        return widget

    def create_footer(self):
        """Vytvoření spodního panelu"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                padding: 10px;
                border-top: 1px solid #bdc3c7;
            }
        """)
        layout = QHBoxLayout(frame)

        # Statistiky
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #7f8c8d; font-size: 11pt;")
        layout.addWidget(self.stats_label)

        layout.addStretch()

        # Verze
        version_label = QLabel(f"Číselníky v{config.APP_VERSION}")
        version_label.setStyleSheet("color: #95a5a6; font-size: 10pt;")
        layout.addWidget(version_label)

        # Aktualizovat statistiky
        QTimer.singleShot(500, self.update_stats)

        return frame

    def update_stats(self):
        """Aktualizace statistik"""
        total_items = 0
        stats_parts = []

        for key, widget in self.codebook_widgets.items():
            if hasattr(widget, 'get_count'):
                try:
                    count = widget.get_count()
                    total_items += count
                except:
                    pass

        stats_parts.append(f"Celkem položek: {total_items}")
        stats_parts.append(f"Číselníků: {len(self.codebook_widgets)}")

        self.stats_label.setText(" | ".join(stats_parts))

    def on_data_changed(self):
        """Handler pro změnu dat v číselníku"""
        self.update_stats()
        self.data_changed.emit()

    def refresh_all(self):
        """Obnovení všech číselníků"""
        progress = QProgressDialog("Obnovuji číselníky...", None, 0, len(self.codebook_widgets), self)
        progress.setWindowTitle("Obnovení")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        for i, (key, widget) in enumerate(self.codebook_widgets.items()):
            progress.setValue(i)
            QApplication.processEvents()

            if hasattr(widget, 'refresh'):
                try:
                    widget.refresh()
                except Exception as e:
                    print(f"Chyba při obnovení {key}: {e}")

        progress.setValue(len(self.codebook_widgets))
        self.update_stats()

        QMessageBox.information(self, "Dokončeno", "Všechny číselníky byly obnoveny.")

    def backup_all(self):
        """Záloha všech číselníků do JSON"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit zálohu číselníků",
            f"ciselniky_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON soubory (*.json)"
        )

        if not file_path:
            return

        try:
            backup_data = {
                "version": config.APP_VERSION,
                "timestamp": datetime.now().isoformat(),
                "codebooks": {}
            }

            progress = QProgressDialog("Vytvářím zálohu...", None, 0, len(self.codebook_widgets), self)
            progress.setWindowTitle("Záloha")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()

            for i, (key, widget) in enumerate(self.codebook_widgets.items()):
                progress.setValue(i)
                QApplication.processEvents()

                if hasattr(widget, 'export_data'):
                    try:
                        data = widget.export_data()
                        backup_data["codebooks"][key] = data
                    except Exception as e:
                        print(f"Chyba při exportu {key}: {e}")

            progress.setValue(len(self.codebook_widgets))

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)

            QMessageBox.information(
                self,
                "Záloha dokončena",
                f"Záloha byla uložena do:\n{file_path}\n\n"
                f"Zálohováno {len(backup_data['codebooks'])} číselníků."
            )

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se vytvořit zálohu:\n{e}")

    def restore_from_backup(self):
        """Obnovení číselníků ze zálohy"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Načíst zálohu číselníků",
            "",
            "JSON soubory (*.json)"
        )

        if not file_path:
            return

        reply = QMessageBox.warning(
            self,
            "Obnovení ze zálohy",
            "Opravdu chcete obnovit číselníky ze zálohy?\n\n"
            "Tato akce může přepsat existující data!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            if "codebooks" not in backup_data:
                QMessageBox.warning(self, "Chyba", "Neplatný formát zálohy.")
                return

            progress = QProgressDialog("Obnovuji ze zálohy...", None, 0, len(backup_data["codebooks"]), self)
            progress.setWindowTitle("Obnovení")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()

            restored = 0
            for i, (key, data) in enumerate(backup_data["codebooks"].items()):
                progress.setValue(i)
                QApplication.processEvents()

                if key in self.codebook_widgets:
                    widget = self.codebook_widgets[key]
                    if hasattr(widget, 'import_data'):
                        try:
                            widget.import_data(data)
                            restored += 1
                        except Exception as e:
                            print(f"Chyba při importu {key}: {e}")

            progress.setValue(len(backup_data["codebooks"]))

            self.update_stats()

            QMessageBox.information(
                self,
                "Obnovení dokončeno",
                f"Obnoveno {restored} číselníků ze zálohy.\n\n"
                f"Záloha z: {backup_data.get('timestamp', 'Neznámé')}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se obnovit ze zálohy:\n{e}")

    def get_current_widget(self):
        """Vrátí aktuálně vybraný widget"""
        return self.tabs.currentWidget()

    def get_codebook_widget(self, key):
        """Vrátí widget podle klíče"""
        return self.codebook_widgets.get(key)
