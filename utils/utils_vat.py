# -*- coding: utf-8 -*-
"""
Kalkulátor DPH pro Motoservis DMS
České sazby DPH: 21%, 12%, 0%
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple, Union


class VATCalculator:
    """
    Kalkulátor DPH s českými sazbami
    Používá Decimal pro přesné finanční výpočty
    """

    # České sazby DPH 2025
    STANDARD_RATE = Decimal("21.0")    # Základní sazba
    REDUCED_RATE = Decimal("12.0")      # Snížená sazba
    ZERO_RATE = Decimal("0.0")          # Osvobozeno

    @staticmethod
    def calculate_vat(amount_without_vat: Union[float, Decimal],
                      vat_rate: Union[float, Decimal]) -> Decimal:
        """
        Výpočet DPH z částky bez DPH

        Args:
            amount_without_vat: Částka bez DPH
            vat_rate: Sazba DPH (21, 12, 0)

        Returns:
            Decimal: Vypočtené DPH

        Example:
            >>> VATCalculator.calculate_vat(1000, 21)
            Decimal('210.00')
        """
        amount = Decimal(str(amount_without_vat))
        rate = Decimal(str(vat_rate))

        vat = (amount * rate / Decimal("100")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        return vat

    @staticmethod
    def add_vat(amount_without_vat: Union[float, Decimal],
                vat_rate: Union[float, Decimal]) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Přidání DPH k částce (ze základu do prodejní ceny)

        Args:
            amount_without_vat: Částka bez DPH
            vat_rate: Sazba DPH (21, 12, 0)

        Returns:
            Tuple: (základ bez DPH, DPH, celkem s DPH)

        Example:
            >>> VATCalculator.add_vat(1000, 21)
            (Decimal('1000.00'), Decimal('210.00'), Decimal('1210.00'))
        """
        amount = Decimal(str(amount_without_vat)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        vat = VATCalculator.calculate_vat(amount, vat_rate)
        total = amount + vat

        return (amount, vat, total)

    @staticmethod
    def remove_vat(amount_with_vat: Union[float, Decimal],
                   vat_rate: Union[float, Decimal]) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Odstranění DPH z částky (z prodejní ceny na základ)

        Args:
            amount_with_vat: Částka s DPH
            vat_rate: Sazba DPH (21, 12, 0)

        Returns:
            Tuple: (základ bez DPH, DPH, celkem s DPH)

        Example:
            >>> VATCalculator.remove_vat(1210, 21)
            (Decimal('1000.00'), Decimal('210.00'), Decimal('1210.00'))
        """
        total = Decimal(str(amount_with_vat))
        rate = Decimal(str(vat_rate))

        if rate == Decimal("0"):
            return (total, Decimal("0.00"), total)

        # Výpočet základu: základ = celkem / (1 + sazba/100)
        base = (total / (Decimal("1") + rate / Decimal("100"))).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        vat = (total - base).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        return (base, vat, total)

    @staticmethod
    def calculate_margin(purchase_price: Union[float, Decimal],
                        selling_price: Union[float, Decimal],
                        return_percentage: bool = True) -> Union[Decimal, float]:
        """
        Výpočet marže (obchodní přirážky)

        Args:
            purchase_price: Nákupní cena
            selling_price: Prodejní cena
            return_percentage: True = vrátit procenta, False = vrátit částku

        Returns:
            Decimal nebo float: Marže v Kč nebo %

        Example:
            >>> VATCalculator.calculate_margin(1000, 1500)
            Decimal('50.00')  # 50%
            >>> VATCalculator.calculate_margin(1000, 1500, False)
            Decimal('500.00')  # 500 Kč
        """
        purchase = Decimal(str(purchase_price))
        selling = Decimal(str(selling_price))

        if purchase == 0:
            return Decimal("0.00")

        margin_amount = selling - purchase

        if return_percentage:
            margin_percent = (margin_amount / purchase * Decimal("100")).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )
            return margin_percent
        else:
            return margin_amount.quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )

    @staticmethod
    def calculate_price_with_margin(purchase_price: Union[float, Decimal],
                                   margin_percent: Union[float, Decimal]) -> Decimal:
        """
        Výpočet prodejní ceny s marží

        Args:
            purchase_price: Nákupní cena
            margin_percent: Marže v procentech (např. 50 = +50%)

        Returns:
            Decimal: Prodejní cena

        Example:
            >>> VATCalculator.calculate_price_with_margin(1000, 50)
            Decimal('1500.00')  # +50% = 1500 Kč
        """
        purchase = Decimal(str(purchase_price))
        margin = Decimal(str(margin_percent))

        selling = (purchase * (Decimal("1") + margin / Decimal("100"))).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        return selling

    @staticmethod
    def split_vat_by_rates(items: list) -> dict:
        """
        Rozdělení položek podle sazeb DPH (pro faktury)

        Args:
            items: List položek, každá má:
                   {'amount_without_vat': float, 'vat_rate': float}

        Returns:
            dict: Rozděleno podle sazeb
                {
                    '21': {'base': Decimal, 'vat': Decimal, 'total': Decimal},
                    '12': {...},
                    '0': {...}
                }

        Example:
            >>> items = [
            ...     {'amount_without_vat': 1000, 'vat_rate': 21},
            ...     {'amount_without_vat': 500, 'vat_rate': 21},
            ...     {'amount_without_vat': 300, 'vat_rate': 12}
            ... ]
            >>> VATCalculator.split_vat_by_rates(items)
            {
                '21': {'base': Decimal('1500.00'), 'vat': Decimal('315.00'), 'total': Decimal('1815.00')},
                '12': {'base': Decimal('300.00'), 'vat': Decimal('36.00'), 'total': Decimal('336.00')}
            }
        """
        result = {}

        for item in items:
            amount = Decimal(str(item['amount_without_vat']))
            rate = str(int(Decimal(str(item['vat_rate']))))

            if rate not in result:
                result[rate] = {
                    'base': Decimal("0.00"),
                    'vat': Decimal("0.00"),
                    'total': Decimal("0.00")
                }

            base, vat, total = VATCalculator.add_vat(amount, item['vat_rate'])

            result[rate]['base'] += base
            result[rate]['vat'] += vat
            result[rate]['total'] += total

        # Zaokrouhlení
        for rate in result:
            result[rate]['base'] = result[rate]['base'].quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            result[rate]['vat'] = result[rate]['vat'].quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            result[rate]['total'] = result[rate]['total'].quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        return result

    @staticmethod
    def format_vat_summary(vat_by_rates: dict) -> str:
        """
        Formátování DPH přehledu pro faktury

        Args:
            vat_by_rates: Výstup z split_vat_by_rates()

        Returns:
            str: Formátovaný text
        """
        lines = ["DPH REKAPITULACE:"]
        lines.append("-" * 60)

        total_base = Decimal("0.00")
        total_vat = Decimal("0.00")
        total_amount = Decimal("0.00")

        for rate in sorted(vat_by_rates.keys(), key=lambda x: int(x), reverse=True):
            data = vat_by_rates[rate]
            lines.append(
                f"Sazba {rate}%: "
                f"Základ {data['base']:>12.2f} Kč | "
                f"DPH {data['vat']:>12.2f} Kč | "
                f"Celkem {data['total']:>12.2f} Kč"
            )
            total_base += data['base']
            total_vat += data['vat']
            total_amount += data['total']

        lines.append("-" * 60)
        lines.append(
            f"CELKEM:   "
            f"Základ {total_base:>12.2f} Kč | "
            f"DPH {total_vat:>12.2f} Kč | "
            f"Celkem {total_amount:>12.2f} Kč"
        )

        return "\n".join(lines)

    @staticmethod
    def validate_vat_rate(rate: Union[float, Decimal]) -> bool:
        """
        Kontrola platnosti DPH sazby

        Args:
            rate: Sazba k validaci

        Returns:
            bool: True = platná sazba
        """
        valid_rates = [
            VATCalculator.STANDARD_RATE,
            VATCalculator.REDUCED_RATE,
            VATCalculator.ZERO_RATE
        ]

        rate_decimal = Decimal(str(rate))
        return rate_decimal in valid_rates

    @staticmethod
    def get_available_rates() -> list:
        """
        Vrátí dostupné DPH sazby

        Returns:
            list: [(21, "Základní 21%"), (12, "Snížená 12%"), (0, "Osvobozeno 0%")]
        """
        return [
            (21, "Základní 21%"),
            (12, "Snížená 12%"),
            (0, "Osvobozeno 0%")
        ]


# ============================================
# POMOCNÉ FUNKCE (zkratky pro časté použití)
# ============================================

def add_vat_21(amount: Union[float, Decimal]) -> Tuple[Decimal, Decimal, Decimal]:
    """Přidání DPH 21% - zkratka"""
    return VATCalculator.add_vat(amount, 21)


def add_vat_12(amount: Union[float, Decimal]) -> Tuple[Decimal, Decimal, Decimal]:
    """Přidání DPH 12% - zkratka"""
    return VATCalculator.add_vat(amount, 12)


def remove_vat_21(amount: Union[float, Decimal]) -> Tuple[Decimal, Decimal, Decimal]:
    """Odstranění DPH 21% - zkratka"""
    return VATCalculator.remove_vat(amount, 21)


def remove_vat_12(amount: Union[float, Decimal]) -> Tuple[Decimal, Decimal, Decimal]:
    """Odstranění DPH 12% - zkratka"""
    return VATCalculator.remove_vat(amount, 12)


# ============================================
# TESTY (spustit pro kontrolu)
# ============================================

if __name__ == "__main__":
    print("=== TEST KALKULÁTORU DPH ===\n")

    # Test 1: Přidání DPH
    print("Test 1: Přidání DPH 21% k 1000 Kč")
    base, vat, total = VATCalculator.add_vat(1000, 21)
    print(f"Základ: {base} Kč, DPH: {vat} Kč, Celkem: {total} Kč")
    assert total == Decimal("1210.00")
    print("✅ OK\n")

    # Test 2: Odstranění DPH
    print("Test 2: Odstranění DPH 21% z 1210 Kč")
    base, vat, total = VATCalculator.remove_vat(1210, 21)
    print(f"Základ: {base} Kč, DPH: {vat} Kč, Celkem: {total} Kč")
    assert base == Decimal("1000.00")
    print("✅ OK\n")

    # Test 3: Marže
    print("Test 3: Marže 50% (nákup 1000 → prodej 1500)")
    margin_pct = VATCalculator.calculate_margin(1000, 1500)
    print(f"Marže: {margin_pct}%")
    assert margin_pct == Decimal("50.00")
    print("✅ OK\n")

    # Test 4: Rozdělení podle sazeb
    print("Test 4: Rozdělení položek podle sazeb DPH")
    items = [
        {'amount_without_vat': 1000, 'vat_rate': 21},
        {'amount_without_vat': 500, 'vat_rate': 21},
        {'amount_without_vat': 300, 'vat_rate': 12}
    ]
    result = VATCalculator.split_vat_by_rates(items)
    print(VATCalculator.format_vat_summary(result))
    print("✅ OK\n")

    print("=== VŠECHNY TESTY PROŠLY ✅ ===")
