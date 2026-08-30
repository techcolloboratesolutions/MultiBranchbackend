from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db.models import Sum

from core.money import calculate_balance, calculate_total_business, money
from expenses.models import DailyExpense, ExpenseHead
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


def sum_expenses(institution_id, start: date, end: date) -> Decimal:
    qs = DailyExpense.objects.filter(is_active=True, business_date__range=(start, end))
    if institution_id is not None:
        qs = qs.filter(institution_id=institution_id)
    total = qs.aggregate(total=Sum("amount"))["total"]
    return money(total or ZERO)


def period_totals(institution_id, year: int, month: int):
    start, end = _date_range(year, month)
    receipt = sum_receipts(institution_id, start, end)
    payment = sum_payments(institution_id, start, end)
    expense = sum_expenses(institution_id, start, end)
    return {
        "total_receipt": receipt,
        "total_payment": payment,
        "total_expense": expense,
        "total_business": calculate_total_business(receipt, payment),
        "total_balance": calculate_balance(receipt, payment, expense),
        "start": start,
        "end": end,
    }


def daily_breakdown(institution_id, year: int, month: int):
    start, end = _date_range(year, month)
    receipts = DailyReceipt.objects.filter(is_active=True, business_date__range=(start, end)).values("business_date")
    payments = DailyPayment.objects.filter(is_active=True, business_date__range=(start, end)).values("business_date")
    expenses = DailyExpense.objects.filter(is_active=True, business_date__range=(start, end)).values("business_date")
    if institution_id is not None:
        receipts = receipts.filter(institution_id=institution_id)
        payments = payments.filter(institution_id=institution_id)
        expenses = expenses.filter(institution_id=institution_id)

    receipt_map = {
        row["business_date"]: money(row["total"] or ZERO)
        for row in receipts.annotate(total=Sum("amount"))
    }
    payment_map = {
        row["business_date"]: money(row["total"] or ZERO)
        for row in payments.annotate(total=Sum("amount"))
    }
    expense_map = {
        row["business_date"]: money(row["total"] or ZERO)
        for row in expenses.annotate(total=Sum("amount"))
    }
    days = sorted(set(receipt_map) | set(payment_map) | set(expense_map))
    rows = []
    for day in days:
        rec = receipt_map.get(day, ZERO)
        pay = payment_map.get(day, ZERO)
        exp = expense_map.get(day, ZERO)
        rows.append(
            {
                "date": day,
                "receipt": rec,
                "payment": pay,
                "expense": exp,
                "business": calculate_total_business(rec, pay),
                "balance": calculate_balance(rec, pay, exp),
            }
        )
    totals = period_totals(institution_id, year, month)
    return rows, totals


def monthly_head_matrix(institution_id, year: int, month: int):
    """Daily matrix of active sales, purchase, and expense heads."""
    start, end = _date_range(year, month)
    receipt_heads = list(ReceiptHead.objects.filter(is_active=True).order_by("code"))
    payment_heads = list(PaymentHead.objects.filter(is_active=True).order_by("code"))
    expense_heads = list(ExpenseHead.objects.filter(is_active=True).order_by("code"))

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
    exp_qs = DailyExpense.objects.filter(
        is_active=True,
        business_date__range=(start, end),
        expense_head__is_active=True,
    )
    if institution_id is not None:
        rec_qs = rec_qs.filter(institution_id=institution_id)
        pay_qs = pay_qs.filter(institution_id=institution_id)
        exp_qs = exp_qs.filter(institution_id=institution_id)

    rec_map = {
        (row["business_date"], row["receipt_head_id"]): money(row["total"] or ZERO)
        for row in rec_qs.values("business_date", "receipt_head_id").annotate(total=Sum("amount"))
    }
    pay_map = {
        (row["business_date"], row["payment_head_id"]): money(row["total"] or ZERO)
        for row in pay_qs.values("business_date", "payment_head_id").annotate(total=Sum("amount"))
    }
    exp_map = {
        (row["business_date"], row["expense_head_id"]): money(row["total"] or ZERO)
        for row in exp_qs.values("business_date", "expense_head_id").annotate(total=Sum("amount"))
    }

    days = sorted({day for day, _head in rec_map} | {day for day, _head in pay_map} | {day for day, _head in exp_map})
    rec_totals = {head.id: ZERO for head in receipt_heads}
    pay_totals = {head.id: ZERO for head in payment_heads}
    exp_totals = {head.id: ZERO for head in expense_heads}
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
        expenses = {}
        exp_total = ZERO
        for head in expense_heads:
            amount = exp_map.get((day, head.id), ZERO)
            expenses[str(head.id)] = amount
            exp_total += amount
            exp_totals[head.id] += amount
        rows.append(
            {
                "date": day,
                "receipts": receipts,
                "payments": payments,
                "expenses": expenses,
                "receipt": money(rec_total),
                "payment": money(pay_total),
                "expense": money(exp_total),
                "business": calculate_total_business(rec_total, pay_total),
                "balance": calculate_balance(rec_total, pay_total, exp_total),
            }
        )

    totals = period_totals(institution_id, year, month)
    return {
        "receipt_heads": receipt_heads,
        "payment_heads": payment_heads,
        "expense_heads": expense_heads,
        "rows": rows,
        "receipt_head_totals": rec_totals,
        "payment_head_totals": pay_totals,
        "expense_head_totals": exp_totals,
        "totals": totals,
    }


def institution_date_head_matrix(day: date):
    """Sales, purchase, and expense heads for every active branch on one business date."""
    receipt_heads = list(ReceiptHead.objects.filter(is_active=True).order_by("code"))
    payment_heads = list(PaymentHead.objects.filter(is_active=True).order_by("code"))
    expense_heads = list(ExpenseHead.objects.filter(is_active=True).order_by("code"))
    rec_qs = DailyReceipt.objects.filter(is_active=True, business_date=day, receipt_head__is_active=True)
    pay_qs = DailyPayment.objects.filter(is_active=True, business_date=day, payment_head__is_active=True)
    exp_qs = DailyExpense.objects.filter(is_active=True, business_date=day, expense_head__is_active=True)
    rec_map = {
        (row["institution_id"], row["receipt_head_id"]): money(row["total"] or ZERO)
        for row in rec_qs.values("institution_id", "receipt_head_id").annotate(total=Sum("amount"))
    }
    pay_map = {
        (row["institution_id"], row["payment_head_id"]): money(row["total"] or ZERO)
        for row in pay_qs.values("institution_id", "payment_head_id").annotate(total=Sum("amount"))
    }
    exp_map = {
        (row["institution_id"], row["expense_head_id"]): money(row["total"] or ZERO)
        for row in exp_qs.values("institution_id", "expense_head_id").annotate(total=Sum("amount"))
    }
    rec_totals = {head.id: ZERO for head in receipt_heads}
    pay_totals = {head.id: ZERO for head in payment_heads}
    exp_totals = {head.id: ZERO for head in expense_heads}
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
        expenses = {}
        exp_total = ZERO
        for head in expense_heads:
            amount = exp_map.get((inst.id, head.id), ZERO)
            expenses[str(head.id)] = amount
            exp_total += amount
            exp_totals[head.id] += amount
        rows.append(
            {
                "institution_id": inst.id,
                "institution_name": inst.name,
                "receipts": receipts,
                "payments": payments,
                "expenses": expenses,
                "receipt": money(rec_total),
                "payment": money(pay_total),
                "expense": money(exp_total),
                "business": calculate_total_business(rec_total, pay_total),
                "balance": calculate_balance(rec_total, pay_total, exp_total),
            }
        )
    rec_sum = sum(rec_totals.values(), ZERO)
    pay_sum = sum(pay_totals.values(), ZERO)
    exp_sum = sum(exp_totals.values(), ZERO)
    return {
        "date": day,
        "receipt_heads": receipt_heads,
        "payment_heads": payment_heads,
        "expense_heads": expense_heads,
        "rows": rows,
        "receipt_head_totals": rec_totals,
        "payment_head_totals": pay_totals,
        "expense_head_totals": exp_totals,
        "totals": {
            "total_receipt": money(rec_sum),
            "total_payment": money(pay_sum),
            "total_expense": money(exp_sum),
            "total_business": calculate_total_business(rec_sum, pay_sum),
            "total_balance": calculate_balance(rec_sum, pay_sum, exp_sum),
        },
    }


def institution_business(year: int, month: int):
    start, end = _date_range(year, month)
    return institution_period_totals(start, end)


def institution_day_totals(day: date):
    return institution_period_totals(day, day)


def _empty_institution_entry(institution_id, institution_name):
    return {
        "institution_id": institution_id,
        "institution_name": institution_name,
        "receipt": ZERO,
        "payment": ZERO,
        "expense": ZERO,
    }


def institution_period_totals(start: date, end: date):
    data = {
        inst.id: _empty_institution_entry(inst.id, inst.name)
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
    expenses = (
        DailyExpense.objects.filter(is_active=True, business_date__range=(start, end))
        .values("institution_id", "institution__name")
        .annotate(total=Sum("amount"))
    )
    for row in receipts:
        entry = data.setdefault(row["institution_id"], _empty_institution_entry(row["institution_id"], row["institution__name"]))
        entry["receipt"] = money(row["total"] or ZERO)
    for row in payments:
        entry = data.setdefault(row["institution_id"], _empty_institution_entry(row["institution_id"], row["institution__name"]))
        entry["payment"] = money(row["total"] or ZERO)
    for row in expenses:
        entry = data.setdefault(row["institution_id"], _empty_institution_entry(row["institution_id"], row["institution__name"]))
        entry["expense"] = money(row["total"] or ZERO)
    result = []
    for entry in data.values():
        entry["business"] = calculate_total_business(entry["receipt"], entry["payment"])
        entry["balance"] = calculate_balance(entry["receipt"], entry["payment"], entry["expense"])
        result.append(entry)
    return sorted(result, key=lambda x: x["institution_name"])


def monthly_trend(institution_id, as_of: date, months: int = 12):
    """Last N calendar months of sales, purchase, expense, business, and balance."""
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
                "expense": totals["total_expense"],
                "business": totals["total_business"],
                "balance": totals["total_balance"],
            }
        )
    return series
