# -*- coding: utf-8 -*-
"""
Správa oprávnění a rolí
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QDialog, QFormLayout, QLineEdit, QComboBox,
    QCheckBox, QMessageBox, QHeaderView, QFrame, QGroupBox, QTreeWidget,
    QTreeWidgetItem, QTabWidget, QScrollArea, QTextEdit, QColorDialog,
    QSplitter
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont, QColor, QBrush
from database_manager import db
import config
import json


class PermissionsSettingsWidget(QWidget):
    """Widget pro správu oprávnění a rolí"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_roles()
        self.load_audit_log()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Záložky
        tabs = QTabWidget()

        # Záložka: Role
        tabs.addTab(self.create_roles_tab(), "🎭 Role")

        # Záložka: Matice oprávnění
        tabs.addTab(self.create_permissions_matrix_tab(), "📊 Matice oprávnění")

        # Záložka: Audit log
        tabs.addTab(self.create_audit_log_tab(), "📋 Audit log")

        layout.addWidget(tabs)

        self.set_styles()

    def create_roles_tab(self):
        """Záložka pro správu rolí"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Horní panel
        top_panel = QHBoxLayout()

        add_role_btn = QPushButton("➕ Nová role")
        add_role_btn.clicked.connect(self.add_role)
        add_role_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_role_btn.setObjectName("primaryButton")

        reset_btn = QPushButton("🔄 Obnovit výchozí")
        reset_btn.clicked.connect(self.reset_default_roles)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        top_panel.addWidget(add_role_btn)
        top_panel.addWidget(reset_btn)
        top_panel.addStretch()

        layout.addLayout(top_panel)

        # Splitter pro role a oprávnění
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Seznam rolí
        roles_frame = QFrame()
        roles_frame.setObjectName("rolesFrame")
        roles_layout = QVBoxLayout(roles_frame)

        roles_label = QLabel("📋 Definované role:")
        roles_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        roles_layout.addWidget(roles_label)

        self.roles_table = QTableWidget()
        self.roles_table.setColumnCount(4)
        self.roles_table.setHorizontalHeaderLabels(["Role", "Popis", "Uživatelů", "Barva"])

        header = self.roles_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)

        self.roles_table.setColumnWidth(2, 80)
        self.roles_table.setColumnWidth(3, 80)

        self.roles_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.roles_table.setAlternatingRowColors(True)
        self.roles_table.itemSelectionChanged.connect(self.on_role_selected)

        roles_layout.addWidget(self.roles_table)

        # Tlačítka akcí
        actions_layout = QHBoxLayout()

        edit_btn = QPushButton("✏️ Upravit")
        edit_btn.clicked.connect(self.edit_role)
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        delete_btn = QPushButton("🗑️ Smazat")
        delete_btn.clicked.connect(self.delete_role)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setObjectName("dangerButton")

        actions_layout.addWidget(edit_btn)
        actions_layout.addWidget(delete_btn)
        actions_layout.addStretch()

        roles_layout.addLayout(actions_layout)

        splitter.addWidget(roles_frame)

        # Oprávnění vybrané role
        permissions_frame = QFrame()
        permissions_frame.setObjectName("permissionsFrame")
        permissions_layout = QVBoxLayout(permissions_frame)

        self.permissions_label = QLabel("🔐 Oprávnění role:")
        self.permissions_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        permissions_layout.addWidget(self.permissions_label)

        self.permissions_tree = QTreeWidget()
        self.permissions_tree.setHeaderLabels(["Modul / Akce", "Povoleno"])
        self.permissions_tree.setAlternatingRowColors(True)
        self.permissions_tree.itemChanged.connect(self.on_permission_changed)

        permissions_layout.addWidget(self.permissions_tree)

        save_perm_btn = QPushButton("💾 Uložit oprávnění")
        save_perm_btn.clicked.connect(self.save_permissions)
        save_perm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_perm_btn.setObjectName("saveButton")

        permissions_layout.addWidget(save_perm_btn)

        splitter.addWidget(permissions_frame)
        splitter.setSizes([400, 600])

        layout.addWidget(splitter)

        return widget

    def create_permissions_matrix_tab(self):
        """Záložka pro matici oprávnění"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        info_label = QLabel("📊 Přehled oprávnění všech rolí:")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(info_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.matrix_table = QTableWidget()
        self.matrix_table.setAlternatingRowColors(True)

        scroll.setWidget(self.matrix_table)
        layout.addWidget(scroll)

        refresh_btn = QPushButton("🔄 Obnovit matici")
        refresh_btn.clicked.connect(self.refresh_matrix)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(refresh_btn)

        return widget

    def create_audit_log_tab(self):
        """Záložka pro audit log"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Filtry
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Uživatel:"))
        self.audit_user_filter = QComboBox()
        self.audit_user_filter.addItem("Všichni", None)
        filter_layout.addWidget(self.audit_user_filter)

        filter_layout.addWidget(QLabel("Akce:"))
        self.audit_action_filter = QComboBox()
        self.audit_action_filter.addItems([
            "Všechny akce",
            "Přihlášení",
            "Odhlášení",
            "Vytvoření",
            "Úprava",
            "Smazání",
            "Export",
            "Import"
        ])
        filter_layout.addWidget(self.audit_action_filter)

        filter_btn = QPushButton("🔍 Filtrovat")
        filter_btn.clicked.connect(self.filter_audit_log)
        filter_layout.addWidget(filter_btn)

        export_btn = QPushButton("📤 Export")
        export_btn.clicked.connect(self.export_audit_log)
        filter_layout.addWidget(export_btn)

        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # Tabulka audit logu
        self.audit_table = QTableWidget()
        self.audit_table.setColumnCount(5)
        self.audit_table.setHorizontalHeaderLabels([
            "Datum a čas", "Uživatel", "Akce", "Modul", "Detail"
        ])

        header = self.audit_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        self.audit_table.setColumnWidth(0, 150)
        self.audit_table.setColumnWidth(1, 120)
        self.audit_table.setColumnWidth(2, 100)
        self.audit_table.setColumnWidth(3, 120)

        self.audit_table.setAlternatingRowColors(True)
        self.audit_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.audit_table)

        return widget

    def load_roles(self):
        """Načtení rolí z databáze"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            # Kontrola, zda existuje tabulka roles
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='roles'
            """)

            if not cursor.fetchone():
                self.create_roles_table()
                self.insert_default_roles()

            cursor.execute("""
                SELECT r.id, r.name, r.description, r.color,
                       (SELECT COUNT(*) FROM users u WHERE u.role = r.name)
                FROM roles r
                ORDER BY r.id
            """)

            rows = cursor.fetchall()
            self.roles_table.setRowCount(len(rows))

            for i, row in enumerate(rows):
                role_id, name, description, color, user_count = row

                name_item = QTableWidgetItem(name)
                name_item.setData(Qt.ItemDataRole.UserRole, role_id)
                self.roles_table.setItem(i, 0, name_item)

                self.roles_table.setItem(i, 1, QTableWidgetItem(description or ""))
                self.roles_table.setItem(i, 2, QTableWidgetItem(str(user_count)))

                color_item = QTableWidgetItem()
                if color:
                    color_item.setBackground(QBrush(QColor(color)))
                self.roles_table.setItem(i, 3, color_item)

            # Načtení uživatelů do filtru audit logu
            cursor.execute("SELECT DISTINCT username FROM users ORDER BY username")
            self.audit_user_filter.clear()
            self.audit_user_filter.addItem("Všichni", None)
            for row in cursor.fetchall():
                self.audit_user_filter.addItem(row[0], row[0])

            self.refresh_matrix()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst role:\n{str(e)}")

    def create_roles_table(self):
        """Vytvoření tabulky roles"""
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                color TEXT,
                permissions TEXT,
                is_system INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                username TEXT,
                action TEXT,
                module TEXT,
                detail TEXT,
                ip_address TEXT
            )
        """)

        conn.commit()

    def insert_default_roles(self):
        """Vložení výchozích rolí"""
        conn = db.get_connection()
        cursor = conn.cursor()

        default_roles = [
            {
                "name": "Administrátor",
                "description": "Plný přístup ke všemu",
                "color": "#e74c3c",
                "permissions": {
                    "dashboard": ["view"],
                    "customers": ["view", "create", "edit", "delete"],
                    "vehicles": ["view", "create", "edit", "delete"],
                    "orders": ["view", "create", "edit", "delete"],
                    "warehouse": ["view", "create", "edit", "delete", "inventory"],
                    "administration": ["view", "create", "edit", "delete"],
                    "codebooks": ["view", "create", "edit", "delete"],
                    "calendar": ["view", "create", "edit", "delete"],
                    "management": ["view", "reports", "analytics"],
                    "users": ["view", "create", "edit", "delete"],
                    "settings": ["view", "edit", "backup", "restore"],
                    "system": ["admin", "backup", "restore", "delete_data"]
                },
                "is_system": 1
            },
            {
                "name": "Manažer",
                "description": "Správa zakázek a reporty",
                "color": "#3498db",
                "permissions": {
                    "dashboard": ["view"],
                    "customers": ["view", "create", "edit", "delete"],
                    "vehicles": ["view", "create", "edit", "delete"],
                    "orders": ["view", "create", "edit", "delete"],
                    "warehouse": ["view", "create", "edit"],
                    "administration": ["view"],
                    "codebooks": ["view", "edit"],
                    "calendar": ["view", "create", "edit", "delete"],
                    "management": ["view", "reports", "analytics"]
                },
                "is_system": 1
            },
            {
                "name": "Mechanik",
                "description": "Práce na zakázkách",
                "color": "#f39c12",
                "permissions": {
                    "dashboard": ["view"],
                    "customers": ["view"],
                    "vehicles": ["view"],
                    "orders": ["view", "edit_own"],
                    "warehouse": ["view", "issue"],
                    "calendar": ["view"]
                },
                "is_system": 1
            },
            {
                "name": "Recepce",
                "description": "Příjem zákazníků a zakázek",
                "color": "#27ae60",
                "permissions": {
                    "dashboard": ["view"],
                    "customers": ["view", "create", "edit"],
                    "vehicles": ["view", "create", "edit"],
                    "orders": ["view", "create"],
                    "calendar": ["view", "create", "edit", "delete"]
                },
                "is_system": 1
            },
            {
                "name": "Účetní",
                "description": "Fakturace a finance",
                "color": "#9b59b6",
                "permissions": {
                    "dashboard": ["view"],
                    "customers": ["view"],
                    "orders": ["view"],
                    "administration": ["view", "create", "edit", "delete"],
                    "management": ["view", "reports"]
                },
                "is_system": 1
            },
            {
                "name": "Sklad",
                "description": "Správa skladu",
                "color": "#1abc9c",
                "permissions": {
                    "dashboard": ["view"],
                    "warehouse": ["view", "create", "edit", "delete", "inventory"],
                    "codebooks": ["view"]
                },
                "is_system": 1
            }
        ]

        for role in default_roles:
            cursor.execute("""
                INSERT OR IGNORE INTO roles (name, description, color, permissions, is_system)
                VALUES (?, ?, ?, ?, ?)
            """, (
                role["name"],
                role["description"],
                role["color"],
                json.dumps(role["permissions"], ensure_ascii=False),
                role["is_system"]
            ))

        conn.commit()

    def on_role_selected(self):
        """Při výběru role"""
        selected = self.roles_table.selectedItems()
        if not selected:
            self.permissions_tree.clear()
            return

        role_id = self.roles_table.item(self.roles_table.currentRow(), 0).data(Qt.ItemDataRole.UserRole)
        role_name = self.roles_table.item(self.roles_table.currentRow(), 0).text()

        self.permissions_label.setText(f"🔐 Oprávnění role: {role_name}")
        self.load_role_permissions(role_id)

    def load_role_permissions(self, role_id):
        """Načtení oprávnění role"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT permissions FROM roles WHERE id = ?", (role_id,))
            row = cursor.fetchone()

            if row and row[0]:
                permissions = json.loads(row[0])
            else:
                permissions = {}

            self.permissions_tree.blockSignals(True)
            self.permissions_tree.clear()

            # Definice modulů a akcí
            modules = {
                "dashboard": ("🏠 Úvodní stránka", ["view"]),
                "customers": ("👥 Zákazníci", ["view", "create", "edit", "delete"]),
                "vehicles": ("🏍️ Motorky", ["view", "create", "edit", "delete"]),
                "orders": ("📋 Zakázky", ["view", "create", "edit", "delete", "edit_own"]),
                "warehouse": ("📦 Sklad", ["view", "create", "edit", "delete", "inventory", "issue"]),
                "administration": ("💼 Administrativa", ["view", "create", "edit", "delete"]),
                "codebooks": ("📚 Číselníky", ["view", "create", "edit", "delete"]),
                "calendar": ("📅 Kalendář", ["view", "create", "edit", "delete"]),
                "management": ("📊 Management", ["view", "reports", "analytics"]),
                "users": ("👤 Uživatelé", ["view", "create", "edit", "delete"]),
                "settings": ("⚙️ Nastavení", ["view", "edit", "backup", "restore"]),
                "system": ("🔧 Systém", ["admin", "backup", "restore", "delete_data"])
            }

            action_names = {
                "view": "Zobrazit",
                "create": "Vytvořit",
                "edit": "Upravit",
                "delete": "Smazat",
                "edit_own": "Upravit vlastní",
                "inventory": "Inventura",
                "issue": "Výdej",
                "reports": "Reporty",
                "analytics": "Analýzy",
                "backup": "Záloha",
                "restore": "Obnovení",
                "admin": "Administrace",
                "delete_data": "Mazání dat"
            }

            for module_id, (module_name, actions) in modules.items():
                module_item = QTreeWidgetItem(self.permissions_tree, [module_name, ""])
                module_item.setData(0, Qt.ItemDataRole.UserRole, module_id)
                module_item.setFlags(module_item.flags() | Qt.ItemFlag.ItemIsAutoTristate)

                module_perms = permissions.get(module_id, [])

                for action in actions:
                    action_item = QTreeWidgetItem(module_item, [action_names.get(action, action), ""])
                    action_item.setData(0, Qt.ItemDataRole.UserRole, action)
                    action_item.setFlags(action_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

                    if action in module_perms:
                        action_item.setCheckState(1, Qt.CheckState.Checked)
                    else:
                        action_item.setCheckState(1, Qt.CheckState.Unchecked)

                module_item.setExpanded(True)

            self.permissions_tree.blockSignals(False)

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst oprávnění:\n{str(e)}")

    def on_permission_changed(self, item, column):
        """Při změně oprávnění"""
        # Zde můžeme přidat logiku pro automatické závislosti
        pass

    def save_permissions(self):
        """Uložení oprávnění"""
        selected = self.roles_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Upozornění", "Vyberte roli pro uložení oprávnění.")
            return

        role_id = self.roles_table.item(self.roles_table.currentRow(), 0).data(Qt.ItemDataRole.UserRole)

        permissions = {}

        root = self.permissions_tree.invisibleRootItem()
        for i in range(root.childCount()):
            module_item = root.child(i)
            module_id = module_item.data(0, Qt.ItemDataRole.UserRole)
            module_perms = []

            for j in range(module_item.childCount()):
                action_item = module_item.child(j)
                if action_item.checkState(1) == Qt.CheckState.Checked:
                    action = action_item.data(0, Qt.ItemDataRole.UserRole)
                    module_perms.append(action)

            if module_perms:
                permissions[module_id] = module_perms

        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE roles SET permissions = ? WHERE id = ?
            """, (json.dumps(permissions, ensure_ascii=False), role_id))

            conn.commit()

            QMessageBox.information(self, "Uloženo", "Oprávnění byla uložena.")
            self.refresh_matrix()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit oprávnění:\n{str(e)}")

    def refresh_matrix(self):
        """Obnovení matice oprávnění"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT name, permissions FROM roles ORDER BY id")
            roles = cursor.fetchall()

            if not roles:
                return

            # Definice všech akcí
            all_actions = [
                ("Zakázky - Číst", "orders", "view"),
                ("Zakázky - Vytvořit", "orders", "create"),
                ("Zakázky - Upravit", "orders", "edit"),
                ("Zakázky - Smazat", "orders", "delete"),
                ("Zákazníci - Vše", "customers", "all"),
                ("Vozidla - Vše", "vehicles", "all"),
                ("Sklad - Vše", "warehouse", "all"),
                ("Fakturace - Vše", "administration", "all"),
                ("Management - Reporty", "management", "reports"),
                ("Nastavení", "settings", "view"),
                ("Systém - Admin", "system", "admin")
            ]

            self.matrix_table.setRowCount(len(all_actions))
            self.matrix_table.setColumnCount(len(roles) + 1)

            headers = ["Akce"] + [r[0] for r in roles]
            self.matrix_table.setHorizontalHeaderLabels(headers)

            for i, (action_name, module, action) in enumerate(all_actions):
                self.matrix_table.setItem(i, 0, QTableWidgetItem(action_name))

                for j, (role_name, perms_json) in enumerate(roles):
                    perms = json.loads(perms_json) if perms_json else {}

                    if action == "all":
                        has_perm = module in perms and len(perms.get(module, [])) >= 3
                    else:
                        has_perm = action in perms.get(module, [])

                    if has_perm:
                        item = QTableWidgetItem("✅")
                        item.setForeground(QBrush(QColor(config.COLOR_SUCCESS)))
                    else:
                        item = QTableWidgetItem("❌")
                        item.setForeground(QBrush(QColor(config.COLOR_DANGER)))

                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.matrix_table.setItem(i, j + 1, item)

            self.matrix_table.resizeColumnsToContents()

        except Exception as e:
            print(f"Chyba při obnovení matice: {e}")

    def add_role(self):
        """Přidání nové role"""
        dialog = RoleDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_roles()

    def edit_role(self):
        """Úprava role"""
        selected = self.roles_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Upozornění", "Vyberte roli pro úpravu.")
            return

        role_id = self.roles_table.item(self.roles_table.currentRow(), 0).data(Qt.ItemDataRole.UserRole)
        dialog = RoleDialog(self, role_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_roles()

    def delete_role(self):
        """Smazání role"""
        selected = self.roles_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Upozornění", "Vyberte roli pro smazání.")
            return

        role_id = self.roles_table.item(self.roles_table.currentRow(), 0).data(Qt.ItemDataRole.UserRole)
        role_name = self.roles_table.item(self.roles_table.currentRow(), 0).text()

        # Kontrola systémové role
        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT is_system FROM roles WHERE id = ?", (role_id,))
            if cursor.fetchone()[0]:
                QMessageBox.warning(self, "Nelze smazat", "Systémovou roli nelze smazat.")
                return

            # Kontrola uživatelů s touto rolí
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = ?", (role_name,))
            if cursor.fetchone()[0] > 0:
                QMessageBox.warning(
                    self,
                    "Nelze smazat",
                    "Roli nelze smazat, protože je přiřazena uživatelům."
                )
                return

        except Exception:
            pass

        reply = QMessageBox.question(
            self,
            "Smazat roli",
            f"Opravdu chcete smazat roli '{role_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                cursor.execute("DELETE FROM roles WHERE id = ?", (role_id,))
                conn.commit()
                self.load_roles()
                QMessageBox.information(self, "Hotovo", "Role byla smazána.")
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat roli:\n{str(e)}")

    def reset_default_roles(self):
        """Obnovení výchozích rolí"""
        reply = QMessageBox.question(
            self,
            "Obnovit výchozí role",
            "Opravdu chcete obnovit výchozí role?\n\n"
            "Tato akce přepíše oprávnění systémových rolí.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = db.get_connection()
                cursor = conn.cursor()

                cursor.execute("DELETE FROM roles WHERE is_system = 1")
                conn.commit()

                self.insert_default_roles()
                self.load_roles()

                QMessageBox.information(self, "Hotovo", "Výchozí role byly obnoveny.")
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se obnovit role:\n{str(e)}")

    def load_audit_log(self):
        """Načtení audit logu"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT timestamp, username, action, module, detail
                FROM audit_log
                ORDER BY timestamp DESC
                LIMIT 500
            """)

            rows = cursor.fetchall()
            self.audit_table.setRowCount(len(rows))

            for i, row in enumerate(rows):
                self.audit_table.setItem(i, 0, QTableWidgetItem(row[0] or ""))
                self.audit_table.setItem(i, 1, QTableWidgetItem(row[1] or ""))
                self.audit_table.setItem(i, 2, QTableWidgetItem(row[2] or ""))
                self.audit_table.setItem(i, 3, QTableWidgetItem(row[3] or ""))
                self.audit_table.setItem(i, 4, QTableWidgetItem(row[4] or ""))

        except Exception as e:
            print(f"Chyba při načítání audit logu: {e}")

    def filter_audit_log(self):
        """Filtrování audit logu"""
        # TODO: Implementovat filtrování
        self.load_audit_log()

    def export_audit_log(self):
        """Export audit logu"""
        QMessageBox.information(
            self,
            "Export",
            "Export audit logu bude implementován v další verzi."
        )

    def save_settings(self):
        """Uložení nastavení"""
        pass

    def get_settings(self):
        """Získání nastavení"""
        return {}

    def set_settings(self, settings):
        """Nastavení hodnot"""
        pass

    def refresh(self):
        """Obnovení"""
        self.load_roles()
        self.load_audit_log()

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                gridline-color: #ecf0f1;
            }}

            QTableWidget::item {{
                padding: 8px;
            }}

            QTableWidget::item:selected {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
            }}

            QHeaderView::section {{
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }}

            QTreeWidget {{
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }}

            QTreeWidget::item {{
                padding: 5px;
            }}

            #rolesFrame, #permissionsFrame {{
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                padding: 10px;
            }}

            QPushButton {{
                padding: 8px 16px;
                border-radius: 4px;
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
            }}

            QPushButton:hover {{
                background-color: #d5dbdb;
            }}

            #primaryButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
            }}

            #primaryButton:hover {{
                background-color: #2980b9;
            }}

            #dangerButton {{
                background-color: {config.COLOR_DANGER};
                color: white;
                border: none;
            }}

            #dangerButton:hover {{
                background-color: #c0392b;
            }}

            #saveButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                border: none;
                font-weight: bold;
            }}

            #saveButton:hover {{
                background-color: #229954;
            }}
        """)


class RoleDialog(QDialog):
    """Dialog pro vytvoření/úpravu role"""

    def __init__(self, parent=None, role_id=None):
        super().__init__(parent)
        self.role_id = role_id
        self.color = "#3498db"
        self.setWindowTitle("Nová role" if not role_id else "Upravit roli")
        self.setMinimumWidth(400)
        self.init_ui()
        if role_id:
            self.load_role_data()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Název role *")
        form.addRow("Název *:", self.name_input)

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Popis role")
        form.addRow("Popis:", self.description_input)

        color_layout = QHBoxLayout()
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(60, 30)
        self.color_preview.setStyleSheet(f"background-color: {self.color}; border-radius: 4px;")

        color_btn = QPushButton("🎨 Vybrat barvu")
        color_btn.clicked.connect(self.choose_color)

        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(color_btn)
        color_layout.addStretch()

        form.addRow("Barva:", color_layout)

        layout.addLayout(form)

        # Tlačítka
        buttons_layout = QHBoxLayout()

        save_btn = QPushButton("💾 Uložit")
        save_btn.clicked.connect(self.save_role)

        cancel_btn = QPushButton("❌ Zrušit")
        cancel_btn.clicked.connect(self.reject)

        buttons_layout.addStretch()
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

    def load_role_data(self):
        """Načtení dat role"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT name, description, color FROM roles WHERE id = ?", (self.role_id,))
            row = cursor.fetchone()

            if row:
                self.name_input.setText(row[0] or "")
                self.description_input.setText(row[1] or "")
                if row[2]:
                    self.color = row[2]
                    self.color_preview.setStyleSheet(f"background-color: {self.color}; border-radius: 4px;")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst data:\n{str(e)}")

    def choose_color(self):
        """Výběr barvy"""
        color = QColorDialog.getColor(QColor(self.color), self)
        if color.isValid():
            self.color = color.name()
            self.color_preview.setStyleSheet(f"background-color: {self.color}; border-radius: 4px;")

    def save_role(self):
        """Uložení role"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Chyba", "Název role je povinný.")
            return

        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            if self.role_id:
                cursor.execute("""
                    UPDATE roles SET name = ?, description = ?, color = ?
                    WHERE id = ?
                """, (
                    self.name_input.text(),
                    self.description_input.text(),
                    self.color,
                    self.role_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO roles (name, description, color, permissions)
                    VALUES (?, ?, ?, ?)
                """, (
                    self.name_input.text(),
                    self.description_input.text(),
                    self.color,
                    "{}"
                ))

            conn.commit()
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit roli:\n{str(e)}")
