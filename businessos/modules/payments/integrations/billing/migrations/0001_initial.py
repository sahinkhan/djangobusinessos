import uuid
from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models
from django.db.models.functions import Length, Trim
from django.db.models.lookups import GreaterThan, LessThanOrEqual


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("organization", "0001_initial"),
        ("payments", "0002_register_manifest"),
        ("billing", "0002_register_manifest"),
    ]
    operations = [
        migrations.CreateModel(
            name="PaymentAllocation",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("amount", models.DecimalField(decimal_places=8, max_digits=38)),
                ("idempotency_key", models.CharField(max_length=128)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="organization.company"
                    ),
                ),
                (
                    "payment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="payments.payment"
                    ),
                ),
                (
                    "invoice",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="billing.invoice"
                    ),
                ),
            ],
            options={
                "ordering": ["created_at", "id"],
                "indexes": [
                    models.Index(
                        fields=["company", "payment", "created_at", "id"],
                        name="allocation_payment_history",
                    ),
                    models.Index(
                        fields=["company", "invoice", "created_at", "id"],
                        name="allocation_invoice_history",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("company", "idempotency_key"), name="allocation_company_key_uniq"
                    ),
                    models.CheckConstraint(
                        condition=models.Q(amount__gt=0), name="allocation_amount_positive"
                    ),
                    models.CheckConstraint(
                        condition=models.Q(amount__lt=Decimal("1e30")),
                        name="allocation_amount_range",
                    ),
                    models.CheckConstraint(
                        condition=GreaterThan(Length(Trim("idempotency_key")), 0)
                        & LessThanOrEqual(Length("idempotency_key"), 128)
                        & models.Q(idempotency_key__regex=r"\S"),
                        name="allocation_key_bounds",
                    ),
                ],
            },
        ),
    ]
