# -*- coding: utf-8 -*-
"""
Motoservis DMS - Testovací skript pro ověření propojení
Spusť tento skript pro kontrolu:
- Připojení k databázi
- Existence všech tabulek
- Správnost sloupců
- Propojení mezi moduly (FK)
- Základní CRUD operace

Použití: python test_database_connections.py
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Přidej cestu k projektu
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

# Import konfigurace a databáze
try:
    import config
    from database_manager import db
    print("✅ Import config a database_manager úspěšný")
except ImportError as e:
    print(f"❌ Chyba importu: {e}")
    sys.exit(1)


def print_header(text: str):
    """Vytiskne formátovanou hlavičku"""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)


def print_result(test_name: str, success: bool, details: str = ""):
    """Vytiskne výsledek testu"""
    icon = "✅" if success else "❌"
    print(f"{icon} {test_name}")
    if details:
        print(f"   └─ {details}")


class DatabaseTester:
    """Třída pro testování databáze a propojení"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = 0
        self.failed = 0
    
    def test_connection(self) -> bool:
        """Test připojení k databázi"""
        print_header("TEST 1: Připojení k databázi")
        
        try:
            result = db.connect()
            if result:
                print_result("Připojení k databázi", True, str(config.DATABASE_PATH))
                self.passed += 1
                return True
            else:
                print_result("Připojení k databázi", False, "db.connect() vrátil False")
                self.failed += 1
                return False
        except Exception as e:
            print_result("Připojení k databázi", False, str(e))
            self.errors.append(f"Připojení: {e}")
            self.failed += 1
            return False
    
    def test_tables_exist(self) -> bool:
        """Test existence všech požadovaných tabulek"""
        print_header("TEST 2: Existence tabulek")
        
        required_tables = [
            # Core
            "customers", "vehicles", "users", "orders",
            # Users modul
            "roles", "permissions", "role_permissions", "user_permissions", 
            "user_logins", "audit_log",
            # Sklad
            "warehouse", "warehouse_categories", "warehouse_suppliers", "warehouse_movements",
            # Zakázky
            "order_items", "order_work_log",
            # Kalendář
            "calendar_events", "calendar_reminders", "calendar_recurring_rules",
            "calendar_availability", "calendar_holidays", "calendar_settings",
            # Administrativa
            "invoices", "invoice_items", "payments", "documents", "admin_settings",
            # Číselníky
            "codebook_brands", "codebook_vehicle_types", "codebook_fuel_types",
            "codebook_colors", "codebook_repair_types", "codebook_positions",
            "codebook_hourly_rates", "codebook_customer_groups", "codebook_payment_methods",
            "codebook_vat_rates", "codebook_order_statuses", "codebook_units", "codebook_currencies",
            # Nastavení
            "settings", "order_sequences", "invoice_sequences",
            # Ostatní
            "rental"
        ]
        
        all_ok = True
        for table in required_tables:
            exists = db.fetch_one(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,)
            )
            if exists:
                print_result(f"Tabulka {table}", True)
                self.passed += 1
            else:
                print_result(f"Tabulka {table}", False, "CHYBÍ!")
                self.errors.append(f"Chybí tabulka: {table}")
                self.failed += 1
                all_ok = False
        
        return all_ok
    
    def test_critical_columns(self) -> bool:
        """Test kritických sloupců v důležitých tabulkách"""
        print_header("TEST 3: Kritické sloupce")
        
        checks = {
            "customers": ["id", "first_name", "last_name", "phone", "email"],
            "vehicles": ["id", "customer_id", "brand", "model", "license_plate", "vin"],
            "users": ["id", "username", "password", "full_name", "role", "active"],
            "orders": ["id", "order_number", "customer_id", "vehicle_id", "status", "created_date"],
            "warehouse": ["id", "code", "name", "quantity", "min_quantity", "price_purchase", "price_sale"],
            "calendar_events": ["id", "title", "start_datetime", "end_datetime", "mechanic_id", "customer_id", "vehicle_id"],
            "user_logins": ["id", "user_id", "login_time", "success"],
            "invoices": ["id", "invoice_number", "invoice_type", "customer_id", "status", "due_date"],
        }
        
        all_ok = True
        for table, columns in checks.items():
            try:
                existing_cols = db.fetch_all(f"PRAGMA table_info({table})")
                existing_names = {c["name"] for c in existing_cols}
                
                missing = set(columns) - existing_names
                if missing:
                    print_result(f"{table}", False, f"Chybí sloupce: {missing}")
                    self.errors.append(f"{table}: chybí {missing}")
                    self.failed += 1
                    all_ok = False
                else:
                    print_result(f"{table}", True, f"Všech {len(columns)} sloupců OK")
                    self.passed += 1
            except Exception as e:
                print_result(f"{table}", False, str(e))
                self.failed += 1
                all_ok = False
        
        return all_ok
    
    def test_foreign_keys(self) -> bool:
        """Test cizích klíčů (propojení)"""
        print_header("TEST 4: Propojení (Foreign Keys)")
        
        fk_tests = [
            ("vehicles", "customer_id", "customers", "id"),
            ("orders", "customer_id", "customers", "id"),
            ("orders", "vehicle_id", "vehicles", "id"),
            ("order_items", "order_id", "orders", "id"),
            ("order_items", "warehouse_id", "warehouse", "id"),
            ("calendar_events", "customer_id", "customers", "id"),
            ("calendar_events", "vehicle_id", "vehicles", "id"),
            ("calendar_events", "mechanic_id", "users", "id"),
            ("invoices", "customer_id", "customers", "id"),
            ("invoices", "order_id", "orders", "id"),
            ("user_logins", "user_id", "users", "id"),
            ("role_permissions", "role_id", "roles", "id"),
            ("role_permissions", "permission_id", "permissions", "id"),
            ("user_permissions", "user_id", "users", "id"),
            ("user_permissions", "permission_id", "permissions", "id"),
        ]
        
        all_ok = True
        for child_table, child_col, parent_table, parent_col in fk_tests:
            # Ověř, že oba sloupce existují
            try:
                child_cols = {c["name"] for c in db.fetch_all(f"PRAGMA table_info({child_table})")}
                parent_cols = {c["name"] for c in db.fetch_all(f"PRAGMA table_info({parent_table})")}
                
                if child_col in child_cols and parent_col in parent_cols:
                    print_result(
                        f"{child_table}.{child_col} → {parent_table}.{parent_col}",
                        True
                    )
                    self.passed += 1
                else:
                    missing = []
                    if child_col not in child_cols:
                        missing.append(f"{child_table}.{child_col}")
                    if parent_col not in parent_cols:
                        missing.append(f"{parent_table}.{parent_col}")
                    print_result(
                        f"{child_table}.{child_col} → {parent_table}.{parent_col}",
                        False,
                        f"Chybí: {missing}"
                    )
                    self.failed += 1
                    all_ok = False
            except Exception as e:
                print_result(
                    f"{child_table}.{child_col} → {parent_table}.{parent_col}",
                    False,
                    str(e)
                )
                self.failed += 1
                all_ok = False
        
        return all_ok
    
    def test_default_data(self) -> bool:
        """Test výchozích dat"""
        print_header("TEST 5: Výchozí data")
        
        tests = [
            ("users", "SELECT COUNT(*) as c FROM users WHERE username='admin'", "Admin účet"),
            ("roles", "SELECT COUNT(*) as c FROM roles", "Role"),
            ("permissions", "SELECT COUNT(*) as c FROM permissions", "Oprávnění"),
            ("codebook_brands", "SELECT COUNT(*) as c FROM codebook_brands", "Značky vozidel"),
            ("settings", "SELECT COUNT(*) as c FROM settings", "Nastavení aplikace"),
            ("calendar_settings", "SELECT COUNT(*) as c FROM calendar_settings", "Nastavení kalendáře"),
            ("admin_settings", "SELECT COUNT(*) as c FROM admin_settings", "Nastavení administrativy"),
            ("calendar_holidays", "SELECT COUNT(*) as c FROM calendar_holidays", "Svátky"),
        ]
        
        all_ok = True
        for name, query, desc in tests:
            try:
                result = db.fetch_one(query)
                count = result["c"] if result else 0
                if count > 0:
                    print_result(desc, True, f"{count} záznamů")
                    self.passed += 1
                else:
                    print_result(desc, False, "Žádná data - spusť initialize_default_data()")
                    self.warnings.append(f"{desc}: prázdné")
                    self.failed += 1
                    all_ok = False
            except Exception as e:
                print_result(desc, False, str(e))
                self.failed += 1
                all_ok = False
        
        return all_ok
    
    def test_crud_operations(self) -> bool:
        """Test základních CRUD operací"""
        print_header("TEST 6: CRUD operace")
        
        all_ok = True
        test_customer_id = None
        test_vehicle_id = None
        test_order_id = None
        test_event_id = None
        
        # CREATE - zákazník
        try:
            db.execute_query("""
                INSERT INTO customers (first_name, last_name, phone, email)
                VALUES ('Test', 'Zákazník', '+420123456789', 'test@test.cz')
            """)
            result = db.fetch_one("SELECT id FROM customers WHERE email='test@test.cz'")
            if result:
                test_customer_id = result["id"]
                print_result("CREATE zákazník", True, f"ID: {test_customer_id}")
                self.passed += 1
            else:
                print_result("CREATE zákazník", False, "Nepodařilo se vytvořit")
                self.failed += 1
                all_ok = False
        except Exception as e:
            print_result("CREATE zákazník", False, str(e))
            self.failed += 1
            all_ok = False
        
        # CREATE - vozidlo
        if test_customer_id:
            try:
                db.execute_query("""
                    INSERT INTO vehicles (customer_id, brand, model, license_plate, vin)
                    VALUES (?, 'TestBrand', 'TestModel', 'TEST123', 'TESTVIN123456789')
                """, (test_customer_id,))
                result = db.fetch_one("SELECT id FROM vehicles WHERE license_plate='TEST123'")
                if result:
                    test_vehicle_id = result["id"]
                    print_result("CREATE vozidlo", True, f"ID: {test_vehicle_id}")
                    self.passed += 1
                else:
                    print_result("CREATE vozidlo", False, "Nepodařilo se vytvořit")
                    self.failed += 1
                    all_ok = False
            except Exception as e:
                print_result("CREATE vozidlo", False, str(e))
                self.failed += 1
                all_ok = False
        
        # CREATE - zakázka
        if test_customer_id and test_vehicle_id:
            try:
                order_number = f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}"
                db.execute_query("""
                    INSERT INTO orders (order_number, customer_id, vehicle_id, status, created_date)
                    VALUES (?, ?, ?, 'V přípravě', DATE('now'))
                """, (order_number, test_customer_id, test_vehicle_id))
                result = db.fetch_one("SELECT id FROM orders WHERE order_number=?", (order_number,))
                if result:
                    test_order_id = result["id"]
                    print_result("CREATE zakázka", True, f"ID: {test_order_id}")
                    self.passed += 1
                else:
                    print_result("CREATE zakázka", False, "Nepodařilo se vytvořit")
                    self.failed += 1
                    all_ok = False
            except Exception as e:
                print_result("CREATE zakázka", False, str(e))
                self.failed += 1
                all_ok = False
        
        # CREATE - kalendářová událost
        if test_customer_id and test_vehicle_id:
            try:
                start_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                end_dt = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
                db.execute_query("""
                    INSERT INTO calendar_events (title, event_type, start_datetime, end_datetime, customer_id, vehicle_id)
                    VALUES ('Test Event', 'service', ?, ?, ?, ?)
                """, (start_dt, end_dt, test_customer_id, test_vehicle_id))
                result = db.fetch_one("SELECT id FROM calendar_events WHERE title='Test Event'")
                if result:
                    test_event_id = result["id"]
                    print_result("CREATE kalendářová událost", True, f"ID: {test_event_id}")
                    self.passed += 1
                else:
                    print_result("CREATE kalendářová událost", False, "Nepodařilo se vytvořit")
                    self.failed += 1
                    all_ok = False
            except Exception as e:
                print_result("CREATE kalendářová událost", False, str(e))
                self.failed += 1
                all_ok = False
        
        # READ - test propojení
        if test_order_id:
            try:
                result = db.fetch_one("""
                    SELECT o.id, o.order_number, c.first_name, c.last_name, v.license_plate
                    FROM orders o
                    JOIN customers c ON c.id = o.customer_id
                    JOIN vehicles v ON v.id = o.vehicle_id
                    WHERE o.id = ?
                """, (test_order_id,))
                if result and result["first_name"] == "Test" and result["license_plate"] == "TEST123":
                    print_result("READ s JOIN (propojení)", True, "Data správně propojena")
                    self.passed += 1
                else:
                    print_result("READ s JOIN (propojení)", False, "Data nejsou správně propojena")
                    self.failed += 1
                    all_ok = False
            except Exception as e:
                print_result("READ s JOIN (propojení)", False, str(e))
                self.failed += 1
                all_ok = False
        
        # UPDATE
        if test_customer_id:
            try:
                db.execute_query(
                    "UPDATE customers SET phone='+420999888777' WHERE id=?",
                    (test_customer_id,)
                )
                result = db.fetch_one("SELECT phone FROM customers WHERE id=?", (test_customer_id,))
                if result and result["phone"] == "+420999888777":
                    print_result("UPDATE", True)
                    self.passed += 1
                else:
                    print_result("UPDATE", False, "Data se neaktualizovala")
                    self.failed += 1
                    all_ok = False
            except Exception as e:
                print_result("UPDATE", False, str(e))
                self.failed += 1
                all_ok = False
        
        # DELETE - úklid testovacích dat
        cleanup_ok = True
        
        if test_event_id:
            try:
                db.execute_query("DELETE FROM calendar_events WHERE id=?", (test_event_id,))
                print_result("DELETE kalendářová událost", True)
                self.passed += 1
            except Exception as e:
                print_result("DELETE kalendářová událost", False, str(e))
                self.failed += 1
                cleanup_ok = False
        
        if test_order_id:
            try:
                db.execute_query("DELETE FROM orders WHERE id=?", (test_order_id,))
                print_result("DELETE zakázka", True)
                self.passed += 1
            except Exception as e:
                print_result("DELETE zakázka", False, str(e))
                self.failed += 1
                cleanup_ok = False
        
        if test_vehicle_id:
            try:
                db.execute_query("DELETE FROM vehicles WHERE id=?", (test_vehicle_id,))
                print_result("DELETE vozidlo", True)
                self.passed += 1
            except Exception as e:
                print_result("DELETE vozidlo", False, str(e))
                self.failed += 1
                cleanup_ok = False
        
        if test_customer_id:
            try:
                db.execute_query("DELETE FROM customers WHERE id=?", (test_customer_id,))
                print_result("DELETE zákazník", True)
                self.passed += 1
            except Exception as e:
                print_result("DELETE zákazník", False, str(e))
                self.failed += 1
                cleanup_ok = False
        
        return all_ok and cleanup_ok
    
    def test_sequences(self) -> bool:
        """Test sekvencí čísel zakázek a faktur"""
        print_header("TEST 7: Sekvence čísel")
        
        all_ok = True
        
        # Test čísla zakázky
        try:
            order_num = db.get_next_order_number()
            if order_num and len(order_num) == 8 and order_num.startswith("2"):
                print_result("Generování čísla zakázky", True, f"Další: {order_num}")
                self.passed += 1
            else:
                print_result("Generování čísla zakázky", False, f"Neplatný formát: {order_num}")
                self.failed += 1
                all_ok = False
        except Exception as e:
            print_result("Generování čísla zakázky", False, str(e))
            self.failed += 1
            all_ok = False
        
        # Test čísla faktury
        try:
            invoice_num = db.get_next_invoice_number("issued")
            if invoice_num and "-" in invoice_num:
                print_result("Generování čísla faktury", True, f"Další: {invoice_num}")
                self.passed += 1
            else:
                print_result("Generování čísla faktury", False, f"Neplatný formát: {invoice_num}")
                self.failed += 1
                all_ok = False
        except Exception as e:
            print_result("Generování čísla faktury", False, str(e))
            self.failed += 1
            all_ok = False
        
        return all_ok
    
    def test_module_imports(self) -> bool:
        """Test importu modulů"""
        print_header("TEST 8: Import modulů")
        
        modules_to_test = [
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
        
        all_ok = True
        for module_path, class_name in modules_to_test:
            try:
                module = __import__(module_path, fromlist=[class_name])
                if hasattr(module, class_name):
                    print_result(f"Import {class_name}", True)
                    self.passed += 1
                else:
                    print_result(f"Import {class_name}", False, f"Třída {class_name} nenalezena v modulu")
                    self.failed += 1
                    all_ok = False
            except ImportError as e:
                print_result(f"Import {class_name}", False, str(e))
                self.warnings.append(f"Nelze importovat {module_path}: {e}")
                self.failed += 1
                all_ok = False
        
        return all_ok
    
    def generate_report(self):
        """Vygeneruje závěrečný report"""
        print_header("ZÁVĚREČNÝ REPORT")
        
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"📊 Celkem testů: {total}")
        print(f"✅ Úspěšných: {self.passed}")
        print(f"❌ Neúspěšných: {self.failed}")
        print(f"📈 Úspěšnost: {success_rate:.1f}%")
        
        if self.errors:
            print("\n🚨 KRITICKÉ CHYBY:")
            for error in self.errors:
                print(f"   • {error}")
        
        if self.warnings:
            print("\n⚠️ VAROVÁNÍ:")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if success_rate == 100:
            print("\n🎉 GRATULACE! Všechny testy prošly úspěšně.")
            print("   Databáze a propojení jsou v pořádku.")
        elif success_rate >= 80:
            print("\n👍 Většina testů prošla. Oprav zbývající chyby.")
        elif success_rate >= 50:
            print("\n⚠️ Polovina testů selhala. Zkontroluj database_manager.py")
        else:
            print("\n🚫 Kritické problémy! Zkontroluj celou konfiguraci.")
        
        print("\n" + "=" * 60)
    
    def run_all_tests(self):
        """Spustí všechny testy"""
        print("\n" + "🔧 " * 20)
        print("   MOTOSERVIS DMS - TESTOVÁNÍ DATABÁZE A PROPOJENÍ")
        print("🔧 " * 20)
        print(f"\n📅 Datum testu: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print(f"📁 Databáze: {config.DATABASE_PATH}")
        
        # 1. Připojení
        if not self.test_connection():
            print("\n❌ Test ukončen - nelze se připojit k databázi")
            return
        
        # 2. Vytvoření tabulek (pokud neexistují)
        try:
            print("\n⏳ Spouštím create_tables() a initialize_default_data()...")
            db.create_tables()
            db.initialize_default_data()
            print("✅ Schéma databáze připraveno")
        except Exception as e:
            print(f"❌ Chyba při vytváření tabulek: {e}")
            self.errors.append(f"create_tables: {e}")
        
        # 3. Testy
        self.test_tables_exist()
        self.test_critical_columns()
        self.test_foreign_keys()
        self.test_default_data()
        self.test_crud_operations()
        self.test_sequences()
        self.test_module_imports()
        
        # 4. Report
        self.generate_report()
        
        # 5. Odpojení
        db.disconnect()
        print("\n✅ Databáze odpojena")


def main():
    """Hlavní funkce"""
    tester = DatabaseTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
