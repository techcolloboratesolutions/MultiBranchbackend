from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db.models import Sum

from core.money import calculate_total_business, money
from institutions.models import Institution
from payments.models import DailyPayment, PaymentHead
from receipts.models import DailyReceipt, ReceiptHead

ZERO = Decimal("0.00")


def _date_range(year: int, month: int):
    start = date(year, month, 1)
    end = date(year, month, monthrange(year, month)[1])
    return start, end


def sum_receipts(institution_id, start: date, end: date) -> Decimal:
    qs = DailyReceipt.objects.filter(is_active=True, business_date__range=(start, end))
    if institution_id is not None:
        qs = qs.filter(institution_id=institution_id)
    total = qs.aggregate(total=Sum("amount"))["total"]
    return money(total or ZERO)


def sum_payments(institution_id, start: date, end: date) -> Decimal:
    qs = DailyPayment.objects.filter(is_active=True, business_date__range=(start, end))
    if institution_id is not None:
        qs = qs.filter(institution_id=institution_id)
    total = qs.aggregate(total=Sum("amount"))["total"]
    return money(total or ZERO)


def period_totals(institution_id, year: int, month: int):
    start, end = _date_range(year, month)
    receipt = sum_receipts(institution_id, start, end)
    payment = sum_payments(institution_id, start, end)
    return {
        "total_receipt": receipt,
        "total_payment": payment,
        "total_business": calculate_total_business(receipt, payment),
        "start": start,
        "end": end,
    }


def daily_breakdown(institution_id, year: int, month: int):
    start, end = _date_range(year, month)
    receipts = (
        DailyReceipt.objects.filter(is_active=True, business_date__range=(start, end))
        .values("business_date")
    )
    payments = (
        DailyPayment.objects.filter(is_active=True, business_date__range=(start, end))
        .values("business_date")
    )
    if institution_id is not None:
        receipts = receipts.filter(institution_id=institution_id)
        payments = payments.filter(institution_id=institution_id)

    receipt_map = {
        row["business_date"]: money(row["total"] or ZERO)
        for row in receipts.annotate(total=Sum("amount"))
    }
    payment_map = {
        row["business_date"]: money(row["total"] or ZERO)
        for row in payments.annotate(total=Sum("amount"))
    }
    days = sorted(set(receipt_map) | set(payment_map))
    rows = []
    for day in days:
        rec = receipt_map.get(day, ZERO)
        pay = payment_map.get(day, ZERO)
        rows.append(
            {
                "date": day,
                "receipt": rec,
                "payment": pay,
                "business": calculate_total_business(rec, pay),
            }
        )
    totals = period_totals(institution_id, year, month)
    return rows, totals


def monthly_head_matrix(institution_id, year: int, month: int):
    """
    Daily matrix of all active receipt heads and payment heads,
    plus a sum under each head for the month.
    """
    start, end = _date_range(year, month)
    receipt_heads = list(ReceiptHead.objects.filter(is_active=True).order_by("code"))
    payment_heads = list(PaymentHead.objects.filter(is_active=True).order_by("code"))

    rec_qs = DailyReceipt.objects.filter(
        is_active=True,
        business_date__range=(start, end),
        receipt_head__is_active=True,
    )
    pay_qs = DailyPayment.objects.filter(
        is_active=True,
        business_date__range=(start, end),
        payment_head__is_active=True,
    )
    if institution_id is not None:
        rec_qs = rec_qs.filter(institution_id=institution_id)
        pay_qs = pay_qs.filter(institution_id=institution_id)

    rec_map = {
        (row["business_date"], row["receipt_head_id"]): money(row["total"] or ZERO)
        for row in rec_qs.values("business_date", "receipt_head_id").annotate(total=Sum("amount"))
    }
    pay_map = {
        (row["business_date"], row["payment_head_id"]): money(row["total"] or ZERO)
        for row in pay_qs.values("business_date", "payment_head_id").annotate(total=Sum("amount"))
    }

    days = sorted({day for day, _head in rec_map} | {day for day, _head in pay_map})
    rec_totals = {head.id: ZERO for head in receipt_heads}
    pay_totals = {head.id: ZERO for head in payment_heads}
    rows = []
    for day in days:
        receipts = {}
        rec_total = ZERO
        for head in receipt_heads:
            amount = rec_map.get((day, head.id), ZERO)
            receipts[str(head.id)] = amount
            rec_total += amount
            rec_totals[head.id] += amount
        payments = {}
        pay_total = ZERO
        for head in payment_heads:
            amount = pay_map.get((day, head.id), ZERO)
            payments[str(head.id)] = amount
            pay_total += amount
            pay_totals[head.id] += amount
        rows.append(
            {
                "date": day,
                "receipts": receipts,
                "payments": payments,
                "receipt": money(rec_total),
                "payment": money(pay_total),
                "business": calculate_total_business(rec_total, pay_total),
            }
        )

    totals = period_totals(institution_id, year, month)
    return {
        "receipt_heads": receipt_heads,
        "payment_heads": payment_heads,
        "rows": rows,
        "receipt_head_totals": rec_totals,
        "payment_head_totals": pay_totals,
        "totals": totals,
    }


def institution_date_head_matrix(day: date):
    """Receipt and payment heads for every active branch on one business date."""
    receipt_heads = list(ReceiptHead.objects.filter(is_active=True).order_by("code"))
    payment_heads = list(PaymentHead.objects.filter(is_active=True).order_by("code"))
    rec_qs = DailyReceipt.objects.filter(
        is_active=True,
        business_date=day,
        receipt_head__is_active=True,
    )
    pay_qs = DailyPayment.objects.filter(
        is_active=True,
        business_date=day,
        payment_head__is_active=True,
    )
    rec_map = {
        (row["institution_id"], row["receipt_head_id"]): money(row["total"] or ZERO)
        for row in rec_qs.values("institution_id", "receipt_head_id").annotate(total=Sum("amount"))
    }
    pay_map = {
        (row["institution_id"], row["payment_head_id"]): money(row["total"] or ZERO)
        for row in pay_qs.values("institution_id", "payment_head_id").annotate(total=Sum("amount"))
    }
    rec_totals = {head.id: ZERO for head in receipt_heads}
    pay_totals = {head.id: ZERO for head in payment_heads}
    rows = []
    for inst in Institution.objects.filter(is_active=True).order_by("name"):
        receipts = {}
        rec_total = ZERO
        for head in receipt_heads:
            amount = rec_map.get((inst.id, head.id), ZERO)
            receipts[str(head.id)] = amount
            rec_total += amount
            rec_totals[head.id] += amount
        payments = {}
        pay_total = ZERO
        for head in payment_heads:
            amount = pay_map.get((inst.id, head.id), ZERO)
            payments[str(head.id)] = amount
            pay_total += amount
            pay_totals[head.id] += amount
        rows.append(
            {
                "institution_id": inst.id,
                "institution_name": inst.name,
                "receipts": receipts,
                "payments": payments,
                "receipt": money(rec_total),
                "payment": money(pay_total),
                "business": calculate_total_business(rec_total, pay_total),
            }
        )
    return {
        "date": day,
        "receipt_heads": receipt_heads,
        "payment_heads": payment_heads,
        "rows": rows,
        "receipt_head_totals": rec_totals,
        "payment_head_totals": pay_totals,
        "totals": {
            "total_receipt": money(sum(rec_totals.values(), ZERO)),
            "total_payment": money(sum(pay_totals.values(), ZERO)),
            "total_business": calculate_total_business(
                sum(rec_totals.values(), ZERO),
                sum(pay_totals.values(), ZERO),
            ),
        },
    }


def institution_business(year: int, month: int):
    start, end = _date_range(year, month)
    return institution_period_totals(start, end)


def institution_day_totals(day: date):
    return institution_period_totals(day, day)


def institution_period_totals(start: date, end: date):
    data = {
        inst.id: {
            "institution_id": inst.id,
            "institution_name": inst.name,
            "receipt": ZERO,
            "payment": ZERO,
        }
        for inst in Institution.objects.filter(is_active=True).order_by("name")
    }
    receipts = (
        DailyReceipt.objects.filter(is_active=True, business_date__range=(start, end))
        .values("institution_id", "institution__name")
        .annotate(total=Sum("amount"))
    )
    payments = (
        DailyPayment.objects.filter(is_active=True, business_date__range=(start, end))
        .values("institution_id", "institution__name")
        .annotate(total=Sum("amount"))
    )
    for row in receipts:
        entry = data.setdefault(
            row["institution_id"],
            {
                "institution_id": row["institution_id"],
                "institution_name": row["institution__name"],
                "receipt": ZERO,
                "payment": ZERO,
            },
        )
        entry["receipt"] = money(row["total"] or ZERO)
    for row in payments:
        entry = data.setdefault(
            row["institution_id"],
            {
                "institution_id": row["institution_id"],
                "institution_name": row["institution__name"],
                "receipt": ZERO,
                "payment": ZERO,
            },
        )
        entry["payment"] = money(row["total"] or ZERO)
    result = []
    for entry in data.values():
        entry["business"] = calculate_total_business(entry["receipt"], entry["payment"])
        result.append(entry)
    return sorted(result, key=lambda x: x["institution_name"])


def monthly_trend(institution_id, as_of: date, months: int = 12):
    """Last N calendar months of receipt, payment, and business (oldest first)."""
    year = as_of.year
    month = as_of.month
    periods = []
    for _ in range(months):
        periods.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    periods.reverse()
    series = []
    for period_year, period_month in periods:
        totals = period_totals(institution_id, period_year, period_month)
        series.append(
            {
                "year": period_year,
                "month": period_month,
                "label": date(period_year, period_month, 1).strftime("%b %Y"),
                "receipt": totals["total_receipt"],
                "payment": totals["total_payment"],
                "business": totals["total_business"],
            }
        )
    return series
