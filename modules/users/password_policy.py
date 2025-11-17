# -*- coding: utf-8 -*-
"""
Nastavení politiky hesel
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QSpinBox, QCheckBox, QPushButton, QLabel, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from database_manager import db
from utils_auth import get_current_user_id
from utils_permissions import has_permission
import config
import json


class PasswordPolicySettings(QWidget):
    """Widget pro nastavení politiky hesel"""

    settings_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.policy = {}

        self.init_ui()
        self.load_policy()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        top_panel = self.create_top_panel()
        main_layout.addWidget(top_panel)

        requirements_group = self.create_requirements_group()
        main_layout.addWidget(requirements_group)

        expiration_group = self.create_expiration_group()
        main_layout.addWidget(expiration_group)

        lockout_group = self.create_lockout_group()
        main_layout.addWidget(lockout_group)

        main_layout.addStretch()

        buttons_panel = self.create_buttons_panel()
        main_layout.addWidget(buttons_panel)

    def create_top_panel(self):
        panel = QFrame()
        panel.setObjectName("topPanel")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("🔒 Politika hesel")
        title.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        layout.addStretch()

        info_label = QLabel("ℹ️ Nastavení platí pro nová hesla")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(info_label)

        panel.setStyleSheet(f"""
            #topPanel {{
                background-color: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
            }}
            #sectionTitle {{
                color: {config.COLOR_PRIMARY};
            }}
        """)

        return panel

    def create_requirements_group(self):
        group = QGroupBox("📏 Požadavky na heslo")
        layout = QFormLayout(group)
        layout.setSpacing(12)

        self.spin_min_length = QSpinBox()
        self.spin_min_length.setRange(4, 32)
        self.spin_min_length.setValue(8)
        self.spin_min_length.setSuffix(" znaků")
        layout.addRow("Minimální délka:", self.spin_min_length)

        self.chk_uppercase = QCheckBox("Vyžadovat velká písmena (A-Z)")
        self.chk_uppercase.setChecked(True)
        layout.addRow("", self.chk_uppercase)

        self.chk_lowercase = QCheckBox("Vyžadovat malá písmena (a-z)")
        self.chk_lowercase.setChecked(True)
        layout.addRow("", self.chk_lowercase)

        self.chk_numbers = QCheckBox("Vyžadovat čísla (0-9)")
        self.chk_numbers.setChecked(True)
        layout.addRow("", self.chk_numbers)

        self.chk_special = QCheckBox("Vyžadovat speciální znaky (!@#$%^&*)")
        self.chk_special.setChecked(False)
        layout.addRow("", self.chk_special)

        self.chk_no_username = QCheckBox("Heslo nesmí obsahovat uživatelské jméno")
        self.chk_no_username.setChecked(True)
        layout.addRow("", self.chk_no_username)

        self.spin_history = QSpinBox()
        self.spin_history.setRange(0, 24)
        self.spin_history.setValue(3)
        self.spin_history.setSpecialValueText("Neomezeno")
        layout.addRow("Pamatovat posledních hesel:", self.spin_history)

        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QSpinBox {
                padding: 6px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
        """)

        return group

    def create_expiration_group(self):
        group = QGroupBox("⏰ Platnost hesla")
        layout = QFormLayout(group)
        layout.setSpacing(12)

        self.chk_expiration_enabled = QCheckBox("Povolit expiraci hesel")
        self.chk_expiration_enabled.setChecked(False)
        self.chk_expiration_enabled.stateChanged.connect(self.on_expiration_toggled)
        layout.addRow("", self.chk_expiration_enabled)

        self.spin_max_age = QSpinBox()
        self.spin_max_age.setRange(1, 365)
        self.spin_max_age.setValue(90)
        self.spin_max_age.setSuffix(" dní")
        self.spin_max_age.setEnabled(False)
        layout.addRow("Maximální stáří hesla:", self.spin_max_age)

        self.spin_warning_days = QSpinBox()
        self.spin_warning_days.setRange(1, 30)
        self.spin_warning_days.setValue(14)
        self.spin_warning_days.setSuffix(" dní předem")
        self.spin_warning_days.setEnabled(False)
        layout.addRow("Upozornit před expirací:", self.spin_warning_days)

        self.chk_force_change_first = QCheckBox("Vynutit změnu hesla při prvním přihlášení")
        self.chk_force_change_first.setChecked(True)
        layout.addRow("", self.chk_force_change_first)

        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QSpinBox {
                padding: 6px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
        """)

        return group

    def create_lockout_group(self):
        group = QGroupBox("🔐 Zamykání účtu")
        layout = QFormLayout(group)
        layout.setSpacing(12)

        self.chk_lockout_enabled = QCheckBox("Povolit zamykání účtu při neúspěšných pokusech")
        self.chk_lockout_enabled.setChecked(True)
        self.chk_lockout_enabled.stateChanged.connect(self.on_lockout_toggled)
        layout.addRow("", self.chk_lockout_enabled)

        self.spin_max_attempts = QSpinBox()
        self.spin_max_attempts.setRange(1, 20)
        self.spin_max_attempts.setValue(5)
        self.spin_max_attempts.setSuffix(" pokusů")
        layout.addRow("Maximální počet pokusů:", self.spin_max_attempts)

        self.spin_lockout_duration = QSpinBox()
        self.spin_lockout_duration.setRange(1, 1440)
        self.spin_lockout_duration.setValue(30)
        self.spin_lockout_duration.setSuffix(" minut")
        layout.addRow("Doba zámku:", self.spin_lockout_duration)

        self.chk_permanent_lockout = QCheckBox("Trvalý zámek (vyžaduje manuální odemknutí)")
        self.chk_permanent_lockout.setChecked(False)
        layout.addRow("", self.chk_permanent_lockout)

        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QSpinBox {
                padding: 6px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
        """)

        return group

    def create_buttons_panel(self):
        panel = QFrame()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        self.btn_reset = QPushButton("🔄 Obnovit výchozí")
        self.btn_reset.clicked.connect(self.reset_to_defaults)
        layout.addWidget(self.btn_reset)

        layout.addStretch()

        self.btn_save = QPushButton("💾 Uložit nastavení")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.clicked.connect(self.save_policy)

        uid = get_current_user_id()
        if uid and not has_permission(uid, "users", "admin"):
            self.btn_save.setEnabled(False)
            self.btn_save.setToolTip("Nemáte oprávnění měnit politiku hesel")

        layout.addWidget(self.btn_save)

        panel.setStyleSheet(f"""
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
            #primaryButton:disabled {{
                background-color: #bdc3c7;
            }}
        """)

        return panel

    def on_expiration_toggled(self, state):
        enabled = state == Qt.CheckState.Checked.value
        self.spin_max_age.setEnabled(enabled)
        self.spin_warning_days.setEnabled(enabled)

    def on_lockout_toggled(self, state):
        enabled = state == Qt.CheckState.Checked.value
        self.spin_max_attempts.setEnabled(enabled)
        self.spin_lockout_duration.setEnabled(enabled)
        self.chk_permanent_lockout.setEnabled(enabled)

    def load_policy(self):
        result = db.fetch_one(
            "SELECT setting_value FROM admin_settings WHERE setting_key = ?",
            ("password_policy",)
        )

        if result and result['setting_value']:
            try:
                self.policy = json.loads(result['setting_value'])
                self.apply_policy()
            except:
                self.reset_to_defaults()
        else:
            self.reset_to_defaults()

    def apply_policy(self):
        self.spin_min_length.setValue(self.policy.get('min_length', 8))
        self.chk_uppercase.setChecked(self.policy.get('require_uppercase', True))
        self.chk_lowercase.setChecked(self.policy.get('require_lowercase', True))
        self.chk_numbers.setChecked(self.policy.get('require_numbers', True))
        self.chk_special.setChecked(self.policy.get('require_special', False))
        self.chk_no_username.setChecked(self.policy.get('no_username', True))
        self.spin_history.setValue(self.policy.get('history_count', 3))

        self.chk_expiration_enabled.setChecked(self.policy.get('expiration_enabled', False))
        self.spin_max_age.setValue(self.policy.get('max_age_days', 90))
        self.spin_warning_days.setValue(self.policy.get('warning_days', 14))
        self.chk_force_change_first.setChecked(self.policy.get('force_change_first', True))

        self.chk_lockout_enabled.setChecked(self.policy.get('lockout_enabled', True))
        self.spin_max_attempts.setValue(self.policy.get('max_attempts', 5))
        self.spin_lockout_duration.setValue(self.policy.get('lockout_duration', 30))
        self.chk_permanent_lockout.setChecked(self.policy.get('permanent_lockout', False))

        self.on_expiration_toggled(self.chk_expiration_enabled.checkState().value)
        self.on_lockout_toggled(self.chk_lockout_enabled.checkState().value)

    def gather_policy(self):
        return {
            'min_length': self.spin_min_length.value(),
            'require_uppercase': self.chk_uppercase.isChecked(),
            'require_lowercase': self.chk_lowercase.isChecked(),
            'require_numbers': self.chk_numbers.isChecked(),
            'require_special': self.chk_special.isChecked(),
            'no_username': self.chk_no_username.isChecked(),
            'history_count': self.spin_history.value(),
            'expiration_enabled': self.chk_expiration_enabled.isChecked(),
            'max_age_days': self.spin_max_age.value(),
            'warning_days': self.spin_warning_days.value(),
            'force_change_first': self.chk_force_change_first.isChecked(),
            'lockout_enabled': self.chk_lockout_enabled.isChecked(),
            'max_attempts': self.spin_max_attempts.value(),
            'lockout_duration': self.spin_lockout_duration.value(),
            'permanent_lockout': self.chk_permanent_lockout.isChecked()
        }

    def save_policy(self):
        uid = get_current_user_id()
        if uid and not has_permission(uid, "users", "admin"):
            QMessageBox.warning(self, "Přístup odepřen", "Nemáte oprávnění měnit politiku hesel.")
            return

        policy = self.gather_policy()
        policy_json = json.dumps(policy, ensure_ascii=False)

        try:
            existing = db.fetch_one(
                "SELECT id FROM admin_settings WHERE setting_key = ?",
                ("password_policy",)
            )

            if existing:
                db.execute_query(
                    "UPDATE admin_settings SET setting_value = ? WHERE setting_key = ?",
                    (policy_json, "password_policy")
                )
            else:
                db.execute_query(
                    "INSERT INTO admin_settings (setting_key, setting_value) VALUES (?, ?)",
                    ("password_policy", policy_json)
                )

            self.policy = policy
            QMessageBox.information(self, "Úspěch", "Politika hesel byla uložena.")
            self.settings_saved.emit()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při ukládání: {e}")

    def reset_to_defaults(self):
        self.spin_min_length.setValue(8)
        self.chk_uppercase.setChecked(True)
        self.chk_lowercase.setChecked(True)
        self.chk_numbers.setChecked(True)
        self.chk_special.setChecked(False)
        self.chk_no_username.setChecked(True)
        self.spin_history.setValue(3)

        self.chk_expiration_enabled.setChecked(False)
        self.spin_max_age.setValue(90)
        self.spin_warning_days.setValue(14)
        self.chk_force_change_first.setChecked(True)

        self.chk_lockout_enabled.setChecked(True)
        self.spin_max_attempts.setValue(5)
        self.spin_lockout_duration.setValue(30)
        self.chk_permanent_lockout.setChecked(False)

        self.on_expiration_toggled(self.chk_expiration_enabled.checkState().value)
        self.on_lockout_toggled(self.chk_lockout_enabled.checkState().value)

    def refresh(self):
        self.load_policy()
