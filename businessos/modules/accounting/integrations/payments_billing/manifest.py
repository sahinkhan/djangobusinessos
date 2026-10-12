VIEW_POSTINGS = "accounting_payments_billing.posting.view"
CREATE_POSTINGS = "accounting_payments_billing.posting.create"
PERMISSIONS = (
    (VIEW_POSTINGS, "View allocation Accounting outcomes"),
    (CREATE_POSTINGS, "Post allocation Accounting outcomes"),
)
MODULE = {
    "code": "accounting_payments_billing",
    "name": "Allocation Accounting",
    "version": "0.1.0",
    "depends": ["accounting", "accounting_billing", "payments_billing"],
    "permissions": [code for code, _ in PERMISSIONS],
}
