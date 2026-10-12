VIEW_POSTINGS = "accounting_billing.posting.view"
CREATE_POSTINGS = "accounting_billing.posting.create"
PERMISSIONS = (
    (VIEW_POSTINGS, "View invoice Accounting outcomes"),
    (CREATE_POSTINGS, "Post invoice Accounting outcomes"),
)
MODULE = {
    "code": "accounting_billing",
    "name": "Invoice Accounting",
    "version": "0.1.0",
    "depends": ["accounting", "billing"],
    "permissions": [code for code, _ in PERMISSIONS],
}
