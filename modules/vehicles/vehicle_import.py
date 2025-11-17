# -*- coding: utf-8 -*-
"""
Import vozidel z externích zdrojů - CSV, Excel, JSON s mapováním sloupců a validací
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QFrame, QMessageBox, QDialog, QFormLayout, QCheckBox, QProgressBar,
    QFileDialog, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QRadioButton, QButtonGroup, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QBrush
from datetime import datetime
from pathlib import Path
import csv
import json
import config
from database_manager import db


class VehicleImporter:
    """Třída pro import vozidel"""

    def __init__(self):
        self.data = []
        self.headers = []
        self.column_mapping = {}
        self.import_results = {
            'imported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }

    def load_csv(self, file_path, delimiter=',', encoding='utf-8'):
        """Načtení dat z CSV"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                # Automatická detekce oddělovače
                sample = f.read(1024)
                f.seek(0)

                if delimiter == 'auto':
                    sniffer = csv.Sniffer()
                    try:
                        dialect = sniffer.sniff(sample)
                        delimiter = dialect.delimiter
                    except:
                        delimiter = ',' if sample.count(',') > sample.count(';') else ';'

                reader = csv.reader(f, delimiter=delimiter)
                rows = list(reader)

                if rows:
                    self.headers = rows[0]
                    self.data = rows[1:]
                    return True, f"Načteno {len(self.data)} řádků"
                else:
                    return False, "Soubor je prázdný"

        except UnicodeDecodeError:
            # Zkusit jiné kódování
            return self.load_csv(file_path, delimiter, 'cp1250')
        except Exception as e:
            return False, f"Chyba při načítání CSV: {e}"

    def load_excel(self, file_path):
        """Načtení dat z Excelu"""
        try:
            import openpyxl

            wb = openpyxl.load_workbook(file_path, data_only=True)
            ws = wb.active

            rows = list(ws.iter_rows(values_only=True))

            if rows:
                self.headers = [str(h) if h else f"Sloupec_{i}" for i, h in enumerate(rows[0], 1)]
                self.data = [[str(cell) if cell else '' for cell in row] for row in rows[1:]]
                return True, f"Načteno {len(self.data)} řádků"
            else:
                return False, "List je prázdný"

        except ImportError:
            return False, "Pro import z Excelu je potřeba nainstalovat openpyxl:\npip install openpyxl"
        except Exception as e:
            return False, f"Chyba při načítání Excelu: {e}"

    def load_json(self, file_path):
        """Načtení dat z JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            if isinstance(json_data, list) and len(json_data) > 0:
                if isinstance(json_data[0], dict):
                    self.headers = list(json_data[0].keys())
                    self.data = [[str(item.get(h, '')) for h in self.headers] for item in json_data]
                    return True, f"Načteno {len(self.data)} záznamů"
                else:
                    return False, "Neplatný formát JSON (očekáváno pole objektů)"
            else:
                return False, "JSON je prázdný nebo má neplatný formát"

        except Exception as e:
            return False, f"Chyba při načítání JSON: {e}"

    def get_preview(self, num_rows=10):
        """Získání náhledu dat"""
        return self.data[:num_rows]

    def set_column_mapping(self, mapping):
        """Nastavení mapování sloupců"""
        self.column_mapping = mapping

    def validate_row(self, row_data):
        """Validace jednoho řádku"""
        errors = []

        # SPZ - povinné a unikátní
        spz = dict(row_data).get('license_plate', '').strip().upper()
        if not spz:
            errors.append("SPZ je povinný údaj")
        elif len(spz) > 20:
            errors.append("SPZ je příliš dlouhá (max 20 znaků)")

        # Značka - povinná
        brand = dict(row_data).get('brand', '').strip()
        if not brand:
            errors.append("Značka je povinný údaj")

        # Model - povinný
        model = dict(row_data).get('model', '').strip()
        if not model:
            errors.append("Model je povinný údaj")

        # Rok výroby - validace rozsahu
        year = dict(row_data).get('year', '')
        if year:
            try:
                year_int = int(year)
                if year_int < 1900 or year_int > datetime.now().year + 1:
                    errors.append(f"Neplatný rok výroby: {year}")
            except:
                errors.append(f"Rok výroby musí být číslo: {year}")

        # VIN - validace délky
        vin = dict(row_data).get('vin', '').strip().upper()
        if vin and len(vin) != 17:
            errors.append(f"VIN musí mít 17 znaků (má {len(vin)})")

        return errors

    def get_row_data(self, row):
        """Získání dat z řádku podle mapování"""
        data = {}

        for target_field, source_col in self.column_mapping.items():
            if source_col and source_col in self.headers:
                col_index = self.headers.index(source_col)
                if col_index < len(row):
                    data[target_field] = row[col_index]
                else:
                    data[target_field] = ''
            else:
                data[target_field] = ''

        return data

    def find_or_create_customer(self, customer_name):
        """Vyhledání nebo vytvoření zákazníka"""
        if not customer_name:
            return None

        # Rozdělení jména
        parts = customer_name.strip().split(' ', 1)
        first_name = parts[0] if parts else customer_name
        last_name = parts[1] if len(parts) > 1 else ''

        # Hledání existujícího zákazníka
        existing = db.fetch_one("""
            SELECT id FROM customers
            WHERE first_name = ? AND last_name = ?
        """, (first_name, last_name))

        if existing:
            return existing['id']

        # Vytvoření nového zákazníka
        try:
            db.execute_query("""
                INSERT INTO customers (first_name, last_name)
                VALUES (?, ?)
            """, (first_name, last_name))

            new_customer = db.fetch_one(
                "SELECT id FROM customers ORDER BY id DESC LIMIT 1"
            )
            return new_customer['id'] if new_customer else None
        except:
            return None

    def import_vehicles(self, conflict_mode='skip'):
        """Import vozidel do databáze"""
        self.import_results = {
            'imported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }

        for row_num, row in enumerate(self.data, 2):  # 2 protože první řádek je hlavička
            row_data = self.get_row_data(row)

            # Validace
            errors = self.validate_row(row_data)
            if errors:
                self.import_results['errors'].append(f"Řádek {row_num}: {', '.join(errors)}")
                continue

            # Příprava dat
            spz = dict(row_data).get('license_plate', '').strip().upper()
            brand = dict(row_data).get('brand', '').strip()
            model = dict(row_data).get('model', '').strip()

            year = None
            if dict(row_data).get('year'):
                try:
                    year = int(row_data['year'])
                except:
                    pass

            vin = dict(row_data).get('vin', '').strip().upper() or None
            color = dict(row_data).get('color', '').strip() or None
            engine_type = dict(row_data).get('engine_type', '').strip() or None
            fuel_type = dict(row_data).get('fuel_type', '').strip() or None

            mileage = None
            if dict(row_data).get('mileage'):
                try:
                    mileage = int(str(row_data['mileage']).replace(' ', '').replace('km', ''))
                except:
                    pass

            notes = dict(row_data).get('notes', '').strip() or None

            # Zákazník
            customer_id = None
            if dict(row_data).get('customer_name'):
                customer_id = self.find_or_create_customer(row_data['customer_name'])

            # Kontrola existence
            existing = db.fetch_one(
                "SELECT id FROM vehicles WHERE license_plate = ?",
                (spz,)
            )

            try:
                if existing:
                    if conflict_mode == 'skip':
                        self.import_results['skipped'] += 1
                        continue
                    elif conflict_mode == 'update':
                        # Aktualizace existujícího
                        db.execute_query("""
                            UPDATE vehicles SET
                                brand = ?,
                                model = ?,
                                year = ?,
                                vin = ?,
                                color = ?,
                                engine_type = ?,
                                fuel_type = ?,
                                mileage = ?,
                                notes = ?,
                                customer_id = COALESCE(?, customer_id),
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (brand, model, year, vin, color, engine_type, fuel_type,
                              mileage, notes, customer_id, existing['id']))
                        self.import_results['updated'] += 1
                    else:  # duplicate
                        # Vytvoření duplikátu s upravenou SPZ
                        new_spz = f"{spz}_DUP"
                        db.execute_query("""
                            INSERT INTO vehicles (
                                license_plate, brand, model, year, vin, color,
                                engine_type, fuel_type, mileage, notes, customer_id
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (new_spz, brand, model, year, vin, color, engine_type,
                              fuel_type, mileage, notes, customer_id))
                        self.import_results['imported'] += 1
                else:
                    # Nové vozidlo
                    db.execute_query("""
                        INSERT INTO vehicles (
                            license_plate, brand, model, year, vin, color,
                            engine_type, fuel_type, mileage, notes, customer_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (spz, brand, model, year, vin, color, engine_type,
                          fuel_type, mileage, notes, customer_id))
                    self.import_results['imported'] += 1

            except Exception as e:
                self.import_results['errors'].append(f"Řádek {row_num}: {e}")

        return self.import_results

    def create_report(self):
        """Vytvoření reportu importu"""
        report = []
        report.append("=" * 50)
        report.append("REPORT IMPORTU VOZIDEL")
        report.append("=" * 50)
        report.append(f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        report.append("")
        report.append("SOUHRN:")
        report.append(f"  ✅ Importováno: {self.import_results['imported']}")
        report.append(f"  🔄 Aktualizováno: {self.import_results['updated']}")
        report.append(f"  ⏭️ Přeskočeno: {self.import_results['skipped']}")
        report.append(f"  ❌ Chyb: {len(self.import_results['errors'])}")
        report.append("")

        if self.import_results['errors']:
            report.append("CHYBY:")
            for error in self.import_results['errors'][:50]:  # Max 50 chyb
                report.append(f"  • {error}")

            if len(self.import_results['errors']) > 50:
                report.append(f"  ... a dalších {len(self.import_results['errors']) - 50} chyb")

        report.append("")
        report.append("=" * 50)

        return "\n".join(report)


class ImportDialog(QDialog):
    """Dialog pro import vozidel"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.importer = VehicleImporter()
        self.file_path = None
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("📥 Import vozidel")
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Krok 1: Výběr souboru
        file_group = QGroupBox("1. Výběr souboru")
        file_layout = QHBoxLayout(file_group)

        self.file_label = QLabel("Není vybrán žádný soubor")
        self.file_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
            }
        """)
        file_layout.addWidget(self.file_label)

        btn_browse = QPushButton("📁 Procházet")
        btn_browse.clicked.connect(self.browse_file)
        file_layout.addWidget(btn_browse)

        layout.addWidget(file_group)

        # Krok 2: Náhled dat
        preview_group = QGroupBox("2. Náhled dat (prvních 10 řádků)")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(200)
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview_table.setAlternatingRowColors(True)
        preview_layout.addWidget(self.preview_table)

        layout.addWidget(preview_group)

        # Krok 3: Mapování sloupců
        mapping_group = QGroupBox("3. Mapování sloupců")
        mapping_layout = QFormLayout(mapping_group)

        self.mapping_combos = {}

        target_fields = [
            ('license_plate', 'SPZ *'),
            ('brand', 'Značka *'),
            ('model', 'Model *'),
            ('year', 'Rok výroby'),
            ('vin', 'VIN'),
            ('color', 'Barva'),
            ('engine_type', 'Typ motoru'),
            ('fuel_type', 'Palivo'),
            ('mileage', 'Stav km'),
            ('notes', 'Poznámky'),
            ('customer_name', 'Zákazník (jméno)')
        ]

        for field_id, field_name in target_fields:
            combo = QComboBox()
            combo.addItem("-- nevybráno --")
            combo.setMinimumWidth(200)
            self.mapping_combos[field_id] = combo
            mapping_layout.addRow(f"{field_name}:", combo)

        layout.addWidget(mapping_group)

        # Krok 4: Konflikty
        conflict_group = QGroupBox("4. Chování při konfliktech (existující SPZ)")
        conflict_layout = QVBoxLayout(conflict_group)

        self.conflict_group = QButtonGroup(self)

        self.conflict_skip = QRadioButton("Přeskočit existující vozidla")
        self.conflict_skip.setChecked(True)
        self.conflict_group.addButton(self.conflict_skip)
        conflict_layout.addWidget(self.conflict_skip)

        self.conflict_update = QRadioButton("Aktualizovat existující vozidla")
        self.conflict_group.addButton(self.conflict_update)
        conflict_layout.addWidget(self.conflict_update)

        self.conflict_duplicate = QRadioButton("Vytvořit duplikát (přidá _DUP k SPZ)")
        self.conflict_group.addButton(self.conflict_duplicate)
        conflict_layout.addWidget(self.conflict_duplicate)

        layout.addWidget(conflict_group)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Status
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Tlačítka
        buttons_layout = QHBoxLayout()

        btn_validate = QPushButton("🔍 Validovat data")
        btn_validate.clicked.connect(self.validate_data)
        buttons_layout.addWidget(btn_validate)

        buttons_layout.addStretch()

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        self.btn_import = QPushButton("📥 Importovat")
        self.btn_import.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #219a52;
            }}
            QPushButton:disabled {{
                background-color: #95a5a6;
            }}
        """)
        self.btn_import.setEnabled(False)
        self.btn_import.clicked.connect(self.perform_import)
        buttons_layout.addWidget(self.btn_import)

        layout.addLayout(buttons_layout)

    def browse_file(self):
        """Výběr souboru pro import"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Vybrat soubor pro import",
            "",
            "Všechny podporované (*.csv *.xlsx *.xls *.json);;"
            "CSV soubory (*.csv);;"
            "Excel soubory (*.xlsx *.xls);;"
            "JSON soubory (*.json);;"
            "Všechny soubory (*.*)"
        )

        if file_path:
            self.file_path = file_path
            self.load_file()

    def load_file(self):
        """Načtení vybraného souboru"""
        path = Path(self.file_path)

        self.status_label.setText("Načítám soubor...")
        QApplication.processEvents()

        success = False
        message = ""

        if path.suffix.lower() == '.csv':
            success, message = self.importer.load_csv(self.file_path, delimiter='auto')
        elif path.suffix.lower() in ['.xlsx', '.xls']:
            success, message = self.importer.load_excel(self.file_path)
        elif path.suffix.lower() == '.json':
            success, message = self.importer.load_json(self.file_path)
        else:
            message = f"Nepodporovaný formát souboru: {path.suffix}"

        if success:
            self.file_label.setText(f"✅ {path.name}")
            self.file_label.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    background-color: #d5f5e3;
                    border-radius: 5px;
                    color: #27ae60;
                }
            """)
            self.status_label.setText(message)
            self.update_preview()
            self.update_mapping_combos()
            self.btn_import.setEnabled(True)
        else:
            self.file_label.setText(f"❌ Chyba při načítání")
            self.file_label.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    background-color: #fadbd8;
                    border-radius: 5px;
                    color: #e74c3c;
                }
            """)
            self.status_label.setText(message)
            QMessageBox.critical(self, "Chyba", message)

    def update_preview(self):
        """Aktualizace náhledu dat"""
        self.preview_table.clear()

        if not self.importer.headers:
            return

        self.preview_table.setColumnCount(len(self.importer.headers))
        self.preview_table.setHorizontalHeaderLabels(self.importer.headers)

        preview_data = self.importer.get_preview(10)
        self.preview_table.setRowCount(len(preview_data))

        for row_idx, row in enumerate(preview_data):
            for col_idx, value in enumerate(row):
                self.preview_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

        self.preview_table.resizeColumnsToContents()

    def update_mapping_combos(self):
        """Aktualizace comboboxů pro mapování"""
        for combo in self.mapping_combos.values():
            current_text = combo.currentText()
            combo.clear()
            combo.addItem("-- nevybráno --")

            for header in self.importer.headers:
                combo.addItem(header)

            # Pokusit se automaticky namapovat
            if current_text in self.importer.headers:
                combo.setCurrentText(current_text)

        # Automatické mapování podle názvů sloupců
        auto_mapping = {
            'license_plate': ['SPZ', 'spz', 'RZ', 'rz', 'license_plate', 'plate', 'registrační značka'],
            'brand': ['Značka', 'značka', 'brand', 'manufacturer', 'výrobce'],
            'model': ['Model', 'model', 'typ', 'type'],
            'year': ['Rok', 'rok', 'year', 'rok výroby', 'vyrobeno'],
            'vin': ['VIN', 'vin', 'číslo karoserie'],
            'color': ['Barva', 'barva', 'color', 'colour'],
            'engine_type': ['Motor', 'motor', 'engine', 'typ motoru'],
            'fuel_type': ['Palivo', 'palivo', 'fuel', 'pohon'],
            'mileage': ['km', 'kilometry', 'mileage', 'nájezd', 'stav km'],
            'notes': ['Poznámky', 'poznámky', 'notes', 'note', 'pozn'],
            'customer_name': ['Zákazník', 'zákazník', 'customer', 'majitel', 'owner']
        }

        for field_id, possible_names in auto_mapping.items():
            combo = self.mapping_combos[field_id]
            for header in self.importer.headers:
                if header.lower() in [n.lower() for n in possible_names] or header in possible_names:
                    combo.setCurrentText(header)
                    break

    def get_mapping(self):
        """Získání mapování sloupců"""
        mapping = {}
        for field_id, combo in self.mapping_combos.items():
            selected = combo.currentText()
            if selected != "-- nevybráno --":
                mapping[field_id] = selected
            else:
                mapping[field_id] = None
        return mapping

    def validate_data(self):
        """Validace dat před importem"""
        mapping = self.get_mapping()

        # Kontrola povinných polí
        required_fields = ['license_plate', 'brand', 'model']
        missing = []

        for field in required_fields:
            if not mapping.get(field):
                field_names = {
                    'license_plate': 'SPZ',
                    'brand': 'Značka',
                    'model': 'Model'
                }
                missing.append(field_names[field])

        if missing:
            QMessageBox.warning(
                self,
                "Chybí povinná pole",
                f"Namapujte následující povinná pole:\n• {', '.join(missing)}"
            )
            return

        self.importer.set_column_mapping(mapping)

        # Validace všech řádků
        errors = []
        valid_count = 0

        for row_num, row in enumerate(self.importer.data, 2):
            row_data = self.importer.get_row_data(row)
            row_errors = self.importer.validate_row(row_data)

            if row_errors:
                errors.append(f"Řádek {row_num}: {', '.join(row_errors)}")
            else:
                valid_count += 1

        # Zobrazení výsledků
        if errors:
            error_text = "\n".join(errors[:20])
            if len(errors) > 20:
                error_text += f"\n... a dalších {len(errors) - 20} chyb"

            QMessageBox.warning(
                self,
                "Výsledky validace",
                f"Platných záznamů: {valid_count}\n"
                f"Neplatných záznamů: {len(errors)}\n\n"
                f"Chyby:\n{error_text}"
            )
        else:
            QMessageBox.information(
                self,
                "Validace úspěšná",
                f"Všechny záznamy jsou platné.\n"
                f"Připraveno k importu: {valid_count} vozidel"
            )

    def get_conflict_mode(self):
        """Získání režimu řešení konfliktů"""
        if self.conflict_skip.isChecked():
            return 'skip'
        elif self.conflict_update.isChecked():
            return 'update'
        else:
            return 'duplicate'

    def perform_import(self):
        """Provedení importu"""
        mapping = self.get_mapping()

        # Kontrola povinných polí
        required_fields = ['license_plate', 'brand', 'model']
        missing = []

        for field in required_fields:
            if not mapping.get(field):
                field_names = {
                    'license_plate': 'SPZ',
                    'brand': 'Značka',
                    'model': 'Model'
                }
                missing.append(field_names[field])

        if missing:
            QMessageBox.warning(
                self,
                "Chybí povinná pole",
                f"Namapujte následující povinná pole:\n• {', '.join(missing)}"
            )
            return

        # Potvrzení
        reply = QMessageBox.question(
            self,
            "Potvrzení importu",
            f"Chystáte se importovat {len(self.importer.data)} vozidel.\n\n"
            f"Chcete pokračovat?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self.importer.set_column_mapping(mapping)
        conflict_mode = self.get_conflict_mode()

        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.btn_import.setEnabled(False)
        self.status_label.setText("Probíhá import...")
        QApplication.processEvents()

        try:
            results = self.importer.import_vehicles(conflict_mode)

            self.progress.setValue(100)

            # Vytvoření reportu
            report = self.importer.create_report()

            # Zobrazení výsledků
            dialog = ImportReportDialog(report, results, self)
            dialog.exec()

            if results['imported'] > 0 or results['updated'] > 0:
                self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při importu:\n{e}")

        finally:
            self.progress.setVisible(False)
            self.btn_import.setEnabled(True)
            self.status_label.setText("")


class ImportReportDialog(QDialog):
    """Dialog s reportem importu"""

    def __init__(self, report_text, results, parent=None):
        super().__init__(parent)
        self.report_text = report_text
        self.results = results
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("📊 Report importu")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Souhrn
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        summary_layout = QHBoxLayout(summary_frame)

        imported_label = QLabel(f"✅ Importováno: <b>{self.results['imported']}</b>")
        updated_label = QLabel(f"🔄 Aktualizováno: <b>{self.results['updated']}</b>")
        skipped_label = QLabel(f"⏭️ Přeskočeno: <b>{self.results['skipped']}</b>")
        errors_label = QLabel(f"❌ Chyb: <b>{len(self.results['errors'])}</b>")

        summary_layout.addWidget(imported_label)
        summary_layout.addWidget(updated_label)
        summary_layout.addWidget(skipped_label)
        summary_layout.addWidget(errors_label)

        layout.addWidget(summary_frame)

        # Report text
        report_text = QTextEdit()
        report_text.setPlainText(self.report_text)
        report_text.setReadOnly(True)
        report_text.setFont(QFont("Courier", 10))
        layout.addWidget(report_text)

        # Tlačítka
        buttons_layout = QHBoxLayout()

        btn_save = QPushButton("💾 Uložit report")
        btn_save.clicked.connect(self.save_report)
        buttons_layout.addWidget(btn_save)

        buttons_layout.addStretch()

        btn_close = QPushButton("✅ Zavřít")
        btn_close.clicked.connect(self.accept)
        buttons_layout.addWidget(btn_close)

        layout.addLayout(buttons_layout)

    def save_report(self):
        """Uložení reportu do souboru"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit report",
            f"import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Textové soubory (*.txt)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.report_text)
                QMessageBox.information(self, "Uloženo", f"Report byl uložen do:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit report:\n{e}")


# Pro import v hlavním widgetu
from PyQt6.QtWidgets import QApplication
