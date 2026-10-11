from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import (
    BooleanField,
    Case,
    Count,
    DecimalField,
    Exists,
    F,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Round, Trim

from businessos.core.access.policies import require_permission
from businessos.core.database import business_atomic, current_database_alias
from businessos.core.organization.models import Company

from .domain import MAX_INPUT, finalize_total
from .manifest import VIEW_INVOICES
from .models import Invoice, InvoiceLine


def invoices_for_company(context, *, search="", status=""):
    require_permission(context, VIEW_INVOICES)
    invoices = Invoice.objects.filter(company_id=context.company_id).prefetch_related("lines")
    if search.strip():
        invoices = invoices.filter(
            Q(number__icontains=search.strip())
            | Q(bill_to_display_name_snapshot__icontains=search.strip())
        )
    if status:
        invoices = invoices.filter(status=status)
    return invoices.order_by("-invoice_date", "-created_at", "id")


def invoice_detail(context, invoice_id):
    return invoices_for_company(context).select_related("company").get(pk=invoice_id)


def invoice_total(context, invoice_id):
    return invoice_detail(context, invoice_id).total


FINANCIAL_BASIS_VERSION = 1


def issued_invoice_basis_query(context, *, invoice_ids):
    """Owner-owned SQL basis for complete-history validation, never line text payload.

    `invoice_ids` is a selected-alias UUID subquery. Results stay on the selected
    alias; callers must stabilize Company and bound any materialized payload.
    """
    require_permission(context, VIEW_INVOICES)
    alias = current_database_alias()
    lines = InvoiceLine.objects.using(alias).filter(invoice_id=OuterRef("pk"))
    invalid = lines.alias(text=Trim("description")).exclude(
        Q(
            company_id=context.company_id,
            quantity__gte=Decimal("0.0001"),
            quantity__lte=MAX_INPUT,
            unit_price__gte=0,
            unit_price__lte=MAX_INPUT,
            position__gte=1,
            description__regex=r"\S",
        )
        & ~Q(text="")
    )
    totals = (
        lines.order_by()
        .values("invoice_id")
        .annotate(raw=Sum(F("quantity") * F("unit_price"), output_field=DecimalField()))
        .values("raw")
    )
    rows = (
        Invoice.objects.using(alias)
        .filter(pk__in=invoice_ids, company_id=context.company_id)
        .only(
            "id",
            "company_id",
            "bill_to_party_id",
            "status",
            "issued_at",
            "currency_id",
            "currency_code_snapshot",
            "currency_decimal_places_snapshot",
        )
        .annotate(
            basis_raw=Subquery(totals, output_field=DecimalField()),
            basis_bad_lines=Exists(invalid),
            basis_has_lines=Exists(lines),
        )
        .annotate(
            basis_total=Round(
                "basis_raw", F("currency_decimal_places_snapshot"), output_field=DecimalField()
            )
        )
    )
    valid = Q(
        company_id=context.company_id,
        bill_to_party__company_id=context.company_id,
        status=Invoice.Status.ISSUED,
        issued_at__isnull=False,
        currency__code=F("currency_code_snapshot"),
        currency_decimal_places_snapshot__gte=0,
        currency_decimal_places_snapshot__lte=8,
        basis_has_lines=True,
        basis_bad_lines=False,
        basis_raw__gte=0,
        basis_raw__lt=Decimal("1e30"),
        basis_total__gte=0,
        basis_total__lt=Decimal("1e30"),
    )
    return rows.annotate(
        basis_valid=Case(
            When(valid, then=Value(True)), default=Value(False), output_field=BooleanField()
        )
    )


@dataclass(frozen=True, slots=True)
class InvoiceFinancialBasis:
    id: UUID
    company_id: UUID
    bill_to_party_id: UUID
    status: str
    issued_at: object
    currency_id: UUID
    currency_code: str
    precision: int
    original_total: Decimal


@business_atomic
def invoice_financial_basis(context, invoice_id, *, lock=True):
    """Minimal owner-owned issued basis; no notes, descriptions or settlement facts.

    Callers composing writes take Company then Payment before this Invoice lock.
    Non-locking use is for immutable issued facts inside an already stabilized read.
    """
    alias = current_database_alias()
    if (
        not Company.objects.using(alias)
        .select_for_update()
        .filter(pk=context.company_id, is_active=True)
        .exists()
    ):
        raise PermissionDenied("The selected company is unavailable.")
    require_permission(context, VIEW_INVOICES)
    rows = Invoice.objects.using(alias)
    if lock:
        rows = rows.select_for_update()
    invoice = rows.filter(pk=invoice_id, company_id=context.company_id).first()
    require_permission(context, VIEW_INVOICES)
    if invoice is None:
        raise PermissionDenied("Invoice is outside the authorized company.")
    if (
        invoice.status != Invoice.Status.ISSUED
        or invoice.issued_at is None
        or not invoice.bill_to_party_id
        or not Invoice.objects.using(alias)
        .filter(
            pk=invoice.pk,
            bill_to_party__company_id=context.company_id,
            currency__code=F("currency_code_snapshot"),
            currency_decimal_places_snapshot__gte=0,
            currency_decimal_places_snapshot__lte=8,
        )
        .exists()
    ):
        raise ValidationError("Invoice financial basis is incompatible.")
    lines = InvoiceLine.objects.using(alias).filter(invoice_id=invoice.pk)
    valid = Q(
        company_id=context.company_id,
        quantity__gte=Decimal("0.0001"),
        quantity__lte=MAX_INPUT,
        unit_price__gte=0,
        unit_price__lte=MAX_INPUT,
        position__gte=1,
        description__regex=r"\S",
    ) & ~Q(description__isnull=True)
    if (
        lines.exclude(valid).exists()
        or lines.alias(text=Trim("description")).filter(text="").exists()
    ):
        raise ValidationError("Invoice line basis is incompatible.")
    totals = lines.aggregate(
        count=Count("id"),
        raw=Sum(F("quantity") * F("unit_price"), output_field=DecimalField()),
    )
    if not totals["count"]:
        raise ValidationError("Issued invoice requires a complete line basis.")
    try:
        total = finalize_total(totals["raw"], invoice.currency_decimal_places_snapshot)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    return InvoiceFinancialBasis(
        invoice.pk,
        invoice.company_id,
        invoice.bill_to_party_id,
        invoice.status,
        invoice.issued_at,
        invoice.currency_id,
        invoice.currency_code_snapshot,
        invoice.currency_decimal_places_snapshot,
        total,
    )
