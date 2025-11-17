@echo off
REM Motoservis DMS - Spousteci skript pro Windows
REM Tento soubor slouzi pro jednoduche spusteni aplikace

echo ========================================
echo Motoservis DMS - Spousteni aplikace
echo ========================================
echo.

REM Kontrola Pythonu
python --version >nul 2>&1
if errorlevel 1 (
    echo CHYBA: Python neni nainstalovan!
    echo Prosim nainstalujte Python z https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo Python je nainstalovany - OK
echo.

REM Kontrola balicku
echo Kontrola potrebnych balicku...
pip show PyQt6 >nul 2>&1
if errorlevel 1 (
    echo PyQt6 neni nainstalovany. Instaluji potrebne balicky...
    pip install -r requirements.txt
    echo.
)

echo Spoustim aplikaci...
echo.

REM Spusteni aplikace
python main.py

REM Pokud dojde k chybe, pauza
if errorlevel 1 (
    echo.
    echo ========================================
    echo CHYBA pri spusteni aplikace!
    echo ========================================
    echo.
    pause
)
