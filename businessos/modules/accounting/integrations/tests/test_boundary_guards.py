import asyncio
from importlib import import_module

import pytest
from asgiref.sync import sync_to_async
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import connection, connections, transaction

from businessos.core.access.models import Permission
from businessos.core.database import current_database_alias
from businessos.core.modules.models import BusinessModule
from businessos.modules.accounting.integrations.billing.models import InvoicePosting
from businessos.modules.accounting.integrations.payments_billing.models import AllocationPosting
from businessos.modules.accounting.selectors import posted_journal_basis
from businessos.modules.billing.selectors import invoice_accounting_basis

from .test_outcomes import allocation_post, invoice_post

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("effect", ["invoice", "allocation"])
@pytest.mark.parametrize(
    "operation",
    ["save", "delete", "update", "rows_delete", "bulk_create", "bulk_update", "create", "upsert"],
)
def test_async_binding_guards(business_context, outcomes, effect, operation):
    invoice, _, allocation = outcomes["sources"]()
    result = invoice_post(business_context, outcomes, invoice)
    if effect == "allocation":
        result = allocation_post(business_context, outcomes, allocation)
    model = InvoicePosting if effect == "invoice" else AllocationPosting
    fact = model.objects.get(pk=result.binding_id)
    actions = {
        "save": fact.asave,
        "delete": fact.adelete,
        "update": lambda: model.objects.aupdate(effect="other"),
        "rows_delete": lambda: model.objects.all().adelete(),
        "bulk_create": lambda: model.objects.abulk_create(
            [fact], update_conflicts=True, update_fields=["effect"], unique_fields=["id"]
        ),
        "bulk_update": lambda: model.objects.abulk_update([fact], ["effect"]),
        "create": lambda: model.objects.acreate(),
        "upsert": lambda: model.objects.aupdate_or_create(pk=fact.pk, defaults={"effect": "other"}),
    }

    async def exercise():
        try:
            with pytest.raises(ValidationError):
                await actions[operation]()
        finally:
            await sync_to_async(connections.close_all, thread_sensitive=True)()

    asyncio.run(exercise())
    fact.refresh_from_db()
    assert fact.effect == result.effect and model.objects.count() == 1


def test_nonlocking_owner_reads_require_outer_transaction(business_context, outcomes):
    invoice, _, _ = outcomes["sources"]("1", None)
    result = invoice_post(business_context, outcomes, invoice)
    for reader, identity in [
        (invoice_accounting_basis, invoice.pk),
        (posted_journal_basis, result.journal_entry_id),
    ]:
        with pytest.raises(ValidationError, match="outer selected-alias"):
            reader(business_context, identity, lock=False)
        with transaction.atomic(using=current_database_alias()):
            assert reader(business_context, identity, lock=False).id == identity


@pytest.mark.parametrize("effect", ["invoice", "allocation"])
def test_frozen_registration_preserves_enablement_and_permission_activity(outcomes, effect):
    code = "accounting_billing" if effect == "invoice" else "accounting_payments_billing"
    module = BusinessModule.objects.get(code=code)
    BusinessModule.objects.filter(pk=module.pk).update(is_enabled=True)
    Permission.objects.filter(code=f"{code}.posting.create").update(is_active=False)
    package = "billing" if effect == "invoice" else "payments_billing"
    registration = import_module(
        f"businessos.modules.accounting.integrations.{package}.migrations.0002_register_manifest"
    )
    # Same frozen migration function, with selected-alias historical app registry contract.
    with connection.schema_editor() as editor:
        registration.register(apps, editor)
    assert BusinessModule.objects.get(pk=module.pk).is_enabled
    assert not Permission.objects.get(code=f"{code}.posting.create").is_active


@pytest.mark.parametrize("missing", [False, True])
def test_non_http_apis_ignore_registry(outcomes, business_context, missing):
    invoice, _, allocation = outcomes["sources"]()
    codes = ["accounting_billing", "accounting_payments_billing"]
    if missing:
        BusinessModule.objects.filter(code__in=codes).delete()
    else:
        BusinessModule.objects.filter(code__in=codes).update(is_enabled=False)
    assert invoice_post(business_context, outcomes, invoice).state == "POSTED"
    assert allocation_post(business_context, outcomes, allocation).state == "POSTED"
