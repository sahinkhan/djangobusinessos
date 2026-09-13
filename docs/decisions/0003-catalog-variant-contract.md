# ADR 0003 — Catalog Product Variant Contract

Status: Accepted

## Context

BusinessOS must support both simple products and configurable products across Ecommerce, Sales, Procurement, Inventory, POS and future verticals such as Garments/Apparel.

If simple products are modeled separately from variant products, downstream modules must repeatedly branch between product-level and variant-level identity. Retrofitting variants after Sales/Inventory/Ecommerce exist would also create avoidable migration and contract churn.

## Decision

`Product` is the conceptual/catalog identity. `ProductVariant` is the actual sellable/purchasable SKU identity.

Every sellable/purchasable Product must have at least one ProductVariant.

### Simple product

A simple product has exactly one default variant and no required attribute-value assignments.

Example:

```text
Product: Organic Honey
└── ProductVariant
    SKU: HONEY-001
    is_default: true
```

### Variable product

A variable product has one or more variants differentiated by attribute values.

Example:

```text
Product: Premium T-Shirt
├── TS-BLK-M -> Color=Black, Size=M
├── TS-BLK-L -> Color=Black, Size=L
└── TS-WHT-M -> Color=White, Size=M
```

## Catalog ownership

Catalog owns:

- Product
- ProductVariant
- ProductCategory
- Attribute
- AttributeValue
- VariantAttributeValue

Catalog does not own authoritative stock quantities, transactional pricing engines, sales/purchase workflows, accounting balances or ecommerce-specific duplicate product records.

## Downstream contract

Where a transaction identifies a concrete sellable/purchasable item, it should reference `ProductVariant`, not alternate between Product and ProductVariant.

Expected future examples:

```text
SalesOrderLine -> ProductVariant
PurchaseOrderLine -> ProductVariant
StockMovement -> ProductVariant
POSLine -> ProductVariant
EcommerceCartLine -> ProductVariant
```

A Product may still be referenced for catalog browsing, grouping, content and product-level metadata.

## Phase 1 scope

Phase 1 implements only the minimum variant foundation:

- Product
- ProductVariant
- ProductCategory
- Attribute
- AttributeValue
- VariantAttributeValue
- invariant that a sellable/purchasable Product has at least one variant
- invariant that a Product has at most one default variant
- simple-product service behavior that creates/maintains its default variant

Phase 1 does NOT implement:

- combinatorial variant generation
- advanced product configurator
- variant pricing/pricelists
- promotions/campaign pricing
- inventory quantities
- barcode platform
- bundles/kits
- BOM/manufacturing
- advanced media library
- complex UoM conversion

## Consequences

Benefits:

- one stable item identity for Sales/Procurement/Inventory/POS/Ecommerce
- simple and variable products share downstream logic
- variants do not need to be retrofitted after transaction modules exist
- Catalog remains reusable for ecommerce and non-ecommerce products

Costs:

- even a simple product has an internal ProductVariant row
- Catalog services must preserve default-variant invariants

The UI may hide variant complexity for simple products. Users do not need to manage a visible variant matrix when only the default variant exists.
