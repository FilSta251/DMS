# -*- coding: utf-8 -*-
"""
Detail a editace uživatele
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QLineEdit, QComboBox, QCheckBox, QPushButton,
    QLabel, QFrame, QMessageBox, QTextEdit, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime
from database_manager import db
from utils.utils_auth import hash_password, get_current_user_id
from utils.utils_permissions import has_permission
import config


class UserDetailDialog(QDialog):
    """Dialog pro detail a editaci uživatele"""

    user_saved = pyqtSignal(int)

    def __init__(self, user_id=None, parent=None):
        super().__init__(parent)

        self.user_id = user_id
        self.is_new = user_id is None
        self.user_data = None

        self.setWindowTitle("Nový uživatel" if self.is_new else "Editace uživatele")
        self.setMinimumSize(700, 600)
        self.setModal(True)

        self.init_ui()

        if not self.is_new:
            self.load_user_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        tabs = QTabWidget()
        tabs.addTab(self.create_basic_tab(), "👤 Základní údaje")
        tabs.addTab(self.create_security_tab(), "🔐 Bezpečnost")
        tabs.addTab(self.create_permissions_tab(), "🔑 Oprávnění")

        if not self.is_new:
            tabs.addTab(self.create_activity_tab(), "📊 Aktivita")

        main_layout.addWidget(tabs)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.btn_save = QPushButton("💾 Uložit")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.clicked.connect(self.save_user)
        buttons_layout.addWidget(self.btn_save)

        self.btn_cancel = QPushButton("❌ Zrušit")
        self.btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(self.btn_cancel)

        main_layout.addLayout(buttons_layout)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: #f5f5f5;
            }}
            QTabWidget::pane {{
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
            }}
            QTabBar::tab {{
                background-color: #e0e0e0;
                padding: 10px 20px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }}
            QTabBar::tab:selected {{
                background-color: white;
                border-bottom: 2px solid {config.COLOR_SECONDARY};
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
            QLineEdit, QComboBox, QTextEdit {{
                padding: 8px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }}
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
                border-color: {config.COLOR_SECONDARY};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)

    def create_basic_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("Unikátní uživatelské jméno")
        layout.addRow("Uživatelské jméno: *", self.txt_username)

        self.txt_full_name = QLineEdit()
        self.txt_full_name.setPlaceholderText("Celé jméno uživatele")
        layout.addRow("Celé jméno: *", self.txt_full_name)

        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("email@example.com")
        layout.addRow("Email:", self.txt_email)

        self.txt_phone = QLineEdit()
        self.txt_phone.setPlaceholderText("+420 123 456 789")
        layout.addRow("Telefon:", self.txt_phone)

        self.cmb_role = QComboBox()
        self.load_roles()
        layout.addRow("Role: *", self.cmb_role)

        self.chk_active = QCheckBox("Účet je aktivní")
        self.chk_active.setChecked(True)
        layout.addRow("Stav:", self.chk_active)

        self.txt_note = QTextEdit()
        self.txt_note.setPlaceholderText("Poznámka k uživateli...")
        self.txt_note.setMaximumHeight(100)
        layout.addRow("Poznámka:", self.txt_note)

        if self.is_new:
            password_group = QGroupBox("Heslo")
            password_layout = QFormLayout(password_group)

            self.txt_password = QLineEdit()
            self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.txt_password.setPlaceholderText("Zadejte heslo")
            password_layout.addRow("Heslo: *", self.txt_password)

            self.txt_password_confirm = QLineEdit()
            self.txt_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
            self.txt_password_confirm.setPlaceholderText("Potvrďte heslo")
            password_layout.addRow("Potvrzení: *", self.txt_password_confirm)

            layout.addRow(password_group)

        required_note = QLabel("* Povinné položky")
        required_note.setStyleSheet("color: #666; font-style: italic;")
        layout.addRow("", required_note)

        return tab

    def create_security_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        if not self.is_new:
            password_group = QGroupBox("Změna hesla")
            password_layout = QFormLayout(password_group)

            self.txt_new_password = QLineEdit()
            self.txt_new_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.txt_new_password.setPlaceholderText("Nechte prázdné pro zachování")
            password_layout.addRow("Nové heslo:", self.txt_new_password)

            self.txt_new_password_confirm = QLineEdit()
            self.txt_new_password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
            self.txt_new_password_confirm.setPlaceholderText("Potvrďte nové heslo")
            password_layout.addRow("Potvrzení:", self.txt_new_password_confirm)

            layout.addWidget(password_group)

        options_group = QGroupBox("Bezpečnostní nastavení")
        options_layout = QVBoxLayout(options_group)

        self.chk_force_password_change = QCheckBox("Vynutit změnu hesla při dalším přihlášení")
        options_layout.addWidget(self.chk_force_password_change)

        self.chk_two_factor = QCheckBox("Dvoufaktorové ověření (připraveno)")
        self.chk_two_factor.setEnabled(False)
        options_layout.addWidget(self.chk_two_factor)

        layout.addWidget(options_group)

        if not self.is_new:
            info_group = QGroupBox("Informace o účtu")
            info_layout = QFormLayout(info_group)

            self.lbl_created = QLabel("--")
            info_layout.addRow("Vytvořeno:", self.lbl_created)

            self.lbl_updated = QLabel("--")
            info_layout.addRow("Poslední změna:", self.lbl_updated)

            self.lbl_last_login = QLabel("--")
            info_layout.addRow("Poslední přihlášení:", self.lbl_last_login)

            self.lbl_login_count = QLabel("--")
            info_layout.addRow("Počet přihlášení:", self.lbl_login_count)

            layout.addWidget(info_group)

        layout.addStretch()

        return tab

    def create_permissions_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        info_label = QLabel(
            "ℹ️ Oprávnění jsou primárně definována rolí uživatele.\n"
            "Zde můžete nastavit výjimky pro konkrétního uživatele."
        )
        info_label.setStyleSheet("color: #0056b3; background-color: #e8f4f8; padding: 10px; border-radius: 5px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

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

        self.load_permissions_matrix()

        layout.addWidget(self.permissions_table)

        buttons_layout = QHBoxLayout()

        btn_reset_permissions = QPushButton("🔄 Reset na role")
        btn_reset_permissions.clicked.connect(self.reset_permissions_to_role)
        buttons_layout.addWidget(btn_reset_permissions)

        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        return tab

    def create_activity_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        login_group = QGroupBox("Historie přihlášení (posledních 10)")
        login_layout = QVBoxLayout(login_group)

        self.login_history_table = QTableWidget()
        self.login_history_table.setColumnCount(3)
        self.login_history_table.setHorizontalHeaderLabels(["Datum a čas", "Typ", "IP adresa"])
        self.login_history_table.setMaximumHeight(200)

        header = self.login_history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        login_layout.addWidget(self.login_history_table)
        layout.addWidget(login_group)

        activity_group = QGroupBox("Poslední aktivita")
        activity_layout = QVBoxLayout(activity_group)

        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(3)
        self.activity_table.setHorizontalHeaderLabels(["Datum a čas", "Akce", "Detaily"])
        self.activity_table.setMaximumHeight(200)

        header = self.activity_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        activity_layout.addWidget(self.activity_table)
        layout.addWidget(activity_group)

        layout.addStretch()

        return tab

    def load_roles(self):
        self.cmb_role.clear()
        self.cmb_role.addItem("-- Vyberte roli --", None)

        roles = db.fetch_all("SELECT name, description FROM roles ORDER BY name")
        for role in roles:
            display = f"{role['name']}"
            if role['description']:
                display += f" - {role['description']}"
            self.cmb_role.addItem(display, role['name'])

    def load_permissions_matrix(self):
        self.permissions_table.setRowCount(0)

        modules = [m for m in config.MODULES]

        for module in modules:
            row = self.permissions_table.rowCount()
            self.permissions_table.insertRow(row)

            name_item = QTableWidgetItem(f"{module['icon']} {module['name']}")
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.permissions_table.setItem(row, 0, name_item)

            actions = ['view', 'create', 'edit', 'delete', 'admin']
            for col, action in enumerate(actions, start=1):
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)

                chk = QCheckBox()
                chk.setProperty("module_id", module['id'])
                chk.setProperty("action", action)
                checkbox_layout.addWidget(chk)

                self.permissions_table.setCellWidget(row, col, checkbox_widget)

    def load_user_data(self):
        if not self.user_id:
            return

        self.user_data = db.fetch_one("SELECT * FROM users WHERE id = ?", (self.user_id,))

        if not self.user_data:
            QMessageBox.warning(self, "Chyba", "Uživatel nebyl nalezen.")
            self.reject()
            return

        self.txt_username.setText(self.user_data['username'] or "")
        self.txt_full_name.setText(self.user_data['full_name'] or "")
        self.txt_email.setText(self.user_data['email'] or "")

        if 'phone' in self.user_data:
            self.txt_phone.setText(self.user_data['phone'] or "")

        if self.user_data['role']:
            index = self.cmb_role.findData(self.user_data['role'])
            if index >= 0:
                self.cmb_role.setCurrentIndex(index)

        self.chk_active.setChecked(bool(self.user_data['active']))

        if 'note' in self.user_data:
            self.txt_note.setPlainText(self.user_data['note'] or "")

        if self.user_data['created_at']:
            try:
                dt = datetime.fromisoformat(self.user_data['created_at'])
                self.lbl_created.setText(dt.strftime("%d.%m.%Y %H:%M"))
            except:
                self.lbl_created.setText(self.user_data['created_at'])

        if dict(self.user_data).get('updated_at'):
            try:
                dt = datetime.fromisoformat(self.user_data['updated_at'])
                self.lbl_updated.setText(dt.strftime("%d.%m.%Y %H:%M"))
            except:
                self.lbl_updated.setText(self.user_data['updated_at'])

        if dict(self.user_data).get('last_login'):
            try:
                dt = datetime.fromisoformat(self.user_data['last_login'])
                self.lbl_last_login.setText(dt.strftime("%d.%m.%Y %H:%M"))
            except:
                self.lbl_last_login.setText(self.user_data['last_login'])

        self.lbl_login_count.setText(str(dict(self.user_data).get('login_count', 0)))

        self.load_user_permissions()
        self.load_user_activity()

    def load_user_permissions(self):
        pass

    def load_user_activity(self):
        pass

    def reset_permissions_to_role(self):
        reply = QMessageBox.question(
            self,
            "Reset oprávnění",
            "Opravdu chcete resetovat všechna uživatelská oprávnění na výchozí hodnoty role?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Reset", "Oprávnění budou resetována po uložení.")

    def validate_input(self):
        if not self.txt_username.text().strip():
            QMessageBox.warning(self, "Chyba", "Uživatelské jméno je povinné.")
            self.txt_username.setFocus()
            return False

        if not self.txt_full_name.text().strip():
            QMessageBox.warning(self, "Chyba", "Celé jméno je povinné.")
            self.txt_full_name.setFocus()
            return False

        if not self.cmb_role.currentData():
            QMessageBox.warning(self, "Chyba", "Vyberte roli uživatele.")
            self.cmb_role.setFocus()
            return False

        if self.is_new:
            if not self.txt_password.text():
                QMessageBox.warning(self, "Chyba", "Heslo je povinné.")
                self.txt_password.setFocus()
                return False

            if self.txt_password.text() != self.txt_password_confirm.text():
                QMessageBox.warning(self, "Chyba", "Hesla se neshodují.")
                self.txt_password_confirm.setFocus()
                return False

            if len(self.txt_password.text()) < 6:
                QMessageBox.warning(self, "Chyba", "Heslo musí mít alespoň 6 znaků.")
                self.txt_password.setFocus()
                return False
        else:
            if self.txt_new_password.text():
                if self.txt_new_password.text() != self.txt_new_password_confirm.text():
                    QMessageBox.warning(self, "Chyba", "Nová hesla se neshodují.")
                    self.txt_new_password_confirm.setFocus()
                    return False

                if len(self.txt_new_password.text()) < 6:
                    QMessageBox.warning(self, "Chyba", "Heslo musí mít alespoň 6 znaků.")
                    self.txt_new_password.setFocus()
                    return False

        existing = db.fetch_one(
            "SELECT id FROM users WHERE username = ? AND id != ?",
            (self.txt_username.text().strip(), self.user_id or 0)
        )
        if existing:
            QMessageBox.warning(self, "Chyba", "Uživatelské jméno již existuje.")
            self.txt_username.setFocus()
            return False

        return True

    def save_user(self):
        if not self.validate_input():
            return

        try:
            username = self.txt_username.text().strip()
            full_name = self.txt_full_name.text().strip()
            email = self.txt_email.text().strip() or None
            phone = self.txt_phone.text().strip() or None
            role = self.cmb_role.currentData()
            active = 1 if self.chk_active.isChecked() else 0
            note = self.txt_note.toPlainText().strip() or None
            now = datetime.now().isoformat()

            if self.is_new:
                password_hash = hash_password(self.txt_password.text())

                db.execute_query("""
                    INSERT INTO users (
                        username, password, full_name, email, phone, role,
                        active, note, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (username, password_hash, full_name, email, phone, role, active, note, now, now))

                result = db.fetch_one("SELECT last_insert_rowid() as id")
                self.user_id = result['id']

                QMessageBox.information(self, "Úspěch", f"Uživatel '{username}' byl úspěšně vytvořen.")
            else:
                db.execute_query("""
                    UPDATE users SET
                        username = ?, full_name = ?, email = ?, phone = ?,
                        role = ?, active = ?, note = ?, updated_at = ?
                    WHERE id = ?
                """, (username, full_name, email, phone, role, active, note, now, self.user_id))

                if hasattr(self, 'txt_new_password') and self.txt_new_password.text():
                    new_hash = hash_password(self.txt_new_password.text())
                    db.execute_query(
                        "UPDATE users SET password = ? WHERE id = ?",
                        (new_hash, self.user_id)
                    )

                QMessageBox.information(self, "Úspěch", f"Uživatel '{username}' byl úspěšně aktualizován.")

            self.user_saved.emit(self.user_id)
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při ukládání uživatele: {e}")
