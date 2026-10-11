from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db.models import DecimalField, Exists, F, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Length, Round, Trim

from businessos.core.database import business_atomic, current_database_alias
from businessos.modules.billing.models import Invoice
from businessos.modules.billing.selectors import invoice_financial_basis, issued_invoice_basis_query
from businessos.modules.payments.models import Payment
from businessos.modules.payments.selectors import payment_receipt_basis, receipt_basis_query

from . import domain
from .authorization import authorize
from .compatibility import evidence_profile
from .manifest import VIEW_ALLOCATIONS
from .models import PaymentAllocation


def value(field, function, *args):
    try:
        return function(*args)
    except ValueError as exc:
        raise ValidationError({field: str(exc)}) from exc


def validate_history(context):
    """Whole scoped evidence, including malformed rows on either endpoint.

    All probes are scalar SQL EXISTS/aggregates; no description/notes or unbounded
    model payload is constructed. A corrupt off-page fact invalidates the result.
    """
    alias = current_database_alias()
    payments_by_id = Payment.objects.using(alias).filter(pk=OuterRef("payment_id"))
    invoices_by_id = Invoice.objects.using(alias).filter(pk=OuterRef("invoice_id"))
    rows = PaymentAllocation.objects.using(alias).filter(
        Q(company_id=context.company_id)
        | Exists(payments_by_id.filter(company_id=context.company_id))
        | Exists(invoices_by_id.filter(company_id=context.company_id))
    )
    # Check the raw ledger before any joins: malformed FK facts must not vanish
    # from the validity proof, even outside the requested page/filter.
    if rows.filter(~Exists(payments_by_id) | ~Exists(invoices_by_id)).exists():
        raise ValidationError("Missing allocation parent history.")
    valid = Q(
        company_id=context.company_id,
        payment__company_id=context.company_id,
        invoice__company_id=context.company_id,
        payment__payer_party_id=F("invoice__bill_to_party_id"),
        payment__currency_id=F("invoice__currency_id"),
        payment__currency_code_snapshot=F("invoice__currency_code_snapshot"),
        payment__currency_decimal_places_snapshot=F("invoice__currency_decimal_places_snapshot"),
        amount__gt=0,
        amount__lt=domain.AMOUNT_LIMIT,
        idempotency_key__regex=r"\S",
        created_at__isnull=False,
        updated_at__isnull=False,
    )
    if (
        rows.alias(key_length=Length("idempotency_key"), trimmed_key=Trim("idempotency_key"))
        .exclude(
            valid
            & Q(key_length__lte=128, idempotency_key=F("trimmed_key"))
            & ~Q(idempotency_key__regex=r"(^\s|\s$)")
        )
        .exists()
    ):
        raise ValidationError("Incompatible allocation provenance.")
    if (
        rows.alias(exact=Round("amount", F("payment__currency_decimal_places_snapshot")))
        .exclude(amount=F("exact"))
        .exists()
    ):
        raise ValidationError("Allocation amount exceeds frozen precision.")
    payments = receipt_basis_query(context, payment_ids=rows.values("payment_id"))
    invoices = issued_invoice_basis_query(context, invoice_ids=rows.values("invoice_id"))
    if payments.filter(basis_valid=False).exists() or invoices.filter(basis_valid=False).exists():
        raise ValidationError("Incompatible allocation parent history.")
    payment_sums = (
        PaymentAllocation.objects.using(alias)
        .filter(payment_id=OuterRef("pk"))
        .order_by()
        .values("payment_id")
        .annotate(total=Sum("amount", output_field=DecimalField()))
        .values("total")
    )
    invoice_sums = (
        PaymentAllocation.objects.using(alias)
        .filter(invoice_id=OuterRef("pk"))
        .order_by()
        .values("invoice_id")
        .annotate(total=Sum("amount", output_field=DecimalField()))
        .values("total")
    )
    if (
        payments.alias(applied=Subquery(payment_sums, output_field=DecimalField()))
        .filter(applied__gt=F("amount"))
        .exists()
    ):
        raise ValidationError("Payment allocation history exceeds capacity.")
    if (
        invoices.alias(applied=Subquery(invoice_sums, output_field=DecimalField()))
        .filter(applied__gt=F("basis_total"))
        .exists()
    ):
        raise ValidationError("Invoice allocation history exceeds capacity.")
    return rows


def applied(rows):
    total = rows.aggregate(total=Sum("amount", output_field=DecimalField()))["total"]
    return Decimal(0) if total is None else total


@dataclass(frozen=True, slots=True)
class AllocationHistoryRow:
    id: UUID
    payment_id: UUID
    invoice_id: UUID
    payment_number: str
    invoice_number: str
    amount: Decimal
    created_at: object
    precision: int

    @property
    def formatted_amount(self):
        return format(self.amount, f".{self.precision}f")


def _page(rows, precision, *, page, search, counterpart_id, endpoint):
    if type(page) is not int or page < 1 or not isinstance(search, str):
        raise ValidationError("Use a positive page number and textual search.")
    if counterpart_id is not None:
        identity = value("counterpart_id", domain.identity, counterpart_id)
        rows = rows.filter(**{f"{endpoint}_id": identity})
    if search.strip():
        rows = rows.filter(
            Q(payment__number__icontains=search.strip())
            | Q(invoice__number__icontains=search.strip())
        )
    count = rows.count()
    pages = max(1, (count + domain.PAGE_SIZE - 1) // domain.PAGE_SIZE)
    page = min(page, pages)
    start = (page - 1) * domain.PAGE_SIZE
    payload = rows.order_by("created_at", "id").values(
        "id",
        "payment_id",
        "invoice_id",
        "payment__number",
        "invoice__number",
        "amount",
        "created_at",
    )[start : start + domain.PAGE_SIZE]
    history = tuple(
        AllocationHistoryRow(
            row["id"],
            row["payment_id"],
            row["invoice_id"],
            row["payment__number"],
            row["invoice__number"],
            row["amount"],
            row["created_at"],
            precision,
        )
        for row in payload
    )
    return history, count, page, pages


@business_atomic
def _evidence(context, identity, *, parent, page=1, search="", counterpart_id=None):
    authorize(context, VIEW_ALLOCATIONS)
    identity = value(f"{parent}_id", domain.identity, identity)
    reason = evidence_profile()
    if reason:
        return domain.AllocationEvidence.unavailable(reason)
    try:
        if parent == "payment":
            basis = payment_receipt_basis(context, identity)
            original = basis.amount
            endpoint = "invoice"
        else:
            basis = invoice_financial_basis(context, identity)
            original = basis.original_total
            endpoint = "payment"
        authorize(context, VIEW_ALLOCATIONS)
        rows = validate_history(context).filter(**{f"{parent}_id": identity})
        total = applied(rows)
    except ValidationError:
        return domain.AllocationEvidence.unavailable("incompatible")
    # Filter validation is deliberately outside the integrity-error conversion.
    history, count, page, pages = _page(
        rows,
        basis.precision,
        page=page,
        search=search,
        counterpart_id=counterpart_id,
        endpoint=endpoint,
    )
    return domain.AllocationEvidence(
        "AVAILABLE",
        applied=total,
        remaining=domain.subtract(original, total),
        original=original,
        currency_code=basis.currency_code,
        precision=basis.precision,
        history=history,
        count=count,
        page=page,
        pages=pages,
    )


def payment_allocation_evidence(context, payment_id, **filters):
    return _evidence(context, payment_id, parent="payment", **filters)


def invoice_allocation_evidence(context, invoice_id, **filters):
    return _evidence(context, invoice_id, parent="invoice", **filters)
