# -*- coding: utf-8 -*-
"""
Modul Administrativa - Správa dokumentů (PRODUKČNÍ VERZE)
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QFrame,
                             QComboBox, QLineEdit, QDateEdit, QHeaderView,
                             QMessageBox, QDialog, QFormLayout, QTextEdit,
                             QSpinBox, QDoubleSpinBox, QFileDialog, QCheckBox,
                             QGroupBox, QTabWidget, QScrollArea, QListWidget,
                             QListWidgetItem, QSplitter, QTreeWidget, QTreeWidgetItem)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QUrl, QSize
from PyQt6.QtGui import QFont, QColor, QIcon, QPixmap, QDesktopServices
from datetime import datetime, timedelta, date
from pathlib import Path
import shutil
import config
from database_manager import db


class DocumentsWidget(QWidget):
    """Widget pro správu dokumentů"""

    def __init__(self):
        super().__init__()
        self.current_document = None
        self.init_ui()
        self.load_documents()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Statistiky
        self.create_stats_panel(layout)

        # Hlavní splitter (levý panel + detail)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Levý panel
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # Pravý panel (detail dokumentu)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

    def create_stats_panel(self, parent_layout):
        """Panel se statistikami"""
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        stats_layout = QHBoxLayout(stats_frame)

        stats = [
            ("📄 Celkem dokumentů", "0", "total"),
            ("📂 Kategorie", "0", "categories"),
            ("💾 Celková velikost", "0 MB", "size"),
            ("📅 Tento měsíc", "0", "this_month"),
        ]

        self.stat_labels = {}

        for title, value, key in stats:
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(10, 5, 10, 5)

            title_label = QLabel(title)
            title_font = QFont()
            title_font.setPointSize(9)
            title_label.setFont(title_font)
            title_label.setStyleSheet("color: #7f8c8d;")

            value_label = QLabel(value)
            value_font = QFont()
            value_font.setPointSize(14)
            value_font.setBold(True)
            value_label.setFont(value_font)

            self.stat_labels[key] = value_label

            stat_layout.addWidget(title_label)
            stat_layout.addWidget(value_label)

            stats_layout.addWidget(stat_widget)

        stats_layout.addStretch()
        parent_layout.addWidget(stats_frame)

    def create_left_panel(self):
        """Vytvoření levého panelu s tabulkou dokumentů"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Filtry
        filters_frame = QFrame()
        filters_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        filters_layout = QVBoxLayout(filters_frame)

        # První řádek filtrů
        row1 = QHBoxLayout()

        # Typ dokumentu
        type_label = QLabel("Typ:")
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Všechny typy",
            "Smlouvy",
            "Protokoly",
            "Certifikáty",
            "Plné moci",
            "Objednávky",
            "Výkazy",
            "Ostatní"
        ])
        self.type_combo.currentTextChanged.connect(self.filter_documents)
        row1.addWidget(type_label)
        row1.addWidget(self.type_combo)

        # Kategorie
        category_label = QLabel("Kategorie:")
        self.category_combo = QComboBox()
        self.category_combo.addItem("Všechny kategorie")
        self.load_categories()
        self.category_combo.currentTextChanged.connect(self.filter_documents)
        row1.addWidget(category_label)
        row1.addWidget(self.category_combo)

        row1.addStretch()
        filters_layout.addLayout(row1)

        # Druhý řádek filtrů
        row2 = QHBoxLayout()

        # Propojení
        link_label = QLabel("Propojeno s:")
        self.link_combo = QComboBox()
        self.link_combo.addItems([
            "Všechny",
            "Zákazníky",
            "Vozidly",
            "Zakázkami",
            "Fakturami",
            "Nepropojené"
        ])
        self.link_combo.currentTextChanged.connect(self.filter_documents)
        row2.addWidget(link_label)
        row2.addWidget(self.link_combo)

        # Vyhledávání
        search_label = QLabel("Hledat:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Název, popis, štítky...")
        self.search_input.textChanged.connect(self.filter_documents)
        row2.addWidget(search_label)
        row2.addWidget(self.search_input)

        row2.addStretch()
        filters_layout.addLayout(row2)

        layout.addWidget(filters_frame)

        # Tlačítka akcí
        buttons_layout = QHBoxLayout()

        new_btn = QPushButton("➕ Nový dokument")
        new_btn.clicked.connect(self.new_document)
        new_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 15px;")
        buttons_layout.addWidget(new_btn)

        upload_btn = QPushButton("📤 Upload souboru")
        upload_btn.clicked.connect(self.upload_document)
        upload_btn.setStyleSheet(f"background-color: {config.COLOR_SECONDARY}; color: white; padding: 8px 15px;")
        buttons_layout.addWidget(upload_btn)

        template_btn = QPushButton("📝 Ze šablony")
        template_btn.clicked.connect(self.create_from_template)
        buttons_layout.addWidget(template_btn)

        delete_btn = QPushButton("🗑️ Smazat")
        delete_btn.clicked.connect(self.delete_document)
        delete_btn.setStyleSheet(f"background-color: {config.COLOR_DANGER}; color: white; padding: 8px 15px;")
        buttons_layout.addWidget(delete_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # Tabulka dokumentů
        self.documents_table = QTableWidget()
        self.documents_table.setColumnCount(7)
        self.documents_table.setHorizontalHeaderLabels([
            "Typ",
            "Název",
            "Kategorie",
            "Datum nahrání",
            "Propojeno s",
            "Velikost",
            "Štítky"
        ])
        self.documents_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.documents_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.documents_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.documents_table.setAlternatingRowColors(True)
        self.documents_table.currentItemChanged.connect(self.on_document_selected)
        self.documents_table.doubleClicked.connect(self.open_document)
        layout.addWidget(self.documents_table)

        return widget

    def create_right_panel(self):
        """Vytvoření pravého panelu s detailem dokumentu"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Hlavička
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        header_layout = QVBoxLayout(header_frame)

        self.detail_title = QLabel("Vyberte dokument")
        detail_font = QFont()
        detail_font.setPointSize(14)
        detail_font.setBold(True)
        self.detail_title.setFont(detail_font)
        header_layout.addWidget(self.detail_title)

        layout.addWidget(header_frame)

        # Náhled dokumentu
        preview_group = QGroupBox("Náhled")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_label = QLabel("Žádný dokument")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(300)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        preview_layout.addWidget(self.preview_label)

        layout.addWidget(preview_group)

        # Informace o dokumentu
        info_group = QGroupBox("Informace")
        info_layout = QFormLayout(info_group)

        self.detail_type = QLabel("-")
        info_layout.addRow("Typ:", self.detail_type)

        self.detail_category = QLabel("-")
        info_layout.addRow("Kategorie:", self.detail_category)

        self.detail_size = QLabel("-")
        info_layout.addRow("Velikost:", self.detail_size)

        self.detail_upload_date = QLabel("-")
        info_layout.addRow("Datum nahrání:", self.detail_upload_date)

        self.detail_uploaded_by = QLabel("-")
        info_layout.addRow("Nahrál:", self.detail_uploaded_by)

        self.detail_linked = QLabel("-")
        info_layout.addRow("Propojeno s:", self.detail_linked)

        self.detail_tags = QLabel("-")
        self.detail_tags.setWordWrap(True)
        info_layout.addRow("Štítky:", self.detail_tags)

        self.detail_note = QTextEdit()
        self.detail_note.setMaximumHeight(80)
        self.detail_note.setReadOnly(True)
        info_layout.addRow("Poznámka:", self.detail_note)

        layout.addWidget(info_group)

        # Tlačítka akcí
        actions_group = QGroupBox("Akce")
        actions_layout = QVBoxLayout(actions_group)

        open_btn = QPushButton("📂 Otevřít dokument")
        open_btn.clicked.connect(self.open_document)
        actions_layout.addWidget(open_btn)

        download_btn = QPushButton("⬇️ Stáhnout")
        download_btn.clicked.connect(self.download_document)
        actions_layout.addWidget(download_btn)

        print_btn = QPushButton("🖨️ Tisk")
        print_btn.clicked.connect(self.print_document)
        actions_layout.addWidget(print_btn)

        email_btn = QPushButton("📧 Odeslat emailem")
        email_btn.clicked.connect(self.send_document_email)
        actions_layout.addWidget(email_btn)

        edit_btn = QPushButton("✏️ Upravit údaje")
        edit_btn.clicked.connect(self.edit_document)
        actions_layout.addWidget(edit_btn)

        layout.addWidget(actions_group)

        layout.addStretch()

        return widget

    # =====================================================
    # NAČÍTÁNÍ DAT
    # =====================================================

    def load_documents(self):
        """Načtení dokumentů z databáze"""
        try:
            query = """
                SELECT
                    d.*,
                    u.full_name as uploaded_by_name,
                    CASE d.linked_entity_type
                        WHEN 'customer' THEN (SELECT first_name || ' ' || last_name FROM customers WHERE id = d.linked_entity_id)
                        WHEN 'vehicle' THEN (SELECT license_plate FROM vehicles WHERE id = d.linked_entity_id)
                        WHEN 'order' THEN (SELECT order_number FROM orders WHERE id = d.linked_entity_id)
                        WHEN 'invoice' THEN (SELECT invoice_number FROM invoices WHERE id = d.linked_entity_id)
                        ELSE NULL
                    END as linked_name
                FROM documents d
                LEFT JOIN users u ON d.uploaded_by = u.id
                ORDER BY d.upload_date DESC
            """
            documents = db.fetch_all(query)

            self.documents_table.setRowCount(len(documents))

            for row, doc in enumerate(documents):
                # Ikona typu
                type_icon = self.get_type_icon(doc["document_type"])
                type_item = QTableWidgetItem(f"{type_icon} {self.get_type_label(doc['document_type'])}")
                self.documents_table.setItem(row, 0, type_item)

                # Název
                name_item = QTableWidgetItem(doc["document_name"])
                name_item.setData(Qt.ItemDataRole.UserRole, doc["id"])  # Uložit ID
                self.documents_table.setItem(row, 1, name_item)

                # Kategorie
                self.documents_table.setItem(row, 2, QTableWidgetItem(doc["category"] or "-"))

                # Datum
                upload_date = datetime.fromisoformat(doc["upload_date"]).strftime("%d.%m.%Y %H:%M")
                self.documents_table.setItem(row, 3, QTableWidgetItem(upload_date))

                # Propojení
                if doc["linked_entity_type"] and doc["linked_name"]:
                    link_text = f"{self.get_entity_label(doc['linked_entity_type'])}: {doc['linked_name']}"
                else:
                    link_text = "-"
                self.documents_table.setItem(row, 4, QTableWidgetItem(link_text))

                # Velikost
                size_kb = doc["file_size"] / 1024 if doc["file_size"] else 0
                if size_kb > 1024:
                    size_text = f"{size_kb/1024:.1f} MB"
                else:
                    size_text = f"{size_kb:.0f} KB"
                self.documents_table.setItem(row, 5, QTableWidgetItem(size_text))

                # Štítky
                self.documents_table.setItem(row, 6, QTableWidgetItem(doc["tags"] or "-"))

            # Aktualizace statistik
            self.update_statistics()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst dokumenty:\n{e}")

    def load_categories(self):
        """Načtení kategorií"""
        try:
            query = """
                SELECT DISTINCT category FROM documents
                WHERE category IS NOT NULL
                ORDER BY category
            """
            categories = db.fetch_all(query)

            for cat in categories:
                self.category_combo.addItem(cat["category"])

        except Exception as e:
            print(f"Chyba při načítání kategorií: {e}")

    def update_statistics(self):
        """Aktualizace statistik"""
        try:
            # Celkem dokumentů
            query_total = "SELECT COUNT(*) as count FROM documents"
            result = db.fetch_one(query_total)
            total = result["count"] if result else 0

            # Počet kategorií
            query_cats = "SELECT COUNT(DISTINCT category) as count FROM documents WHERE category IS NOT NULL"
            result = db.fetch_one(query_cats)
            categories = result["count"] if result else 0

            # Celková velikost
            query_size = "SELECT COALESCE(SUM(file_size), 0) as total FROM documents"
            result = db.fetch_one(query_size)
            size_bytes = result["total"] if result else 0
            size_mb = size_bytes / (1024 * 1024)

            # Tento měsíc
            query_month = """
                SELECT COUNT(*) as count FROM documents
                WHERE upload_date >= DATE('now', 'start of month')
            """
            result = db.fetch_one(query_month)
            this_month = result["count"] if result else 0

            # Aktualizace labelů
            self.stat_labels["total"].setText(str(total))
            self.stat_labels["categories"].setText(str(categories))
            self.stat_labels["size"].setText(f"{size_mb:.1f} MB")
            self.stat_labels["this_month"].setText(str(this_month))

        except Exception as e:
            print(f"Chyba při aktualizaci statistik: {e}")

    # =====================================================
    # FILTRY
    # =====================================================

    def filter_documents(self):
        """Filtrování dokumentů"""
        search_text = self.search_input.text().lower()
        type_filter = self.type_combo.currentText()
        category_filter = self.category_combo.currentText()
        link_filter = self.link_combo.currentText()

        for row in range(self.documents_table.rowCount()):
            show = True

            # Filtr vyhledávání
            if search_text:
                name = self.documents_table.item(row, 1).text().lower()
                tags = self.documents_table.item(row, 6).text().lower()
                if search_text not in name and search_text not in tags:
                    show = False

            # Filtr typu
            if type_filter != "Všechny typy":
                type_text = self.documents_table.item(row, 0).text()
                if type_filter not in type_text:
                    show = False

            # Filtr kategorie
            if category_filter != "Všechny kategorie":
                category_text = self.documents_table.item(row, 2).text()
                if category_filter != category_text:
                    show = False

            # Filtr propojení
            if link_filter != "Všechny":
                link_text = self.documents_table.item(row, 4).text()
                if link_filter == "Nepropojené":
                    if link_text != "-":
                        show = False
                else:
                    entity_label = link_filter.rstrip('y')  # Zákazníky -> Zákazník
                    if not link_text.startswith(entity_label):
                        show = False

            self.documents_table.setRowHidden(row, not show)

    # =====================================================
    # UDÁLOSTI
    # =====================================================

    def on_document_selected(self):
        """Vybraný dokument v tabulce"""
        current_row = self.documents_table.currentRow()
        if current_row < 0:
            return

        try:
            doc_id = self.documents_table.item(current_row, 1).data(Qt.ItemDataRole.UserRole)

            query = """
                SELECT
                    d.*,
                    u.full_name as uploaded_by_name,
                    CASE d.linked_entity_type
                        WHEN 'customer' THEN (SELECT first_name || ' ' || last_name FROM customers WHERE id = d.linked_entity_id)
                        WHEN 'vehicle' THEN (SELECT license_plate FROM vehicles WHERE id = d.linked_entity_id)
                        WHEN 'order' THEN (SELECT order_number FROM orders WHERE id = d.linked_entity_id)
                        WHEN 'invoice' THEN (SELECT invoice_number FROM invoices WHERE id = d.linked_entity_id)
                        ELSE NULL
                    END as linked_name
                FROM documents d
                LEFT JOIN users u ON d.uploaded_by = u.id
                WHERE d.id = ?
            """
            doc = db.fetch_one(query, (doc_id,))

            if not doc:
                return

            self.current_document = doc

            # Aktualizace detailu
            self.detail_title.setText(doc["document_name"])
            self.detail_type.setText(self.get_type_label(doc["document_type"]))
            self.detail_category.setText(doc["category"] or "-")

            size_kb = doc["file_size"] / 1024 if doc["file_size"] else 0
            if size_kb > 1024:
                size_text = f"{size_kb/1024:.1f} MB"
            else:
                size_text = f"{size_kb:.0f} KB"
            self.detail_size.setText(size_text)

            upload_date = datetime.fromisoformat(doc["upload_date"]).strftime("%d.%m.%Y %H:%M")
            self.detail_upload_date.setText(upload_date)

            self.detail_uploaded_by.setText(doc["uploaded_by_name"] or "-")

            if doc["linked_entity_type"] and doc["linked_name"]:
                link_text = f"{self.get_entity_label(doc['linked_entity_type'])}: {doc['linked_name']}"
            else:
                link_text = "-"
            self.detail_linked.setText(link_text)

            self.detail_tags.setText(doc["tags"] or "-")
            self.detail_note.setPlainText(doc["note"] or "")

            # Náhled
            self.load_preview(doc)

        except Exception as e:
            print(f"Chyba při načítání detailu dokumentu: {e}")

    def load_preview(self, doc):
        """Načtení náhledu dokumentu"""
        file_path = Path(doc["file_path"])

        if not file_path.exists():
            self.preview_label.setText("⚠️ Soubor nenalezen")
            return

        # Pokud je to obrázek, zobrazit náhled
        if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            pixmap = QPixmap(str(file_path))
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    400, 400,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
            else:
                self.preview_label.setText("❌ Nelze načíst náhled")
        else:
            # Pro ostatní soubory zobrazit ikonu podle typu
            icon = self.get_file_icon(file_path.suffix)
            self.preview_label.setText(f"{icon}\n\n{file_path.suffix.upper()[1:]}")

    # =====================================================
    # AKCE
    # =====================================================

    def new_document(self):
        """Vytvoření nového dokumentu"""
        dialog = DocumentDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_documents()

    def upload_document(self):
        """Upload existującího souboru"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Vyberte soubory k nahrání",
            "",
            "Všechny soubory (*.*)"
        )

        if not file_paths:
            return

        for file_path in file_paths:
            dialog = DocumentDialog(self, file_path=file_path)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                pass  # Dialog sám uloží

        self.load_documents()

    def create_from_template(self):
        """Vytvoření dokumentu ze šablony"""
        # Dialog pro výběr šablony
        dialog = TemplateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            template = dialog.get_selected_template()
            if template:
                # TODO: Zpracovat šablonu a vytvořit dokument
                QMessageBox.information(
                    self,
                    "Šablona",
                    f"Vytvoření dokumentu ze šablony '{template}' bude implementováno.\n\n"
                    "Bude zahrnovat:\n"
                    "- Automatické vyplnění údajů\n"
                    "- Generování PDF\n"
                    "- Možnost elektronického podpisu"
                )

    def delete_document(self):
        """Smazání dokumentu"""
        current_row = self.documents_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Upozornění", "Vyberte dokument ke smazání.")
            return

        doc_id = self.documents_table.item(current_row, 1).data(Qt.ItemDataRole.UserRole)
        doc_name = self.documents_table.item(current_row, 1).text()

        reply = QMessageBox.question(
            self,
            "Smazat dokument",
            f"Opravdu chcete smazat dokument '{doc_name}'?\n\n"
            "Tato akce je nevratná!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Získat cestu k souboru
                query = "SELECT file_path FROM documents WHERE id = ?"
                result = db.fetch_one(query, (doc_id,))

                if result:
                    file_path = Path(result["file_path"])
                    if file_path.exists():
                        file_path.unlink()

                # Smazat z databáze
                delete_query = "DELETE FROM documents WHERE id = ?"
                db.execute_query(delete_query, (doc_id,))

                QMessageBox.information(self, "Úspěch", "Dokument byl smazán.")
                self.load_documents()

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat dokument:\n{e}")

    def open_document(self):
        """Otevření dokumentu"""
        if not self.current_document:
            return

        file_path = Path(self.current_document["file_path"])
        if file_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path)))
        else:
            QMessageBox.warning(self, "Chyba", "Soubor nebyl nalezen.")

    def download_document(self):
        """Stažení dokumentu"""
        if not self.current_document:
            return

        source_path = Path(self.current_document["file_path"])
        if not source_path.exists():
            QMessageBox.critical(self, "Chyba", "Soubor nebyl nalezen.")
            return

        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit jako",
            self.current_document["document_name"]
        )

        if dest_path:
            try:
                shutil.copy2(source_path, dest_path)
                QMessageBox.information(self, "Úspěch", "Dokument byl stažen.")
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se stáhnout dokument:\n{e}")

    def print_document(self):
        """Tisk dokumentu"""
        if not self.current_document:
            return

        # TODO: Implementovat tisk
        QMessageBox.information(
            self,
            "Tisk",
            f"Tisk dokumentu '{self.current_document['document_name']}' bude implementován.\n\n"
            "Funkce odešle dokument na výchozí tiskárnu."
        )

    def send_document_email(self):
        """Odeslání dokumentu emailem"""
        if not self.current_document:
            return

        # Dialog pro email
        dialog = EmailDocumentDialog(self, self.current_document)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Email", "Dokument by byl odeslán emailem.")

    def edit_document(self):
        """Úprava údajů dokumentu"""
        if not self.current_document:
            return

        dialog = DocumentDialog(self, document_id=self.current_document["id"])
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_documents()
            self.on_document_selected()

    # =====================================================
    # POMOCNÉ METODY
    # =====================================================

    def get_type_icon(self, doc_type):
        """Vrátí ikonu pro typ dokumentu"""
        icons = {
            "contract": "📄",
            "protocol": "📋",
            "certificate": "📜",
            "power_of_attorney": "📝",
            "order": "📑",
            "report": "📊",
            "invoice_attachment": "💰",
            "other": "📎"
        }
        return icons.get(doc_type, "📎")

    def get_type_label(self, doc_type):
        """Vrátí popisek pro typ dokumentu"""
        labels = {
            "contract": "Smlouva",
            "protocol": "Protokol",
            "certificate": "Certifikát",
            "power_of_attorney": "Plná moc",
            "order": "Objednávka",
            "report": "Výkaz",
            "invoice_attachment": "Příloha faktury",
            "other": "Ostatní"
        }
        return labels.get(doc_type, "Ostatní")

    def get_entity_label(self, entity_type):
        """Vrátí popisek pro typ entity"""
        labels = {
            "customer": "Zákazník",
            "vehicle": "Vozidlo",
            "order": "Zakázka",
            "invoice": "Faktura"
        }
        return labels.get(entity_type, "")

    def get_file_icon(self, extension):
        """Vrátí ikonu podle přípony souboru"""
        icons = {
            ".pdf": "📕",
            ".doc": "📘",
            ".docx": "📘",
            ".xls": "📗",
            ".xlsx": "📗",
            ".txt": "📄",
            ".jpg": "🖼️",
            ".jpeg": "🖼️",
            ".png": "🖼️",
            ".gif": "🖼️",
        }
        return icons.get(extension.lower(), "📎")

    def refresh(self):
        """Obnovení dat"""
        self.load_documents()


# =====================================================
# DIALOGY
# =====================================================

class DocumentDialog(QDialog):
    """Dialog pro vytvoření/úpravu dokumentu"""

    def __init__(self, parent, document_id=None, file_path=None):
        super().__init__(parent)
        self.document_id = document_id
        self.file_path = file_path
        self.is_edit = document_id is not None

        self.setWindowTitle("Upravit dokument" if self.is_edit else "Nový dokument")
        self.setMinimumWidth(600)

        self.init_ui()

        if self.is_edit:
            self.load_document()
        elif file_path:
            self.file_path_input.setText(file_path)
            # Automaticky vyplnit název z názvu souboru
            self.name_input.setText(Path(file_path).name)

    def init_ui(self):
        """Inicializace UI"""
        layout = QFormLayout(self)

        # Název dokumentu
        self.name_input = QLineEdit()
        layout.addRow("Název dokumentu:", self.name_input)

        # Typ dokumentu
        self.type_combo = QComboBox()
        self.type_combo.addItem("Smlouva", "contract")
        self.type_combo.addItem("Protokol", "protocol")
        self.type_combo.addItem("Certifikát", "certificate")
        self.type_combo.addItem("Plná moc", "power_of_attorney")
        self.type_combo.addItem("Objednávka", "order")
        self.type_combo.addItem("Výkaz", "report")
        self.type_combo.addItem("Ostatní", "other")
        layout.addRow("Typ dokumentu:", self.type_combo)

        # Kategorie
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.load_categories()
        layout.addRow("Kategorie:", self.category_input)

        # Soubor
        file_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setReadOnly(True)
        file_layout.addWidget(self.file_path_input)

        browse_btn = QPushButton("📁 Procházet")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)

        layout.addRow("Soubor:", file_layout)

        # Propojení s entitou
        link_group = QGroupBox("Propojení")
        link_layout = QFormLayout(link_group)

        self.link_type_combo = QComboBox()
        self.link_type_combo.addItem("-- Nepropojeno --", None)
        self.link_type_combo.addItem("Zákazník", "customer")
        self.link_type_combo.addItem("Vozidlo", "vehicle")
        self.link_type_combo.addItem("Zakázka", "order")
        self.link_type_combo.addItem("Faktura", "invoice")
        self.link_type_combo.currentIndexChanged.connect(self.on_link_type_changed)
        link_layout.addRow("Propojit s:", self.link_type_combo)

        self.link_entity_combo = QComboBox()
        self.link_entity_combo.setEnabled(False)
        link_layout.addRow("Vybrat:", self.link_entity_combo)

        layout.addRow(link_group)

        # Štítky
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Štítky oddělené čárkou (např: důležité, smlouva, 2025)")
        layout.addRow("Štítky:", self.tags_input)

        # Poznámka
        self.note_input = QTextEdit()
        self.note_input.setMaximumHeight(80)
        layout.addRow("Poznámka:", self.note_input)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Uložit")
        save_btn.clicked.connect(self.save_document)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 8px 20px;
            }}
        """)
        buttons_layout.addWidget(save_btn)

        layout.addRow(buttons_layout)

    def load_categories(self):
        """Načtení kategorií"""
        try:
            query = """
                SELECT DISTINCT category FROM documents
                WHERE category IS NOT NULL
                ORDER BY category
            """
            categories = db.fetch_all(query)

            for cat in categories:
                self.category_input.addItem(cat["category"])

        except Exception as e:
            print(f"Chyba při načítání kategorií: {e}")

    def load_document(self):
        """Načtení dokumentu pro úpravu"""
        try:
            query = "SELECT * FROM documents WHERE id = ?"
            doc = db.fetch_one(query, (self.document_id,))

            if not doc:
                return

            self.name_input.setText(doc["document_name"])

            # Typ
            index = self.type_combo.findData(doc["document_type"])
            if index >= 0:
                self.type_combo.setCurrentIndex(index)

            # Kategorie
            if doc["category"]:
                self.category_input.setCurrentText(doc["category"])

            # Soubor
            self.file_path_input.setText(doc["file_path"])

            # Propojení
            if doc["linked_entity_type"]:
                index = self.link_type_combo.findData(doc["linked_entity_type"])
                if index >= 0:
                    self.link_type_combo.setCurrentIndex(index)
                    self.load_link_entities(doc["linked_entity_type"])

                    # Vybrat správnou entitu
                    entity_index = self.link_entity_combo.findData(doc["linked_entity_id"])
                    if entity_index >= 0:
                        self.link_entity_combo.setCurrentIndex(entity_index)

            # Štítky
            if doc["tags"]:
                self.tags_input.setText(doc["tags"])

            # Poznámka
            if doc["note"]:
                self.note_input.setPlainText(doc["note"])

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst dokument:\n{e}")

    def on_link_type_changed(self):
        """Změna typu propojení"""
        link_type = self.link_type_combo.currentData()

        if link_type:
            self.link_entity_combo.setEnabled(True)
            self.load_link_entities(link_type)
        else:
            self.link_entity_combo.setEnabled(False)
            self.link_entity_combo.clear()

    def load_link_entities(self, entity_type):
        """Načtení entit pro propojení"""
        self.link_entity_combo.clear()
        self.link_entity_combo.addItem("-- Vyberte --", None)

        try:
            if entity_type == "customer":
                query = """
                    SELECT id, first_name, last_name, company
                    FROM customers
                    ORDER BY last_name, first_name
                """
                entities = db.fetch_all(query)
                for e in entities:
                    text = f"{e['first_name']} {e['last_name']}"
                    if e['company']:
                        text += f" ({e['company']})"
                    self.link_entity_combo.addItem(text, e["id"])

            elif entity_type == "vehicle":
                query = """
                    SELECT v.id, v.license_plate, v.brand, v.model,
                           c.first_name, c.last_name
                    FROM vehicles v
                    LEFT JOIN customers c ON v.customer_id = c.id
                    ORDER BY v.license_plate
                """
                entities = db.fetch_all(query)
                for e in entities:
                    text = f"{e['license_plate']} - {e['brand']} {e['model']}"
                    if e['first_name']:
                        text += f" ({e['first_name']} {e['last_name']})"
                    self.link_entity_combo.addItem(text, e["id"])

            elif entity_type == "order":
                query = """
                    SELECT o.id, o.order_number, c.first_name, c.last_name
                    FROM orders o
                    LEFT JOIN customers c ON o.customer_id = c.id
                    ORDER BY o.created_date DESC
                    LIMIT 100
                """
                entities = db.fetch_all(query)
                for e in entities:
                    text = f"{e['order_number']}"
                    if e['first_name']:
                        text += f" - {e['first_name']} {e['last_name']}"
                    self.link_entity_combo.addItem(text, e["id"])

            elif entity_type == "invoice":
                query = """
                    SELECT i.id, i.invoice_number, c.first_name, c.last_name
                    FROM invoices i
                    LEFT JOIN customers c ON i.customer_id = c.id
                    ORDER BY i.issue_date DESC
                    LIMIT 100
                """
                entities = db.fetch_all(query)
                for e in entities:
                    text = f"{e['invoice_number']}"
                    if e['first_name']:
                        text += f" - {e['first_name']} {e['last_name']}"
                    self.link_entity_combo.addItem(text, e["id"])

        except Exception as e:
            print(f"Chyba při načítání entit: {e}")

    def browse_file(self):
        """Procházet soubory"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Vyberte soubor",
            "",
            "Všechny soubory (*.*)"
        )

        if file_path:
            self.file_path_input.setText(file_path)
            self.file_path = file_path

            # Pokud není vyplněný název, použít název souboru
            if not self.name_input.text():
                self.name_input.setText(Path(file_path).name)

    def save_document(self):
        """Uložení dokumentu"""
        try:
            # Validace
            if not self.name_input.text().strip():
                QMessageBox.warning(self, "Chyba", "Vyplňte název dokumentu.")
                return

            if not self.file_path_input.text() and not self.is_edit:
                QMessageBox.warning(self, "Chyba", "Vyberte soubor.")
                return

            # Zkopírovat soubor do data/documents
            if self.file_path and not self.is_edit:
                documents_dir = Path(config.DATA_DIR) / "documents" / "general"
                documents_dir.mkdir(parents=True, exist_ok=True)

                source_path = Path(self.file_path)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest_filename = f"{timestamp}_{source_path.name}"
                dest_path = documents_dir / dest_filename

                shutil.copy2(source_path, dest_path)
                file_path = str(dest_path)
                file_size = dest_path.stat().st_size
            elif self.is_edit:
                # Při úpravě ponechat původní soubor
                query = "SELECT file_path, file_size FROM documents WHERE id = ?"
                result = db.fetch_one(query, (self.document_id,))
                file_path = result["file_path"]
                file_size = result["file_size"]
            else:
                file_path = None
                file_size = 0

            # Data dokumentu
            doc_data = {
                "document_type": self.type_combo.currentData(),
                "document_name": self.name_input.text().strip(),
                "category": self.category_input.currentText().strip() or None,
                "tags": self.tags_input.text().strip() or None,
                "linked_entity_type": self.link_type_combo.currentData(),
                "linked_entity_id": self.link_entity_combo.currentData(),
                "note": self.note_input.toPlainText().strip() or None,
                "file_path": file_path,
                "file_size": file_size,
                "uploaded_by": 1  # TODO: Skutečné ID uživatele
            }

            if self.is_edit:
                # Aktualizace
                query = """
                    UPDATE documents SET
                        document_type = ?,
                        document_name = ?,
                        category = ?,
                        tags = ?,
                        linked_entity_type = ?,
                        linked_entity_id = ?,
                        note = ?
                    WHERE id = ?
                """
                db.execute_query(query, (
                    doc_data["document_type"],
                    doc_data["document_name"],
                    doc_data["category"],
                    doc_data["tags"],
                    doc_data["linked_entity_type"],
                    doc_data["linked_entity_id"],
                    doc_data["note"],
                    self.document_id
                ))
            else:
                # Vložení
                query = """
                    INSERT INTO documents (
                        document_type, document_name, file_path, category, tags,
                        linked_entity_type, linked_entity_id, file_size,
                        uploaded_by, note
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                db.execute_query(query, (
                    doc_data["document_type"],
                    doc_data["document_name"],
                    doc_data["file_path"],
                    doc_data["category"],
                    doc_data["tags"],
                    doc_data["linked_entity_type"],
                    doc_data["linked_entity_id"],
                    doc_data["file_size"],
                    doc_data["uploaded_by"],
                    doc_data["note"]
                ))

            QMessageBox.information(
                self,
                "Úspěch",
                f"Dokument '{doc_data['document_name']}' byl {'aktualizován' if self.is_edit else 'vytvořen'}."
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit dokument:\n{e}")


class TemplateDialog(QDialog):
    """Dialog pro výběr šablony"""

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Vybrat šablonu")
        self.setMinimumSize(500, 400)

        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QVBoxLayout(self)

        info_label = QLabel("Vyberte šablonu dokumentu:")
        layout.addWidget(info_label)

        # Seznam šablon
        self.templates_list = QListWidget()
        templates = [
            "Servisní smlouva",
            "Rámcová smlouva na údržbu",
            "Protokol o převzetí vozidla",
            "Protokol o předání vozidla",
            "Certifikát o provedené kontrole",
            "Plná moc k převzetí vozidla",
            "Objednávka dílů",
        ]
        for template in templates:
            self.templates_list.addItem(template)
        layout.addWidget(self.templates_list)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("Vybrat")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 20px;")
        buttons_layout.addWidget(ok_btn)

        layout.addLayout(buttons_layout)

    def get_selected_template(self):
        """Vrátí vybranou šablonu"""
        current_item = self.templates_list.currentItem()
        return current_item.text() if current_item else None


class EmailDocumentDialog(QDialog):
    """Dialog pro odeslání dokumentu emailem"""

    def __init__(self, parent, document):
        super().__init__(parent)
        self.document = document

        self.setWindowTitle("Odeslat dokument emailem")
        self.setMinimumWidth(500)

        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        layout = QFormLayout(self)

        # Dokument
        doc_label = QLabel(f"<b>{self.document['document_name']}</b>")
        layout.addRow("Dokument:", doc_label)

        # Email příjemce
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("prijemce@email.cz")
        layout.addRow("Email příjemce:", self.email_input)

        # Předmět
        self.subject_input = QLineEdit()
        self.subject_input.setText(f"Dokument: {self.document['document_name']}")
        layout.addRow("Předmět:", self.subject_input)

        # Zpráva
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(150)
        self.message_input.setPlainText(
            f"Dobrý den,\n\n"
            f"v příloze zasíláme dokument: {self.document['document_name']}\n\n"
            f"S pozdravem"
        )
        layout.addRow("Zpráva:", self.message_input)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Zrušit")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        send_btn = QPushButton("📧 Odeslat")
        send_btn.clicked.connect(self.accept)
        send_btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS}; color: white; padding: 8px 20px;")
        buttons_layout.addWidget(send_btn)

        layout.addRow(buttons_layout)
