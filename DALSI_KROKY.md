# 🎉 MOTOSERVIS DMS - ZÁKLADNÍ KOSTRA HOTOVA!

## ✅ Co je hotovo

### 1. Základní struktura aplikace
- ✅ Hlavní okno s navigací
- ✅ Modulární systém
- ✅ Databázový systém (SQLite)
- ✅ Konfigurace
- ✅ Systém zálohování

### 2. Hotové moduly
- ✅ **Dashboard** - Úvodní stránka s přehledem statistik
- ✅ **Zákazníci** - Kompletní CRUD modul (Create, Read, Update, Delete)

### 3. Databáze
- ✅ Všechny tabulky vytvořeny
- ✅ Relace mezi tabulkami nastaveny
- ✅ Základní data naplněna
- ✅ Výchozí admin účet vytvořen

### 4. Dokumentace
- ✅ PROJEKT_INFO.md - Kompletní informace o projektu
- ✅ README.md - Návod na instalaci a spuštění
- ✅ NAVOD_MODULY.md - Jak přidat nové moduly
- ✅ DALSI_KROKY.md - Tento soubor

## 📂 Struktura souborů

```
MotoservisDMS/
│
├── main.py                    ⭐ HLAVNÍ SOUBOR - TENTO SPOUŠTĚJTE
├── config.py                  Konfigurace aplikace
├── database_manager.py        Správa databáze
├── main_window.py             Hlavní okno s navigací
├── module_dashboard.py        Modul: Úvodní stránka
├── module_customers.py        Modul: Zákazníci (VZOROVÝ)
│
├── requirements.txt           Seznam potřebných balíčků
├── spustit.bat               Batch soubor pro Windows
│
├── PROJEKT_INFO.md           📖 Kompletní info o projektu
├── README.md                 📖 Návod na instalaci
├── NAVOD_MODULY.md          📖 Jak přidat nové moduly
├── DALSI_KROKY.md           📖 Tento soubor
│
└── data/                      📁 Složka s daty (vytvoří se automaticky)
    ├── database/
    │   └── motoservis.db     Databáze
    ├── backups/              Zálohy
    └── exports/              Exporty
```

## 🚀 Jak spustit aplikaci (stručně)

### Windows:
1. Nainstalujte Python 3.11+ z https://www.python.org/downloads/
2. Otevřete příkazový řádek (CMD)
3. Přejděte do složky: `cd C:\cesta\k\MotoservisDMS`
4. Nainstalujte balíčky: `pip install -r requirements.txt`
5. Spusťte: `python main.py`

**NEBO** jednoduše dvojklik na `spustit.bat`

### První přihlášení:
- Uživatel: **admin**
- Heslo: **admin**

## 📝 Co zbývá udělat - Další moduly

### 1. Modul Vozidla (module_vehicles.py)
**Co bude obsahovat:**
- Seznam vozidel s SPZ, značkou, modelem
- Propojení se zákazníky
- Historie oprav vozidla
- Stav kilometrů

**Jak vytvořit:**
- Zkopírujte `module_customers.py`
- Přejmenujte na `module_vehicles.py`
- Upravte podle databázové tabulky `vehicles`
- Přidejte do `main.py`

### 2. Modul Zakázky (module_orders.py)
**Co bude obsahovat:**
- Seznam zakázek s čísly
- Stavy: nová, rozpracovaná, čeká na součástky, hotová, archiv
- Propojení se zákazníkem a vozidlem
- Kalkulace ceny (práce + díly)
- Export do PDF

**Důležité funkce:**
- Vytvoření nové zakázky
- Přidání dílů ze skladu
- Změna stavu zakázky
- Tisk/export zakázky

### 3. Modul Sklad (module_warehouse.py)
**Co bude obsahovat:**
- Seznam dílů a materiálu
- Stavy skladem
- Upozornění na minimum
- Nákupní a prodejní cena

**Důležité funkce:**
- Příjem na sklad
- Výdej ze skladu
- Inventura
- Export seznamu

### 4. Modul Administrativa (module_administration.py)
**Co bude obsahovat:**
- Faktury
- Dokumenty
- Účetní přehledy
- Export do PDF a Excel

### 5. Modul Číselníky (module_codebooks.py)
**Co bude obsahovat:**
- Značky vozidel
- Typy oprav
- Jednotky
- Měny

### 6. Modul Půjčovna (module_rental.py)
**Co bude obsahovat:**
- Půjčená vozidla
- Zálohy
- Vratky
- Přehledy

### 7. Modul Kalendář (module_calendar.py)
**Co bude obsahovat:**
- Naplánované servisní termíny
- Připomínky
- Přehled obsazenosti

### 8. Modul Nastavení (module_settings.py)
**Co bude obsahovat:**
- Údaje o firmě
- Nastavení aplikace
- Zálohy
- Import/Export

### 9. Modul Uživatelé (module_users.py)
**Co bude obsahovat:**
- Správa uživatelů
- Role a oprávnění
- Historie přihlášení

## 🎯 Doporučený postup implementace

### Fáze 1 - Základní funkce (nejdříve implementovat)
1. ✅ Dashboard (HOTOVO)
2. ✅ Zákazníci (HOTOVO)
3. ⬜ Vozidla
4. ⬜ Zakázky
5. ⬜ Sklad

### Fáze 2 - Rozšířené funkce
6. ⬜ Číselníky
7. ⬜ Kalendář
8. ⬜ Nastavení

### Fáze 3 - Pokročilé funkce
9. ⬜ Administrativa
10. ⬜ Půjčovna
11. ⬜ Uživatelé

## 💡 Tipy pro rychlý vývoj

### Jak postupovat:
1. **Vždy začněte zkopírováním `module_customers.py`**
2. Přejmenujte soubor na `module_NAZEV.py`
3. Změňte název třídy
4. Upravte sloupce tabulky podle databáze
5. Upravte formulář pro přidání/úpravu
6. Přidejte do `main.py`

### Použijte vzorový modul:
```python
# 1. Zkopírujte module_customers.py → module_vehicles.py
# 2. Změňte CustomersModule → VehiclesModule
# 3. Změňte "customers" → "vehicles" v SQL dotazech
# 4. Upravte sloupce tabulky
# 5. Hotovo!
```

## 🔧 Časté úpravy

### Změna barev:
Soubor: `config.py`
```python
COLOR_PRIMARY = "#2c3e50"      # Tmavě modrá
COLOR_SECONDARY = "#3498db"    # Světle modrá
COLOR_SUCCESS = "#27ae60"      # Zelená
```

### Přidání nového pole do databáze:
1. Upravte `database_manager.py` - metodu `create_tables()`
2. Přidejte sloupec do tabulky
3. Smažte `data/database/motoservis.db`
4. Spusťte aplikaci - databáze se vytvoří znovu

### Export do PDF:
```python
from reportlab.pdfgen import canvas

def export_to_pdf(filename, data):
    c = canvas.Canvas(filename)
    c.drawString(100, 750, "Motoservis DMS")
    # ... další obsah
    c.save()
```

## 📞 Pokud něco nefunguje

### Kontrolní seznam:
1. ⬜ Je nainstalován Python 3.11+?
2. ⬜ Jsou nainstalovány všechny balíčky? (`pip install -r requirements.txt`)
3. ⬜ Jste ve správné složce?
4. ⬜ Existuje složka `data/`?
5. ⬜ Máte práva zápisu do složky?

### Časté chyby:
- **"No module named 'PyQt6'"** → `pip install PyQt6`
- **"Permission denied"** → Spusťte jako administrátor
- **Aplikace se nespustí** → `python main.py` v CMD zobrazí chybu

## 🎓 Co se naučíte

Během implementace dalších modulů se naučíte:
- Práci s PyQt6 (GUI)
- SQL dotazy
- Práci s formuláři
- Export dat (PDF, Excel)
- Strukturování kódu
- Validaci dat

## 📚 Užitečné odkazy

- PyQt6 dokumentace: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- SQLite dokumentace: https://www.sqlite.org/docs.html
- Python dokumentace: https://docs.python.org/3/

## ✨ Důležité soubory k prostudování

1. **PROJEKT_INFO.md** - Kompletní informace o projektu
2. **README.md** - Návod na instalaci
3. **NAVOD_MODULY.md** - Jak přidat nové moduly
4. **module_customers.py** - VZOROVÝ modul pro kopírování

## 🎉 Gratulujeme!

Základní kostra aplikace je hotová a funkční. Nyní můžete začít přidávat další moduly podle potřeby.

**Doporučený první krok:** Implementujte modul Vozidla zkopírováním modulu Zákazníci.

---

**Vytvořeno:** 10.11.2025  
**Verze:** 1.0.0  
**Status:** ✅ Základní kostra funkční
