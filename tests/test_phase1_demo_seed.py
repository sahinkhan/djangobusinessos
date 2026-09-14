from io import StringIO

import pytest
from django.core.management import call_command

from businessos.core.access.models import UserCompanyAccess
from businessos.core.modules.models import BusinessModule
from businessos.core.organization.models import Company
from businessos.modules.catalog.models import (
    Attribute,
    AttributeValue,
    Product,
    ProductVariant,
    VariantAttributeValue,
)
from businessos.modules.party.models import Party


@pytest.mark.django_db
def test_seed_phase1_demo_is_idempotent_and_creates_representative_data():
    first_output = StringIO()
    call_command("seed_phase1_demo", stdout=first_output)
    company = Company.objects.get(code="DEMO")
    first_counts = (
        Party.objects.filter(company=company).count(),
        Product.objects.filter(company=company).count(),
        ProductVariant.objects.filter(company=company).count(),
        Attribute.objects.filter(company=company).count(),
        AttributeValue.objects.filter(company=company).count(),
        VariantAttributeValue.objects.filter(company=company).count(),
        UserCompanyAccess.objects.filter(company=company).count(),
    )

    second_output = StringIO()
    call_command("seed_phase1_demo", stdout=second_output)
    second_counts = (
        Party.objects.filter(company=company).count(),
        Product.objects.filter(company=company).count(),
        ProductVariant.objects.filter(company=company).count(),
        Attribute.objects.filter(company=company).count(),
        AttributeValue.objects.filter(company=company).count(),
        VariantAttributeValue.objects.filter(company=company).count(),
        UserCompanyAccess.objects.filter(company=company).count(),
    )

    assert first_counts == second_counts == (2, 3, 5, 2, 4, 6, 1)
    assert "Phase 1 demo ready for DEMO" in first_output.getvalue()
    assert "0 created" in second_output.getvalue()
    assert set(
        Party.objects.filter(company=company).values_list(
            "display_name", "is_customer", "is_supplier"
        )
    ) == {("Demo Customer", True, False), ("Demo Supplier", False, True)}
    assert ProductVariant.objects.get(company=company, sku="HONEY-001").is_default is True
    service = ProductVariant.objects.get(company=company, sku="SERVICE-WEB-001").product
    assert service.product_type == Product.Type.SERVICE
    assert set(
        ProductVariant.objects.filter(
            company=company, product__name="Premium T-Shirt"
        ).values_list("sku", flat=True)
    ) == {"TS-BLK-M", "TS-BLK-L", "TS-WHT-M"}
    assert set(
        BusinessModule.objects.filter(code__in=["party", "catalog"], is_enabled=True).values_list(
            "code", flat=True
        )
    ) == {"party", "catalog"}
