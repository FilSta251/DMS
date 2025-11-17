# -*- coding: utf-8 -*-
"""
České formátování pro Motoservis DMS
Částky, data, čísla, telefony, IČO, DIČ
"""

from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import Union, Optional
import re


class CzechFormatter:
    """
    České formátování pro faktury, reporty a UI
    """

    @staticmethod
    def format_currency(amount: Union[float, Decimal, int, None],
                       with_symbol: bool = True,
                       decimals: int = 2) -> str:
        """
        Formátování částky v českém formátu

        Args:
            amount: Částka (může být None)
            with_symbol: True = přidat "Kč"
            decimals: Počet desetinných míst (0, 2)

        Returns:
            str: "1 234,56 Kč" nebo "1 234,56"

        Example:
            >>> CzechFormatter.format_currency(1234.56)
            '1 234,56 Kč'
            >>> CzechFormatter.format_currency(1234, with_symbol=False, decimals=0)
            '1 234'
        """
        if amount is None:
            return "0,00 Kč" if with_symbol else "0,00"

        # Převod na Decimal pro přesnost
        amount_decimal = Decimal(str(amount))

        # Formátování
        if decimals == 0:
            formatted = f"{amount_decimal:,.0f}".replace(",", " ")
        else:
            formatted = f"{amount_decimal:,.{decimals}f}".replace(",", " ").replace(".", ",")

        # Přidání měny
        if with_symbol:
            return f"{formatted} Kč"

        return formatted

    @staticmethod
    def format_date(date_obj: Union[date, datetime, str, None],
                   format_type: str = "short") -> str:
        """
        Formátování data v českém formátu

        Args:
            date_obj: Datum (date, datetime, string YYYY-MM-DD, nebo None)
            format_type:
                - "short": 15.11.2025
                - "long": 15. listopadu 2025
                - "iso": 2025-11-15
                - "month_year": Listopad 2025

        Returns:
            str: Formátované datum

        Example:
            >>> CzechFormatter.format_date(date(2025, 11, 15))
            '15.11.2025'
        """
        if date_obj is None:
            return "-"

        # Převod na date objekt
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
            except:
                return date_obj
        elif isinstance(date_obj, datetime):
            date_obj = date_obj.date()

        # Formátování
        if format_type == "short":
            return date_obj.strftime("%d.%m.%Y")

        elif format_type == "long":
            months = {
                1: "ledna", 2: "února", 3: "března", 4: "dubna",
                5: "května", 6: "června", 7: "července", 8: "srpna",
                9: "září", 10: "října", 11: "listopadu", 12: "prosince"
            }
            return f"{date_obj.day}. {months[date_obj.month]} {date_obj.year}"

        elif format_type == "iso":
            return date_obj.strftime("%Y-%m-%d")

        elif format_type == "month_year":
            months = {
                1: "Leden", 2: "Únor", 3: "Březen", 4: "Duben",
                5: "Květen", 6: "Červen", 7: "Červenec", 8: "Srpen",
                9: "Září", 10: "Říjen", 11: "Listopad", 12: "Prosinec"
            }
            return f"{months[date_obj.month]} {date_obj.year}"

        return date_obj.strftime("%d.%m.%Y")

    @staticmethod
    def format_datetime(datetime_obj: Union[datetime, str, None],
                       with_seconds: bool = False) -> str:
        """
        Formátování data a času

        Args:
            datetime_obj: Datum a čas
            with_seconds: True = zobrazit sekundy

        Returns:
            str: "15.11.2025 14:30" nebo "15.11.2025 14:30:45"

        Example:
            >>> CzechFormatter.format_datetime(datetime(2025, 11, 15, 14, 30))
            '15.11.2025 14:30'
        """
        if datetime_obj is None:
            return "-"

        # Převod na datetime objekt
        if isinstance(datetime_obj, str):
            try:
                datetime_obj = datetime.fromisoformat(datetime_obj)
            except:
                return datetime_obj

        # Formátování
        if with_seconds:
            return datetime_obj.strftime("%d.%m.%Y %H:%M:%S")
        else:
            return datetime_obj.strftime("%d.%m.%Y %H:%M")

    @staticmethod
    def format_time(time_obj: Union[datetime, str, None]) -> str:
        """
        Formátování pouze času

        Args:
            time_obj: Čas

        Returns:
            str: "14:30"

        Example:
            >>> CzechFormatter.format_time(datetime(2025, 11, 15, 14, 30))
            '14:30'
        """
        if time_obj is None:
            return "-"

        if isinstance(time_obj, str):
            try:
                time_obj = datetime.fromisoformat(time_obj)
            except:
                return time_obj

        return time_obj.strftime("%H:%M")

    @staticmethod
    def format_phone(phone: Optional[str],
                    international: bool = False) -> str:
        """
        Formátování telefonního čísla

        Args:
            phone: Telefon (např. "123456789" nebo "+420123456789")
            international: True = přidat +420

        Returns:
            str: "123 456 789" nebo "+420 123 456 789"

        Example:
            >>> CzechFormatter.format_phone("123456789")
            '123 456 789'
            >>> CzechFormatter.format_phone("123456789", international=True)
            '+420 123 456 789'
        """
        if not phone:
            return "-"

        # Odstranění mezer a speciálních znaků
        phone_clean = re.sub(r'[^\d+]', '', phone)

        # Odstranění +420 pro normalizaci
        if phone_clean.startswith("+420"):
            phone_clean = phone_clean[4:]
        elif phone_clean.startswith("00420"):
            phone_clean = phone_clean[5:]

        # Formátování po trojicích
        if len(phone_clean) == 9:
            formatted = f"{phone_clean[0:3]} {phone_clean[3:6]} {phone_clean[6:9]}"
        else:
            formatted = phone_clean

        # Přidání +420
        if international:
            return f"+420 {formatted}"

        return formatted

    @staticmethod
    def format_ico(ico: Optional[str]) -> str:
        """
        Formátování IČO

        Args:
            ico: IČO (8 číslic)

        Returns:
            str: "12345678" (bez formátování, jen validace)

        Example:
            >>> CzechFormatter.format_ico("12345678")
            '12345678'
        """
        if not ico:
            return "-"

        ico_clean = re.sub(r'\D', '', ico)

        if len(ico_clean) == 8:
            return ico_clean

        return ico

    @staticmethod
    def format_dic(dic: Optional[str]) -> str:
        """
        Formátování DIČ

        Args:
            dic: DIČ (CZ12345678)

        Returns:
            str: "CZ12345678"

        Example:
            >>> CzechFormatter.format_dic("12345678")
            'CZ12345678'
            >>> CzechFormatter.format_dic("CZ12345678")
            'CZ12345678'
        """
        if not dic:
            return "-"

        dic_clean = dic.upper().strip()

        # Přidání CZ pokud chybí
        if not dic_clean.startswith("CZ"):
            dic_clean = f"CZ{dic_clean}"

        return dic_clean

    @staticmethod
    def format_number(number: Union[int, float, Decimal, None],
                     decimals: int = 2,
                     with_spaces: bool = True) -> str:
        """
        Formátování čísla (bez měny)

        Args:
            number: Číslo
            decimals: Desetinná místa
            with_spaces: True = tisícové oddělovače

        Returns:
            str: "1 234,56" nebo "1234.56"

        Example:
            >>> CzechFormatter.format_number(1234.56)
            '1 234,56'
        """
        if number is None:
            return "0"

        number_decimal = Decimal(str(number))

        if decimals == 0:
            formatted = f"{number_decimal:,.0f}"
        else:
            formatted = f"{number_decimal:,.{decimals}f}"

        if with_spaces:
            formatted = formatted.replace(",", " ").replace(".", ",")

        return formatted

    @staticmethod
    def format_percentage(value: Union[float, Decimal, None],
                         decimals: int = 2) -> str:
        """
        Formátování procent

        Args:
            value: Hodnota (např. 15.5 = 15.5%)
            decimals: Desetinná místa

        Returns:
            str: "15,50 %"

        Example:
            >>> CzechFormatter.format_percentage(15.5)
            '15,50 %'
        """
        if value is None:
            return "0,00 %"

        value_decimal = Decimal(str(value))
        formatted = f"{value_decimal:.{decimals}f}".replace(".", ",")

        return f"{formatted} %"

    @staticmethod
    def format_license_plate(plate: Optional[str]) -> str:
        """
        Formátování SPZ (státní poznávací značky)

        Args:
            plate: SPZ (např. "1A23456")

        Returns:
            str: "1A2 3456"

        Example:
            >>> CzechFormatter.format_license_plate("1A23456")
            '1A2 3456'
        """
        if not plate:
            return "-"

        plate_clean = plate.upper().replace(" ", "")

        # České SPZ formát: 1A2 3456
        if len(plate_clean) == 7 and plate_clean[0].isdigit():
            return f"{plate_clean[0:3]} {plate_clean[3:]}"

        return plate_clean

    @staticmethod
    def format_vin(vin: Optional[str]) -> str:
        """
        Formátování VIN (17 znaků)

        Args:
            vin: VIN kód

        Returns:
            str: VIN uppercase

        Example:
            >>> CzechFormatter.format_vin("wbadt43452g123456")
            'WBADT43452G123456'
        """
        if not vin:
            return "-"

        return vin.upper().strip()

    @staticmethod
    def parse_czech_number(text: str) -> Union[Decimal, None]:
        """
        Parsování českého čísla na Decimal

        Args:
            text: "1 234,56" nebo "1234.56"

        Returns:
            Decimal nebo None

        Example:
            >>> CzechFormatter.parse_czech_number("1 234,56")
            Decimal('1234.56')
        """
        if not text:
            return None

        try:
            # Odstranění mezer
            text_clean = text.replace(" ", "")
            # Nahrazení české čárky za tečku
            text_clean = text_clean.replace(",", ".")
            # Odstranění měny
            text_clean = re.sub(r'[^\d.]', '', text_clean)

            return Decimal(text_clean)
        except:
            return None

    @staticmethod
    def format_age(birth_date: Union[date, datetime, str, None]) -> str:
        """
        Výpočet a formátování věku

        Args:
            birth_date: Datum narození

        Returns:
            str: "25 let" nebo "5 měsíců"

        Example:
            >>> CzechFormatter.format_age(date(2000, 1, 1))
            '25 let'
        """
        if birth_date is None:
            return "-"

        # Převod na date
        if isinstance(birth_date, str):
            try:
                birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
            except:
                return "-"
        elif isinstance(birth_date, datetime):
            birth_date = birth_date.date()

        today = date.today()
        age_years = today.year - birth_date.year

        # Kontrola zda už měl letos narozeniny
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age_years -= 1

        if age_years == 1:
            return "1 rok"
        elif 2 <= age_years <= 4:
            return f"{age_years} roky"
        else:
            return f"{age_years} let"

    @staticmethod
    def format_relative_date(date_obj: Union[date, datetime, str, None]) -> str:
        """
        Relativní formátování data

        Args:
            date_obj: Datum

        Returns:
            str: "Dnes", "Včera", "Za 3 dny", "Před 2 dny"

        Example:
            >>> CzechFormatter.format_relative_date(date.today())
            'Dnes'
        """
        if date_obj is None:
            return "-"

        # Převod na date
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
            except:
                return date_obj
        elif isinstance(date_obj, datetime):
            date_obj = date_obj.date()

        today = date.today()
        delta = (date_obj - today).days

        if delta == 0:
            return "Dnes"
        elif delta == 1:
            return "Zítra"
        elif delta == -1:
            return "Včera"
        elif delta > 0:
            if delta <= 7:
                return f"Za {delta} dny" if 2 <= delta <= 4 else f"Za {delta} dní"
            else:
                return CzechFormatter.format_date(date_obj, "short")
        else:  # delta < 0
            abs_delta = abs(delta)
            if abs_delta <= 7:
                return f"Před {abs_delta} dny" if 2 <= abs_delta <= 4 else f"Před {abs_delta} dny"
            else:
                return CzechFormatter.format_date(date_obj, "short")


# ============================================
# ZKRATKY (pro časté použití)
# ============================================

def fmt_czk(amount: Union[float, Decimal, None]) -> str:
    """Zkratka: formátovat částku v Kč"""
    return CzechFormatter.format_currency(amount)


def fmt_date(date_obj: Union[date, datetime, str, None]) -> str:
    """Zkratka: formátovat datum"""
    return CzechFormatter.format_date(date_obj)


def fmt_datetime(datetime_obj: Union[datetime, str, None]) -> str:
    """Zkratka: formátovat datum a čas"""
    return CzechFormatter.format_datetime(datetime_obj)


def fmt_phone(phone: Optional[str]) -> str:
    """Zkratka: formátovat telefon"""
    return CzechFormatter.format_phone(phone)


# ============================================
# TESTY
# ============================================

if __name__ == "__main__":
    print("=== TEST ČESKÉHO FORMÁTOVÁNÍ ===\n")

    # Test 1: Částka
    print("Test 1: Formátování částky")
    result = CzechFormatter.format_currency(1234567.89)
    print(f"1234567.89 → {result}")
    assert result == "1 234 567,89 Kč"
    print("✅ OK\n")

    # Test 2: Datum
    print("Test 2: Formátování data")
    result = CzechFormatter.format_date(date(2025, 11, 15))
    print(f"2025-11-15 → {result}")
    assert result == "15.11.2025"
    print("✅ OK\n")

    # Test 3: Telefon
    print("Test 3: Formátování telefonu")
    result = CzechFormatter.format_phone("123456789")
    print(f"123456789 → {result}")
    assert result == "123 456 789"
    print("✅ OK\n")

    # Test 4: SPZ
    print("Test 4: Formátování SPZ")
    result = CzechFormatter.format_license_plate("1A23456")
    print(f"1A23456 → {result}")
    assert result == "1A2 3456"
    print("✅ OK\n")

    # Test 5: Parsování českého čísla
    print("Test 5: Parsování českého čísla")
    result = CzechFormatter.parse_czech_number("1 234,56 Kč")
    print(f"'1 234,56 Kč' → {result}")
    assert result == Decimal("1234.56")
    print("✅ OK\n")

    print("=== VŠECHNY TESTY PROŠLY ✅ ===")
