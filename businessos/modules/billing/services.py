from datetime import date, datetime
from uuid import uuid4

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.db.models import Max
from django.utils import timezone

from businessos.core.access.policies import require_permission
from businessos.core.audit.services import record_audit_entry
from businessos.core.common.context import BusinessContext
from businessos.core.database import business_atomic, business_atomic_context
from businessos.core.organization.models import Company
from businessos.core.organization.time import company_local_date
from businessos.core.reference.models import Currency
from businessos.modules.party.models import Party

from .domain import currency_precision, decimal_input
from .manifest import CREATE_INVOICES, ISSUE_INVOICES, UPDATE_INVOICES
from .models import _ISSUE_TOKEN, _WRITE_TOKEN, Invoice, InvoiceLine


def _authorize(context: BusinessContext, permission):
    company = (
        Company.objects.select_for_update().filter(pk=context.company_id, is_active=True).first()
    )
    if company is None:
        raise PermissionDenied("The selected company does not exist or is inactive.")
    require_permission(context, permission)


def _party(context, party_id):
    try:
        return Party.objects.select_for_update().get(
            pk=party_id,
            company_id=context.company_id,
            is_active=True,
            party_type__in=[Party.Type.PERSON, Party.Type.ORGANIZATION],
        )
    except Party.DoesNotExist as exc:
        raise ValidationError({"bill_to_party": "Select an active Party in this company."}) from exc


def _currency(currency_id):
    try:
        currency = Currency.objects.select_for_update().get(pk=currency_id, is_active=True)
        currency_precision(currency.decimal_places)
        return currency
    except (Currency.DoesNotExist, ValueError) as exc:
        raise ValidationError(
            {"currency": "Select an active currency with precision 0–8."}
        ) from exc


def _date(value, field, *, optional=False):
    if value is None and optional:
        return None
    if isinstance(value, str):
        try:
            value = date.fromisoformat(value)
        except ValueError:
            value = None
    if not isinstance(value, date) or isinstance(value, datetime):
        raise ValidationError({field: "Enter a valid date."})
    return value


def _locked_invoice(context, invoice_id):
    try:
        return Invoice.objects.select_for_update().get(pk=invoice_id, company_id=context.company_id)
    except Invoice.DoesNotExist as exc:
        raise PermissionDenied("Invoice is outside the selected company.") from exc


def _draft(invoice):
    if invoice.status != Invoice.Status.DRAFT:
        raise ValidationError("Only draft invoices may change.")


def _line(invoice, line_id):
    try:
        return InvoiceLine.objects.select_for_update().get(
            pk=line_id, invoice_id=invoice.pk, company_id=invoice.company_id
        )
    except InvoiceLine.DoesNotExist as exc:
        raise PermissionDenied("Line is outside this invoice and company.") from exc


def _audit(context, invoice, action="updated", **metadata):
    record_audit_entry(
        context=context,
        action=f"billing.invoice.{action}",
        object_type="billing.Invoice",
        object_id=invoice.pk,
        metadata=metadata,
    )


def _snap_party(invoice, party):
    invoice.bill_to_party = party
    invoice.bill_to_display_name_snapshot = party.display_name
    invoice.bill_to_legal_name_snapshot = party.legal_name


def _snap_currency(invoice, currency):
    invoice.currency = currency
    invoice.currency_code_snapshot = currency.code
    invoice.currency_decimal_places_snapshot = currency.decimal_places


def _number():
    return f"INV-{uuid4().hex.upper()}"


def _validate_total(invoice):
    try:
        return invoice.total
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


@business_atomic
def create_invoice(
    context: BusinessContext,
    *,
    bill_to_party_id,
    currency_id,
    invoice_date=None,
    due_date=None,
    notes="",
):
    _authorize(context, CREATE_INVOICES)
    invoice = Invoice(
        company_id=context.company_id,
        invoice_date=_date(
            company_local_date(context.company_id) if invoice_date is None else invoice_date,
            "invoice_date",
        ),
        due_date=_date(due_date, "due_date", optional=True),
        notes=notes,
    )
    _snap_party(invoice, _party(context, bill_to_party_id))
    _snap_currency(invoice, _currency(currency_id))
    for attempt in range(3):
        invoice.number = _number()
        try:
            with business_atomic_context():
                invoice._persist(_WRITE_TOKEN, creating=True)
        except IntegrityError:
            if not Invoice.objects.filter(
                company_id=context.company_id, number=invoice.number
            ).exists():
                raise
            if attempt == 2:
                raise ValidationError("Could not allocate a unique invoice number.") from None
        else:
            break
    _audit(context, invoice, "created", number=invoice.number)
    return invoice


@business_atomic
def update_invoice(context: BusinessContext, invoice_id, **changes):
    _authorize(context, UPDATE_INVOICES)
    invoice = _locked_invoice(context, invoice_id)
    _draft(invoice)
    allowed = {"bill_to_party_id", "currency_id", "invoice_date", "due_date", "notes"}
    if changes.keys() - allowed:
        raise ValidationError("Unsupported invoice fields.")
    fields = [
        "bill_to_party_id",
        "bill_to_display_name_snapshot",
        "bill_to_legal_name_snapshot",
        "currency_id",
        "currency_code_snapshot",
        "currency_decimal_places_snapshot",
        "invoice_date",
        "due_date",
        "notes",
    ]
    before = {field: getattr(invoice, field) for field in fields}
    if "bill_to_party_id" in changes:
        _snap_party(invoice, _party(context, changes.pop("bill_to_party_id")))
    if "currency_id" in changes:
        _snap_currency(invoice, _currency(changes.pop("currency_id")))
    for field, value in changes.items():
        if field in {"invoice_date", "due_date"}:
            value = _date(value, field, optional=field == "due_date")
        setattr(invoice, field, value)
    invoice.full_clean(validate_constraints=False)
    _validate_total(invoice)
    changed = [field for field in fields if before[field] != getattr(invoice, field)]
    if changed:
        invoice._persist(_WRITE_TOKEN)
        _audit(context, invoice, change="header", fields=changed)
    return invoice


def _line_data(line, description, quantity, unit_price):
    line.description = description
    for field, value, positive in [("quantity", quantity, True), ("unit_price", unit_price, False)]:
        try:
            setattr(line, field, decimal_input(value, positive=positive))
        except ValueError as exc:
            raise ValidationError({field: str(exc)}) from exc
    line.clean()


@business_atomic
def add_invoice_line(context: BusinessContext, invoice_id, *, description, quantity, unit_price):
    _authorize(context, UPDATE_INVOICES)
    invoice = _locked_invoice(context, invoice_id)
    _draft(invoice)
    position = (invoice.lines.aggregate(value=Max("position"))["value"] or 0) + 1
    line = InvoiceLine(company_id=context.company_id, invoice=invoice, position=position)
    _line_data(line, description, quantity, unit_price)
    line._persist(_WRITE_TOKEN, creating=True)
    _validate_total(invoice)
    _audit(context, invoice, change="line_added", line_id=str(line.pk))
    return line


@business_atomic
def update_invoice_line(context: BusinessContext, invoice_id, line_id, **changes):
    _authorize(context, UPDATE_INVOICES)
    invoice = _locked_invoice(context, invoice_id)
    _draft(invoice)
    line = _line(invoice, line_id)
    fields = ("description", "quantity", "unit_price")
    if changes.keys() - set(fields):
        raise ValidationError("Unsupported invoice line fields.")
    before = tuple(getattr(line, f) for f in fields)
    _line_data(line, **{f: changes.get(f, getattr(line, f)) for f in fields})
    if before != tuple(getattr(line, f) for f in fields):
        line._persist(_WRITE_TOKEN)
        _validate_total(invoice)
        _audit(context, invoice, change="line_updated", line_id=str(line.pk))
    return line


@business_atomic
def remove_invoice_line(context: BusinessContext, invoice_id, line_id):
    _authorize(context, UPDATE_INVOICES)
    invoice = _locked_invoice(context, invoice_id)
    _draft(invoice)
    line = _line(invoice, line_id)
    line._persist(_WRITE_TOKEN, remove=True)
    _audit(context, invoice, change="line_removed", line_id=str(line_id))


@business_atomic
def issue_invoice(context: BusinessContext, invoice_id):
    _authorize(context, ISSUE_INVOICES)
    invoice = _locked_invoice(context, invoice_id)
    if invoice.status == Invoice.Status.ISSUED:
        return invoice
    _draft(invoice)
    _party(context, invoice.bill_to_party_id)
    currency = _currency(invoice.currency_id)
    if (currency.code, currency.decimal_places) != (
        invoice.currency_code_snapshot,
        invoice.currency_decimal_places_snapshot,
    ):
        raise ValidationError({"currency": "Currency changed; explicitly refresh the draft first."})
    invoice.full_clean()
    lines = list(invoice.lines.select_for_update())
    if not lines:
        raise ValidationError("An invoice requires at least one line before issue.")
    for line in lines:
        line.clean()
        line.full_clean()
    _validate_total(invoice)
    invoice._issue(_ISSUE_TOKEN, timezone.now())
    _audit(context, invoice, "issued", number=invoice.number)
    return invoice
