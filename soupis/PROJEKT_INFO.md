# MOTOSERVIS DMS - Informace o projektu

## Základní informace
**Název:** Motoservis DMS (Desktop Management System)
**Jazyk:** Python
**Typ:** Desktopová aplikace pro správu motoservisu
**Uložiště dat:** Lokální PC / NAS
**Inspirace:** DMS, Caris systémy

## Struktura aplikace

### Hlavní moduly:
1. **Úvodní modul** - Hlavní dashboard s přehledem
2. **Vozidlo** - Správa vozidel (evidence, historie oprav)
3. **Zákazník** - Správa klientů a kontaktů
4. **Zakázky** - Zakázky, archiv zakázek, stavy zakázek
5. **Sklad** - Správa dílů a materiálu
6. **Administrativa** - Faktury, dokumenty, účetnictví
7. **Číselníky** - Značky vozidel, typy oprav, ceníky
8. **Půjčovna** - Půjčování náhradních vozidel
9. **Kalendář** - Plánování servisních termínů
10. **Nastavení** - Konfigurace aplikace
11. **Správa uživatelů** - Uživatelské účty a oprávnění

### Kategorizace modulů:
- Každý modul může mít podkategorie (např. Zakázky → Aktivní, Archiv, Rozpracované)
- Moduly komunikují mezi sebou (např. Zakázka potřebuje Zákazníka a Vozidlo)

## Technické řešení

### Použité technologie:
- **GUI Framework:** PyQt6 (moderní, profesionální vzhled)
- **Databáze:** SQLite (lokální, bez serveru, snadno přenositelná)
- **Reporting:** ReportLab (PDF faktury a dokumenty)
- **Excel export:** openpyxl (export dat)
- **Kalendář:** PyQt6 vestavěné komponenty

### Architektura:
```
motoservis_dms/
├── main.py                 # Hlavní spouštěcí soubor
├── config.py               # Konfigurace aplikace
├── database/
│   ├── db_manager.py       # Správa databáze
│   └── models.py           # Datové modely
├── modules/
│   ├── dashboard.py        # Úvodní modul
│   ├── vehicles.py         # Modul Vozidla
│   ├── customers.py        # Modul Zákazníci
│   ├── orders.py           # Modul Zakázky
│   ├── warehouse.py        # Modul Sklad
│   ├── administration.py   # Modul Administrativa
│   ├── codebooks.py        # Modul Číselníky
│   ├── rental.py           # Modul Půjčovna
│   ├── calendar.py         # Modul Kalendář
│   ├── settings.py         # Modul Nastavení
│   └── users.py            # Modul Správa uživatelů
├── ui/
│   ├── main_window.py      # Hlavní okno
│   └── widgets.py          # Vlastní komponenty
└── utils/
    ├── helpers.py          # Pomocné funkce
    └── validators.py       # Validace dat
```

### Důležité vlastnosti:
- **Modulární design** - Snadné přidávání nových modulů
- **Jednotný vzhled** - Všechny moduly mají stejný design
- **Komunikace mezi moduly** - Sdílení dat (např. Zakázka odkazuje na Zákazníka)
- **Filtry a vyhledávání** - V každém modulu
- **Export dat** - Excel, PDF
- **Zálohování** - Automatické zálohy databáze

## Důležité poznámky pro další chaty:

### Co Filip potřebuje:
- **Kompletní funkční kód** - Ne částečné ukázky
- **Detailní instrukce** - Vysvětlit jako "pětiletému"
- **Řešení pomocí free balíčků** - Žádné placené nástroje
- **Česká lokalizace** - Všechny texty v češtině

### Pracovní postup:
1. Vždy poskytovat kompletní soubory, ne jen úryvky
2. Testovat před odesláním
3. Jasně popsat, kam soubory uložit
4. Vysvětlit, jak aplikaci spustit
5. Řešit problémy kompletně, ne částečně

### Aktuální stav projektu:
- **Fáze:** Vytváření základní kostry
- **Co je hotovo:** Základní struktura, databáze, hlavní okno
- **Co zbývá:** Implementace jednotlivých modulů

### Kontakt k databázi:
- Databáze: SQLite soubor `motoservis.db`
- Umístění: Ve složce aplikace
- Automatická migrace: Při prvním spuštění se vytvoří struktura

---

**Poslední aktualizace:** 10.11.2025
**Status:** ✅ Základní kostra vytvořena
