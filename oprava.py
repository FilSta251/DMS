# -*- coding: utf-8 -*-
"""
FINÁLNÍ OPRAVA USERS - Synchronizace dat
=========================================
"""

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from database_manager import db


def main():
    print("=" * 70)
    print(" FINÁLNÍ OPRAVA USERS")
    print("=" * 70)

    if not db.connect():
        print("❌ Nelze se připojit!")
        return

    # Zjisti aktuální strukturu
    print("\n⏳ Kontroluji strukturu...")
    cols = db.fetch_all("PRAGMA table_info(users)")
    col_names = [c['name'] for c in cols]
    print(f"   Sloupce: {', '.join(sorted(col_names))}")

    # Zkontroluj jestli máme data
    print("\n⏳ Kontroluji uživatele...")
    users = db.fetch_all("SELECT * FROM users")
    print(f"   Počet uživatelů: {len(users)}")

    if len(users) == 0:
        print("\n⚠️  ŽÁDNÍ UŽIVATELÉ! Vytvářím admin účet...")

        # Vytvoř admin účet
        db.cursor.execute("""
            INSERT INTO users (username, password, first_name, last_name, role, active, email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ('admin', 'admin', 'Admin', 'Systému', 'admin', 1, ''))

        db.connection.commit()
        print("✅ Admin účet vytvořen (admin/admin)")
    else:
        # Zobraz uživatele
        for user_row in users:
            user = dict(user_row)
            print(f"\n   ID: {user.get('id')}")
            print(f"   Username: {user.get('username')}")
            print(f"   First name: {user.get('first_name', 'PRÁZDNÉ')}")
            print(f"   Last name: {user.get('last_name', 'PRÁZDNÉ')}")
            print(f"   Role: {user.get('role')}")
            print(f"   Active: {user.get('active')}")

            # Pokud je jméno prázdné, nastav výchozí
            if not user.get('first_name'):
                print(f"   ⚠️  Prázdné jméno - nastavuji na 'Admin'")
                db.cursor.execute("""
                    UPDATE users
                    SET first_name = 'Admin', last_name = 'Systému'
                    WHERE id = ?
                """, (user['id'],))

    # Přidej full_name jako computed sloupec (pro kompatibilitu)
    print("\n⏳ Přidávám full_name pro zpětnou kompatibilitu...")

    if 'full_name' not in col_names:
        db._ensure_columns("users", [
            ("full_name", "TEXT"),
        ])

        # Synchronizuj full_name = first_name + ' ' + last_name
        db.cursor.execute("""
            UPDATE users
            SET full_name = TRIM(COALESCE(first_name, '') || ' ' || COALESCE(last_name, ''))
        """)
        print("✅ full_name přidán a synchronizován")
    else:
        print("✅ full_name už existuje")

    db.connection.commit()

    # Finální kontrola
    print("\n📊 FINÁLNÍ STAV:")
    users = db.fetch_all("SELECT id, username, first_name, last_name, full_name, role, active FROM users")
    for user_row in users:
        user = dict(user_row)
        status = "✅" if user.get('active') else "❌"
        print(f"   {user['id']}: {user['username']} - {user.get('first_name', '')} {user.get('last_name', '')} (full: {user.get('full_name', '')}) [{user['role']}] {status}")

    db.disconnect()

    print("\n" + "=" * 70)
    print(" ✅ HOTOVO!")
    print("=" * 70)
    print("\nSpusť: python main.py")
    print("Přihlášení: admin / admin")


if __name__ == "__main__":
    main()
