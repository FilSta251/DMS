# -*- coding: utf-8 -*-
"""
Modul Číselníky - Stavy zakázek (PRODUKČNÍ VERZE)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QFrame,
                             QComboBox, QLineEdit, QHeaderView, QMessageBox,
                             QDialog, QFormLayout, QCheckBox, QFileDialog,
                             QSpinBox, QTextEdit, QGroupBox, QColorDialog,
                             QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPixmap
from datetime import datetime
import csv
import json
import config
from database_manager import db


class OrderStatusesWidget(QWidget):
    """Widget pro správu stavů zakázek"""

    data_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Horní panel s akcemi
        top_panel = self.create_top_panel()
        layout.addWidget(top_panel)

        # Informační panel
        info_panel = self.create_info_panel()
        layout.addWidget(info_panel)

        # Filtr
        filter_panel = self.create_filter_panel()
        layout.addWidget(filter_panel)

        # Tabulka
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Kód", "Ikona", "Název", "Barva", "Pořadí", "Notifikace", "Aktivní", "Akce"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 80)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 60)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 100)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 70)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 80)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(7, 70)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(8, 150)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self.on_double_click)
        layout.addWidget(self.table)

        # Workflow diagram
        workflow_panel = self.create_workflow_panel()
        layout.addWidget(workflow_panel)

        # Spodní panel
        bottom_panel = self.create_bottom_panel()
        layout.addWidget(bottom_panel)

    def create_top_panel(self):
        """Vytvoření horního panelu"""
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tlačítka
        add_btn = QPushButton("➕ Přidat stav")
        add_btn.clicked.connect(self.add_status)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 4px;
            }}
        """)
        layout.addWidget(add_btn)

        import_btn = QPushButton("📥 Import CSV")
        import_btn.clicked.connect(self.import_csv)
        layout.addWidget(import_btn)

        export_btn = QPushButton("📤 Export CSV")
        export_btn.clicked.connect(self.export_csv)
        layout.addWidget(export_btn)

        reset_btn = QPushButton("🔄 Obnovit výchozí")
        reset_btn.clicked.connect(self.reset_to_default)
        layout.addWidget(reset_btn)

        layout.addStretch()

        # Vyhledávání
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Vyhledat stav...")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self.filter_data)
        layout.addWidget(self.search_input)

        return frame

    def create_info_panel(self):
        """Vytvoření informačního panelu"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #ebf5fb;
                border-radius: 4px;
                padding: 10px;
                border: 1px solid #3498db;
            }
        """)
        layout = QHBoxLayout(frame)

        info_icon = QLabel("💡")
        info_icon.setStyleSheet("font-size: 20pt;")
        layout.addWidget(info_icon)

        info_text = QLabel(
            "Stavy zakázek definují životní cyklus zakázky. Každý stav může mít\n"
            "povolené přechody do jiných stavů, barvu pro vizuální rozlišení a notifikace."
        )
        info_text.setStyleSheet("font-size: 11pt;")
        layout.addWidget(info_text)

        layout.addStretch()

        return frame

    def create_filter_panel(self):
        """Vytvoření panelu filtrů"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        layout = QHBoxLayout(frame)

        # Filtr aktivní
        layout.addWidget(QLabel("Stav:"))
        self.active_filter = QComboBox()
        self.active_filter.addItem("Všechny", "all")
        self.active_filter.addItem("✅ Aktivní", "active")
        self.active_filter.addItem("❌ Neaktivní", "inactive")
        self.active_filter.currentIndexChanged.connect(self.filter_data)
        layout.addWidget(self.active_filter)

        layout.addStretch()

        # Řazení
        layout.addWidget(QLabel("Řadit:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Podle pořadí", "sort_order")
        self.sort_combo.addItem("Podle kódu", "code")
        self.sort_combo.addItem("Podle názvu", "name")
        self.sort_combo.currentIndexChanged.connect(self.load_data)
        layout.addWidget(self.sort_combo)

        return frame

    def create_workflow_panel(self):
        """Vytvoření panelu s workflow diagramem"""
        group = QGroupBox("📊 Workflow zakázky")
        layout = QVBoxLayout(group)

        self.workflow_label = QLabel("")
        self.workflow_label.setStyleSheet("font-size: 12pt; padding: 10px;")
        self.workflow_label.setWordWrap(True)
        self.workflow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.workflow_label)

        return group

    def create_bottom_panel(self):
        """Vytvoření spodního panelu"""
        frame = QFrame()
        layout = QHBoxLayout(frame)

        self.count_label = QLabel("Celkem: 0 stavů")
        self.count_label.setStyleSheet("color: #7f8c8d; font-size: 11pt;")
        layout.addWidget(self.count_label)

        layout.addStretch()

        info_label = QLabel("💡 Dvojklik pro rychlou úpravu")
        info_label.setStyleSheet("color: #95a5a6; font-size: 10pt;")
        layout.addWidget(info_label)

        return frame

    # =====================================================
    # CRUD OPERACE
    # =====================================================

    def load_data(self):
        """Načtení dat z databáze"""
        try:
            sort_option = self.sort_combo.currentData() if hasattr(self, 'sort_combo') else "sort_order"

            order_by = "sort_order ASC"
            if sort_option == "code":
                order_by = "code ASC"
            elif sort_option == "name":
                order_by = "name ASC"

            query = f"""
                SELECT id, code, name, color, icon, sort_order, allowed_transitions,
                       notify_customer, active
                FROM codebook_order_statuses
                ORDER BY {order_by}
            """
            statuses = db.fetch_all(query)

            self.all_data = statuses
            self.filter_data()
            self.update_workflow_diagram()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst data:\n{e}")

    def filter_data(self):
        """Filtrování dat podle kritérií"""
        if not hasattr(self, 'all_data'):
            return

        filtered = self.all_data

        # Filtr podle textu
        search_text = self.search_input.text().lower().strip()
        if search_text:
            filtered = [s for s in filtered if
                       search_text in s["name"].lower() or
                       search_text in s["code"].lower()]

        # Filtr podle stavu
        active_filter = self.active_filter.currentData()
        if active_filter == "active":
            filtered = [s for s in filtered if s["active"] == 1]
        elif active_filter == "inactive":
            filtered = [s for s in filtered if s["active"] == 0]

        self.display_data(filtered)

    def display_data(self, data):
        """Zobrazení dat v tabulce"""
        self.table.setRowCount(len(data))

        for row, status in enumerate(data):
            # ID
            id_item = QTableWidgetItem(str(status["id"]))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, id_item)

            # Kód
            code_item = QTableWidgetItem(status["code"])
            code_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            code_item.setFlags(code_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            code_font = QFont()
            code_font.setBold(True)
            code_item.setFont(code_font)
            self.table.setItem(row, 1, code_item)

            # Ikona
            icon_item = QTableWidgetItem(status["icon"] or "📋")
            icon_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_item.setFlags(icon_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            icon_font = QFont()
            icon_font.setPointSize(16)
            icon_item.setFont(icon_font)
            self.table.setItem(row, 2, icon_item)

            # Název
            name_item = QTableWidgetItem(status["name"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if status["color"]:
                name_item.setForeground(QColor(status["color"]))
            self.table.setItem(row, 3, name_item)

            # Barva
            color_widget = QWidget()
            color_layout = QHBoxLayout(color_widget)
            color_layout.setContentsMargins(5, 5, 5, 5)

            color_preview = QLabel()
            color_preview.setFixedSize(20, 20)
            if status["color"]:
                pixmap = QPixmap(20, 20)
                pixmap.fill(QColor(status["color"]))
                color_preview.setPixmap(pixmap)
                color_preview.setStyleSheet("border: 1px solid #bdc3c7; border-radius: 3px;")
            color_layout.addWidget(color_preview)

            color_text = QLabel(status["color"] or "Bez barvy")
            color_text.setStyleSheet("font-size: 10pt;")
            color_layout.addWidget(color_text)

            color_layout.addStretch()
            self.table.setCellWidget(row, 4, color_widget)

            # Pořadí
            order_item = QTableWidgetItem(str(status["sort_order"]))
            order_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            order_item.setFlags(order_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 5, order_item)

            # Notifikace
            notify_item = QTableWidgetItem("📧" if status["notify_customer"] else "")
            notify_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            notify_item.setFlags(notify_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if status["notify_customer"]:
                notify_item.setToolTip("Zákazník bude notifikován při přechodu do tohoto stavu")
            self.table.setItem(row, 6, notify_item)

            # Aktivní
            active_item = QTableWidgetItem("✅" if status["active"] else "❌")
            active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            active_item.setFlags(active_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if not status["active"]:
                active_item.setForeground(QColor("#e74c3c"))
            self.table.setItem(row, 7, active_item)

            # Akce
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.setSpacing(5)

            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Upravit")
            edit_btn.setFixedSize(30, 30)
            edit_btn.clicked.connect(lambda checked, s=status: self.edit_status(s))
            actions_layout.addWidget(edit_btn)

            up_btn = QPushButton("⬆️")
            up_btn.setToolTip("Posunout nahoru")
            up_btn.setFixedSize(30, 30)
            up_btn.clicked.connect(lambda checked, s=status: self.move_up(s))
            actions_layout.addWidget(up_btn)

            down_btn = QPushButton("⬇️")
            down_btn.setToolTip("Posunout dolů")
            down_btn.setFixedSize(30, 30)
            down_btn.clicked.connect(lambda checked, s=status: self.move_down(s))
            actions_layout.addWidget(down_btn)

            delete_btn = QPushButton("🗑️")
            delete_btn.setToolTip("Smazat")
            delete_btn.setFixedSize(30, 30)
            delete_btn.clicked.connect(lambda checked, s=status: self.delete_status(s))
            actions_layout.addWidget(delete_btn)

            self.table.setCellWidget(row, 8, actions_widget)

        self.count_label.setText(f"Celkem: {len(data)} stavů")

    def update_workflow_diagram(self):
        """Aktualizace workflow diagramu"""
        if not hasattr(self, 'all_data') or not self.all_data:
            self.workflow_label.setText("Žádné stavy")
            return

        # Seřadit podle pořadí
        sorted_statuses = sorted([s for s in self.all_data if s["active"] == 1],
                                 key=lambda x: x["sort_order"])

        if not sorted_statuses:
            self.workflow_label.setText("Žádné aktivní stavy")
            return

        # Sestavit workflow
        workflow_parts = []
        for status in sorted_statuses:
            icon = status["icon"] or "📋"
            name = status["name"]
            color = status["color"] or "#000000"
            workflow_parts.append(f'<span style="color: {color}; font-weight: bold;">{icon} {name}</span>')

        workflow_text = " → ".join(workflow_parts)
        self.workflow_label.setText(workflow_text)

    def on_double_click(self, row, column):
        """Dvojklik na řádek - otevře editaci"""
        id_item = self.table.item(row, 0)
        if id_item:
            status_id = int(id_item.text())
            for status in self.all_data:
                if status["id"] == status_id:
                    self.edit_status(status)
                    break

    def add_status(self):
        """Přidání nového stavu"""
        dialog = OrderStatusDialog(self, all_statuses=self.all_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    INSERT INTO codebook_order_statuses
                    (code, name, color, icon, sort_order, allowed_transitions,
                     notify_customer, active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                db.execute_query(query, (
                    data["code"],
                    data["name"],
                    data["color"],
                    data["icon"],
                    data["sort_order"],
                    data["allowed_transitions"],
                    data["notify_customer"],
                    data["active"]
                ))

                QMessageBox.information(self, "Úspěch", f"Stav '{data['name']}' byl přidán.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    QMessageBox.warning(self, "Chyba", f"Kód '{data['code']}' již existuje.")
                else:
                    QMessageBox.critical(self, "Chyba", f"Nepodařilo se přidat stav:\n{e}")

    def edit_status(self, status):
        """Úprava stavu"""
        dialog = OrderStatusDialog(self, status, all_statuses=self.all_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    UPDATE codebook_order_statuses
                    SET code = ?, name = ?, color = ?, icon = ?, sort_order = ?,
                        allowed_transitions = ?, notify_customer = ?, active = ?
                    WHERE id = ?
                """
                db.execute_query(query, (
                    data["code"],
                    data["name"],
                    data["color"],
                    data["icon"],
                    data["sort_order"],
                    data["allowed_transitions"],
                    data["notify_customer"],
                    data["active"],
                    status["id"]
                ))

                QMessageBox.information(self, "Úspěch", "Stav byl upraven.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se upravit stav:\n{e}")

    def delete_status(self, status):
        """Smazání stavu"""
        reply = QMessageBox.question(
            self,
            "Smazat stav",
            f"Opravdu chcete smazat stav '{status['name']}'?\n\n"
            "Tato akce může narušit workflow zakázek!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = "DELETE FROM codebook_order_statuses WHERE id = ?"
                db.execute_query(query, (status["id"],))

                QMessageBox.information(self, "Úspěch", "Stav byl smazán.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat stav:\n{e}")

    def move_up(self, status):
        """Posun stavu nahoru"""
        try:
            current_order = status["sort_order"]
            if current_order <= 1:
                return

            # Najít předchozí stav
            query = """
                SELECT id, sort_order FROM codebook_order_statuses
                WHERE sort_order < ? ORDER BY sort_order DESC LIMIT 1
            """
            prev_status = db.fetch_one(query, (current_order,))

            if prev_status:
                # Vyměnit pořadí
                db.execute_query(
                    "UPDATE codebook_order_statuses SET sort_order = ? WHERE id = ?",
                    (prev_status["sort_order"], status["id"])
                )
                db.execute_query(
                    "UPDATE codebook_order_statuses SET sort_order = ? WHERE id = ?",
                    (current_order, prev_status["id"])
                )

                self.load_data()
                self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se posunout stav:\n{e}")

    def move_down(self, status):
        """Posun stavu dolů"""
        try:
            current_order = status["sort_order"]

            # Najít následující stav
            query = """
                SELECT id, sort_order FROM codebook_order_statuses
                WHERE sort_order > ? ORDER BY sort_order ASC LIMIT 1
            """
            next_status = db.fetch_one(query, (current_order,))

            if next_status:
                # Vyměnit pořadí
                db.execute_query(
                    "UPDATE codebook_order_statuses SET sort_order = ? WHERE id = ?",
                    (next_status["sort_order"], status["id"])
                )
                db.execute_query(
                    "UPDATE codebook_order_statuses SET sort_order = ? WHERE id = ?",
                    (current_order, next_status["id"])
                )

                self.load_data()
                self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se posunout stav:\n{e}")

    # =====================================================
    # IMPORT / EXPORT
    # =====================================================

    def import_csv(self):
        """Import stavů z CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importovat stavy z CSV",
            "",
            "CSV soubory (*.csv)"
        )

        if not file_path:
            return

        try:
            imported = 0
            skipped = 0

            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')

                for row in reader:
                    code = dict(row).get("code", "").strip()
                    name = dict(row).get("name", "").strip()
                    if not code or not name:
                        continue

                    # Kontrola existence
                    check_query = "SELECT id FROM codebook_order_statuses WHERE code = ?"
                    existing = db.fetch_one(check_query, (code,))

                    if existing:
                        skipped += 1
                        continue

                    color = dict(row).get("color", "").strip() or None
                    icon = dict(row).get("icon", "").strip() or "📋"
                    sort_order = int(dict(row).get("sort_order", 0))
                    allowed_transitions = dict(row).get("allowed_transitions", "").strip() or "[]"
                    notify_customer = int(dict(row).get("notify_customer", 0))
                    active = int(dict(row).get("active", 1))

                    query = """
                        INSERT INTO codebook_order_statuses
                        (code, name, color, icon, sort_order, allowed_transitions,
                         notify_customer, active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    db.execute_query(query, (
                        code, name, color, icon, sort_order,
                        allowed_transitions, notify_customer, active
                    ))
                    imported += 1

            QMessageBox.information(
                self,
                "Import dokončen",
                f"Importováno: {imported} stavů\nPřeskočeno (duplicity): {skipped}"
            )

            self.load_data()
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se importovat CSV:\n{e}")

    def export_csv(self):
        """Export stavů do CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportovat stavy do CSV",
            f"stavy_zakazek_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV soubory (*.csv)"
        )

        if not file_path:
            return

        try:
            query = """
                SELECT code, name, color, icon, sort_order, allowed_transitions,
                       notify_customer, active
                FROM codebook_order_statuses
                ORDER BY sort_order
            """
            statuses = db.fetch_all(query)

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["code", "name", "color", "icon", "sort_order",
                               "allowed_transitions", "notify_customer", "active"],
                    delimiter=';'
                )
                writer.writeheader()

                for status in statuses:
                    writer.writerow({
                        "code": status["code"],
                        "name": status["name"],
                        "color": status["color"] or "",
                        "icon": status["icon"] or "",
                        "sort_order": status["sort_order"],
                        "allowed_transitions": status["allowed_transitions"] or "[]",
                        "notify_customer": status["notify_customer"],
                        "active": status["active"]
                    })

            QMessageBox.information(
                self,
                "Export dokončen",
                f"Exportováno {len(statuses)} stavů do:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se exportovat CSV:\n{e}")

    def reset_to_default(self):
        """Obnovení výchozích stavů"""
        reply = QMessageBox.question(
            self,
            "Obnovit výchozí stavy zakázek",
            "Opravdu chcete obnovit výchozí stavy?\n\n"
            "Budou přidány chybějící stavy, existující zůstanou.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            default_statuses = [
                ("PREP", "V přípravě", "#95a5a6", "📝", 10, '["INPROG"]', 0),
                ("INPROG", "V práci", "#3498db", "🔧", 20, '["WAIT", "DONE"]', 1),
                ("WAIT", "Čeká na díly", "#f39c12", "⏳", 30, '["INPROG"]', 1),
                ("DONE", "Dokončeno", "#27ae60", "✅", 40, '["INV"]', 1),
                ("INV", "Fakturováno", "#9b59b6", "📄", 50, '["PAID"]', 0),
                ("PAID", "Zaplaceno", "#2ecc71", "💰", 60, '[]', 0),
                ("CANCEL", "Zrušeno", "#e74c3c", "❌", 100, '[]', 0),
            ]

            added = 0
            for code, name, color, icon, sort_order, transitions, notify in default_statuses:
                check_query = "SELECT id FROM codebook_order_statuses WHERE code = ?"
                existing = db.fetch_one(check_query, (code,))

                if not existing:
                    query = """
                        INSERT INTO codebook_order_statuses
                        (code, name, color, icon, sort_order, allowed_transitions,
                         notify_customer, active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    """
                    db.execute_query(query, (code, name, color, icon, sort_order, transitions, notify))
                    added += 1

            QMessageBox.information(
                self,
                "Dokončeno",
                f"Přidáno {added} výchozích stavů."
            )

            self.load_data()
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se obnovit výchozí stavy:\n{e}")

    # =====================================================
    # POMOCNÉ METODY
    # =====================================================

    def get_count(self):
        """Vrátí počet položek"""
        try:
            query = "SELECT COUNT(*) as count FROM codebook_order_statuses"
            result = db.fetch_one(query)
            return result["count"] if result else 0
        except:
            return 0

    def export_data(self):
        """Export dat pro zálohu"""
        try:
            query = """
                SELECT code, name, color, icon, sort_order, allowed_transitions,
                       notify_customer, active
                FROM codebook_order_statuses
            """
            return db.fetch_all(query)
        except:
            return []

    def import_data(self, data):
        """Import dat ze zálohy"""
        try:
            for item in data:
                check_query = "SELECT id FROM codebook_order_statuses WHERE code = ?"
                existing = db.fetch_one(check_query, (item["code"],))

                if existing:
                    query = """
                        UPDATE codebook_order_statuses
                        SET name = ?, color = ?, icon = ?, sort_order = ?,
                            allowed_transitions = ?, notify_customer = ?, active = ?
                        WHERE code = ?
                    """
                    db.execute_query(query, (
                        item["name"],
                        item.get("color"),
                        item.get("icon", "📋"),
                        item["sort_order"],
                        item.get("allowed_transitions", "[]"),
                        item["notify_customer"],
                        item["active"],
                        item["code"]
                    ))
                else:
                    query = """
                        INSERT INTO codebook_order_statuses
                        (code, name, color, icon, sort_order, allowed_transitions,
                         notify_customer, active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    db.execute_query(query, (
                        item["code"],
                        item["name"],
                        item.get("color"),
                        item.get("icon", "📋"),
                        item["sort_order"],
                        item.get("allowed_transitions", "[]"),
                        item["notify_customer"],
                        item["active"]
                    ))

            self.load_data()

        except Exception as e:
            print(f"Chyba při importu dat: {e}")

    def refresh(self):
        """Obnovení dat"""
        self.load_data()


# =====================================================
# DIALOG PRO STAV ZAKÁZKY
# =====================================================

class OrderStatusDialog(QDialog):
    """Dialog pro přidání/úpravu stavu zakázky"""

    def __init__(self, parent, status=None, all_statuses=None):
        super().__init__(parent)
        self.status = status
        self.all_statuses = all_statuses or []
        self.selected_color = "#3498db"
        self.setWindowTitle("Upravit stav" if status else "Nový stav zakázky")
        self.setMinimumWidth(550)
        self.init_ui()

        if status:
            self.load_status_data()

    def init_ui(self):
        """Inicializace UI"""
        layout = QFormLayout(self)

        # Kód
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Např: PREP, INPROG, DONE...")
        self.code_input.setMaxLength(20)
        layout.addRow("Kód:", self.code_input)

        # Název
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Např: V přípravě, V práci, Dokončeno...")
        layout.addRow("Název:", self.name_input)

        # Ikona
        icon_group = QGroupBox("Ikona")
        icon_layout = QHBoxLayout(icon_group)

        self.icon_input = QLineEdit()
        self.icon_input.setMaxLength(5)
        self.icon_input.setFixedWidth(60)
        self.icon_input.setText("📋")
        self.icon_input.setStyleSheet("font-size: 20pt;")
        icon_layout.addWidget(self.icon_input)

        # Rychlé ikony
        quick_icons = ["📝", "🔧", "⏳", "✅", "📄", "💰", "❌", "🚗", "⚙️", "📦"]
        for icon in quick_icons:
            btn = QPushButton(icon)
            btn.setFixedSize(35, 35)
            btn.clicked.connect(lambda checked, i=icon: self.icon_input.setText(i))
            icon_layout.addWidget(btn)

        icon_layout.addStretch()
        layout.addRow(icon_group)

        # Barva
        color_group = QGroupBox("Barva pro vizuální rozlišení")
        color_layout = QHBoxLayout(color_group)

        self.color_preview = QLabel()
        self.color_preview.setFixedSize(30, 30)
        self.update_color_preview()
        color_layout.addWidget(self.color_preview)

        color_btn = QPushButton("Vybrat barvu...")
        color_btn.clicked.connect(self.choose_color)
        color_layout.addWidget(color_btn)

        # Rychlé barvy
        quick_colors = [
            ("#95a5a6", "Šedá"),
            ("#3498db", "Modrá"),
            ("#f39c12", "Oranžová"),
            ("#27ae60", "Zelená"),
            ("#e74c3c", "Červená"),
            ("#9b59b6", "Fialová"),
        ]
        for color, name in quick_colors:
            btn = QPushButton()
            btn.setFixedSize(25, 25)
            btn.setStyleSheet(f"background-color: {color}; border-radius: 3px;")
            btn.setToolTip(name)
            btn.clicked.connect(lambda checked, c=color: self.set_color(c))
            color_layout.addWidget(btn)

        color_layout.addStretch()
        layout.addRow(color_group)

        # Pořadí
        self.sort_order_input = QSpinBox()
        self.sort_order_input.setRange(1, 999)
        self.sort_order_input.setValue(10)
        layout.addRow("Pořadí ve workflow:", self.sort_order_input)

        # Povolené přechody
        transitions_group = QGroupBox("Povolené přechody do jiných stavů")
        transitions_layout = QVBoxLayout(transitions_group)

        self.transitions_list = QListWidget()
        self.transitions_list.setMaximumHeight(150)

        # Naplnit seznamem dostupných stavů
        for s in self.all_statuses:
            if self.status is None or s["code"] != self.status["code"]:
                item = QListWidgetItem(f"{s['icon']} {s['name']} ({s['code']})")
                item.setData(Qt.ItemDataRole.UserRole, s["code"])
                item.setCheckState(Qt.CheckState.Unchecked)
                self.transitions_list.addItem(item)

        transitions_layout.addWidget(self.transitions_list)

        transitions_info = QLabel(
            "Vyberte stavy, do kterých je možné přejít z tohoto stavu."
        )
        transitions_info.setStyleSheet("color: #7f8c8d; font-size: 9pt;")
        transitions_layout.addWidget(transitions_info)

        layout.addRow(transitions_group)

        # Notifikace
        self.notify_checkbox = QCheckBox("Notifikovat zákazníka při přechodu do tohoto stavu")
        layout.addRow("", self.notify_checkbox)

        # Aktivní
        self.active_checkbox = QCheckBox("Aktivní (dostupný pro výběr)")
        self.active_checkbox.setChecked(True)
        layout.addRow("", self.active_checkbox)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        if self.status:
            delete_btn = QPushButton("🗑️ Smazat")
            delete_btn.clicked.connect(self.delete_status)
            delete_btn.setStyleSheet(f"background-color: {config.COLOR_DANGER}; color: white; padding: 8px 20px;")
            buttons_layout.addWidget(delete_btn)

        save_btn = QPushButton("💾 Uložit")
        save_btn.clicked.connect(self.save)
        save_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 20px;")
        buttons_layout.addWidget(save_btn)

        layout.addRow(buttons_layout)

    def update_color_preview(self):
        """Aktualizace náhledu barvy"""
        pixmap = QPixmap(30, 30)
        pixmap.fill(QColor(self.selected_color))
        self.color_preview.setPixmap(pixmap)
        self.color_preview.setStyleSheet("border: 2px solid #bdc3c7; border-radius: 4px;")

    def choose_color(self):
        """Výběr barvy"""
        color = QColorDialog.getColor(QColor(self.selected_color), self, "Vyberte barvu stavu")
        if color.isValid():
            self.selected_color = color.name()
            self.update_color_preview()

    def set_color(self, color):
        """Nastavení barvy"""
        self.selected_color = color
        self.update_color_preview()

    def load_status_data(self):
        """Načtení dat stavu"""
        self.code_input.setText(self.status["code"])
        self.name_input.setText(self.status["name"])
        self.icon_input.setText(self.status["icon"] or "📋")

        if self.status["color"]:
            self.selected_color = self.status["color"]
            self.update_color_preview()

        self.sort_order_input.setValue(self.status["sort_order"])

        # Povolené přechody
        try:
            allowed = json.loads(self.status["allowed_transitions"] or "[]")
            for i in range(self.transitions_list.count()):
                item = self.transitions_list.item(i)
                code = item.data(Qt.ItemDataRole.UserRole)
                if code in allowed:
                    item.setCheckState(Qt.CheckState.Checked)
        except:
            pass

        self.notify_checkbox.setChecked(self.status["notify_customer"] == 1)
        self.active_checkbox.setChecked(self.status["active"] == 1)

    def delete_status(self):
        """Smazání stavu z dialogu"""
        if self.status:
            self.parent().delete_status(self.status)
            self.reject()

    def save(self):
        """Uložení stavu"""
        code = self.code_input.text().strip()
        name = self.name_input.text().strip()

        if not code:
            QMessageBox.warning(self, "Chyba", "Vyplňte kód stavu.")
            return

        if not name:
            QMessageBox.warning(self, "Chyba", "Vyplňte název stavu.")
            return

        self.accept()

    def get_data(self):
        """Vrácení dat"""
        # Získat povolené přechody
        allowed_transitions = []
        for i in range(self.transitions_list.count()):
            item = self.transitions_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                allowed_transitions.append(item.data(Qt.ItemDataRole.UserRole))

        return {
            "code": self.code_input.text().strip().upper(),
            "name": self.name_input.text().strip(),
            "color": self.selected_color,
            "icon": self.icon_input.text().strip() or "📋",
            "sort_order": self.sort_order_input.value(),
            "allowed_transitions": json.dumps(allowed_transitions),
            "notify_customer": 1 if self.notify_checkbox.isChecked() else 0,
            "active": 1 if self.active_checkbox.isChecked() else 0
        }
