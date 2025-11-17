# customer_import.py
# -*- coding: utf-8 -*-
"""
Import zákazníků z externích zdrojů
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QGroupBox, QProgressBar,
    QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QWizard, QWizardPage, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
import config
from database_manager import db
from datetime import datetime
import csv
import os


class CustomerImporter:
    """Třída pro import zákazníků"""

    @staticmethod
    def preview_file(file_path, rows=10):
        """Náhled souboru"""
        try:
            ext = os.path.splitext(file_path)[1].lower()

            if ext == ".csv":
                return CustomerImporter._preview_csv(file_path, rows)
            elif ext in [".xls", ".xlsx"]:
                return CustomerImporter._preview_excel(file_path, rows)
            elif ext == ".vcf":
                return CustomerImporter._preview_vcard(file_path, rows)
            elif ext == ".json":
                return CustomerImporter._preview_json(file_path, rows)
            else:
                return None, f"Nepodporovaný formát: {ext}"

        except Exception as e:
            return None, str(e)

    @staticmethod
    def _preview_csv(file_path, rows):
        """Náhled CSV souboru"""
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            # Detekce oddělovače
            sample = f.read(1024)
            f.seek(0)

            if ';' in sample:
                delimiter = ';'
            else:
                delimiter = ','

            reader = csv.reader(f, delimiter=delimiter)
            for i, row in enumerate(reader):
                if i >= rows:
                    break
                data.append(row)

        return data, None

    @staticmethod
    def _preview_excel(file_path, rows):
        """Náhled Excel souboru"""
        # Zde by byla implementace s openpyxl
        return [], "Excel import bude implementován"

    @staticmethod
    def _preview_vcard(file_path, rows):
        """Náhled vCard souboru"""
        # Zde by byla implementace parsování vCard
        return [], "vCard import bude implementován"

    @staticmethod
    def _preview_json(file_path, rows):
        """Náhled JSON souboru"""
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list) and data:
            headers = list(data[0].keys())
            result = [headers]
            for i, item in enumerate(data[:rows-1]):
                result.append([str(item.get(h, "")) for h in headers])
            return result, None

        return [], "Neplatný formát JSON"

    @staticmethod
    def validate_data(data, mapping):
        """Validace dat před importem"""
        errors = []
        warnings = []

        required_fields = ["email", "phone"]

        for i, row in enumerate(data[1:], start=2):  # Skip header
            # Kontrola povinných polí
            for field in required_fields:
                if field in mapping:
                    col_index = mapping[field]
                    if col_index < len(row) and not row[col_index].strip():
                        warnings.append(f"Řádek {i}: Prázdné pole {field}")

        return errors, warnings

    @staticmethod
    def check_duplicates(data, mapping):
        """Kontrola duplikátů"""
        duplicates = []

        email_col = mapping.get("email", -1)
        phone_col = mapping.get("phone", -1)
        ico_col = mapping.get("ico", -1)

        for i, row in enumerate(data[1:], start=2):
            # Kontrola emailu
            if email_col >= 0 and email_col < len(row):
                email = row[email_col].strip()
                if email:
                    existing = db.fetch_one(
                        "SELECT id FROM customers WHERE email = ?",
                        (email,)
                    )
                    if existing:
                        duplicates.append(f"Řádek {i}: Email {email} již existuje")

            # Kontrola IČO
            if ico_col >= 0 and ico_col < len(row):
                ico = row[ico_col].strip()
                if ico:
                    existing = db.fetch_one(
                        "SELECT id FROM customers WHERE ico = ?",
                        (ico,)
                    )
                    if existing:
                        duplicates.append(f"Řádek {i}: IČO {ico} již existuje")

        return duplicates

    @staticmethod
    def import_customers(data, mapping, settings):
        """Import zákazníků"""
        imported = 0
        skipped = 0
        errors = []

        for i, row in enumerate(data[1:], start=2):  # Skip header
            try:
                customer_data = {}

                for field, col_index in mapping.items():
                    if col_index < len(row):
                        customer_data[field] = row[col_index].strip()
                    else:
                        customer_data[field] = ""

                # Přidat výchozí hodnoty
                customer_data["customer_group"] = settings.get("default_group", "Standardní")
                customer_data["is_active"] = 1
                customer_data["has_debt"] = 0
                customer_data["created_at"] = datetime.now().isoformat()

                # Určit typ zákazníka
                if customer_data.get("ico") or customer_data.get("company_name"):
                    customer_data["customer_type"] = "company"
                else:
                    customer_data["customer_type"] = "personal"

                # Kontrola duplikátů
                if settings.get("skip_duplicates"):
                    email = customer_data.get("email", "")
                    if email:
                        existing = db.fetch_one(
                            "SELECT id FROM customers WHERE email = ?",
                            (email,)
                        )
                        if existing:
                            skipped += 1
                            continue

                # Vložení do databáze
                columns = ", ".join(customer_data.keys())
                placeholders = ", ".join(["?" for _ in customer_data])

                db.execute(
                    f"INSERT INTO customers ({columns}) VALUES ({placeholders})",
                    list(customer_data.values())
                )

                imported += 1

            except Exception as e:
                errors.append(f"Řádek {i}: {str(e)}")

        return imported, skipped, errors


class ImportWizard(QWizard):
    """Průvodce importem zákazníků"""

    import_completed = pyqtSignal(int, int, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path = ""
        self.preview_data = []
        self.mapping = {}
        self.settings = {}

        self.setWindowTitle("Import zákazníků")
        self.setMinimumSize(800, 600)

        self.addPage(FileSelectionPage(self))
        self.addPage(ColumnMappingPage(self))
        self.addPage(ImportSettingsPage(self))
        self.addPage(ImportProgressPage(self))

        self.setStyleSheet(f"""
            QWizard {{
                background-color: #f5f5f5;
            }}
            QWizardPage {{
                background-color: white;
                border-radius: 8px;
            }}
        """)


class FileSelectionPage(QWizardPage):
    """Stránka výběru souboru"""

    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard
        self.setTitle("1. Výběr souboru")
        self.setSubTitle("Vyberte soubor pro import zákazníků")
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Výběr souboru
        file_group = QGroupBox("📁 Soubor")
        file_layout = QHBoxLayout(file_group)

        self.le_file = QLabel("Žádný soubor nevybrán")
        self.le_file.setStyleSheet("padding: 10px; background-color: #f8f9fa; border-radius: 4px;")
        file_layout.addWidget(self.le_file, 1)

        btn_browse = QPushButton("📂 Procházet")
        btn_browse.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_browse.clicked.connect(self.browse_file)
        file_layout.addWidget(btn_browse)

        layout.addWidget(file_group)

        # Podporované formáty
        formats_group = QGroupBox("📋 Podporované formáty")
        formats_layout = QVBoxLayout(formats_group)

        formats_layout.addWidget(QLabel("• CSV (čárka nebo středník)"))
        formats_layout.addWidget(QLabel("• Excel (XLS, XLSX)"))
        formats_layout.addWidget(QLabel("• vCard (VCF)"))
        formats_layout.addWidget(QLabel("• JSON"))

        layout.addWidget(formats_group)

        # Náhled
        preview_group = QGroupBox("👁️ Náhled dat (prvních 10 řádků)")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(200)
        preview_layout.addWidget(self.preview_table)

        layout.addWidget(preview_group)

    def browse_file(self):
        """Výběr souboru"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Vybrat soubor pro import",
            "",
            "CSV soubory (*.csv);;Excel soubory (*.xls *.xlsx);;vCard (*.vcf);;JSON (*.json);;Všechny soubory (*.*)"
        )

        if file_path:
            self.wizard.file_path = file_path
            self.le_file.setText(file_path)
            self.load_preview()

    def load_preview(self):
        """Načtení náhledu"""
        data, error = CustomerImporter.preview_file(self.wizard.file_path)

        if error:
            QMessageBox.warning(self, "Chyba", error)
            return

        self.wizard.preview_data = data

        if data:
            self.preview_table.setRowCount(len(data))
            self.preview_table.setColumnCount(len(data[0]) if data else 0)

            for i, row in enumerate(data):
                for j, value in enumerate(row):
                    self.preview_table.setItem(i, j, QTableWidgetItem(str(value)))

            self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def isComplete(self):
        """Kontrola dokončení stránky"""
        return bool(self.wizard.file_path and self.wizard.preview_data)


class ColumnMappingPage(QWizardPage):
    """Stránka mapování sloupců"""

    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard
        self.setTitle("2. Mapování sloupců")
        self.setSubTitle("Přiřaďte sloupce ze souboru k polím zákazníka")
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        # Tabulka mapování
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(2)
        self.mapping_table.setHorizontalHeaderLabels(["Pole zákazníka", "Sloupec ze souboru"])
        self.mapping_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.mapping_table)

    def initializePage(self):
        """Inicializace při zobrazení stránky"""
        fields = [
            ("first_name", "Jméno"),
            ("last_name", "Příjmení"),
            ("company_name", "Název firmy"),
            ("ico", "IČO"),
            ("dic", "DIČ"),
            ("email", "Email"),
            ("phone", "Telefon"),
            ("street", "Ulice"),
            ("city", "Město"),
            ("zip", "PSČ"),
            ("country", "Země"),
            ("notes", "Poznámky")
        ]

        self.mapping_table.setRowCount(len(fields))
        self.combos = {}

        # Získat názvy sloupců z náhledu
        column_names = ["-- Nevybráno --"]
        if self.wizard.preview_data:
            header = self.wizard.preview_data[0]
            for i, col in enumerate(header):
                column_names.append(f"{i}: {col}")

        for i, (field_id, field_name) in enumerate(fields):
            # Pole zákazníka
            self.mapping_table.setItem(i, 0, QTableWidgetItem(field_name))

            # Combo pro výběr sloupce
            combo = QComboBox()
            combo.addItems(column_names)

            # Automatické mapování podle názvu
            for j, col_name in enumerate(column_names[1:], start=1):
                if field_name.lower() in col_name.lower():
                    combo.setCurrentIndex(j)
                    break

            self.combos[field_id] = combo
            self.mapping_table.setCellWidget(i, 1, combo)

    def validatePage(self):
        """Validace stránky"""
        # Uložit mapování
        for field_id, combo in self.combos.items():
            index = combo.currentIndex()
            if index > 0:  # Přeskočit "Nevybráno"
                self.wizard.mapping[field_id] = index - 1  # -1 protože první je "Nevybráno"

        # Kontrola povinných polí
        if "email" not in self.wizard.mapping and "phone" not in self.wizard.mapping:
            QMessageBox.warning(
                self,
                "Chybějící pole",
                "Musíte namapovat alespoň email nebo telefon."
            )
            return False

        return True


class ImportSettingsPage(QWizardPage):
    """Stránka nastavení importu"""

    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard
        self.setTitle("3. Nastavení importu")
        self.setSubTitle("Nastavte parametry importu")
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Výchozí skupina
        group_frame = QGroupBox("👥 Zákaznická skupina")
        group_layout = QHBoxLayout(group_frame)

        group_layout.addWidget(QLabel("Výchozí skupina:"))
        self.cb_group = QComboBox()
        self.cb_group.addItems(["Standardní", "VIP", "Firemní", "Pojišťovna"])
        group_layout.addWidget(self.cb_group)
        group_layout.addStretch()

        layout.addWidget(group_frame)

        # Duplikáty
        duplicates_frame = QGroupBox("🔄 Zpracování duplikátů")
        duplicates_layout = QVBoxLayout(duplicates_frame)

        self.rb_skip = QCheckBox("Přeskočit duplikáty (podle emailu, telefonu, IČO)")
        self.rb_skip.setChecked(True)
        duplicates_layout.addWidget(self.rb_skip)

        self.rb_update = QCheckBox("Aktualizovat existující záznamy")
        duplicates_layout.addWidget(self.rb_update)

        layout.addWidget(duplicates_frame)

        # Validace
        validation_frame = QGroupBox("✅ Validace")
        validation_layout = QVBoxLayout(validation_frame)

        self.chk_validate_email = QCheckBox("Validovat formát emailu")
        self.chk_validate_email.setChecked(True)
        validation_layout.addWidget(self.chk_validate_email)

        self.chk_validate_phone = QCheckBox("Validovat formát telefonu")
        self.chk_validate_phone.setChecked(True)
        validation_layout.addWidget(self.chk_validate_phone)

        layout.addWidget(validation_frame)

        layout.addStretch()

    def validatePage(self):
        """Validace stránky"""
        self.wizard.settings = {
            "default_group": self.cb_group.currentText(),
            "skip_duplicates": self.rb_skip.isChecked(),
            "update_existing": self.rb_update.isChecked(),
            "validate_email": self.chk_validate_email.isChecked(),
            "validate_phone": self.chk_validate_phone.isChecked()
        }
        return True


class ImportProgressPage(QWizardPage):
    """Stránka průběhu importu"""

    def __init__(self, wizard):
        super().__init__(wizard)
        self.wizard = wizard
        self.setTitle("4. Import")
        self.setSubTitle("Probíhá import zákazníků")
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        # Status
        self.lbl_status = QLabel("Připraveno k importu...")
        self.lbl_status.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.lbl_status)

        # Souhrn
        summary_group = QGroupBox("📊 Souhrn importu")
        summary_layout = QVBoxLayout(summary_group)

        self.lbl_imported = QLabel("Importováno: 0")
        self.lbl_imported.setStyleSheet("color: #27ae60; font-weight: bold;")
        summary_layout.addWidget(self.lbl_imported)

        self.lbl_skipped = QLabel("Přeskočeno: 0")
        self.lbl_skipped.setStyleSheet("color: #f39c12;")
        summary_layout.addWidget(self.lbl_skipped)

        self.lbl_errors = QLabel("Chyby: 0")
        self.lbl_errors.setStyleSheet("color: #e74c3c;")
        summary_layout.addWidget(self.lbl_errors)

        layout.addWidget(summary_group)

        # Tlačítko spustit
        self.btn_start = QPushButton("▶️ Spustit import")
        self.btn_start.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; font-weight: bold; padding: 12px;")
        self.btn_start.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_start.clicked.connect(self.start_import)
        layout.addWidget(self.btn_start)

        layout.addStretch()

    def start_import(self):
        """Spuštění importu"""
        self.btn_start.setEnabled(False)
        self.lbl_status.setText("Importování...")
        self.progress.setValue(10)

        try:
            # Validace
            errors, warnings = CustomerImporter.validate_data(
                self.wizard.preview_data,
                self.wizard.mapping
            )

            if errors:
                QMessageBox.critical(
                    self,
                    "Chyby validace",
                    "Nalezeny kritické chyby:\n\n" + "\n".join(errors[:10])
                )
                self.btn_start.setEnabled(True)
                return

            self.progress.setValue(30)

            # Kontrola duplikátů
            duplicates = CustomerImporter.check_duplicates(
                self.wizard.preview_data,
                self.wizard.mapping
            )

            if duplicates and self.wizard.settings.get("skip_duplicates"):
                self.lbl_status.setText(f"Nalezeno {len(duplicates)} duplikátů")

            self.progress.setValue(50)

            # Import
            imported, skipped, import_errors = CustomerImporter.import_customers(
                self.wizard.preview_data,
                self.wizard.mapping,
                self.wizard.settings
            )

            self.progress.setValue(100)

            # Aktualizace souhrnu
            self.lbl_imported.setText(f"Importováno: {imported}")
            self.lbl_skipped.setText(f"Přeskočeno: {skipped}")
            self.lbl_errors.setText(f"Chyby: {len(import_errors)}")

            if import_errors:
                self.lbl_status.setText("Import dokončen s chybami")
            else:
                self.lbl_status.setText("✅ Import úspěšně dokončen!")

            self.wizard.import_completed.emit(imported, skipped, import_errors)

            QMessageBox.information(
                self,
                "Import dokončen",
                f"Importováno: {imported}\nPřeskočeno: {skipped}\nChyby: {len(import_errors)}"
            )

        except Exception as e:
            self.lbl_status.setText(f"❌ Chyba: {str(e)}")
            QMessageBox.critical(self, "Chyba importu", str(e))
            self.btn_start.setEnabled(True)

    def isComplete(self):
        """Kontrola dokončení"""
        return self.progress.value() == 100


