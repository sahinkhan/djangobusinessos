VIEW_ORDERS = "procurement.order.view"
CREATE_ORDERS = "procurement.order.create"
UPDATE_ORDERS = "procurement.order.update"
CONFIRM_ORDERS = "procurement.order.confirm"
CANCEL_ORDERS = "procurement.order.cancel"
RECEIVE_ORDERS = "procurement.receipt.receive"

PROCUREMENT_PERMISSION_DECLARATIONS = (
    (VIEW_ORDERS, "View purchase orders and purchase receipts"),
    (CREATE_ORDERS, "Create purchase orders"),
    (UPDATE_ORDERS, "Update draft purchase orders"),
    (CONFIRM_ORDERS, "Confirm purchase orders"),
    (CANCEL_ORDERS, "Cancel confirmed purchase orders"),
    (RECEIVE_ORDERS, "Post purchase receipts"),
)

MODULE = {
    "code": "procurement",
    "name": "Procurement",
    "version": "0.1.0",
    "depends": ["party", "catalog", "organization", "reference", "access"],
    "permissions": [code for code, _name in PROCUREMENT_PERMISSION_DECLARATIONS],
}
