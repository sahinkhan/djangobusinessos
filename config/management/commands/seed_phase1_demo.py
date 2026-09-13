from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from businessos.core.access.models import UserCompanyAccess
from businessos.core.common.context import BusinessContext
from businessos.core.modules.services import register_manifest
from businessos.core.organization.models import Company
from businessos.core.reference.models import Country, Currency, Language, UnitOfMeasure
from businessos.modules.catalog.manifest import MODULE as CATALOG_MANIFEST
from businessos.modules.catalog.models import Attribute, AttributeValue, Product, ProductVariant
from businessos.modules.catalog.services import (
    assign_variant_attribute_values,
    create_attribute,
    create_attribute_value,
    create_product_variant,
    create_simple_product,
    create_variable_product,
)
from businessos.modules.party.manifest import MODULE as PARTY_MANIFEST
from businessos.modules.party.models import Party
from businessos.modules.party.services import create_party


class Command(BaseCommand):
    help = (
        "Create an idempotent Phase 1 demo in the DEMO company, or in an existing "
        "company selected with --company. The command also enables Party and Catalog."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--company",
            default="DEMO",
            help="Existing company code. The default DEMO company is created when absent.",
        )

    def _report(self, label, created):
        self._created += int(created)
        self._existing += int(not created)
        state = "created" if created else "already existed"
        self.stdout.write(f"{label}: {state}")

    def _reference(self, model, code, defaults):
        record, created = model.objects.get_or_create(code=code, defaults=defaults)
        if not record.is_active:
            raise CommandError(f"{model.__name__} {code} must be active before demo seeding.")
        self._report(f"{model.__name__} {code}", created)
        return record

    def _party(self, context, *, display_name, is_customer=False, is_supplier=False):
        party = Party.objects.filter(
            company_id=context.company_id, display_name=display_name
        ).first()
        if party is None:
            party = create_party(
                context,
                party_type=Party.Type.ORGANIZATION,
                display_name=display_name,
                is_customer=is_customer,
                is_supplier=is_supplier,
            )
            created = True
        else:
            created = False
        self._report(f"Party {display_name}", created)
        return party

    def _simple_product(self, context, *, name, sku, product_type, uom):
        variant = ProductVariant.objects.select_related("product").filter(
            company_id=context.company_id, sku=sku
        ).first()
        if variant is None:
            product = create_simple_product(
                context,
                name=name,
                sku=sku,
                product_type=product_type,
                default_uom_id=uom.id,
            )
            created = True
        else:
            product = variant.product
            created = False
        if product.structure != Product.Structure.SIMPLE:
            raise CommandError(f"SKU {sku} already belongs to a non-simple Product.")
        self._report(f"Simple Product {name} / {sku}", created)
        return product

    def _attribute(self, context, name):
        attribute = Attribute.objects.filter(
            company_id=context.company_id, name=name
        ).first()
        if attribute is None:
            attribute = create_attribute(context, name=name)
            created = True
        else:
            created = False
        self._report(f"Attribute {name}", created)
        return attribute

    def _attribute_value(self, context, attribute, value):
        attribute_value = AttributeValue.objects.filter(
            attribute=attribute, value=value
        ).first()
        if attribute_value is None:
            attribute_value = create_attribute_value(
                context, attribute_id=attribute.id, value=value
            )
            created = True
        else:
            created = False
        self._report(f"Attribute value {attribute.name}={value}", created)
        return attribute_value

    def _variable_product(self, context, uom):
        product = Product.objects.filter(
            company_id=context.company_id,
            name="Premium T-Shirt",
            structure=Product.Structure.VARIABLE,
        ).first()
        specs = (
            {"sku": "TS-BLK-M", "is_default": True},
            {"sku": "TS-BLK-L"},
            {"sku": "TS-WHT-M"},
        )
        if product is None:
            product = create_variable_product(
                context,
                name="Premium T-Shirt",
                variants=specs,
                product_type=Product.Type.STOCKABLE,
                default_uom_id=uom.id,
            )
            self._report("Variable Product Premium T-Shirt", True)
        else:
            self._report("Variable Product Premium T-Shirt", False)
            existing_skus = set(product.variants.values_list("sku", flat=True))
            for spec in specs:
                if spec["sku"] not in existing_skus:
                    create_product_variant(context, product_id=product.id, **spec)
                    self._report(f"Variant {spec['sku']}", True)
        return product

    @transaction.atomic
    def handle(self, *args, **options):
        self._created = 0
        self._existing = 0
        company_code = options["company"].strip().upper()
        currency = self._reference(
            Currency,
            "USD",
            {"name": "US Dollar", "symbol": "$", "decimal_places": 2},
        )
        country = self._reference(Country, "US", {"name": "United States"})
        language = self._reference(Language, "EN", {"name": "English"})
        uom = self._reference(
            UnitOfMeasure,
            "EA",
            {"name": "Each", "symbol": "ea"},
        )
        company = Company.objects.filter(code=company_code).first()
        if company is None:
            if company_code != "DEMO":
                raise CommandError(
                    f"Company {company_code} does not exist. Only the default DEMO company "
                    "is created automatically."
                )
            company = Company.objects.create(
                code="DEMO",
                name="BusinessOS Demo Company",
                base_currency=currency,
                country=country,
                default_language=language,
            )
            company_created = True
        else:
            company_created = False
        if not company.is_active:
            raise CommandError(f"Company {company.code} must be active before demo seeding.")
        self._report(f"Company {company.code}", company_created)

        user_model = get_user_model()
        actor, actor_created = user_model.objects.get_or_create(
            email="phase1-demo@businessos.local"
        )
        if actor_created:
            actor.set_unusable_password()
            actor.save(update_fields=["password"])
        elif not actor.is_active:
            raise CommandError("The Phase 1 demo actor exists but is inactive.")
        self._report("Non-login Phase 1 demo actor", actor_created)
        _, access_created = UserCompanyAccess.objects.get_or_create(user=actor, company=company)
        self._report(f"Demo actor access to {company.code}", access_created)
        context = BusinessContext(actor_id=actor.id, company_id=company.id)

        for manifest in (PARTY_MANIFEST, CATALOG_MANIFEST):
            module = register_manifest(manifest)
            was_enabled = module.is_enabled
            if not was_enabled:
                module.is_enabled = True
                module.save(update_fields=["is_enabled", "updated_at"])
            self.stdout.write(
                f"Module {module.code}: {'already enabled' if was_enabled else 'enabled'}"
            )

        self._party(context, display_name="Demo Customer", is_customer=True)
        self._party(context, display_name="Demo Supplier", is_supplier=True)
        self._simple_product(
            context,
            name="Organic Honey",
            sku="HONEY-001",
            product_type=Product.Type.STOCKABLE,
            uom=uom,
        )
        self._simple_product(
            context,
            name="Website Development",
            sku="SERVICE-WEB-001",
            product_type=Product.Type.SERVICE,
            uom=uom,
        )
        variable_product = self._variable_product(context, uom)
        color = self._attribute(context, "Color")
        size = self._attribute(context, "Size")
        black = self._attribute_value(context, color, "Black")
        white = self._attribute_value(context, color, "White")
        medium = self._attribute_value(context, size, "M")
        large = self._attribute_value(context, size, "L")
        assignments = {
            "TS-BLK-M": [black.id, medium.id],
            "TS-BLK-L": [black.id, large.id],
            "TS-WHT-M": [white.id, medium.id],
        }
        for sku, value_ids in assignments.items():
            variant = variable_product.variants.get(sku=sku)
            assign_variant_attribute_values(
                context, variant_id=variant.id, attribute_value_ids=value_ids
            )
            self.stdout.write(f"Variant {sku} attributes: synchronized")

        self.stdout.write(
            self.style.SUCCESS(
                f"Phase 1 demo ready for {company.code} "
                f"({self._created} created, {self._existing} already existed)."
            )
        )
