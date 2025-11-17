# -*- coding: utf-8 -*-
"""
Fotogalerie vozidla - správa fotek s kategoriemi, lightboxem a exportem
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QPushButton, QLabel, QComboBox, QFrame, QMessageBox, QDialog,
    QFormLayout, QLineEdit, QTextEdit, QFileDialog, QMenu, QApplication
)
from PyQt6.QtCore import Qt, QSize, QMimeData, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon, QDrag, QPainter, QColor, QCursor
from datetime import datetime
from pathlib import Path
import shutil
import config
from database_manager import db


class VehiclePhotosWidget(QWidget):
    """Widget pro správu fotek vozidla"""

    photo_selected = pyqtSignal(int)  # Signal při výběru fotky

    def __init__(self, vehicle_id, parent=None):
        super().__init__(parent)
        self.vehicle_id = vehicle_id
        self.photos_dir = self.ensure_photos_directory()
        self.photos = []
        self.selected_photo_id = None
        self.init_ui()
        self.ensure_photos_table()
        self.load_photos()

    def ensure_photos_directory(self):
        """Zajištění existence adresáře pro fotky"""
        photos_dir = Path(config.DATA_DIR) / "vehicle_photos" / str(self.vehicle_id)
        photos_dir.mkdir(parents=True, exist_ok=True)

        # Vytvoření podsložek pro thumbnails
        thumbs_dir = photos_dir / "thumbnails"
        thumbs_dir.mkdir(exist_ok=True)

        return photos_dir

    def ensure_photos_table(self):
        """Zajištění existence tabulky pro fotky v DB"""
        try:
            db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicle_photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    thumbnail_path TEXT,
                    category TEXT DEFAULT 'Ostatní',
                    description TEXT,
                    is_main INTEGER DEFAULT 0,
                    sort_order INTEGER DEFAULT 0,
                    taken_at DATE,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (vehicle_id) REFERENCES vehicles (id)
                )
            """)
            db.connection.commit()
        except Exception as e:
            print(f"Chyba při vytváření tabulky fotek: {e}")

    def init_ui(self):
        """Inicializace uživatelského rozhraní"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        # Hlavička
        header_panel = self.create_header_panel()
        layout.addWidget(header_panel)

        # Info o hlavní fotce
        self.main_photo_info = QLabel("")
        self.main_photo_info.setStyleSheet("""
            QLabel {
                color: #27ae60;
                font-size: 12px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.main_photo_info)

        # Scrollovací oblast pro fotky
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
        """)

        self.photos_container = QWidget()
        self.photos_layout = QGridLayout(self.photos_container)
        self.photos_layout.setSpacing(15)
        self.photos_layout.setContentsMargins(10, 10, 10, 10)

        scroll_area.setWidget(self.photos_container)
        layout.addWidget(scroll_area)

        # Drop area info
        self.drop_info = QLabel("📷 Přetáhněte sem fotky pro nahrání")
        self.drop_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_info.setStyleSheet("""
            QLabel {
                color: #95a5a6;
                font-size: 14px;
                padding: 30px;
                border: 2px dashed #bdc3c7;
                border-radius: 10px;
                background-color: #fafafa;
            }
        """)
        self.drop_info.hide()
        layout.addWidget(self.drop_info)

        # Povolení drag & drop
        self.setAcceptDrops(True)

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
        title = QLabel("📷 Fotogalerie")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        layout.addStretch()

        # Filtr kategorie
        category_label = QLabel("Kategorie:")
        self.category_filter = QComboBox()
        self.category_filter.addItems([
            "Vše",
            "Celkové pohledy",
            "Detaily poškození",
            "Servisní fotky",
            "Dokumentace stavu",
            "Před/Po servisu",
            "Ostatní"
        ])
        self.category_filter.setMinimumWidth(150)
        self.category_filter.currentTextChanged.connect(self.filter_photos)

        layout.addWidget(category_label)
        layout.addWidget(self.category_filter)

        # Počet fotek
        self.photos_count_label = QLabel("0 fotek")
        self.photos_count_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.photos_count_label)

        # Tlačítko přidat
        btn_add = QPushButton("📷 Přidat fotku")
        btn_add.setStyleSheet(f"""
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
        btn_add.clicked.connect(self.add_photo)
        layout.addWidget(btn_add)

        # Tlačítko export
        btn_export = QPushButton("📤 Export galerie")
        btn_export.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_export.clicked.connect(self.export_gallery)
        layout.addWidget(btn_export)

        return panel

    def load_photos(self):
        """Načtení fotek z databáze"""
        try:
            self.photos = db.fetch_all("""
                SELECT * FROM vehicle_photos
                WHERE vehicle_id = ?
                ORDER BY is_main DESC, sort_order ASC, uploaded_at DESC
            """, (self.vehicle_id,))

            self.display_photos(self.photos)
            self.update_main_photo_info()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst fotky:\n{e}")

    def display_photos(self, photos):
        """Zobrazení fotek v mřížce"""
        # Vyčištění layoutu
        while self.photos_layout.count():
            item = self.photos_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not photos:
            self.drop_info.show()
            self.photos_count_label.setText("0 fotek")
            return

        self.drop_info.hide()
        self.photos_count_label.setText(f"{len(photos)} fotek")

        # Zobrazení fotek v mřížce (4 sloupce)
        columns = 4
        for idx, photo in enumerate(photos):
            row = idx // columns
            col = idx % columns

            photo_widget = self.create_photo_thumbnail(photo)
            self.photos_layout.addWidget(photo_widget, row, col)

        # Přidání prázdných widgetů pro vyrovnání
        remaining = columns - (len(photos) % columns)
        if remaining < columns:
            last_row = len(photos) // columns
            for i in range(remaining):
                spacer = QWidget()
                self.photos_layout.addWidget(spacer, last_row, (len(photos) % columns) + i)

    def create_photo_thumbnail(self, photo):
        """Vytvoření thumbnail widgetu pro fotku"""
        frame = QFrame()
        frame.setFixedSize(180, 220)
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 8px;
            }
            QFrame:hover {
                border-color: #3498db;
                background-color: #ecf0f1;
            }
        """)
        frame.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Náhled fotky
        photo_label = QLabel()
        photo_label.setFixedSize(160, 120)
        photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo_label.setStyleSheet("""
            QLabel {
                background-color: #ecf0f1;
                border-radius: 5px;
            }
        """)

        # Načtení thumbnail nebo vytvoření z originálu
        pixmap = None
        if photo['thumbnail_path'] and Path(photo['thumbnail_path']).exists():
            pixmap = QPixmap(photo['thumbnail_path'])
        elif photo['file_path'] and Path(photo['file_path']).exists():
            pixmap = QPixmap(photo['file_path'])

        if pixmap and not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                160, 120,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            photo_label.setPixmap(scaled_pixmap)
        else:
            photo_label.setText("🖼️\nNáhled není k dispozici")

        layout.addWidget(photo_label)

        # Informace
        info_layout = QHBoxLayout()

        # Kategorie s ikonou
        category = photo['category'] or 'Ostatní'
        category_icon = self.get_category_icon(category)
        category_label = QLabel(f"{category_icon}")
        category_label.setToolTip(category)
        info_layout.addWidget(category_label)

        # Hvězdička pro hlavní fotku
        if photo['is_main']:
            main_label = QLabel("⭐")
            main_label.setToolTip("Hlavní fotka")
            info_layout.addWidget(main_label)

        info_layout.addStretch()

        # Datum
        if photo['taken_at']:
            try:
                taken = datetime.strptime(str(photo['taken_at']), "%Y-%m-%d")
                date_label = QLabel(taken.strftime("%d.%m.%Y"))
            except:
                date_label = QLabel("")
        else:
            date_label = QLabel("")
        date_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        info_layout.addWidget(date_label)

        layout.addLayout(info_layout)

        # Popis (zkrácený)
        desc = photo['description'] or ''
        if len(desc) > 25:
            desc = desc[:22] + "..."
        desc_label = QLabel(desc)
        desc_label.setStyleSheet("color: #34495e; font-size: 11px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Kliknutí pro lightbox
        frame.mousePressEvent = lambda event, p=photo: self.handle_photo_click(event, p)

        return frame

    def get_category_icon(self, category):
        """Získání ikony podle kategorie"""
        icons = {
            "Celkové pohledy": "🏍️",
            "Detaily poškození": "🔧",
            "Servisní fotky": "🛠️",
            "Dokumentace stavu": "📋",
            "Před/Po servisu": "📅",
            "Ostatní": "📷"
        }
        return icons.get(category, "📷")

    def handle_photo_click(self, event, photo):
        """Zpracování kliknutí na fotku"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_lightbox(photo)
        elif event.button() == Qt.MouseButton.RightButton:
            self.show_photo_context_menu(photo)

    def show_photo_context_menu(self, photo):
        """Zobrazení kontextového menu pro fotku"""
        menu = QMenu(self)

        action_view = menu.addAction("👁️ Zobrazit ve velkém")
        action_view.triggered.connect(lambda: self.open_lightbox(photo))

        action_edit = menu.addAction("✏️ Upravit informace")
        action_edit.triggered.connect(lambda: self.edit_photo(photo))

        menu.addSeparator()

        if not photo['is_main']:
            action_main = menu.addAction("⭐ Nastavit jako hlavní")
            action_main.triggered.connect(lambda: self.set_main_photo(photo['id']))

        action_download = menu.addAction("📥 Stáhnout")
        action_download.triggered.connect(lambda: self.download_photo(photo))

        menu.addSeparator()

        action_delete = menu.addAction("🗑️ Smazat")
        action_delete.triggered.connect(lambda: self.remove_photo(photo['id']))

        menu.exec(QCursor.pos())

    def update_main_photo_info(self):
        """Aktualizace info o hlavní fotce"""
        main_photo = next((p for p in self.photos if p['is_main']), None)
        if main_photo:
            self.main_photo_info.setText(f"⭐ Hlavní fotka: {main_photo['file_name']}")
        else:
            self.main_photo_info.setText("ℹ️ Není nastavena hlavní fotka")

    def filter_photos(self):
        """Filtrování fotek podle kategorie"""
        selected_category = self.category_filter.currentText()

        if selected_category == "Vše":
            self.display_photos(self.photos)
        else:
            filtered = [p for p in self.photos if p['category'] == selected_category]
            self.display_photos(filtered)

    def add_photo(self):
        """Přidání nové fotky"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Vybrat fotky",
            "",
            "Obrázky (*.jpg *.jpeg *.png *.bmp *.gif);;Všechny soubory (*.*)"
        )

        if file_paths:
            dialog = AddPhotoDialog(self)
            if dialog.exec():
                data = dialog.get_data()

                success_count = 0
                for file_path in file_paths:
                    if self.save_photo(file_path, data):
                        success_count += 1

                self.load_photos()
                QMessageBox.information(
                    self,
                    "Úspěch",
                    f"Nahráno {success_count} z {len(file_paths)} fotek."
                )

    def save_photo(self, source_path, metadata):
        """Uložení fotky"""
        try:
            source = Path(source_path)
            if not source.exists():
                return False

            # Vytvoření unikátního názvu
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            new_filename = f"{timestamp}{source.suffix}"
            dest_path = self.photos_dir / new_filename

            # Kopírování souboru
            shutil.copy2(source, dest_path)

            # Vytvoření thumbnail
            thumbnail_path = self.create_thumbnail(dest_path)

            # Uložení do databáze
            db.execute_query("""
                INSERT INTO vehicle_photos (
                    vehicle_id, file_name, file_path, thumbnail_path,
                    category, description, taken_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.vehicle_id,
                source.name,
                str(dest_path),
                str(thumbnail_path) if thumbnail_path else None,
                metadata['category'],
                metadata['description'],
                metadata['taken_at']
            ))

            return True
        except Exception as e:
            print(f"Chyba při ukládání fotky: {e}")
            return False

    def create_thumbnail(self, image_path):
        """Vytvoření thumbnail"""
        try:
            pixmap = QPixmap(str(image_path))
            if pixmap.isNull():
                return None

            # Zmenšení na 150x150
            thumbnail = pixmap.scaled(
                150, 150,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            # Uložení thumbnail
            thumb_filename = f"thumb_{Path(image_path).name}"
            thumb_path = self.photos_dir / "thumbnails" / thumb_filename
            thumbnail.save(str(thumb_path), "JPEG", 85)

            return thumb_path
        except Exception as e:
            print(f"Chyba při vytváření thumbnail: {e}")
            return None

    def remove_photo(self, photo_id):
        """Smazání fotky"""
        reply = QMessageBox.question(
            self,
            "Potvrzení",
            "Opravdu chcete smazat tuto fotku?\nTato akce je nevratná.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Získání cest k souborům
                photo = db.fetch_one(
                    "SELECT file_path, thumbnail_path FROM vehicle_photos WHERE id = ?",
                    (photo_id,)
                )

                if photo:
                    # Smazání souborů
                    if photo['file_path']:
                        file_path = Path(photo['file_path'])
                        if file_path.exists():
                            file_path.unlink()

                    if photo['thumbnail_path']:
                        thumb_path = Path(photo['thumbnail_path'])
                        if thumb_path.exists():
                            thumb_path.unlink()

                    # Smazání z DB
                    db.execute_query(
                        "DELETE FROM vehicle_photos WHERE id = ?",
                        (photo_id,)
                    )

                    self.load_photos()
                    QMessageBox.information(self, "Úspěch", "Fotka byla smazána.")

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat fotku:\n{e}")

    def set_main_photo(self, photo_id):
        """Nastavení hlavní fotky"""
        try:
            # Zrušení předchozí hlavní fotky
            db.execute_query(
                "UPDATE vehicle_photos SET is_main = 0 WHERE vehicle_id = ?",
                (self.vehicle_id,)
            )

            # Nastavení nové hlavní fotky
            db.execute_query(
                "UPDATE vehicle_photos SET is_main = 1 WHERE id = ?",
                (photo_id,)
            )

            self.load_photos()
            QMessageBox.information(self, "Úspěch", "Hlavní fotka byla nastavena.")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se nastavit hlavní fotku:\n{e}")

    def edit_photo(self, photo):
        """Editace informací o fotce"""
        dialog = EditPhotoDialog(photo, self)
        if dialog.exec():
            data = dialog.get_data()

            try:
                db.execute_query("""
                    UPDATE vehicle_photos
                    SET category = ?, description = ?, taken_at = ?
                    WHERE id = ?
                """, (data['category'], data['description'], data['taken_at'], photo['id']))

                self.load_photos()
                QMessageBox.information(self, "Úspěch", "Informace byly aktualizovány.")

            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit změny:\n{e}")

    def download_photo(self, photo):
        """Stažení fotky"""
        source_path = Path(photo['file_path'])

        if not source_path.exists():
            QMessageBox.warning(self, "Chyba", "Soubor nebyl nalezen.")
            return

        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit fotku",
            photo['file_name'],
            f"Obrázky (*{source_path.suffix})"
        )

        if dest_path:
            try:
                shutil.copy2(source_path, dest_path)
                QMessageBox.information(self, "Úspěch", f"Fotka byla uložena do:\n{dest_path}")
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit fotku:\n{e}")

    def open_lightbox(self, photo):
        """Otevření lightboxu"""
        dialog = PhotoLightboxDialog(photo, self.photos, self)
        dialog.exec()

    def export_gallery(self):
        """Export celé galerie"""
        if not self.photos:
            QMessageBox.warning(self, "Upozornění", "Galerie je prázdná.")
            return

        dest_dir = QFileDialog.getExistingDirectory(
            self,
            "Vybrat složku pro export"
        )

        if dest_dir:
            try:
                dest_path = Path(dest_dir)
                exported = 0

                for photo in self.photos:
                    source = Path(photo['file_path'])
                    if source.exists():
                        # Vytvoření názvu s kategorií
                        category = photo['category'].replace(" ", "_").replace("/", "-")
                        new_name = f"{category}_{photo['file_name']}"
                        shutil.copy2(source, dest_path / new_name)
                        exported += 1

                QMessageBox.information(
                    self,
                    "Export dokončen",
                    f"Exportováno {exported} fotek do:\n{dest_dir}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se exportovat galerii:\n{e}")

    def dragEnterEvent(self, event):
        """Zpracování drag enter"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("background-color: #d5f5e3;")

    def dragLeaveEvent(self, event):
        """Zpracování drag leave"""
        self.setStyleSheet("")

    def dropEvent(self, event):
        """Zpracování drop"""
        self.setStyleSheet("")

        urls = event.mimeData().urls()
        file_paths = []

        for url in urls:
            path = url.toLocalFile()
            if path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
                file_paths.append(path)

        if file_paths:
            dialog = AddPhotoDialog(self)
            if dialog.exec():
                data = dialog.get_data()

                success_count = 0
                for file_path in file_paths:
                    if self.save_photo(file_path, data):
                        success_count += 1

                self.load_photos()
                QMessageBox.information(
                    self,
                    "Úspěch",
                    f"Nahráno {success_count} z {len(file_paths)} fotek."
                )


class AddPhotoDialog(QDialog):
    """Dialog pro přidání fotky"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("📷 Informace o fotce")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Kategorie
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Celkové pohledy",
            "Detaily poškození",
            "Servisní fotky",
            "Dokumentace stavu",
            "Před/Po servisu",
            "Ostatní"
        ])
        form_layout.addRow("Kategorie:", self.category_combo)

        # Datum pořízení
        from PyQt6.QtWidgets import QDateEdit
        from PyQt6.QtCore import QDate

        self.taken_date = QDateEdit()
        self.taken_date.setCalendarPopup(True)
        self.taken_date.setDate(QDate.currentDate())
        self.taken_date.setDisplayFormat("dd.MM.yyyy")
        form_layout.addRow("Datum pořízení:", self.taken_date)

        # Popis
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Popis fotky...")
        self.description_input.setMaximumHeight(80)
        form_layout.addRow("Popis:", self.description_input)

        layout.addLayout(form_layout)

        # Tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_cancel = QPushButton("❌ Zrušit")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Uložit")
        btn_save.setStyleSheet(f"background-color: {config.COLOR_SUCCESS};")
        btn_save.clicked.connect(self.accept)
        buttons_layout.addWidget(btn_save)

        layout.addLayout(buttons_layout)

    def get_data(self):
        """Získání dat"""
        return {
            'category': self.category_combo.currentText(),
            'description': self.description_input.toPlainText().strip(),
            'taken_at': self.taken_date.date().toString("yyyy-MM-dd")
        }


class EditPhotoDialog(AddPhotoDialog):
    """Dialog pro editaci fotky"""

    def __init__(self, photo, parent=None):
        self.photo = photo
        super().__init__(parent)
        self.load_data()

    def load_data(self):
        """Načtení dat do formuláře"""
        self.setWindowTitle("✏️ Upravit informace o fotce")

        # Kategorie
        if self.photo['category']:
            idx = self.category_combo.findText(self.photo['category'])
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)

        # Popis
        if self.photo['description']:
            self.description_input.setPlainText(self.photo['description'])

        # Datum
        if self.photo['taken_at']:
            try:
                from PyQt6.QtCore import QDate
                taken = datetime.strptime(str(self.photo['taken_at']), "%Y-%m-%d")
                self.taken_date.setDate(QDate(taken.year, taken.month, taken.day))
            except:
                pass


class PhotoLightboxDialog(QDialog):
    """Lightbox pro velký náhled fotky"""

    def __init__(self, current_photo, all_photos, parent=None):
        super().__init__(parent)
        self.all_photos = all_photos
        self.current_index = next(
            (i for i, p in enumerate(all_photos) if p['id'] == current_photo['id']),
            0
        )
        self.init_ui()
        self.show_photo()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("📷 Prohlížeč fotek")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #2c3e50;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Navigace
        nav_layout = QHBoxLayout()

        btn_prev = QPushButton("◀️ Předchozí")
        btn_prev.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #4a6278;
            }
        """)
        btn_prev.clicked.connect(self.prev_photo)
        nav_layout.addWidget(btn_prev)

        self.counter_label = QLabel()
        self.counter_label.setStyleSheet("color: white; font-size: 14px;")
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(self.counter_label)

        btn_next = QPushButton("Další ▶️")
        btn_next.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #4a6278;
            }
        """)
        btn_next.clicked.connect(self.next_photo)
        nav_layout.addWidget(btn_next)

        layout.addLayout(nav_layout)

        # Fotka
        self.photo_label = QLabel()
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_label.setStyleSheet("""
            QLabel {
                background-color: black;
                border-radius: 10px;
            }
        """)
        layout.addWidget(self.photo_label, 1)

        # Info o fotce
        self.info_label = QLabel()
        self.info_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                padding: 10px;
                background-color: #34495e;
                border-radius: 5px;
            }
        """)
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # Tlačítka
        buttons_layout = QHBoxLayout()

        btn_download = QPushButton("📥 Stáhnout plnou velikost")
        btn_download.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        btn_download.clicked.connect(self.download_current)
        buttons_layout.addWidget(btn_download)

        buttons_layout.addStretch()

        btn_close = QPushButton("✅ Zavřít")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_close.clicked.connect(self.accept)
        buttons_layout.addWidget(btn_close)

        layout.addLayout(buttons_layout)

    def show_photo(self):
        """Zobrazení aktuální fotky"""
        if not self.all_photos:
            return

        photo = self.all_photos[self.current_index]

        # Načtení a zobrazení fotky
        if photo['file_path'] and Path(photo['file_path']).exists():
            pixmap = QPixmap(photo['file_path'])
            if not pixmap.isNull():
                # Škálování na velikost okna
                scaled = pixmap.scaled(
                    self.photo_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.photo_label.setPixmap(scaled)
            else:
                self.photo_label.setText("🖼️ Nelze načíst fotku")
        else:
            self.photo_label.setText("🖼️ Soubor nenalezen")

        # Aktualizace counteru
        self.counter_label.setText(f"{self.current_index + 1} / {len(self.all_photos)}")

        # Info o fotce
        info_parts = [f"📁 {photo['file_name']}"]
        if photo['category']:
            info_parts.append(f"📂 Kategorie: {photo['category']}")
        if photo['taken_at']:
            try:
                taken = datetime.strptime(str(photo['taken_at']), "%Y-%m-%d")
                info_parts.append(f"📅 Pořízeno: {taken.strftime('%d.%m.%Y')}")
            except:
                pass
        if photo['description']:
            info_parts.append(f"📝 {photo['description']}")
        if photo['is_main']:
            info_parts.append("⭐ Hlavní fotka")

        self.info_label.setText(" | ".join(info_parts))

    def prev_photo(self):
        """Předchozí fotka"""
        if self.current_index > 0:
            self.current_index -= 1
            self.show_photo()

    def next_photo(self):
        """Další fotka"""
        if self.current_index < len(self.all_photos) - 1:
            self.current_index += 1
            self.show_photo()

    def download_current(self):
        """Stažení aktuální fotky"""
        photo = self.all_photos[self.current_index]
        source_path = Path(photo['file_path'])

        if not source_path.exists():
            QMessageBox.warning(self, "Chyba", "Soubor nebyl nalezen.")
            return

        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit fotku",
            photo['file_name'],
            f"Obrázky (*{source_path.suffix})"
        )

        if dest_path:
            try:
                shutil.copy2(source_path, dest_path)
                QMessageBox.information(self, "Úspěch", f"Fotka byla uložena.")
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit fotku:\n{e}")

    def keyPressEvent(self, event):
        """Klávesové zkratky"""
        if event.key() == Qt.Key.Key_Left:
            self.prev_photo()
        elif event.key() == Qt.Key.Key_Right:
            self.next_photo()
        elif event.key() == Qt.Key.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        """Při změně velikosti znovu škálovat fotku"""
        super().resizeEvent(event)
        self.show_photo()
