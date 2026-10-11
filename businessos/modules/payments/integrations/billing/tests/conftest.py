import pytest

from businessos.core.access.models import Permission, Role, RolePermission, UserRoleAssignment
from businessos.core.modules.services import register_manifest
from businessos.modules.billing import services as billing
from businessos.modules.billing.manifest import MODULE as BILLING
from businessos.modules.party.models import Party
from businessos.modules.payments import services as payments
from businessos.modules.payments.integrations.billing.manifest import MODULE
from businessos.modules.payments.manifest import MODULE as PAYMENTS


@pytest.fixture
def allocation_role(company, operator):
    for manifest in (BILLING, PAYMENTS, MODULE):
        register_manifest(manifest)
    role = Role.objects.create(company=company, code="allocation-test", name="Allocation test")
    for permission in Permission.objects.filter(
        code__in=[
            code for manifest in (BILLING, PAYMENTS, MODULE) for code in manifest["permissions"]
        ]
    ):
        RolePermission.objects.create(role=role, permission=permission)
    UserRoleAssignment.objects.create(user=operator, company=company, role=role)
    return role


@pytest.fixture
def allocation_party(company):
    return Party.objects.create(
        company=company, party_type="person", display_name="Synthetic payer"
    )


@pytest.fixture
def financial_factory(business_context, currency, allocation_role, allocation_party):
    method = payments.create_payment_method(business_context, code="CASH", name="Cash")

    def create(*, receipt="100", total="100", issued=True, party=None, currency_id=None):
        party = party or allocation_party
        currency_id = currency_id or currency.pk
        payment = payments.record_payment(
            business_context,
            payer_party_id=party.pk,
            currency_id=currency_id,
            amount=receipt,
            payment_method_id=method.pk,
        )
        invoice = billing.create_invoice(
            business_context, bill_to_party_id=party.pk, currency_id=currency_id
        )
        billing.add_invoice_line(
            business_context,
            invoice_id=invoice.pk,
            description="Synthetic line",
            quantity="1",
            unit_price=total,
        )
        if issued:
            invoice = billing.issue_invoice(business_context, invoice_id=invoice.pk)
        return payment, invoice

    return create


@pytest.fixture
def parents(financial_factory):
    return financial_factory()
