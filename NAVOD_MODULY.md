# Jak přidat nový modul do aplikace

## 📝 Postup krok za krokem

### Krok 1: Vytvoření souboru modulu

1. Vytvořte nový soubor s názvem `module_NAZEV.py` (např. `module_vehicles.py`)
2. Zkopírujte obsah souboru `module_customers.py` jako šablonu
3. Upravte název třídy a obsah podle potřeby

### Krok 2: Úprava souboru main.py

V souboru `main.py` proveďte tyto změny:

**A) Přidejte import na začátek souboru:**
```python
from module_vehicles import VehiclesModule  # Nový modul
```

**B) Přidejte registraci modulu do funkce main():**
```python
# Vozidla
vehicles = VehiclesModule()
window.add_module("vehicles", vehicles)
```

### Krok 3: Ověření v config.py

Zkontrolujte, že váš modul je v seznamu MODULES v souboru `config.py`:
```python
MODULES = [
    {"id": "vehicles", "name": "Vozidla", "icon": "🚗"},
    # ... další moduly
]
```

## 🎯 Struktura modulu (template)

Každý modul by měl obsahovat:

```python
# -*- coding: utf-8 -*-
"""
Modul NÁZEV - Popis modulu
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, ...)
from PyQt6.QtCore import Qt
import config
from database_manager import db


class NazevModule(QWidget):
    """Třída modulu"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Inicializace rozhraní"""
        layout = QVBoxLayout(self)
        # ... zde vytvoříte rozhraní
        
    def refresh(self):
        """Obnovení dat - volá se při přepnutí na modul"""
        # ... zde načtete data z databáze
        pass
```

## 🔑 Důležité metody

### refresh()
- Volá se automaticky při přepnutí na modul
- Zde načítáte aktuální data z databáze
- Měla by být v každém modulu

### init_ui()
- Vytváření uživatelského rozhraní
- Nastavení layoutů, tlačítek, tabulek atd.

## 📋 Příklad: Modul Vozidla

```python
from module_customers import CustomersModule  # Jako šablona

class VehiclesModule(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. Horní panel s tlačítky
        top_panel = self.create_top_panel()
        layout.addWidget(top_panel)
        
        # 2. Tabulka s daty
        self.table = self.create_table()
        layout.addWidget(self.table)
        
        # 3. Načtení dat
        self.refresh()
        
    def create_top_panel(self):
        # Tlačítka: Nové, Upravit, Smazat, Obnovit
        pass
        
    def create_table(self):
        # Tabulka se sloupci
        pass
        
    def refresh(self):
        # Načíst vozidla z databáze
        vehicles = db.fetch_all("SELECT * FROM vehicles")
        # Naplnit tabulku
        pass
```

## ✅ Checklist pro nový modul

- [ ] Vytvořen soubor `module_NAZEV.py`
- [ ] Přidán import do `main.py`
- [ ] Registrován v `main.py` pomocí `window.add_module()`
- [ ] Existuje v seznamu MODULES v `config.py`
- [ ] Má metodu `refresh()`
- [ ] Má metodu `init_ui()`
- [ ] Má tabulku nebo zobrazení dat
- [ ] Má tlačítka pro CRUD operace (Create, Read, Update, Delete)
- [ ] Otestován po spuštění

## 🎨 Tipy pro vzhled

```python
# Barvy z config.py
config.COLOR_PRIMARY    # Hlavní barva
config.COLOR_SECONDARY  # Vedlejší barva
config.COLOR_SUCCESS    # Zelená (úspěch)
config.COLOR_WARNING    # Oranžová (varování)
config.COLOR_DANGER     # Červená (smazání)

# Stylování tlačítka
btn.setStyleSheet(f"background-color: {config.COLOR_SUCCESS};")
```

## 📚 Užitečné příklady kódu

### Načtení dat z databáze
```python
def refresh(self):
    items = db.fetch_all("SELECT * FROM table_name ORDER BY column")
    
    self.table.setRowCount(0)
    for item in items:
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(item['id'])))
```

### Dialog pro přidání/úpravu
```python
def add_item(self):
    dialog = ItemDialog(self)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        data = dialog.get_data()
        db.execute_query("INSERT INTO table ...", data)
        self.refresh()
```

### Vyhledávání
```python
def search_items(self):
    search_text = self.search_input.text().lower()
    for row in range(self.table.rowCount()):
        show = False
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item and search_text in item.text().lower():
                show = True
                break
        self.table.setRowHidden(row, not show)
```

---

**Tip:** Vždy začněte zkopírováním `module_customers.py` a upravte podle potřeby!
