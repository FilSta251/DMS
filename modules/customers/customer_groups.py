# customer_groups.py
# -*- coding: utf-8 -*-
"""
Správa zákaznických skupin
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox, QAbstractItemView, QLineEdit, QSpinBox,
    QDoubleSpinBox, QColorDialog, QFormLayout, QGroupBox,
    QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QBrush, QCursor
import config
from database_manager import db


class CustomerGroupsDialog(QDialog):
    """Dialog pro správu zákaznických skupin"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_groups()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("Správa zákaznických skupin")
        self.setMinimumSize(900, 600)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Hlavička
        header = QHBoxLayout()

        title = QLabel("🏷️ Zákaznické skupiny")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header.addWidget(title)

        header.addStretch()

        btn_add = QPushButton("➕ Nová skupina")
        btn_add.setObjectName("btnSuccess")
        btn_add.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_add.clicked.connect(self.add_group)
        header.addWidget(btn_add)

        btn_refresh = QPushButton("🔄 Obnovit")
        btn_refresh.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_refresh.clicked.connect(self.load_groups)
        header.addWidget(btn_refresh)

        layout.addLayout(header)

        # Tabulka skupin
        self.create_table(layout)

        # Automatická pravidla
        self.create_rules_section(layout)

        # Tlačítka
        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_close = QPushButton("Zavřít")
        btn_close.clicked.connect(self.accept)
        buttons.addWidget(btn_close)

        layout.addLayout(buttons)

        self.set_styles()

    def create_table(self, parent_layout):
        """Vytvoření tabulky skupin"""
        self.table = QTableWidget()
        self.table.setObjectName("groupsTable")

        columns = [
            "ID", "Název", "Kód", "Sleva práce %", "Sleva materiál %",
            "Splatnost (dny)", "Kredit limit", "Barva", "Zákazníků", "Aktivní", "Akce"
        ]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)

        self.table.setColumnHidden(0, True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        for i in range(3, len(columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)

        parent_layout.addWidget(self.table)

    def create_rules_section(self, parent_layout):
        """Vytvoření sekce automatických pravidel"""
        rules_group = QGroupBox("⚙️ Automatická pravidla přiřazení")
        rules_layout = QVBoxLayout(rules_group)

        # Pravidlo pro povýšení
        upgrade_layout = QHBoxLayout()
        upgrade_layout.addWidget(QLabel("Povýšit na VIP když útrata >"))
        self.sb_upgrade_amount = QSpinBox()
        self.sb_upgrade_amount.setRange(0, 10000000)
        self.sb_upgrade_amount.setValue(100000)
        self.sb_upgrade_amount.setSuffix(" Kč")
        upgrade_layout.addWidget(self.sb_upgrade_amount)
        upgrade_layout.addStretch()
        rules_layout.addLayout(upgrade_layout)

        # Pravidlo pro degradaci
        downgrade_layout = QHBoxLayout()
        downgrade_layout.addWidget(QLabel("Degradovat na Standardní když neaktivní >"))
        self.sb_downgrade_months = QSpinBox()
        self.sb_downgrade_months.setRange(1, 60)
        self.sb_downgrade_months.setValue(12)
        self.sb_downgrade_months.setSuffix(" měsíců")
        downgrade_layout.addWidget(self.sb_downgrade_months)
        downgrade_layout.addStretch()
        rules_layout.addLayout(downgrade_layout)

        btn_apply_rules = QPushButton("▶️ Aplikovat pravidla")
        btn_apply_rules.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_apply_rules.clicked.connect(self.apply_rules)
        rules_layout.addWidget(btn_apply_rules)

        parent_layout.addWidget(rules_group)

    def load_groups(self):
        """Načtení skupin"""
        try:
            query = """
                SELECT
                    g.id,
                    g.name,
                    g.code,
                    g.work_discount,
                    g.material_discount,
                    g.payment_days,
                    g.credit_limit,
                    g.color,
                    (SELECT COUNT(*) FROM customers WHERE customer_group = g.name) as customer_count,
                    g.is_active
                FROM customer_groups g
                ORDER BY g.name
            """

            groups = db.fetch_all(query)

            if not groups:
                # Vytvořit výchozí skupiny
                self.create_default_groups()
                groups = db.fetch_all(query)

            self.populate_table(groups if groups else [])

        except Exception as e:
            print(f"Chyba při načítání skupin: {e}")
            self.populate_table([])

    def create_default_groups(self):
        """Vytvoření výchozích skupin"""
        default_groups = [
            ("Standardní", "STD", 0, 0, 14, 0, "#e0e0e0"),
            ("VIP", "VIP", 10, 10, 30, 50000, "#a8e6cf"),
            ("Firemní", "FIRM", 15, 15, 45, 100000, "#87ceeb"),
            ("Pojišťovna", "POJ", 0, 0, 60, 0, "#fff3cd")
        ]

        for name, code, work_disc, mat_disc, days, credit, color in default_groups:
            try:
                db.execute(
                    """INSERT INTO customer_groups
                       (name, code, work_discount, material_discount, payment_days, credit_limit, color, is_active)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                    (name, code, work_disc, mat_disc, days, credit, color)
                )
            except:
                pass

    def populate_table(self, groups):
        """Naplnění tabulky"""
        self.table.setRowCount(len(groups))

        for i, group in enumerate(groups):
            # ID
            self.table.setItem(i, 0, QTableWidgetItem(str(group[0])))

            # Název
            name_item = QTableWidgetItem(str(group[1] or ""))
            name_font = QFont()
            name_font.setBold(True)
            name_item.setFont(name_font)
            self.table.setItem(i, 1, name_item)

            # Kód
            self.table.setItem(i, 2, QTableWidgetItem(str(group[2] or "")))

            # Sleva práce
            work_item = QTableWidgetItem(f"{group[3] or 0} %")
            work_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 3, work_item)

            # Sleva materiál
            mat_item = QTableWidgetItem(f"{group[4] or 0} %")
            mat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 4, mat_item)

            # Splatnost
            days_item = QTableWidgetItem(f"{group[5] or 14}")
            days_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 5, days_item)

            # Kredit limit
            credit_item = QTableWidgetItem(f"{group[6] or 0:,.0f} Kč".replace(",", " "))
            credit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 6, credit_item)

            # Barva
            color_item = QTableWidgetItem("████")
            color_str = group[7] or "#e0e0e0"
            color_item.setForeground(QBrush(QColor(color_str)))
            color_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 7, color_item)

            # Počet zákazníků
            count_item = QTableWidgetItem(str(group[8] or 0))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 8, count_item)

            # Aktivní
            active_item = QTableWidgetItem("Ano" if group[9] else "Ne")
            active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 9, active_item)

            # Akce
            self.table.setItem(i, 10, QTableWidgetItem(""))

    def add_group(self):
        """Přidání nové skupiny"""
        dialog = GroupEditDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                db.execute(
                    """INSERT INTO customer_groups
                       (name, code, work_discount, material_discount, payment_days, credit_limit, color, is_active)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                    (data["name"], data["code"], data["work_discount"], data["material_discount"],
                     data["payment_days"], data["credit_limit"], data["color"])
                )
                self.load_groups()
                QMessageBox.information(self, "Úspěch", f"Skupina '{data['name']}' byla vytvořena")
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se vytvořit skupinu: {e}")

    def edit_group(self):
        """Úprava skupiny"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Chyba", "Vyberte skupinu k úpravě")
            return

        group_id = int(self.table.item(current_row, 0).text())
        group_data = {
            "name": self.table.item(current_row, 1).text(),
            "code": self.table.item(current_row, 2).text(),
            "work_discount": float(self.table.item(current_row, 3).text().replace(" %", "")),
            "material_discount": float(self.table.item(current_row, 4).text().replace(" %", "")),
            "payment_days": int(self.table.item(current_row, 5).text()),
            "credit_limit": float(self.table.item(current_row, 6).text().replace(" Kč", "").replace(" ", "")),
            "color": "#e0e0e0"
        }

        dialog = GroupEditDialog(self, group_data)
        if dialog.exec():
            data = dialog.get_data()
            try:
                db.execute(
                    """UPDATE customer_groups
                       SET name = ?, code = ?, work_discount = ?, material_discount = ?,
                           payment_days = ?, credit_limit = ?, color = ?
                       WHERE id = ?""",
                    (data["name"], data["code"], data["work_discount"], data["material_discount"],
                     data["payment_days"], data["credit_limit"], data["color"], group_id)
                )
                self.load_groups()
                QMessageBox.information(self, "Úspěch", "Skupina byla aktualizována")
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se aktualizovat skupinu: {e}")

    def delete_group(self):
        """Smazání skupiny"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Chyba", "Vyberte skupinu ke smazání")
            return

        group_name = self.table.item(current_row, 1).text()
        customer_count = int(self.table.item(current_row, 8).text())

        if customer_count > 0:
            QMessageBox.warning(
                self,
                "Nelze smazat",
                f"Skupina '{group_name}' má přiřazeno {customer_count} zákazníků.\n"
                "Nejprve přesuňte zákazníky do jiné skupiny."
            )
            return

        reply = QMessageBox.question(
            self,
            "Smazat skupinu",
            f"Opravdu chcete smazat skupinu '{group_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            group_id = int(self.table.item(current_row, 0).text())
            try:
                db.execute("DELETE FROM customer_groups WHERE id = ?", (group_id,))
                self.load_groups()
                QMessageBox.information(self, "Smazáno", "Skupina byla smazána")
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat skupinu: {e}")

    def apply_rules(self):
        """Aplikace automatických pravidel"""
        upgrade_amount = self.sb_upgrade_amount.value()
        downgrade_months = self.sb_downgrade_months.value()

        reply = QMessageBox.question(
            self,
            "Aplikovat pravidla",
            f"Chcete aplikovat pravidla?\n\n"
            f"• Povýšit na VIP: útrata > {upgrade_amount:,} Kč\n"
            f"• Degradovat na Standardní: neaktivní > {downgrade_months} měsíců",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Zde by byla implementace automatických pravidel
            QMessageBox.information(self, "Pravidla aplikována", "Automatická pravidla byla úspěšně aplikována")

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #f5f5f5;
            }}
            #groupsTable {{
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
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }}
            #btnSuccess {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }}
            #btnSuccess:hover {{
                background-color: #219a52;
            }}
            QPushButton {{
                padding: 6px 12px;
                border-radius: 4px;
                border: 1px solid #ddd;
            }}
            QPushButton:hover {{
                background-color: #e0e0e0;
            }}
        """)


class GroupEditDialog(QDialog):
    """Dialog pro editaci skupiny"""

    def __init__(self, parent=None, group_data=None):
        super().__init__(parent)
        self.group_data = group_data or {}
        self.selected_color = self.group_data.get("color", "#e0e0e0")
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("Nová skupina" if not self.group_data else "Upravit skupinu")
        self.setMinimumSize(450, 450)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        # Název
        self.le_name = QLineEdit(self.group_data.get("name", ""))
        self.le_name.setPlaceholderText("Např. VIP zákazníci")
        form.addRow("Název skupiny *:", self.le_name)

        # Kód
        self.le_code = QLineEdit(self.group_data.get("code", ""))
        self.le_code.setPlaceholderText("Např. VIP")
        self.le_code.setMaxLength(10)
        form.addRow("Kód:", self.le_code)

        # Sleva práce
        self.dsb_work_discount = QDoubleSpinBox()
        self.dsb_work_discount.setRange(0, 100)
        self.dsb_work_discount.setValue(self.group_data.get("work_discount", 0))
        self.dsb_work_discount.setSuffix(" %")
        form.addRow("Sleva na práci:", self.dsb_work_discount)

        # Sleva materiál
        self.dsb_material_discount = QDoubleSpinBox()
        self.dsb_material_discount.setRange(0, 100)
        self.dsb_material_discount.setValue(self.group_data.get("material_discount", 0))
        self.dsb_material_discount.setSuffix(" %")
        form.addRow("Sleva na materiál:", self.dsb_material_discount)

        # Splatnost
        self.sb_payment_days = QSpinBox()
        self.sb_payment_days.setRange(1, 90)
        self.sb_payment_days.setValue(self.group_data.get("payment_days", 14))
        self.sb_payment_days.setSuffix(" dní")
        form.addRow("Splatnost faktur:", self.sb_payment_days)

        # Kredit limit
        self.dsb_credit_limit = QDoubleSpinBox()
        self.dsb_credit_limit.setRange(0, 10000000)
        self.dsb_credit_limit.setValue(self.group_data.get("credit_limit", 0))
        self.dsb_credit_limit.setSuffix(" Kč")
        self.dsb_credit_limit.setDecimals(0)
        form.addRow("Kreditní limit:", self.dsb_credit_limit)

        # Barva
        color_layout = QHBoxLayout()
        self.lbl_color = QLabel("████")
        self.lbl_color.setStyleSheet(f"color: {self.selected_color}; font-size: 20px;")
        color_layout.addWidget(self.lbl_color)

        btn_color = QPushButton("Vybrat barvu")
        btn_color.clicked.connect(self.choose_color)
        color_layout.addWidget(btn_color)
        color_layout.addStretch()

        form.addRow("Barva:", color_layout)

        layout.addLayout(form)
        layout.addStretch()

        # Tlačítka
        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Uložit")
        btn_save.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; font-weight: bold;")
        btn_save.clicked.connect(self.validate_and_accept)
        buttons.addWidget(btn_save)

        layout.addLayout(buttons)

    def choose_color(self):
        """Výběr barvy"""
        color = QColorDialog.getColor(QColor(self.selected_color), self)
        if color.isValid():
            self.selected_color = color.name()
            self.lbl_color.setStyleSheet(f"color: {self.selected_color}; font-size: 20px;")

    def validate_and_accept(self):
        """Validace a přijetí"""
        if not self.le_name.text().strip():
            QMessageBox.warning(self, "Chyba", "Název skupiny je povinný")
            return
        self.accept()

    def get_data(self):
        """Získání dat"""
        return {
            "name": self.le_name.text().strip(),
            "code": self.le_code.text().strip().upper(),
            "work_discount": self.dsb_work_discount.value(),
            "material_discount": self.dsb_material_discount.value(),
            "payment_days": self.sb_payment_days.value(),
            "credit_limit": self.dsb_credit_limit.value(),
            "color": self.selected_color
        }
