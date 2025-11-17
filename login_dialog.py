# -*- coding: utf-8 -*-
"""
Login dialog: ověří uživatele, zapíše user_logins, aktualizuje last_login,
a při úspěchu uloží aktuálního uživatele (utils_auth.set_current_user).
Pokud najde plaintext heslo, po úspěšném loginu ho převede na bcrypt.
"""

from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QMessageBox
from PyQt6.QtCore import Qt
from database_manager import db
from utils_auth import verify_password, set_current_user, upgrade_password_to_bcrypt

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Přihlášení")
        self.setMinimumWidth(380)

        form = QFormLayout(self)
        self.in_user = QLineEdit(); self.in_user.setPlaceholderText("uživatelské jméno")
        self.in_pass = QLineEdit(); self.in_pass.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Uživatel:", self.in_user)
        form.addRow("Heslo:", self.in_pass)

        row = QHBoxLayout()
        btn_ok = QPushButton("Přihlásit"); btn_ok.clicked.connect(self._login)
        btn_cancel = QPushButton("Zrušit"); btn_cancel.clicked.connect(self.reject)
        row.addStretch(); row.addWidget(btn_ok); row.addWidget(btn_cancel)
        form.addRow(row)

    def _login(self):
        uname = self.in_user.text().strip()
        pwd = self.in_pass.text().strip()
        if not uname or not pwd:
            QMessageBox.warning(self, "Chyba", "Zadejte uživatelské jméno i heslo.")
            return

        user = db.fetch_one("SELECT * FROM users WHERE username=?", (uname,))
        if not user:
            QMessageBox.critical(self, "Chyba", "Neplatné přihlašovací údaje.")
            return
        if int(user['active']) != 1:
            QMessageBox.critical(self, "Chyba", "Účet je deaktivován.")
            return

        if not verify_password(pwd, user['password']):
            # neúspěch -> log
            db.execute_query("""
                INSERT INTO user_logins (user_id, ip_address, success, note)
                VALUES (?, '127.0.0.1', 0, 'Neúspěšné přihlášení')
            """, (user['id'],))
            QMessageBox.critical(self, "Chyba", "Neplatné přihlašovací údaje.")
            return

        # úspěch -> případný upgrade na bcrypt
        upgrade_password_to_bcrypt(user['id'], pwd, user['password'])

        # log + update last_login
        db.execute_query("""
            INSERT INTO user_logins (user_id, ip_address, success, note)
            VALUES (?, '127.0.0.1', 1, 'Přihlášení přes login dialog')
        """, (user['id'],))
        db.execute_query("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?", (user['id'],))

        # nastavit aktuálního uživatele
        set_current_user(user['id'], user['username'])
        self.accept()
