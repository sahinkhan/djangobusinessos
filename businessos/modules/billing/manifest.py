VIEW_INVOICES = "billing.invoice.view"
CREATE_INVOICES = "billing.invoice.create"
UPDATE_INVOICES = "billing.invoice.update"
ISSUE_INVOICES = "billing.invoice.issue"

BILLING_PERMISSION_DECLARATIONS = (
    (VIEW_INVOICES, "View invoices"),
    (CREATE_INVOICES, "Create draft invoices"),
    (UPDATE_INVOICES, "Update draft invoices and lines"),
    (ISSUE_INVOICES, "Issue invoices"),
)

MODULE = {
    "code": "billing",
    "name": "Billing & Invoicing",
    "version": "0.1.0",
    "depends": ["party", "organization", "reference", "access"],
    "permissions": [code for code, _ in BILLING_PERMISSION_DECLARATIONS],
}
