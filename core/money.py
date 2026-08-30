from decimal import Decimal, ROUND_HALF_UP

MONEY_QUANTIZE = Decimal("0.01")
HUNDRED = Decimal("100")


def money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(MONEY_QUANTIZE, rounding=ROUND_HALF_UP)


def calculate_total_business(total_receipt: Decimal, total_payment: Decimal) -> Decimal:
    return money(Decimal(total_receipt) + Decimal(total_payment))


def calculate_balance(total_receipt: Decimal, total_payment: Decimal, total_expense: Decimal) -> Decimal:
    return money(calculate_total_business(total_receipt, total_payment) - Decimal(total_expense))


def calculate_partner_wage(total_business: Decimal, share_percent: Decimal) -> Decimal:
    return money(Decimal(total_business) * Decimal(share_percent) / HUNDRED)
