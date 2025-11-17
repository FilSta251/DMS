# customer_detail.py
# -*- coding: utf-8 -*-
"""
Detailní okno zákazníka
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QFrame, QScrollArea, QGridLayout, QMessageBox,
    QSplitter, QGroupBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor, QDesktopServices
from PyQt6.QtCore import QUrl
import config
from database_manager import db
from datetime import datetime
from .customer_vehicles import CustomerVehiclesWidget
from .customer_orders import CustomerOrdersWidget
from .customer_financial import CustomerFinancialWidget
from .customer_communication import CustomerCommunicationWidget
from .customer_documents import CustomerDocumentsWidget


class CustomerDetailWindow(QWidget):
    """Detailní zobrazení zákazníka"""

    customer_updated = pyqtSignal()
    customer_deleted = pyqtSignal()

    def __init__(self, customer_id, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.customer_data = None
        self.init_ui()
        self.load_customer_data()

    def init_ui(self):
        """Inicializace UI"""
        self.setWindowTitle("Detail zákazníka")
        self.setMinimumSize(1200, 800)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Horní lišta
        self.create_action_bar(layout)

        # Hlavní obsah
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Levý panel - záložky
        self.create_tabs_panel(splitter)

        # Pravý panel - rychlé akce
        self.create_side_panel(splitter)

        splitter.setSizes([900, 300])
        layout.addWidget(splitter)

        self.set_styles()

    def create_action_bar(self, parent_layout):
        """Vytvoření horní akční lišty"""
        action_bar = QFrame()
        action_bar.setObjectName("actionBar")
        action_bar.setFixedHeight(70)
        bar_layout = QHBoxLayout(action_bar)
        bar_layout.setContentsMargins(20, 10, 20, 10)

        # Jméno zákazníka
        self.lbl_customer_name = QLabel("Načítání...")
        name_font = QFont()
        name_font.setPointSize(22)
        name_font.setBold(True)
        self.lbl_customer_name.setFont(name_font)
        bar_layout.addWidget(self.lbl_customer_name)

        # Badge skupina
        self.lbl_group_badge = QLabel("Standardní")
        self.lbl_group_badge.setObjectName("groupBadge")
        bar_layout.addWidget(self.lbl_group_badge)

        # Badge VIP
        self.lbl_vip_badge = QLabel("⭐ VIP")
        self.lbl_vip_badge.setObjectName("vipBadge")
        self.lbl_vip_badge.hide()
        bar_layout.addWidget(self.lbl_vip_badge)

        bar_layout.addStretch()

        # Tlačítka
        btn_edit = QPushButton("✏️ Upravit")
        btn_edit.setObjectName("btnPrimary")
        btn_edit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_edit.clicked.connect(self.edit_customer)
        bar_layout.addWidget(btn_edit)

        btn_new_order = QPushButton("➕ Nová zakázka")
        btn_new_order.setObjectName("btnSuccess")
        btn_new_order.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_new_order.clicked.connect(self.create_new_order)
        bar_layout.addWidget(btn_new_order)

        btn_email = QPushButton("📧 Odeslat email")
        btn_email.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_email.clicked.connect(self.send_email)
        bar_layout.addWidget(btn_email)

        btn_print = QPushButton("🖨️ Tisk karty")
        btn_print.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_print.clicked.connect(self.print_card)
        bar_layout.addWidget(btn_print)

        btn_delete = QPushButton("🗑️ Smazat")
        btn_delete.setObjectName("btnDanger")
        btn_delete.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_delete.clicked.connect(self.delete_customer)
        bar_layout.addWidget(btn_delete)

        parent_layout.addWidget(action_bar)

    def create_tabs_panel(self, parent_splitter):
        """Vytvoření levého panelu se záložkami"""
        self.tabs = QTabWidget()
        self.tabs.setObjectName("detailTabs")

        # Základní informace
        self.tabs.addTab(self.create_info_tab(), "👤 Základní informace")

        # Vozidla
        self.vehicles_widget = CustomerVehiclesWidget(self.customer_id)
        self.tabs.addTab(self.vehicles_widget, "🏍️ Vozidla")

        # Zakázky
        self.orders_widget = CustomerOrdersWidget(self.customer_id)
        self.tabs.addTab(self.orders_widget, "📋 Zakázky")

        # Finance
        self.financial_widget = CustomerFinancialWidget(self.customer_id)
        self.tabs.addTab(self.financial_widget, "💰 Finance")

        # Komunikace
        self.communication_widget = CustomerCommunicationWidget(self.customer_id)
        self.tabs.addTab(self.communication_widget, "📧 Komunikace")

        # Dokumenty
        self.documents_widget = CustomerDocumentsWidget(self.customer_id)
        self.tabs.addTab(self.documents_widget, "📁 Dokumenty")

        # Poznámky
        self.tabs.addTab(self.create_notes_tab(), "📝 Poznámky")

        parent_splitter.addWidget(self.tabs)

    def create_info_tab(self):
        """Záložka základních informací"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Osobní/Firemní údaje
        personal_group = QGroupBox("Osobní/Firemní údaje")
        personal_layout = QGridLayout(personal_group)
        personal_layout.setSpacing(10)

        self.info_labels = {}

        row = 0
        for label, key in [
            ("Jméno:", "name"),
            ("IČO:", "ico"),
            ("DIČ:", "dic"),
            ("Kontaktní osoba:", "contact_person"),
            ("Datum narození:", "birth_date"),
            ("Zákaznická skupina:", "group")
        ]:
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: bold; color: #7f8c8d;")
            value = QLabel("-")
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.info_labels[key] = value
            personal_layout.addWidget(lbl, row, 0)
            personal_layout.addWidget(value, row, 1)
            row += 1

        layout.addWidget(personal_group)

        # Kontaktní údaje
        contact_group = QGroupBox("Kontaktní údaje")
        contact_layout = QGridLayout(contact_group)
        contact_layout.setSpacing(10)

        row = 0
        for label, key in [
            ("Telefon:", "phone"),
            ("Telefon 2:", "phone2"),
            ("Email:", "email"),
            ("Email 2:", "email2"),
            ("Web:", "web")
        ]:
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: bold; color: #7f8c8d;")
            value = QLabel("-")
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.info_labels[key] = value
            contact_layout.addWidget(lbl, row, 0)
            contact_layout.addWidget(value, row, 1)
            row += 1

        layout.addWidget(contact_group)

        # Adresa
        address_group = QGroupBox("Adresa")
        address_layout = QVBoxLayout(address_group)

        self.lbl_main_address = QLabel("-")
        self.lbl_main_address.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        address_layout.addWidget(QLabel("Hlavní adresa:"))
        address_layout.addWidget(self.lbl_main_address)

        self.lbl_billing_address = QLabel("-")
        self.lbl_billing_address.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        address_layout.addWidget(QLabel("Fakturační adresa:"))
        address_layout.addWidget(self.lbl_billing_address)

        btn_maps = QPushButton("🗺️ Zobrazit na mapě")
        btn_maps.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_maps.clicked.connect(self.open_maps)
        address_layout.addWidget(btn_maps)

        layout.addWidget(address_group)

        # Fakturační údaje
        billing_group = QGroupBox("Fakturační údaje")
        billing_layout = QGridLayout(billing_group)
        billing_layout.setSpacing(10)

        row = 0
        for label, key in [
            ("Číslo účtu:", "bank_account"),
            ("Banka:", "bank_name"),
            ("Splatnost faktur:", "payment_days"),
            ("Platební metoda:", "payment_method"),
            ("Kredit limit:", "credit_limit")
        ]:
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: bold; color: #7f8c8d;")
            value = QLabel("-")
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.info_labels[key] = value
            billing_layout.addWidget(lbl, row, 0)
            billing_layout.addWidget(value, row, 1)
            row += 1

        layout.addWidget(billing_group)

        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    def create_notes_tab(self):
        """Záložka poznámek"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Poznámky
        layout.addWidget(QLabel("Poznámky k zákazníkovi:"))
        self.te_notes = QTextEdit()
        self.te_notes.setPlaceholderText("Interní poznámky...")
        layout.addWidget(self.te_notes)

        # Speciální požadavky
        layout.addWidget(QLabel("Speciální požadavky:"))
        self.te_special = QTextEdit()
        self.te_special.setPlaceholderText("Speciální požadavky zákazníka...")
        self.te_special.setMaximumHeight(150)
        layout.addWidget(self.te_special)

        # Tlačítko uložit
        btn_save_notes = QPushButton("💾 Uložit poznámky")
        btn_save_notes.setObjectName("btnSuccess")
        btn_save_notes.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save_notes.clicked.connect(self.save_notes)
        layout.addWidget(btn_save_notes)

        return widget

    def create_side_panel(self, parent_splitter):
        """Vytvoření pravého panelu"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("sidePanel")
        scroll.setMinimumWidth(280)
        scroll.setMaximumWidth(350)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # Statistiky
        stats_group = QGroupBox("📊 Statistiky")
        stats_layout = QVBoxLayout(stats_group)

        self.stat_labels = {}
        for key, name in [
            ("vehicles", "Počet vozidel"),
            ("orders", "Celkem zakázek"),
            ("total_spent", "Celková útrata"),
            ("avg_order", "Průměrná zakázka"),
            ("last_contact", "Poslední kontakt"),
            ("customer_since", "Zákazníkem od")
        ]:
            row = QHBoxLayout()
            lbl_name = QLabel(name + ":")
            lbl_name.setStyleSheet("color: #7f8c8d;")
            lbl_value = QLabel("-")
            lbl_value.setStyleSheet("font-weight: bold;")
            lbl_value.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.stat_labels[key] = lbl_value
            row.addWidget(lbl_name)
            row.addWidget(lbl_value)
            stats_layout.addLayout(row)

        layout.addWidget(stats_group)

        # Upozornění
        alerts_group = QGroupBox("⚠️ Upozornění")
        self.alerts_layout = QVBoxLayout(alerts_group)
        self.lbl_no_alerts = QLabel("Žádná upozornění")
        self.lbl_no_alerts.setStyleSheet("color: #27ae60; font-style: italic;")
        self.alerts_layout.addWidget(self.lbl_no_alerts)
        layout.addWidget(alerts_group)

        # Rychlé akce
        actions_group = QGroupBox("⚡ Rychlé akce")
        actions_layout = QVBoxLayout(actions_group)

        btn_email = QPushButton("📧 Odeslat email")
        btn_email.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_email.clicked.connect(self.send_email)
        actions_layout.addWidget(btn_email)

        btn_call = QPushButton("📞 Zavolat")
        btn_call.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_call.clicked.connect(self.make_call)
        actions_layout.addWidget(btn_call)

        btn_order = QPushButton("📋 Nová zakázka")
        btn_order.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_order.clicked.connect(self.create_new_order)
        actions_layout.addWidget(btn_order)

        btn_vehicle = QPushButton("🏍️ Přidat vozidlo")
        btn_vehicle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_vehicle.clicked.connect(self.add_vehicle)
        actions_layout.addWidget(btn_vehicle)

        layout.addWidget(actions_group)

        layout.addStretch()
        scroll.setWidget(content)
        parent_splitter.addWidget(scroll)

    def load_customer_data(self):
        """Načtení dat zákazníka"""
        try:
            query = """
                SELECT
                    c.*,
                    (SELECT COUNT(*) FROM vehicles WHERE customer_id = c.id) as vehicle_count,
                    (SELECT COUNT(*) FROM orders WHERE customer_id = c.id) as order_count,
                    (SELECT COALESCE(SUM(total_price), 0) FROM orders WHERE customer_id = c.id) as total_spent,
                    (SELECT MAX(created_at) FROM orders WHERE customer_id = c.id) as last_order
                FROM customers c
                WHERE c.id = ?
            """

            result = db.fetch_one(query, (self.customer_id,))
            if result:
                self.customer_data = result
                self.update_ui()
            else:
                QMessageBox.warning(self, "Chyba", "Zákazník nebyl nalezen")
                self.close()

        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst zákazníka: {e}")

    def update_ui(self):
        """Aktualizace UI daty"""
        if not self.customer_data:
            return

        data = self.customer_data

        # Jméno
        if data[1] == "company":  # customer_type
            name = data[4] or ""  # company_name
            self.lbl_customer_name.setText(name)
        else:
            name = f"{data[2] or ''} {data[3] or ''}".strip()  # first_name, last_name
            self.lbl_customer_name.setText(name)

        # Badge skupina
        group = data[25] if len(data) > 25 else "Standardní"  # customer_group
        self.lbl_group_badge.setText(group)
        self.lbl_group_badge.setStyleSheet(f"""
            background-color: {self.get_group_color(group)};
            padding: 5px 15px;
            border-radius: 12px;
            font-weight: bold;
        """)

        # VIP badge
        is_vip = data[29] if len(data) > 29 else 0  # is_vip
        if is_vip:
            self.lbl_vip_badge.show()

        # Info labels
        self.info_labels["name"].setText(name)
        self.info_labels["ico"].setText(data[5] or "-")  # ico
        self.info_labels["dic"].setText(data[6] or "-")  # dic
        self.info_labels["contact_person"].setText(data[7] if len(data) > 7 else "-")
        self.info_labels["group"].setText(group)

        # Kontakty
        self.info_labels["phone"].setText(data[9] or "-")  # phone
        self.info_labels["phone2"].setText(data[10] or "-")  # phone2
        self.info_labels["email"].setText(data[11] or "-")  # email
        self.info_labels["email2"].setText(data[12] or "-")  # email2
        self.info_labels["web"].setText(data[13] or "-")  # web

        # Adresa
        street = data[14] or ""  # street
        city = data[15] or ""  # city
        zip_code = data[16] or ""  # zip
        country = data[18] or ""  # country
        self.lbl_main_address.setText(f"{street}\n{zip_code} {city}\n{country}")

        # Fakturační údaje
        self.info_labels["bank_account"].setText(data[38] if len(data) > 38 else "-")
        self.info_labels["bank_name"].setText(data[39] if len(data) > 39 else "-")
        self.info_labels["payment_days"].setText(f"{data[36] if len(data) > 36 else 14} dní")
        self.info_labels["payment_method"].setText(data[37] if len(data) > 37 else "-")
        self.info_labels["credit_limit"].setText(f"{data[40] if len(data) > 40 else 0:,.0f} Kč".replace(",", " "))

        # Statistiky
        vehicle_count = data[-4] if len(data) > 4 else 0
        order_count = data[-3] if len(data) > 3 else 0
        total_spent = data[-2] if len(data) > 2 else 0

        self.stat_labels["vehicles"].setText(str(vehicle_count))
        self.stat_labels["orders"].setText(str(order_count))
        self.stat_labels["total_spent"].setText(f"{total_spent:,.0f} Kč".replace(",", " "))

        if order_count > 0:
            avg = total_spent / order_count
            self.stat_labels["avg_order"].setText(f"{avg:,.0f} Kč".replace(",", " "))

        # Poznámky
        self.te_notes.setPlainText(data[30] if len(data) > 30 else "")
        self.te_special.setPlainText(data[31] if len(data) > 31 else "")

        # Upozornění
        self.check_alerts()

    def get_group_color(self, group):
        """Vrátí barvu pro skupinu"""
        colors = {
            "VIP": "#a8e6cf",
            "Firemní": "#87ceeb",
            "Pojišťovna": "#fff3cd",
            "Standardní": "#e0e0e0"
        }
        return colors.get(group, "#e0e0e0")

    def check_alerts(self):
        """Kontrola upozornění"""
        alerts = []

        # Kontrola neuhrazených faktur
        if self.customer_data and len(self.customer_data) > 42:
            if self.customer_data[42]:  # has_debt
                alerts.append(("danger", "⚠️ Neuhrazené faktury"))

        # Zobrazení upozornění
        if alerts:
            self.lbl_no_alerts.hide()
            for alert_type, text in alerts:
                lbl = QLabel(text)
                if alert_type == "danger":
                    lbl.setStyleSheet("color: #e74c3c; font-weight: bold;")
                elif alert_type == "warning":
                    lbl.setStyleSheet("color: #f39c12; font-weight: bold;")
                else:
                    lbl.setStyleSheet("color: #3498db;")
                self.alerts_layout.addWidget(lbl)

    def edit_customer(self):
        """Úprava zákazníka"""
        from .customer_form import CustomerFormDialog
        dialog = CustomerFormDialog(self, self.customer_id)
        if dialog.exec():
            self.load_customer_data()
            self.customer_updated.emit()

    def create_new_order(self):
        """Vytvoření nové zakázky"""
        QMessageBox.information(self, "Nová zakázka", f"Vytvoření zakázky pro zákazníka ID: {self.customer_id}")

    def send_email(self):
        """Odeslání emailu"""
        if self.customer_data and len(self.customer_data) > 11:
            email = self.customer_data[11]
            if email:
                QDesktopServices.openUrl(QUrl(f"mailto:{email}"))

    def make_call(self):
        """Zavolání zákazníkovi"""
        if self.customer_data and len(self.customer_data) > 9:
            phone = self.customer_data[9]
            if phone:
                QDesktopServices.openUrl(QUrl(f"tel:{phone}"))

    def print_card(self):
        """Tisk karty zákazníka"""
        QMessageBox.information(self, "Tisk", "Funkce tisku karty bude implementována")

    def delete_customer(self):
        """Smazání zákazníka"""
        reply = QMessageBox.question(
            self,
            "Smazat zákazníka",
            "Opravdu chcete smazat tohoto zákazníka?\nTato akce je nevratná.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                db.execute("UPDATE customers SET is_active = 0 WHERE id = ?", (self.customer_id,))
                self.customer_deleted.emit()
                self.close()
            except Exception as e:
                QMessageBox.critical(self, "Chyba", f"Nepodařilo se smazat zákazníka: {e}")

    def add_vehicle(self):
        """Přidání vozidla"""
        self.vehicles_widget.add_vehicle()

    def open_maps(self):
        """Otevření adresy na mapě"""
        if self.customer_data:
            address = f"{self.customer_data[14] or ''}, {self.customer_data[16] or ''} {self.customer_data[15] or ''}"
            url = f"https://www.google.com/maps/search/?api=1&query={address.replace(' ', '+')}"
            QDesktopServices.openUrl(QUrl(url))

    def save_notes(self):
        """Uložení poznámek"""
        try:
            notes = self.te_notes.toPlainText()
            special = self.te_special.toPlainText()
            db.execute(
                "UPDATE customers SET notes = ?, special_requirements = ? WHERE id = ?",
                (notes, special, self.customer_id)
            )
            QMessageBox.information(self, "Uloženo", "Poznámky byly uloženy")
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se uložit poznámky: {e}")

    def refresh(self):
        """Obnovení dat"""
        self.load_customer_data()
        self.vehicles_widget.load_vehicles()
        self.orders_widget.load_orders()
        self.financial_widget.load_data()

    def set_styles(self):
        """Nastavení stylů"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: #f5f5f5;
            }}
            #actionBar {{
                background-color: white;
                border-bottom: 2px solid #e0e0e0;
            }}
            #groupBadge {{
                padding: 5px 15px;
                border-radius: 12px;
                font-weight: bold;
            }}
            #vipBadge {{
                background-color: #ffd700;
                padding: 5px 15px;
                border-radius: 12px;
                font-weight: bold;
            }}
            #detailTabs {{
                background-color: white;
            }}
            #detailTabs::pane {{
                border: 1px solid #ddd;
                background-color: white;
            }}
            QTabBar::tab {{
                background-color: #e0e0e0;
                padding: 10px 20px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: white;
                font-weight: bold;
            }}
            #sidePanel {{
                background-color: white;
                border-left: 1px solid #e0e0e0;
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
            #btnDanger {{
                background-color: {config.COLOR_DANGER};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }}
            #btnDanger:hover {{
                background-color: #c0392b;
            }}
            QPushButton {{
                padding: 8px 12px;
                border-radius: 4px;
                border: 1px solid #ddd;
            }}
            QPushButton:hover {{
                background-color: #e0e0e0;
            }}
        """)
