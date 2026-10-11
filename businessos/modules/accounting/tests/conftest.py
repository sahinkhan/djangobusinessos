import pytest

from businessos.core.access.models import Permission, Role, RolePermission, UserRoleAssignment
from businessos.core.modules.services import register_manifest
from businessos.modules.accounting import services
from businessos.modules.accounting.manifest import MODULE
from businessos.modules.party.models import Party


@pytest.fixture
def accounting_role(operator, company):
    register_manifest(MODULE)
    role = Role.objects.create(company=company, code="accounting-test", name="Accounting test")
    for permission in Permission.objects.filter(code__in=MODULE["permissions"]):
        RolePermission.objects.create(role=role, permission=permission)
    UserRoleAssignment.objects.create(user=operator, company=company, role=role)
    return role


@pytest.fixture
def account(business_context, accounting_role):
    return services.create_account(business_context, code="CASH", name="Cash", type="ASSET")


@pytest.fixture
def journal(business_context, accounting_role):
    return services.create_journal(business_context, code="GEN", name="General")


@pytest.fixture
def entry(business_context, journal):
    return services.create_journal_entry(
        business_context, journal_id=journal.pk, entry_date="2026-10-11"
    )


@pytest.fixture
def party(company):
    return Party.objects.create(company=company, party_type="person", display_name="No roles")


@pytest.fixture
def balanced(business_context, entry, account, party):
    for debit, credit in [("10.50", "0"), ("0", "10.5000")]:
        services.add_journal_entry_line(
            business_context,
            entry.pk,
            account_id=account.pk,
            party_id=party.pk,
            debit=debit,
            credit=credit,
        )
    return entry
