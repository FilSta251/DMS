# -*- coding: utf-8 -*-
"""
Konfigurace aplikace Motoservis DMS
"""

from pathlib import Path

# Základní informace o aplikaci
APP_NAME = "Motoservis DMS"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Filip"

# Cesty
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = DATA_DIR / "database"
BACKUP_DIR = DATA_DIR / "backups"
EXPORTS_DIR = DATA_DIR / "exports"

# Vytvoření složek pokud neexistují
for directory in (DATA_DIR, DB_DIR, BACKUP_DIR, EXPORTS_DIR):
    directory.mkdir(parents=True, exist_ok=True)

# Databáze
DATABASE_PATH = DB_DIR / "motoservis.db"

# Vzhled aplikace
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 700

# Barvy
COLOR_PRIMARY = "#2c3e50"
COLOR_SECONDARY = "#3498db"
COLOR_SUCCESS = "#27ae60"
COLOR_WARNING = "#f39c12"
COLOR_DANGER = "#e74c3c"
COLOR_LIGHT = "#ecf0f1"
COLOR_DARK = "#2c3e50"

# === BARVY PRO STAVY SKLADU ===
STOCK_OK = "#27ae60"        # Zelená - nad minimem
STOCK_WARNING = "#f39c12"   # Oranžová - blíží se minimu (< 1.5x minimum)
STOCK_CRITICAL = "#e74c3c"  # Červená - pod minimem
STOCK_ZERO = "#95a5a6"      # Šedá - nulový stav

# Moduly aplikace (pořadí = pořadí v levém menu)
MODULES = [
    {"id": "dashboard",      "name": "Úvodní stránka", "icon": "🏠"},
    {"id": "vehicles",       "name": "Motorky",        "icon": "🏍️"},
    {"id": "customers",      "name": "Zákazníci",      "icon": "👥"},
    {"id": "orders",         "name": "Zakázky",        "icon": "📋"},
    {"id": "warehouse",      "name": "Sklad",          "icon": "📦"},
    {"id": "administration", "name": "Administrativa", "icon": "💼"},
    {"id": "codebooks",      "name": "Číselníky",      "icon": "📚"},
    {"id": "rental",         "name": "Půjčovna",       "icon": "🔑"},
    {"id": "calendar",       "name": "Kalendář",       "icon": "📅"},  # NOVĚ: kalendář
    {"id": "settings",       "name": "Nastavení",      "icon": "⚙️"},
    {"id": "management",     "name": "Management",     "icon": "📊"},
    {"id": "users",          "name": "Uživatelé",      "icon": "👤"},
]

# Zálohy
AUTO_BACKUP_ENABLED = True
BACKUP_INTERVAL_DAYS = 1
MAX_BACKUPS = 30  # Maximální počet záloh k uchování

# Zakázky - typy
ORDER_TYPES = [
    "Zakázka",
    "Volný prodej",
    "Interní zakázka",
    "Reklamace",
    "Nabídka"
]

# Zakázky - stavy (POUZE 3!)
ORDER_STATUSES = [
    "V přípravě",
    "Otevřená",
    "Rozpracovaná"
]

# Zakázky - barvy stavů
ORDER_STATUS_COLORS = {
    "V přípravě": "#95a5a6",
    "Otevřená": "#3498db",
    "Rozpracovaná": "#f39c12"
}
