# -*- coding: utf-8 -*-
"""
Audit log - historie aktivit uživatelů
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QFrame, QLineEdit, QComboBox, QHeaderView,
    QDateEdit, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, timedelta
from database_manager import db
import config


class AuditLog(QWidget):
    """Widget pro zobrazení audit logu"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.log_data = []

        self.init_ui()
        self.load_log()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        top_panel = self.create_top_panel()
        main_layout.addWidget(top_panel)

        filters_panel = self.create_filters_panel()
        main_layout.addWidget(filters_panel)

        self.create_table()
        main_layout.addWidget(self.table)

        bottom_panel = self.create_bottom_panel()
        main_layout.addWidget(bottom_panel)

    def create_top_panel(self):
        panel = QFrame()
        panel.setObjectName("topPanel")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("📊 Audit log")
        title.setObjectName("sectionTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)

        layout.addStretch()

        self.btn_export = QPushButton("📤 Export")
        self.btn_export.clicked.connect(self.export_log)
        layout.addWidget(self.btn_export)

        self.btn_clear_old = QPushButton("🗑️ Vyčistit staré")
        self.btn_clear_old.clicked.connect(self.clear_old_logs)
        layout.addWidget(self.btn_clear_old)

        panel.setStyleSheet(f"""
            #topPanel {{
                background-color: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
            }}
            #sectionTitle {{
                color: {config.COLOR_PRIMARY};
            }}
        """)

        return panel

    def create_filters_panel(self):
        panel = QFrame()
        panel.setObjectName("filtersPanel")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        date_from_layout = QHBoxLayout()
        date_from_label = QLabel("Od:")
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.dateChanged.connect(self.filter_log)
        date_from_layout.addWidget(date_from_label)
        date_from_layout.addWidget(self.date_from)
        layout.addLayout(date_from_layout)

        date_to_layout = QHBoxLayout()
        date_to_label = QLabel("Do:")
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.dateChanged.connect(self.filter_log)
        date_to_layout.addWidget(date_to_label)
        date_to_layout.addWidget(self.date_to)
        layout.addLayout(date_to_layout)

        event_layout = QHBoxLayout()
        event_label = QLabel("Typ:")
        self.cmb_event_type = QComboBox()
        self.cmb_event_type.addItem("Všechny typy", None)
        self.cmb_event_type.addItem("🔐 Přihlášení", "login")
        self.cmb_event_type.addItem("🔓 Odhlášení", "logout")
        self.cmb_event_type.addItem("👤 Uživatel vytvořen", "user_created")
        self.cmb_event_type.addItem("✏️ Uživatel upraven", "user_edited")
        self.cmb_event_type.addItem("🗑️ Uživatel smazán", "user_deleted")
        self.cmb_event_type.addItem("🔑 Reset hesla", "password_reset")
        self.cmb_event_type.addItem("🎭 Role upravena", "role_updated")
        self.cmb_event_type.addItem("🔐 Oprávnění změněno", "permission_changed")
        self.cmb_event_type.addItem("⚠️ Neúspěšné přihlášení", "login_failed")
        self.cmb_event_type.currentIndexChanged.connect(self.filter_log)
        event_layout.addWidget(event_label)
        event_layout.addWidget(self.cmb_event_type)
        layout.addLayout(event_layout)

        user_layout = QHBoxLayout()
        user_label = QLabel("Uživatel:")
        self.cmb_user = QComboBox()
        self.cmb_user.addItem("Všichni uživatelé", None)
        self.load_users_combo()
        self.cmb_user.currentIndexChanged.connect(self.filter_log)
        user_layout.addWidget(user_label)
        user_layout.addWidget(self.cmb_user)
        layout.addLayout(user_layout)

        search_layout = QHBoxLayout()
        search_label = QLabel("🔍")
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Hledat v detailech...")
        self.txt_search.textChanged.connect(self.filter_log)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.txt_search)
        layout.addLayout(search_layout)

        layout.addStretch()

        self.btn_reset = QPushButton("🔄 Reset")
        self.btn_reset.clicked.connect(self.reset_filters)
        layout.addWidget(self.btn_reset)

        panel.setStyleSheet("""
            #filtersPanel {
                background-color: #f8f9fa;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
            }
            QDateEdit, QComboBox, QLineEdit {
                padding: 6px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }
        """)

        return panel

    def create_table(self):
        self.table = QTableWidget()
        self.table.setObjectName("auditTable")

        columns = ["Datum a čas", "Uživatel", "Typ události", "Detaily", "IP adresa"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 180)
        self.table.setColumnWidth(4, 120)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)

        self.table.setStyleSheet(f"""
            #auditTable {{
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                background-color: white;
                gridline-color: #e0e0e0;
            }}
            #auditTable::item {{
                padding: 8px;
            }}
            QHeaderView::section {{
                background-color: {config.COLOR_PRIMARY};
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
        """)

    def create_bottom_panel(self):
        panel = QFrame()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_count = QLabel("Celkem: 0 záznamů")
        self.lbl_count.setStyleSheet("color: #666; font-weight: bold;")
        layout.addWidget(self.lbl_count)

        layout.addStretch()

        self.lbl_last_update = QLabel(f"Aktualizováno: {datetime.now().strftime('%H:%M')}")
        self.lbl_last_update.setStyleSheet("color: #666;")
        layout.addWidget(self.lbl_last_update)

        return panel

    def load_users_combo(self):
        users = db.fetch_all("SELECT id, username FROM users ORDER BY username")
        for user in users:
            self.cmb_user.addItem(user['username'], user['id'])

    def load_log(self):
        query = """
            SELECT
                id, user_id, username, event_type, details, ip_address, created_at
            FROM audit_log
            ORDER BY created_at DESC
            LIMIT 1000
        """

        self.log_data = db.fetch_all(query)
        self.display_log(self.log_data)

    def display_log(self, logs):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        event_type_names = {
            'login': '🔐 Přihlášení',
            'logout': '🔓 Odhlášení',
            'user_created': '👤 Uživatel vytvořen',
            'user_edited': '✏️ Uživatel upraven',
            'user_deleted': '🗑️ Uživatel smazán',
            'password_reset': '🔑 Reset hesla',
            'role_updated': '🎭 Role upravena',
            'permission_changed': '🔐 Oprávnění změněno',
            'login_failed': '⚠️ Neúspěšné přihlášení',
            'profile_updated': '👤 Profil upraven',
            'users_imported': '📥 Import uživatelů'
        }

        event_type_colors = {
            'login': config.COLOR_SUCCESS,
            'logout': '#95a5a6',
            'user_created': config.COLOR_SECONDARY,
            'user_edited': config.COLOR_WARNING,
            'user_deleted': config.COLOR_DANGER,
            'password_reset': config.COLOR_WARNING,
            'role_updated': config.COLOR_SECONDARY,
            'permission_changed': config.COLOR_WARNING,
            'login_failed': config.COLOR_DANGER,
            'profile_updated': config.COLOR_SECONDARY,
            'users_imported': config.COLOR_SUCCESS
        }

        for log in logs:
            row = self.table.rowCount()
            self.table.insertRow(row)

            if log['created_at']:
                try:
                    dt = datetime.fromisoformat(log['created_at'])
                    date_text = dt.strftime("%d.%m.%Y %H:%M:%S")
                except:
                    date_text = log['created_at']
            else:
                date_text = "--"
            date_item = QTableWidgetItem(date_text)
            date_item.setFlags(date_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, date_item)

            user_item = QTableWidgetItem(log['username'] or f"ID: {log['user_id']}")
            user_item.setFlags(user_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, user_item)

            event_name = event_type_names.get(log['event_type'], log['event_type'])
            event_item = QTableWidgetItem(event_name)
            event_item.setFlags(event_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            event_color = event_type_colors.get(log['event_type'], '#666')
            event_item.setForeground(QColor(event_color))
            self.table.setItem(row, 2, event_item)

            details_item = QTableWidgetItem(log['details'] or "")
            details_item.setFlags(details_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, details_item)

            ip_item = QTableWidgetItem(log['ip_address'] or "--")
            ip_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            ip_item.setFlags(ip_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, ip_item)

        self.table.setSortingEnabled(True)
        self.lbl_count.setText(f"Celkem: {len(logs)} záznamů")
        self.lbl_last_update.setText(f"Aktualizováno: {datetime.now().strftime('%H:%M')}")

    def filter_log(self):
        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()
        event_type = self.cmb_event_type.currentData()
        user_id = self.cmb_user.currentData()
        search_text = self.txt_search.text().lower()

        filtered = []
        for log in self.log_data:
            if log['created_at']:
                try:
                    log_date = datetime.fromisoformat(log['created_at']).date()
                    if log_date < date_from or log_date > date_to:
                        continue
                except:
                    pass

            if event_type and log['event_type'] != event_type:
                continue

            if user_id and log['user_id'] != user_id:
                continue

            if search_text:
                details = (log['details'] or "").lower()
                if search_text not in details:
                    continue

            filtered.append(log)

        self.display_log(filtered)

    def reset_filters(self):
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_to.setDate(QDate.currentDate())
        self.cmb_event_type.setCurrentIndex(0)
        self.cmb_user.setCurrentIndex(0)
        self.txt_search.clear()
        self.display_log(self.log_data)

    def export_log(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export audit logu",
            f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV soubory (*.csv)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8-sig') as f:
                    f.write("Datum a čas;Uživatel;Typ události;Detaily;IP adresa\n")

                    for row in range(self.table.rowCount()):
                        row_data = []
                        for col in range(5):
                            item = self.table.item(row, col)
                            row_data.append(item.text() if item else "")
                        f.write(";".join(row_data) + "\n")

                QMessageBox.information(self, "Export", f"Audit log byl exportován do:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Chyba při exportu: {e}")

    def clear_old_logs(self):
        reply = QMessageBox.question(
            self,
            "Vyčistit staré záznamy",
            "Opravdu chcete smazat záznamy starší než 90 dní?\n\nTato akce je nevratná!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            cutoff_date = (datetime.now() - timedelta(days=90)).isoformat()

            result = db.fetch_one(
                "SELECT COUNT(*) as count FROM audit_log WHERE created_at < ?",
                (cutoff_date,)
            )
            count = result['count'] if result else 0

            if count > 0:
                db.execute_query(
                    "DELETE FROM audit_log WHERE created_at < ?",
                    (cutoff_date,)
                )

                QMessageBox.information(
                    self,
                    "Vyčištěno",
                    f"Bylo smazáno {count} starých záznamů."
                )
                self.load_log()
            else:
                QMessageBox.information(self, "Info", "Žádné staré záznamy k vymazání.")

    def refresh(self):
        self.load_log()
