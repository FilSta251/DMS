# -*- coding: utf-8 -*-
"""
Motoservis DMS - ULTIMÁTNÍ DIAGNOSTIKA
========================================

Tento skript:
1. Projde VŠECHNY Python soubory v projektu
2. Najde VŠECHNY SQL dotazy (SELECT, INSERT, UPDATE, DELETE)
3. Extrahuje všechny tabulky a sloupce z dotazů
4. Porovná je s reálnou databází
5. Najde VŠECHNY chybějící tabulky a sloupce
6. Vygeneruje PŘESNÝ seznam oprav

Použití: python kompletni_diagnostika.py
"""

import sys
import re
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Nastavení cesty projektu
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))


class UltimateDiagnostics:
    """Ultimátní diagnostika projektu"""
    
    def __init__(self):
        self.project_dir = PROJECT_DIR
        self.python_files = []
        self.sql_queries = []
        self.tables_in_code = defaultdict(set)  # tabulka -> set(sloupce)
        self.tables_in_db = {}  # tabulka -> set(sloupce)
        self.missing_tables = set()
        self.missing_columns = defaultdict(set)  # tabulka -> set(chybějící sloupce)
        self.errors = []
        self.warnings = []
        self.fixes_needed = []
        self.db = None
        
    def print_header(self, title: str):
        print("\n" + "=" * 70)
        print(f" {title}")
        print("=" * 70)
    
    def print_subheader(self, title: str):
        print(f"\n--- {title} ---")
    
    # =========================================================================
    # KROK 1: Najdi všechny Python soubory
    # =========================================================================
    def find_python_files(self):
        """Najde všechny Python soubory v projektu"""
        self.print_header("KROK 1: HLEDÁNÍ PYTHON SOUBORŮ")
        
        self.python_files = list(self.project_dir.rglob("*.py"))
        # Filtruj __pycache__ a venv
        self.python_files = [
            f for f in self.python_files 
            if "__pycache__" not in str(f) and "venv" not in str(f) and ".git" not in str(f)
        ]
        
        print(f"✅ Nalezeno {len(self.python_files)} Python souborů")
        
        # Ukáž některé důležité
        important_dirs = ["modules/customers", "modules/vehicles", "modules/orders", 
                         "modules/warehouse", "modules/calendar", "modules/users"]
        for dir_name in important_dirs:
            count = len([f for f in self.python_files if dir_name in str(f)])
            print(f"   📁 {dir_name}: {count} souborů")
    
    # =========================================================================
    # KROK 2: Extrahuj SQL dotazy ze všech souborů
    # =========================================================================
    def extract_sql_queries(self):
        """Extrahuje všechny SQL dotazy ze všech Python souborů"""
        self.print_header("KROK 2: EXTRAKCE SQL DOTAZŮ")
        
        # Regex patterny pro různé typy SQL v Pythonu
        patterns = [
            # Trojité uvozovky
            r'"""(.*?)"""',
            r"'''(.*?)'''",
            # Normální stringy s SQL klíčovými slovy
            r'"([^"]*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER)[^"]*)"',
            r"'([^']*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER)[^']*)'",
        ]
        
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE TABLE', 'ALTER TABLE', 'FROM', 'JOIN']
        
        for py_file in self.python_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Hledej SQL v trojitých uvozovkách (multiline)
                for pattern in patterns[:2]:
                    matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                    for match in matches:
                        if any(kw in match.upper() for kw in sql_keywords):
                            self.sql_queries.append({
                                "file": py_file.relative_to(self.project_dir),
                                "query": match.strip(),
                                "type": "multiline"
                            })
                
                # Hledej SQL v jednořádkových stringech
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    # Hledej execute_query, fetch_one, fetch_all
                    if any(func in line for func in ['execute_query', 'fetch_one', 'fetch_all', 'cursor.execute']):
                        # Extrahuj SQL z tohoto a následujících řádků
                        sql_text = self._extract_sql_from_lines(lines, i)
                        if sql_text and any(kw in sql_text.upper() for kw in sql_keywords):
                            self.sql_queries.append({
                                "file": py_file.relative_to(self.project_dir),
                                "query": sql_text,
                                "type": "inline",
                                "line": i + 1
                            })
                
            except Exception as e:
                self.warnings.append(f"Nelze přečíst {py_file}: {e}")
        
        print(f"✅ Extrahováno {len(self.sql_queries)} SQL dotazů")
        
        # Statistika podle typu
        selects = len([q for q in self.sql_queries if 'SELECT' in q['query'].upper()])
        inserts = len([q for q in self.sql_queries if 'INSERT' in q['query'].upper()])
        updates = len([q for q in self.sql_queries if 'UPDATE' in q['query'].upper()])
        creates = len([q for q in self.sql_queries if 'CREATE' in q['query'].upper()])
        
        print(f"   📊 SELECT: {selects}, INSERT: {inserts}, UPDATE: {updates}, CREATE: {creates}")
    
    def _extract_sql_from_lines(self, lines, start_idx):
        """Extrahuje SQL z řádků začínajících na start_idx"""
        result = []
        in_string = False
        quote_char = None
        paren_depth = 0
        
        for i in range(start_idx, min(start_idx + 20, len(lines))):
            line = lines[i]
            
            # Jednoduchá extrakce - hledej string s SQL
            for match in re.finditer(r'["\']([^"\']+)["\']', line):
                text = match.group(1)
                if any(kw in text.upper() for kw in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'FROM']):
                    result.append(text)
            
            # Detekce trojitých uvozovek
            if '"""' in line or "'''" in line:
                triple_match = re.search(r'(""".*?"""|\'\'\'.*?\'\'\')', line, re.DOTALL)
                if triple_match:
                    text = triple_match.group(1)[3:-3]
                    if any(kw in text.upper() for kw in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'FROM']):
                        result.append(text)
        
        return ' '.join(result) if result else None
    
    # =========================================================================
    # KROK 3: Analyzuj SQL dotazy
    # =========================================================================
    def analyze_sql_queries(self):
        """Analyzuje SQL dotazy a extrahuje tabulky a sloupce"""
        self.print_header("KROK 3: ANALÝZA SQL DOTAZŮ")
        
        for query_info in self.sql_queries:
            query = query_info['query'].upper()
            query_lower = query_info['query']
            
            # Extrahuj tabulky z FROM a JOIN
            tables = self._extract_tables(query_lower)
            
            # Extrahuj sloupce
            columns = self._extract_columns(query_lower, tables)
            
            # Uložit
            for table, cols in columns.items():
                self.tables_in_code[table].update(cols)
        
        print(f"✅ Analyzováno {len(self.tables_in_code)} tabulek z kódu")
        
        for table in sorted(self.tables_in_code.keys()):
            cols = self.tables_in_code[table]
            print(f"   📋 {table}: {len(cols)} sloupců")
    
    def _extract_tables(self, query):
        """Extrahuje názvy tabulek z SQL dotazu"""
        tables = set()
        query_upper = query.upper()
        
        # FROM tabulka
        from_matches = re.findall(r'\bFROM\s+([a-z_][a-z0-9_]*)', query, re.IGNORECASE)
        tables.update(from_matches)
        
        # JOIN tabulka
        join_matches = re.findall(r'\bJOIN\s+([a-z_][a-z0-9_]*)', query, re.IGNORECASE)
        tables.update(join_matches)
        
        # INSERT INTO tabulka
        insert_matches = re.findall(r'\bINSERT\s+INTO\s+([a-z_][a-z0-9_]*)', query, re.IGNORECASE)
        tables.update(insert_matches)
        
        # UPDATE tabulka
        update_matches = re.findall(r'\bUPDATE\s+([a-z_][a-z0-9_]*)', query, re.IGNORECASE)
        tables.update(update_matches)
        
        # CREATE TABLE tabulka
        create_matches = re.findall(r'\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-z_][a-z0-9_]*)', query, re.IGNORECASE)
        tables.update(create_matches)
        
        # DELETE FROM tabulka
        delete_matches = re.findall(r'\bDELETE\s+FROM\s+([a-z_][a-z0-9_]*)', query, re.IGNORECASE)
        tables.update(delete_matches)
        
        return tables
    
    def _extract_columns(self, query, tables):
        """Extrahuje sloupce z SQL dotazu pro dané tabulky"""
        columns = defaultdict(set)
        
        # Normalizuj dotaz
        query_clean = re.sub(r'\s+', ' ', query)
        
        # SELECT sloupce
        # Pattern: sloupec, alias.sloupec, tabulka.sloupec
        col_patterns = [
            r'([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)',  # alias.sloupec
            r'\b([a-z_][a-z0-9_]*)\s+(?:AS|as)\s+',  # sloupec AS ...
        ]
        
        # Extrahuj aliasy tabulek
        aliases = {}
        alias_pattern = r'\b([a-z_][a-z0-9_]*)\s+(?:AS\s+)?([a-z])\b'
        for match in re.finditer(alias_pattern, query, re.IGNORECASE):
            table_name = match.group(1).lower()
            alias = match.group(2).lower()
            if table_name in [t.lower() for t in tables]:
                aliases[alias] = table_name
        
        # Také zkus FROM table alias pattern
        from_alias = re.findall(r'\bFROM\s+([a-z_][a-z0-9_]*)\s+([a-z])\b', query, re.IGNORECASE)
        for table, alias in from_alias:
            aliases[alias.lower()] = table.lower()
        
        join_alias = re.findall(r'\bJOIN\s+([a-z_][a-z0-9_]*)\s+([a-z])\b', query, re.IGNORECASE)
        for table, alias in join_alias:
            aliases[alias.lower()] = table.lower()
        
        # Najdi všechny alias.column patterny
        for match in re.finditer(r'\b([a-z])\.([a-z_][a-z0-9_]*)\b', query, re.IGNORECASE):
            alias = match.group(1).lower()
            col = match.group(2).lower()
            if alias in aliases:
                columns[aliases[alias]].add(col)
        
        # Najdi table.column patterny
        for table in tables:
            pattern = rf'\b{re.escape(table)}\.([a-z_][a-z0-9_]*)\b'
            for match in re.finditer(pattern, query, re.IGNORECASE):
                columns[table.lower()].add(match.group(1).lower())
        
        # Speciální case pro WHERE, ORDER BY, GROUP BY
        where_cols = re.findall(r'\bWHERE\s+([a-z_][a-z0-9_]*)\s*[=<>]', query, re.IGNORECASE)
        for col in where_cols:
            if col.lower() not in ['and', 'or', 'not', 'in', 'like']:
                # Přiřaď k první tabulce pokud je jen jedna
                if len(tables) == 1:
                    columns[list(tables)[0].lower()].add(col.lower())
        
        return dict(columns)
    
    # =========================================================================
    # KROK 4: Načti strukturu databáze
    # =========================================================================
    def load_database_structure(self):
        """Načte skutečnou strukturu databáze"""
        self.print_header("KROK 4: NAČÍTÁNÍ STRUKTURY DATABÁZE")
        
        try:
            from database_manager import db
            self.db = db
            
            if not db.connect():
                self.errors.append("Nelze se připojit k databázi!")
                return False
            
            # Vytvoř tabulky pokud neexistují
            print("⏳ Spouštím create_tables()...")
            db.create_tables()
            db.initialize_default_data()
            
            # Načti všechny tabulky
            tables = db.fetch_all("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            
            print(f"✅ Nalezeno {len(tables)} tabulek v databázi")
            
            # Pro každou tabulku načti sloupce
            for table_row in tables:
                table_name = table_row['name']
                cols = db.fetch_all(f"PRAGMA table_info({table_name})")
                self.tables_in_db[table_name] = {c['name'] for c in cols}
                print(f"   📋 {table_name}: {len(self.tables_in_db[table_name])} sloupců")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Chyba při načítání DB: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # =========================================================================
    # KROK 5: Porovnej kód vs databáze
    # =========================================================================
    def compare_code_vs_database(self):
        """Porovná sloupce v kódu s databází"""
        self.print_header("KROK 5: POROVNÁNÍ KÓDU VS DATABÁZE")
        
        # Najdi chybějící tabulky
        self.print_subheader("Chybějící tabulky")
        for table in self.tables_in_code:
            if table not in self.tables_in_db:
                self.missing_tables.add(table)
                print(f"❌ Tabulka {table} NEEXISTUJE v databázi!")
                self.fixes_needed.append({
                    "type": "missing_table",
                    "table": table,
                    "columns": list(self.tables_in_code[table])
                })
        
        if not self.missing_tables:
            print("✅ Všechny tabulky existují")
        
        # Najdi chybějící sloupce
        self.print_subheader("Chybějící sloupce")
        found_missing = False
        
        for table, code_cols in self.tables_in_code.items():
            if table in self.tables_in_db:
                db_cols = self.tables_in_db[table]
                missing = code_cols - db_cols
                
                if missing:
                    found_missing = True
                    self.missing_columns[table] = missing
                    print(f"❌ Tabulka {table}:")
                    for col in sorted(missing):
                        print(f"      - {col}")
                    
                    self.fixes_needed.append({
                        "type": "missing_columns",
                        "table": table,
                        "columns": list(missing)
                    })
        
        if not found_missing:
            print("✅ Všechny sloupce existují")
    
    # =========================================================================
    # KROK 6: Zkontroluj Python chyby (sqlite3.Row.get atd.)
    # =========================================================================
    def check_python_errors(self):
        """Kontroluje časté Python chyby"""
        self.print_header("KROK 6: KONTROLA PYTHON CHYB")
        
        issues = []
        
        for py_file in self.python_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines):
                    # Kontrola .get() na sqlite3.Row
                    if ".get(" in line and ("fetch_one" in ''.join(lines[max(0,i-10):i]) or 
                                            "user_data" in line or "row" in line.lower()):
                        # Možný problém s .get() na Row objektu
                        if "dict(" not in line and "if " not in lines[max(0,i-1)]:
                            issues.append({
                                "file": py_file.relative_to(self.project_dir),
                                "line": i + 1,
                                "issue": "Možné použití .get() na sqlite3.Row",
                                "code": line.strip()
                            })
                    
                    # Kontrola přístupu k neexistujícím atributům
                    if "self.user_data.get" in line or "row.get" in line:
                        issues.append({
                            "file": py_file.relative_to(self.project_dir),
                            "line": i + 1,
                            "issue": "sqlite3.Row nemá .get() metodu",
                            "code": line.strip(),
                            "fix": "Změň na: dict(row).get(...) nebo row['...'] if '...' in row.keys()"
                        })
                
            except Exception:
                pass
        
        if issues:
            print(f"❌ Nalezeno {len(issues)} potenciálních Python chyb:")
            for issue in issues[:20]:  # Zobraz max 20
                print(f"\n   📁 {issue['file']}:{issue['line']}")
                print(f"      Problém: {issue['issue']}")
                print(f"      Kód: {issue['code'][:80]}")
                if 'fix' in issue:
                    print(f"      Oprava: {issue['fix']}")
            
            self.fixes_needed.extend(issues)
        else:
            print("✅ Žádné zjevné Python chyby nenalezeny")
    
    # =========================================================================
    # KROK 7: Generuj opravy
    # =========================================================================
    def generate_fixes(self):
        """Generuje seznam oprav"""
        self.print_header("KROK 7: SEZNAM POTŘEBNÝCH OPRAV")
        
        if not self.fixes_needed and not self.missing_tables and not self.missing_columns:
            print("🎉 ŽÁDNÉ OPRAVY NEJSOU POTŘEBA!")
            return
        
        # Opravy pro databázi
        if self.missing_tables or self.missing_columns:
            self.print_subheader("OPRAVY DATABÁZE (database_manager.py)")
            
            print("\n📝 Přidej tyto ALTER TABLE příkazy do create_tables():\n")
            
            # Chybějící tabulky
            for table in self.missing_tables:
                cols = self.tables_in_code[table]
                print(f"# Chybí tabulka: {table}")
                print(f"# Sloupce používané v kódu: {', '.join(sorted(cols))}")
                print(f"# VYTVOŘ TABULKU nebo změň kód!\n")
            
            # Chybějící sloupce
            for table, cols in self.missing_columns.items():
                print(f"# Tabulka: {table}")
                print(f"self._ensure_columns(\"{table}\", [")
                for col in sorted(cols):
                    # Odhad typu podle názvu
                    if col.endswith("_id"):
                        col_type = "INTEGER"
                    elif col.endswith("_date") or col.endswith("_at"):
                        col_type = "TEXT"
                    elif col in ["is_active", "has_debt", "is_default"]:
                        col_type = "INTEGER DEFAULT 0"
                    elif col.endswith("_price") or col.endswith("_amount"):
                        col_type = "REAL DEFAULT 0"
                    else:
                        col_type = "TEXT"
                    
                    print(f"    (\"{col}\", \"{col_type}\"),")
                print("])\n")
        
        # Python opravy
        python_fixes = [f for f in self.fixes_needed if isinstance(f, dict) and 'file' in f and 'line' in f]
        if python_fixes:
            self.print_subheader("OPRAVY PYTHON SOUBORŮ")
            
            # Seskup podle souboru
            by_file = defaultdict(list)
            for fix in python_fixes:
                by_file[fix['file']].append(fix)
            
            for file_path, fixes in by_file.items():
                print(f"\n📁 {file_path}:")
                for fix in fixes:
                    print(f"   Řádek {fix['line']}: {fix['issue']}")
                    if 'fix' in fix:
                        print(f"   ➡️  {fix['fix']}")
    
    # =========================================================================
    # KROK 8: Export oprav do souboru
    # =========================================================================
    def export_fixes_to_file(self):
        """Exportuje potřebné opravy do souboru"""
        self.print_header("KROK 8: EXPORT OPRAV DO SOUBORU")
        
        output_file = self.project_dir / "OPRAVY_POTREBNE.txt"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write("MOTOSERVIS DMS - SEZNAM POTŘEBNÝCH OPRAV\n")
            f.write(f"Vygenerováno: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")
            
            # Chybějící tabulky
            if self.missing_tables:
                f.write("🔴 CHYBĚJÍCÍ TABULKY\n")
                f.write("-" * 70 + "\n")
                for table in sorted(self.missing_tables):
                    f.write(f"Tabulka: {table}\n")
                    f.write(f"Sloupce v kódu: {', '.join(sorted(self.tables_in_code[table]))}\n\n")
            
            # Chybějící sloupce
            if self.missing_columns:
                f.write("\n🟡 CHYBĚJÍCÍ SLOUPCE\n")
                f.write("-" * 70 + "\n")
                for table, cols in sorted(self.missing_columns.items()):
                    f.write(f"\nTabulka: {table}\n")
                    f.write("Chybějící sloupce:\n")
                    for col in sorted(cols):
                        f.write(f"  - {col}\n")
                    f.write("\nKód pro database_manager.py:\n")
                    f.write(f'self._ensure_columns("{table}", [\n')
                    for col in sorted(cols):
                        if col.endswith("_id"):
                            col_type = "INTEGER"
                        elif col.endswith("_date") or col.endswith("_at"):
                            col_type = "TEXT"
                        elif col in ["is_active", "has_debt", "is_default"]:
                            col_type = "INTEGER DEFAULT 0"
                        else:
                            col_type = "TEXT"
                        f.write(f'    ("{col}", "{col_type}"),\n')
                    f.write("])\n")
            
            # Python chyby
            python_fixes = [fix for fix in self.fixes_needed if isinstance(fix, dict) and 'file' in fix]
            if python_fixes:
                f.write("\n🟠 PYTHON CHYBY K OPRAVĚ\n")
                f.write("-" * 70 + "\n")
                for fix in python_fixes:
                    f.write(f"\nSoubor: {fix['file']}\n")
                    f.write(f"Řádek: {fix['line']}\n")
                    f.write(f"Problém: {fix['issue']}\n")
                    f.write(f"Kód: {fix.get('code', 'N/A')}\n")
                    if 'fix' in fix:
                        f.write(f"Oprava: {fix['fix']}\n")
            
            f.write("\n" + "=" * 70 + "\n")
            f.write("KONEC SEZNAMU OPRAV\n")
            f.write("=" * 70 + "\n")
        
        print(f"✅ Opravy exportovány do: {output_file}")
        print(f"   Otevři tento soubor pro detailní seznam!")
    
    # =========================================================================
    # SOUHRN
    # =========================================================================
    def generate_summary(self):
        """Generuje závěrečný souhrn"""
        self.print_header("ZÁVĚREČNÝ SOUHRN")
        
        total_issues = len(self.missing_tables) + len(self.missing_columns) + \
                      len([f for f in self.fixes_needed if isinstance(f, dict) and 'file' in f])
        
        print(f"\n📊 STATISTIKA:")
        print(f"   📁 Python souborů: {len(self.python_files)}")
        print(f"   🔍 SQL dotazů: {len(self.sql_queries)}")
        print(f"   📋 Tabulek v kódu: {len(self.tables_in_code)}")
        print(f"   🗃️  Tabulek v DB: {len(self.tables_in_db)}")
        print(f"   ❌ Chybějících tabulek: {len(self.missing_tables)}")
        print(f"   ⚠️  Tabulek s chybějícími sloupci: {len(self.missing_columns)}")
        print(f"   🔧 Celkem oprav potřeba: {total_issues}")
        
        if total_issues == 0:
            print("\n🎉 VÝBORNĚ! Projekt je v perfektním stavu!")
            print("   Můžeš spustit: python main.py")
        elif total_issues < 5:
            print("\n👍 Jen pár oprav potřeba.")
            print("   Zkontroluj soubor OPRAVY_POTREBNE.txt")
        elif total_issues < 20:
            print("\n⚠️  Několik oprav potřeba.")
            print("   Pošli mi soubor OPRAVY_POTREBNE.txt a pomůžu ti opravit.")
        else:
            print("\n🚫 Hodně oprav potřeba!")
            print("   Pošli mi soubor OPRAVY_POTREBNE.txt")
        
        print("\n" + "=" * 70)
    
    # =========================================================================
    # HLAVNÍ SPUŠTĚNÍ
    # =========================================================================
    def run_full_diagnostics(self):
        """Spustí kompletní diagnostiku"""
        print("\n" + "🔍 " * 25)
        print("    MOTOSERVIS DMS - ULTIMÁTNÍ DIAGNOSTIKA")
        print("🔍 " * 25)
        print(f"\n📅 Datum: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print(f"📁 Projekt: {self.project_dir}")
        
        # Spusť všechny kroky
        self.find_python_files()
        self.extract_sql_queries()
        self.analyze_sql_queries()
        
        if self.load_database_structure():
            self.compare_code_vs_database()
        
        self.check_python_errors()
        self.generate_fixes()
        self.export_fixes_to_file()
        self.generate_summary()
        
        # Odpoj databázi
        if self.db:
            self.db.disconnect()


def main():
    diagnostics = UltimateDiagnostics()
    diagnostics.run_full_diagnostics()


if __name__ == "__main__":
    main()
