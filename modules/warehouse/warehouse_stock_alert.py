# -*- coding: utf-8 -*-
"""
Systém upozornění skladu - PROFESIONÁLNÍ
Kontrola minimálních stavů, notifikace, email alerts, historie
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QFormLayout, QLineEdit, QCheckBox, QSpinBox, QMessageBox,
    QTabWidget, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont
import config
from database_manager import db
from datetime import datetime, timedelta


class WarehouseStockAlertWindow(QMainWindow):
    """Okno systému upozornění"""

    alert_resolved = pyqtSignal(int)  # ID položky byla vyřešena

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("⚠️ Systém upozornění skladu")
        self.setMinimumSize(1000, 700)

        self.init_ui()
        self.load_alerts()

    def init_ui(self):
        """Inicializace UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === HORNÍ LIŠTA ===
        self.create_action_bar(main_layout)

        # === ZÁLOŽKY ===
        self.tabs = QTabWidget()

        # ZÁLOŽKA 1: Dashboard kritických položek
        self.tab_dashboard = self.create_tab_dashboard()
        self.tabs.addTab(self.tab_dashboard, "⚠️ Kritické položky")

        # ZÁLOŽKA 2: Historie upozornění
        self.tab_history = self.create_tab_history()
        self.tabs.addTab(self.tab_history, "📋 Historie")

        # ZÁLOŽKA 3: Nastavení
        self.tab_settings = self.create_tab_settings()
        self.tabs.addTab(self.tab_settings, "⚙️ Nastavení")

        main_layout.addWidget(self.tabs)

    def create_action_bar(self, parent_layout):
        """Horní lišta"""
        action_bar = QWidget()
        action_bar.setFixedHeight(80)
        action_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {config.COLOR_DANGER};
                border-bottom: 3px solid #c0392b;
            }}
        """)
        action_layout = QVBoxLayout(action_bar)
        action_layout.setContentsMargins(15, 10, 15, 10)

        # Nadpis
        title = QLabel("⚠️ SYSTÉM UPOZORNĚNÍ SKLADU")
        title.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        action_layout.addWidget(title)

        # Statistiky
        stats_layout = QHBoxLayout()

        self.lbl_critical_count = QLabel("Kritických: 0")
        self.lbl_critical_count.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(self.lbl_critical_count)

        self.lbl_warning_count = QLabel("Varování: 0")
        self.lbl_warning_count.setStyleSheet("color: white; font-size: 14px;")
        stats_layout.addWidget(self.lbl_warning_count)

        stats_layout.addStretch()

        # Tlačítka
        btn_refresh = QPushButton("↻ Obnovit")
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #e74c3c;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        btn_refresh.clicked.connect(self.load_alerts)
        stats_layout.addWidget(btn_refresh)

        btn_close = QPushButton("✕ Zavřít")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        btn_close.clicked.connect(self.close)
        stats_layout.addWidget(btn_close)

        action_layout.addLayout(stats_layout)

        parent_layout.addWidget(action_bar)

    # ========================================
    # ZÁLOŽKA: DASHBOARD
    # ========================================

    def create_tab_dashboard(self):
        """ZÁLOŽKA: Dashboard kritických položek"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info
        info = QLabel(
            "⚠️ Položky, které vyžadují vaši pozornost:\n"
            "• KRITICKÉ (červené) - pod minimálním stavem\n"
            "• VAROVÁNÍ (oranžové) - blíží se k minimu (< 1.5× minimum)"
        )
        info.setStyleSheet("""
            padding: 15px;
            background-color: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 5px;
            color: #856404;
        """)
        info.setWordWrap(True)
        layout.addWidget(info)

        # Tabulka kritických položek
        self.table_alerts = QTableWidget()
        self.table_alerts.setColumnCount(10)
        self.table_alerts.setHorizontalHeaderLabels([
            'Stav', 'Položka', 'Aktuální', 'Minimum', 'Chybí', 'Dodavatel',
            'Telefon', 'Akce', 'Poslední upozornění', 'ID'
        ])
        self.table_alerts.setColumnHidden(9, True)
        self.table_alerts.horizontalHeader().setStretchLastSection(True)
        self.table_alerts.setAlternatingRowColors(True)

        self.table_alerts.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                font-weight: bold;
            }
        """)

        layout.addWidget(self.table_alerts)

        # Akční tlačítka
        actions = QHBoxLayout()

        btn_order_all = QPushButton("📦 Objednat vše pod minimem")
        btn_order_all.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 12px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
        """)
        btn_order_all.clicked.connect(self.order_all_below_minimum)
        actions.addWidget(btn_order_all)

        btn_export = QPushButton("📄 Export seznamu")
        btn_export.clicked.connect(self.export_alert_list)
        actions.addWidget(btn_export)

        btn_send_email = QPushButton("📧 Odeslat email dodavatelům")
        btn_send_email.clicked.connect(self.send_email_to_suppliers)
        actions.addWidget(btn_send_email)

        actions.addStretch()

        layout.addLayout(actions)

        return widget

    def load_alerts(self):
        """Načtení upozornění"""
        try:
            # Načtení položek pod nebo blízko minima
            items = db.execute_query("""
                SELECT w.id, w.name, w.quantity, w.min_quantity, w.unit,
                       s.name as supplier, s.phone,
                       (SELECT MAX(created_at) FROM stock_alerts WHERE item_id = w.id) as last_alert
                FROM warehouse w
                LEFT JOIN warehouse_suppliers s ON w.supplier_id = s.id
                WHERE w.quantity < w.min_quantity * 1.5
                ORDER BY (w.quantity / NULLIF(w.min_quantity, 0)) ASC
            """)

            self.table_alerts.setRowCount(0)

            if not items:
                self.lbl_critical_count.setText("Kritických: 0 ✓")
                self.lbl_warning_count.setText("Varování: 0 ✓")
                return

            critical_count = 0
            warning_count = 0

            for item in items:
                row = self.table_alerts.rowCount()
                self.table_alerts.insertRow(row)

                item_id = item[0]
                name = item[1]
                quantity = item[2]
                min_qty = item[3]
                unit = item[4]
                supplier = item[5] or "---"
                phone = item[6] or "---"
                last_alert = item[7]

                shortage = max(0, min_qty - quantity)

                # Určení závažnosti
                if quantity < min_qty:
                    status = "❌ KRITICKÉ"
                    status_color = QColor(config.STOCK_CRITICAL)
                    critical_count += 1
                else:
                    status = "⚠️ VAROVÁNÍ"
                    status_color = QColor(config.STOCK_WARNING)
                    warning_count += 1

                # Status
                status_item = QTableWidgetItem(status)
                status_item.setBackground(status_color)
                status_item.setForeground(QColor("white"))
                status_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_alerts.setItem(row, 0, status_item)

                # Název
                self.table_alerts.setItem(row, 1, QTableWidgetItem(name))

                # Aktuální stav
                qty_item = QTableWidgetItem(f"{quantity:.2f} {unit}")
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table_alerts.setItem(row, 2, qty_item)

                # Minimum
                min_item = QTableWidgetItem(f"{min_qty:.2f}")
                min_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table_alerts.setItem(row, 3, min_item)

                # Chybí
                shortage_item = QTableWidgetItem(f"{shortage:.2f}")
                shortage_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if shortage > 0:
                    shortage_item.setBackground(QColor("#ffebee"))
                    shortage_item.setForeground(QColor("#c62828"))
                self.table_alerts.setItem(row, 4, shortage_item)

                # Dodavatel
                self.table_alerts.setItem(row, 5, QTableWidgetItem(supplier))

                # Telefon
                self.table_alerts.setItem(row, 6, QTableWidgetItem(phone))

                # Akce - tlačítko
                btn_order = QPushButton("📦 Objednat")
                btn_order.clicked.connect(lambda checked, iid=item_id: self.order_item(iid))
                self.table_alerts.setCellWidget(row, 7, btn_order)

                # Poslední upozornění
                last_text = last_alert.split()[0] if last_alert else "Nikdy"
                self.table_alerts.setItem(row, 8, QTableWidgetItem(last_text))

                # ID
                self.table_alerts.setItem(row, 9, QTableWidgetItem(str(item_id)))

                # Uložení do historie upozornění
                self.log_alert(item_id, status, quantity, min_qty)

            # Aktualizace statistik
            self.lbl_critical_count.setText(f"Kritických: {critical_count}")
            self.lbl_warning_count.setText(f"Varování: {warning_count}")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba:\n{str(e)}")

    def log_alert(self, item_id, status, quantity, min_qty):
        """Záznam upozornění do historie"""
        try:
            # Kontrola, zda už není záznam z dneška
            today = datetime.now().strftime('%Y-%m-%d')

            existing = db.execute_query(
                """SELECT id FROM stock_alerts
                   WHERE item_id = ? AND DATE(created_at) = ?""",
                [item_id, today]
            )

            if not existing:
                db.execute_query(
                    """INSERT INTO stock_alerts (item_id, alert_type, quantity, min_quantity, created_at)
                       VALUES (?, ?, ?, ?, ?)""",
                    [item_id, status, quantity, min_qty, datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
                )

        except Exception as e:
            print(f"Chyba při logování: {e}")

    def order_item(self, item_id):
        """Objednání jedné položky"""
        from .warehouse_widgets import ReceiveStockDialog

        dialog = ReceiveStockDialog(item_id, self)
        if dialog.exec():
            self.load_alerts()
            self.alert_resolved.emit(item_id)

    def order_all_below_minimum(self):
        """Vytvoření objednávky pro všechny položky pod minimem"""
        try:
            items = db.execute_query("""
                SELECT w.id, w.name, w.quantity, w.min_quantity, w.unit, s.name as supplier
                FROM warehouse w
                LEFT JOIN warehouse_suppliers s ON w.supplier_id = s.id
                WHERE w.quantity < w.min_quantity
                ORDER BY s.name, w.name
            """)

            if not items:
                QMessageBox.information(self, "Info", "Žádné položky pod minimem")
                return

            # Vytvoření seznamu objednávky
            order_text = "OBJEDNÁVKA POLOŽEK POD MINIMEM\n"
            order_text += f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            order_text += "="*60 + "\n\n"

            current_supplier = None

            for item in items:
                supplier = item[5] or "Bez dodavatele"

                if supplier != current_supplier:
                    order_text += f"\n{'='*60}\n"
                    order_text += f"DODAVATEL: {supplier}\n"
                    order_text += f"{'='*60}\n\n"
                    current_supplier = supplier

                name = item[1]
                current = item[2]
                minimum = item[3]
                unit = item[4]
                to_order = minimum - current + minimum  # Objednat minimum + zásobu

                order_text += f"• {name}\n"
                order_text += f"  Aktuální stav: {current:.2f} {unit}\n"
                order_text += f"  Minimum: {minimum:.2f} {unit}\n"
                order_text += f"  Doporučeno objednat: {to_order:.2f} {unit}\n\n"

            # Zobrazení v dialogu
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Objednávka")
            dialog.setText("Seznam položek k objednání:")
            dialog.setDetailedText(order_text)
            dialog.setIcon(QMessageBox.Icon.Information)
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba:\n{str(e)}")

    def export_alert_list(self):
        """Export seznamu upozornění"""
        from PyQt6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit seznam",
            f"kriticke_polozky_{datetime.now().strftime('%Y%m%d')}.txt",
            "Textové soubory (*.txt)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("KRITICKÉ POLOŽKY SKLADU\n")
                f.write(f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
                f.write("="*60 + "\n\n")

                for row in range(self.table_alerts.rowCount()):
                    status = self.table_alerts.item(row, 0).text()
                    name = self.table_alerts.item(row, 1).text()
                    current = self.table_alerts.item(row, 2).text()
                    minimum = self.table_alerts.item(row, 3).text()
                    shortage = self.table_alerts.item(row, 4).text()
                    supplier = self.table_alerts.item(row, 5).text()

                    f.write(f"{status} - {name}\n")
                    f.write(f"  Aktuální: {current}, Minimum: {minimum}\n")
                    f.write(f"  Chybí: {shortage}\n")
                    f.write(f"  Dodavatel: {supplier}\n\n")

            QMessageBox.information(self, "Úspěch", f"Seznam byl exportován:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba:\n{str(e)}")

    def send_email_to_suppliers(self):
        """Odeslání emailů dodavatelům"""
        QMessageBox.information(
            self,
            "Email notifikace",
            "Funkce email notifikací bude implementována v budoucí verzi.\n\n"
            "Bude vyžadovat konfiguraci SMTP serveru v nastavení."
        )

    # ========================================
    # ZÁLOŽKA: HISTORIE
    # ========================================

    def create_tab_history(self):
        """ZÁLOŽKA: Historie upozornění"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info
        info = QLabel("📋 Historie všech upozornění o nízkých stavech")
        info.setStyleSheet("padding: 10px; background-color: #ecf0f1; font-weight: bold;")
        layout.addWidget(info)

        # Filtr
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Zobrazit posledních:"))

        self.spin_history_days = QSpinBox()
        self.spin_history_days.setRange(1, 365)
        self.spin_history_days.setValue(30)
        self.spin_history_days.setSuffix(" dní")
        filter_layout.addWidget(self.spin_history_days)

        btn_load_history = QPushButton("Načíst")
        btn_load_history.clicked.connect(self.load_history)
        filter_layout.addWidget(btn_load_history)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Tabulka
        self.table_history = QTableWidget()
        self.table_history.setColumnCount(6)
        self.table_history.setHorizontalHeaderLabels([
            'Datum', 'Položka', 'Stav', 'Aktuální', 'Minimum', 'ID'
        ])
        self.table_history.setColumnHidden(5, True)
        self.table_history.horizontalHeader().setStretchLastSection(True)
        self.table_history.setAlternatingRowColors(True)

        layout.addWidget(self.table_history)

        return widget

    def load_history(self):
        """Načtení historie upozornění"""
        try:
            days = self.spin_history_days.value()
            date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            alerts = db.execute_query("""
                SELECT sa.created_at, w.name, sa.alert_type, sa.quantity, sa.min_quantity, sa.id
                FROM stock_alerts sa
                LEFT JOIN warehouse w ON sa.item_id = w.id
                WHERE DATE(sa.created_at) >= ?
                ORDER BY sa.created_at DESC
            """, [date_from])

            self.table_history.setRowCount(0)

            if not alerts:
                return

            for alert in alerts:
                row = self.table_history.rowCount()
                self.table_history.insertRow(row)

                created = alert[0]
                name = alert[1] or "Smazaná položka"
                alert_type = alert[2]
                quantity = alert[3]
                min_qty = alert[4]
                alert_id = alert[5]

                self.table_history.setItem(row, 0, QTableWidgetItem(created))
                self.table_history.setItem(row, 1, QTableWidgetItem(name))

                type_item = QTableWidgetItem(alert_type)
                if "KRITICKÉ" in alert_type:
                    type_item.setBackground(QColor(config.STOCK_CRITICAL))
                    type_item.setForeground(QColor("white"))
                else:
                    type_item.setBackground(QColor(config.STOCK_WARNING))
                self.table_history.setItem(row, 2, type_item)

                self.table_history.setItem(row, 3, QTableWidgetItem(f"{quantity:.2f}"))
                self.table_history.setItem(row, 4, QTableWidgetItem(f"{min_qty:.2f}"))
                self.table_history.setItem(row, 5, QTableWidgetItem(str(alert_id)))

        except Exception as e:
            print(f"Chyba: {e}")

    # ========================================
    # ZÁLOŽKA: NASTAVENÍ
    # ========================================

    def create_tab_settings(self):
        """ZÁLOŽKA: Nastavení"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Obecné nastavení
        general_group = QGroupBox("⚙️ Obecné nastavení")
        general_form = QFormLayout(general_group)

        self.check_auto_check = QCheckBox("Automatická kontrola při startu")
        self.check_auto_check.setChecked(True)
        general_form.addRow("", self.check_auto_check)

        self.spin_check_interval = QSpinBox()
        self.spin_check_interval.setRange(1, 24)
        self.spin_check_interval.setValue(1)
        self.spin_check_interval.setSuffix(" hodina(y)")
        general_form.addRow("Interval kontroly:", self.spin_check_interval)

        layout.addWidget(general_group)

        # Email nastavení
        email_group = QGroupBox("📧 Email notifikace")
        email_form = QFormLayout(email_group)

        self.check_email_enabled = QCheckBox("Povolit email notifikace")
        email_form.addRow("", self.check_email_enabled)

        self.input_smtp_server = QLineEdit()
        self.input_smtp_server.setPlaceholderText("smtp.gmail.com")
        email_form.addRow("SMTP server:", self.input_smtp_server)

        self.spin_smtp_port = QSpinBox()
        self.spin_smtp_port.setRange(1, 65535)
        self.spin_smtp_port.setValue(587)
        email_form.addRow("Port:", self.spin_smtp_port)

        self.input_email_from = QLineEdit()
        self.input_email_from.setPlaceholderText("vas@email.cz")
        email_form.addRow("Email odesílatele:", self.input_email_from)

        self.input_email_password = QLineEdit()
        self.input_email_password.setEchoMode(QLineEdit.EchoMode.Password)
        email_form.addRow("Heslo:", self.input_email_password)

        self.input_email_to = QLineEdit()
        self.input_email_to.setPlaceholderText("prijemce@email.cz")
        email_form.addRow("Email příjemce:", self.input_email_to)

        btn_test_email = QPushButton("✉️ Otestovat email")
        btn_test_email.clicked.connect(self.test_email)
        email_form.addRow("", btn_test_email)

        layout.addWidget(email_group)

        # Tlačítka
        buttons = QHBoxLayout()

        btn_save_settings = QPushButton("💾 Uložit nastavení")
        btn_save_settings.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
        """)
        btn_save_settings.clicked.connect(self.save_settings)
        buttons.addWidget(btn_save_settings)

        buttons.addStretch()

        layout.addLayout(buttons)
        layout.addStretch()

        # Načtení nastavení
        self.load_settings()

        return widget

    def save_settings(self):
        """Uložení nastavení"""
        try:
            settings = {
                'auto_check': self.check_auto_check.isChecked(),
                'check_interval': self.spin_check_interval.value(),
                'email_enabled': self.check_email_enabled.isChecked(),
                'smtp_server': self.input_smtp_server.text(),
                'smtp_port': self.spin_smtp_port.value(),
                'email_from': self.input_email_from.text(),
                'email_password': self.input_email_password.text(),
                'email_to': self.input_email_to.text()
            }

            # Uložení do settings tabulky (nebo JSON souboru)
            import json
            settings_file = config.DATA_DIR / "alert_settings.json"

            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)

            QMessageBox.information(self, "Úspěch", "Nastavení bylo uloženo")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba:\n{str(e)}")

    def load_settings(self):
        """Načtení nastavení"""
        try:
            import json
            settings_file = config.DATA_DIR / "alert_settings.json"

            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                self.check_auto_check.setChecked(settings.get('auto_check', True))
                self.spin_check_interval.setValue(settings.get('check_interval', 1))
                self.check_email_enabled.setChecked(settings.get('email_enabled', False))
                self.input_smtp_server.setText(settings.get('smtp_server', ''))
                self.spin_smtp_port.setValue(settings.get('smtp_port', 587))
                self.input_email_from.setText(settings.get('email_from', ''))
                self.input_email_password.setText(settings.get('email_password', ''))
                self.input_email_to.setText(settings.get('email_to', ''))

        except Exception as e:
            print(f"Chyba při načítání nastavení: {e}")

    def test_email(self):
        """Test emailové notifikace"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # Získání nastavení
            smtp_server = self.input_smtp_server.text()
            smtp_port = self.spin_smtp_port.value()
            email_from = self.input_email_from.text()
            email_password = self.input_email_password.text()
            email_to = self.input_email_to.text()

            if not all([smtp_server, email_from, email_password, email_to]):
                QMessageBox.warning(self, "Chyba", "Vyplňte všechny údaje")
                return

            # Vytvoření zprávy
            msg = MIMEMultipart()
            msg['From'] = email_from
            msg['To'] = email_to
            msg['Subject'] = "Test - Systém upozornění skladu"

            body = "Toto je testovací email ze systému upozornění skladu.\n\nPokud tuto zprávu vidíte, email notifikace funguje správně."
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # Odeslání
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_from, email_password)
            server.send_message(msg)
            server.quit()

            QMessageBox.information(self, "Úspěch", "Testovací email byl odeslán!")

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Chyba při odesílání emailu:\n{str(e)}")


# ========================================
# ALERT CHECKER - pro kontrolu při startu
# ========================================

class StockAlertChecker:
    """Třída pro kontrolu skladových upozornění"""

    @staticmethod
    def check_and_notify(parent_window=None):
        """Kontrola a notifikace o položkách pod minimem"""
        try:
            # Počet kritických položek
            critical = db.execute_query("""
                SELECT COUNT(*) FROM warehouse WHERE quantity < min_quantity
            """)

            critical_count = critical[0][0] if critical else 0

            if critical_count > 0:
                # Zobrazení notifikace
                if parent_window:
                    msg = QMessageBox(parent_window)
                    msg.setIcon(QMessageBox.Icon.Warning)
                    msg.setWindowTitle("⚠️ Upozornění skladu")
                    msg.setText(f"<b>Máte {critical_count} položek pod minimálním stavem!</b>")
                    msg.setInformativeText("Doporučujeme zkontrolovat sklad a objednat chybějící položky.")

                    btn_show = msg.addButton("Zobrazit", QMessageBox.ButtonRole.AcceptRole)
                    btn_later = msg.addButton("Později", QMessageBox.ButtonRole.RejectRole)

                    msg.exec()

                    if msg.clickedButton() == btn_show:
                        # Otevření okna upozornění
                        alert_window = WarehouseStockAlertWindow(parent_window)
                        alert_window.show()

            return critical_count

        except Exception as e:
            print(f"Chyba při kontrole upozornění: {e}")
            return 0

    @staticmethod
    def get_alert_badge_count():
        """Získání počtu upozornění pro badge"""
        try:
            critical = db.execute_query("""
                SELECT COUNT(*) FROM warehouse WHERE quantity < min_quantity
            """)
            return critical[0][0] if critical else 0
        except:
            return 0
