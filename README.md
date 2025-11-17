# Motoservis DMS - Návod na instalaci a spuštění

## 📋 Co je Motoservis DMS?

Desktopová aplikace pro správu motoservisu - evidence zakázek, zákazníků, vozidel, skladu a další.

## 🛠️ Instalace (KROK ZA KROKEM)

### Krok 1: Instalace Pythonu

1. Stáhněte si Python z: https://www.python.org/downloads/
2. **DŮLEŽITÉ:** Při instalaci zaškrtněte "Add Python to PATH"
3. Nainstalujte Python (doporučená verze 3.11 nebo novější)

### Krok 2: Ověření instalace Pythonu

1. Otevřete příkazový řádek (CMD):
   - Stiskněte Win + R
   - Napište: `cmd`
   - Stiskněte Enter

2. Napište: `python --version`
3. Měli byste vidět něco jako: `Python 3.11.5`

### Krok 3: Stažení aplikace

1. Vytvořte si složku pro aplikaci, například: `C:\MotoservisDMS`
2. Zkopírujte do ní všechny soubory aplikace

### Krok 4: Instalace potřebných balíčků

1. Otevřete příkazový řádek (CMD)
2. Přejděte do složky s aplikací:
   ```
   cd C:\MotoservisDMS
   ```
3. Nainstalujte potřebné balíčky:
   ```
   pip install -r requirements.txt
   ```
4. Počkejte, až se nainstalují všechny balíčky (může to trvat 1-2 minuty)

## 🚀 Spuštění aplikace

### Způsob 1: Přes příkazový řádek

1. Otevřete příkazový řádek (CMD)
2. Přejděte do složky s aplikací:
   ```
   cd C:\MotoservisDMS
   ```
3. Spusťte aplikaci:
   ```
   python main.py
   ```

### Způsob 2: Dvojklik (po prvním spuštění)

1. Vytvořte si zkratku na `main.py`
2. Klikněte pravým tlačítkem → Otevřít v programu → Python

## 📁 Struktura souborů

```
MotoservisDMS/
├── main.py                    # Hlavní spouštěcí soubor - TENTO SPOUŠTĚJTE
├── config.py                  # Konfigurace aplikace
├── database_manager.py        # Správa databáze
├── main_window.py             # Hlavní okno
├── module_dashboard.py        # Modul úvodní stránky
├── requirements.txt           # Seznam potřebných balíčků
├── PROJEKT_INFO.md           # Informace o projektu
├── README.md                 # Tento soubor
└── data/                     # Složka s daty (vytvoří se automaticky)
    ├── database/
    │   └── motoservis.db     # Databáze (vytvoří se automaticky)
    ├── backups/              # Zálohy databáze
    └── exports/              # Exportované soubory
```

## 👤 První přihlášení

Po prvním spuštění se vytvoří výchozí admin účet:
- **Uživatelské jméno:** admin
- **Heslo:** admin

⚠️ **DŮLEŽITÉ:** Po prvním přihlášení si změňte heslo v nastavení!

## ❓ Časté problémy a řešení

### Problem 1: "Python není rozpoznán jako příkaz"
**Řešení:** Python není nainstalován nebo není v PATH. Přeinstalujte Python a zaškrtněte "Add Python to PATH"

### Problem 2: "No module named 'PyQt6'"
**Řešení:** Nenainstalovali jste potřebné balíčky. Spusťte: `pip install -r requirements.txt`

### Problem 3: "Permission denied" při zápisu do databáze
**Řešení:** Ujistěte se, že máte práva zápisu do složky s aplikací

### Problem 4: Aplikace se nespustí
**Řešení:** 
1. Zkontrolujte, že máte Python 3.11 nebo novější
2. Zkontrolujte, že jsou nainstalovány všechny balíčky
3. Otevřete příkazový řádek a spusťte: `python main.py` - uvidíte chybovou hlášku

## 🔄 Aktualizace aplikace

1. Zazálohujte složku `data/` (obsahuje vaši databázi)
2. Nahraďte staré soubory .py novými verzemi
3. Spusťte aplikaci - databáze se automaticky aktualizuje

## 💾 Zálohy

- Zálohy se ukládají do složky `data/backups/`
- Zálohu můžete vytvořit ručně tlačítkem "💾 Záloha" v aplikaci
- Automatické zálohy lze nastavit v souboru `config.py`

## 📞 Podpora

Pokud máte problémy nebo otázky, zkontrolujte soubor `PROJEKT_INFO.md`

---

**Verze:** 1.0.0  
**Poslední aktualizace:** 10.11.2025
"# DMS" 
