VIEW_METHODS = "payments.method.view"
MANAGE_METHODS = "payments.method.manage"
VIEW_PAYMENTS = "payments.payment.view"
RECORD_PAYMENTS = "payments.payment.record"

PAYMENTS_PERMISSION_DECLARATIONS = (
    (VIEW_METHODS, "View payment methods"),
    (MANAGE_METHODS, "Manage payment methods"),
    (VIEW_PAYMENTS, "View receipts"),
    (RECORD_PAYMENTS, "Record incoming receipts"),
)

MODULE = {
    "code": "payments",
    "name": "Payments",
    "version": "0.1.0",
    "depends": ["party", "organization", "reference", "access"],
    "permissions": [code for code, _ in PAYMENTS_PERMISSION_DECLARATIONS],
}
