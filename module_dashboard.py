# -*- coding: utf-8 -*-
"""
Modul Dashboard - Úvodní stránka s přehledem + náhled dnešních termínů
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
    QPushButton, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from datetime import datetime
import config
from database_manager import db


def _table_columns(table: str) -> set:
    try:
        cols = db.fetch_all(f"PRAGMA table_info({table})")
        return {c["name"] for c in cols} if cols else set()
    except Exception:
        return set()


def _customer_label_sql(alias: str = "c") -> tuple[str, str, str]:
    """
    Vrátí (label_sql, email_sql, phone_sql) podle dostupných sloupců customers.
    """
    cols = _table_columns("customers")

    # jméno
    if "full_name" in cols:
        label = f"{alias}.full_name"
    elif "name" in cols:
        label = f"{alias}.name"
    elif "first_name" in cols or "last_name" in cols:
        fn = f"COALESCE({alias}.first_name,'')" if "first_name" in cols else "''"
        ln = f"COALESCE({alias}.last_name,'')"  if "last_name"  in cols else "''"
        label = f"TRIM({fn} || ' ' || {ln})"
    else:
        label = "''"

    # email
    email = f"{alias}.email" if "email" in cols else "''"
    # telefon
    phone = f"{alias}.phone" if "phone" in cols else ("{}.phone_number".format(alias) if "phone_number" in cols else "''")

    return label, email, phone


def _vehicle_fields_sql(alias: str = "v") -> tuple[str, str, str, str]:
    """
    Vrátí (brand_sql, model_sql, spz_sql, vin_sql) podle dostupných sloupců vehicles.
    """
    cols = _table_columns("vehicles")
    brand = f"COALESCE({alias}.brand,'')" if "brand" in cols else "''"
    model = f"COALESCE({alias}.model,'')" if "model" in cols else "''"
    spz   = f"COALESCE({alias}.license_plate,'')" if "license_plate" in cols else "''"
    vin   = f"COALESCE({alias}.vin,'')" if "vin" in cols else "''"
    return brand, model, spz, vin


class DashboardModule(QWidget):
    """Úvodní modul s přehledem důležitých informací + dnešní termíny"""

    def __init__(self):
        super().__init__()
        self.today_list = None
        self.init_ui()

    def init_ui(self):
        """Inicializace uživatelského rozhraní"""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Uvítací text
        welcome_label = QLabel(f"Vítejte v systému {config.APP_NAME}")
        welcome_font = QFont()
        welcome_font.setPointSize(16)
        welcome_font.setBold(True)
        welcome_label.setFont(welcome_font)
        layout.addWidget(welcome_label)

        # Datum (lokálně)
        try:
            date_label = QLabel(datetime.now().strftime("%d.%m.%Y"))
        except Exception:
            date_label = QLabel("Dnes")
        date_font = QFont()
        date_font.setPointSize(11)
        date_label.setFont(date_font)
        date_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(date_label)

        # Statistické karty
        stats_layout = QGridLayout()
        stats_layout.setSpacing(15)

        self.create_stat_card(stats_layout, 0, 0, "Aktivní zakázky", "0", config.COLOR_PRIMARY)
        self.create_stat_card(stats_layout, 0, 1, "Čeká na součástky", "0", config.COLOR_WARNING)
        self.create_stat_card(stats_layout, 0, 2, "Hotové dnes", "0", config.COLOR_SUCCESS)
        self.create_stat_card(stats_layout, 1, 0, "Zákazníci celkem", "0", config.COLOR_SECONDARY)
        self.create_stat_card(stats_layout, 1, 1, "Vozidla v servisu", "0", config.COLOR_DANGER)
        self.create_stat_card(stats_layout, 1, 2, "Položky na skladě", "0", "#9b59b6")

        layout.addLayout(stats_layout)

        # Dnešní události (servisní termíny z kalendáře)
        today_frame = self._create_today_events_section()
        layout.addWidget(today_frame)

        # Rychlé akce
        actions_frame = self.create_quick_actions()
        layout.addWidget(actions_frame)

        # Posuvník dolů
        layout.addStretch()

        # Načtení dat
        self.refresh()

    def create_stat_card(self, layout, row, col, title, value, color):
        """Vytvoření statistické karty"""

        card = QFrame()
        card.setObjectName("statCard")
        card.setStyleSheet(f"""
            #statCard {{
                background-color: white;
                border-radius: 8px;
                border-left: 4px solid {color};
                padding: 15px;
            }}
        """)

        card_layout = QVBoxLayout(card)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold;")

        value_label = QLabel(value)
        value_label.setObjectName(f"stat_{title.replace(' ', '_')}")
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet(f"color: {color};")

        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        card_layout.addStretch()

        layout.addWidget(card, row, col)

    def _create_today_events_section(self) -> QFrame:
        """Panel s dnešními termíny z kalendáře (calendar_events)."""

        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
            }
            QListWidget {
                border: none;
                padding: 6px;
            }
        """)
        wrap = QVBoxLayout(frame)

        header_row = QHBoxLayout()
        header = QLabel("📅  Dnešní termíny v servisu")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)

        header_row.addWidget(header)
        header_row.addStretch()
        wrap.addLayout(header_row)

        self.today_list = QListWidget()
        wrap.addWidget(self.today_list)

        return frame

    def create_quick_actions(self):
        """Vytvoření panelu s rychlými akcemi"""

        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(frame)

        header = QLabel("⚡  Rychlé akce")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)

        # Tlačítka rychlých akcí
        actions_layout = QHBoxLayout()

        btn_new_order = QPushButton("📋 Nová zakázka")
        btn_new_order.setFixedHeight(40)
        btn_new_order.clicked.connect(lambda: self.quick_action("orders"))

        btn_new_customer = QPushButton("👤 Nový zákazník")
        btn_new_customer.setFixedHeight(40)
        btn_new_customer.clicked.connect(lambda: self.quick_action("customers"))

        btn_warehouse = QPushButton("📦 Sklad")
        btn_warehouse.setFixedHeight(40)
        btn_warehouse.clicked.connect(lambda: self.quick_action("warehouse"))

        btn_new_vehicle = QPushButton("🏍️ Nová motorka")
        btn_new_vehicle.setFixedHeight(40)
        btn_new_vehicle.clicked.connect(self.quick_new_vehicle)

        actions_layout.addWidget(btn_new_order)
        actions_layout.addWidget(btn_new_customer)
        actions_layout.addWidget(btn_warehouse)
        actions_layout.addWidget(btn_new_vehicle)

        layout.addLayout(actions_layout)

        return frame

    def quick_action(self, module_id):
        """Rychlá akce - přepnutí na modul"""
        main_window = self.window()
        if hasattr(main_window, 'switch_module'):
            main_window.switch_module(module_id)

    def quick_new_vehicle(self):
        """
        Přepne na modul Motorky a pokusí se otevřít dialog pro vytvoření nové motorky.
        Pokud VehiclesModule neumí new_vehicle()/add_vehicle(), aspoň tě přepne do modulu.
        """
        main_window = self.window()
        if hasattr(main_window, 'switch_module'):
            main_window.switch_module("vehicles")
        # pokus o vyvolání akce v modulu
        try:
            vehicles_module = getattr(main_window, "modules", {}).get("vehicles")
            if vehicles_module:
                if hasattr(vehicles_module, "new_vehicle"):
                    vehicles_module.new_vehicle()
                elif hasattr(vehicles_module, "add_vehicle"):
                    vehicles_module.add_vehicle()
        except Exception:
            pass  # nevadí, modul to neumí – jsi alespoň na správné obrazovce

    # ------------------------- DATA -------------------------

    def refresh(self):
        """Obnovení dat na dashboardu"""
        self._load_stats()
        self._load_today_appointments()

    def _load_stats(self):
        try:
            # Aktivní zakázky
            active_orders = db.fetch_one(
                "SELECT COUNT(*) as count FROM orders WHERE status NOT IN ('dokončeno','archiv')"
            )
            if active_orders:
                self.update_stat_value("Aktivní_zakázky", str(active_orders['count']))

            # Zakázky čekající na součástky
            waiting_orders = db.fetch_one(
                "SELECT COUNT(*) as count FROM orders WHERE status = 'čeká na součástky'"
            )
            if waiting_orders:
                self.update_stat_value("Čeká_na_součástky", str(waiting_orders['count']))

            # Hotové dnes
            completed_today = db.fetch_one(
                "SELECT COUNT(*) as count FROM orders WHERE DATE(completed_date) = DATE('now')"
            )
            if completed_today:
                self.update_stat_value("Hotové_dnes", str(completed_today['count']))

            # Celkový počet zákazníků
            customers = db.fetch_one("SELECT COUNT(*) as count FROM customers")
            if customers:
                self.update_stat_value("Zákazníci_celkem", str(customers['count']))

            # Vozidla v servisu (z nedokončených zakázek)
            vehicles = db.fetch_one(
                """SELECT COUNT(DISTINCT vehicle_id) as count FROM orders
                   WHERE status NOT IN ('dokončeno','archiv')"""
            )
            if vehicles:
                self.update_stat_value("Vozidla_v_servisu", str(vehicles['count']))

            # Položky na skladě
            warehouse = db.fetch_one("SELECT COUNT(*) as count FROM warehouse WHERE quantity > 0")
            if warehouse:
                self.update_stat_value("Položky_na_skladě", str(warehouse['count']))

        except Exception as e:
            print(f"Chyba při načítání statistik: {e}")

    def _load_today_appointments(self):
        """Načte dnešní termíny z calendar_events (pokud tabulka existuje)."""
        if self.today_list is None:
            return

        self.today_list.clear()

        # Ověřit existenci tabulky calendar_events
        try:
            exist = db.fetch_one("SELECT name FROM sqlite_master WHERE type='table' AND name='calendar_events'")
            if not exist:
                self.today_list.addItem(QListWidgetItem("Žádné termíny (kalendář není vytvořen)"))
                return
        except Exception:
            self.today_list.addItem(QListWidgetItem("Žádné termíny (chyba při zjišťování DB)"))
            return

        cust_label_sql, cust_email_sql, _ = _customer_label_sql("c")
        v_brand, v_model, v_spz, _ = _vehicle_fields_sql("v")
        today = datetime.now().strftime("%Y-%m-%d")

        try:
            # Dotaz na calendar_events - nová struktura
            rows = db.fetch_all(f"""
                SELECT
                    e.id,
                    e.title,
                    e.start_datetime,
                    e.end_datetime,
                    e.event_type,
                    e.status,
                    e.notes,
                    e.vehicle_id,
                    e.customer_id,
                    e.mechanic_id,
                    {cust_label_sql} AS customer_label,
                    {cust_email_sql} AS customer_email,
                    {v_brand} AS v_brand,
                    {v_model} AS v_model,
                    {v_spz} AS v_spz,
                    u.full_name AS mechanic_name
                FROM calendar_events e
                LEFT JOIN customers c ON c.id = e.customer_id
                LEFT JOIN vehicles v ON v.id = e.vehicle_id
                LEFT JOIN users u ON u.id = e.mechanic_id
                WHERE DATE(e.start_datetime) = ?
                ORDER BY e.start_datetime
            """, (today,))
        except Exception as e:
            self.today_list.addItem(QListWidgetItem(f"Chyba při načítání dnešních termínů: {e}"))
            return

        if not rows:
            self.today_list.addItem(QListWidgetItem("Dnes nemáte žádné termíny."))
            return

        for r in rows:
            # Čas události
            start_dt = r["start_datetime"] or ""
            if " " in start_dt:
                time_part = start_dt.split(" ")[1][:5]  # HH:MM
            else:
                time_part = "00:00"

            # SPZ vozidla
            spz = (r["v_spz"] or "").strip()

            # Zákazník
            cust = (r["customer_label"] or "").strip()
            if not cust:
                cust = "nepřiřazený zákazník"

            # Mechanik
            mechanic = (r["mechanic_name"] or "").strip()
            if not mechanic:
                mechanic = "nepřiřazen"

            # Typ události
            event_type = r["event_type"] or "service"
            type_icon = {
                "service": "🔧",
                "meeting": "📞",
                "delivery": "📦",
                "pickup": "🚗",
                "reminder": "⏰",
                "other": "📅"
            }.get(event_type, "📅")

            # Sestavení textu
            if spz:
                text = f"{time_part} {type_icon} SPZ {spz} — {cust} ({mechanic})"
            else:
                text = f"{time_part} {type_icon} {r['title'] or 'Událost'} — {cust} ({mechanic})"

            item = QListWidgetItem(text)

            # Barevné odlišení podle stavu
            status = r["status"] or "scheduled"
            if status == "completed":
                item.setForeground(Qt.GlobalColor.darkGreen)
            elif status == "cancelled":
                item.setForeground(Qt.GlobalColor.darkRed)
            elif status == "in_progress":
                item.setForeground(Qt.GlobalColor.darkBlue)

            self.today_list.addItem(item)

    # ------------------------- UI helper -------------------------

    def update_stat_value(self, stat_name, value):
        """Aktualizace hodnoty statistiky"""
        label = self.findChild(QLabel, f"stat_{stat_name}")
        if label:
            label.setText(value)
