# -*- coding: utf-8 -*-
"""
Správa rolí a jejich oprávnění
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QFrame, QLineEdit, QHeaderView,
    QMessageBox, QDialog, QFormLayout, QTextEdit, QComboBox,
    QCheckBox, QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
from database_manager import db
from utils_auth import get_current_user_id
from utils_permissions import has_permission
import config


class RolesManager(QWidget):
    """Widget pro správu rolí"""

    role_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.roles_data = []
        self.selected_role_id = None

        self.init_ui()
        self.load_roles()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        top_panel = self.create_top_panel()
        main_layout.addWidget(top_panel)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = self.create_roles_list_panel()
        splitter.addWidget(left_panel)

        right_panel = self.create_role_detail_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([400, 800])

        main_layout.addWidget(splitter)

    def create_top_panel(self):
        panel = QFrame()
        panel.setObjectName("topPanel")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("🎭 Správa rolí")
        title.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        layout.addStretch()

        self.btn_new_role = QPushButton("➕ Nová role")
        self.btn_new_role.setObjectName("primaryButton")
        self.btn_new_role.clicked.connect(self.create_new_role)

        uid = get_current_user_id()
        if uid and not has_permission(uid, "users", "admin"):
            self.btn_new_role.setEnabled(False)

        layout.addWidget(self.btn_new_role)

        panel.setStyleSheet(f"""
            #topPanel {{
                background-color: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
            }}
            #sectionTitle {{
                color: {config.COLOR_PRIMARY};
            }}
            #primaryButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }}
            #primaryButton:hover {{
                background-color: #2980b9;
            }}
        """)

        return panel

    def create_roles_list_panel(self):
        panel = QFrame()
        panel.setObjectName("rolesListPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        list_label = QLabel("📋 Seznam rolí")
        list_label.setObjectName("panelTitle")
        font = QFont()
        font.setBold(True)
        list_label.setFont(font)
        layout.addWidget(list_label)

        self.roles_table = QTableWidget()
        self.roles_table.setColumnCount(3)
        self.roles_table.setHorizontalHeaderLabels(["Název", "Uživatelů", "Výchozí"])

        header = self.roles_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.roles_table.setColumnWidth(1, 80)
        self.roles_table.setColumnWidth(2, 70)

        self.roles_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.roles_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.roles_table.itemSelectionChanged.connect(self.on_role_selected)

        layout.addWidget(self.roles_table)

        buttons_layout = QHBoxLayout()

        self.btn_edit_role = QPushButton("✏️ Upravit")
        self.btn_edit_role.clicked.connect(self.edit_selected_role)
        self.btn_edit_role.setEnabled(False)
        buttons_layout.addWidget(self.btn_edit_role)

        self.btn_copy_role = QPushButton("📋 Kopírovat")
        self.btn_copy_role.clicked.connect(self.copy_selected_role)
        self.btn_copy_role.setEnabled(False)
        buttons_layout.addWidget(self.btn_copy_role)

        self.btn_delete_role = QPushButton("🗑️ Smazat")
        self.btn_delete_role.setObjectName("dangerButton")
        self.btn_delete_role.clicked.connect(self.delete_selected_role)
        self.btn_delete_role.setEnabled(False)
        buttons_layout.addWidget(self.btn_delete_role)

        layout.addLayout(buttons_layout)

        panel.setStyleSheet(f"""
            #rolesListPanel {{
                background-color: white;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
            }}
            #panelTitle {{
                color: {config.COLOR_PRIMARY};
            }}
            #dangerButton {{
                background-color: {config.COLOR_DANGER};
                color: white;
            }}
            #dangerButton:hover {{
                background-color: #c0392b;
            }}
            QTableWidget {{
                border: 1px solid #d0d0d0;
                border-radius: 5px;
            }}
            QHeaderView::section {{
                background-color: {config.COLOR_PRIMARY};
                color: white;
                padding: 8px;
                border: none;
            }}
        """)

        return panel

    def create_role_detail_panel(self):
        panel = QFrame()
        panel.setObjectName("roleDetailPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        detail_label = QLabel("🔐 Oprávnění role")
        detail_label.setObjectName("panelTitle")
        font = QFont()
        font.setBold(True)
        detail_label.setFont(font)
        layout.addWidget(detail_label)

        self.lbl_selected_role = QLabel("Vyberte roli ze seznamu")
        self.lbl_selected_role.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.lbl_selected_role)

        self.permissions_table = QTableWidget()
        self.permissions_table.setColumnCount(6)
        self.permissions_table.setHorizontalHeaderLabels([
            "Modul", "Zobrazit", "Vytvořit", "Upravit", "Smazat", "Admin"
        ])

        header = self.permissions_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 6):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            self.permissions_table.setColumnWidth(i, 80)

        layout.addWidget(self.permissions_table)

        buttons_layout = QHBoxLayout()

        self.btn_select_all = QPushButton("✅ Vybrat vše")
        self.btn_select_all.clicked.connect(self.select_all_permissions)
        self.btn_select_all.setEnabled(False)
        buttons_layout.addWidget(self.btn_select_all)

        self.btn_deselect_all = QPushButton("❌ Odznačit vše")
        self.btn_deselect_all.clicked.connect(self.deselect_all_permissions)
        self.btn_deselect_all.setEnabled(False)
        buttons_layout.addWidget(self.btn_deselect_all)

        buttons_layout.addStretch()

        self.btn_save_permissions = QPushButton("💾 Uložit oprávnění")
        self.btn_save_permissions.setObjectName("primaryButton")
        self.btn_save_permissions.clicked.connect(self.save_role_permissions)
        self.btn_save_permissions.setEnabled(False)
        buttons_layout.addWidget(self.btn_save_permissions)

        layout.addLayout(buttons_layout)

        panel.setStyleSheet(f"""
            #roleDetailPanel {{
                background-color: white;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
            }}
            #panelTitle {{
                color: {config.COLOR_PRIMARY};
            }}
            #primaryButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }}
            #primaryButton:hover {{
                background-color: #2980b9;
            }}
            QTableWidget {{
                border: 1px solid #d0d0d0;
                border-radius: 5px;
            }}
            QHeaderView::section {{
                background-color: {config.COLOR_PRIMARY};
                color: white;
                padding: 8px;
                border: none;
            }}
        """)

        return panel

    def load_roles(self):
        query = """
            SELECT
                r.id, r.name, r.description, r.is_default,
                (SELECT COUNT(*) FROM users WHERE role = r.name) as user_count
            FROM roles r
            ORDER BY r.name
        """

        self.roles_data = db.fetch_all(query)
        self.display_roles()

    def display_roles(self):
        self.roles_table.setRowCount(0)

        for role in self.roles_data:
            row = self.roles_table.rowCount()
            self.roles_table.insertRow(row)

            name_item = QTableWidgetItem(role['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, role['id'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.roles_table.setItem(row, 0, name_item)

            count_item = QTableWidgetItem(str(role['user_count']))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            count_item.setFlags(count_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.roles_table.setItem(row, 1, count_item)

            default_text = "✅" if role['is_default'] else ""
            default_item = QTableWidgetItem(default_text)
            default_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            default_item.setFlags(default_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.roles_table.setItem(row, 2, default_item)

    def on_role_selected(self):
        selected = self.roles_table.selectedItems()
        if not selected:
            self.selected_role_id = None
            self.lbl_selected_role.setText("Vyberte roli ze seznamu")
            self.btn_edit_role.setEnabled(False)
            self.btn_copy_role.setEnabled(False)
            self.btn_delete_role.setEnabled(False)
            self.btn_select_all.setEnabled(False)
            self.btn_deselect_all.setEnabled(False)
            self.btn_save_permissions.setEnabled(False)
            return

        name_item = self.roles_table.item(selected[0].row(), 0)
        self.selected_role_id = name_item.data(Qt.ItemDataRole.UserRole)
        role_name = name_item.text()

        self.lbl_selected_role.setText(f"Role: {role_name}")
        self.btn_edit_role.setEnabled(True)
        self.btn_copy_role.setEnabled(True)
        self.btn_delete_role.setEnabled(True)
        self.btn_select_all.setEnabled(True)
        self.btn_deselect_all.setEnabled(True)
        self.btn_save_permissions.setEnabled(True)

        self.load_role_permissions(self.selected_role_id)

    def load_role_permissions(self, role_id):
        self.permissions_table.setRowCount(0)

        modules = config.MODULES

        for module in modules:
            row = self.permissions_table.rowCount()
            self.permissions_table.insertRow(row)

            name_item = QTableWidgetItem(f"{module['icon']} {module['name']}")
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setData(Qt.ItemDataRole.UserRole, module['id'])
            self.permissions_table.setItem(row, 0, name_item)

            actions = ['view', 'create', 'edit', 'delete', 'admin']
            for col, action in enumerate(actions, start=1):
                perm = db.fetch_one(
                    "SELECT id FROM permissions WHERE module_id = ? AND action = ?",
                    (module['id'], action)
                )

                if perm:
                    rp = db.fetch_one(
                        "SELECT allowed FROM role_permissions WHERE role_id = ? AND permission_id = ?",
                        (role_id, perm['id'])
                    )
                    is_allowed = bool(rp and rp['allowed'])
                else:
                    is_allowed = False

                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)

                chk = QCheckBox()
                chk.setChecked(is_allowed)
                chk.setProperty("module_id", module['id'])
                chk.setProperty("action", action)
                checkbox_layout.addWidget(chk)

                self.permissions_table.setCellWidget(row, col, checkbox_widget)

    def select_all_permissions(self):
        for row in range(self.permissions_table.rowCount()):
            for col in range(1, 6):
                widget = self.permissions_table.cellWidget(row, col)
                if widget:
                    chk = widget.findChild(QCheckBox)
                    if chk:
                        chk.setChecked(True)

    def deselect_all_permissions(self):
        for row in range(self.permissions_table.rowCount()):
            for col in range(1, 6):
                widget = self.permissions_table.cellWidget(row, col)
                if widget:
                    chk = widget.findChild(QCheckBox)
                    if chk:
                        chk.setChecked(False)

    def save_role_permissions(self):
        if not self.selected_role_id:
            return

        uid = get_current_user_id()
        if uid and not has_permission(uid, "users", "admin"):
            QMessageBox.warning(self, "Přístup odepřen", "Nemáte oprávnění měnit oprávnění rolí.")
            return

        try:
            for row in range(self.permissions_table.rowCount()):
                module_item = self.permissions_table.item(row, 0)
                module_id = module_item.data(Qt.ItemDataRole.UserRole)

                actions = ['view', 'create', 'edit', 'delete', 'admin']
                for col, action in enumerate(actions, start=1):
                    widget = self.permissions_table.cellWidget(row, col)
                    if widget:
                        chk = widget.findChild(QCheckBox)
                        if chk:
                            is_allowed = 1 if chk.isChecked() else 0

                            perm = db.fetch_one(
                                "SELECT id FROM permissions WHERE module_id = ? AND action = ?",
                                (module_id, action)
                            )

                            if perm:
                                existing = db.fetch_one(
                                    "SELECT id FROM role_permissions WHERE role_id = ? AND permission_id = ?",
                                    (self.selected_role_id, perm['id'])
                                )

                                if existing:
                                    db.execute_query(
                                        "UPDATE role_permissions SET allowed = ? WHERE id = ?",
                                        (is_allowed, existing['id'])
                                    )
                                else:
                                    db.execute_query(
                                        "INSERT INTO role_permissions (role_id, permission_id, allowed) VALUES (?, ?, ?)",
                                        (self.selected_role_id, perm['id'], is_allowed)
                                    )

            QMessageBox.information(self, "Úspěch", "Oprávnění role byla uložena.")
            self.role_updated.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při ukládání oprávnění: {e}")

    def create_new_role(self):
        uid = get_current_user_id()
        if uid and not has_permission(uid, "users", "admin"):
            QMessageBox.warning(self, "Přístup odepřen", "Nemáte oprávnění vytvářet role.")
            return

        dialog = RoleDialog(parent=self)
        if dialog.exec():
            self.load_roles()
            self.role_updated.emit()

    def edit_selected_role(self):
        if not self.selected_role_id:
            return

        uid = get_current_user_id()
        if uid and not has_permission(uid, "users", "admin"):
            QMessageBox.warning(self, "Přístup odepřen", "Nemáte oprávnění upravovat role.")
            return

        dialog = RoleDialog(role_id=self.selected_role_id, parent=self)
        if dialog.exec():
            self.load_roles()
            self.role_updated.emit()

    def copy_selected_role(self):
        if not self.selected_role_id:
            return

        uid = get_current_user_id()
        if uid and not has_permission(uid, "users", "admin"):
            QMessageBox.warning(self, "Přístup odepřen", "Nemáte oprávnění kopírovat role.")
            return

        role = db.fetch_one("SELECT name FROM roles WHERE id = ?", (self.selected_role_id,))
        if not role:
            return

        new_name = f"{role['name']}_kopie"

        dialog = RoleDialog(copy_from_id=self.selected_role_id, default_name=new_name, parent=self)
        if dialog.exec():
            self.load_roles()
            self.role_updated.emit()

    def delete_selected_role(self):
        if not self.selected_role_id:
            return

        uid = get_current_user_id()
        if uid and not has_permission(uid, "users", "admin"):
            QMessageBox.warning(self, "Přístup odepřen", "Nemáte oprávnění mazat role.")
            return

        role = db.fetch_one("SELECT name FROM roles WHERE id = ?", (self.selected_role_id,))
        if not role:
            return

        user_count = db.fetch_one(
            "SELECT COUNT(*) as count FROM users WHERE role = ?",
            (role['name'],)
        )

        if user_count and user_count['count'] > 0:
            QMessageBox.warning(
                self,
                "Nelze smazat",
                f"Roli '{role['name']}' nelze smazat, protože ji má přiřazeno {user_count['count']} uživatelů."
            )
            return

        reply = QMessageBox.question(
            self,
            "Potvrzení smazání",
            f"Opravdu chcete smazat roli '{role['name']}'?\n\nTato akce je nevratná!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            db.execute_query("DELETE FROM role_permissions WHERE role_id = ?", (self.selected_role_id,))
            db.execute_query("DELETE FROM roles WHERE id = ?", (self.selected_role_id,))

            self.selected_role_id = None
            self.load_roles()
            self.role_updated.emit()

    def refresh(self):
        self.load_roles()
        if self.selected_role_id:
            self.load_role_permissions(self.selected_role_id)


class RoleDialog(QDialog):
    """Dialog pro vytvoření/editaci role"""

    def __init__(self, role_id=None, copy_from_id=None, default_name="", parent=None):
        super().__init__(parent)

        self.role_id = role_id
        self.copy_from_id = copy_from_id
        self.is_new = role_id is None

        if self.is_new and copy_from_id:
            self.setWindowTitle("Kopírovat roli")
        elif self.is_new:
            self.setWindowTitle("Nová role")
        else:
            self.setWindowTitle("Editace role")

        self.setMinimumSize(400, 300)
        self.setModal(True)

        self.init_ui()

        if default_name:
            self.txt_name.setText(default_name)

        if not self.is_new:
            self.load_role_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Název role (např. mechanik)")
        form_layout.addRow("Název: *", self.txt_name)

        self.txt_description = QTextEdit()
        self.txt_description.setPlaceholderText("Popis role...")
        self.txt_description.setMaximumHeight(100)
        form_layout.addRow("Popis:", self.txt_description)

        self.chk_default = QCheckBox("Toto je výchozí role pro nové uživatele")
        form_layout.addRow("Výchozí:", self.chk_default)

        layout.addLayout(form_layout)

        required_note = QLabel("* Povinné položky")
        required_note.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(required_note)

        layout.addStretch()

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_save = QPushButton("💾 Uložit")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self.save_role)
        buttons_layout.addWidget(btn_save)

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        layout.addLayout(buttons_layout)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: #f5f5f5;
            }}
            QLineEdit, QTextEdit {{
                padding: 8px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }}
            #primaryButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 25px;
                font-weight: bold;
            }}
            #primaryButton:hover {{
                background-color: #2980b9;
            }}
        """)

    def load_role_data(self):
        if not self.role_id:
            return

        role = db.fetch_one("SELECT * FROM roles WHERE id = ?", (self.role_id,))
        if role:
            self.txt_name.setText(role['name'])
            self.txt_description.setPlainText(role['description'] or "")
            self.chk_default.setChecked(bool(role['is_default']))

    def save_role(self):
        name = self.txt_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Chyba", "Název role je povinný.")
            return

        existing = db.fetch_one(
            "SELECT id FROM roles WHERE name = ? AND id != ?",
            (name, self.role_id or 0)
        )
        if existing:
            QMessageBox.warning(self, "Chyba", "Role s tímto názvem již existuje.")
            return

        description = self.txt_description.toPlainText().strip() or None
        is_default = 1 if self.chk_default.isChecked() else 0

        try:
            if is_default:
                db.execute_query("UPDATE roles SET is_default = 0")

            if self.is_new:
                db.execute_query(
                    "INSERT INTO roles (name, description, is_default) VALUES (?, ?, ?)",
                    (name, description, is_default)
                )

                if self.copy_from_id:
                    new_role = db.fetch_one("SELECT last_insert_rowid() as id")
                    if new_role:
                        perms = db.fetch_all(
                            "SELECT permission_id, allowed FROM role_permissions WHERE role_id = ?",
                            (self.copy_from_id,)
                        )
                        for perm in perms:
                            db.execute_query(
                                "INSERT INTO role_permissions (role_id, permission_id, allowed) VALUES (?, ?, ?)",
                                (new_role['id'], perm['permission_id'], perm['allowed'])
                            )
            else:
                db.execute_query(
                    "UPDATE roles SET name = ?, description = ?, is_default = ? WHERE id = ?",
                    (name, description, is_default, self.role_id)
                )

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při ukládání role: {e}")
