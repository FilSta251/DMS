# -*- coding: utf-8 -*-
"""
Widgety a dialogy pro modul uživatelů
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QFrame, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QWidget, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime
from database_manager import db
from utils_auth import hash_password, get_current_user_id
from utils_permissions import has_permission
import config


class UserDialog(QDialog):
    """Dialog pro rychlé vytvoření nového uživatele"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.created_username = ""

        self.setWindowTitle("Nový uživatel")
        self.setMinimumSize(450, 400)
        self.setModal(True)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("Unikátní uživatelské jméno")
        form_layout.addRow("Uživatelské jméno: *", self.txt_username)

        self.txt_full_name = QLineEdit()
        self.txt_full_name.setPlaceholderText("Celé jméno uživatele")
        form_layout.addRow("Celé jméno: *", self.txt_full_name)

        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("email@example.com")
        form_layout.addRow("Email:", self.txt_email)

        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setPlaceholderText("Minimálně 6 znaků")
        form_layout.addRow("Heslo: *", self.txt_password)

        self.txt_password_confirm = QLineEdit()
        self.txt_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password_confirm.setPlaceholderText("Potvrďte heslo")
        form_layout.addRow("Potvrzení hesla: *", self.txt_password_confirm)

        from PyQt6.QtWidgets import QComboBox
        self.cmb_role = QComboBox()
        self.cmb_role.addItem("-- Vyberte roli --", None)
        roles = db.fetch_all("SELECT name FROM roles ORDER BY name")
        for role in roles:
            self.cmb_role.addItem(role['name'], role['name'])
        form_layout.addRow("Role: *", self.cmb_role)

        self.chk_active = QCheckBox("Účet je aktivní")
        self.chk_active.setChecked(True)
        form_layout.addRow("", self.chk_active)

        layout.addLayout(form_layout)

        note_label = QLabel("* Povinné položky")
        note_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(note_label)

        layout.addStretch()

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_create = QPushButton("✅ Vytvořit")
        btn_create.setObjectName("primaryButton")
        btn_create.clicked.connect(self.create_user)
        buttons_layout.addWidget(btn_create)

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        layout.addLayout(buttons_layout)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: #f5f5f5;
            }}
            QLineEdit, QComboBox {{
                padding: 8px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }}
            #primaryButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 25px;
                font-weight: bold;
            }}
            #primaryButton:hover {{
                background-color: #229954;
            }}
        """)

    def create_user(self):
        username = self.txt_username.text().strip()
        full_name = self.txt_full_name.text().strip()
        email = self.txt_email.text().strip() or None
        password = self.txt_password.text()
        password_confirm = self.txt_password_confirm.text()
        role = self.cmb_role.currentData()
        active = 1 if self.chk_active.isChecked() else 0

        if not username:
            QMessageBox.warning(self, "Chyba", "Uživatelské jméno je povinné.")
            return

        if not full_name:
            QMessageBox.warning(self, "Chyba", "Celé jméno je povinné.")
            return

        if not password:
            QMessageBox.warning(self, "Chyba", "Heslo je povinné.")
            return

        if password != password_confirm:
            QMessageBox.warning(self, "Chyba", "Hesla se neshodují.")
            return

        if len(password) < 6:
            QMessageBox.warning(self, "Chyba", "Heslo musí mít alespoň 6 znaků.")
            return

        if not role:
            QMessageBox.warning(self, "Chyba", "Vyberte roli uživatele.")
            return

        existing = db.fetch_one("SELECT id FROM users WHERE username = ?", (username,))
        if existing:
            QMessageBox.warning(self, "Chyba", "Uživatelské jméno již existuje.")
            return

        try:
            password_hash = hash_password(password)
            now = datetime.now().isoformat()

            db.execute_query("""
                INSERT INTO users (username, password, full_name, email, role, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (username, password_hash, full_name, email, role, active, now, now))

            self.created_username = username
            QMessageBox.information(self, "Úspěch", f"Uživatel '{username}' byl vytvořen.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při vytváření uživatele: {e}")


class ResetPasswordDialog(QDialog):
    """Dialog pro reset hesla uživatele"""

    def __init__(self, user_id, parent=None):
        super().__init__(parent)

        self.user_id = user_id

        self.setWindowTitle("Reset hesla")
        self.setMinimumSize(400, 250)
        self.setModal(True)

        self.init_ui()
        self.load_user_info()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.lbl_user_info = QLabel("Uživatel: --")
        self.lbl_user_info.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.lbl_user_info)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.txt_new_password = QLineEdit()
        self.txt_new_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_new_password.setPlaceholderText("Nové heslo")
        form_layout.addRow("Nové heslo:", self.txt_new_password)

        self.txt_confirm_password = QLineEdit()
        self.txt_confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_confirm_password.setPlaceholderText("Potvrďte heslo")
        form_layout.addRow("Potvrzení:", self.txt_confirm_password)

        layout.addLayout(form_layout)

        self.chk_force_change = QCheckBox("Vynutit změnu hesla při dalším přihlášení")
        self.chk_force_change.setChecked(True)
        layout.addWidget(self.chk_force_change)

        layout.addStretch()

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_reset = QPushButton("🔑 Resetovat heslo")
        btn_reset.setObjectName("primaryButton")
        btn_reset.clicked.connect(self.reset_password)
        buttons_layout.addWidget(btn_reset)

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        layout.addLayout(buttons_layout)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: #f5f5f5;
            }}
            QLineEdit {{
                padding: 8px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }}
            #primaryButton {{
                background-color: {config.COLOR_WARNING};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 25px;
                font-weight: bold;
            }}
            #primaryButton:hover {{
                background-color: #d68910;
            }}
        """)

    def load_user_info(self):
        user = db.fetch_one("SELECT username, full_name FROM users WHERE id = ?", (self.user_id,))
        if user:
            self.lbl_user_info.setText(f"Uživatel: {user['full_name']} ({user['username']})")

    def reset_password(self):
        new_password = self.txt_new_password.text()
        confirm_password = self.txt_confirm_password.text()

        if not new_password:
            QMessageBox.warning(self, "Chyba", "Zadejte nové heslo.")
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Chyba", "Hesla se neshodují.")
            return

        if len(new_password) < 6:
            QMessageBox.warning(self, "Chyba", "Heslo musí mít alespoň 6 znaků.")
            return

        try:
            password_hash = hash_password(new_password)

            db.execute_query(
                "UPDATE users SET password = ?, updated_at = ? WHERE id = ?",
                (password_hash, datetime.now().isoformat(), self.user_id)
            )

            QMessageBox.information(self, "Úspěch", "Heslo bylo úspěšně resetováno.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při resetování hesla: {e}")


class UserPermissionsDialog(QDialog):
    """Dialog pro úpravu uživatelských výjimek oprávnění"""

    def __init__(self, user_id, parent=None):
        super().__init__(parent)

        self.user_id = user_id

        self.setWindowTitle("Uživatelská oprávnění")
        self.setMinimumSize(700, 500)
        self.setModal(True)

        self.init_ui()
        self.load_user_info()
        self.load_permissions()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.lbl_user_info = QLabel("Uživatel: --")
        self.lbl_user_info.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.lbl_user_info)

        info_label = QLabel(
            "ℹ️ Zde můžete nastavit výjimky oprávnění pro tohoto uživatele.\n"
            "Výjimky přepíší oprávnění z role."
        )
        info_label.setStyleSheet("color: #0056b3; background-color: #e8f4f8; padding: 10px; border-radius: 5px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        self.permissions_table = QTableWidget()
        self.permissions_table.setColumnCount(7)
        self.permissions_table.setHorizontalHeaderLabels([
            "Modul", "Z role", "Zobrazit", "Vytvořit", "Upravit", "Smazat", "Admin"
        ])

        header = self.permissions_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.permissions_table.setColumnWidth(1, 80)
        for i in range(2, 7):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            self.permissions_table.setColumnWidth(i, 70)

        layout.addWidget(self.permissions_table)

        buttons_layout = QHBoxLayout()

        btn_reset = QPushButton("🔄 Reset na role")
        btn_reset.clicked.connect(self.reset_to_role)
        buttons_layout.addWidget(btn_reset)

        buttons_layout.addStretch()

        btn_save = QPushButton("💾 Uložit")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self.save_permissions)
        buttons_layout.addWidget(btn_save)

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        layout.addLayout(buttons_layout)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: #f5f5f5;
            }}
            QTableWidget {{
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                background-color: white;
            }}
            QHeaderView::section {{
                background-color: {config.COLOR_PRIMARY};
                color: white;
                padding: 8px;
                border: none;
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

    def load_user_info(self):
        user = db.fetch_one("SELECT username, full_name, role FROM users WHERE id = ?", (self.user_id,))
        if user:
            self.lbl_user_info.setText(f"Uživatel: {user['full_name']} ({user['username']}) - Role: {user['role']}")
            self.user_role = user['role']

    def load_permissions(self):
        self.permissions_table.setRowCount(0)

        modules = config.MODULES

        for module in modules:
            row = self.permissions_table.rowCount()
            self.permissions_table.insertRow(row)

            name_item = QTableWidgetItem(f"{module['icon']} {module['name']}")
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setData(Qt.ItemDataRole.UserRole, module['id'])
            self.permissions_table.setItem(row, 0, name_item)

            role_perm = has_permission(self.user_id, module['id'], 'view')
            role_text = "✅" if role_perm else "❌"
            role_item = QTableWidgetItem(role_text)
            role_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            role_item.setFlags(role_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.permissions_table.setItem(row, 1, role_item)

            actions = ['view', 'create', 'edit', 'delete', 'admin']
            for col, action in enumerate(actions, start=2):
                perm = db.fetch_one(
                    "SELECT id FROM permissions WHERE module_id = ? AND action = ?",
                    (module['id'], action)
                )

                user_override = None
                if perm:
                    up = db.fetch_one(
                        "SELECT allowed FROM user_permissions WHERE user_id = ? AND permission_id = ?",
                        (self.user_id, perm['id'])
                    )
                    if up is not None:
                        user_override = bool(up['allowed'])

                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)

                chk = QCheckBox()
                chk.setProperty("module_id", module['id'])
                chk.setProperty("action", action)
                chk.setTristate(True)

                if user_override is None:
                    chk.setCheckState(Qt.CheckState.PartiallyChecked)
                elif user_override:
                    chk.setCheckState(Qt.CheckState.Checked)
                else:
                    chk.setCheckState(Qt.CheckState.Unchecked)

                checkbox_layout.addWidget(chk)
                self.permissions_table.setCellWidget(row, col, checkbox_widget)

    def reset_to_role(self):
        for row in range(self.permissions_table.rowCount()):
            for col in range(2, 7):
                widget = self.permissions_table.cellWidget(row, col)
                if widget:
                    chk = widget.findChild(QCheckBox)
                    if chk:
                        chk.setCheckState(Qt.CheckState.PartiallyChecked)

    def save_permissions(self):
        try:
            db.execute_query("DELETE FROM user_permissions WHERE user_id = ?", (self.user_id,))

            for row in range(self.permissions_table.rowCount()):
                module_item = self.permissions_table.item(row, 0)
                module_id = module_item.data(Qt.ItemDataRole.UserRole)

                actions = ['view', 'create', 'edit', 'delete', 'admin']
                for col, action in enumerate(actions, start=2):
                    widget = self.permissions_table.cellWidget(row, col)
                    if widget:
                        chk = widget.findChild(QCheckBox)
                        if chk:
                            state = chk.checkState()

                            if state != Qt.CheckState.PartiallyChecked:
                                perm = db.fetch_one(
                                    "SELECT id FROM permissions WHERE module_id = ? AND action = ?",
                                    (module_id, action)
                                )

                                if perm:
                                    allowed = 1 if state == Qt.CheckState.Checked else 0
                                    db.execute_query(
                                        "INSERT INTO user_permissions (user_id, permission_id, allowed) VALUES (?, ?, ?)",
                                        (self.user_id, perm['id'], allowed)
                                    )

            QMessageBox.information(self, "Úspěch", "Uživatelská oprávnění byla uložena.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při ukládání: {e}")


class UserHistoryDialog(QDialog):
    """Dialog pro zobrazení historie uživatele"""

    def __init__(self, user_id, parent=None):
        super().__init__(parent)

        self.user_id = user_id

        self.setWindowTitle("Historie uživatele")
        self.setMinimumSize(600, 400)
        self.setModal(True)

        self.init_ui()
        self.load_history()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.lbl_user_info = QLabel("Uživatel: --")
        self.lbl_user_info.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.lbl_user_info)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(["Datum a čas", "Typ události", "Detaily"])

        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.history_table.setColumnWidth(0, 150)
        self.history_table.setColumnWidth(1, 180)

        layout.addWidget(self.history_table)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_close = QPushButton("✅ Zavřít")
        btn_close.clicked.connect(self.accept)
        buttons_layout.addWidget(btn_close)

        layout.addLayout(buttons_layout)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: #f5f5f5;
            }}
            QTableWidget {{
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                background-color: white;
            }}
            QHeaderView::section {{
                background-color: {config.COLOR_PRIMARY};
                color: white;
                padding: 8px;
                border: none;
            }}
        """)

    def load_history(self):
        user = db.fetch_one("SELECT username, full_name FROM users WHERE id = ?", (self.user_id,))
        if user:
            self.lbl_user_info.setText(f"Uživatel: {user['full_name']} ({user['username']})")

        logs = db.fetch_all("""
            SELECT created_at, event_type, details
            FROM audit_log
            WHERE user_id = ? OR details LIKE ?
            ORDER BY created_at DESC
            LIMIT 100
        """, (self.user_id, f"%ID: {self.user_id}%"))

        self.history_table.setRowCount(0)

        event_names = {
            'login': '🔐 Přihlášení',
            'logout': '🔓 Odhlášení',
            'user_edited': '✏️ Profil upraven',
            'password_reset': '🔑 Reset hesla',
            'profile_updated': '👤 Profil aktualizován'
        }

        for log in logs:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)

            if log['created_at']:
                try:
                    dt = datetime.fromisoformat(log['created_at'])
                    date_text = dt.strftime("%d.%m.%Y %H:%M:%S")
                except:
                    date_text = log['created_at']
            else:
                date_text = "--"

            date_item = QTableWidgetItem(date_text)
            date_item.setFlags(date_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.history_table.setItem(row, 0, date_item)

            event_name = event_names.get(log['event_type'], log['event_type'])
            event_item = QTableWidgetItem(event_name)
            event_item.setFlags(event_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.history_table.setItem(row, 1, event_item)

            details_item = QTableWidgetItem(log['details'] or "")
            details_item.setFlags(details_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.history_table.setItem(row, 2, details_item)


class PasswordStrengthMeter(QWidget):
    """Widget pro zobrazení síly hesla"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.strength_label = QLabel("Síla hesla: --")
        layout.addWidget(self.strength_label)

        self.strength_bar = QFrame()
        self.strength_bar.setFixedHeight(10)
        self.strength_bar.setStyleSheet("background-color: #e0e0e0; border-radius: 5px;")
        layout.addWidget(self.strength_bar)

    def update_strength(self, password):
        if not password:
            self.strength_label.setText("Síla hesla: --")
            self.strength_bar.setStyleSheet("background-color: #e0e0e0; border-radius: 5px;")
            return

        strength = 0

        if len(password) >= 6:
            strength += 1
        if len(password) >= 8:
            strength += 1
        if len(password) >= 12:
            strength += 1
        if any(c.isupper() for c in password):
            strength += 1
        if any(c.islower() for c in password):
            strength += 1
        if any(c.isdigit() for c in password):
            strength += 1
        if any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in password):
            strength += 1

        if strength <= 2:
            text = "🔴 Slabé"
            color = config.COLOR_DANGER
        elif strength <= 4:
            text = "🟡 Střední"
            color = config.COLOR_WARNING
        elif strength <= 5:
            text = "🟢 Silné"
            color = config.COLOR_SUCCESS
        else:
            text = "💪 Velmi silné"
            color = config.COLOR_SUCCESS

        self.strength_label.setText(f"Síla hesla: {text}")
        self.strength_bar.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
