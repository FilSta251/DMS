# -*- coding: utf-8 -*-
"""
Správa databáze
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QComboBox, QSpinBox, QCheckBox, QLabel,
    QPushButton, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QTextEdit, QMessageBox,
    QFrame, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from database_manager import db
import config
import json
from pathlib import Path
from datetime import datetime


class DatabaseMaintenanceThread(QThread):
    """Vlákno pro údržbu databáze"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, operation):
        super().__init__()
        self.operation = operation

    def run(self):
        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            if self.operation == "vacuum":
                self.progress.emit("Optimalizace databáze (VACUUM)...")
                cursor.execute("VACUUM")
                self.finished.emit(True, "Databáze byla optimalizována.")

            elif self.operation == "integrity":
                self.progress.emit("Kontrola integrity...")
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()[0]
                if result == "ok":
                    self.finished.emit(True, "Integrita databáze je v pořádku.")
                else:
                    self.finished.emit(False, f"Nalezeny problémy: {result}")

            elif self.operation == "reindex":
                self.progress.emit("Reindexace databáze...")
                cursor.execute("REINDEX")
                self.finished.emit(True, "Databáze byla reindexována.")

            elif self.operation == "analyze":
                self.progress.emit("Analýza statistik...")
                cursor.execute("ANALYZE")
                self.finished.emit(True, "Statistiky byly aktualizovány.")

            conn.commit()

        except Exception as e:
            self.finished.emit(False, str(e))


class DatabaseSettingsWidget(QWidget):
    """Widget pro správu databáze"""

    def __init__(self):
        super().__init__()
        self.maintenance_thread = None
        self.init_ui()
        self.load_database_info()

    def init_ui(self):
        """Inicializace UI"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Informace o databázi
        main_layout.addWidget(self.create_info_section())

        # Údržba databáze
        main_layout.addWidget(self.create_maintenance_section())

        # Archivace
        main_layout.addWidget(self.create_archive_section())

        # Migrace dat
        main_layout.addWidget(self.create_migration_section())

        # Pokročilé (SQL konzole)
        main_layout.addWidget(self.create_advanced_section())

        main_layout.addStretch()

        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        self.set_styles()

    def create_info_section(self):
        """Sekce informací o databázi"""
        group = QGroupBox("📊 Informace o databázi")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Základní info
        info_form = QFormLayout()
        info_form.setSpacing(8)

        self.db_type = QLabel("SQLite 3")
        self.db_type.setStyleSheet("font-weight: bold;")
        info_form.addRow("Typ databáze:", self.db_type)

        self.db_version = QLabel("--")
        info_form.addRow("Verze:", self.db_version)

        self.db_path = QLabel(str(config.DATABASE_PATH))
        self.db_path.setWordWrap(True)
        self.db_path.setStyleSheet("color: #7f8c8d;")
        info_form.addRow("Cesta:", self.db_path)

        self.db_size = QLabel("--")
        self.db_size.setStyleSheet("font-weight: bold;")
        info_form.addRow("Velikost:", self.db_size)

        self.last_backup = QLabel("--")
        info_form.addRow("Poslední záloha:", self.last_backup)

        self.db_status = QLabel("✅ OK")
        self.db_status.setStyleSheet("color: #27ae60; font-weight: bold;")
        info_form.addRow("Stav:", self.db_status)

        layout.addLayout(info_form)

        # Počty záznamů
        records_label = QLabel("Počet záznamů:")
        records_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(records_label)

        self.records_table = QTableWidget()
        self.records_table.setColumnCount(2)
        self.records_table.setHorizontalHeaderLabels(["Tabulka", "Počet"])

        header = self.records_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.records_table.setColumnWidth(1, 100)

        self.records_table.setMaximumHeight(200)
        self.records_table.setAlternatingRowColors(True)
        self.records_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.records_table)

        # Tlačítko obnovit
        refresh_btn = QPushButton("🔄 Obnovit informace")
        refresh_btn.clicked.connect(self.load_database_info)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(refresh_btn)

        return group

    def create_maintenance_section(self):
        """Sekce údržby databáze"""
        group = QGroupBox("🔧 Údržba databáze")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Varování
        warning = QLabel("⚠️ Před údržbou doporučujeme vytvořit zálohu databáze!")
        warning.setStyleSheet("color: #e74c3c; font-weight: bold;")
        layout.addWidget(warning)

        # Tlačítka údržby
        buttons_layout = QHBoxLayout()

        vacuum_btn = QPushButton("🔧 Optimalizovat")
        vacuum_btn.setToolTip("VACUUM - Optimalizuje velikost databáze")
        vacuum_btn.clicked.connect(lambda: self.run_maintenance("vacuum"))
        vacuum_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        integrity_btn = QPushButton("✅ Kontrola integrity")
        integrity_btn.setToolTip("Zkontroluje integritu databáze")
        integrity_btn.clicked.connect(lambda: self.run_maintenance("integrity"))
        integrity_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        reindex_btn = QPushButton("🔄 Reindex")
        reindex_btn.setToolTip("Přestaví indexy pro lepší výkon")
        reindex_btn.clicked.connect(lambda: self.run_maintenance("reindex"))
        reindex_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        analyze_btn = QPushButton("📊 Analyzovat")
        analyze_btn.setToolTip("Aktualizuje statistiky pro optimalizátor")
        analyze_btn.clicked.connect(lambda: self.run_maintenance("analyze"))
        analyze_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        buttons_layout.addWidget(vacuum_btn)
        buttons_layout.addWidget(integrity_btn)
        buttons_layout.addWidget(reindex_btn)
        buttons_layout.addWidget(analyze_btn)

        layout.addLayout(buttons_layout)

        # Další údržba
        cleanup_layout = QHBoxLayout()

        cleanup_temp_btn = QPushButton("🗑️ Vyčistit dočasné soubory")
        cleanup_temp_btn.clicked.connect(self.cleanup_temp_files)
        cleanup_temp_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        cleanup_logs_btn = QPushButton("📋 Vyčistit staré logy")
        cleanup_logs_btn.clicked.connect(self.cleanup_old_logs)
        cleanup_logs_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        cleanup_layout.addWidget(cleanup_temp_btn)
        cleanup_layout.addWidget(cleanup_logs_btn)
        cleanup_layout.addStretch()

        layout.addLayout(cleanup_layout)

        # Status
        self.maintenance_status = QLabel("")
        self.maintenance_status.setStyleSheet("font-style: italic;")
        layout.addWidget(self.maintenance_status)

        return group

    def create_archive_section(self):
        """Sekce archivace"""
        group = QGroupBox("📦 Archivace starých dat")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Archivace zakázek
        orders_layout = QHBoxLayout()
        self.archive_orders = QCheckBox("Archivovat zakázky starší než")
        orders_layout.addWidget(self.archive_orders)

        self.archive_orders_years = QSpinBox()
        self.archive_orders_years.setRange(1, 10)
        self.archive_orders_years.setValue(3)
        self.archive_orders_years.setSuffix(" roky")
        orders_layout.addWidget(self.archive_orders_years)
        orders_layout.addStretch()

        layout.addLayout(orders_layout)

        # Archivace faktur
        invoices_layout = QHBoxLayout()
        self.archive_invoices = QCheckBox("Archivovat faktury starší než")
        invoices_layout.addWidget(self.archive_invoices)

        self.archive_invoices_years = QSpinBox()
        self.archive_invoices_years.setRange(1, 15)
        self.archive_invoices_years.setValue(5)
        self.archive_invoices_years.setSuffix(" let")
        invoices_layout.addWidget(self.archive_invoices_years)
        invoices_layout.addStretch()

        layout.addLayout(invoices_layout)

        # Archivace logů
        logs_layout = QHBoxLayout()
        self.archive_logs = QCheckBox("Archivovat logy starší než")
        logs_layout.addWidget(self.archive_logs)

        self.archive_logs_months = QSpinBox()
        self.archive_logs_months.setRange(1, 24)
        self.archive_logs_months.setValue(12)
        self.archive_logs_months.setSuffix(" měsíců")
        logs_layout.addWidget(self.archive_logs_months)
        logs_layout.addStretch()

        layout.addLayout(logs_layout)

        # Cíl archivace
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("Archivovat do:"))

        self.archive_target = QComboBox()
        self.archive_target.addItems([
            "Samostatný soubor (archive.db)",
            "ZIP archiv",
            "CSV soubory"
        ])
        target_layout.addWidget(self.archive_target)
        target_layout.addStretch()

        layout.addLayout(target_layout)

        # Tlačítko archivace
        archive_btn = QPushButton("📦 Spustit archivaci")
        archive_btn.clicked.connect(self.run_archivation)
        archive_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        archive_btn.setObjectName("warningButton")

        layout.addWidget(archive_btn)

        # Info
        info_label = QLabel("💡 Archivovaná data budou přesunuta z hlavní databáze do archivního souboru.")
        info_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        return group

    def create_migration_section(self):
        """Sekce migrace dat"""
        group = QGroupBox("🔄 Migrace dat")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        info_label = QLabel("Nástroje pro import/export dat pro migraci mezi systémy:")
        info_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(info_label)

        # Export pro migraci
        export_layout = QHBoxLayout()

        export_format = QComboBox()
        export_format.addItems(["SQL dump", "CSV", "JSON", "XML"])
        export_layout.addWidget(export_format)

        export_btn = QPushButton("📤 Export pro migraci")
        export_btn.clicked.connect(self.export_for_migration)
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_layout.addWidget(export_btn)
        export_layout.addStretch()

        layout.addLayout(export_layout)

        # Import z jiného systému
        import_layout = QHBoxLayout()

        import_source = QComboBox()
        import_source.addItems([
            "Z jiného Motoservis DMS",
            "Z CSV souborů",
            "Z SQL dump",
            "Z Excelu"
        ])
        import_layout.addWidget(import_source)

        import_btn = QPushButton("📥 Import dat")
        import_btn.clicked.connect(self.import_from_other)
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_layout.addWidget(import_btn)
        import_layout.addStretch()

        layout.addLayout(import_layout)

        return group

    def create_advanced_section(self):
        """Sekce pokročilých funkcí"""
        group = QGroupBox("⚙️ Pokročilé (pouze pro administrátory)")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Varování
        warning = QLabel("⚠️ POZOR! Tyto operace mohou být nevratné! Používejte s opatrností!")
        warning.setStyleSheet("color: #e74c3c; font-weight: bold;")
        layout.addWidget(warning)

        # SQL konzole
        sql_label = QLabel("SQL konzole:")
        sql_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(sql_label)

        self.sql_input = QTextEdit()
        self.sql_input.setPlaceholderText("Zadejte SQL dotaz...\n\nPříklad:\nSELECT COUNT(*) FROM customers;")
        self.sql_input.setMaximumHeight(100)
        layout.addWidget(self.sql_input)

        sql_buttons = QHBoxLayout()

        run_sql_btn = QPushButton("▶️ Spustit dotaz")
        run_sql_btn.clicked.connect(self.run_sql_query)
        run_sql_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        run_sql_btn.setObjectName("dangerButton")

        clear_btn = QPushButton("🗑️ Vyčistit")
        clear_btn.clicked.connect(lambda: self.sql_input.clear())

        sql_buttons.addWidget(run_sql_btn)
        sql_buttons.addWidget(clear_btn)
        sql_buttons.addStretch()

        layout.addLayout(sql_buttons)

        # Výsledky
        results_label = QLabel("Výsledky:")
        results_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(results_label)

        self.sql_results = QTextEdit()
        self.sql_results.setReadOnly(True)
        self.sql_results.setMaximumHeight(150)
        self.sql_results.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: monospace;")
        layout.addWidget(self.sql_results)

        # Další pokročilé funkce
        advanced_buttons = QHBoxLayout()

        structure_btn = QPushButton("📋 Struktura tabulek")
        structure_btn.clicked.connect(self.show_table_structure)

        errors_btn = QPushButton("📜 Log chyb")
        errors_btn.clicked.connect(self.show_error_log)

        advanced_buttons.addWidget(structure_btn)
        advanced_buttons.addWidget(errors_btn)
        advanced_buttons.addStretch()

        layout.addLayout(advanced_buttons)

        return group

    def load_database_info(self):
        """Načtení informací o databázi"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            # Verze SQLite
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            self.db_version.setText(version)

            # Velikost databáze
            db_file = Path(config.DATABASE_PATH)
            if db_file.exists():
                size_bytes = db_file.stat().st_size
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.2f} KB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
                self.db_size.setText(size_str)

            # Počty záznamů
            tables = [
                ("customers", "Zákazníci"),
                ("vehicles", "Vozidla"),
                ("orders", "Zakázky"),
                ("invoices", "Faktury"),
                ("warehouse_items", "Skladové položky"),
                ("users", "Uživatelé"),
                ("audit_log", "Audit log")
            ]

            valid_tables = []
            for table_name, display_name in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    valid_tables.append((display_name, count))
                except Exception:
                    pass

            self.records_table.setRowCount(len(valid_tables))
            for i, (name, count) in enumerate(valid_tables):
                self.records_table.setItem(i, 0, QTableWidgetItem(name))
                count_item = QTableWidgetItem(str(count))
                count_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.records_table.setItem(i, 1, count_item)

            # Status
            self.db_status.setText("✅ OK")
            self.db_status.setStyleSheet("color: #27ae60; font-weight: bold;")

        except Exception as e:
            self.db_status.setText(f"❌ Chyba: {str(e)}")
            self.db_status.setStyleSheet("color: #e74c3c; font-weight: bold;")

    def run_maintenance(self, operation):
        """Spuštění údržby databáze"""
        operations = {
            "vacuum": "optimalizaci",
            "integrity": "kontrolu integrity",
            "reindex": "reindexaci",
            "analyze": "analýzu"
        }

        reply = QMessageBox.question(
            self,
            "Údržba databáze",
            f"Chcete spustit {operations.get(operation, operation)} databáze?\n\n"
            "Doporučujeme nejdříve vytvořit zálohu.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.maintenance_status.setText("⏳ Probíhá údržba...")
            self.maintenance_status.setStyleSheet("color: #f39c12; font-style: italic;")

            self.maintenance_thread = DatabaseMaintenanceThread(operation)
            self.maintenance_thread.progress.connect(self.on_maintenance_progress)
            self.maintenance_thread.finished.connect(self.on_maintenance_finished)
            self.maintenance_thread.start()

    def on_maintenance_progress(self, message):
        """Aktualizace stavu údržby"""
        self.maintenance_status.setText(f"⏳ {message}")

    def on_maintenance_finished(self, success, message):
        """Callback po dokončení údržby"""
        if success:
            self.maintenance_status.setText(f"✅ {message}")
            self.maintenance_status.setStyleSheet("color: #27ae60; font-style: italic;")
            QMessageBox.information(self, "Hotovo", message)
        else:
            self.maintenance_status.setText(f"❌ Chyba: {message}")
            self.maintenance_status.setStyleSheet("color: #e74c3c; font-style: italic;")
            QMessageBox.critical(self, "Chyba", message)

        self.load_database_info()

    def cleanup_temp_files(self):
        """Vyčištění dočasných souborů"""
        QMessageBox.information(
            self,
            "Vyčištění",
            "Funkce vyčištění dočasných souborů bude implementována v další verzi."
        )

    def cleanup_old_logs(self):
        """Vyčištění starých logů"""
        reply = QMessageBox.question(
            self,
            "Vyčistit logy",
            "Chcete smazat audit logy starší než 90 dní?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM audit_log
                    WHERE timestamp < datetime('now', '-90 days')
                """)
                deleted = cursor.rowcount
                conn.commit()

                QMessageBox.information(
                    self,
                    "Hotovo",
                    f"Bylo smazáno {deleted} starých záznamů z audit logu."
                )
                self.load_database_info()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se vyčistit logy:\n{str(e)}")

    def run_archivation(self):
        """Spuštění archivace"""
        QMessageBox.information(
            self,
            "Archivace",
            "Funkce archivace starých dat bude implementována v další verzi.\n\n"
            "Archivace přesune stará data do samostatného souboru pro lepší výkon."
        )

    def export_for_migration(self):
        """Export pro migraci"""
        QMessageBox.information(
            self,
            "Export",
            "Funkce exportu pro migraci bude implementována v další verzi."
        )

    def import_from_other(self):
        """Import z jiného systému"""
        QMessageBox.information(
            self,
            "Import",
            "Funkce importu z jiného systému bude implementována v další verzi."
        )

    def run_sql_query(self):
        """Spuštění SQL dotazu"""
        query = self.sql_input.toPlainText().strip()

        if not query:
            QMessageBox.warning(self, "Upozornění", "Zadejte SQL dotaz.")
            return

        # Varování pro nebezpečné operace
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "UPDATE"]
        if any(kw in query.upper() for kw in dangerous_keywords):
            reply = QMessageBox.warning(
                self,
                "Nebezpečná operace",
                "Tento dotaz může změnit nebo smazat data!\n\n"
                "Opravdu chcete pokračovat?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute(query)

            if query.upper().strip().startswith("SELECT"):
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]

                result_text = " | ".join(columns) + "\n"
                result_text += "-" * len(result_text) + "\n"

                for row in rows[:100]:  # Max 100 řádků
                    result_text += " | ".join(str(val) for val in row) + "\n"

                if len(rows) > 100:
                    result_text += f"\n... a dalších {len(rows) - 100} řádků"

                self.sql_results.setPlainText(result_text)
            else:
                conn.commit()
                self.sql_results.setPlainText(f"Dotaz proveden úspěšně.\nOvlivněno řádků: {cursor.rowcount}")

        except Exception as e:
            self.sql_results.setPlainText(f"CHYBA:\n{str(e)}")

    def show_table_structure(self):
        """Zobrazení struktury tabulek"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = cursor.fetchall()

            structure_text = "STRUKTURA DATABÁZE\n" + "=" * 50 + "\n\n"

            for (table_name,) in tables:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()

                structure_text += f"📋 {table_name}\n"
                structure_text += "-" * 40 + "\n"

                for col in columns:
                    cid, name, dtype, notnull, default, pk = col
                    pk_str = " [PK]" if pk else ""
                    nn_str = " NOT NULL" if notnull else ""
                    structure_text += f"  {name} ({dtype}){pk_str}{nn_str}\n"

                structure_text += "\n"

            self.sql_results.setPlainText(structure_text)

        except Exception as e:
            self.sql_results.setPlainText(f"CHYBA:\n{str(e)}")

    def show_error_log(self):
        """Zobrazení logu chyb"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT timestamp, action, detail
                FROM audit_log
                WHERE action LIKE '%error%' OR action LIKE '%chyba%'
                ORDER BY timestamp DESC
                LIMIT 50
            """)

            rows = cursor.fetchall()

            if rows:
                log_text = "POSLEDNÍ CHYBY\n" + "=" * 50 + "\n\n"
                for timestamp, action, detail in rows:
                    log_text += f"{timestamp}\n{action}\n{detail}\n" + "-" * 40 + "\n"
            else:
                log_text = "Žádné chyby nebyly nalezeny."

            self.sql_results.setPlainText(log_text)

        except Exception as e:
            self.sql_results.setPlainText(f"CHYBA:\n{str(e)}")

    def save_settings(self):
        """Uložení nastavení"""
        settings = self.get_settings()

        try:
            conn = db.get_connection()
            cursor = conn.cursor()

            for key, value in settings.items():
                if isinstance(value, bool):
                    value = str(value)
                cursor.execute("""
                    INSERT OR REPLACE INTO app_settings (key, value)
                    VALUES (?, ?)
                """, (f"database_{key}", str(value)))

            conn.commit()

        except Exception as e:
            raise Exception(f"Chyba při ukládání: {str(e)}")

    def get_settings(self):
        """Získání nastavení"""
        return {
            "archive_orders": self.archive_orders.isChecked(),
            "archive_orders_years": self.archive_orders_years.value(),
            "archive_invoices": self.archive_invoices.isChecked(),
            "archive_invoices_years": self.archive_invoices_years.value(),
            "archive_logs": self.archive_logs.isChecked(),
            "archive_logs_months": self.archive_logs_months.value(),
            "archive_target": self.archive_target.currentText()
        }

    def set_settings(self, settings):
        """Nastavení hodnot"""
        if "archive_orders" in settings:
            self.archive_orders.setChecked(settings["archive_orders"] == "True")
        if "archive_orders_years" in settings:
            self.archive_orders_years.setValue(int(settings["archive_orders_years"]))
        if "archive_invoices" in settings:
            self.archive_invoices.setChecked(settings["archive_invoices"] == "True")
        if "archive_invoices_years" in settings:
            self.archive_invoices_years.setValue(int(settings["archive_invoices_years"]))
        if "archive_logs" in settings:
            self.archive_logs.setChecked(settings["archive_logs"] == "True")
        if "archive_logs_months" in settings:
            self.archive_logs_months.setValue(int(settings["archive_logs_months"]))

    def refresh(self):
        """Obnovení"""
        self.load_database_info()

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

            QLineEdit, QComboBox, QSpinBox {{
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }}

            QTextEdit {{
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
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

            #warningButton {{
                background-color: {config.COLOR_WARNING};
                color: white;
                border: none;
            }}

            #warningButton:hover {{
                background-color: #d68910;
            }}

            #dangerButton {{
                background-color: {config.COLOR_DANGER};
                color: white;
                border: none;
            }}

            #dangerButton:hover {{
                background-color: #c0392b;
            }}

            QCheckBox {{
                spacing: 8px;
            }}
        """)
