# ⚡ RYCHLÝ START - Motoservis DMS

## 🎯 Co jste získali

### ✅ Funkční aplikaci se základní kostrou
- Hlavní okno s navigací
- Dashboard s přehledem statistik
- Kompletní modul pro správu zákazníků
- Databázový systém
- Systém zálohování

### 📂 Soubory (12 souborů)

#### Spouštěcí soubory:
1. **main.py** ⭐ - Hlavní soubor, tento spouštíte
2. **spustit.bat** - Pro Windows (dvojklik)

#### Konfigurační soubory:
3. **config.py** - Nastavení aplikace (barvy, názvy, cesty)
4. **requirements.txt** - Seznam potřebných balíčků
5. **database_manager.py** - Správa databáze

#### Rozhraní aplikace:
6. **main_window.py** - Hlavní okno a navigace
7. **module_dashboard.py** - Úvodní stránka
8. **module_customers.py** - Modul zákazníci (VZOR pro další moduly)

#### Dokumentace:
9. **README.md** - Návod na instalaci (ZAČNĚTE ZDE)
10. **PROJEKT_INFO.md** - Kompletní info o projektu
11. **NAVOD_MODULY.md** - Jak přidat nové moduly
12. **DALSI_KROKY.md** - Co dělat dál

## 🚀 Jak spustit (3 kroky)

### 1. Nainstalujte Python
- Stáhněte z https://www.python.org/downloads/
- ⚠️ DŮLEŽITÉ: Zaškrtněte "Add Python to PATH"

### 2. Nainstalujte balíčky
Otevřete CMD ve složce s aplikací:
```
pip install -r requirements.txt
```

### 3. Spusťte aplikaci
```
python main.py
```
NEBO dvojklik na `spustit.bat`

## 👤 Přihlášení
- Uživatel: **admin**
- Heslo: **admin**

## 📖 Co si přečíst

### Pro začátek:
1. **README.md** - Detailní návod na instalaci
2. **DALSI_KROKY.md** - Co dělat dál

### Pro pochopení projektu:
3. **PROJEKT_INFO.md** - Kompletní informace

### Pro přidávání modulů:
4. **NAVOD_MODULY.md** - Jak přidat další moduly
5. **module_customers.py** - Vzor pro kopírování

## 🎯 Co udělat dál

### Doporučené pořadí:
1. ✅ Spusťte aplikaci a prozkoumejte ji
2. ⬜ Vytvořte modul Vozidla (zkopírujte module_customers.py)
3. ⬜ Vytvořte modul Zakázky
4. ⬜ Vytvořte modul Sklad
5. ⬜ Přidejte další moduly podle potřeby

## 💡 Důležité poznámky

- **module_customers.py** je VZOR - zkopírujte ho pro další moduly
- Všechny moduly komunikují přes databázi
- Databáze se vytvoří automaticky při prvním spuštění
- Zálohy se ukládají do složky `data/backups/`

## ❓ Problémy?

### Aplikace se nespustí:
```
python main.py
```
V CMD uvidíte chybovou hlášku

### "No module named 'PyQt6'":
```
pip install PyQt6
```

### Další problémy:
Podívejte se do **README.md** - sekce "Časté problémy"

## 🎉 Hotovo!

Máte funkční základní kostru aplikace. Nyní můžete začít přidávat další moduly.

---

**Rychlá pomoc:** Vše najdete v souborech .md (Markdown)  
**První krok:** Přečtěte si README.md
