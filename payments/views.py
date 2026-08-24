from decimal import Decimal, InvalidOperation

from django.db import transaction
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from accounts.permissions import IsAdminOrManager, IsAdminOrReadOnlyManager
from accounts.scoping import INSTITUTION_FORBIDDEN, apply_institution_filter, scoped_institution_id
from institutions.models import Institution
from payments.models import DailyPayment, PaymentHead
from payments.serializers import DailyPaymentSerializer, PaymentHeadSerializer

VALID_RECURRING_TYPES = {choice.value for choice in PaymentHead.RecurringType}


def parse_recurring_types(request, *, default=(PaymentHead.RecurringType.DAILY,)):
    """Daily is selected by default; Monthly is included when requested."""
    raw_values = request.query_params.getlist("recurring_type")
    selected = []
    for raw in raw_values:
        for part in str(raw).split(","):
            value = part.strip()
            matched = next(
                (valid for valid in VALID_RECURRING_TYPES if valid.lower() == value.lower()),
                None,
            )
            if matched and matched not in selected:
                selected.append(matched)
    return selected or list(default)


def payment_entry_row(head, payment):
    return {
        "payment_head": head.id,
        "code": head.code,
        "description": head.description,
        "recurring_type": head.recurring_type,
        "amount": str(payment.amount) if payment else "",
        "payment_id": payment.id if payment else None,
        "entered_by_name": (
            payment.entered_by.username if payment and payment.entered_by_id else None
        ),
    }


class PaymentHeadViewSet(viewsets.ModelViewSet):
    queryset = PaymentHead.objects.all()
    serializer_class = PaymentHeadSerializer
    permission_classes = [IsAdminOrReadOnlyManager]

    def get_queryset(self):
        qs = super().get_queryset()
        active = self.request.query_params.get("active")
        if active in ("true", "True", "Y", "y", "1"):
            qs = qs.filter(is_active=True)
        elif active in ("false", "False", "N", "n", "0"):
            qs = qs.filter(is_active=False)
        if "recurring_type" in self.request.query_params:
            qs = qs.filter(recurring_type__in=parse_recurring_types(self.request, default=()))
        return qs


class DailyPaymentViewSet(viewsets.ModelViewSet):
    queryset = DailyPayment.objects.select_related(
        "payment_head", "institution", "entered_by"
    ).all()
    serializer_class = DailyPaymentSerializer
    permission_classes = [IsAdminOrManager]

    def get_queryset(self):
        qs = apply_institution_filter(super().get_queryset(), self.request)
        business_date = self.request.query_params.get("business_date")
        if business_date:
            qs = qs.filter(business_date=business_date)
        year = self.request.query_params.get("year")
        month = self.request.query_params.get("month")
        if year:
            qs = qs.filter(business_date__year=year)
        if month:
            qs = qs.filter(business_date__month=month)
        active = self.request.query_params.get("active")
        if active in ("true", "Y", "y"):
            qs = qs.filter(is_active=True)
        elif active in ("false", "N", "n"):
            qs = qs.filter(is_active=False)
        return qs

    def perform_create(self, serializer):
        institution_id = scoped_institution_id(
            self.request,
            serializer.validated_data.get("institution").id
            if serializer.validated_data.get("institution")
            else None,
        )
        institution = serializer.validated_data.get("institution")
        if institution_id and institution and institution.id != institution_id:
            raise PermissionDenied(detail=INSTITUTION_FORBIDDEN)
        if institution_id and not institution:
            institution = Institution.objects.get(pk=institution_id)
        serializer.save(entered_by=self.request.user, institution=institution)

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        obj = self.get_object()
        obj.is_active = False
        obj.modified_by = request.user
        obj.save(update_fields=["is_active", "modified_by", "modified_date"])
        return Response(self.get_serializer(obj).data)

    @action(detail=False, methods=["get"], url_path="entry-sheet")
    def entry_sheet(self, request):
        """Two-column entry sheet: Daily heads and Monthly heads on one screen.

        Daily is checked by default. Monthly heads are returned in the monthly
        column only when Monthly is requested.
        """
        business_date = request.query_params.get("business_date")
        if not business_date:
            raise ValidationError("Business date is required.")
        institution_id = scoped_institution_id(request)
        recurring_types = parse_recurring_types(request)
        monthly_flag = request.query_params.get("monthly")
        monthly_selected = PaymentHead.RecurringType.MONTHLY in recurring_types or monthly_flag in (
            "true",
            "True",
            "1",
            "Y",
            "y",
        )
        daily_off = request.query_params.get("daily") in ("false", "False", "0", "N", "n")
        daily_selected = not daily_off
        heads = PaymentHead.objects.filter(is_active=True).order_by("code")
        payments_by_head = {}
        if institution_id is not None:
            existing = (
                DailyPayment.objects.filter(
                    institution_id=institution_id,
                    business_date=business_date,
                    is_active=True,
                )
                .select_related("entered_by")
                .order_by("id")
            )
            for payment in existing:
                payments_by_head[payment.payment_head_id] = payment
        daily_rows = []
        monthly_rows = []
        for head in heads:
            row = payment_entry_row(head, payments_by_head.get(head.id))
            if head.recurring_type == PaymentHead.RecurringType.MONTHLY:
                monthly_rows.append(row)
            else:
                daily_rows.append(row)
        visible_daily = daily_rows if daily_selected else []
        visible_monthly = monthly_rows if monthly_selected else []
        return Response(
            {
                "institution_id": institution_id,
                "business_date": business_date,
                "layout": "two_column",
                "recurring_types": [
                    value
                    for value, selected in (
                        (PaymentHead.RecurringType.DAILY, daily_selected),
                        (PaymentHead.RecurringType.MONTHLY, monthly_selected),
                    )
                    if selected
                ],
                "daily_selected": daily_selected,
                "monthly_selected": monthly_selected,
                "daily_rows": visible_daily,
                "monthly_rows": visible_monthly,
                "rows": visible_daily + visible_monthly,
            }
        )

    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk(self, request):
        """Save amounts for all active payment heads in one request."""
        business_date = request.data.get("business_date")
        lines = request.data.get("lines") or []
        if not business_date:
            raise ValidationError("Business date is required.")

        raw_institution = request.data.get("institution_id", request.data.get("institution"))
        requested = None if raw_institution in (None, "", "all", "ALL") else int(raw_institution)
        institution_id = scoped_institution_id(request, requested)
        if institution_id is None:
            raise ValidationError("Select a specific institution.")
        institution = Institution.objects.get(pk=institution_id)

        active_head_ids = set(
            PaymentHead.objects.filter(is_active=True).values_list("id", flat=True)
        )
        saved = []
        with transaction.atomic():
            for line in lines:
                head_id = int(line.get("payment_head"))
                if head_id not in active_head_ids:
                    continue
                raw_amount = line.get("amount")
                if raw_amount in (None, ""):
                    continue
                try:
                    amount = Decimal(str(raw_amount))
                except (InvalidOperation, TypeError) as exc:
                    raise ValidationError("Enter a valid amount.") from exc
                if amount < 0:
                    raise ValidationError("Amount cannot be negative.")
                if amount == 0:
                    continue
                existing = (
                    DailyPayment.objects.select_for_update()
                    .filter(
                        institution=institution,
                        business_date=business_date,
                        payment_head_id=head_id,
                        is_active=True,
                    )
                    .order_by("-id")
                    .first()
                )
                if existing:
                    existing.amount = amount
                    existing.modified_by = request.user
                    existing.save()
                    saved.append(existing)
                else:
                    saved.append(
                        DailyPayment.objects.create(
                            institution=institution,
                            business_date=business_date,
                            payment_head_id=head_id,
                            amount=amount,
                            entered_by=request.user,
                        )
                    )
        return Response(self.get_serializer(saved, many=True).data)
