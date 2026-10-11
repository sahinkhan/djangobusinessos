import asyncio

import pytest
from asgiref.sync import sync_to_async
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import connections

if not apps.is_installed("businessos.modules.payments.integrations.billing"):
    pytest.skip("Optional payments_billing deployment is not installed.", allow_module_level=True)

from ..models import PaymentAllocation
from .test_allocations import create

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize(
    "operation",
    ["save", "delete", "update", "delete_rows", "bulk_create", "bulk_update", "create", "upsert"],
)
def test_async_orm_guards(business_context, parents, operation):
    fact = create(business_context, parents)
    actions = {
        "save": lambda: fact.asave(),
        "delete": lambda: fact.adelete(),
        "update": lambda: PaymentAllocation.objects.aupdate(amount=1),
        "delete_rows": lambda: PaymentAllocation.objects.all().adelete(),
        "bulk_create": lambda: PaymentAllocation.objects.abulk_create([fact]),
        "bulk_update": lambda: PaymentAllocation.objects.abulk_update([fact], ["amount"]),
        "create": lambda: PaymentAllocation.objects.acreate(
            company_id=fact.company_id,
            payment_id=fact.payment_id,
            invoice_id=fact.invoice_id,
            amount=1,
            idempotency_key="async-bypass",
        ),
        "upsert": lambda: PaymentAllocation.objects.aupdate_or_create(
            pk=fact.pk, defaults={"amount": 1}
        ),
    }

    async def exercise():
        try:
            with pytest.raises(ValidationError):
                await actions[operation]()
        finally:
            # Close on the actual async ORM worker, not only the main test thread.
            await sync_to_async(connections.close_all, thread_sensitive=True)()

    asyncio.run(exercise())
    fact.refresh_from_db()
    assert fact.amount == 10 and PaymentAllocation.objects.count() == 1
