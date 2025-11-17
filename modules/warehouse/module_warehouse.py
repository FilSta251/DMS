# -*- coding: utf-8 -*-
"""
Modul Sklad - HLAVNÍ OKNO
Seznam položek, filtry, příjem, výdej, inventura
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QLabel, QComboBox, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
import config
from database_manager import db

class WarehouseModule(QWidget):
    """Hlavní modul skladu"""

    item_selected = pyqtSignal(int)  # ID vybrané položky

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_filter_category = None
        self.current_filter_supplier = None
        self.current_filter_status = "all"

        self.init_ui()
        self.load_filters()
        self.load_warehouse_items()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === HORNÍ LIŠTA S AKCEMI ===
        self.create_action_bar(layout)

        # === FILTRY ===
        self.create_filters(layout)

        # === TABULKA POLOŽEK ===
        self.create_table(layout)

        # === DOLNÍ LIŠTA SE STATISTIKAMI ===
        self.create_stats_bar(layout)

    def create_action_bar(self, parent_layout):
        """Horní lišta s tlačítky"""
        action_bar = QWidget()
        action_bar.setFixedHeight(60)
        action_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {config.COLOR_PRIMARY};
                border-bottom: 2px solid #1a252f;
            }}
        """)
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(15, 10, 15, 10)

        # Nadpis
        title = QLabel("📦 SKLAD")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        action_layout.addWidget(title)

        action_layout.addStretch()

        # === TLAČÍTKO UPOZORNĚNÍ ===
        self.btn_alerts = QPushButton("⚠️ Upozornění")
        self.btn_alerts.setStyleSheet(self.get_button_style(config.COLOR_DANGER))
        self.btn_alerts.clicked.connect(self.show_alerts)
        action_layout.addWidget(self.btn_alerts)

        # Aktualizace počtu upozornění
        self.update_alert_badge()

        # === TLAČÍTKO NOVÁ POLOŽKA ===
        btn_new = QPushButton("➕ Nová položka")
        btn_new.setStyleSheet(self.get_button_style(config.COLOR_SUCCESS))
        btn_new.clicked.connect(self.add_new_item)
        action_layout.addWidget(btn_new)

        # === TLAČÍTKO PŘÍJEM ===
        btn_receive = QPushButton("📥 Příjem")
        btn_receive.setStyleSheet(self.get_button_style(config.COLOR_SECONDARY))
        btn_receive.clicked.connect(self.receive_stock)
        action_layout.addWidget(btn_receive)

        # === TLAČÍTKO VÝDEJ ===
        btn_issue = QPushButton("📤 Výdej")
        btn_issue.setStyleSheet(self.get_button_style("#e67e22"))
        btn_issue.clicked.connect(self.issue_stock)
        action_layout.addWidget(btn_issue)

        # === TLAČÍTKO INVENTURA ===
        btn_inventory = QPushButton("📋 Inventura")
        btn_inventory.setStyleSheet(self.get_button_style("#9b59b6"))
        btn_inventory.clicked.connect(self.do_inventory)
        action_layout.addWidget(btn_inventory)

        # === TLAČÍTKO VÍCE (MENU) ===
        btn_more = QPushButton("⚙️ Více")
        btn_more.setStyleSheet(self.get_button_style("#7f8c8d"))
        btn_more.clicked.connect(self.show_more_menu)
        action_layout.addWidget(btn_more)

        parent_layout.addWidget(action_bar)

    def create_filters(self, parent_layout):
        """Filtry"""
        filter_bar = QWidget()
        filter_bar.setStyleSheet("background-color: #ecf0f1; padding: 10px;")
        filter_layout = QHBoxLayout(filter_bar)

        # Vyhledávání
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("🔍 Hledat položku (název, kód, EAN)...")
        self.input_search.setFixedWidth(300)
        self.input_search.textChanged.connect(self.on_search)
        filter_layout.addWidget(self.input_search)

        # Kategorie
        filter_layout.addWidget(QLabel("Kategorie:"))
        self.combo_category = QComboBox()
        self.combo_category.setFixedWidth(200)
        self.combo_category.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.combo_category)

        # Dodavatel
        filter_layout.addWidget(QLabel("Dodavatel:"))
        self.combo_supplier = QComboBox()
        self.combo_supplier.setFixedWidth(200)
        self.combo_supplier.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.combo_supplier)

        # Stav
        filter_layout.addWidget(QLabel("Stav:"))
        self.combo_status = QComboBox()
        self.combo_status.addItems([
            "Všechny položky",
            "⚠️ Pod minimem",
            "✓ Nad minimem",
            "❌ Nulový stav"
        ])
        self.combo_status.setFixedWidth(150)
        self.combo_status.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.combo_status)

        filter_layout.addStretch()

        # Reset filtrů
        btn_reset = QPushButton("↺ Reset")
        btn_reset.clicked.connect(self.reset_filters)
        filter_layout.addWidget(btn_reset)

        parent_layout.addWidget(filter_bar)

    def create_table(self, parent_layout):
        """Tabulka položek"""
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "Kód", "Název", "Kategorie", "Množství", "Jedn.",
            "Min. stav", "Cena nákup", "Cena prodej", "Marže %", "Dodavatel", "ID"
        ])

        # Skrytí ID
        self.table.setColumnHidden(10, True)

        # Nastavení
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)

        # Double click pro detail
        self.table.doubleClicked.connect(self.open_detail)

        # Kontextové menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        parent_layout.addWidget(self.table)

    def create_stats_bar(self, parent_layout):
        """Dolní lišta se statistikami"""
        stats_bar = QWidget()
        stats_bar.setFixedHeight(40)
        stats_bar.setStyleSheet("background-color: #ecf0f1; border-top: 1px solid #bdc3c7;")
        stats_layout = QHBoxLayout(stats_bar)
        stats_layout.setContentsMargins(15, 5, 15, 5)

        self.lbl_total_items = QLabel("Celkem položek: 0")
        stats_layout.addWidget(self.lbl_total_items)

        self.lbl_total_value = QLabel("Hodnota skladu: 0.00 Kč")
        stats_layout.addWidget(self.lbl_total_value)

        self.lbl_below_minimum = QLabel("⚠️ Pod minimem: 0")
        self.lbl_below_minimum.setStyleSheet("color: #e74c3c; font-weight: bold;")
        stats_layout.addWidget(self.lbl_below_minimum)

        stats_layout.addStretch()

        parent_layout.addWidget(stats_bar)

    def get_button_style(self, color):
        """Styl tlačítek"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """

    def load_filters(self):
        """Načtení filtrů"""
        try:
            # Kategorie
            self.combo_category.clear()
            self.combo_category.addItem("Všechny kategorie", None)

            categories = db.execute_query("SELECT id, name FROM warehouse_categories ORDER BY name")
            if categories:
                for cat in categories:
                    self.combo_category.addItem(cat[1], cat[0])

            # Dodavatelé
            self.combo_supplier.clear()
            self.combo_supplier.addItem("Všichni dodavatelé", None)

            suppliers = db.execute_query("SELECT id, name FROM warehouse_suppliers ORDER BY name")
            if suppliers:
                for sup in suppliers:
                    self.combo_supplier.addItem(sup[1], sup[0])

        except Exception as e:
            print(f"Chyba při načítání filtrů: {e}")

    def load_warehouse_items(self):
        """Načtení položek skladu"""
        try:
            # Sestavení SQL dotazu s filtry
            query = """
                SELECT
                    w.id, w.code, w.name, w.quantity, w.unit, w.min_quantity,
                    w.price_purchase, w.price_sale,
                    c.name as category_name,
                    s.name as supplier_name
                FROM warehouse w
                LEFT JOIN warehouse_categories c ON w.category_id = c.id
                LEFT JOIN warehouse_suppliers s ON w.supplier_id = s.id
                WHERE 1=1
            """

            params = []

            # Filtr vyhledávání
            search_text = self.input_search.text().strip()
            if search_text:
                query += " AND (w.name LIKE ? OR w.code LIKE ? OR w.ean LIKE ?)"
                search_param = f"%{search_text}%"
                params.extend([search_param, search_param, search_param])

            # Filtr kategorie
            category_id = self.combo_category.currentData()
            if category_id:
                query += " AND w.category_id = ?"
                params.append(category_id)

            # Filtr dodavatel
            supplier_id = self.combo_supplier.currentData()
            if supplier_id:
                query += " AND w.supplier_id = ?"
                params.append(supplier_id)

            # Filtr stavu
            status_index = self.combo_status.currentIndex()
            if status_index == 1:  # Pod minimem
                query += " AND w.quantity < w.min_quantity"
            elif status_index == 2:  # Nad minimem
                query += " AND w.quantity >= w.min_quantity"
            elif status_index == 3:  # Nulový stav
                query += " AND w.quantity = 0"

            query += " ORDER BY w.name"

            items = db.execute_query(query, params)

            # Vyčištění tabulky
            self.table.setRowCount(0)

            if not items:
                self.update_stats(0, 0, 0)
                return

            # Vyplnění tabulky
            total_value = 0
            below_minimum = 0

            for item in items:
                row = self.table.rowCount()
                self.table.insertRow(row)

                item_id = item[0]
                code = item[1] or ""
                name = item[2]
                quantity = item[3]
                unit = item[4]
                min_qty = item[5]
                price_purchase = item[6] or 0
                price_sale = item[7] or 0
                category = item[8] or "---"
                supplier = item[9] or "---"

                # Marže
                if price_purchase > 0:
                    margin = ((price_sale - price_purchase) / price_purchase) * 100
                else:
                    margin = 0

                # Hodnota
                total_value += quantity * price_purchase

                # Kontrola minima
                is_below_min = quantity < min_qty
                if is_below_min:
                    below_minimum += 1

                # Vyplnění buněk
                self.table.setItem(row, 0, QTableWidgetItem(code))
                self.table.setItem(row, 1, QTableWidgetItem(name))
                self.table.setItem(row, 2, QTableWidgetItem(category))

                qty_item = QTableWidgetItem(f"{quantity:.2f}")
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 3, qty_item)

                self.table.setItem(row, 4, QTableWidgetItem(unit))

                min_item = QTableWidgetItem(f"{min_qty:.2f}")
                min_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 5, min_item)

                purchase_item = QTableWidgetItem(f"{price_purchase:.2f} Kč")
                purchase_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 6, purchase_item)

                sale_item = QTableWidgetItem(f"{price_sale:.2f} Kč")
                sale_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 7, sale_item)

                margin_item = QTableWidgetItem(f"{margin:.1f}%")
                margin_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 8, margin_item)

                self.table.setItem(row, 9, QTableWidgetItem(supplier))
                self.table.setItem(row, 10, QTableWidgetItem(str(item_id)))

                # Barevné zvýraznění řádku
                if quantity == 0:
                    color = QColor(config.STOCK_ZERO)
                elif is_below_min:
                    color = QColor(config.STOCK_CRITICAL)
                elif quantity < min_qty * 1.5:
                    color = QColor(config.STOCK_WARNING)
                else:
                    color = QColor(config.STOCK_OK)

                # Zvýraznění sloupce s množstvím
                qty_item.setBackground(color)
                qty_item.setForeground(QColor("white") if quantity < min_qty else QColor("black"))

            # Aktualizace statistik
            self.update_stats(len(items), total_value, below_minimum)

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při načítání skladu:\n{str(e)}")

    def update_stats(self, total_items, total_value, below_minimum):
        """Aktualizace statistik"""
        self.lbl_total_items.setText(f"Celkem položek: {total_items}")
        self.lbl_total_value.setText(f"Hodnota skladu: {total_value:,.2f} Kč")
        self.lbl_below_minimum.setText(f"⚠️ Pod minimem: {below_minimum}")

    def on_search(self):
        """Změna vyhledávání"""
        self.load_warehouse_items()

    def on_filter_changed(self):
        """Změna filtru"""
        self.load_warehouse_items()

    def reset_filters(self):
        """Reset filtrů"""
        self.input_search.clear()
        self.combo_category.setCurrentIndex(0)
        self.combo_supplier.setCurrentIndex(0)
        self.combo_status.setCurrentIndex(0)
        self.load_warehouse_items()

    def receive_stock(self):
        """Příjem na sklad"""
        from .warehouse_widgets import ReceiveStockDialog
        dialog = ReceiveStockDialog(parent=self)
        dialog.stock_received.connect(self.load_warehouse_items)
        dialog.exec()

    def issue_stock(self):
        """Výdej ze skladu"""
        from .warehouse_widgets import IssueStockDialog
        dialog = IssueStockDialog(parent=self)
        dialog.stock_issued.connect(self.load_warehouse_items)
        dialog.exec()

    def do_inventory(self):
        """Inventura"""
        from .warehouse_widgets import InventoryDialog
        dialog = InventoryDialog(parent=self)
        dialog.inventory_done.connect(self.load_warehouse_items)
        dialog.exec()
    def add_new_item(self):
        """Nová položka"""
        from .warehouse_detail import WarehouseDetailWindow
        dialog = WarehouseDetailWindow(parent=self)
        dialog.item_updated.connect(self.load_warehouse_items)
        dialog.show()

    def open_detail(self):
        """Otevření detailu položky"""
        if self.table.currentRow() < 0:
            return

        item_id = int(self.table.item(self.table.currentRow(), 10).text())
        from .warehouse_detail import WarehouseDetailWindow
        dialog = WarehouseDetailWindow(item_id, self)
        dialog.item_updated.connect(self.load_warehouse_items)
        dialog.show()

    def show_context_menu(self, position):
        """Kontextové menu"""
        if self.table.currentRow() < 0:
            return

        menu = QMenu()

        action_detail = menu.addAction("📋 Detail")
        action_detail.triggered.connect(self.open_detail)

        menu.addSeparator()

        action_receive = menu.addAction("➕ Příjem")
        action_receive.triggered.connect(self.receive_stock)

        action_issue = menu.addAction("➖ Výdej")
        action_issue.triggered.connect(self.issue_stock)

        menu.addSeparator()

        action_delete = menu.addAction("🗑️ Smazat")
        action_delete.triggered.connect(self.delete_item)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def delete_item(self):
        """Smazání položky"""
        if self.table.currentRow() < 0:
            return

        item_id = int(self.table.item(self.table.currentRow(), 10).text())
        item_name = self.table.item(self.table.currentRow(), 1).text()

        reply = QMessageBox.question(
            self,
            "Smazat položku?",
            f"Opravdu smazat '{item_name}' ze skladu?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                db.execute_query("DELETE FROM warehouse WHERE id = ?", [item_id])
                self.load_warehouse_items()
                QMessageBox.information(self, "Úspěch", "Položka byla smazána")
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Chyba:\n{str(e)}")

    def show_more_menu(self):
        """Menu s dalšími akcemi"""
        menu = QMenu(self)

        action_categories = menu.addAction("📁 Kategorie")
        action_categories.triggered.connect(self.manage_categories)

        action_suppliers = menu.addAction("🚚 Dodavatelé")
        action_suppliers.triggered.connect(self.manage_suppliers)

        menu.addSeparator()

        action_movements = menu.addAction("📊 Historie pohybů")
        action_movements.triggered.connect(self.show_movements)

        action_analytics = menu.addAction("📈 Analýzy")
        action_analytics.triggered.connect(self.show_analytics)

        menu.addSeparator()

        # NOVÉ - Hromadná úprava
        action_bulk_edit = menu.addAction("🔧 Hromadná úprava")
        action_bulk_edit.triggered.connect(self.bulk_edit)

        menu.addSeparator()

        action_import = menu.addAction("📥 Import")
        action_import.triggered.connect(self.import_items)

        action_export = menu.addAction("📤 Export")
        action_export.triggered.connect(self.export_items)

        action_labels = menu.addAction("🏷️ Tisk štítků")
        action_labels.triggered.connect(self.print_labels)

        button = self.sender()
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))

    def bulk_edit(self):
        """Hromadná úprava"""
        from .warehouse_widgets import BulkEditDialog
        dialog = BulkEditDialog(self)
        dialog.items_updated.connect(self.load_warehouse_items)
        dialog.exec()
    def manage_categories(self):
        """Správa kategorií"""
        from .warehouse_categories import WarehouseCategoriesWindow
        dialog = WarehouseCategoriesWindow(self)
        dialog.categories_changed.connect(self.load_warehouse_items)
        dialog.categories_changed.connect(self.load_filters)
        dialog.show()

    def manage_suppliers(self):
        """Správa dodavatelů"""
        from .warehouse_suppliers import WarehouseSuppliersWindow
        dialog = WarehouseSuppliersWindow(self)
        dialog.suppliers_changed.connect(self.load_warehouse_items)
        dialog.suppliers_changed.connect(self.load_filters)
        dialog.show()

    def show_movements(self):
        """Historie pohybů"""
        from .warehouse_movements import WarehouseMovementsWindow
        dialog = WarehouseMovementsWindow(self)
        dialog.movement_changed.connect(self.load_warehouse_items)
        dialog.show()

    def show_analytics(self):
        """Analýzy"""
        from .warehouse_analytics import WarehouseAnalyticsWindow
        dialog = WarehouseAnalyticsWindow(self)
        dialog.show()

    def import_items(self):
        """Import"""
        from .warehouse_import import WarehouseImportDialog
        dialog = WarehouseImportDialog(self)
        dialog.items_imported.connect(self.load_warehouse_items)
        dialog.exec()

    def export_items(self):
        """Export"""
        from PyQt6.QtWidgets import QMenu
        from .warehouse_export import exporter

        menu = QMenu(self)

        # PDF exporty
        pdf_menu = menu.addMenu("📄 Export do PDF")

        action_price_list = pdf_menu.addAction("Ceník")
        action_price_list.triggered.connect(self.export_price_list_pdf)

        action_inventory = pdf_menu.addAction("Inventurní seznam")
        action_inventory.triggered.connect(self.export_inventory_pdf)

        action_below_min = pdf_menu.addAction("Položky pod minimem")
        action_below_min.triggered.connect(self.export_below_minimum_pdf)

        # Excel exporty
        excel_menu = menu.addMenu("📊 Export do Excel")

        action_full_warehouse = excel_menu.addAction("Kompletní sklad")
        action_full_warehouse.triggered.connect(self.export_full_warehouse_excel)

        action_movements = excel_menu.addAction("Pohyby skladu")
        action_movements.triggered.connect(self.export_movements_excel)

        action_abc = excel_menu.addAction("ABC analýza")
        action_abc.triggered.connect(self.export_abc_analysis)

        # Zobrazení menu
        button = self.sender()
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))

    def export_price_list_pdf(self):
        """Export ceníku"""
        from PyQt6.QtWidgets import QFileDialog
        from .warehouse_export import exporter
        from datetime import datetime

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit ceník",
            f"cenik_{datetime.now().strftime('%Y%m%d')}.pdf",
            "PDF soubory (*.pdf)"
        )

        if file_path:
            if exporter.export_price_list_pdf(file_path):
                QMessageBox.information(self, "Úspěch", f"Ceník byl vyexportován:\n{file_path}")
                try:
                    import os
                    os.startfile(file_path)
                except:
                    pass
            else:
                QMessageBox.critical(self, "Chyba", "Nepodařilo se exportovat ceník")

    def export_inventory_pdf(self):
        """Export inventurního seznamu"""
        from PyQt6.QtWidgets import QFileDialog
        from .warehouse_export import exporter
        from datetime import datetime

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit inventurní seznam",
            f"inventura_{datetime.now().strftime('%Y%m%d')}.pdf",
            "PDF soubory (*.pdf)"
        )

        if file_path:
            if exporter.export_inventory_list_pdf(file_path):
                QMessageBox.information(self, "Úspěch", f"Inventurní seznam byl vyexportován:\n{file_path}")
                try:
                    import os
                    os.startfile(file_path)
                except:
                    pass
            else:
                QMessageBox.critical(self, "Chyba", "Nepodařilo se exportovat")

    def export_below_minimum_pdf(self):
        """Export položek pod minimem"""
        from PyQt6.QtWidgets import QFileDialog
        from .warehouse_export import exporter
        from datetime import datetime

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit seznam",
            f"pod_minimem_{datetime.now().strftime('%Y%m%d')}.pdf",
            "PDF soubory (*.pdf)"
        )

        if file_path:
            if exporter.export_below_minimum_pdf(file_path):
                QMessageBox.information(self, "Úspěch", f"Seznam byl vyexportován:\n{file_path}")
                try:
                    import os
                    os.startfile(file_path)
                except:
                    pass
            else:
                QMessageBox.critical(self, "Chyba", "Nepodařilo se exportovat")

    def export_full_warehouse_excel(self):
        """Export kompletního skladu"""
        from PyQt6.QtWidgets import QFileDialog
        from .warehouse_export import exporter
        from datetime import datetime

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit jako Excel",
            f"sklad_{datetime.now().strftime('%Y%m%d')}.xlsx",
            "Excel soubory (*.xlsx)"
        )

        if file_path:
            if exporter.export_full_warehouse_excel(file_path):
                QMessageBox.information(self, "Úspěch", f"Sklad byl vyexportován:\n{file_path}")
                try:
                    import os
                    os.startfile(file_path)
                except:
                    pass
            else:
                QMessageBox.critical(self, "Chyba", "Nepodařilo se exportovat")

    def export_movements_excel(self):
        """Export pohybů"""
        from PyQt6.QtWidgets import QFileDialog
        from .warehouse_export import exporter
        from datetime import datetime

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit jako Excel",
            f"pohyby_{datetime.now().strftime('%Y%m%d')}.xlsx",
            "Excel soubory (*.xlsx)"
        )

        if file_path:
            if exporter.export_movements_excel(file_path):
                QMessageBox.information(self, "Úspěch", f"Pohyby byly vyexportovány:\n{file_path}")
                try:
                    import os
                    os.startfile(file_path)
                except:
                    pass
            else:
                QMessageBox.critical(self, "Chyba", "Nepodařilo se exportovat")

    def export_abc_analysis(self):
        """Export ABC analýzy"""
        from PyQt6.QtWidgets import QFileDialog
        from .warehouse_export import exporter
        from datetime import datetime

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit ABC analýzu",
            f"abc_analyza_{datetime.now().strftime('%Y%m%d')}.xlsx",
            "Excel soubory (*.xlsx)"
        )

        if file_path:
            if exporter.export_abc_analysis_excel(file_path):
                QMessageBox.information(self, "Úspěch", f"ABC analýza byla vyexportována:\n{file_path}")
                try:
                    import os
                    os.startfile(file_path)
                except:
                    pass
            else:
                QMessageBox.critical(self, "Chyba", "Nepodařilo se exportovat")

    def update_alert_badge(self):
        """Aktualizace počtu upozornění na tlačítku"""
        try:
            from .warehouse_stock_alert import StockAlertChecker
            count = StockAlertChecker.get_alert_badge_count()

            if count > 0:
                self.btn_alerts.setText(f"⚠️ Upozornění ({count})")
                self.btn_alerts.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {config.COLOR_DANGER};
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 5px;
                        font-weight: bold;
                        font-size: 12px;
                        animation: blink 1s infinite;
                    }}
                """)
            else:
                self.btn_alerts.setText("⚠️ Upozornění")
                self.btn_alerts.setStyleSheet(self.get_button_style("#95a5a6"))
        except:
            pass

    def show_alerts(self):
        """Zobrazení systému upozornění"""
        from .warehouse_stock_alert import WarehouseStockAlertWindow
        dialog = WarehouseStockAlertWindow(self)
        dialog.alert_resolved.connect(self.load_warehouse_items)
        dialog.alert_resolved.connect(self.update_alert_badge)
        dialog.show()

    def refresh(self):
        """Refresh modulu (voláno při přepnutí)"""
        self.load_warehouse_items()
        self.update_alert_badge()

    def print_labels(self):
        """Tisk štítků"""
        from .warehouse_labels import WarehouseLabelsDialog

        # Získání vybraných položek
        selected = []
        for item in self.table.selectedItems():
            if item.column() == 8:  # ID sloupec
                item_id = int(item.text())
                if item_id not in selected:
                    selected.append(item_id)

        if not selected:
            QMessageBox.warning(self, "Info", "Nejprve vyberte položky pro tisk štítků")
            return

        dialog = WarehouseLabelsDialog(self, items_list=selected)
        dialog.exec()
