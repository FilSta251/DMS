# -*- coding: utf-8 -*-
"""
Správa dokumentů vozidla - upload, náhled, stažení, kontrola platnosti
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QFrame, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QDateEdit, QFileDialog, QGroupBox,
    QTextEdit
)
from PyQt6.QtCore import Qt, QDate, QSize
from PyQt6.QtGui import QFont, QColor, QBrush, QPixmap
from datetime import datetime, date, timedelta
from pathlib import Path
import shutil
import config
from database_manager import db


class VehicleDocumentsWidget(QWidget):
    """Widget pro správu dokumentů vozidla"""

    def __init__(self, vehicle_id, parent=None):
        super().__init__(parent)
        self.vehicle_id = vehicle_id
        self.documents_dir = self.ensure_documents_directory()
        self.init_ui()
        self.load_documents()

    def ensure_documents_directory(self):
        """Zajištění existence adresáře pro dokumenty"""
        docs_dir = Path(config.DATA_DIR) / "vehicle_documents" / str(self.vehicle_id)
        docs_dir.mkdir(parents=True, exist_ok=True)
        return docs_dir

    def ensure_documents_table(self):
        """Zajištění existence tabulky pro dokumenty v DB"""
        try:
            db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicle_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_id INTEGER NOT NULL,
                    document_type TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    valid_until DATE,
                    description TEXT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
                )
            """)
            db.connection.commit()
        except Exception as e:
            print(f"Chyba při vytváření tabulky dokumentů: {e}")

    def init_ui(self):
        """Inicializace uživatelského rozhraní"""
        self.ensure_documents_table()

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        # Hlavička
        header_panel = self.create_header_panel()
        layout.addWidget(header_panel)

        # Upozornění na expirující dokumenty
        self.alerts_panel = self.create_alerts_panel()
        layout.addWidget(self.alerts_panel)

        # Tabulka dokumentů
        self.table = self.create_table()
        layout.addWidget(self.table)

    def create_header_panel(self):
        """Vytvoření hlavičky"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QHBoxLayout(panel)
        layout.setSpacing(15)

        # Titulek
        title = QLabel("📁 Dokumenty vozidla")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        layout.addStretch()

        # Filtr typu
        type_label = QLabel("Typ:")
        self.type_filter = QComboBox()
        self.type_filter.addItems([
            "Vše",
            "Technický průkaz",
            "STK protokol",
            "Emisní protokol",
            "Pojistná smlouva",
            "Kupní smlouva",
            "Servisní kniha",
            "Ostatní"
        ])
        self.type_filter.setMinimumWidth(150)
        self.type_filter.currentTextChanged.connect(self.filter_documents)

        layout.addWidget(type_label)
        layout.addWidget(self.type_filter)

        # Tlačítko nahrát
        btn_upload = QPushButton("📤 Nahrát dokument")
        btn_upload.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #219a52;
            }}
        """)
        btn_upload.clicked.connect(self.upload_document)
        layout.addWidget(btn_upload)

        return panel

    def create_alerts_panel(self):
        """Vytvoření panelu s upozorněními"""
        panel = QFrame()
        panel.setObjectName("alerts_panel")
        panel.setStyleSheet("""
            QFrame#alerts_panel {
                background-color: #fef9e7;
                border: 2px solid #f39c12;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setSpacing(5)

        self.alerts_label = QLabel("")
        self.alerts_label.setWordWrap(True)
        self.alerts_label.setStyleSheet("""
            QLabel {
                color: #d35400;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.alerts_label)

        # Skrýt panel pokud nejsou upozornění
        panel.hide()

        return panel

    def create_table(self):
        """Vytvoření tabulky dokumentů"""
        table = QTableWidget()
        table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                gridline-color: #ecf0f1;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                font-weight: bold;
                border: none;
            }
        """)

        # Sloupce
        columns = ["ID", "Typ dokumentu", "Název souboru", "Platnost do", "Popis", "Nahráno", "Velikost", "Akce"]
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)

        # Nastavení
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setColumnHidden(0, True)  # Skrýt ID

        # Roztažení sloupců
        header = table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        return table

    def load_documents(self):
        """Načtení dokumentů z databáze"""
        try:
            documents = db.fetch_all("""
                SELECT * FROM vehicle_documents
                WHERE vehicle_id = ?
                ORDER BY uploaded_at DESC
            """, (self.vehicle_id,))

            self.populate_table(documents)
            self.check_expiration(documents)

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst dokumenty:\n{e}")

    def populate_table(self, documents):
        """Naplnění tabulky dokumenty"""
        self.table.setRowCount(0)

        today = date.today()
        warning_date = today + timedelta(days=30)

        for doc in documents:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # ID (skrytý)
            id_item = QTableWidgetItem()
            id_item.setData(Qt.ItemDataRole.DisplayRole, doc['id'])
            self.table.setItem(row, 0, id_item)

            # Typ dokumentu s ikonou
            doc_type = doc['document_type'] or ''
            icon = self.get_document_icon(doc_type)
            type_item = QTableWidgetItem(f"{icon} {doc_type}")
            self.table.setItem(row, 1, type_item)

            # Název souboru
            self.table.setItem(row, 2, QTableWidgetItem(doc['file_name'] or ''))

            # Platnost do s barevným pozadím
            valid_until_item = QTableWidgetItem()
            if doc['valid_until']:
                try:
                    valid_date = datetime.strptime(str(doc['valid_until']), "%Y-%m-%d").date()
                    valid_until_item.setText(valid_date.strftime("%d.%m.%Y"))

                    if valid_date < today:
                        valid_until_item.setBackground(QBrush(QColor("#e74c3c")))
                        valid_until_item.setForeground(QBrush(QColor("white")))
                    elif valid_date <= warning_date:
                        valid_until_item.setBackground(QBrush(QColor("#f39c12")))
                        valid_until_item.setForeground(QBrush(QColor("white")))
                    else:
                        valid_until_item.setBackground(QBrush(QColor("#27ae60")))
                        valid_until_item.setForeground(QBrush(QColor("white")))
                except:
                    valid_until_item.setText("Neplatné datum")
            else:
                valid_until_item.setText("-")
            self.table.setItem(row, 3, valid_until_item)

            # Popis
            description = doc['description'] or ''
            if len(description) > 50:
                description = description[:47] + "..."
            self.table.setItem(row, 4, QTableWidgetItem(description))

            # Datum nahrání
            if doc['uploaded_at']:
                try:
                    uploaded = datetime.strptime(str(doc['uploaded_at']), "%Y-%m-%d %H:%M:%S")
                    uploaded_text = uploaded.strftime("%d.%m.%Y")
                except:
                    uploaded_text = str(doc['uploaded_at'])[:10]
            else:
                uploaded_text = "-"
            self.table.setItem(row, 5, QTableWidgetItem(uploaded_text))

            # Velikost souboru
            file_path = Path(doc['file_path'])
            if file_path.exists():
                size_bytes = file_path.stat().st_size
                size_text = self.format_file_size(size_bytes)
            else:
                size_text = "Soubor nenalezen"
            self.table.setItem(row, 6, QTableWidgetItem(size_text))

            # Tlačítka akcí
            actions_widget = self.create_actions_widget(doc['id'], doc['file_path'])
            self.table.setCellWidget(row, 7, actions_widget)

    def get_document_icon(self, doc_type):
        """Získání ikony podle typu dokumentu"""
        icons = {
            "Technický průkaz": "📜",
            "STK protokol": "🔧",
            "Emisní protokol": "💨",
            "Pojistná smlouva": "📄",
            "Kupní smlouva": "📋",
            "Servisní kniha": "📝",
            "Ostatní": "📊"
        }
        return icons.get(doc_type, "📄")

    def format_file_size(self, size_bytes):
        """Formátování velikosti souboru"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def create_actions_widget(self, doc_id, file_path):
        """Vytvoření widgetu s akcemi"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)

        # Náhled
        btn_preview = QPushButton("👁️")
        btn_preview.setToolTip("Náhled")
        btn_preview.setFixedSize(30, 30)
        btn_preview.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_preview.clicked.connect(lambda: self.preview_document(file_path))
        layout.addWidget(btn_preview)

        # Stažení
        btn_download = QPushButton("📥")
        btn_download.setToolTip("Stáhnout")
        btn_download.setFixedSize(30, 30)
        btn_download.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        btn_download.clicked.connect(lambda: self.download_document(file_path))
        layout.addWidget(btn_download)

        # Smazání
        btn_delete = QPushButton("🗑️")
        btn_delete.setToolTip("Smazat")
        btn_delete.setFixedSize(30, 30)
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        btn_delete.clicked.connect(lambda: self.delete_document(doc_id))
        layout.addWidget(btn_delete)

        return widget

    def check_expiration(self, documents):
        """Kontrola platnosti dokumentů"""
        today = date.today()
        warning_date = today + timedelta(days=30)

        alerts = []

        for doc in documents:
            if doc['valid_until']:
                try:
                    valid_date = datetime.strptime(str(doc['valid_until']), "%Y-%m-%d").date()
                    doc_type = doc['document_type']

                    if valid_date < today:
                        alerts.append(f"⚠️ <b>{doc_type}</b> - NEPLATNÝ (vypršel {valid_date.strftime('%d.%m.%Y')})")
                    elif valid_date <= warning_date:
                        days_left = (valid_date - today).days
                        alerts.append(f"⚠️ <b>{doc_type}</b> - expiruje za {days_left} dní ({valid_date.strftime('%d.%m.%Y')})")
                except:
                    pass

        if alerts:
            self.alerts_label.setText("<br>".join(alerts))
            self.alerts_panel.show()
        else:
            self.alerts_panel.hide()

    def filter_documents(self):
        """Filtrování dokumentů podle typu"""
        selected_type = self.type_filter.currentText()

        for row in range(self.table.rowCount()):
            if selected_type == "Vše":
                self.table.setRowHidden(row, False)
            else:
                type_item = self.table.item(row, 1)
                if type_item:
                    # Odstranit ikonu pro porovnání
                    doc_type = type_item.text().split(" ", 1)[-1]
                    self.table.setRowHidden(row, doc_type != selected_type)

    def upload_document(self):
        """Nahrání nového dokumentu"""
        dialog = UploadDocumentDialog(self)
        if dialog.exec():
            data = dialog.get_data()

            # Kopírování souboru
            source_path = Path(data['file_path'])
            if not source_path.exists():
                QMessageBox.critical(self, "Chyba", "Vybraný soubor neexistuje.")
                return

            # Vytvoření unikátního názvu
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{timestamp}_{source_path.name}"
            dest_path = self.documents_dir / new_filename

            try:
                shutil.copy2(source_path, dest_path)

                # Uložení do databáze
                db.execute_query("""
                    INSERT INTO vehicle_documents (
                        vehicle_id, document_type, file_name, file_path,
                        valid_until, description
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.vehicle_id,
                    data['document_type'],
                    source_path.name,
                    str(dest_path),
                    data['valid_until'],
                    data['description']
                ))

                self.load_documents()
                QMessageBox.information(self, "Úspěch", "Dokument byl úspěšně nahrán.")

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se nahrát dokument:\n{e}")

    def preview_document(self, file_path):
        """Náhled dokumentu"""
        path = Path(file_path)

        if not path.exists():
            QMessageBox.warning(self, "Chyba", "Soubor nebyl nalezen.")
            return

        # Otevření v systémovém prohlížeči
        try:
            import subprocess
            import sys

            if sys.platform == 'win32':
                subprocess.run(['start', '', str(path)], shell=True)
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(path)])
            else:
                subprocess.run(['xdg-open', str(path)])
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se otevřít soubor:\n{e}")

    def download_document(self, file_path):
        """Stažení (kopírování) dokumentu"""
        source_path = Path(file_path)

        if not source_path.exists():
            QMessageBox.warning(self, "Chyba", "Soubor nebyl nalezen.")
            return

        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit dokument",
            source_path.name,
            f"Všechny soubory (*{source_path.suffix})"
        )

        if dest_path:
            try:
                shutil.copy2(source_path, dest_path)
                QMessageBox.information(self, "Úspěch", f"Dokument byl uložen do:\n{dest_path}")
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit dokument:\n{e}")

    def delete_document(self, doc_id):
        """Smazání dokumentu"""
        reply = QMessageBox.question(
            self,
            "Potvrzení",
            "Opravdu chcete smazat tento dokument?\nTato akce je nevratná.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Získání cesty k souboru
                doc = db.fetch_one(
                    "SELECT file_path FROM vehicle_documents WHERE id = ?",
                    (doc_id,)
                )

                if doc:
                    # Smazání souboru
                    file_path = Path(doc['file_path'])
                    if file_path.exists():
                        file_path.unlink()

                    # Smazání záznamu z DB
                    db.execute_query(
                        "DELETE FROM vehicle_documents WHERE id = ?",
                        (doc_id,)
                    )

                    self.load_documents()
                    QMessageBox.information(self, "Úspěch", "Dokument byl smazán.")

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat dokument:\n{e}")


class UploadDocumentDialog(QDialog):
    """Dialog pro nahrání dokumentu"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path = None
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("📤 Nahrát dokument")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Typ dokumentu
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Technický průkaz",
            "STK protokol",
            "Emisní protokol",
            "Pojistná smlouva",
            "Kupní smlouva",
            "Servisní kniha",
            "Ostatní"
        ])
        form_layout.addRow("Typ dokumentu *:", self.type_combo)

        # Výběr souboru
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Nevybrán žádný soubor")
        self.file_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #ecf0f1;
                border-radius: 5px;
            }
        """)
        file_layout.addWidget(self.file_label)

        btn_browse = QPushButton("📁 Procházet")
        btn_browse.clicked.connect(self.browse_file)
        file_layout.addWidget(btn_browse)

        form_layout.addRow("Soubor *:", file_layout)

        # Platnost do
        self.valid_until_input = QDateEdit()
        self.valid_until_input.setCalendarPopup(True)
        self.valid_until_input.setDate(QDate.currentDate().addYears(2))
        self.valid_until_input.setDisplayFormat("dd.MM.yyyy")
        self.valid_until_input.setSpecialValueText("Bez platnosti")
        form_layout.addRow("Platnost do:", self.valid_until_input)

        # Popis
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Popis dokumentu...")
        self.description_input.setMaximumHeight(80)
        form_layout.addRow("Popis:", self.description_input)

        layout.addLayout(form_layout)

        # Podporované formáty
        formats_label = QLabel(
            "Podporované formáty: PDF, JPG, JPEG, PNG, DOC, DOCX, XLS, XLSX"
        )
        formats_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(formats_label)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        btn_upload = QPushButton("📤 Nahrát")
        btn_upload.setStyleSheet(f"""
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
        """)
        btn_upload.clicked.connect(self.validate_and_accept)
        buttons_layout.addWidget(btn_upload)

        layout.addLayout(buttons_layout)

    def browse_file(self):
        """Výběr souboru"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Vybrat dokument",
            "",
            "Dokumenty (*.pdf *.jpg *.jpeg *.png *.doc *.docx *.xls *.xlsx);;Všechny soubory (*.*)"
        )

        if file_path:
            self.file_path = file_path
            file_name = Path(file_path).name
            if len(file_name) > 40:
                file_name = file_name[:37] + "..."
            self.file_label.setText(f"✅ {file_name}")
            self.file_label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    background-color: #d5f5e3;
                    border-radius: 5px;
                    color: #27ae60;
                }
            """)

    def validate_and_accept(self):
        """Validace a potvrzení"""
        if not self.file_path:
            QMessageBox.warning(self, "Chyba", "Vyberte soubor k nahrání.")
            return

        if not Path(self.file_path).exists():
            QMessageBox.warning(self, "Chyba", "Vybraný soubor neexistuje.")
            return

        self.accept()

    def get_data(self):
        """Získání dat"""
        valid_until = None
        if self.valid_until_input.date() > self.valid_until_input.minimumDate():
            valid_until = self.valid_until_input.date().toString("yyyy-MM-dd")

        return {
            'document_type': self.type_combo.currentText(),
            'file_path': self.file_path,
            'valid_until': valid_until,
            'description': self.description_input.toPlainText().strip()
        }
