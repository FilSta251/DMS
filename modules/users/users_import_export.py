# -*- coding: utf-8 -*-
"""
Import a export uživatelů
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QMessageBox, QFileDialog, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime
from database_manager import db
from utils.utils_auth import hash_password
import config
import csv
import random
import string


class UsersExportDialog(QDialog):
    """Dialog pro export uživatelů"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Export uživatelů")
        self.setMinimumSize(500, 400)
        self.setModal(True)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("📤 Export uživatelů")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        options_group = QGroupBox("Možnosti exportu")
        options_layout = QVBoxLayout(options_group)

        self.chk_include_passwords = QCheckBox("Zahrnout hesla (NEBEZPEČNÉ)")
        self.chk_include_passwords.setChecked(False)
        self.chk_include_passwords.setStyleSheet("color: red;")
        options_layout.addWidget(self.chk_include_passwords)

        self.chk_active_only = QCheckBox("Pouze aktivní uživatelé")
        self.chk_active_only.setChecked(False)
        options_layout.addWidget(self.chk_active_only)

        self.chk_include_permissions = QCheckBox("Zahrnout oprávnění")
        self.chk_include_permissions.setChecked(False)
        options_layout.addWidget(self.chk_include_permissions)

        layout.addWidget(options_group)

        format_group = QGroupBox("Formát exportu")
        format_layout = QVBoxLayout(format_group)

        self.cmb_format = QComboBox()
        self.cmb_format.addItem("CSV (Excel kompatibilní)", "csv")
        self.cmb_format.addItem("JSON (záloha)", "json")
        format_layout.addWidget(self.cmb_format)

        layout.addWidget(format_group)

        users = db.fetch_all("SELECT COUNT(*) as count FROM users")
        count = users[0]['count'] if users else 0

        info_label = QLabel(f"ℹ️ Bude exportováno {count} uživatelů")
        info_label.setStyleSheet("color: #0056b3; background-color: #e8f4f8; padding: 10px; border-radius: 5px;")
        layout.addWidget(info_label)

        layout.addStretch()

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_export = QPushButton("📤 Exportovat")
        btn_export.setObjectName("primaryButton")
        btn_export.clicked.connect(self.export_users)
        buttons_layout.addWidget(btn_export)

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        layout.addLayout(buttons_layout)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: #f5f5f5;
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QComboBox {{
                padding: 8px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
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

    def export_users(self):
        export_format = self.cmb_format.currentData()

        if export_format == "csv":
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export uživatelů",
                f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV soubory (*.csv)"
            )
        else:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export uživatelů",
                f"users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON soubory (*.json)"
            )

        if not file_path:
            return

        try:
            query = "SELECT * FROM users"
            if self.chk_active_only.isChecked():
                query += " WHERE active = 1"
            query += " ORDER BY username"

            users = db.fetch_all(query)

            if export_format == "csv":
                self.export_to_csv(file_path, users)
            else:
                self.export_to_json(file_path, users)

            QMessageBox.information(
                self,
                "Export dokončen",
                f"Exportováno {len(users)} uživatelů do:\n{file_path}"
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při exportu: {e}")

    def export_to_csv(self, file_path, users):
        with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f, delimiter=';')

            headers = ['ID', 'Uživatelské jméno', 'Celé jméno', 'Email', 'Telefon', 'Role', 'Aktivní', 'Vytvořeno']
            if self.chk_include_passwords.isChecked():
                headers.insert(2, 'Heslo (hash)')
            writer.writerow(headers)

            for user in users:
                row = [
                    user['id'],
                    user['username'],
                    user['full_name'],
                    user['email'] or '',
                    user.get('phone', ''),
                    user['role'],
                    'Ano' if user['active'] else 'Ne',
                    user['created_at']
                ]
                if self.chk_include_passwords.isChecked():
                    row.insert(2, user['password'])
                writer.writerow(row)

    def export_to_json(self, file_path, users):
        import json

        export_data = {
            'export_date': datetime.now().isoformat(),
            'version': config.APP_VERSION,
            'users': []
        }

        for user in users:
            user_data = {
                'id': user['id'],
                'username': user['username'],
                'full_name': user['full_name'],
                'email': user['email'],
                'phone': user.get('phone'),
                'role': user['role'],
                'active': bool(user['active']),
                'created_at': user['created_at']
            }
            if self.chk_include_passwords.isChecked():
                user_data['password_hash'] = user['password']
            export_data['users'].append(user_data)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)


class UsersImportDialog(QDialog):
    """Dialog pro import uživatelů"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.imported_count = 0
        self.file_path = None
        self.preview_data = []

        self.setWindowTitle("Import uživatelů")
        self.setMinimumSize(800, 600)
        self.setModal(True)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("📥 Import uživatelů")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        file_frame = QFrame()
        file_layout = QHBoxLayout(file_frame)
        file_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_file = QLabel("Soubor: Nevybrán")
        file_layout.addWidget(self.lbl_file)

        file_layout.addStretch()

        btn_browse = QPushButton("📂 Vybrat soubor")
        btn_browse.clicked.connect(self.browse_file)
        file_layout.addWidget(btn_browse)

        layout.addWidget(file_frame)

        options_group = QGroupBox("Možnosti importu")
        options_layout = QVBoxLayout(options_group)

        self.chk_generate_passwords = QCheckBox("Generovat náhodná hesla (doporučeno)")
        self.chk_generate_passwords.setChecked(True)
        options_layout.addWidget(self.chk_generate_passwords)

        self.chk_skip_existing = QCheckBox("Přeskočit existující uživatele")
        self.chk_skip_existing.setChecked(True)
        options_layout.addWidget(self.chk_skip_existing)

        self.chk_activate_all = QCheckBox("Aktivovat všechny importované uživatele")
        self.chk_activate_all.setChecked(True)
        options_layout.addWidget(self.chk_activate_all)

        layout.addWidget(options_group)

        preview_label = QLabel("Náhled dat:")
        preview_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(preview_label)

        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(200)
        layout.addWidget(self.preview_table)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #666;")
        layout.addWidget(self.lbl_status)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.btn_import = QPushButton("📥 Importovat")
        self.btn_import.setObjectName("primaryButton")
        self.btn_import.clicked.connect(self.import_users)
        self.btn_import.setEnabled(False)
        buttons_layout.addWidget(self.btn_import)

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        layout.addLayout(buttons_layout)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: #f5f5f5;
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
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
            #primaryButton:disabled {{
                background-color: #bdc3c7;
            }}
        """)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Vyberte soubor s uživateli",
            "",
            "CSV soubory (*.csv);;JSON soubory (*.json);;Všechny soubory (*.*)"
        )

        if file_path:
            self.file_path = file_path
            self.lbl_file.setText(f"Soubor: {file_path}")
            self.load_preview()

    def load_preview(self):
        if not self.file_path:
            return

        try:
            if self.file_path.endswith('.csv'):
                self.load_csv_preview()
            elif self.file_path.endswith('.json'):
                self.load_json_preview()
            else:
                QMessageBox.warning(self, "Chyba", "Nepodporovaný formát souboru.")
                return

            self.btn_import.setEnabled(len(self.preview_data) > 0)
            self.lbl_status.setText(f"Nalezeno {len(self.preview_data)} uživatelů k importu")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při načítání souboru: {e}")

    def load_csv_preview(self):
        self.preview_data = []

        with open(self.file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')

            for row in reader:
                self.preview_data.append(row)

        if self.preview_data:
            headers = list(self.preview_data[0].keys())
            self.preview_table.setColumnCount(len(headers))
            self.preview_table.setHorizontalHeaderLabels(headers)

            header = self.preview_table.horizontalHeader()
            for i in range(len(headers)):
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

            self.preview_table.setRowCount(min(5, len(self.preview_data)))

            for row_idx, row_data in enumerate(self.preview_data[:5]):
                for col_idx, key in enumerate(headers):
                    item = QTableWidgetItem(str(dict(row_data).get(key, '')))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.preview_table.setItem(row_idx, col_idx, item)

    def load_json_preview(self):
        import json

        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if 'users' in data:
            self.preview_data = data['users']
        else:
            self.preview_data = data if isinstance(data, list) else []

        if self.preview_data:
            headers = list(self.preview_data[0].keys())
            self.preview_table.setColumnCount(len(headers))
            self.preview_table.setHorizontalHeaderLabels(headers)

            header = self.preview_table.horizontalHeader()
            for i in range(len(headers)):
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

            self.preview_table.setRowCount(min(5, len(self.preview_data)))

            for row_idx, row_data in enumerate(self.preview_data[:5]):
                for col_idx, key in enumerate(headers):
                    value = dict(row_data).get(key, '')
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.preview_table.setItem(row_idx, col_idx, item)

    def generate_password(self, length=12):
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choice(characters) for _ in range(length))

    def import_users(self):
        if not self.preview_data:
            QMessageBox.warning(self, "Chyba", "Žádná data k importu.")
            return

        reply = QMessageBox.question(
            self,
            "Potvrdit import",
            f"Opravdu chcete importovat {len(self.preview_data)} uživatelů?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        imported = 0
        skipped = 0
        errors = 0
        generated_passwords = []

        try:
            for user_data in self.preview_data:
                username = dict(user_data).get('username') or dict(user_data).get('Uživatelské jméno', '')
                full_name = dict(user_data).get('full_name') or dict(user_data).get('Celé jméno', '')
                email = dict(user_data).get('email') or dict(user_data).get('Email', '') or None
                phone = dict(user_data).get('phone') or dict(user_data).get('Telefon', '') or None
                role = dict(user_data).get('role') or dict(user_data).get('Role', 'mechanik')

                if not username or not full_name:
                    errors += 1
                    continue

                existing = db.fetch_one("SELECT id FROM users WHERE username = ?", (username,))

                if existing:
                    if self.chk_skip_existing.isChecked():
                        skipped += 1
                        continue
                    else:
                        errors += 1
                        continue

                if self.chk_generate_passwords.isChecked():
                    password = self.generate_password()
                    generated_passwords.append((username, password))
                else:
                    password = dict(user_data).get('password', 'changeme123')

                password_hash = hash_password(password)
                active = 1 if self.chk_activate_all.isChecked() else 0
                now = datetime.now().isoformat()

                db.execute_query("""
                    INSERT INTO users (username, password, full_name, email, phone, role, active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (username, password_hash, full_name, email, phone, role, active, now, now))

                imported += 1

            self.imported_count = imported

            message = f"Import dokončen:\n\n✅ Importováno: {imported}\n⏭️ Přeskočeno: {skipped}\n❌ Chyby: {errors}"

            if generated_passwords:
                message += "\n\n⚠️ Vygenerovaná hesla byla uložena do souboru 'generated_passwords.txt'"

                with open('generated_passwords.txt', 'w', encoding='utf-8') as f:
                    f.write(f"Vygenerovaná hesla - {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
                    f.write("=" * 50 + "\n")
                    for username, password in generated_passwords:
                        f.write(f"{username}: {password}\n")

            QMessageBox.information(self, "Import dokončen", message)
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při importu: {e}")
