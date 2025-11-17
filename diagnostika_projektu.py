# -*- coding: utf-8 -*-
"""
Motoservis DMS - KOMPLETNÍ DIAGNOSTIKA PROJEKTU
=================================================

Tento skript provede kompletní kontrolu:
1. Struktura projektu (soubory a složky)
2. Syntaxe všech Python souborů
3. Importy a závislosti
4. Databáze (tabulky, sloupce, FK, data)
5. Moduly (existence, třídy, metody)
6. Konzistence mezi moduly
7. Konfigurace
8. Bezpečnost (hesla, práva)

Použití: python diagnostika_projektu.py
"""

import sys
import os
import ast
import importlib
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Any
import traceback

# Nastavení cesty projektu
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))


class ProjectDiagnostics:
    """Kompletní diagnostika projektu Motoservis DMS"""
    
    def __init__(self):
        self.project_dir = PROJECT_DIR
        self.results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "errors": [],
            "warnings_list": [],
            "info": []
        }
        self.modules_found = {}
        self.python_files = []
        self.import_errors = []
        
    def log_pass(self, message: str):
        self.results["passed"] += 1
        print(f"✅ {message}")
    
    def log_fail(self, message: str, details: str = ""):
        self.results["failed"] += 1
        self.results["errors"].append(message)
        if details:
            print(f"❌ {message}\n   └─ {details}")
        else:
            print(f"❌ {message}")
    
    def log_warn(self, message: str):
        self.results["warnings"] += 1
        self.results["warnings_list"].append(message)
        print(f"⚠️  {message}")
    
    def log_info(self, message: str):
        self.results["info"].append(message)
        print(f"ℹ️  {message}")
    
    def print_header(self, title: str):
        print("\n" + "=" * 70)
        print(f" {title}")
        print("=" * 70)
    
    def print_subheader(self, title: str):
        print(f"\n--- {title} ---")
    
    # =========================================================================
    # TEST 1: STRUKTURA PROJEKTU
    # =========================================================================
    def test_project_structure(self):
        """Kontrola struktury projektu a souborů"""
        self.print_header("1. STRUKTURA PROJEKTU")
        
        # Povinné soubory v kořenu
        required_root_files = [
            "main.py",
            "config.py",
            "database_manager.py",
            "main_window.py",
            "module_dashboard.py",
            "login_dialog.py",
            "utils_auth.py",
            "utils_permissions.py",
        ]
        
        self.print_subheader("Kořenové soubory")
        for file in required_root_files:
            path = self.project_dir / file
            if path.exists():
                self.log_pass(f"{file}")
            else:
                self.log_fail(f"{file}", "Soubor neexistuje!")
        
        # Povinné složky modulů
        required_modules = [
            "modules/customers",
            "modules/vehicles",
            "modules/orders",
            "modules/warehouse",
            "modules/calendar",
            "modules/users",
            "modules/management",
            "modules/administration",
            "modules/codebooks",
            "modules/settings",
        ]
        
        self.print_subheader("Složky modulů")
        for module_path in required_modules:
            path = self.project_dir / module_path
            if path.exists() and path.is_dir():
                init_file = path / "__init__.py"
                if init_file.exists():
                    self.log_pass(f"{module_path}/ (+ __init__.py)")
                else:
                    self.log_warn(f"{module_path}/ (CHYBÍ __init__.py)")
            else:
                self.log_fail(f"{module_path}/", "Složka neexistuje!")
        
        # Datové složky
        self.print_subheader("Datové složky")
        data_dirs = ["data", "data/database", "data/backups", "data/exports"]
        for dir_path in data_dirs:
            path = self.project_dir / dir_path
            if path.exists():
                self.log_pass(f"{dir_path}/")
            else:
                self.log_info(f"{dir_path}/ bude vytvořena při spuštění")
        
        # Spočítat všechny Python soubory
        self.python_files = list(self.project_dir.rglob("*.py"))
        # Filtrovat __pycache__
        self.python_files = [f for f in self.python_files if "__pycache__" not in str(f)]
        self.log_info(f"Celkem nalezeno {len(self.python_files)} Python souborů")
    
    # =========================================================================
    # TEST 2: SYNTAXE PYTHON SOUBORŮ
    # =========================================================================
    def test_python_syntax(self):
        """Kontrola syntaxe všech Python souborů"""
        self.print_header("2. SYNTAXE PYTHON SOUBORŮ")
        
        syntax_errors = []
        
        for py_file in self.python_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    source = f.read()
                compile(source, py_file, "exec")
            except SyntaxError as e:
                relative_path = py_file.relative_to(self.project_dir)
                syntax_errors.append((relative_path, e))
                self.log_fail(f"{relative_path}", f"Řádek {e.lineno}: {e.msg}")
            except Exception as e:
                relative_path = py_file.relative_to(self.project_dir)
                self.log_warn(f"{relative_path}: {type(e).__name__}")
        
        if not syntax_errors:
            self.log_pass(f"Všech {len(self.python_files)} souborů má správnou syntaxi")
        else:
            self.log_info(f"{len(syntax_errors)} souborů má syntaktické chyby")
    
    # =========================================================================
    # TEST 3: KONTROLA IMPORTŮ
    # =========================================================================
    def test_imports(self):
        """Kontrola že všechny importy jsou platné"""
        self.print_header("3. KONTROLA IMPORTŮ")
        
        # Nejprve zkontroluj základní importy
        self.print_subheader("Základní knihovny")
        
        basic_imports = [
            ("PyQt6.QtWidgets", "PyQt6"),
            ("PyQt6.QtCore", "PyQt6"),
            ("PyQt6.QtGui", "PyQt6"),
            ("sqlite3", "sqlite3"),
            ("bcrypt", "bcrypt"),
        ]
        
        for module_name, display_name in basic_imports:
            try:
                __import__(module_name)
                self.log_pass(f"{display_name}")
            except ImportError as e:
                self.log_fail(f"{display_name}", f"pip install {display_name.lower()}")
        
        # Kontrola hlavních souborů projektu
        self.print_subheader("Hlavní soubory projektu")
        
        project_imports = [
            "config",
            "database_manager",
            "utils_auth",
            "utils_permissions",
            "login_dialog",
            "main_window",
            "module_dashboard",
        ]
        
        for module_name in project_imports:
            try:
                importlib.import_module(module_name)
                self.log_pass(f"{module_name}")
            except Exception as e:
                self.log_fail(f"{module_name}", str(e))
                self.import_errors.append((module_name, e))
        
        # Kontrola modulů
        self.print_subheader("Moduly aplikace")
        
        module_imports = [
            ("modules.customers", "CustomersModule"),
            ("modules.vehicles", "VehiclesModule"),
            ("modules.orders", "OrdersModule"),
            ("modules.warehouse", "WarehouseModule"),
            ("modules.calendar.module_calendar", "CalendarModule"),
            ("modules.users.module_users", "UsersModule"),
            ("modules.management", "ManagementModule"),
            ("modules.administration", "AdministrationModule"),
            ("modules.codebooks", "CodebooksModule"),
            ("modules.settings", "SettingsModule"),
        ]
        
        for module_path, class_name in module_imports:
            try:
                mod = importlib.import_module(module_path)
                if hasattr(mod, class_name):
                    self.log_pass(f"{module_path}.{class_name}")
                    self.modules_found[class_name] = mod
                else:
                    self.log_fail(f"{module_path}.{class_name}", f"Třída {class_name} neexistuje v modulu")
            except Exception as e:
                self.log_fail(f"{module_path}", str(e))
                self.import_errors.append((module_path, e))
    
    # =========================================================================
    # TEST 4: DATABÁZE
    # =========================================================================
    def test_database(self):
        """Kompletní test databáze"""
        self.print_header("4. DATABÁZE")
        
        try:
            from database_manager import db
            import config
        except ImportError as e:
            self.log_fail("Import databáze", str(e))
            return
        
        # Připojení
        self.print_subheader("Připojení")
        try:
            if db.connect():
                self.log_pass(f"Připojeno k {config.DATABASE_PATH}")
            else:
                self.log_fail("Připojení k databázi", "db.connect() vrátil False")
                return
        except Exception as e:
            self.log_fail("Připojení k databázi", str(e))
            return
        
        # Vytvoření tabulek
        self.print_subheader("Vytvoření schématu")
        try:
            db.create_tables()
            self.log_pass("create_tables() proběhlo bez chyby")
        except Exception as e:
            self.log_fail("create_tables()", str(e))
            traceback.print_exc()
        
        # Inicializace dat
        try:
            db.initialize_default_data()
            self.log_pass("initialize_default_data() proběhlo bez chyby")
        except Exception as e:
            self.log_fail("initialize_default_data()", str(e))
        
        # Kontrola tabulek
        self.print_subheader("Tabulky v databázi")
        
        expected_tables = {
            # Core
            "customers": ["id", "first_name", "last_name", "phone", "email"],
            "vehicles": ["id", "customer_id", "brand", "model", "license_plate"],
            "users": ["id", "username", "password", "full_name", "role"],
            "orders": ["id", "order_number", "customer_id", "vehicle_id", "status"],
            # Users modul
            "roles": ["id", "name", "description"],
            "permissions": ["id", "module_id", "action"],
            "role_permissions": ["id", "role_id", "permission_id"],
            "user_permissions": ["id", "user_id", "permission_id"],
            "user_logins": ["id", "user_id", "login_time", "success"],
            "audit_log": ["id", "user_id", "event_type"],
            # Sklad
            "warehouse": ["id", "code", "name", "quantity", "price_purchase"],
            "warehouse_categories": ["id", "name"],
            "warehouse_suppliers": ["id", "name"],
            "warehouse_movements": ["id", "item_id", "qty_change"],
            "order_items": ["id", "order_id", "item_name", "quantity"],
            # Kalendář
            "calendar_events": ["id", "title", "start_datetime", "end_datetime"],
            "calendar_reminders": ["id", "event_id", "remind_at"],
            "calendar_recurring_rules": ["id", "frequency"],
            "calendar_availability": ["id", "day_of_week", "start_time"],
            "calendar_holidays": ["id", "holiday_date", "name"],
            "calendar_settings": ["id", "setting_key", "setting_value"],
            # Administrativa
            "invoices": ["id", "invoice_number", "invoice_type", "status"],
            "invoice_items": ["id", "invoice_id", "item_name"],
            "payments": ["id", "invoice_id", "amount"],
            "documents": ["id", "document_type", "file_path"],
            "admin_settings": ["id", "setting_key", "setting_value"],
            # Číselníky
            "codebook_brands": ["id", "name"],
            "codebook_vehicle_types": ["id", "code", "name"],
            "codebook_repair_types": ["id", "name"],
            # Nastavení
            "settings": ["key", "value"],
            "order_sequences": ["year", "last_number"],
            "invoice_sequences": ["year", "last_number"],
        }
        
        for table_name, required_cols in expected_tables.items():
            try:
                exists = db.fetch_one(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,)
                )
                if exists:
                    # Zkontroluj sloupce
                    cols = {c["name"] for c in db.fetch_all(f"PRAGMA table_info({table_name})")}
                    missing = set(required_cols) - cols
                    if missing:
                        self.log_warn(f"{table_name} - chybí sloupce: {missing}")
                    else:
                        # Spočítej záznamy
                        count = db.fetch_one(f"SELECT COUNT(*) as c FROM {table_name}")["c"]
                        self.log_pass(f"{table_name} ({count} záznamů)")
                else:
                    self.log_fail(f"{table_name}", "Tabulka neexistuje!")
            except Exception as e:
                self.log_fail(f"{table_name}", str(e))
        
        # Test propojení (FK)
        self.print_subheader("Propojení dat (Foreign Keys)")
        
        fk_tests = [
            ("vehicles.customer_id → customers.id", 
             "SELECT COUNT(*) as c FROM vehicles v LEFT JOIN customers c ON v.customer_id = c.id WHERE v.customer_id IS NOT NULL AND c.id IS NULL"),
            ("orders.customer_id → customers.id",
             "SELECT COUNT(*) as c FROM orders o LEFT JOIN customers c ON o.customer_id = c.id WHERE o.customer_id IS NOT NULL AND c.id IS NULL"),
            ("orders.vehicle_id → vehicles.id",
             "SELECT COUNT(*) as c FROM orders o LEFT JOIN vehicles v ON o.vehicle_id = v.id WHERE o.vehicle_id IS NOT NULL AND v.id IS NULL"),
            ("calendar_events.customer_id → customers.id",
             "SELECT COUNT(*) as c FROM calendar_events ce LEFT JOIN customers c ON ce.customer_id = c.id WHERE ce.customer_id IS NOT NULL AND c.id IS NULL"),
            ("user_logins.user_id → users.id",
             "SELECT COUNT(*) as c FROM user_logins ul LEFT JOIN users u ON ul.user_id = u.id WHERE ul.user_id IS NOT NULL AND u.id IS NULL"),
        ]
        
        for name, query in fk_tests:
            try:
                result = db.fetch_one(query)
                if result and result["c"] == 0:
                    self.log_pass(f"{name}")
                else:
                    self.log_warn(f"{name} - {result['c']} neplatných odkazů")
            except Exception as e:
                self.log_warn(f"{name} - {e}")
        
        # Test výchozích dat
        self.print_subheader("Výchozí data")
        
        data_checks = [
            ("Admin účet", "SELECT COUNT(*) as c FROM users WHERE username='admin'", 1),
            ("Role", "SELECT COUNT(*) as c FROM roles", 1),
            ("Oprávnění", "SELECT COUNT(*) as c FROM permissions", 1),
            ("Značky vozidel", "SELECT COUNT(*) as c FROM codebook_brands", 1),
            ("Nastavení kalendáře", "SELECT COUNT(*) as c FROM calendar_settings", 1),
            ("Svátky", "SELECT COUNT(*) as c FROM calendar_holidays", 1),
        ]
        
        for name, query, min_count in data_checks:
            try:
                result = db.fetch_one(query)
                if result and result["c"] >= min_count:
                    self.log_pass(f"{name} ({result['c']} záznamů)")
                else:
                    self.log_warn(f"{name} - chybí výchozí data")
            except Exception as e:
                self.log_fail(f"{name}", str(e))
        
        # Odpojení
        db.disconnect()
        self.log_info("Databáze odpojena")
    
    # =========================================================================
    # TEST 5: MODULY - KONTROLA TŘÍD A METOD
    # =========================================================================
    def test_module_classes(self):
        """Kontrola že moduly mají správné třídy a metody"""
        self.print_header("5. MODULY - TŘÍDY A METODY")
        
        # Očekávané metody pro hlavní moduly
        expected_methods = {
            "CustomersModule": ["refresh", "init_ui"],
            "VehiclesModule": ["refresh", "init_ui"],
            "OrdersModule": ["refresh", "init_ui"],
            "WarehouseModule": ["refresh", "init_ui"],
            "CalendarModule": ["refresh", "init_ui"],
            "UsersModule": ["refresh", "init_ui"],
            "ManagementModule": ["refresh", "init_ui"],
            "AdministrationModule": ["refresh", "init_ui"],
            "CodebooksModule": ["refresh", "init_ui"],
            "SettingsModule": ["refresh", "init_ui"],
        }
        
        for class_name, methods in expected_methods.items():
            if class_name in self.modules_found:
                mod = self.modules_found[class_name]
                cls = getattr(mod, class_name)
                
                missing_methods = []
                for method in methods:
                    if not hasattr(cls, method):
                        missing_methods.append(method)
                
                if missing_methods:
                    self.log_warn(f"{class_name} - chybí metody: {missing_methods}")
                else:
                    self.log_pass(f"{class_name} - všechny metody OK")
            else:
                self.log_fail(f"{class_name}", "Modul nebyl načten")
        
        # Kontrola dědičnosti (všechny moduly by měly dědit z QWidget)
        self.print_subheader("Dědičnost (QWidget)")
        
        from PyQt6.QtWidgets import QWidget
        
        for class_name, mod in self.modules_found.items():
            cls = getattr(mod, class_name)
            if issubclass(cls, QWidget):
                self.log_pass(f"{class_name} dědí z QWidget")
            else:
                self.log_fail(f"{class_name}", "Nedědí z QWidget!")
    
    # =========================================================================
    # TEST 6: KONFIGURACE
    # =========================================================================
    def test_configuration(self):
        """Kontrola konfigurace"""
        self.print_header("6. KONFIGURACE")
        
        try:
            import config
        except ImportError:
            self.log_fail("Import config.py", "Soubor neexistuje nebo má chyby")
            return
        
        # Povinné konstanty
        required_config = [
            "APP_NAME",
            "APP_VERSION",
            "DATABASE_PATH",
            "WINDOW_WIDTH",
            "WINDOW_HEIGHT",
            "MODULES",
            "COLOR_PRIMARY",
            "COLOR_SECONDARY",
            "COLOR_SUCCESS",
            "COLOR_WARNING",
            "COLOR_DANGER",
        ]
        
        self.print_subheader("Povinné konstanty")
        for const in required_config:
            if hasattr(config, const):
                value = getattr(config, const)
                if isinstance(value, str) and len(value) > 50:
                    value = value[:50] + "..."
                self.log_pass(f"{const} = {value}")
            else:
                self.log_fail(f"{const}", "Konstanta není definována")
        
        # Kontrola MODULES
        self.print_subheader("Definice modulů")
        if hasattr(config, "MODULES"):
            for mod_def in config.MODULES:
                if isinstance(mod_def, dict) and "id" in mod_def and "name" in mod_def:
                    self.log_pass(f"Modul: {mod_def['id']} ({mod_def['name']})")
                else:
                    self.log_warn(f"Neplatná definice modulu: {mod_def}")
        else:
            self.log_fail("config.MODULES", "Není definováno")
    
    # =========================================================================
    # TEST 7: BEZPEČNOST
    # =========================================================================
    def test_security(self):
        """Kontrola bezpečnostních aspektů"""
        self.print_header("7. BEZPEČNOST")
        
        # Kontrola hashování hesel
        self.print_subheader("Hashování hesel")
        try:
            from utils_auth import hash_password, verify_password, is_bcrypt_hash
            
            test_password = "TestPassword123!"
            hashed = hash_password(test_password)
            
            if is_bcrypt_hash(hashed):
                self.log_pass("hash_password() generuje bcrypt hash")
            else:
                self.log_fail("hash_password()", "Negeneruje bcrypt hash!")
            
            if verify_password(test_password, hashed):
                self.log_pass("verify_password() správně ověřuje")
            else:
                self.log_fail("verify_password()", "Neověřuje správně hesla")
            
            if not verify_password("WrongPassword", hashed):
                self.log_pass("verify_password() odmítá špatná hesla")
            else:
                self.log_fail("verify_password()", "Přijímá špatná hesla!")
        except Exception as e:
            self.log_fail("Test hashování hesel", str(e))
        
        # Kontrola admin účtu
        self.print_subheader("Admin účet")
        try:
            from database_manager import db
            db.connect()
            
            admin = db.fetch_one("SELECT * FROM users WHERE username='admin'")
            if admin:
                if admin["password"] == "admin":
                    self.log_warn("Admin má výchozí heslo 'admin' - ZMĚŇ HO!")
                elif is_bcrypt_hash(admin["password"]):
                    self.log_pass("Admin má hashované heslo")
                else:
                    self.log_warn("Admin má plaintext heslo - bude upgradováno při přihlášení")
                
                if admin["active"] == 1:
                    self.log_pass("Admin účet je aktivní")
                else:
                    self.log_fail("Admin účet", "Není aktivní!")
            else:
                self.log_fail("Admin účet", "Neexistuje!")
            
            db.disconnect()
        except Exception as e:
            self.log_fail("Kontrola admin účtu", str(e))
        
        # Kontrola oprávnění
        self.print_subheader("Systém oprávnění")
        try:
            from utils_permissions import has_permission
            self.log_pass("has_permission() je dostupná")
        except Exception as e:
            self.log_fail("Import has_permission", str(e))
    
    # =========================================================================
    # TEST 8: KONZISTENCE
    # =========================================================================
    def test_consistency(self):
        """Kontrola konzistence mezi moduly"""
        self.print_header("8. KONZISTENCE")
        
        # Kontrola že main.py importuje správné moduly
        self.print_subheader("main.py importy")
        
        main_py = self.project_dir / "main.py"
        if main_py.exists():
            with open(main_py, "r", encoding="utf-8") as f:
                content = f.read()
            
            expected_imports = [
                "CustomersModule",
                "VehiclesModule",
                "OrdersModule",
                "WarehouseModule",
                "CalendarModule",
                "UsersModule",
                "ManagementModule",
                "AdministrationModule",
                "CodebooksModule",
                "SettingsModule",
            ]
            
            for imp in expected_imports:
                if imp in content:
                    self.log_pass(f"main.py importuje {imp}")
                else:
                    self.log_warn(f"main.py neimportuje {imp}")
            
            # Kontrola add_module volání
            for imp in expected_imports:
                module_id = imp.replace("Module", "").lower()
                if module_id == "customers":
                    search = 'add_module("customers"'
                elif module_id == "vehicles":
                    search = 'add_module("vehicles"'
                else:
                    search = f'add_module("{module_id}"'
                
                if search in content or f"add_module('{module_id}'" in content:
                    pass  # OK
                else:
                    self.log_warn(f"main.py možná nevolá add_module pro {module_id}")
        else:
            self.log_fail("main.py", "Soubor neexistuje!")
        
        # Kontrola config.MODULES vs skutečné moduly
        self.print_subheader("config.MODULES vs skutečné moduly")
        try:
            import config
            
            config_module_ids = {m["id"] for m in config.MODULES}
            loaded_modules = {
                "dashboard", "customers", "vehicles", "orders", "warehouse",
                "calendar", "users", "management", "administration", "codebooks", "settings"
            }
            
            missing_in_config = loaded_modules - config_module_ids
            extra_in_config = config_module_ids - loaded_modules - {"rental"}  # rental je volitelný
            
            if missing_in_config:
                self.log_warn(f"Moduly chybí v config.MODULES: {missing_in_config}")
            
            if extra_in_config:
                self.log_info(f"Extra moduly v config.MODULES (možná neimplementované): {extra_in_config}")
            
            if not missing_in_config:
                self.log_pass("Všechny moduly jsou v config.MODULES")
        except Exception as e:
            self.log_fail("Konzistence config.MODULES", str(e))
    
    # =========================================================================
    # TEST 9: ZÁVISLOSTI MEZI MODULY
    # =========================================================================
    def test_module_dependencies(self):
        """Test závislostí mezi moduly"""
        self.print_header("9. ZÁVISLOSTI MEZI MODULY")
        
        # Kontrola kritických závislostí
        dependencies = [
            ("Zakázky", "modules/orders", ["customers", "vehicles", "warehouse"]),
            ("Kalendář", "modules/calendar", ["customers", "vehicles", "users"]),
            ("Administrativa", "modules/administration", ["customers", "orders"]),
            ("Management", "modules/management", ["orders", "warehouse", "customers"]),
        ]
        
        for module_name, module_path, deps in dependencies:
            path = self.project_dir / module_path
            if not path.exists():
                self.log_warn(f"{module_name} - složka neexistuje")
                continue
            
            # Projdi všechny Python soubory v modulu
            has_imports = {d: False for d in deps}
            
            for py_file in path.glob("*.py"):
                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    for dep in deps:
                        if dep in content or f"from modules.{dep}" in content:
                            has_imports[dep] = True
                except Exception:
                    pass
            
            missing = [d for d, found in has_imports.items() if not found]
            if missing:
                self.log_info(f"{module_name} pravděpodobně neimportuje: {missing} (může být OK)")
            else:
                self.log_pass(f"{module_name} má reference na všechny závislosti")
    
    # =========================================================================
    # SOUHRN
    # =========================================================================
    def generate_summary(self):
        """Vygeneruje závěrečný souhrn"""
        self.print_header("ZÁVĚREČNÝ SOUHRN")
        
        total = self.results["passed"] + self.results["failed"]
        success_rate = (self.results["passed"] / total * 100) if total > 0 else 0
        
        print(f"\n📊 STATISTIKA:")
        print(f"   ✅ Úspěšných testů: {self.results['passed']}")
        print(f"   ❌ Neúspěšných testů: {self.results['failed']}")
        print(f"   ⚠️  Varování: {self.results['warnings']}")
        print(f"   📈 Celková úspěšnost: {success_rate:.1f}%")
        
        if self.results["errors"]:
            print(f"\n🚨 KRITICKÉ CHYBY ({len(self.results['errors'])}):")
            for i, error in enumerate(self.results["errors"][:10], 1):
                print(f"   {i}. {error}")
            if len(self.results["errors"]) > 10:
                print(f"   ... a dalších {len(self.results['errors']) - 10} chyb")
        
        if self.results["warnings_list"]:
            print(f"\n⚠️  VAROVÁNÍ ({len(self.results['warnings_list'])}):")
            for i, warning in enumerate(self.results["warnings_list"][:10], 1):
                print(f"   {i}. {warning}")
            if len(self.results["warnings_list"]) > 10:
                print(f"   ... a dalších {len(self.results['warnings_list']) - 10} varování")
        
        # Doporučení
        print("\n💡 DOPORUČENÍ:")
        
        if success_rate == 100:
            print("   🎉 VÝBORNĚ! Projekt je v perfektním stavu.")
            print("   Můžeš spustit aplikaci: python main.py")
        elif success_rate >= 90:
            print("   👍 Projekt je téměř v pořádku. Oprav zbývající chyby.")
        elif success_rate >= 70:
            print("   ⚠️ Několik problémů k řešení:")
            if self.import_errors:
                print("   - Oprav chyby importů (pravděpodobně chybějící soubory)")
            if "user_logins" in str(self.results["errors"]):
                print("   - Aktualizuj database_manager.py (chybí tabulka user_logins)")
            if "calendar_events" in str(self.results["errors"]):
                print("   - Aktualizuj module_dashboard.py (používá starou tabulku)")
        else:
            print("   🚫 Kritické problémy! Zkontroluj:")
            print("   - database_manager.py")
            print("   - __init__.py soubory v modulech")
            print("   - Instalace PyQt6 a bcrypt")
        
        print("\n" + "=" * 70)
        print(f" Diagnostika dokončena: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print("=" * 70)
    
    # =========================================================================
    # HLAVNÍ SPUŠTĚNÍ
    # =========================================================================
    def run_all_diagnostics(self):
        """Spustí kompletní diagnostiku"""
        print("\n" + "🔧 " * 25)
        print("    MOTOSERVIS DMS - KOMPLETNÍ DIAGNOSTIKA PROJEKTU")
        print("🔧 " * 25)
        print(f"\n📅 Datum: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print(f"📁 Projekt: {self.project_dir}")
        
        # Spusť všechny testy
        self.test_project_structure()
        self.test_python_syntax()
        self.test_imports()
        self.test_database()
        self.test_module_classes()
        self.test_configuration()
        self.test_security()
        self.test_consistency()
        self.test_module_dependencies()
        
        # Souhrn
        self.generate_summary()


def main():
    """Hlavní funkce"""
    diagnostics = ProjectDiagnostics()
    diagnostics.run_all_diagnostics()


if __name__ == "__main__":
    main()
