# -*- coding: utf-8 -*-
"""
Tabulkový seznam událostí kalendáře
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QLabel,
    QComboBox, QLineEdit, QFrame, QMenu, QMessageBox,
    QDateEdit, QCheckBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QIcon, QAction
from datetime import datetime, date, timedelta
from database_manager import db
import config


class CalendarEventsList(QWidget):
    """Widget pro tabulkový seznam událostí"""

    event_selected = pyqtSignal(int)
    event_edit_requested = pyqtSignal(int)
    event_delete_requested = pyqtSignal(int)
    event_duplicate_requested = pyqtSignal(int)
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_sort_column = 0
        self.current_sort_order = Qt.SortOrder.AscendingOrder
        self.selected_events = []

        self.init_ui()
        self.load_filter_data()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Horní panel s filtry
        filters_panel = self.create_filters_panel()
        layout.addWidget(filters_panel)

        # Tabulka
        self.create_table()
        layout.addWidget(self.table)

        # Spodní panel s akcemi a statistikami
        bottom_panel = self.create_bottom_panel()
        layout.addWidget(bottom_panel)

    def create_filters_panel(self):
        """Vytvoření panelu s filtry"""
        panel = QFrame()
        panel.setObjectName("filtersPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        # První řádek filtrů
        row1 = QHBoxLayout()

        # Vyhledávání
        search_label = QLabel("🔍")
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Vyhledat událost...")
        self.txt_search.setMinimumWidth(200)
        self.txt_search.textChanged.connect(self.on_filter_changed)
        row1.addWidget(search_label)
        row1.addWidget(self.txt_search)

        row1.addSpacing(20)

        # Období
        period_label = QLabel("Období:")
        self.cmb_period = QComboBox()
        self.cmb_period.addItem("Dnes", "today")
        self.cmb_period.addItem("Tento týden", "week")
        self.cmb_period.addItem("Tento měsíc", "month")
        self.cmb_period.addItem("Příští měsíc", "next_month")
        self.cmb_period.addItem("Všechny", "all")
        self.cmb_period.addItem("Vlastní období", "custom")
        self.cmb_period.setCurrentIndex(2)  # Tento měsíc
        self.cmb_period.currentIndexChanged.connect(self.on_period_changed)
        row1.addWidget(period_label)
        row1.addWidget(self.cmb_period)

        # Vlastní období
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setVisible(False)
        self.date_from.dateChanged.connect(self.on_filter_changed)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setVisible(False)
        self.date_to.dateChanged.connect(self.on_filter_changed)

        row1.addWidget(QLabel("Od:"))
        row1.addWidget(self.date_from)
        row1.addWidget(QLabel("Do:"))
        row1.addWidget(self.date_to)

        row1.addStretch()

        layout.addLayout(row1)

        # Druhý řádek filtrů
        row2 = QHBoxLayout()

        # Typ události
        type_label = QLabel("Typ:")
        self.cmb_type = QComboBox()
        self.cmb_type.addItem("Všechny typy", None)
        self.cmb_type.addItem("🔧 Servisní termín", "service")
        self.cmb_type.addItem("📞 Schůzka", "meeting")
        self.cmb_type.addItem("📦 Příjem dílu", "delivery")
        self.cmb_type.addItem("🚗 Předání vozidla", "handover")
        self.cmb_type.addItem("⏰ Připomínka", "reminder")
        self.cmb_type.addItem("📅 Jiné", "other")
        self.cmb_type.currentIndexChanged.connect(self.on_filter_changed)
        row2.addWidget(type_label)
        row2.addWidget(self.cmb_type)

        # Mechanik
        mechanic_label = QLabel("Mechanik:")
        self.cmb_mechanic = QComboBox()
        self.cmb_mechanic.addItem("Všichni", None)
        self.cmb_mechanic.currentIndexChanged.connect(self.on_filter_changed)
        row2.addWidget(mechanic_label)
        row2.addWidget(self.cmb_mechanic)

        # Stav
        status_label = QLabel("Stav:")
        self.cmb_status = QComboBox()
        self.cmb_status.addItem("Všechny stavy", None)
        self.cmb_status.addItem("📅 Naplánováno", "scheduled")
        self.cmb_status.addItem("✅ Potvrzeno", "confirmed")
        self.cmb_status.addItem("🔄 Probíhá", "in_progress")
        self.cmb_status.addItem("✔️ Dokončeno", "completed")
        self.cmb_status.addItem("❌ Zrušeno", "cancelled")
        self.cmb_status.currentIndexChanged.connect(self.on_filter_changed)
        row2.addWidget(status_label)
        row2.addWidget(self.cmb_status)

        row2.addStretch()

        # Tlačítka
        self.btn_refresh = QPushButton("🔄 Obnovit")
        self.btn_refresh.clicked.connect(self.refresh)
        row2.addWidget(self.btn_refresh)

        self.btn_reset = QPushButton("🔄 Reset filtrů")
        self.btn_reset.clicked.connect(self.reset_filters)
        row2.addWidget(self.btn_reset)

        layout.addLayout(row2)

        panel.setStyleSheet(f"""
            #filtersPanel {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}
            QComboBox, QLineEdit, QDateEdit {{
                padding: 6px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }}
            QPushButton {{
                padding: 6px 12px;
            }}
        """)

        return panel

    def create_table(self):
        """Vytvoření tabulky"""
        self.table = QTableWidget()
        self.table.setObjectName("eventsTable")

        # Sloupce
        columns = [
            "ID", "Datum a čas", "Název", "Typ", "Zákazník",
            "Vozidlo", "Mechanik", "Stav", "Priorita", "Akce"
        ]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)

        # Nastavení sloupců
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Datum
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Název
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Typ
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Zákazník
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Vozidlo
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Mechanik
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Stav
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)  # Priorita
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)  # Akce

        self.table.setColumnWidth(0, 50)  # ID
        self.table.setColumnWidth(8, 80)  # Priorita
        self.table.setColumnWidth(9, 120)  # Akce

        # Skrýt ID sloupec
        self.table.setColumnHidden(0, True)

        # Vlastnosti tabulky
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.doubleClicked.connect(self.on_row_double_clicked)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)

        # Řazení
        self.table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)

        self.table.setStyleSheet(f"""
            #eventsTable {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                gridline-color: #e8e8e8;
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
            }}
            QHeaderView::section {{
                background-color: #f8f9fa;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #e0e0e0;
                font-weight: bold;
            }}
        """)

    def create_bottom_panel(self):
        """Vytvoření spodního panelu"""
        panel = QFrame()
        panel.setObjectName("bottomPanel")
        panel.setFixedHeight(60)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(15, 10, 15, 10)

        # Hromadné akce
        actions_label = QLabel("Hromadné akce:")
        layout.addWidget(actions_label)

        self.btn_delete_selected = QPushButton("🗑️ Smazat vybrané")
        self.btn_delete_selected.setEnabled(False)
        self.btn_delete_selected.clicked.connect(self.delete_selected)
        layout.addWidget(self.btn_delete_selected)

        self.btn_change_status = QPushButton("📊 Změnit stav")
        self.btn_change_status.setEnabled(False)
        self.btn_change_status.clicked.connect(self.change_selected_status)
        layout.addWidget(self.btn_change_status)

        self.btn_assign_mechanic = QPushButton("👷 Přiřadit mechanika")
        self.btn_assign_mechanic.setEnabled(False)
        self.btn_assign_mechanic.clicked.connect(self.assign_mechanic)
        layout.addWidget(self.btn_assign_mechanic)

        self.btn_export = QPushButton("📤 Export vybraných")
        self.btn_export.clicked.connect(self.export_selected)
        layout.addWidget(self.btn_export)

        layout.addStretch()

        # Statistiky
        self.lbl_total = QLabel("Celkem: 0")
        self.lbl_total.setObjectName("statLabel")
        layout.addWidget(self.lbl_total)

        self.lbl_selected = QLabel("Vybráno: 0")
        self.lbl_selected.setObjectName("statLabel")
        layout.addWidget(self.lbl_selected)

        panel.setStyleSheet(f"""
            #bottomPanel {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}
            QPushButton {{
                padding: 6px 12px;
            }}
            #statLabel {{
                color: #666;
                font-weight: bold;
                padding: 0 10px;
            }}
        """)

        return panel

    def load_filter_data(self):
        """Načtení dat pro filtry"""
        # Mechanici
        mechanics = db.fetch_all("""
            SELECT id, full_name FROM users
            WHERE role IN ('mechanik', 'admin') AND active = 1
            ORDER BY full_name
        """)

        self.cmb_mechanic.clear()
        self.cmb_mechanic.addItem("Všichni", None)
        for m in mechanics:
            self.cmb_mechanic.addItem(f"👤 {m['full_name']}", m['id'])

    def on_period_changed(self):
        """Změna období"""
        period = self.cmb_period.currentData()

        # Zobrazit/skrýt vlastní období
        is_custom = period == "custom"
        self.date_from.setVisible(is_custom)
        self.date_to.setVisible(is_custom)

        self.on_filter_changed()

    def on_filter_changed(self):
        """Změna filtrů"""
        self.refresh()

    def reset_filters(self):
        """Reset filtrů"""
        self.txt_search.clear()
        self.cmb_period.setCurrentIndex(2)  # Tento měsíc
        self.cmb_type.setCurrentIndex(0)
        self.cmb_mechanic.setCurrentIndex(0)
        self.cmb_status.setCurrentIndex(0)
        self.refresh()

    def get_date_range(self):
        """Získání rozsahu dat podle vybraného období"""
        period = self.cmb_period.currentData()
        today = date.today()

        if period == "today":
            return today, today
        elif period == "week":
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            return start, end
        elif period == "month":
            start = today.replace(day=1)
            if today.month == 12:
                end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            return start, end
        elif period == "next_month":
            if today.month == 12:
                start = today.replace(year=today.year + 1, month=1, day=1)
                end = start.replace(month=2, day=1) - timedelta(days=1)
            else:
                start = today.replace(month=today.month + 1, day=1)
                if today.month == 11:
                    end = start.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    end = start.replace(month=today.month + 2, day=1) - timedelta(days=1)
            return start, end
        elif period == "custom":
            return self.date_from.date().toPyDate(), self.date_to.date().toPyDate()
        else:  # all
            return None, None

    def refresh(self):
        """Obnovení dat v tabulce"""
        # Sestavení dotazu
        query = """
            SELECT
                e.id, e.title, e.event_type, e.start_datetime,
                e.end_datetime, e.status, e.priority, e.color,
                c.first_name || ' ' || c.last_name as customer_name,
                v.license_plate as vehicle_plate,
                u.full_name as mechanic_name
            FROM calendar_events e
            LEFT JOIN customers c ON e.customer_id = c.id
            LEFT JOIN vehicles v ON e.vehicle_id = v.id
            LEFT JOIN users u ON e.mechanic_id = u.id
            WHERE 1=1
        """
        params = []

        # Filtr období
        date_from, date_to = self.get_date_range()
        if date_from and date_to:
            query += " AND DATE(e.start_datetime) BETWEEN ? AND ?"
            params.extend([date_from.isoformat(), date_to.isoformat()])

        # Filtr typu
        event_type = self.cmb_type.currentData()
        if event_type:
            query += " AND e.event_type = ?"
            params.append(event_type)

        # Filtr mechanika
        mechanic_id = self.cmb_mechanic.currentData()
        if mechanic_id:
            query += " AND e.mechanic_id = ?"
            params.append(mechanic_id)

        # Filtr stavu
        status = self.cmb_status.currentData()
        if status:
            query += " AND e.status = ?"
            params.append(status)

        # Fulltext vyhledávání
        search_text = self.txt_search.text().strip()
        if search_text:
            query += """ AND (
                e.title LIKE ? OR
                c.first_name LIKE ? OR c.last_name LIKE ? OR
                v.license_plate LIKE ? OR
                u.full_name LIKE ?
            )"""
            search_pattern = f"%{search_text}%"
            params.extend([search_pattern] * 5)

        # Řazení
        query += " ORDER BY e.start_datetime DESC"

        # Načtení dat
        events = db.fetch_all(query, tuple(params))

        # Naplnění tabulky
        self.table.setRowCount(len(events))

        for row, event in enumerate(events):
            self.populate_row(row, event)

        # Aktualizace statistik
        self.lbl_total.setText(f"Celkem: {len(events)}")
        self.lbl_selected.setText("Vybráno: 0")

    def populate_row(self, row, event):
        """Naplnění řádku tabulky"""
        # ID (skryté)
        id_item = QTableWidgetItem(str(event['id']))
        self.table.setItem(row, 0, id_item)

        # Datum a čas
        datetime_str = ""
        if event['start_datetime']:
            try:
                dt = datetime.fromisoformat(event['start_datetime'])
                datetime_str = dt.strftime("%d.%m.%Y %H:%M")
            except:
                pass
        datetime_item = QTableWidgetItem(datetime_str)
        self.table.setItem(row, 1, datetime_item)

        # Název
        title_item = QTableWidgetItem(event['title'] or "")
        self.table.setItem(row, 2, title_item)

        # Typ
        type_icons = {
            'service': '🔧 Servis',
            'meeting': '📞 Schůzka',
            'delivery': '📦 Příjem',
            'handover': '🚗 Předání',
            'reminder': '⏰ Připomínka',
            'other': '📅 Jiné'
        }
        type_text = type_icons.get(event['event_type'], event['event_type'] or "")
        type_item = QTableWidgetItem(type_text)
        self.table.setItem(row, 3, type_item)

        # Zákazník
        customer_item = QTableWidgetItem(event['customer_name'] or "")
        self.table.setItem(row, 4, customer_item)

        # Vozidlo
        vehicle_item = QTableWidgetItem(event['vehicle_plate'] or "")
        self.table.setItem(row, 5, vehicle_item)

        # Mechanik
        mechanic_item = QTableWidgetItem(event['mechanic_name'] or "")
        self.table.setItem(row, 6, mechanic_item)

        # Stav
        status_icons = {
            'scheduled': '📅 Naplánováno',
            'confirmed': '✅ Potvrzeno',
            'in_progress': '🔄 Probíhá',
            'completed': '✔️ Dokončeno',
            'cancelled': '❌ Zrušeno'
        }
        status_text = status_icons.get(event['status'], event['status'] or "")
        status_item = QTableWidgetItem(status_text)

        # Barva pozadí podle stavu
        status_colors = {
            'scheduled': '#e3f2fd',
            'confirmed': '#e8f5e9',
            'in_progress': '#fff8e1',
            'completed': '#f1f8e9',
            'cancelled': '#ffebee'
        }
        if event['status'] in status_colors:
            status_item.setBackground(QColor(status_colors[event['status']]))

        self.table.setItem(row, 7, status_item)

        # Priorita
        priority_icons = {1: '🟢', 2: '🟡', 3: '🔴'}
        priority = event['priority'] or 2
        priority_item = QTableWidgetItem(priority_icons.get(priority, '🟡'))
        priority_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 8, priority_item)

        # Akce
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(5, 2, 5, 2)
        actions_layout.setSpacing(3)

        btn_edit = QPushButton("✏️")
        btn_edit.setFixedSize(30, 25)
        btn_edit.setToolTip("Editovat")
        btn_edit.clicked.connect(lambda checked, eid=event['id']: self.event_edit_requested.emit(eid))
        actions_layout.addWidget(btn_edit)

        btn_duplicate = QPushButton("📋")
        btn_duplicate.setFixedSize(30, 25)
        btn_duplicate.setToolTip("Duplikovat")
        btn_duplicate.clicked.connect(lambda checked, eid=event['id']: self.event_duplicate_requested.emit(eid))
        actions_layout.addWidget(btn_duplicate)

        btn_delete = QPushButton("🗑️")
        btn_delete.setFixedSize(30, 25)
        btn_delete.setToolTip("Smazat")
        btn_delete.clicked.connect(lambda checked, eid=event['id']: self.confirm_delete(eid))
        actions_layout.addWidget(btn_delete)

        self.table.setCellWidget(row, 9, actions_widget)

    def on_header_clicked(self, column):
        """Kliknutí na hlavičku - řazení"""
        if column == self.current_sort_column:
            # Změna směru
            if self.current_sort_order == Qt.SortOrder.AscendingOrder:
                self.current_sort_order = Qt.SortOrder.DescendingOrder
            else:
                self.current_sort_order = Qt.SortOrder.AscendingOrder
        else:
            self.current_sort_column = column
            self.current_sort_order = Qt.SortOrder.AscendingOrder

        self.table.sortItems(column, self.current_sort_order)

    def on_selection_changed(self):
        """Změna výběru"""
        selected_rows = self.table.selectionModel().selectedRows()
        count = len(selected_rows)

        self.lbl_selected.setText(f"Vybráno: {count}")

        # Povolit/zakázat hromadné akce
        has_selection = count > 0
        self.btn_delete_selected.setEnabled(has_selection)
        self.btn_change_status.setEnabled(has_selection)
        self.btn_assign_mechanic.setEnabled(has_selection)

    def on_row_double_clicked(self, index):
        """Dvojklik na řádek"""
        row = index.row()
        event_id = int(self.table.item(row, 0).text())
        self.event_edit_requested.emit(event_id)

    def show_context_menu(self, position):
        """Kontextové menu"""
        menu = QMenu()

        edit_action = menu.addAction("✏️ Editovat")
        duplicate_action = menu.addAction("📋 Duplikovat")
        menu.addSeparator()
        confirm_action = menu.addAction("✅ Potvrdit")
        complete_action = menu.addAction("✔️ Dokončit")
        cancel_action = menu.addAction("❌ Zrušit")
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ Smazat")

        action = menu.exec(self.table.viewport().mapToGlobal(position))

        if not action:
            return

        # Získat ID vybrané události
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        event_id = int(self.table.item(current_row, 0).text())

        if action == edit_action:
            self.event_edit_requested.emit(event_id)
        elif action == duplicate_action:
            self.event_duplicate_requested.emit(event_id)
        elif action == confirm_action:
            self.update_event_status(event_id, 'confirmed')
        elif action == complete_action:
            self.update_event_status(event_id, 'completed')
        elif action == cancel_action:
            self.update_event_status(event_id, 'cancelled')
        elif action == delete_action:
            self.confirm_delete(event_id)

    def update_event_status(self, event_id, new_status):
        """Aktualizace stavu události"""
        try:
            db.execute_query(
                "UPDATE calendar_events SET status = ?, updated_at = ? WHERE id = ?",
                (new_status, datetime.now().isoformat(), event_id)
            )
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při aktualizaci: {e}")

    def confirm_delete(self, event_id):
        """Potvrzení smazání"""
        reply = QMessageBox.question(
            self,
            "Potvrzení",
            "Opravdu chcete smazat tuto událost?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                db.execute_query("DELETE FROM calendar_events WHERE id = ?", (event_id,))
                self.refresh()
                self.event_delete_requested.emit(event_id)
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Chyba při mazání: {e}")

    def delete_selected(self):
        """Smazání vybraných událostí"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        count = len(selected_rows)
        reply = QMessageBox.question(
            self,
            "Potvrzení",
            f"Opravdu chcete smazat {count} vybraných událostí?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                for index in selected_rows:
                    event_id = int(self.table.item(index.row(), 0).text())
                    db.execute_query("DELETE FROM calendar_events WHERE id = ?", (event_id,))
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Chyba při mazání: {e}")

    def change_selected_status(self):
        """Změna stavu vybraných"""
        # TODO: Implementovat dialog pro výběr nového stavu
        QMessageBox.information(self, "Info", "Funkce bude implementována.")

    def assign_mechanic(self):
        """Přiřazení mechanika vybraným"""
        # TODO: Implementovat dialog pro výběr mechanika
        QMessageBox.information(self, "Info", "Funkce bude implementována.")

    def export_selected(self):
        """Export vybraných událostí"""
        # TODO: Implementovat export
        QMessageBox.information(self, "Export", "Funkce exportu bude implementována.")
