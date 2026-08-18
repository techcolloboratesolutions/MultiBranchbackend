from decimal import Decimal, InvalidOperation

from django.db import transaction
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from accounts.permissions import IsAdminOrManager, IsAdminOrReadOnlyManager
from accounts.scoping import INSTITUTION_FORBIDDEN, apply_institution_filter, scoped_institution_id
from institutions.models import Institution
from receipts.models import DailyReceipt, ReceiptHead
from receipts.serializers import DailyReceiptSerializer, ReceiptHeadSerializer


class ReceiptHeadViewSet(viewsets.ModelViewSet):
    queryset = ReceiptHead.objects.all()
    serializer_class = ReceiptHeadSerializer
    permission_classes = [IsAdminOrReadOnlyManager]

    def get_queryset(self):
        qs = super().get_queryset()
        active = self.request.query_params.get("active")
        if active in ("true", "True", "Y", "y", "1"):
            qs = qs.filter(is_active=True)
        elif active in ("false", "False", "N", "n", "0"):
            qs = qs.filter(is_active=False)
        return qs


class DailyReceiptViewSet(viewsets.ModelViewSet):
    queryset = DailyReceipt.objects.select_related(
        "receipt_head", "institution", "entered_by"
    ).all()
    serializer_class = DailyReceiptSerializer
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
        """One row per active receipt head (ACTIVE='Y') for the selected date."""
        business_date = request.query_params.get("business_date")
        if not business_date:
            raise ValidationError("Business date is required.")
        institution_id = scoped_institution_id(request)
        heads = ReceiptHead.objects.filter(is_active=True).order_by("code")
        receipts_by_head = {}
        if institution_id is not None:
            existing = (
                DailyReceipt.objects.filter(
                    institution_id=institution_id,
                    business_date=business_date,
                    is_active=True,
                )
                .select_related("entered_by")
                .order_by("id")
            )
            for receipt in existing:
                receipts_by_head[receipt.receipt_head_id] = receipt
        rows = []
        for head in heads:
            receipt = receipts_by_head.get(head.id)
            rows.append(
                {
                    "receipt_head": head.id,
                    "code": head.code,
                    "description": head.description,
                    "amount": str(receipt.amount) if receipt else "",
                    "receipt_id": receipt.id if receipt else None,
                    "entered_by_name": (
                        receipt.entered_by.username if receipt and receipt.entered_by_id else None
                    ),
                }
            )
        return Response(
            {
                "institution_id": institution_id,
                "business_date": business_date,
                "rows": rows,
            }
        )

    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk(self, request):
        """Save amounts for all active receipt heads in one request."""
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
            ReceiptHead.objects.filter(is_active=True).values_list("id", flat=True)
        )
        saved = []
        with transaction.atomic():
            for line in lines:
                head_id = int(line.get("receipt_head"))
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
                    DailyReceipt.objects.select_for_update()
                    .filter(
                        institution=institution,
                        business_date=business_date,
                        receipt_head_id=head_id,
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
                        DailyReceipt.objects.create(
                            institution=institution,
                            business_date=business_date,
                            receipt_head_id=head_id,
                            amount=amount,
                            entered_by=request.user,
                        )
                    )
        return Response(self.get_serializer(saved, many=True).data)
