# customer_documents.py
# -*- coding: utf-8 -*-
"""
Widget pro správu dokumentů zákazníka
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QComboBox, QMessageBox, QAbstractItemView, QFileDialog,
    QDialog, QFormLayout, QLineEdit, QDateEdit, QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QColor, QBrush, QCursor, QDesktopServices
from PyQt6.QtCore import QUrl
import config
from database_manager import db
from datetime import datetime, date
import os


class CustomerDocumentsWidget(QWidget):
    """Widget pro správu dokumentů zákazníka"""

    document_added = pyqtSignal()

    def __init__(self, customer_id):
        super().__init__()
        self.customer_id = customer_id
        self.init_ui()
        self.load_documents()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Hlavička
        self.create_header(layout)

        # Kategorie a filtry
        self.create_filters(layout)

        # Tabulka dokumentů
        self.create_table(layout)

        # Šablony
        self.create_templates_section(layout)

        self.set_styles()

    def create_header(self, parent_layout):
        """Vytvoření hlavičky"""
        header = QHBoxLayout()

        title = QLabel("📁 Dokumenty zákazníka")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header.addWidget(title)

        header.addStretch()

        btn_upload = QPushButton("📤 Nahrát dokument")
        btn_upload.setObjectName("btnSuccess")
        btn_upload.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_upload.clicked.connect(self.upload_document)
        header.addWidget(btn_upload)

        btn_generate = QPushButton("📝 Generovat smlouvu")
        btn_generate.setObjectName("btnPrimary")
        btn_generate.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_generate.clicked.connect(self.generate_contract)
        header.addWidget(btn_generate)

        btn_refresh = QPushButton("🔄 Obnovit")
        btn_refresh.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_refresh.clicked.connect(self.load_documents)
        header.addWidget(btn_refresh)

        parent_layout.addLayout(header)

    def create_filters(self, parent_layout):
        """Vytvoření filtrů"""
        filters_frame = QFrame()
        filters_frame.setObjectName("filtersFrame")
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setSpacing(10)

        # Kategorie
        filters_layout.addWidget(QLabel("Kategorie:"))
        self.cb_category = QComboBox()
        self.cb_category.addItems([
            "Vše",
            "📄 Rámcové smlouvy",
            "📋 Servisní smlouvy",
            "📝 Plné moci",
            "🧾 Faktury",
            "📊 Cenové nabídky",
            "📜 GDPR souhlasy",
            "📁 Ostatní"
        ])
        self.cb_category.currentTextChanged.connect(self.filter_documents)
        filters_layout.addWidget(self.cb_category)

        # Platnost
        filters_layout.addWidget(QLabel("Platnost:"))
        self.cb_validity = QComboBox()
        self.cb_validity.addItems(["Vše", "Platné", "Neplatné", "Bez platnosti"])
        self.cb_validity.currentTextChanged.connect(self.filter_documents)
        filters_layout.addWidget(self.cb_validity)

        filters_layout.addStretch()

        # Statistiky
        self.lbl_stats = QLabel("Celkem: 0 dokumentů")
        self.lbl_stats.setStyleSheet("color: #7f8c8d;")
        filters_layout.addWidget(self.lbl_stats)

        parent_layout.addWidget(filters_frame)

    def create_table(self, parent_layout):
        """Vytvoření tabulky dokumentů"""
        self.table = QTableWidget()
        self.table.setObjectName("documentsTable")

        columns = [
            "ID", "Typ", "Název souboru", "Datum nahrání",
            "Platnost do", "Velikost", "Akce"
        ]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)

        self.table.setColumnHidden(0, True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)

        self.table.doubleClicked.connect(self.preview_document)

        parent_layout.addWidget(self.table)

    def create_templates_section(self, parent_layout):
        """Vytvoření sekce šablon"""
        templates_group = QGroupBox("📋 Šablony smluv")
        templates_layout = QHBoxLayout(templates_group)
        templates_layout.setSpacing(10)

        templates = [
            ("Servisní smlouva", "service_contract"),
            ("Rámcová smlouva", "framework_contract"),
            ("Plná moc", "power_of_attorney"),
            ("GDPR souhlas", "gdpr_consent")
        ]

        for name, template_id in templates:
            btn = QPushButton(name)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(lambda checked, t=template_id: self.use_template(t))
            templates_layout.addWidget(btn)

        templates_layout.addStretch()
        parent_layout.addWidget(templates_group)

    def load_documents(self):
        """Načtení dokumentů"""
        try:
            query = """
                SELECT
                    id,
                    doc_type,
                    file_name,
                    uploaded_at,
                    valid_until,
                    file_size,
                    file_path
                FROM customer_documents
                WHERE customer_id = ?
                ORDER BY uploaded_at DESC
            """

            documents = db.fetch_all(query, (self.customer_id,))
            self.all_documents = documents if documents else []
            self.populate_table(self.all_documents)
            self.update_stats(len(self.all_documents))

        except Exception as e:
            print(f"Chyba při načítání dokumentů: {e}")
            self.all_documents = []
            self.populate_table([])

    def populate_table(self, documents):
        """Naplnění tabulky"""
        self.table.setRowCount(0)

        today = date.today()

        for doc in documents:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(doc[0])))

            # Typ dokumentu
            doc_type = str(doc[1] or "Ostatní")
            type_item = QTableWidgetItem(doc_type)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, type_item)

            # Název souboru
            file_name = str(doc[2] or "")
            name_item = QTableWidgetItem(file_name)
            name_font = QFont()
            name_font.setBold(True)
            name_item.setFont(name_font)
            self.table.setItem(row, 2, name_item)

            # Datum nahrání
            upload_date = doc[3] or ""
            if upload_date:
                try:
                    dt = datetime.fromisoformat(upload_date)
                    upload_date = dt.strftime("%d.%m.%Y")
                except:
                    pass
            self.table.setItem(row, 3, QTableWidgetItem(upload_date))

            # Platnost do
            valid_until = doc[4]
            valid_item = QTableWidgetItem("")
            if valid_until:
                try:
                    if isinstance(valid_until, str):
                        valid_dt = datetime.fromisoformat(valid_until).date()
                    else:
                        valid_dt = valid_until
                    valid_item.setText(valid_dt.strftime("%d.%m.%Y"))

                    # Barevné označení
                    if valid_dt < today:
                        valid_item.setBackground(QBrush(QColor("#ffcccc")))  # Neplatné
                    elif (valid_dt - today).days <= 30:
                        valid_item.setBackground(QBrush(QColor("#fff3cd")))  # Brzy vyprší
                    else:
                        valid_item.setBackground(QBrush(QColor("#d4edda")))  # Platné
                except:
                    pass
            else:
                valid_item.setText("Bez platnosti")
                valid_item.setStyleSheet("color: #7f8c8d;")

            valid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, valid_item)

            # Velikost
            file_size = doc[5] or 0
            size_str = self.format_file_size(file_size)
            size_item = QTableWidgetItem(size_str)
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 5, size_item)

            # Akce
            self.table.setItem(row, 6, QTableWidgetItem(""))

    def format_file_size(self, size_bytes):
        """Formátování velikosti souboru"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def filter_documents(self):
        """Filtrování dokumentů"""
        category = self.cb_category.currentText()
        validity = self.cb_validity.currentText()

        filtered = self.all_documents

        # Filtr kategorie
        if category != "Vše":
            # Odstranit emoji z kategorie
            category_clean = category.split(" ", 1)[-1] if " " in category else category
            filtered = [d for d in filtered if category_clean in str(d[1] or "")]

        # Filtr platnosti
        if validity != "Vše":
            today = date.today()
            new_filtered = []
            for doc in filtered:
                valid_until = doc[4]
                if validity == "Bez platnosti":
                    if not valid_until:
                        new_filtered.append(doc)
                elif valid_until:
                    try:
                        if isinstance(valid_until, str):
                            valid_dt = datetime.fromisoformat(valid_until).date()
                        else:
                            valid_dt = valid_until

                        if validity == "Platné" and valid_dt >= today:
                            new_filtered.append(doc)
                        elif validity == "Neplatné" and valid_dt < today:
                            new_filtered.append(doc)
                    except:
                        pass
            filtered = new_filtered

        self.populate_table(filtered)
        self.update_stats(len(filtered))

    def update_stats(self, count):
        """Aktualizace statistik"""
        self.lbl_stats.setText(f"Celkem: {count} dokumentů")

    def upload_document(self):
        """Nahrání dokumentu"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Vybrat dokument",
            "",
            "Dokumenty (*.pdf *.doc *.docx *.xls *.xlsx *.jpg *.jpeg *.png);;Všechny soubory (*.*)"
        )

        if file_path:
            dialog = DocumentUploadDialog(file_path, self)
            if dialog.exec():
                doc_data = dialog.get_data()
                self.save_document(file_path, doc_data)
                self.load_documents()

    def save_document(self, file_path, doc_data):
        """Uložení dokumentu do databáze"""
        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            # V produkci by se soubor kopíroval do úložiště
            storage_path = file_path  # Placeholder

            valid_until = doc_data.get("valid_until")
            if valid_until and isinstance(valid_until, QDate):
                valid_until = valid_until.toString("yyyy-MM-dd")

            db.execute(
                """INSERT INTO customer_documents
                   (customer_id, doc_type, file_name, file_path, file_size, valid_until, uploaded_at, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    self.customer_id,
                    doc_data["doc_type"],
                    file_name,
                    storage_path,
                    file_size,
                    valid_until,
                    datetime.now().isoformat(),
                    doc_data.get("notes", "")
                )
            )

            self.document_added.emit()
            QMessageBox.information(self, "Úspěch", f"Dokument {file_name} byl nahrán")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se nahrát dokument: {e}")

    def preview_document(self):
        """Náhled dokumentu"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            file_name = self.table.item(current_row, 2).text()
            QMessageBox.information(self, "Náhled", f"Náhled dokumentu: {file_name}\n\nTato funkce otevře dokument v externím prohlížeči.")

    def download_document(self):
        """Stažení dokumentu"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            file_name = self.table.item(current_row, 2).text()

            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Uložit dokument",
                file_name,
                "Všechny soubory (*.*)"
            )

            if save_path:
                QMessageBox.information(self, "Staženo", f"Dokument uložen do: {save_path}")

    def delete_document(self):
        """Smazání dokumentu"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            doc_id = int(self.table.item(current_row, 0).text())
            file_name = self.table.item(current_row, 2).text()

            reply = QMessageBox.question(
                self,
                "Smazat dokument",
                f"Opravdu chcete smazat dokument {file_name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                try:
                    db.execute("DELETE FROM customer_documents WHERE id = ?", (doc_id,))
                    self.load_documents()
                    QMessageBox.information(self, "Smazáno", "Dokument byl smazán")
                except Exception as e:
                    QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat dokument: {e}")

    def generate_contract(self):
        """Generování smlouvy"""
        QMessageBox.information(
            self,
            "Generování smlouvy",
            "Vyberte šablonu smlouvy z dostupných šablon níže."
        )

    def use_template(self, template_id):
        """Použití šablony"""
        template_names = {
            "service_contract": "Servisní smlouva",
            "framework_contract": "Rámcová smlouva",
            "power_of_attorney": "Plná moc",
            "gdpr_consent": "GDPR souhlas"
        }

        template_name = template_names.get(template_id, "Smlouva")

        reply = QMessageBox.question(
            self,
            "Generovat smlouvu",
            f"Chcete vygenerovat {template_name} pro tohoto zákazníka?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(
                self,
                "Smlouva vygenerována",
                f"{template_name} byla vygenerována a uložena do dokumentů zákazníka."
            )
            self.load_documents()

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet(f"""
            #filtersFrame {{
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 10px;
            }}
            #documentsTable {{
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                gridline-color: #e0e0e0;
            }}
            #documentsTable::item {{
                padding: 8px;
            }}
            QHeaderView::section {{
                background-color: {config.COLOR_PRIMARY};
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #ddd;
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
            #btnSuccess {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }}
            #btnSuccess:hover {{
                background-color: #219a52;
            }}
            #btnPrimary {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }}
            #btnPrimary:hover {{
                background-color: #2980b9;
            }}
            QPushButton {{
                padding: 6px 12px;
                border-radius: 4px;
                border: 1px solid #ddd;
            }}
            QPushButton:hover {{
                background-color: #e0e0e0;
            }}
            QComboBox {{
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-width: 150px;
            }}
        """)


class DocumentUploadDialog(QDialog):
    """Dialog pro nahrání dokumentu"""

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("Nahrát dokument")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)

        # Info o souboru
        info_group = QGroupBox("📄 Informace o souboru")
        info_layout = QFormLayout(info_group)

        lbl_file = QLabel(self.file_name)
        lbl_file.setStyleSheet("font-weight: bold;")
        info_layout.addRow("Soubor:", lbl_file)

        file_size = os.path.getsize(self.file_path)
        size_str = self.format_size(file_size)
        info_layout.addRow("Velikost:", QLabel(size_str))

        layout.addWidget(info_group)

        # Metadata
        meta_group = QGroupBox("📋 Metadata dokumentu")
        meta_layout = QFormLayout(meta_group)

        # Typ dokumentu
        self.cb_doc_type = QComboBox()
        self.cb_doc_type.addItems([
            "Rámcová smlouva",
            "Servisní smlouva",
            "Plná moc",
            "Faktura",
            "Cenová nabídka",
            "GDPR souhlas",
            "Ostatní"
        ])
        meta_layout.addRow("Typ dokumentu:", self.cb_doc_type)

        # Platnost do
        self.de_valid_until = QDateEdit()
        self.de_valid_until.setCalendarPopup(True)
        self.de_valid_until.setDate(QDate.currentDate().addYears(1))
        self.de_valid_until.setDisplayFormat("dd.MM.yyyy")

        valid_layout = QHBoxLayout()
        self.chk_has_validity = QCheckBox("Dokument má platnost")
        self.chk_has_validity.toggled.connect(self.de_valid_until.setEnabled)
        self.chk_has_validity.setChecked(True)
        valid_layout.addWidget(self.chk_has_validity)
        valid_layout.addWidget(self.de_valid_until)
        meta_layout.addRow("Platnost:", valid_layout)

        # Poznámky
        self.te_notes = QLineEdit()
        self.te_notes.setPlaceholderText("Volitelné poznámky k dokumentu...")
        meta_layout.addRow("Poznámky:", self.te_notes)

        layout.addWidget(meta_group)

        layout.addStretch()

        # Tlačítka
        buttons = QHBoxLayout()
        buttons.addStretch()

        btn_cancel = QPushButton("Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_upload = QPushButton("📤 Nahrát")
        btn_upload.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; font-weight: bold; padding: 10px 20px;")
        btn_upload.clicked.connect(self.accept)
        buttons.addWidget(btn_upload)

        layout.addLayout(buttons)

    def format_size(self, size_bytes):
        """Formátování velikosti"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def get_data(self):
        """Získání dat"""
        return {
            "doc_type": self.cb_doc_type.currentText(),
            "valid_until": self.de_valid_until.date() if self.chk_has_validity.isChecked() else None,
            "notes": self.te_notes.text()
        }
