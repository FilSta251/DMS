# -*- coding: utf-8 -*-
"""
Seznam uživatelů
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QFrame, QLineEdit, QComboBox, QHeaderView,
    QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QIcon
from datetime import datetime
from database_manager import db
from utils_auth import get_current_user_id, hash_password
from utils_permissions import has_permission
import config


class UsersList(QWidget):
    """Widget pro seznam uživatelů"""

    user_selected = pyqtSignal(int)
    user_edited = pyqtSignal(int)
    user_deleted = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.users_data = []

        self.init_ui()
        self.load_users()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        filters_panel = self.create_filters_panel()
        main_layout.addWidget(filters_panel)

        self.create_table()
        main_layout.addWidget(self.table)

        actions_panel = self.create_actions_panel()
        main_layout.addWidget(actions_panel)

    def create_filters_panel(self):
        panel = QFrame()
        panel.setObjectName("filtersPanel")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        search_layout = QHBoxLayout()
        search_label = QLabel("🔍")
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Hledat uživatele...")
        self.txt_search.setMinimumWidth(250)
        self.txt_search.textChanged.connect(self.filter_users)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.txt_search)
        layout.addLayout(search_layout)

        role_layout = QHBoxLayout()
        role_label = QLabel("Role:")
        self.cmb_role = QComboBox()
        self.cmb_role.addItem("Všechny role", None)
        self.load_roles_combo()
        self.cmb_role.currentIndexChanged.connect(self.filter_users)
        role_layout.addWidget(role_label)
        role_layout.addWidget(self.cmb_role)
        layout.addLayout(role_layout)

        status_layout = QHBoxLayout()
        status_label = QLabel("Stav:")
        self.cmb_status = QComboBox()
        self.cmb_status.addItem("Všechny stavy", None)
        self.cmb_status.addItem("✅ Aktivní", 1)
        self.cmb_status.addItem("❌ Neaktivní", 0)
        self.cmb_status.currentIndexChanged.connect(self.filter_users)
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.cmb_status)
        layout.addLayout(status_layout)

        layout.addStretch()

        self.btn_reset = QPushButton("🔄 Reset")
        self.btn_reset.clicked.connect(self.reset_filters)
        layout.addWidget(self.btn_reset)

        self.btn_refresh = QPushButton("🔄 Obnovit")
        self.btn_refresh.clicked.connect(self.load_users)
        layout.addWidget(self.btn_refresh)

        panel.setStyleSheet("""
            #filtersPanel {
                background-color: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
            }
        """)

        return panel

    def create_table(self):
        self.table = QTableWidget()
        self.table.setObjectName("usersTable")

        columns = [
            "ID", "Uživatelské jméno", "Celé jméno", "Email",
            "Role", "Aktivní", "Poslední přihlášení", "Vytvořeno", "Akce"
        ]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(3, 200)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 70)
        self.table.setColumnWidth(6, 150)
        self.table.setColumnWidth(7, 120)
        self.table.setColumnWidth(8, 150)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.cellDoubleClicked.connect(self.on_row_double_clicked)

        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                background-color: white;
                gridline-color: #e0e0e0;
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {config.COLOR_PRIMARY};
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
        """)

    def create_actions_panel(self):
        panel = QFrame()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.lbl_count = QLabel("Celkem: 0 uživatelů")
        self.lbl_count.setObjectName("countLabel")
        layout.addWidget(self.lbl_count)

        layout.addStretch()

        self.btn_activate = QPushButton("✅ Aktivovat")
        self.btn_activate.clicked.connect(lambda: self.toggle_user_status(True))
        layout.addWidget(self.btn_activate)

        self.btn_deactivate = QPushButton("❌ Deaktivovat")
        self.btn_deactivate.clicked.connect(lambda: self.toggle_user_status(False))
        layout.addWidget(self.btn_deactivate)

        self.btn_reset_password = QPushButton("🔑 Reset hesla")
        self.btn_reset_password.clicked.connect(self.reset_user_password)
        layout.addWidget(self.btn_reset_password)

        self.btn_delete = QPushButton("🗑️ Smazat")
        self.btn_delete.setObjectName("dangerButton")
        self.btn_delete.clicked.connect(self.delete_user)
        layout.addWidget(self.btn_delete)

        panel.setStyleSheet(f"""
            #countLabel {{
                color: #666;
                font-weight: bold;
            }}
            #dangerButton {{
                background-color: {config.COLOR_DANGER};
                color: white;
            }}
            #dangerButton:hover {{
                background-color: #c0392b;
            }}
        """)

        return panel

    def load_roles_combo(self):
        roles = db.fetch_all("SELECT name FROM roles ORDER BY name")
        for role in roles:
            self.cmb_role.addItem(role['name'], role['name'])

    def load_users(self):
        query = """
            SELECT
                id, username, full_name, email, role, active,
                last_login, created_at
            FROM users
            ORDER BY full_name
        """

        self.users_data = db.fetch_all(query)
        self.display_users(self.users_data)

    def display_users(self, users):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        for user in users:
            row = self.table.rowCount()
            self.table.insertRow(row)

            id_item = QTableWidgetItem(str(user['id']))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, id_item)

            username_item = QTableWidgetItem(user['username'] or "")
            username_item.setFlags(username_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, username_item)

            fullname_item = QTableWidgetItem(user['full_name'] or "")
            fullname_item.setFlags(fullname_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, fullname_item)

            email_item = QTableWidgetItem(user['email'] or "")
            email_item.setFlags(email_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, email_item)

            role_text = user['role'] or "Bez role"
            role_item = QTableWidgetItem(role_text)
            role_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            role_item.setFlags(role_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            role_colors = {
                'admin': '#e74c3c',
                'vedouci': '#f39c12',
                'mechanik': '#3498db',
                'recepcni': '#9b59b6',
                'skladnik': '#27ae60',
                'ucetni': '#1abc9c'
            }
            if user['role'] and user['role'].lower() in role_colors:
                role_item.setForeground(QColor(role_colors[user['role'].lower()]))
            self.table.setItem(row, 4, role_item)

            active_text = "✅ Ano" if user['active'] else "❌ Ne"
            active_item = QTableWidgetItem(active_text)
            active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            active_item.setFlags(active_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if not user['active']:
                active_item.setForeground(QColor(config.COLOR_DANGER))
            self.table.setItem(row, 5, active_item)

            if user['last_login']:
                try:
                    dt = datetime.fromisoformat(user['last_login'])
                    login_text = dt.strftime("%d.%m.%Y %H:%M")
                except:
                    login_text = user['last_login']
            else:
                login_text = "Nikdy"
            login_item = QTableWidgetItem(login_text)
            login_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            login_item.setFlags(login_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 6, login_item)

            if user['created_at']:
                try:
                    dt = datetime.fromisoformat(user['created_at'])
                    created_text = dt.strftime("%d.%m.%Y")
                except:
                    created_text = user['created_at']
            else:
                created_text = "--"
            created_item = QTableWidgetItem(created_text)
            created_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            created_item.setFlags(created_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 7, created_item)

            actions_widget = self.create_action_buttons(user['id'])
            self.table.setCellWidget(row, 8, actions_widget)

        self.table.setSortingEnabled(True)
        self.lbl_count.setText(f"Celkem: {len(users)} uživatelů")

    def create_action_buttons(self, user_id):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)

        btn_edit = QPushButton("✏️")
        btn_edit.setToolTip("Upravit")
        btn_edit.setFixedSize(30, 25)
        btn_edit.clicked.connect(lambda: self.edit_user(user_id))
        layout.addWidget(btn_edit)

        btn_permissions = QPushButton("🔐")
        btn_permissions.setToolTip("Oprávnění")
        btn_permissions.setFixedSize(30, 25)
        btn_permissions.clicked.connect(lambda: self.edit_user_permissions(user_id))
        layout.addWidget(btn_permissions)

        btn_history = QPushButton("📊")
        btn_history.setToolTip("Historie")
        btn_history.setFixedSize(30, 25)
        btn_history.clicked.connect(lambda: self.show_user_history(user_id))
        layout.addWidget(btn_history)

        return widget

    def filter_users(self):
        search_text = self.txt_search.text().lower()
        role_filter = self.cmb_role.currentData()
        status_filter = self.cmb_status.currentData()

        filtered = []
        for user in self.users_data:
            if search_text:
                searchable = f"{user['username']} {user['full_name']} {user['email']}".lower()
                if search_text not in searchable:
                    continue

            if role_filter and user['role'] != role_filter:
                continue

            if status_filter is not None and user['active'] != status_filter:
                continue

            filtered.append(user)

        self.display_users(filtered)

    def reset_filters(self):
        self.txt_search.clear()
        self.cmb_role.setCurrentIndex(0)
        self.cmb_status.setCurrentIndex(0)
        self.display_users(self.users_data)

    def get_selected_user_id(self):
        selected = self.table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        id_item = self.table.item(row, 0)
        return int(id_item.text()) if id_item else None

    def on_row_double_clicked(self, row, column):
        id_item = self.table.item(row, 0)
        if id_item:
            user_id = int(id_item.text())
            self.edit_user(user_id)

    def show_context_menu(self, position):
        menu = QMenu()

        edit_action = menu.addAction("✏️ Upravit")
        permissions_action = menu.addAction("🔐 Oprávnění")
        history_action = menu.addAction("📊 Historie")
        menu.addSeparator()
        reset_pwd_action = menu.addAction("🔑 Reset hesla")
        menu.addSeparator()
        activate_action = menu.addAction("✅ Aktivovat")
        deactivate_action = menu.addAction("❌ Deaktivovat")
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ Smazat")

        action = menu.exec(self.table.mapToGlobal(position))

        user_id = self.get_selected_user_id()
        if not user_id:
            return

        if action == edit_action:
            self.edit_user(user_id)
        elif action == permissions_action:
            self.edit_user_permissions(user_id)
        elif action == history_action:
            self.show_user_history(user_id)
        elif action == reset_pwd_action:
            self.reset_user_password()
        elif action == activate_action:
            self.toggle_user_status(True)
        elif action == deactivate_action:
            self.toggle_user_status(False)
        elif action == delete_action:
            self.delete_user()

    def edit_user(self, user_id):
        uid = get_current_user_id()
        if uid and not has_permission(uid, "users", "edit"):
            QMessageBox.warning(self, "Přístup odepřen", "Nemáte oprávnění upravovat uživatele.")
            return

        from .user_detail import UserDetailDialog
        dialog = UserDetailDialog(user_id=user_id, parent=self)
        if dialog.exec():
            self.load_users()
            self.user_edited.emit(user_id)

    def edit_user_permissions(self, user_id):
        uid = get_current_user_id()
        if uid and not has_permission(uid, "users", "admin"):
            QMessageBox.warning(self, "Přístup odepřen", "Nemáte oprávnění měnit oprávnění.")
            return

        from .users_widgets import UserPermissionsDialog
        dialog = UserPermissionsDialog(user_id=user_id, parent=self)
        if dialog.exec():
            self.user_edited.emit(user_id)

    def show_user_history(self, user_id):
        from .users_widgets import UserHistoryDialog
        dialog = UserHistoryDialog(user_id=user_id, parent=self)
        dialog.exec()

    def toggle_user_status(self, activate):
        user_id = self.get_selected_user_id()
        if not user_id:
            QMessageBox.warning(self, "Upozornění", "Vyberte uživatele.")
            return

        uid = get_current_user_id()
        if uid and not has_permission(uid, "users", "edit"):
            QMessageBox.warning(self, "Přístup odepřen", "Nemáte oprávnění měnit stav uživatelů.")
            return

        if user_id == uid and not activate:
            QMessageBox.warning(self, "Upozornění", "Nemůžete deaktivovat sami sebe.")
            return

        status_text = "aktivovat" if activate else "deaktivovat"
        reply = QMessageBox.question(
            self,
            "Potvrzení",
            f"Opravdu chcete {status_text} tohoto uživatele?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            db.execute_query(
                "UPDATE users SET active = ?, updated_at = ? WHERE id = ?",
                (1 if activate else 0, datetime.now().isoformat(), user_id)
            )
            self.load_users()
            self.user_edited.emit(user_id)

    def reset_user_password(self):
        user_id = self.get_selected_user_id()
        if not user_id:
            QMessageBox.warning(self, "Upozornění", "Vyberte uživatele.")
            return

        uid = get_current_user_id()
        if uid and not has_permission(uid, "users", "admin"):
            QMessageBox.warning(self, "Přístup odepřen", "Nemáte oprávnění resetovat hesla.")
            return

        from .users_widgets import ResetPasswordDialog
        dialog = ResetPasswordDialog(user_id=user_id, parent=self)
        if dialog.exec():
            self.user_edited.emit(user_id)

    def delete_user(self):
        user_id = self.get_selected_user_id()
        if not user_id:
            QMessageBox.warning(self, "Upozornění", "Vyberte uživatele.")
            return

        uid = get_current_user_id()
        if uid and not has_permission(uid, "users", "delete"):
            QMessageBox.warning(self, "Přístup odepřen", "Nemáte oprávnění mazat uživatele.")
            return

        if user_id == uid:
            QMessageBox.warning(self, "Upozornění", "Nemůžete smazat sami sebe.")
            return

        user = db.fetch_one("SELECT username, full_name FROM users WHERE id = ?", (user_id,))
        if not user:
            return

        reply = QMessageBox.question(
            self,
            "Potvrzení smazání",
            f"Opravdu chcete SMAZAT uživatele:\n\n"
            f"Uživatelské jméno: {user['username']}\n"
            f"Celé jméno: {user['full_name']}\n\n"
            f"Tato akce je nevratná!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            db.execute_query("DELETE FROM user_permissions WHERE user_id = ?", (user_id,))
            db.execute_query("DELETE FROM users WHERE id = ?", (user_id,))

            self.load_users()
            self.user_deleted.emit(user_id)

    def refresh(self):
        self.load_users()
