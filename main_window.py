# -*- coding: utf-8 -*-
"""
Hlavní okno aplikace Motoservis DMS (s vynucením oprávnění a zobrazením přihlášeného uživatele)
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QStackedWidget, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import config
from utils.utils_auth import get_current_username, get_current_user_id
from utils.utils_permissions import has_permission


class MainWindow(QMainWindow):
    """Hlavní okno aplikace"""

    def __init__(self):
        super().__init__()
        self.current_module = None
        self.modules = {}  # instance modulů
        self.init_ui()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.setGeometry(100, 100, config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.setMinimumSize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.create_navigation_panel(main_layout)
        self.create_content_panel(main_layout)
        self.set_styles()

    def create_navigation_panel(self, parent_layout):
        """Levá navigace"""
        nav_widget = QWidget()
        nav_widget.setObjectName("navPanel")
        nav_widget.setFixedWidth(250)

        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        # Hlavička
        header = QFrame()
        header.setObjectName("navHeader")
        header.setFixedHeight(80)
        header_layout = QVBoxLayout(header)

        title = QLabel(config.APP_NAME)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont(); title_font.setPointSize(16); title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel(f"Verze {config.APP_VERSION}")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont(); subtitle_font.setPointSize(9)
        subtitle.setFont(subtitle_font)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        nav_layout.addWidget(header)

        # Tlačítka navigace (jen moduly, na které má uživatel právo "view")
        self.nav_buttons = {}
        uid = get_current_user_id()
        for module in config.MODULES:
            can_view = True
            if uid:
                can_view = has_permission(uid, module["id"], "view")
            if not can_view:
                continue
            btn = QPushButton(f"{module['icon']}  {module['name']}")
            btn.setObjectName("navButton")
            btn.setFixedHeight(50)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, m=module['id']: self.switch_module(m))
            self.nav_buttons[module['id']] = btn
            nav_layout.addWidget(btn)

        # Posuvník dolů
        nav_layout.addStretch()

        # Informační panel: jméno přihlášeného
        info_panel = QFrame()
        info_panel.setObjectName("infoPanel")
        info_panel.setFixedHeight(60)
        info_layout = QVBoxLayout(info_panel)

        user_label = QLabel(f"👤 Přihlášen: {get_current_username() or 'Neznámý'}")
        user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(user_label)

        nav_layout.addWidget(info_panel)
        parent_layout.addWidget(nav_widget)

    def create_content_panel(self, parent_layout):
        """Pravý panel s obsahem"""
        content_widget = QWidget()
        content_widget.setObjectName("contentPanel")

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Horní lišta
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(60)
        top_bar_layout = QHBoxLayout(top_bar)

        self.module_title = QLabel("Úvodní stránka")
        title_font = QFont(); title_font.setPointSize(18); title_font.setBold(True)
        self.module_title.setFont(title_font)

        top_bar_layout.addWidget(self.module_title)
        top_bar_layout.addStretch()

        # Tlačítko zálohy – povol jen pokud má uživatel právo "admin" pro modul "administration"
        backup_btn = QPushButton("💾 Záloha")
        backup_btn.clicked.connect(self.create_backup)
        backup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        uid = get_current_user_id()
        if uid and not has_permission(uid, "administration", "admin"):
            backup_btn.setEnabled(False)
        top_bar_layout.addWidget(backup_btn)

        content_layout.addWidget(top_bar)

        # Stack pro moduly
        self.module_stack = QStackedWidget()
        self.module_stack.setObjectName("moduleStack")
        content_layout.addWidget(self.module_stack)

        parent_layout.addWidget(content_widget)

    def add_module(self, module_id, module_widget):
        """Registrace modulu"""
        self.modules[module_id] = module_widget
        self.module_stack.addWidget(module_widget)

    def switch_module(self, module_id):
        """Přepnutí modulu"""
        if module_id in self.modules:
            # zvýraznění aktivního tlačítka
            for btn_id, btn in self.nav_buttons.items():
                btn.setProperty("active", btn_id == module_id)
                btn.style().unpolish(btn); btn.style().polish(btn)
            # přepnutí stacku
            self.module_stack.setCurrentWidget(self.modules[module_id])
            self.current_module = module_id
            # titulek
            module_name = next((m['name'] for m in config.MODULES if m['id'] == module_id), '')
            self.module_title.setText(module_name)
            # refresh modulu
            if hasattr(self.modules[module_id], 'refresh'):
                self.modules[module_id].refresh()
        else:
            QMessageBox.warning(
                self,
                "Modul není implementován",
                f"Modul '{module_id}' ještě není implementován.\n"
                "Bude přidán v příští verzi."
            )

    def create_backup(self):
        """Vytvoření zálohy databáze"""
        from database_manager import db
        reply = QMessageBox.question(
            self,
            "Záloha databáze",
            "Chcete vytvořit zálohu databáze?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if db.backup_database():
                QMessageBox.information(
                    self,
                    "Záloha vytvořena",
                    f"Záloha byla úspěšně vytvořena.\nUmístění: {config.BACKUP_DIR}"
                )
            else:
                QMessageBox.critical(self, "Chyba", "Nepodařilo se vytvořit zálohu databáze.")

    def set_styles(self):
        """Styly aplikace"""
        stylesheet = f"""
            QMainWindow {{
                background-color: #f5f5f5;
            }}
            #navPanel {{
                background-color: {config.COLOR_PRIMARY};
                border-right: 2px solid #1a252f;
            }}
            #navHeader {{
                background-color: #1a252f;
                color: white;
            }}
            #navButton {{
                background-color: transparent;
                border: none;
                color: white;
                text-align: left;
                padding: 15px 20px;
                font-size: 14px;
            }}
            #navButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            #navButton[active="true"] {{
                background-color: {config.COLOR_SECONDARY};
                border-left: 4px solid {config.COLOR_SUCCESS};
            }}
            #infoPanel {{
                background-color: #1a252f;
                color: white;
                padding: 10px;
            }}
            #topBar {{
                background-color: white;
                border-bottom: 2px solid #e0e0e0;
                padding: 0 20px;
            }}
            #contentPanel {{
                background-color: #f5f5f5;
            }}
            #moduleStack {{
                background-color: #f5f5f5;
            }}
            QPushButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #2980b9;
            }}
            QPushButton:pressed {{
                background-color: #21618c;
            }}
        """
        self.setStyleSheet(stylesheet)
