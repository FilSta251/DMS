# -*- coding: utf-8 -*-
"""
Hlavní modul správy uživatelů
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QPushButton, QLabel, QFrame, QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime
from database_manager import db
from utils_auth import get_current_user_id, get_current_username
from utils_permissions import has_permission
import config


class UsersModule(QWidget):
    """Hlavní widget modulu správy uživatelů"""

    user_updated = pyqtSignal()
    role_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_section = "users_list"

        self.init_ui()
        self.load_statistics()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        self.create_top_panel(main_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        splitter.setSizes([250, 1000])

        main_layout.addWidget(splitter)

        self.create_bottom_panel(main_layout)

        self.set_styles()

    def create_top_panel(self, parent_layout):
        top_frame = QFrame()
        top_frame.setObjectName("topPanel")
        top_frame.setFixedHeight(70)
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(15, 10, 15, 10)

        title_label = QLabel("👤 Správa uživatelů")
        title_label.setObjectName("moduleTitle")
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        title_label.setFont(font)
        top_layout.addWidget(title_label)

        top_layout.addStretch()

        actions_frame = QFrame()
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(10)

        self.btn_new_user = QPushButton("➕ Nový uživatel")
        self.btn_new_user.setObjectName("primaryButton")
        self.btn_new_user.setFixedHeight(40)
        self.btn_new_user.clicked.connect(self.create_new_user)

        uid = get_current_user_id()
        if uid and not has_permission(uid, "users", "create"):
            self.btn_new_user.setEnabled(False)
            self.btn_new_user.setToolTip("Nemáte oprávnění vytvářet uživatele")

        actions_layout.addWidget(self.btn_new_user)

        self.btn_export = QPushButton("📤 Export")
        self.btn_export.setObjectName("actionButton")
        self.btn_export.setFixedHeight(40)
        self.btn_export.clicked.connect(self.export_users)
        actions_layout.addWidget(self.btn_export)

        self.btn_import = QPushButton("📥 Import")
        self.btn_import.setObjectName("actionButton")
        self.btn_import.setFixedHeight(40)
        self.btn_import.clicked.connect(self.import_users)
        actions_layout.addWidget(self.btn_import)

        top_layout.addWidget(actions_frame)

        parent_layout.addWidget(top_frame)

    def create_left_panel(self):
        left_frame = QFrame()
        left_frame.setObjectName("leftPanel")
        left_frame.setMinimumWidth(230)
        left_frame.setMaximumWidth(300)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)

        nav_label = QLabel("📂 Sekce")
        nav_label.setObjectName("sectionLabel")
        left_layout.addWidget(nav_label)

        self.nav_buttons = {}

        sections = [
            ("users_list", "👤 Seznam uživatelů"),
            ("roles", "🎭 Správa rolí"),
            ("permissions", "🔐 Oprávnění"),
            ("audit", "📊 Audit log"),
            ("password_policy", "🔒 Politika hesel"),
            ("my_profile", "👤⚙️ Můj profil"),
        ]

        for section_id, section_name in sections:
            btn = QPushButton(section_name)
            btn.setObjectName("navSectionButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, s=section_id: self.switch_section(s))
            self.nav_buttons[section_id] = btn
            left_layout.addWidget(btn)

        self.nav_buttons["users_list"].setChecked(True)

        left_layout.addSpacing(20)

        stats_label = QLabel("📊 Statistiky")
        stats_label.setObjectName("sectionLabel")
        left_layout.addWidget(stats_label)

        self.stats_frame = QFrame()
        self.stats_frame.setObjectName("statsFrame")
        stats_layout = QVBoxLayout(self.stats_frame)
        stats_layout.setContentsMargins(10, 10, 10, 10)
        stats_layout.setSpacing(8)

        self.lbl_total_users = QLabel("Celkem uživatelů: 0")
        self.lbl_active_users = QLabel("Aktivních: 0")
        self.lbl_inactive_users = QLabel("Neaktivních: 0")
        self.lbl_roles_count = QLabel("Počet rolí: 0")
        self.lbl_last_login = QLabel("Poslední přihlášení: --")

        for lbl in [self.lbl_total_users, self.lbl_active_users,
                    self.lbl_inactive_users, self.lbl_roles_count,
                    self.lbl_last_login]:
            lbl.setObjectName("statLabel")
            stats_layout.addWidget(lbl)

        left_layout.addWidget(self.stats_frame)

        left_layout.addStretch()

        current_user_frame = QFrame()
        current_user_frame.setObjectName("currentUserFrame")
        current_user_layout = QVBoxLayout(current_user_frame)
        current_user_layout.setContentsMargins(10, 10, 10, 10)

        current_user_label = QLabel("🔑 Přihlášen jako:")
        current_user_label.setObjectName("currentUserTitle")
        current_user_layout.addWidget(current_user_label)

        username = get_current_username() or "Neznámý"
        self.lbl_current_user = QLabel(f"👤 {username}")
        self.lbl_current_user.setObjectName("currentUserName")
        font = QFont()
        font.setBold(True)
        self.lbl_current_user.setFont(font)
        current_user_layout.addWidget(self.lbl_current_user)

        left_layout.addWidget(current_user_frame)

        return left_frame

    def create_right_panel(self):
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentStack")

        from .users_list import UsersList
        self.users_list_view = UsersList(self)
        self.users_list_view.user_selected.connect(self.on_user_selected)
        self.users_list_view.user_edited.connect(self.on_user_edited)
        self.users_list_view.user_deleted.connect(self.on_user_deleted)
        self.content_stack.addWidget(self.users_list_view)

        from .roles_manager import RolesManager
        self.roles_view = RolesManager(self)
        self.roles_view.role_updated.connect(self.on_role_updated)
        self.content_stack.addWidget(self.roles_view)

        from .permissions_matrix import PermissionsMatrix
        self.permissions_view = PermissionsMatrix(self)
        self.content_stack.addWidget(self.permissions_view)

        from .audit_log import AuditLog
        self.audit_view = AuditLog(self)
        self.content_stack.addWidget(self.audit_view)

        from .password_policy import PasswordPolicySettings
        self.password_policy_view = PasswordPolicySettings(self)
        self.content_stack.addWidget(self.password_policy_view)

        from .user_profile import UserProfile
        self.my_profile_view = UserProfile(self)
        self.my_profile_view.profile_updated.connect(self.on_profile_updated)
        self.content_stack.addWidget(self.my_profile_view)

        return self.content_stack

    def create_bottom_panel(self, parent_layout):
        bottom_frame = QFrame()
        bottom_frame.setObjectName("bottomPanel")
        bottom_frame.setFixedHeight(50)
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(15, 5, 15, 5)

        self.lbl_section_info = QLabel("Sekce: Seznam uživatelů")
        self.lbl_section_info.setObjectName("bottomStat")

        self.lbl_last_update = QLabel(f"Poslední aktualizace: {datetime.now().strftime('%H:%M')}")
        self.lbl_last_update.setObjectName("bottomStat")

        bottom_layout.addWidget(self.lbl_section_info)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.lbl_last_update)

        parent_layout.addWidget(bottom_frame)

    def switch_section(self, section_id):
        self.current_section = section_id

        for btn_id, btn in self.nav_buttons.items():
            btn.setChecked(btn_id == section_id)

        section_names = {
            "users_list": ("Seznam uživatelů", self.users_list_view),
            "roles": ("Správa rolí", self.roles_view),
            "permissions": ("Oprávnění", self.permissions_view),
            "audit": ("Audit log", self.audit_view),
            "password_policy": ("Politika hesel", self.password_policy_view),
            "my_profile": ("Můj profil", self.my_profile_view),
        }

        if section_id in section_names:
            name, widget = section_names[section_id]
            self.lbl_section_info.setText(f"Sekce: {name}")
            self.content_stack.setCurrentWidget(widget)

            if hasattr(widget, 'refresh'):
                widget.refresh()

    def load_statistics(self):
        result = db.fetch_one("SELECT COUNT(*) as count FROM users")
        total = result['count'] if result else 0
        self.lbl_total_users.setText(f"Celkem uživatelů: {total}")

        result = db.fetch_one("SELECT COUNT(*) as count FROM users WHERE active = 1")
        active = result['count'] if result else 0
        self.lbl_active_users.setText(f"Aktivních: {active}")

        inactive = total - active
        self.lbl_inactive_users.setText(f"Neaktivních: {inactive}")

        result = db.fetch_one("SELECT COUNT(*) as count FROM roles")
        roles = result['count'] if result else 0
        self.lbl_roles_count.setText(f"Počet rolí: {roles}")

        result = db.fetch_one("""
            SELECT username, last_login FROM users
            WHERE last_login IS NOT NULL
            ORDER BY last_login DESC
            LIMIT 1
        """)
        if result and result['last_login']:
            try:
                dt = datetime.fromisoformat(result['last_login'])
                self.lbl_last_login.setText(f"Poslední: {result['username']} ({dt.strftime('%d.%m. %H:%M')})")
            except:
                self.lbl_last_login.setText("Poslední přihlášení: --")
        else:
            self.lbl_last_login.setText("Poslední přihlášení: --")

    def create_new_user(self):
        from .users_widgets import UserDialog
        dialog = UserDialog(parent=self)
        if dialog.exec():
            self.log_audit_event("user_created", f"Vytvořen uživatel: {dialog.created_username}")
            self.refresh()
            self.user_updated.emit()

    def export_users(self):
        from .users_import_export import UsersExportDialog
        dialog = UsersExportDialog(parent=self)
        dialog.exec()

    def import_users(self):
        uid = get_current_user_id()
        if uid and not has_permission(uid, "users", "create"):
            QMessageBox.warning(self, "Přístup odepřen", "Nemáte oprávnění importovat uživatele.")
            return

        from .users_import_export import UsersImportDialog
        dialog = UsersImportDialog(parent=self)
        if dialog.exec():
            self.log_audit_event("users_imported", f"Importováno {dialog.imported_count} uživatelů")
            self.refresh()
            self.user_updated.emit()

    def on_user_selected(self, user_id):
        pass

    def on_user_edited(self, user_id):
        self.log_audit_event("user_edited", f"Upraven uživatel ID: {user_id}")
        self.load_statistics()
        self.user_updated.emit()

    def on_user_deleted(self, user_id):
        self.log_audit_event("user_deleted", f"Smazán uživatel ID: {user_id}")
        self.load_statistics()
        self.user_updated.emit()

    def on_role_updated(self):
        self.log_audit_event("role_updated", "Upravena role nebo oprávnění")
        self.load_statistics()
        self.role_updated.emit()

    def on_profile_updated(self):
        username = get_current_username()
        self.lbl_current_user.setText(f"👤 {username}")
        self.log_audit_event("profile_updated", "Upraven vlastní profil")

    def log_audit_event(self, event_type, details):
        try:
            user_id = get_current_user_id()
            username = get_current_username()

            db.execute_query("""
                INSERT INTO audit_log (user_id, username, event_type, details, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, event_type, details, datetime.now().isoformat()))
        except Exception as e:
            print(f"Chyba při logování audit eventu: {e}")

    def refresh(self):
        self.load_statistics()

        current_widget = self.content_stack.currentWidget()
        if hasattr(current_widget, 'refresh'):
            current_widget.refresh()

        self.lbl_last_update.setText(f"Poslední aktualizace: {datetime.now().strftime('%H:%M')}")

    def set_styles(self):
        self.setStyleSheet(f"""
            QWidget {{
                font-family: 'Segoe UI';
                font-size: 13px;
            }}

            #topPanel {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}

            #moduleTitle {{
                color: {config.COLOR_PRIMARY};
            }}

            #leftPanel {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}

            #bottomPanel {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}

            #primaryButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }}

            #primaryButton:hover {{
                background-color: #2980b9;
            }}

            #primaryButton:disabled {{
                background-color: #bdc3c7;
            }}

            #actionButton {{
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 8px 15px;
            }}

            #actionButton:hover {{
                background-color: #e0e0e0;
            }}

            #sectionLabel {{
                font-weight: bold;
                color: {config.COLOR_PRIMARY};
                font-size: 14px;
                padding: 5px 0;
            }}

            #navSectionButton {{
                background-color: transparent;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                padding: 10px;
                text-align: left;
            }}

            #navSectionButton:hover {{
                background-color: #f0f0f0;
                border-color: {config.COLOR_SECONDARY};
            }}

            #navSectionButton:checked {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border-color: {config.COLOR_SECONDARY};
            }}

            #statsFrame {{
                background-color: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
            }}

            #statLabel {{
                color: #555;
                padding: 2px 0;
            }}

            #currentUserFrame {{
                background-color: #e8f4f8;
                border-radius: 5px;
                border: 1px solid #b8daff;
            }}

            #currentUserTitle {{
                color: #0056b3;
                font-size: 11px;
            }}

            #currentUserName {{
                color: {config.COLOR_PRIMARY};
            }}

            #bottomStat {{
                color: #666;
                font-size: 12px;
            }}

            #contentStack {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}
        """)
