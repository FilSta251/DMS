# -*- coding: utf-8 -*-
"""
Pomocné widgety a dialogy pro nastavení
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QLabel, QPushButton, QProgressBar, QTextEdit,
    QColorDialog, QSlider, QFrame, QComboBox, QSpinBox,
    QDialogButtonBox, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPixmap
import config


class PasswordChangeDialog(QDialog):
    """Dialog pro změnu hesla"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Změna hesla")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Formulář
        form = QFormLayout()
        form.setSpacing(10)

        self.old_password = QLineEdit()
        self.old_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.old_password.setPlaceholderText("Zadejte aktuální heslo")
        form.addRow("Staré heslo:", self.old_password)

        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password.setPlaceholderText("Zadejte nové heslo")
        self.new_password.textChanged.connect(self.check_password_strength)
        form.addRow("Nové heslo:", self.new_password)

        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password.setPlaceholderText("Potvrďte nové heslo")
        self.confirm_password.textChanged.connect(self.check_passwords_match)
        form.addRow("Potvrdit heslo:", self.confirm_password)

        layout.addLayout(form)

        # Indikátor síly hesla
        strength_layout = QVBoxLayout()
        strength_label = QLabel("Síla hesla:")
        strength_layout.addWidget(strength_label)

        self.strength_bar = QProgressBar()
        self.strength_bar.setMaximum(100)
        self.strength_bar.setValue(0)
        self.strength_bar.setTextVisible(False)
        self.strength_bar.setMaximumHeight(10)
        strength_layout.addWidget(self.strength_bar)

        self.strength_text = QLabel("Zadejte heslo")
        self.strength_text.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        strength_layout.addWidget(self.strength_text)

        layout.addLayout(strength_layout)

        # Status shody hesel
        self.match_status = QLabel("")
        self.match_status.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.match_status)

        # Požadavky na heslo
        requirements = QLabel(
            "Požadavky na heslo:\n"
            "• Minimálně 8 znaků\n"
            "• Alespoň jedno velké písmeno\n"
            "• Alespoň jedno malé písmeno\n"
            "• Alespoň jedna číslice"
        )
        requirements.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(requirements)

        # Tlačítka
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

    def check_password_strength(self, password):
        """Kontrola síly hesla"""
        strength = 0
        text = "Velmi slabé"
        color = "#e74c3c"

        if len(password) >= 8:
            strength += 25
        if any(c.isupper() for c in password):
            strength += 25
        if any(c.islower() for c in password):
            strength += 25
        if any(c.isdigit() for c in password):
            strength += 15
        if any(c in "!@#$%^&*()_+-=" for c in password):
            strength += 10

        if strength >= 80:
            text = "Silné"
            color = "#27ae60"
        elif strength >= 60:
            text = "Dobré"
            color = "#2ecc71"
        elif strength >= 40:
            text = "Střední"
            color = "#f39c12"
        elif strength >= 20:
            text = "Slabé"
            color = "#e67e22"

        self.strength_bar.setValue(strength)
        self.strength_bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 5px;
            }}
        """)
        self.strength_text.setText(text)
        self.strength_text.setStyleSheet(f"font-size: 11px; color: {color}; font-weight: bold;")

    def check_passwords_match(self):
        """Kontrola shody hesel"""
        if self.new_password.text() == self.confirm_password.text():
            self.match_status.setText("✅ Hesla se shodují")
            self.match_status.setStyleSheet("font-size: 11px; color: #27ae60;")
        else:
            self.match_status.setText("❌ Hesla se neshodují")
            self.match_status.setStyleSheet("font-size: 11px; color: #e74c3c;")

    def validate_and_accept(self):
        """Validace a potvrzení"""
        if not self.old_password.text():
            QMessageBox.warning(self, "Chyba", "Zadejte staré heslo.")
            return

        if len(self.new_password.text()) < 8:
            QMessageBox.warning(self, "Chyba", "Nové heslo musí mít alespoň 8 znaků.")
            return

        if self.new_password.text() != self.confirm_password.text():
            QMessageBox.warning(self, "Chyba", "Hesla se neshodují.")
            return

        self.accept()

    def get_passwords(self):
        """Získání hesel"""
        return {
            "old": self.old_password.text(),
            "new": self.new_password.text()
        }


class ColorPickerWidget(QFrame):
    """Widget pro výběr barvy"""
    colorChanged = pyqtSignal(str)

    def __init__(self, initial_color="#3498db", parent=None):
        super().__init__(parent)
        self.current_color = initial_color
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Náhled barvy
        self.preview = QLabel()
        self.preview.setFixedSize(40, 30)
        self.preview.setStyleSheet(f"""
            background-color: {self.current_color};
            border: 1px solid #bdc3c7;
            border-radius: 4px;
        """)
        layout.addWidget(self.preview)

        # Hex input
        self.hex_input = QLineEdit(self.current_color)
        self.hex_input.setMaxLength(7)
        self.hex_input.setFixedWidth(80)
        self.hex_input.textChanged.connect(self.on_hex_changed)
        layout.addWidget(self.hex_input)

        # Tlačítko pro picker
        pick_btn = QPushButton("🎨")
        pick_btn.setFixedWidth(30)
        pick_btn.clicked.connect(self.open_color_picker)
        pick_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(pick_btn)

    def on_hex_changed(self, text):
        """Změna hex hodnoty"""
        if not text.startswith("#"):
            text = "#" + text

        if len(text) == 7:
            self.current_color = text
            self.preview.setStyleSheet(f"""
                background-color: {text};
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            """)
            self.colorChanged.emit(text)

    def open_color_picker(self):
        """Otevření dialogu pro výběr barvy"""
        color = QColorDialog.getColor(QColor(self.current_color), self)
        if color.isValid():
            hex_color = color.name()
            self.current_color = hex_color
            self.hex_input.setText(hex_color)
            self.preview.setStyleSheet(f"""
                background-color: {hex_color};
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            """)
            self.colorChanged.emit(hex_color)

    def get_color(self):
        """Získání aktuální barvy"""
        return self.current_color

    def set_color(self, color):
        """Nastavení barvy"""
        self.current_color = color
        self.hex_input.setText(color)


class FilePathSelector(QFrame):
    """Widget pro výběr cesty k souboru/složce"""
    pathChanged = pyqtSignal(str)

    def __init__(self, mode="file", parent=None):
        super().__init__(parent)
        self.mode = mode  # "file" nebo "folder"
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Vyberte cestu...")
        self.path_input.textChanged.connect(self.validate_path)
        layout.addWidget(self.path_input)

        browse_btn = QPushButton("📁 Procházet")
        browse_btn.clicked.connect(self.browse)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(browse_btn)

        self.status_label = QLabel("")
        self.status_label.setFixedWidth(30)
        layout.addWidget(self.status_label)

    def browse(self):
        """Procházení souborů/složek"""
        if self.mode == "folder":
            path = QFileDialog.getExistingDirectory(self, "Vyberte složku")
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Vyberte soubor")

        if path:
            self.path_input.setText(path)
            self.pathChanged.emit(path)

    def validate_path(self, path):
        """Validace cesty"""
        from pathlib import Path
        p = Path(path)

        if self.mode == "folder":
            if p.exists() and p.is_dir():
                self.status_label.setText("✅")
            elif path:
                self.status_label.setText("❌")
            else:
                self.status_label.setText("")
        else:
            if p.exists() and p.is_file():
                self.status_label.setText("✅")
            elif path:
                self.status_label.setText("❌")
            else:
                self.status_label.setText("")

    def get_path(self):
        """Získání cesty"""
        return self.path_input.text()

    def set_path(self, path):
        """Nastavení cesty"""
        self.path_input.setText(path)


class BackupProgressDialog(QDialog):
    """Dialog pro průběh zálohování"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zálohování")
        self.setMinimumWidth(400)
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Ikona
        icon_label = QLabel("💾")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Aktuální operace
        self.operation_label = QLabel("Připravuji zálohu...")
        self.operation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.operation_label)

        # Čas
        self.time_label = QLabel("Zbývající čas: --:--")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.time_label)

        # Tlačítko zrušit
        self.cancel_btn = QPushButton("❌ Zrušit")
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn)

    def set_progress(self, value, operation=""):
        """Nastavení průběhu"""
        self.progress_bar.setValue(value)
        if operation:
            self.operation_label.setText(operation)

    def set_time_remaining(self, seconds):
        """Nastavení zbývajícího času"""
        minutes = seconds // 60
        secs = seconds % 60
        self.time_label.setText(f"Zbývající čas: {minutes:02d}:{secs:02d}")


class TestConnectionDialog(QDialog):
    """Dialog pro test připojení"""

    def __init__(self, service_name="Služba", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Test připojení - {service_name}")
        self.setMinimumWidth(350)
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Ikona a status
        self.status_icon = QLabel("⏳")
        self.status_icon.setStyleSheet("font-size: 48px;")
        self.status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_icon)

        self.status_text = QLabel("Testování připojení...")
        self.status_text.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.status_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_text)

        # Detail
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(100)
        self.detail_text.setStyleSheet("font-family: monospace;")
        layout.addWidget(self.detail_text)

        # Tlačítko zavřít
        close_btn = QPushButton("Zavřít")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def set_success(self, message="Připojení úspěšné"):
        """Nastavení úspěchu"""
        self.status_icon.setText("✅")
        self.status_text.setText(message)
        self.status_text.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")

    def set_error(self, message="Připojení selhalo", detail=""):
        """Nastavení chyby"""
        self.status_icon.setText("❌")
        self.status_text.setText(message)
        self.status_text.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c;")
        if detail:
            self.detail_text.setPlainText(detail)

    def add_log(self, text):
        """Přidání log záznamu"""
        self.detail_text.append(text)


class AboutDialog(QDialog):
    """Dialog O aplikaci"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("O aplikaci")
        self.setMinimumWidth(450)
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Logo a název
        logo_layout = QVBoxLayout()
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo = QLabel("🏍️")
        logo.setStyleSheet("font-size: 64px;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo)

        name = QLabel("Motoservis DMS")
        name.setStyleSheet("font-size: 28px; font-weight: bold;")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(name)

        version = QLabel(f"Verze {config.APP_VERSION}")
        version.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(version)

        layout.addLayout(logo_layout)

        # Popis
        description = QLabel(
            "Komplexní systém pro správu motoservisu.\n"
            "Zakázky • Zákazníci • Vozidla • Sklad • Fakturace"
        )
        description.setStyleSheet("color: #34495e;")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description)

        # Info
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
        """)
        info_layout = QFormLayout(info_frame)
        info_layout.setSpacing(8)

        info_layout.addRow("Vývojář:", QLabel("Váš vývojář"))
        info_layout.addRow("Kontakt:", QLabel("support@motoservis-dms.cz"))
        info_layout.addRow("Web:", QLabel("www.motoservis-dms.cz"))

        layout.addWidget(info_frame)

        # Copyright
        copyright_label = QLabel("© 2025 Motoservis DMS. Všechna práva vyhrazena.")
        copyright_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright_label)

        # Tlačítko zavřít
        close_btn = QPushButton("Zavřít")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            padding: 10px 30px;
            border-radius: 5px;
            background-color: #3498db;
            color: white;
            border: none;
        """)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)


class ImportExportDialog(QDialog):
    """Dialog pro import/export dat"""

    def __init__(self, mode="export", parent=None):
        super().__init__(parent)
        self.mode = mode
        self.setWindowTitle("Export dat" if mode == "export" else "Import dat")
        self.setMinimumWidth(500)
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Formát
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Formát:"))

        self.format_combo = QComboBox()
        self.format_combo.addItems(["CSV", "Excel (XLSX)", "JSON", "SQL"])
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()

        layout.addLayout(format_layout)

        # Data
        data_layout = QHBoxLayout()
        data_layout.addWidget(QLabel("Data:"))

        self.data_combo = QComboBox()
        self.data_combo.addItems([
            "Kompletní databáze",
            "Pouze zákazníci",
            "Pouze vozidla",
            "Pouze zakázky",
            "Pouze faktury"
        ])
        data_layout.addWidget(self.data_combo)
        data_layout.addStretch()

        layout.addLayout(data_layout)

        # Cesta
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Soubor:"))

        self.path_input = QLineEdit()
        path_layout.addWidget(self.path_input)

        browse_btn = QPushButton("📁")
        browse_btn.setFixedWidth(40)
        browse_btn.clicked.connect(self.browse_file)
        path_layout.addWidget(browse_btn)

        layout.addLayout(path_layout)

        # Preview (pouze pro import)
        if self.mode == "import":
            preview_label = QLabel("Náhled dat:")
            preview_label.setStyleSheet("font-weight: bold;")
            layout.addWidget(preview_label)

            self.preview_text = QTextEdit()
            self.preview_text.setReadOnly(True)
            self.preview_text.setMaximumHeight(150)
            layout.addWidget(self.preview_text)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Tlačítka
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText(
            "Exportovat" if self.mode == "export" else "Importovat"
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

    def browse_file(self):
        """Procházení souborů"""
        if self.mode == "export":
            path, _ = QFileDialog.getSaveFileName(
                self, "Uložit soubor", "", "Všechny soubory (*.*)"
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "Otevřít soubor", "", "Všechny soubory (*.*)"
            )

        if path:
            self.path_input.setText(path)


class LicenseActivationDialog(QDialog):
    """Dialog pro aktivaci licence"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aktivace licence")
        self.setMinimumWidth(450)
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Ikona
        icon = QLabel("🔑")
        icon.setStyleSheet("font-size: 48px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        # Nadpis
        title = QLabel("Aktivace licence Motoservis DMS")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Input pro klíč
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("MOTO-XXXX-XXXX-XXXX-XXXX")
        self.key_input.setStyleSheet("font-size: 14px; padding: 10px;")
        self.key_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.key_input)

        # Status
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(0)  # Indeterminate
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Tlačítka
        buttons_layout = QHBoxLayout()

        online_btn = QPushButton("🌐 Online aktivace")
        online_btn.clicked.connect(self.activate_online)
        online_btn.setStyleSheet("""
            padding: 10px 20px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
        """)

        offline_btn = QPushButton("📁 Offline aktivace")
        offline_btn.clicked.connect(self.activate_offline)

        buttons_layout.addWidget(online_btn)
        buttons_layout.addWidget(offline_btn)

        layout.addLayout(buttons_layout)

        # Zavřít
        close_btn = QPushButton("Zavřít")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)

    def activate_online(self):
        """Online aktivace"""
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Chyba", "Zadejte licenční klíč.")
            return

        self.progress_bar.setVisible(True)
        self.status_label.setText("Ověřuji licenci...")
        self.status_label.setStyleSheet("color: #f39c12;")

        # Simulace
        QTimer.singleShot(2000, self.on_activation_complete)

    def on_activation_complete(self):
        """Callback po aktivaci"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("✅ Licence úspěšně aktivována!")
        self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")

    def activate_offline(self):
        """Offline aktivace"""
        QMessageBox.information(
            self,
            "Offline aktivace",
            "Pro offline aktivaci kontaktujte podporu."
        )
