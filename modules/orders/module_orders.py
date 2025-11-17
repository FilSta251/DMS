# -*- coding: utf-8 -*-
"""
Modul Zakázky - Hlavní seznam zakázek (OPRAVENÝ + VYLEPŠENÝ)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox,
    QLabel, QHeaderView, QMessageBox, QMenu, QGroupBox,
    QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QClipboard
import config
from database_manager import db
from .order_form import OrderFormDialog
from .order_detail import OrderDetailWindow


class OrdersModule(QWidget):
    """Modul pro správu zakázek"""

    order_selected = pyqtSignal(int)  # Signal při výběru zakázky

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_vehicle_id = None  # Pro filtrování podle motorky
        self.detail_windows = []  # Seznam otevřených detailů
        self.init_ui()
        self.load_orders()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Hlavička
        header = QHBoxLayout()

        title = QLabel("📋 Zakázky")
        title.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {config.COLOR_PRIMARY};
        """)
        header.addWidget(title)
        header.addStretch()

        # Tlačítka pro vytvoření zakázek
        self.btn_new_order = QPushButton("+ Nová zakázka")
        self.btn_new_order.setStyleSheet(self.get_button_style(config.COLOR_SUCCESS))
        self.btn_new_order.clicked.connect(lambda: self.create_order("Zakázka"))

        self.btn_free_sale = QPushButton("+ Volný prodej")
        self.btn_free_sale.setStyleSheet(self.get_button_style(config.COLOR_SECONDARY))
        self.btn_free_sale.clicked.connect(lambda: self.create_order("Volný prodej"))

        self.btn_offer = QPushButton("+ Nabídka")
        self.btn_offer.setStyleSheet(self.get_button_style(config.COLOR_WARNING))
        self.btn_offer.clicked.connect(lambda: self.create_order("Nabídka"))

        header.addWidget(self.btn_new_order)
        header.addWidget(self.btn_free_sale)
        header.addWidget(self.btn_offer)

        layout.addLayout(header)

        # Statistiky - rychlý přehled
        self.stats_widget = self.create_stats_widget()
        layout.addWidget(self.stats_widget)

        # Filtry
        filters = QHBoxLayout()

        # Vyhledávání
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Hledat podle čísla, zákazníka, motorky...")
        self.search_input.textChanged.connect(self.filter_orders)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        filters.addWidget(self.search_input, stretch=2)

        # Filtr typu
        filters.addWidget(QLabel("Typ:"))
        self.filter_type = QComboBox()
        self.filter_type.addItems(["Vše"] + config.ORDER_TYPES)
        self.filter_type.currentTextChanged.connect(self.filter_orders)
        self.filter_type.setStyleSheet(self.get_combo_style())
        filters.addWidget(self.filter_type)

        # Filtr stavu
        filters.addWidget(QLabel("Stav:"))
        self.filter_status = QComboBox()
        self.filter_status.addItems(["Vše"] + config.ORDER_STATUSES)
        self.filter_status.currentTextChanged.connect(self.filter_orders)
        self.filter_status.setStyleSheet(self.get_combo_style())
        filters.addWidget(self.filter_status)

        # Tlačítko reset filtrů
        btn_reset = QPushButton("🔄 Reset")
        btn_reset.clicked.connect(self.reset_filters)
        btn_reset.setStyleSheet(self.get_button_style("#95a5a6"))
        filters.addWidget(btn_reset)

        layout.addLayout(filters)

        # Tabulka zakázek
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Číslo", "Typ", "Stav", "Zákazník", "Motorka",
            "Datum vytvoření", "Datum dokončení", "Cena celkem", "Poznámka", "ID"
        ])

        # Skrytý sloupec ID
        self.table.setColumnHidden(9, True)

        # Nastavení tabulky
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)

        # Dvojklik otevře detail
        self.table.doubleClicked.connect(self.open_order_detail)

        # Pravé tlačítko myši
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.table)

        # Statistiky
        stats = QHBoxLayout()
        self.lbl_total = QLabel("Celkem: 0")
        self.lbl_total.setStyleSheet("font-size: 14px; font-weight: bold;")
        stats.addWidget(self.lbl_total)
        stats.addStretch()
        layout.addLayout(stats)

    def create_stats_widget(self):
        """Vytvoření widgetu se statistikami"""
        widget = QGroupBox("📊 Rychlý přehled")
        layout = QHBoxLayout(widget)

        # Statistické boxy
        self.lbl_stat_total = QLabel("Celkem: 0")
        self.lbl_stat_preparation = QLabel("V přípravě: 0")
        self.lbl_stat_open = QLabel("Otevřená: 0")
        self.lbl_stat_working = QLabel("Rozpracovaná: 0")

        # Styly
        for lbl in [self.lbl_stat_total, self.lbl_stat_preparation,
                    self.lbl_stat_open, self.lbl_stat_working]:
            lbl.setStyleSheet("padding: 5px; font-weight: bold;")

        self.lbl_stat_total.setStyleSheet("padding: 5px; font-weight: bold; color: #2c3e50;")
        self.lbl_stat_preparation.setStyleSheet("padding: 5px; font-weight: bold; color: #95a5a6;")
        self.lbl_stat_open.setStyleSheet("padding: 5px; font-weight: bold; color: #3498db;")
        self.lbl_stat_working.setStyleSheet("padding: 5px; font-weight: bold; color: #f39c12;")

        layout.addWidget(self.lbl_stat_total)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.lbl_stat_preparation)
        layout.addWidget(self.lbl_stat_open)
        layout.addWidget(self.lbl_stat_working)
        layout.addStretch()

        return widget

    def update_stats(self):
        """Aktualizace statistik"""
        try:
            # Celkový počet
            total = db.execute_query("SELECT COUNT(*) FROM orders")
            total_count = total[0][0] if total else 0

            # Podle stavů
            preparation = db.execute_query(
                "SELECT COUNT(*) FROM orders WHERE status = 'V přípravě'"
            )
            open_orders = db.execute_query(
                "SELECT COUNT(*) FROM orders WHERE status = 'Otevřená'"
            )
            working = db.execute_query(
                "SELECT COUNT(*) FROM orders WHERE status = 'Rozpracovaná'"
            )

            prep_count = preparation[0][0] if preparation else 0
            open_count = open_orders[0][0] if open_orders else 0
            work_count = working[0][0] if working else 0

            # Aktualizace labelů
            self.lbl_stat_total.setText(f"Celkem: {total_count}")
            self.lbl_stat_preparation.setText(f"V přípravě: {prep_count}")
            self.lbl_stat_open.setText(f"Otevřená: {open_count}")
            self.lbl_stat_working.setText(f"Rozpracovaná: {work_count}")

        except Exception as e:
            print(f"Chyba při aktualizaci statistik: {e}")

    def get_button_style(self, color):
        """Styl pro tlačítka"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 0.3)};
            }}
        """

    def get_combo_style(self):
        """Styl pro combobox"""
        return """
            QComboBox {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background-color: white;
                min-width: 150px;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
            }
        """

    def darken_color(self, hex_color, factor=0.2):
        """Ztmavení barvy"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = int(r * (1 - factor))
        g = int(g * (1 - factor))
        b = int(b * (1 - factor))
        return f'#{r:02x}{g:02x}{b:02x}'

    def create_order(self, order_type):
        """Vytvoření nové zakázky"""
        dialog = OrderFormDialog(order_type, vehicle_id=self.current_vehicle_id, parent=self)
        if dialog.exec():
            self.load_orders()
            QMessageBox.information(self, "Úspěch", f"{order_type} byla úspěšně vytvořena!")

    def load_orders(self):
        """Načtení zakázek z databáze"""
        try:
            query = """
                SELECT
                    o.id,
                    o.order_number,
                    o.order_type,
                    o.status,
                    c.first_name || ' ' || c.last_name as customer_name,
                    v.brand || ' ' || v.model || ' (' || v.license_plate || ')' as vehicle_info,
                    o.created_date,
                    o.completed_date,
                    o.total_price,
                    o.note
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                LEFT JOIN vehicles v ON o.vehicle_id = v.id
            """

            # Filtrování podle motorky
            params = []
            if self.current_vehicle_id:
                query += " WHERE o.vehicle_id = ?"
                params.append(self.current_vehicle_id)

            query += " ORDER BY o.created_date DESC"

            orders = db.execute_query(query, params)
            self.display_orders(orders)
            self.update_stats()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při načítání zakázek:\n{str(e)}")

    def refresh(self):
        """Obnovení dat - volá se při přepnutí na modul"""
        self.load_orders()
        self.update_stats()


    def display_orders(self, orders):
        """Zobrazení zakázek v tabulce"""
        self.table.setRowCount(0)

        for order in orders:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Číslo zakázky
            self.table.setItem(row, 0, QTableWidgetItem(str(order[1])))

            # Typ
            type_item = QTableWidgetItem(order[2])
            self.table.setItem(row, 1, type_item)

            # Stav
            status_item = QTableWidgetItem(order[3])
            status_color = config.ORDER_STATUS_COLORS.get(order[3], "#95a5a6")
            status_item.setBackground(QColor(status_color))
            status_item.setForeground(QColor("white"))
            self.table.setItem(row, 2, status_item)

            # Zákazník
            self.table.setItem(row, 3, QTableWidgetItem(order[4] or "---"))

            # Motorka
            self.table.setItem(row, 4, QTableWidgetItem(order[5] or "---"))

            # Datum vytvoření
            self.table.setItem(row, 5, QTableWidgetItem(order[6] or "---"))

            # Datum dokončení
            self.table.setItem(row, 6, QTableWidgetItem(order[7] or "---"))

            # Cena
            price = f"{order[8]:.2f} Kč" if order[8] else "0.00 Kč"
            price_item = QTableWidgetItem(price)
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 7, price_item)

            # Poznámka
            note_text = order[9][:50] + "..." if order[9] and len(order[9]) > 50 else (order[9] or "---")
            self.table.setItem(row, 8, QTableWidgetItem(note_text))

            # ID (skryté)
            self.table.setItem(row, 9, QTableWidgetItem(str(order[0])))

        # Aktualizace statistik
        self.lbl_total.setText(f"Celkem: {len(orders)}")

        # Automatické přizpůsobení šířky sloupců
        for i in range(8):
            self.table.resizeColumnToContents(i)

    def filter_orders(self):
        """Filtrování zakázek"""
        search_text = self.search_input.text().lower()
        filter_type = self.filter_type.currentText()
        filter_status = self.filter_status.currentText()

        for row in range(self.table.rowCount()):
            show = True

            # Filtr vyhledávání
            if search_text:
                row_text = ""
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        row_text += item.text().lower() + " "
                show = search_text in row_text

            # Filtr typu
            if show and filter_type != "Vše":
                type_item = self.table.item(row, 1)
                if type_item and type_item.text() != filter_type:
                    show = False

            # Filtr stavu
            if show and filter_status != "Vše":
                status_item = self.table.item(row, 2)
                if status_item and status_item.text() != filter_status:
                    show = False

            self.table.setRowHidden(row, not show)

        # Aktualizace počtu
        visible = sum(1 for row in range(self.table.rowCount()) if not self.table.isRowHidden(row))
        self.lbl_total.setText(f"Zobrazeno: {visible} / {self.table.rowCount()}")

    def reset_filters(self):
        """Reset filtrů"""
        self.search_input.clear()
        self.filter_type.setCurrentIndex(0)
        self.filter_status.setCurrentIndex(0)
        self.current_vehicle_id = None
        self.load_orders()

    def open_order_detail(self):
        """Otevření detailu zakázky"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        order_id = int(self.table.item(current_row, 9).text())

        # Otevření detailu v novém okně
        detail_window = OrderDetailWindow(order_id, parent=self)
        detail_window.order_updated.connect(self.load_orders)
        detail_window.show()
        self.detail_windows.append(detail_window)

    def show_context_menu(self, position):
        """Kontextové menu pravým tlačítkem - VYLEPŠENÉ"""
        if self.table.currentRow() < 0:
            return

        menu = QMenu(self)

        # Základní akce
        action_open = menu.addAction("📖 Otevřít detail")
        action_edit = menu.addAction("✏️ Upravit")

        menu.addSeparator()

        # Kopírovat číslo zakázky
        action_copy = menu.addAction("📋 Kopírovat číslo zakázky")

        menu.addSeparator()

        # Rychlé změny stavu
        status_menu = menu.addMenu("🔄 Změnit stav")
        for status in config.ORDER_STATUSES:
            status_action = status_menu.addAction(status)
            status_action.setData(status)

        menu.addSeparator()

        action_delete = menu.addAction("🗑️ Smazat")
        action_delete.setIcon(menu.style().standardIcon(menu.style().StandardPixmap.SP_TrashIcon))

        action = menu.exec(self.table.viewport().mapToGlobal(position))

        if action == action_open:
            self.open_order_detail()
        elif action == action_edit:
            self.edit_order()
        elif action == action_copy:
            self.copy_order_number()
        elif action == action_delete:
            self.delete_order()
        elif action and action.parent() == status_menu:
            # Změna stavu
            new_status = action.data()
            self.quick_change_status(new_status)

    def copy_order_number(self):
        """Kopírování čísla zakázky do schránky"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        order_number = self.table.item(current_row, 0).text()
        clipboard = QApplication.clipboard()
        clipboard.setText(order_number)

        QMessageBox.information(
            self,
            "Zkopírováno",
            f"Číslo zakázky {order_number} bylo zkopírováno do schránky."
        )

    def quick_change_status(self, new_status):
        """Rychlá změna stavu zakázky"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        order_id = int(self.table.item(current_row, 9).text())
        order_number = self.table.item(current_row, 0).text()

        try:
            db.execute_query(
                "UPDATE orders SET status = ? WHERE id = ?",
                [new_status, order_id]
            )

            QMessageBox.information(
                self,
                "Úspěch",
                f"Stav zakázky č. {order_number} byl změněn na: {new_status}"
            )

            self.load_orders()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při změně stavu:\n{str(e)}")

    def edit_order(self):
        """Úprava zakázky"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        order_id = int(self.table.item(current_row, 9).text())

        dialog = OrderFormDialog(order_id=order_id, parent=self)
        if dialog.exec():
            self.load_orders()

    def delete_order(self):
        """Smazání zakázky"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        order_number = self.table.item(current_row, 0).text()
        order_id = int(self.table.item(current_row, 9).text())

        reply = QMessageBox.question(
            self,
            "Potvrzení smazání",
            f"Opravdu chcete smazat zakázku č. {order_number}?\n"
            "Tato akce je nevratná a smaže i všechny položky zakázky!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                db.execute_query("DELETE FROM order_items WHERE order_id = ?", [order_id])
                db.execute_query("DELETE FROM orders WHERE id = ?", [order_id])
                self.load_orders()
                QMessageBox.information(self, "Úspěch", "Zakázka byla smazána.")
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Chyba při mazání:\n{str(e)}")

    def set_vehicle_filter(self, vehicle_id):
        """Nastavení filtru podle motorky"""
        self.current_vehicle_id = vehicle_id
        self.load_orders()
