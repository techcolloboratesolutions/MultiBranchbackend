from decimal import Decimal, ROUND_HALF_UP

MONEY_QUANTIZE = Decimal("0.01")
HUNDRED = Decimal("100")


def money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(MONEY_QUANTIZE, rounding=ROUND_HALF_UP)


def calculate_total_business(total_sales: Decimal, total_purchase: Decimal) -> Decimal:
    return money(Decimal(total_sales) + Decimal(total_purchase))


def calculate_balance(total_sales: Decimal, total_purchase: Decimal, total_expense: Decimal) -> Decimal:
    # Purchase is not part of balance; callers still pass it for a stable signature.
    _ = total_purchase
    return money(Decimal(total_sales) - Decimal(total_expense))


def calculate_partner_wage(base_amount: Decimal, share_percent: Decimal) -> Decimal:
    return money(Decimal(base_amount) * Decimal(share_percent) / HUNDRED)
