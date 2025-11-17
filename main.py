# -*- coding: utf-8 -*-
"""
Motoservis DMS - Hlavní spouštěcí soubor (s login dialogem a právy)
"""

import sys

# Přidej cestu, kde máš uložené moduly (ponech i do budoucna)
sys.path.append(r"C:\Users\Phili\Desktop\moto DMS")

from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import config
from database_manager import db
from main_window import MainWindow
from module_dashboard import DashboardModule
from modules.customers import CustomersModule
from modules.vehicles import VehiclesModule
from modules.users.module_users import UsersModule
from modules.calendar.module_calendar import CalendarModule
from login_dialog import LoginDialog
from utils.utils_auth import get_current_username
from modules.orders import OrdersModule
from modules.warehouse import WarehouseModule
from modules.management import ManagementModule  # ← PŘIDEJ TENTO ŘÁDEK
from modules.administration import AdministrationModule
from modules.codebooks import CodebooksModule
from modules.settings import SettingsModule

def initialize_database():
    """Inicializace databáze"""
    try:
        print("Připojování k databázi...")
        if not db.connect():
            raise Exception("Nepodařilo se připojit k databázi")

        print("Vytváření tabulek...")
        db.create_tables()

        print("Naplnění výchozími daty...")
        db.initialize_default_data()

        print("✅ Databáze inicializována")
        return True

    except Exception as e:
        print(f"❌ Chyba při inicializaci databáze: {e}")
        return False


def create_splash_screen():
    """Vytvoření úvodní obrazovky"""
    splash = QSplashScreen()
    splash.setStyleSheet(f"""
        QSplashScreen {{
            background-color: {config.COLOR_PRIMARY};
            color: white;
        }}
    """)
    font = QFont()
    font.setPointSize(16)
    font.setBold(True)
    splash.setFont(font)
    splash.showMessage(
        f"{config.APP_NAME}\nSpouštění...",
        Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom,
        Qt.GlobalColor.white
    )
    return splash


def check_warehouse_alerts(window):
    """Kontrola skladových upozornění"""
    try:
        from modules.warehouse.warehouse_stock_alert import StockAlertChecker
        StockAlertChecker.check_and_notify(window)
    except Exception as e:
        print(f"Chyba při kontrole upozornění: {e}")


def main():
    """Hlavní funkce aplikace"""
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)
    app.setFont(QFont("Segoe UI", 10))

    splash = create_splash_screen()
    splash.show()
    app.processEvents()

    # Inicializace DB
    splash.showMessage(
        f"{config.APP_NAME}\nInicializace databáze...",
        Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom,
        Qt.GlobalColor.white
    )
    app.processEvents()

    if not initialize_database():
        QMessageBox.critical(
            None,
            "Chyba databáze",
            "Nepodařilo se inicializovat databázi.\n"
            "Aplikace bude ukončena."
        )
        sys.exit(1)

    # Přihlášení uživatele (před vytvořením hlavního okna)
    splash.showMessage(
        f"{config.APP_NAME}\nPřihlášení...",
        Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom,
        Qt.GlobalColor.white
    )
    app.processEvents()

    login = LoginDialog()
    if login.exec() != login.DialogCode.Accepted:
        sys.exit(0)

    # Hlavní okno a moduly
    splash.showMessage(
        f"{config.APP_NAME}\nNačítání modulů...",
        Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom,
        Qt.GlobalColor.white
    )
    app.processEvents()

    window = MainWindow()

    # Přidání modulů
    window.add_module("dashboard", DashboardModule())
    window.add_module("customers", CustomersModule())
    window.add_module("vehicles", VehiclesModule())
    window.add_module("orders", OrdersModule())
    window.add_module("warehouse", WarehouseModule())
    window.add_module("calendar", CalendarModule())
    window.add_module("users", UsersModule())
    window.add_module("management", ManagementModule())  # ← PŘIDEJ TENTO ŘÁDEK
    window.add_module("administration", AdministrationModule())
    window.add_module("codebooks", CodebooksModule())
    window.add_module("settings", SettingsModule())

    # Výchozí modul
    window.switch_module("dashboard")

    # Zobrazení
    window.show()
    splash.finish(window)

    # ========================================
    # KONTROLA SKLADOVÝCH UPOZORNĚNÍ PŘI STARTU
    # ========================================
    # Spustí se 2 sekundy po zobrazení hlavního okna
    QTimer.singleShot(2000, lambda: check_warehouse_alerts(window))

    # Info do konzole
    print(f"Přihlášený uživatel: {get_current_username() or 'neznámý'}")
    print("✅ Aplikace spuštěna")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
