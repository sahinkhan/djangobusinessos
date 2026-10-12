import pytest
from django.apps import apps

if not apps.is_installed("businessos.modules.accounting.integrations.payments_billing"):
    pytest.skip(
        "ACC-INT-1 all-opt-in integration fixture topology is absent.", allow_module_level=True
    )

from businessos.core.access.models import Permission, Role, RolePermission, UserRoleAssignment
from businessos.core.modules.services import register_manifest
from businessos.modules.accounting import services as accounting
from businessos.modules.accounting.integrations.billing.manifest import MODULE as INVOICE
from businessos.modules.accounting.integrations.payments_billing.manifest import (
    MODULE as ALLOCATION,
)
from businessos.modules.accounting.manifest import MODULE as ACCOUNTING
from businessos.modules.billing import services as billing
from businessos.modules.billing.manifest import MODULE as BILLING
from businessos.modules.party.models import Party
from businessos.modules.payments import services as payments
from businessos.modules.payments.integrations.billing.manifest import MODULE as PAYINT
from businessos.modules.payments.integrations.billing.services import create_payment_allocation
from businessos.modules.payments.manifest import MODULE as PAYMENTS


@pytest.fixture
def outcome_role(company, operator):
    manifests = (ACCOUNTING, BILLING, PAYMENTS, PAYINT, INVOICE, ALLOCATION)
    for manifest in manifests:
        register_manifest(manifest)
    role = Role.objects.create(company=company, code="outcome-test", name="Synthetic outcomes")
    for permission in Permission.objects.filter(
        code__in=[code for manifest in manifests for code in manifest["permissions"]]
    ):
        RolePermission.objects.create(role=role, permission=permission)
    UserRoleAssignment.objects.create(user=operator, company=company, role=role)
    return role


@pytest.fixture
def outcomes(business_context, company, currency, outcome_role):
    party = Party.objects.create(
        company=company, party_type="person", display_name="Synthetic payer"
    )
    journal = accounting.create_journal(business_context, code="COMM", name="Commercial")
    ar = accounting.create_account(business_context, code="AR", name="Receivables", type="ASSET")
    revenue = accounting.create_account(business_context, code="REV", name="Revenue", type="INCOME")
    cash = accounting.create_account(business_context, code="CASH", name="Cash", type="ASSET")
    method = payments.create_payment_method(business_context, code="WIRE", name="Wire")

    def sources(total="100", allocated="40", *, issued=True, payment_date="2026-10-12"):
        invoice = billing.create_invoice(
            business_context,
            bill_to_party_id=party.pk,
            currency_id=currency.pk,
            invoice_date="2026-10-12",
        )
        billing.add_invoice_line(
            business_context,
            invoice_id=invoice.pk,
            description="Synthetic goods",
            quantity="1",
            unit_price=total,
        )
        if issued:
            invoice = billing.issue_invoice(business_context, invoice_id=invoice.pk)
        if allocated is None:
            return invoice, None, None
        payment = payments.record_payment(
            business_context,
            payer_party_id=party.pk,
            currency_id=currency.pk,
            amount="100",
            payment_method_id=method.pk,
            payment_date=payment_date,
        )
        allocation = create_payment_allocation(
            business_context,
            payment_id=payment.pk,
            invoice_id=invoice.pk,
            amount=allocated,
            idempotency_key=f"synthetic-{invoice.pk}",
        )
        return invoice, payment, allocation

    return {
        "journal": journal,
        "ar": ar,
        "revenue": revenue,
        "cash": cash,
        "party": party,
        "sources": sources,
    }
