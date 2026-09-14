VIEW_ORDERS = "sales.order.view"
CREATE_ORDERS = "sales.order.create"
UPDATE_ORDERS = "sales.order.update"
CONFIRM_ORDERS = "sales.order.confirm"
CANCEL_ORDERS = "sales.order.cancel"

SALES_PERMISSION_DECLARATIONS = (
    (VIEW_ORDERS, "View sales orders"),
    (CREATE_ORDERS, "Create sales orders"),
    (UPDATE_ORDERS, "Update draft sales orders"),
    (CONFIRM_ORDERS, "Confirm sales orders"),
    (CANCEL_ORDERS, "Cancel confirmed sales orders"),
)

MODULE = {
    "code": "sales",
    "name": "Sales",
    "version": "0.1.0",
    "depends": ["party", "catalog", "organization", "reference", "access"],
    "permissions": [code for code, _name in SALES_PERMISSION_DECLARATIONS],
}
