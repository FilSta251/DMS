# -*- coding: utf-8 -*-
"""
Vizuální matice oprávnění
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QFrame, QComboBox, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from database_manager import db
from utils.utils_auth import get_current_user_id
from utils.utils_permissions import has_permission
import config


class PermissionsMatrix(QWidget):
    """Widget pro vizuální matici oprávnění"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_view = "role"

        self.init_ui()
        self.load_matrix()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        top_panel = self.create_top_panel()
        main_layout.addWidget(top_panel)

        self.create_matrix_table()
        main_layout.addWidget(self.matrix_table)

        legend_panel = self.create_legend_panel()
        main_layout.addWidget(legend_panel)

    def create_top_panel(self):
        panel = QFrame()
        panel.setObjectName("topPanel")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("🔐 Matice oprávnění")
        title.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        layout.addStretch()

        view_label = QLabel("Zobrazit:")
        layout.addWidget(view_label)

        self.cmb_view = QComboBox()
        self.cmb_view.addItem("📊 Podle rolí", "role")
        self.cmb_view.addItem("👤 Podle uživatelů", "user")
        self.cmb_view.addItem("📦 Podle modulů", "module")
        self.cmb_view.currentIndexChanged.connect(self.on_view_changed)
        layout.addWidget(self.cmb_view)

        self.cmb_filter = QComboBox()
        self.cmb_filter.setMinimumWidth(200)
        self.cmb_filter.currentIndexChanged.connect(self.load_matrix)
        layout.addWidget(self.cmb_filter)

        self.btn_refresh = QPushButton("🔄 Obnovit")
        self.btn_refresh.clicked.connect(self.load_matrix)
        layout.addWidget(self.btn_refresh)

        panel.setStyleSheet(f"""
            #topPanel {{
                background-color: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
            }}
            #sectionTitle {{
                color: {config.COLOR_PRIMARY};
            }}
            QComboBox {{
                padding: 8px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }}
        """)

        return panel

    def create_matrix_table(self):
        self.matrix_table = QTableWidget()
        self.matrix_table.setObjectName("matrixTable")

        self.matrix_table.setStyleSheet(f"""
            #matrixTable {{
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                background-color: white;
                gridline-color: #e0e0e0;
            }}
            #matrixTable::item {{
                padding: 5px;
            }}
            QHeaderView::section {{
                background-color: {config.COLOR_PRIMARY};
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
        """)

    def create_legend_panel(self):
        panel = QFrame()
        panel.setObjectName("legendPanel")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        legend_title = QLabel("Legenda:")
        legend_title.setStyleSheet("font-weight: bold;")
        layout.addWidget(legend_title)

        allowed_label = QLabel("✅ Povoleno")
        allowed_label.setStyleSheet(f"color: {config.COLOR_SUCCESS};")
        layout.addWidget(allowed_label)

        denied_label = QLabel("❌ Zakázáno")
        denied_label.setStyleSheet(f"color: {config.COLOR_DANGER};")
        layout.addWidget(denied_label)

        override_label = QLabel("⚠️ Uživatelská výjimka")
        override_label.setStyleSheet(f"color: {config.COLOR_WARNING};")
        layout.addWidget(override_label)

        layout.addStretch()

        panel.setStyleSheet("""
            #legendPanel {
                background-color: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
            }
        """)

        return panel

    def on_view_changed(self):
        self.current_view = self.cmb_view.currentData()
        self.load_filter_options()
        self.load_matrix()

    def load_filter_options(self):
        self.cmb_filter.clear()

        if self.current_view == "role":
            self.cmb_filter.addItem("Všechny role", None)
            roles = db.fetch_all("SELECT id, name FROM roles ORDER BY name")
            for role in roles:
                self.cmb_filter.addItem(role['name'], role['id'])

        elif self.current_view == "user":
            self.cmb_filter.addItem("Všichni uživatelé", None)
            users = db.fetch_all("SELECT id, username, full_name FROM users WHERE active = 1 ORDER BY full_name")
            for user in users:
                self.cmb_filter.addItem(f"{user['full_name']} ({user['username']})", user['id'])

        elif self.current_view == "module":
            self.cmb_filter.addItem("Všechny moduly", None)
            for module in config.MODULES:
                self.cmb_filter.addItem(f"{module['icon']} {module['name']}", module['id'])

    def load_matrix(self):
        if self.current_view == "role":
            self.load_role_matrix()
        elif self.current_view == "user":
            self.load_user_matrix()
        elif self.current_view == "module":
            self.load_module_matrix()

    def load_role_matrix(self):
        filter_id = self.cmb_filter.currentData()

        if filter_id:
            roles = db.fetch_all("SELECT id, name FROM roles WHERE id = ?", (filter_id,))
        else:
            roles = db.fetch_all("SELECT id, name FROM roles ORDER BY name")

        columns = ["Modul"] + [r['name'] for r in roles]
        self.matrix_table.setColumnCount(len(columns))
        self.matrix_table.setHorizontalHeaderLabels(columns)

        header = self.matrix_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            self.matrix_table.setColumnWidth(i, 120)

        modules = config.MODULES
        actions = ['view', 'create', 'edit', 'delete', 'admin']

        self.matrix_table.setRowCount(0)

        for module in modules:
            for action in actions:
                row = self.matrix_table.rowCount()
                self.matrix_table.insertRow(row)

                action_names = {
                    'view': 'Zobrazit',
                    'create': 'Vytvořit',
                    'edit': 'Upravit',
                    'delete': 'Smazat',
                    'admin': 'Admin'
                }

                module_text = f"{module['icon']} {module['name']} - {action_names[action]}"
                module_item = QTableWidgetItem(module_text)
                module_item.setFlags(module_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.matrix_table.setItem(row, 0, module_item)

                for col, role in enumerate(roles, start=1):
                    perm = db.fetch_one(
                        "SELECT id FROM permissions WHERE module_id = ? AND action = ?",
                        (module['id'], action)
                    )

                    if perm:
                        rp = db.fetch_one(
                            "SELECT allowed FROM role_permissions WHERE role_id = ? AND permission_id = ?",
                            (role['id'], perm['id'])
                        )
                        is_allowed = bool(rp and rp['allowed'])
                    else:
                        is_allowed = False

                    status_text = "✅" if is_allowed else "❌"
                    status_item = QTableWidgetItem(status_text)
                    status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    if is_allowed:
                        status_item.setForeground(QColor(config.COLOR_SUCCESS))
                    else:
                        status_item.setForeground(QColor(config.COLOR_DANGER))

                    self.matrix_table.setItem(row, col, status_item)

    def load_user_matrix(self):
        filter_id = self.cmb_filter.currentData()

        if filter_id:
            users = db.fetch_all(
                "SELECT id, username, full_name, role FROM users WHERE id = ?",
                (filter_id,)
            )
        else:
            users = db.fetch_all(
                "SELECT id, username, full_name, role FROM users WHERE active = 1 ORDER BY full_name LIMIT 10"
            )

        columns = ["Modul"] + [u['username'] for u in users]
        self.matrix_table.setColumnCount(len(columns))
        self.matrix_table.setHorizontalHeaderLabels(columns)

        header = self.matrix_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            self.matrix_table.setColumnWidth(i, 120)

        modules = config.MODULES
        actions = ['view', 'create', 'edit', 'delete', 'admin']

        self.matrix_table.setRowCount(0)

        for module in modules:
            for action in actions:
                row = self.matrix_table.rowCount()
                self.matrix_table.insertRow(row)

                action_names = {
                    'view': 'Zobrazit',
                    'create': 'Vytvořit',
                    'edit': 'Upravit',
                    'delete': 'Smazat',
                    'admin': 'Admin'
                }

                module_text = f"{module['icon']} {module['name']} - {action_names[action]}"
                module_item = QTableWidgetItem(module_text)
                module_item.setFlags(module_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.matrix_table.setItem(row, 0, module_item)

                for col, user in enumerate(users, start=1):
                    has_perm = has_permission(user['id'], module['id'], action)

                    status_text = "✅" if has_perm else "❌"
                    status_item = QTableWidgetItem(status_text)
                    status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    if has_perm:
                        status_item.setForeground(QColor(config.COLOR_SUCCESS))
                    else:
                        status_item.setForeground(QColor(config.COLOR_DANGER))

                    self.matrix_table.setItem(row, col, status_item)

    def load_module_matrix(self):
        filter_id = self.cmb_filter.currentData()

        if filter_id:
            modules = [m for m in config.MODULES if m['id'] == filter_id]
        else:
            modules = config.MODULES

        roles = db.fetch_all("SELECT id, name FROM roles ORDER BY name")

        columns = ["Akce"] + [r['name'] for r in roles]
        self.matrix_table.setColumnCount(len(columns))
        self.matrix_table.setHorizontalHeaderLabels(columns)

        header = self.matrix_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            self.matrix_table.setColumnWidth(i, 120)

        actions = ['view', 'create', 'edit', 'delete', 'admin']
        action_names = {
            'view': '👁️ Zobrazit',
            'create': '➕ Vytvořit',
            'edit': '✏️ Upravit',
            'delete': '🗑️ Smazat',
            'admin': '⚙️ Admin'
        }

        self.matrix_table.setRowCount(0)

        for module in modules:
            header_row = self.matrix_table.rowCount()
            self.matrix_table.insertRow(header_row)
            header_item = QTableWidgetItem(f"{module['icon']} {module['name']}")
            header_item.setFlags(header_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            font = header_item.font()
            font.setBold(True)
            header_item.setFont(font)
            header_item.setBackground(QColor("#e0e0e0"))
            self.matrix_table.setItem(header_row, 0, header_item)

            for col in range(1, len(columns)):
                empty_item = QTableWidgetItem("")
                empty_item.setBackground(QColor("#e0e0e0"))
                empty_item.setFlags(empty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.matrix_table.setItem(header_row, col, empty_item)

            for action in actions:
                row = self.matrix_table.rowCount()
                self.matrix_table.insertRow(row)

                action_item = QTableWidgetItem(f"  {action_names[action]}")
                action_item.setFlags(action_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.matrix_table.setItem(row, 0, action_item)

                for col, role in enumerate(roles, start=1):
                    perm = db.fetch_one(
                        "SELECT id FROM permissions WHERE module_id = ? AND action = ?",
                        (module['id'], action)
                    )

                    if perm:
                        rp = db.fetch_one(
                            "SELECT allowed FROM role_permissions WHERE role_id = ? AND permission_id = ?",
                            (role['id'], perm['id'])
                        )
                        is_allowed = bool(rp and rp['allowed'])
                    else:
                        is_allowed = False

                    status_text = "✅" if is_allowed else "❌"
                    status_item = QTableWidgetItem(status_text)
                    status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    if is_allowed:
                        status_item.setForeground(QColor(config.COLOR_SUCCESS))
                    else:
                        status_item.setForeground(QColor(config.COLOR_DANGER))

                    self.matrix_table.setItem(row, col, status_item)

    def refresh(self):
        self.load_filter_options()
        self.load_matrix()
