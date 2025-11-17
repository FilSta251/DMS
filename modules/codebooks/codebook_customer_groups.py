# -*- coding: utf-8 -*-
"""
Modul Číselníky - Zákaznické skupiny (PRODUKČNÍ VERZE)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QFrame,
                             QComboBox, QLineEdit, QHeaderView, QMessageBox,
                             QDialog, QFormLayout, QCheckBox, QFileDialog,
                             QDoubleSpinBox, QSpinBox, QTextEdit, QGroupBox,
                             QColorDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPixmap, QPainter
from datetime import datetime
import csv
import config
from database_manager import db


class CustomerGroupsWidget(QWidget):
    """Widget pro správu zákaznických skupin"""

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
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Kód", "Název", "Sleva práce", "Sleva materiál",
            "Splatnost", "Kredit. limit", "Priorita", "Aktivní", "Akce"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 80)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 90)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 100)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 80)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 100)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(7, 80)
        self.table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(8, 70)
        self.table.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(9, 150)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self.on_double_click)
        layout.addWidget(self.table)

        # Spodní panel
        bottom_panel = self.create_bottom_panel()
        layout.addWidget(bottom_panel)

    def create_top_panel(self):
        """Vytvoření horního panelu"""
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tlačítka
        add_btn = QPushButton("➕ Přidat skupinu")
        add_btn.clicked.connect(self.add_group)
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
        self.search_input.setPlaceholderText("🔍 Vyhledat skupinu...")
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
            "Zákaznické skupiny umožňují automaticky aplikovat slevy a speciální podmínky.\n"
            "Každý zákazník může být přiřazen k jedné skupině."
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
        self.sort_combo.addItem("Podle priority", "priority")
        self.sort_combo.addItem("Podle kódu", "code")
        self.sort_combo.addItem("Podle názvu", "name")
        self.sort_combo.addItem("Podle slevy", "discount")
        self.sort_combo.currentIndexChanged.connect(self.load_data)
        layout.addWidget(self.sort_combo)

        return frame

    def create_bottom_panel(self):
        """Vytvoření spodního panelu"""
        frame = QFrame()
        layout = QHBoxLayout(frame)

        self.count_label = QLabel("Celkem: 0 skupin")
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
            sort_option = self.sort_combo.currentData() if hasattr(self, 'sort_combo') else "priority"

            order_by = "priority DESC, name ASC"
            if sort_option == "code":
                order_by = "code ASC"
            elif sort_option == "name":
                order_by = "name ASC"
            elif sort_option == "discount":
                order_by = "discount_work DESC, discount_material DESC"

            query = f"""
                SELECT id, code, name, discount_work, discount_material,
                       payment_terms, credit_limit, priority, color, description, active
                FROM codebook_customer_groups
                ORDER BY {order_by}
            """
            groups = db.fetch_all(query)

            self.all_data = groups
            self.filter_data()

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
            filtered = [g for g in filtered if
                       search_text in g["name"].lower() or
                       search_text in g["code"].lower() or
                       search_text in (g["description"] or "").lower()]

        # Filtr podle stavu
        active_filter = self.active_filter.currentData()
        if active_filter == "active":
            filtered = [g for g in filtered if g["active"] == 1]
        elif active_filter == "inactive":
            filtered = [g for g in filtered if g["active"] == 0]

        self.display_data(filtered)

    def display_data(self, data):
        """Zobrazení dat v tabulce"""
        self.table.setRowCount(len(data))

        for row, group in enumerate(data):
            # ID
            id_item = QTableWidgetItem(str(group["id"]))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, id_item)

            # Kód s barvou
            code_item = QTableWidgetItem(group["code"])
            code_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            code_item.setFlags(code_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            code_font = QFont()
            code_font.setBold(True)
            code_item.setFont(code_font)
            if group["color"]:
                code_item.setForeground(QColor(group["color"]))
            self.table.setItem(row, 1, code_item)

            # Název
            name_item = QTableWidgetItem(group["name"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if group["description"]:
                name_item.setToolTip(group["description"])
            if group["color"]:
                name_item.setForeground(QColor(group["color"]))
            self.table.setItem(row, 2, name_item)

            # Sleva práce
            discount_work_text = f"{group['discount_work']:.0f}%"
            discount_work_item = QTableWidgetItem(discount_work_text)
            discount_work_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            discount_work_item.setFlags(discount_work_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if group['discount_work'] > 0:
                discount_work_item.setForeground(QColor("#27ae60"))
            self.table.setItem(row, 3, discount_work_item)

            # Sleva materiál
            discount_mat_text = f"{group['discount_material']:.0f}%"
            discount_mat_item = QTableWidgetItem(discount_mat_text)
            discount_mat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            discount_mat_item.setFlags(discount_mat_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if group['discount_material'] > 0:
                discount_mat_item.setForeground(QColor("#27ae60"))
            self.table.setItem(row, 4, discount_mat_item)

            # Splatnost
            payment_text = f"{group['payment_terms']} dní"
            payment_item = QTableWidgetItem(payment_text)
            payment_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            payment_item.setFlags(payment_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 5, payment_item)

            # Kreditní limit
            if group['credit_limit'] > 0:
                limit_text = f"{group['credit_limit']:,.0f} Kč".replace(",", " ")
            else:
                limit_text = "Bez limitu"
            limit_item = QTableWidgetItem(limit_text)
            limit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            limit_item.setFlags(limit_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 6, limit_item)

            # Priorita
            priority = group["priority"]
            priority_stars = "⭐" * priority
            priority_item = QTableWidgetItem(priority_stars)
            priority_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            priority_item.setFlags(priority_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 7, priority_item)

            # Aktivní
            active_item = QTableWidgetItem("✅" if group["active"] else "❌")
            active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            active_item.setFlags(active_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if not group["active"]:
                active_item.setForeground(QColor("#e74c3c"))
            self.table.setItem(row, 8, active_item)

            # Akce
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.setSpacing(5)

            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Upravit")
            edit_btn.setFixedSize(30, 30)
            edit_btn.clicked.connect(lambda checked, g=group: self.edit_group(g))
            actions_layout.addWidget(edit_btn)

            customers_btn = QPushButton("👥")
            customers_btn.setToolTip("Zobrazit zákazníky")
            customers_btn.setFixedSize(30, 30)
            customers_btn.clicked.connect(lambda checked, g=group: self.show_customers(g))
            actions_layout.addWidget(customers_btn)

            toggle_btn = QPushButton("🔄")
            toggle_btn.setToolTip("Aktivovat/Deaktivovat")
            toggle_btn.setFixedSize(30, 30)
            toggle_btn.clicked.connect(lambda checked, g=group: self.toggle_active(g))
            actions_layout.addWidget(toggle_btn)

            delete_btn = QPushButton("🗑️")
            delete_btn.setToolTip("Smazat")
            delete_btn.setFixedSize(30, 30)
            delete_btn.clicked.connect(lambda checked, g=group: self.delete_group(g))
            actions_layout.addWidget(delete_btn)

            self.table.setCellWidget(row, 9, actions_widget)

        self.count_label.setText(f"Celkem: {len(data)} skupin")

    def on_double_click(self, row, column):
        """Dvojklik na řádek - otevře editaci"""
        id_item = self.table.item(row, 0)
        if id_item:
            group_id = int(id_item.text())
            for group in self.all_data:
                if group["id"] == group_id:
                    self.edit_group(group)
                    break

    def add_group(self):
        """Přidání nové skupiny"""
        dialog = CustomerGroupDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    INSERT INTO codebook_customer_groups
                    (code, name, discount_work, discount_material, payment_terms,
                     credit_limit, priority, color, description, active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                db.execute_query(query, (
                    data["code"],
                    data["name"],
                    data["discount_work"],
                    data["discount_material"],
                    data["payment_terms"],
                    data["credit_limit"],
                    data["priority"],
                    data["color"],
                    data["description"],
                    data["active"]
                ))

                QMessageBox.information(self, "Úspěch", f"Skupina '{data['name']}' byla přidána.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    QMessageBox.warning(self, "Chyba", f"Kód '{data['code']}' již existuje.")
                else:
                    QMessageBox.critical(self, "Chyba", f"Nepodařilo se přidat skupinu:\n{e}")

    def edit_group(self, group):
        """Úprava skupiny"""
        dialog = CustomerGroupDialog(self, group)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            try:
                query = """
                    UPDATE codebook_customer_groups
                    SET code = ?, name = ?, discount_work = ?, discount_material = ?,
                        payment_terms = ?, credit_limit = ?, priority = ?, color = ?,
                        description = ?, active = ?
                    WHERE id = ?
                """
                db.execute_query(query, (
                    data["code"],
                    data["name"],
                    data["discount_work"],
                    data["discount_material"],
                    data["payment_terms"],
                    data["credit_limit"],
                    data["priority"],
                    data["color"],
                    data["description"],
                    data["active"],
                    group["id"]
                ))

                QMessageBox.information(self, "Úspěch", "Skupina byla upravena.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se upravit skupinu:\n{e}")

    def delete_group(self, group):
        """Smazání skupiny"""
        # Kontrola použití - závisí na struktuře customers tabulky
        # Předpokládáme sloupec customer_group_id nebo podobný
        try:
            query = "SELECT COUNT(*) as count FROM customers WHERE customer_group_id = ?"
            result = db.fetch_one(query, (group["id"],))
            usage_count = result["count"] if result else 0
        except:
            usage_count = 0

        if usage_count > 0:
            QMessageBox.warning(
                self,
                "Nelze smazat",
                f"Skupina '{group['name']}' je přiřazena {usage_count} zákazníkům.\n\n"
                "Místo smazání ji můžete deaktivovat."
            )
            return

        reply = QMessageBox.question(
            self,
            "Smazat skupinu",
            f"Opravdu chcete smazat skupinu '{group['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = "DELETE FROM codebook_customer_groups WHERE id = ?"
                db.execute_query(query, (group["id"],))

                QMessageBox.information(self, "Úspěch", "Skupina byla smazána.")
                self.load_data()
                self.data_changed.emit()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat skupinu:\n{e}")

    def toggle_active(self, group):
        """Přepnutí aktivního stavu"""
        try:
            new_state = 0 if group["active"] else 1
            query = "UPDATE codebook_customer_groups SET active = ? WHERE id = ?"
            db.execute_query(query, (new_state, group["id"]))

            self.load_data()
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se změnit stav:\n{e}")

    def show_customers(self, group):
        """Zobrazení zákazníků ve skupině"""
        try:
            query = """
                SELECT first_name, last_name, company
                FROM customers
                WHERE customer_group_id = ?
                ORDER BY last_name, first_name
            """
            customers = db.fetch_all(query, (group["id"],))

            if not customers:
                QMessageBox.information(
                    self,
                    f"Zákazníci - {group['name']}",
                    "Žádní zákazníci nejsou přiřazeni k této skupině."
                )
                return

            customer_list = []
            for c in customers[:20]:  # Max 20 zobrazených
                if c["company"]:
                    customer_list.append(f"• {c['company']} ({c['first_name']} {c['last_name']})")
                else:
                    customer_list.append(f"• {c['first_name']} {c['last_name']}")

            text = "\n".join(customer_list)
            if len(customers) > 20:
                text += f"\n\n... a dalších {len(customers) - 20} zákazníků"

            QMessageBox.information(
                self,
                f"Zákazníci - {group['name']}",
                f"Počet zákazníků: {len(customers)}\n\n{text}"
            )

        except Exception as e:
            QMessageBox.information(
                self,
                f"Zákazníci - {group['name']}",
                "Nepodařilo se načíst zákazníky.\n\n"
                "Možná není v tabulce customers sloupec customer_group_id."
            )

    # =====================================================
    # IMPORT / EXPORT
    # =====================================================

    def import_csv(self):
        """Import skupin z CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importovat skupiny z CSV",
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
                    check_query = "SELECT id FROM codebook_customer_groups WHERE code = ?"
                    existing = db.fetch_one(check_query, (code,))

                    if existing:
                        skipped += 1
                        continue

                    discount_work = float(dict(row).get("discount_work", 0))
                    discount_material = float(dict(row).get("discount_material", 0))
                    payment_terms = int(dict(row).get("payment_terms", 14))
                    credit_limit = float(dict(row).get("credit_limit", 0))
                    priority = int(dict(row).get("priority", 1))
                    color = dict(row).get("color", "").strip() or None
                    description = dict(row).get("description", "").strip()
                    active = int(dict(row).get("active", 1))

                    query = """
                        INSERT INTO codebook_customer_groups
                        (code, name, discount_work, discount_material, payment_terms,
                         credit_limit, priority, color, description, active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    db.execute_query(query, (
                        code, name, discount_work, discount_material, payment_terms,
                        credit_limit, priority, color, description, active
                    ))
                    imported += 1

            QMessageBox.information(
                self,
                "Import dokončen",
                f"Importováno: {imported} skupin\nPřeskočeno (duplicity): {skipped}"
            )

            self.load_data()
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se importovat CSV:\n{e}")

    def export_csv(self):
        """Export skupin do CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportovat skupiny do CSV",
            f"zakaznicke_skupiny_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV soubory (*.csv)"
        )

        if not file_path:
            return

        try:
            query = """
                SELECT code, name, discount_work, discount_material, payment_terms,
                       credit_limit, priority, color, description, active
                FROM codebook_customer_groups
                ORDER BY priority DESC, name
            """
            groups = db.fetch_all(query)

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["code", "name", "discount_work", "discount_material",
                               "payment_terms", "credit_limit", "priority", "color",
                               "description", "active"],
                    delimiter=';'
                )
                writer.writeheader()

                for grp in groups:
                    writer.writerow({
                        "code": grp["code"],
                        "name": grp["name"],
                        "discount_work": grp["discount_work"],
                        "discount_material": grp["discount_material"],
                        "payment_terms": grp["payment_terms"],
                        "credit_limit": grp["credit_limit"],
                        "priority": grp["priority"],
                        "color": grp["color"] or "",
                        "description": grp["description"] or "",
                        "active": grp["active"]
                    })

            QMessageBox.information(
                self,
                "Export dokončen",
                f"Exportováno {len(groups)} skupin do:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se exportovat CSV:\n{e}")

    def reset_to_default(self):
        """Obnovení výchozích skupin"""
        reply = QMessageBox.question(
            self,
            "Obnovit výchozí skupiny",
            "Opravdu chcete obnovit výchozí zákaznické skupiny?\n\n"
            "Budou přidány chybějící skupiny, existující zůstanou.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            default_groups = [
                ("STD", "Standardní zákazník", 0, 0, 14, 0, 1, "#7f8c8d", "Běžný zákazník bez speciálních podmínek"),
                ("VERNY", "Věrný zákazník", 5, 3, 14, 0, 2, "#27ae60", "Zákazník s historií - sleva za věrnost"),
                ("VIP", "VIP zákazník", 10, 5, 30, 50000, 3, "#f39c12", "Prémiový zákazník s rozšířenými výhodami"),
                ("FIREMNI", "Firemní zákazník", 15, 10, 45, 100000, 4, "#3498db", "Firemní zákazník s fakturací"),
                ("POJIST", "Pojišťovna", 0, 0, 60, 500000, 5, "#9b59b6", "Pojišťovna - speciální ceník"),
                ("ZAMEST", "Zaměstnanec", 20, 15, 30, 20000, 3, "#e74c3c", "Zaměstnanec firmy - zvýhodněné ceny"),
            ]

            added = 0
            for code, name, disc_work, disc_mat, terms, limit, priority, color, desc in default_groups:
                check_query = "SELECT id FROM codebook_customer_groups WHERE code = ?"
                existing = db.fetch_one(check_query, (code,))

                if not existing:
                    query = """
                        INSERT INTO codebook_customer_groups
                        (code, name, discount_work, discount_material, payment_terms,
                         credit_limit, priority, color, description, active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """
                    db.execute_query(query, (code, name, disc_work, disc_mat, terms, limit, priority, color, desc))
                    added += 1

            QMessageBox.information(
                self,
                "Dokončeno",
                f"Přidáno {added} výchozích skupin."
            )

            self.load_data()
            self.data_changed.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se obnovit výchozí skupiny:\n{e}")

    # =====================================================
    # POMOCNÉ METODY
    # =====================================================

    def get_count(self):
        """Vrátí počet položek"""
        try:
            query = "SELECT COUNT(*) as count FROM codebook_customer_groups"
            result = db.fetch_one(query)
            return result["count"] if result else 0
        except:
            return 0

    def export_data(self):
        """Export dat pro zálohu"""
        try:
            query = """
                SELECT code, name, discount_work, discount_material, payment_terms,
                       credit_limit, priority, color, description, active
                FROM codebook_customer_groups
            """
            return db.fetch_all(query)
        except:
            return []

    def import_data(self, data):
        """Import dat ze zálohy"""
        try:
            for item in data:
                check_query = "SELECT id FROM codebook_customer_groups WHERE code = ?"
                existing = db.fetch_one(check_query, (item["code"],))

                if existing:
                    query = """
                        UPDATE codebook_customer_groups
                        SET name = ?, discount_work = ?, discount_material = ?,
                            payment_terms = ?, credit_limit = ?, priority = ?,
                            color = ?, description = ?, active = ?
                        WHERE code = ?
                    """
                    db.execute_query(query, (
                        item["name"],
                        item["discount_work"],
                        item["discount_material"],
                        item["payment_terms"],
                        item["credit_limit"],
                        item["priority"],
                        item.get("color"),
                        item.get("description", ""),
                        item["active"],
                        item["code"]
                    ))
                else:
                    query = """
                        INSERT INTO codebook_customer_groups
                        (code, name, discount_work, discount_material, payment_terms,
                         credit_limit, priority, color, description, active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    db.execute_query(query, (
                        item["code"],
                        item["name"],
                        item["discount_work"],
                        item["discount_material"],
                        item["payment_terms"],
                        item["credit_limit"],
                        item["priority"],
                        item.get("color"),
                        item.get("description", ""),
                        item["active"]
                    ))

            self.load_data()

        except Exception as e:
            print(f"Chyba při importu dat: {e}")

    def refresh(self):
        """Obnovení dat"""
        self.load_data()


# =====================================================
# DIALOG PRO ZÁKAZNICKOU SKUPINU
# =====================================================

class CustomerGroupDialog(QDialog):
    """Dialog pro přidání/úpravu zákaznické skupiny"""

    def __init__(self, parent, group=None):
        super().__init__(parent)
        self.group = group
        self.selected_color = "#3498db"
        self.setWindowTitle("Upravit skupinu" if group else "Nová zákaznická skupina")
        self.setMinimumWidth(550)
        self.init_ui()

        if group:
            self.load_group_data()

    def init_ui(self):
        """Inicializace UI"""
        layout = QFormLayout(self)

        # Kód
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Např: VIP, FIREMNI, STD...")
        self.code_input.setMaxLength(20)
        layout.addRow("Kód:", self.code_input)

        # Název
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Např: VIP zákazník, Firemní zákazník...")
        layout.addRow("Název:", self.name_input)

        # Slevy
        discounts_group = QGroupBox("Slevy")
        discounts_layout = QFormLayout(discounts_group)

        self.discount_work_input = QDoubleSpinBox()
        self.discount_work_input.setRange(0, 100)
        self.discount_work_input.setDecimals(1)
        self.discount_work_input.setSuffix(" %")
        self.discount_work_input.setValue(0)
        discounts_layout.addRow("Sleva na práci:", self.discount_work_input)

        self.discount_material_input = QDoubleSpinBox()
        self.discount_material_input.setRange(0, 100)
        self.discount_material_input.setDecimals(1)
        self.discount_material_input.setSuffix(" %")
        self.discount_material_input.setValue(0)
        discounts_layout.addRow("Sleva na materiál:", self.discount_material_input)

        layout.addRow(discounts_group)

        # Podmínky
        terms_group = QGroupBox("Platební podmínky")
        terms_layout = QFormLayout(terms_group)

        self.payment_terms_input = QSpinBox()
        self.payment_terms_input.setRange(0, 365)
        self.payment_terms_input.setSuffix(" dní")
        self.payment_terms_input.setValue(14)
        terms_layout.addRow("Splatnost faktur:", self.payment_terms_input)

        self.credit_limit_input = QDoubleSpinBox()
        self.credit_limit_input.setRange(0, 99999999)
        self.credit_limit_input.setDecimals(0)
        self.credit_limit_input.setSuffix(" Kč")
        self.credit_limit_input.setValue(0)
        self.credit_limit_input.setSpecialValueText("Bez limitu")
        terms_layout.addRow("Kreditní limit:", self.credit_limit_input)

        layout.addRow(terms_group)

        # Priorita
        priority_group = QGroupBox("Priorita zákazníka")
        priority_layout = QVBoxLayout(priority_group)

        self.priority_input = QSpinBox()
        self.priority_input.setRange(1, 5)
        self.priority_input.setValue(1)
        self.priority_input.valueChanged.connect(self.update_priority_label)
        priority_layout.addWidget(self.priority_input)

        self.priority_label = QLabel("⭐ Level 1 - Základní priorita")
        self.priority_label.setStyleSheet("font-weight: bold;")
        priority_layout.addWidget(self.priority_label)

        priority_info = QLabel(
            "Vyšší priorita = důležitější zákazník.\n"
            "Zákazníci s vyšší prioritou mohou mít přednost v obsluze."
        )
        priority_info.setStyleSheet("color: #7f8c8d; font-size: 9pt;")
        priority_layout.addWidget(priority_info)

        layout.addRow(priority_group)

        # Barva
        color_layout = QHBoxLayout()
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(30, 30)
        self.update_color_preview()
        color_layout.addWidget(self.color_preview)

        color_btn = QPushButton("Vybrat barvu...")
        color_btn.clicked.connect(self.choose_color)
        color_layout.addWidget(color_btn)

        color_layout.addStretch()
        layout.addRow("Barva:", color_layout)

        # Popis
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("Popis skupiny a podmínek...")
        layout.addRow("Popis:", self.description_input)

        # Aktivní
        self.active_checkbox = QCheckBox("Aktivní (dostupná pro přiřazení)")
        self.active_checkbox.setChecked(True)
        layout.addRow("", self.active_checkbox)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        if self.group:
            delete_btn = QPushButton("🗑️ Smazat")
            delete_btn.clicked.connect(self.delete_group)
            delete_btn.setStyleSheet(f"background-color: {config.COLOR_DANGER}; color: white; padding: 8px 20px;")
            buttons_layout.addWidget(delete_btn)

        save_btn = QPushButton("💾 Uložit")
        save_btn.clicked.connect(self.save)
        save_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 20px;")
        buttons_layout.addWidget(save_btn)

        layout.addRow(buttons_layout)

    def update_priority_label(self):
        """Aktualizace popisku priority"""
        level = self.priority_input.value()
        stars = "⭐" * level

        level_descriptions = {
            1: "Základní priorita",
            2: "Mírně zvýšená priorita",
            3: "Střední priorita",
            4: "Vysoká priorita",
            5: "Nejvyšší priorita"
        }

        self.priority_label.setText(f"{stars} Level {level} - {level_descriptions[level]}")

    def update_color_preview(self):
        """Aktualizace náhledu barvy"""
        pixmap = QPixmap(30, 30)
        pixmap.fill(QColor(self.selected_color))
        self.color_preview.setPixmap(pixmap)
        self.color_preview.setStyleSheet(f"border: 2px solid #bdc3c7; border-radius: 4px;")

    def choose_color(self):
        """Výběr barvy"""
        color = QColorDialog.getColor(QColor(self.selected_color), self, "Vyberte barvu skupiny")
        if color.isValid():
            self.selected_color = color.name()
            self.update_color_preview()

    def load_group_data(self):
        """Načtení dat skupiny"""
        self.code_input.setText(self.group["code"])
        self.name_input.setText(self.group["name"])
        self.discount_work_input.setValue(self.group["discount_work"])
        self.discount_material_input.setValue(self.group["discount_material"])
        self.payment_terms_input.setValue(self.group["payment_terms"])
        self.credit_limit_input.setValue(self.group["credit_limit"])
        self.priority_input.setValue(self.group["priority"])

        if self.group["color"]:
            self.selected_color = self.group["color"]
            self.update_color_preview()

        self.description_input.setPlainText(self.group["description"] or "")
        self.active_checkbox.setChecked(self.group["active"] == 1)
        self.update_priority_label()

    def delete_group(self):
        """Smazání skupiny z dialogu"""
        if self.group:
            self.parent().delete_group(self.group)
            self.reject()

    def save(self):
        """Uložení skupiny"""
        code = self.code_input.text().strip()
        name = self.name_input.text().strip()

        if not code:
            QMessageBox.warning(self, "Chyba", "Vyplňte kód skupiny.")
            return

        if not name:
            QMessageBox.warning(self, "Chyba", "Vyplňte název skupiny.")
            return

        self.accept()

    def get_data(self):
        """Vrácení dat"""
        return {
            "code": self.code_input.text().strip().upper(),
            "name": self.name_input.text().strip(),
            "discount_work": self.discount_work_input.value(),
            "discount_material": self.discount_material_input.value(),
            "payment_terms": self.payment_terms_input.value(),
            "credit_limit": self.credit_limit_input.value(),
            "priority": self.priority_input.value(),
            "color": self.selected_color,
            "description": self.description_input.toPlainText().strip(),
            "active": 1 if self.active_checkbox.isChecked() else 0
        }
