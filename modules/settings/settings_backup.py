# -*- coding: utf-8 -*-
"""
Nastavení zálohování a obnovy dat
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QLabel,
    QPushButton, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QFileDialog, QMessageBox,
    QTimeEdit, QFrame
)
from PyQt6.QtCore import Qt, QTime, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from database_manager import db
import config
import json
import zipfile
from pathlib import Path
from datetime import datetime


class BackupThread(QThread):
    """Vlákno pro zálohování"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, backup_options, backup_path):
        super().__init__()
        self.backup_options = backup_options
        self.backup_path = backup_path

    def run(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.zip"
            backup_file = Path(self.backup_path) / backup_name

            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                total_steps = sum(self.backup_options.values())
                current_step = 0

                if self.backup_options.get("database", False):
                    self.progress.emit(int(current_step / total_steps * 100), "Zálohování databáze...")
                    db_path = config.DATABASE_PATH
                    if db_path.exists():
                        zf.write(db_path, "database/motoservis.db")
                    current_step += 1

                if self.backup_options.get("documents", False):
                    self.progress.emit(int(current_step / total_steps * 100), "Zálohování dokumentů...")
                    docs_dir = config.DATA_DIR / "documents"
                    if docs_dir.exists():
                        for file in docs_dir.rglob("*"):
                            if file.is_file():
                                arcname = f"documents/{file.relative_to(docs_dir)}"
                                zf.write(file, arcname)
                    current_step += 1

                if self.backup_options.get("photos", False):
                    self.progress.emit(int(current_step / total_steps * 100), "Zálohování fotek...")
                    photos_dir = config.DATA_DIR / "photos"
                    if photos_dir.exists():
                        for file in photos_dir.rglob("*"):
                            if file.is_file():
                                arcname = f"photos/{file.relative_to(photos_dir)}"
                                zf.write(file, arcname)
                    current_step += 1

                if self.backup_options.get("settings", False):
                    self.progress.emit(int(current_step / total_steps * 100), "Zálohování nastavení...")
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT key, value FROM app_settings")
                    settings = {row[0]: row[1] for row in cursor.fetchall()}
                    settings_json = json.dumps(settings, ensure_ascii=False, indent=2)
                    zf.writestr("settings/app_settings.json", settings_json)
                    current_step += 1

                if self.backup_options.get("templates", False):
                    self.progress.emit(int(current_step / total_steps * 100), "Zálohování šablon...")
                    templates_dir = config.DATA_DIR / "templates"
                    if templates_dir.exists():
                        for file in templates_dir.rglob("*"):
                            if file.is_file():
                                arcname = f"templates/{file.relative_to(templates_dir)}"
                                zf.write(file, arcname)
                    current_step += 1

            backup_size = backup_file.stat().st_size / (1024 * 1024)

            self.progress.emit(100, "Hotovo!")
            self.finished.emit(True, f"Záloha vytvořena: {backup_name}\nVelikost: {backup_size:.2f} MB")

        except Exception as e:
            self.finished.emit(False, str(e))


class BackupSettingsWidget(QWidget):
    """Widget pro nastavení zálohování"""

    def __init__(self):
        super().__init__()
        self.backup_thread = None
        self.init_ui()
        self.load_settings()
        self.load_backup_list()

    def init_ui(self):
        """Inicializace UI"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        main_layout.addWidget(self.create_auto_backup_section())
        main_layout.addWidget(self.create_manual_backup_section())
        main_layout.addWidget(self.create_restore_section())
        main_layout.addWidget(self.create_export_section())
        main_layout.addWidget(self.create_import_section())
        main_layout.addWidget(self.create_backup_log_section())

        main_layout.addStretch()

        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        self.set_styles()

    def create_auto_backup_section(self):
        """Sekce automatického zálohování"""
        group = QGroupBox("⏰ Automatické zálohování")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        self.enable_auto_backup = QCheckBox("Povolit automatické zálohování")
        self.enable_auto_backup.toggled.connect(self.toggle_auto_backup)
        layout.addWidget(self.enable_auto_backup)

        auto_frame = QFrame()
        auto_frame.setObjectName("autoBackupFrame")
        auto_layout = QFormLayout(auto_frame)
        auto_layout.setSpacing(10)

        self.backup_frequency = QComboBox()
        self.backup_frequency.addItems(["Denně", "Týdně", "Měsíčně"])
        auto_layout.addRow("Frekvence:", self.backup_frequency)

        self.backup_time = QTimeEdit()
        self.backup_time.setTime(QTime(23, 0))
        self.backup_time.setDisplayFormat("HH:mm")
        auto_layout.addRow("Čas zálohování:", self.backup_time)

        location_layout = QHBoxLayout()

        self.backup_location_type = QComboBox()
        self.backup_location_type.addItems([
            "Lokální složka",
            "Síťový disk (NAS)",
            "Google Drive",
            "OneDrive"
        ])
        location_layout.addWidget(self.backup_location_type)

        self.backup_path = QLineEdit()
        self.backup_path.setText(str(config.BACKUP_DIR))
        location_layout.addWidget(self.backup_path)

        browse_btn = QPushButton("📁")
        browse_btn.setFixedWidth(40)
        browse_btn.clicked.connect(self.browse_backup_location)
        location_layout.addWidget(browse_btn)

        auto_layout.addRow("Místo uložení:", location_layout)

        self.max_backups = QSpinBox()
        self.max_backups.setRange(1, 365)
        self.max_backups.setValue(30)
        self.max_backups.setSuffix(" záloh")
        auto_layout.addRow("Uchovat maximálně:", self.max_backups)

        self.rotate_backups = QCheckBox("Automaticky mazat staré zálohy")
        self.rotate_backups.setChecked(True)
        auto_layout.addRow("", self.rotate_backups)

        self.auto_backup_frame = auto_frame
        layout.addWidget(auto_frame)

        status_layout = QHBoxLayout()
        self.auto_backup_status = QLabel("Status: Vypnuto")
        self.auto_backup_status.setStyleSheet("color: #7f8c8d;")
        status_layout.addWidget(self.auto_backup_status)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        self.toggle_auto_backup(False)

        return group

    def toggle_auto_backup(self, checked):
        """Přepnutí automatického zálohování"""
        self.auto_backup_frame.setEnabled(checked)
        if checked:
            self.auto_backup_status.setText("Status: Aktivní")
            self.auto_backup_status.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.auto_backup_status.setText("Status: Vypnuto")
            self.auto_backup_status.setStyleSheet("color: #7f8c8d;")

    def browse_backup_location(self):
        """Výběr složky pro zálohy"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Vyberte složku pro zálohy",
            self.backup_path.text()
        )
        if folder:
            self.backup_path.setText(folder)

    def create_manual_backup_section(self):
        """Sekce manuální zálohy"""
        group = QGroupBox("💾 Manuální záloha")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        what_label = QLabel("Co zálohovat:")
        what_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(what_label)

        self.backup_database = QCheckBox("✅ Databáze")
        self.backup_database.setChecked(True)
        layout.addWidget(self.backup_database)

        self.backup_documents = QCheckBox("✅ Dokumenty")
        self.backup_documents.setChecked(True)
        layout.addWidget(self.backup_documents)

        self.backup_photos = QCheckBox("✅ Fotky")
        self.backup_photos.setChecked(True)
        layout.addWidget(self.backup_photos)

        self.backup_settings = QCheckBox("✅ Nastavení")
        self.backup_settings.setChecked(True)
        layout.addWidget(self.backup_settings)

        self.backup_templates = QCheckBox("✅ Šablony")
        self.backup_templates.setChecked(True)
        layout.addWidget(self.backup_templates)

        self.backup_progress = QProgressBar()
        self.backup_progress.setValue(0)
        self.backup_progress.setTextVisible(True)
        self.backup_progress.setFormat("%p% - Připraveno")
        layout.addWidget(self.backup_progress)

        backup_btn_layout = QHBoxLayout()

        self.create_backup_btn = QPushButton("💾 Vytvořit zálohu nyní")
        self.create_backup_btn.clicked.connect(self.create_backup)
        self.create_backup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_backup_btn.setObjectName("primaryButton")

        backup_btn_layout.addWidget(self.create_backup_btn)
        backup_btn_layout.addStretch()

        layout.addLayout(backup_btn_layout)

        self.backup_info = QLabel("")
        self.backup_info.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.backup_info)

        return group

    def create_backup(self):
        """Vytvoření zálohy"""
        options = {
            "database": self.backup_database.isChecked(),
            "documents": self.backup_documents.isChecked(),
            "photos": self.backup_photos.isChecked(),
            "settings": self.backup_settings.isChecked(),
            "templates": self.backup_templates.isChecked()
        }

        if not any(options.values()):
            QMessageBox.warning(self, "Upozornění", "Vyberte alespoň jednu položku k zálohování.")
            return

        backup_path = self.backup_path.text()
        if not Path(backup_path).exists():
            try:
                Path(backup_path).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nelze vytvořit složku:\n{str(e)}")
                return

        self.create_backup_btn.setEnabled(False)
        self.backup_progress.setValue(0)
        self.backup_progress.setFormat("%p% - Zahajuji zálohu...")

        self.backup_thread = BackupThread(options, backup_path)
        self.backup_thread.progress.connect(self.on_backup_progress)
        self.backup_thread.finished.connect(self.on_backup_finished)
        self.backup_thread.start()

    def on_backup_progress(self, value, message):
        """Aktualizace progress baru"""
        self.backup_progress.setValue(value)
        self.backup_progress.setFormat(f"%p% - {message}")

    def on_backup_finished(self, success, message):
        """Callback po dokončení zálohy"""
        self.create_backup_btn.setEnabled(True)

        if success:
            self.backup_progress.setFormat("100% - Záloha dokončena!")
            self.backup_info.setText(message)
            self.backup_info.setStyleSheet("color: #27ae60; font-weight: bold;")
            QMessageBox.information(self, "Záloha dokončena", message)
            self.load_backup_list()
        else:
            self.backup_progress.setFormat("Chyba!")
            self.backup_info.setText(f"Chyba: {message}")
            self.backup_info.setStyleSheet("color: #e74c3c; font-weight: bold;")
            QMessageBox.critical(self, "Chyba zálohy", message)

    def create_restore_section(self):
        """Sekce obnovy ze zálohy"""
        group = QGroupBox("🔄 Obnova ze zálohy")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        self.backups_table = QTableWidget()
        self.backups_table.setColumnCount(4)
        self.backups_table.setHorizontalHeaderLabels([
            "Datum a čas", "Velikost", "Typ", "Soubor"
        ])

        header = self.backups_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.backups_table.setColumnWidth(0, 150)
        self.backups_table.setColumnWidth(1, 100)
        self.backups_table.setColumnWidth(2, 100)
        self.backups_table.setMaximumHeight(180)
        self.backups_table.setAlternatingRowColors(True)
        self.backups_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(self.backups_table)

        buttons_layout = QHBoxLayout()

        refresh_btn = QPushButton("🔄 Obnovit seznam")
        refresh_btn.clicked.connect(self.load_backup_list)

        restore_btn = QPushButton("🔄 Obnovit ze zálohy")
        restore_btn.clicked.connect(self.restore_backup)
        restore_btn.setObjectName("warningButton")

        delete_btn = QPushButton("🗑️ Smazat zálohu")
        delete_btn.clicked.connect(self.delete_backup)

        buttons_layout.addWidget(refresh_btn)
        buttons_layout.addWidget(restore_btn)
        buttons_layout.addWidget(delete_btn)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        warning_label = QLabel("⚠️ Obnova přepíše aktuální data! Před obnovou vytvořte zálohu.")
        warning_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        layout.addWidget(warning_label)

        return group

    def load_backup_list(self):
        """Načtení seznamu záloh"""
        backup_path = Path(self.backup_path.text())

        if not backup_path.exists():
            self.backups_table.setRowCount(0)
            return

        backups = list(backup_path.glob("backup_*.zip"))
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        self.backups_table.setRowCount(len(backups))

        for i, backup_file in enumerate(backups):
            mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            date_item = QTableWidgetItem(mtime.strftime("%d.%m.%Y %H:%M"))
            self.backups_table.setItem(i, 0, date_item)

            size_mb = backup_file.stat().st_size / (1024 * 1024)
            size_item = QTableWidgetItem(f"{size_mb:.2f} MB")
            self.backups_table.setItem(i, 1, size_item)

            type_item = QTableWidgetItem("Manuální")
            self.backups_table.setItem(i, 2, type_item)

            file_item = QTableWidgetItem(backup_file.name)
            file_item.setData(Qt.ItemDataRole.UserRole, str(backup_file))
            self.backups_table.setItem(i, 3, file_item)

    def restore_backup(self):
        """Obnova ze zálohy"""
        selected = self.backups_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Upozornění", "Vyberte zálohu pro obnovu.")
            return

        backup_file = self.backups_table.item(self.backups_table.currentRow(), 3).data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.warning(
            self,
            "Obnova ze zálohy",
            "VAROVÁNÍ!\n\n"
            "Obnova přepíše aktuální data v databázi.\n"
            "Tato akce nelze vrátit zpět!\n\n"
            "Doporučujeme nejdříve vytvořit aktuální zálohu.\n\n"
            "Opravdu chcete pokračovat?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(
                self,
                "Obnova",
                "Funkce obnovy bude implementována v další verzi.\n\n"
                f"Vybraná záloha: {backup_file}"
            )

    def delete_backup(self):
        """Smazání zálohy"""
        selected = self.backups_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Upozornění", "Vyberte zálohu pro smazání.")
            return

        backup_file = Path(self.backups_table.item(self.backups_table.currentRow(), 3).data(Qt.ItemDataRole.UserRole))

        reply = QMessageBox.question(
            self,
            "Smazat zálohu",
            f"Opravdu chcete smazat zálohu?\n\n{backup_file.name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                backup_file.unlink()
                self.load_backup_list()
                QMessageBox.information(self, "Hotovo", "Záloha byla smazána.")
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat zálohu:\n{str(e)}")

    def create_export_section(self):
        """Sekce exportu dat"""
        group = QGroupBox("📤 Export dat")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Formát:"))

        self.export_format = QComboBox()
        self.export_format.addItems([
            "SQL dump",
            "CSV",
            "Excel (XLSX)",
            "JSON"
        ])
        format_layout.addWidget(self.export_format)
        format_layout.addStretch()

        layout.addLayout(format_layout)

        what_layout = QHBoxLayout()
        what_layout.addWidget(QLabel("Co exportovat:"))

        self.export_what = QComboBox()
        self.export_what.addItems([
            "Kompletní databáze",
            "Pouze zákazníci",
            "Pouze zakázky",
            "Pouze vozidla",
            "Pouze sklad",
            "Pouze faktury"
        ])
        what_layout.addWidget(self.export_what)
        what_layout.addStretch()

        layout.addLayout(what_layout)

        export_btn = QPushButton("📤 Exportovat data")
        export_btn.clicked.connect(self.export_data)
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(export_btn)

        return group

    def export_data(self):
        """Export dat"""
        file_filter = {
            "SQL dump": "SQL soubory (*.sql)",
            "CSV": "CSV soubory (*.csv)",
            "Excel (XLSX)": "Excel soubory (*.xlsx)",
            "JSON": "JSON soubory (*.json)"
        }

        export_format = self.export_format.currentText()

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportovat data",
            str(config.EXPORTS_DIR / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            file_filter.get(export_format, "*.*")
        )

        if file_path:
            QMessageBox.information(
                self,
                "Export",
                f"Funkce exportu do formátu '{export_format}' bude implementována v další verzi.\n\n"
                f"Cílový soubor: {file_path}"
            )

    def create_import_section(self):
        """Sekce importu dat"""
        group = QGroupBox("📥 Import dat")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Typ importu:"))

        self.import_type = QComboBox()
        self.import_type.addItems([
            "Import z CSV",
            "Import ze zálohy",
            "Import z Excelu"
        ])
        type_layout.addWidget(self.import_type)
        type_layout.addStretch()

        layout.addLayout(type_layout)

        buttons_layout = QHBoxLayout()

        import_btn = QPushButton("📥 Importovat data")
        import_btn.clicked.connect(self.import_data)
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        validate_btn = QPushButton("✅ Validovat soubor")
        validate_btn.clicked.connect(self.validate_import)

        buttons_layout.addWidget(import_btn)
        buttons_layout.addWidget(validate_btn)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        warning_label = QLabel("⚠️ Import může přepsat existující data. Doporučujeme nejdříve vytvořit zálohu.")
        warning_label.setStyleSheet("color: #f39c12;")
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)

        return group

    def import_data(self):
        """Import dat"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importovat data",
            str(config.EXPORTS_DIR),
            "Všechny podporované (*.csv *.xlsx *.json *.zip);;CSV (*.csv);;Excel (*.xlsx);;JSON (*.json);;Záloha (*.zip)"
        )

        if file_path:
            QMessageBox.information(
                self,
                "Import",
                f"Funkce importu bude implementována v další verzi.\n\n"
                f"Vybraný soubor: {file_path}"
            )

    def validate_import(self):
        """Validace importního souboru"""
        QMessageBox.information(
            self,
            "Validace",
            "Funkce validace importního souboru bude implementována v další verzi."
        )

    def create_backup_log_section(self):
        """Sekce logu zálohování"""
        group = QGroupBox("📋 Historie zálohování")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        self.backup_log_table = QTableWidget()
        self.backup_log_table.setColumnCount(5)
        self.backup_log_table.setHorizontalHeaderLabels([
            "Datum a čas", "Typ", "Stav", "Velikost", "Trvání"
        ])

        header = self.backup_log_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.backup_log_table.setMaximumHeight(150)
        self.backup_log_table.setAlternatingRowColors(True)

        layout.addWidget(self.backup_log_table)

        return group

    def load_settings(self):
        """Načtení nastavení"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT key, value FROM app_settings WHERE key LIKE 'backup_%'")
            rows = cursor.fetchall()

            settings = {}
            for key, value in rows:
                settings[key.replace("backup_", "")] = value

            self.set_settings(settings)

        except Exception:
            pass

    def save_settings(self):
        """Uložení nastavení"""
        settings = self.get_settings()

        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            for key, value in settings.items():
                if isinstance(value, (dict, list, bool)):
                    value = json.dumps(value, ensure_ascii=False)
                cursor.execute("""
                    INSERT OR REPLACE INTO app_settings (key, value)
                    VALUES (?, ?)
                """, (f"backup_{key}", str(value)))

            conn.commit()

        except Exception as e:
            raise Exception(f"Chyba při ukládání: {str(e)}")

    def get_settings(self):
        """Získání nastavení"""
        return {
            "enable_auto_backup": self.enable_auto_backup.isChecked(),
            "backup_frequency": self.backup_frequency.currentText(),
            "backup_time": self.backup_time.time().toString("HH:mm"),
            "backup_location_type": self.backup_location_type.currentText(),
            "backup_path": self.backup_path.text(),
            "max_backups": self.max_backups.value(),
            "rotate_backups": self.rotate_backups.isChecked()
        }

    def set_settings(self, settings):
        """Nastavení hodnot"""
        if "enable_auto_backup" in settings:
            self.enable_auto_backup.setChecked(settings["enable_auto_backup"] == "True")

        if "backup_frequency" in settings:
            index = self.backup_frequency.findText(settings["backup_frequency"])
            if index >= 0:
                self.backup_frequency.setCurrentIndex(index)

        if "backup_time" in settings:
            self.backup_time.setTime(QTime.fromString(settings["backup_time"], "HH:mm"))

        if "backup_location_type" in settings:
            index = self.backup_location_type.findText(settings["backup_location_type"])
            if index >= 0:
                self.backup_location_type.setCurrentIndex(index)

        if "backup_path" in settings:
            self.backup_path.setText(settings["backup_path"])

        if "max_backups" in settings:
            self.max_backups.setValue(int(settings["max_backups"]))

        if "rotate_backups" in settings:
            self.rotate_backups.setChecked(settings["rotate_backups"] == "True")

    def refresh(self):
        """Obnovení"""
        self.load_settings()
        self.load_backup_list()

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet(f"""
            #settingsGroup {{
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }}

            #settingsGroup::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}

            QLineEdit, QComboBox, QSpinBox, QTimeEdit {{
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }}

            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTimeEdit:focus {{
                border: 2px solid #3498db;
            }}

            QTableWidget {{
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }}

            QHeaderView::section {{
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
            }}

            QProgressBar {{
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                text-align: center;
                background-color: #ecf0f1;
            }}

            QProgressBar::chunk {{
                background-color: {config.COLOR_SUCCESS};
                border-radius: 3px;
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

            #warningButton {{
                background-color: {config.COLOR_WARNING};
                color: white;
                border: none;
            }}

            #warningButton:hover {{
                background-color: #d68910;
            }}

            #autoBackupFrame {{
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
            }}

            QCheckBox {{
                spacing: 8px;
            }}
        """)
